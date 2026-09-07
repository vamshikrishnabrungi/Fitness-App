from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.ids import uuid7
from .models import (
    SportKnowledgeArticle,
    SportKnowledgeArticleSource,
    SportKnowledgeArticleVersion,
    SportKnowledgeRelease,
    SportKnowledgeSource,
)
from .sports import SUPPORTED_TRAINING_SPORTS


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _reviewed(value: str | date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    return datetime.combine(date.fromisoformat(value), time.min, tzinfo=timezone.utc)


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


async def admin_sport_content(session: AsyncSession, sport_code: str) -> dict[str, Any]:
    rows = (await session.execute(
        select(SportKnowledgeArticle, SportKnowledgeArticleVersion)
        .join(SportKnowledgeArticleVersion, (SportKnowledgeArticleVersion.article_id == SportKnowledgeArticle.id) & (SportKnowledgeArticleVersion.content_version == SportKnowledgeArticle.latest_version))
        .where(SportKnowledgeArticle.sport_code == sport_code)
        .order_by(SportKnowledgeArticleVersion.category, SportKnowledgeArticleVersion.title)
    )).all()
    return {"items": [{"id": article.id, "slug": article.slug, "latest_version": article.latest_version, "published_version": article.published_version, "archived": article.archived, "record_version": article.version, "status": version.status, "category": version.category, "title": version.title, "summary": version.summary, "updated_at": version.updated_at} for article, version in rows]}


async def admin_article_detail(session: AsyncSession, article_id: UUID, version_number: int | None = None) -> dict[str, Any] | None:
    article = await session.get(SportKnowledgeArticle, article_id)
    if article is None:
        return None
    version_number = version_number or article.latest_version
    version = await session.get(SportKnowledgeArticleVersion, (article.id, version_number))
    if version is None:
        return None
    sources = (await session.scalars(select(SportKnowledgeSource).join(SportKnowledgeArticleSource, SportKnowledgeArticleSource.source_id == SportKnowledgeSource.id).where(SportKnowledgeArticleSource.article_id == article.id, SportKnowledgeArticleSource.article_version == version_number).order_by(SportKnowledgeSource.source_key))).all()
    return {"id": article.id, "sport_code": article.sport_code, "slug": article.slug, "latest_version": article.latest_version, "published_version": article.published_version, "archived": article.archived, "content_version": version.content_version, "category": version.category, "title": version.title, "summary": version.summary, "icon": version.icon, "audiences": version.audiences, "events": version.events, "sections": version.sections, "medical_disclaimer": version.medical_disclaimer, "reviewed_on": version.reviewed_on.date().isoformat(), "status": version.status, "record_version": version.record_version, "source_ids": [source.source_key for source in sources]}


async def create_sport_article(session: AsyncSession, payload: dict[str, Any]) -> SportKnowledgeArticle:
    sport_code = str(payload.get("sport_code", "")).strip().lower()
    slug = str(payload.get("slug", "")).strip().lower()
    if sport_code not in SUPPORTED_TRAINING_SPORTS:
        raise ValueError("unsupported sport code")
    if not slug or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in slug):
        raise ValueError("slug must contain only lowercase letters, numbers and hyphens")
    existing = await session.scalar(select(SportKnowledgeArticle).where(SportKnowledgeArticle.sport_code == sport_code, SportKnowledgeArticle.slug == slug))
    if existing:
        raise ValueError("article slug already exists for this sport")
    title = str(payload.get("title", "")).strip()
    if not title:
        raise ValueError("article title is required")
    now = _now()
    article = SportKnowledgeArticle(id=uuid7(), sport_code=sport_code, slug=slug, latest_version=1, archived=False)
    session.add(article)
    session.add(SportKnowledgeArticleVersion(
        article_id=article.id, content_version=1,
        category=str(payload.get("category", "foundations")).strip() or "foundations",
        title=title, summary=str(payload.get("summary", "Draft athlete education article.")).strip(),
        icon=str(payload.get("icon", "book-open")).strip() or "book-open",
        audiences=list(payload.get("audiences") or ["all"]), events=list(payload.get("events") or []),
        sections=list(payload.get("sections") or [{"heading": "Draft", "body": ["Add reviewed content before publishing."], "source_ids": []}]),
        medical_disclaimer=str(payload.get("medical_disclaimer", "Educational information only; not medical diagnosis or individualized treatment.")).strip(),
        reviewed_on=_reviewed(payload.get("reviewed_on") or date.today()), status="draft",
        created_at=now, updated_at=now, record_version=1,
    ))
    await session.commit()
    return article


async def publish_sport_content(session: AsyncSession, sport_code: str, *, actor: UUID | None, title: str, subtitle: str, medical_disclaimer: str) -> dict[str, Any]:
    articles = (await session.scalars(select(SportKnowledgeArticle).where(SportKnowledgeArticle.sport_code == sport_code, SportKnowledgeArticle.archived.is_(False)).with_for_update())).all()
    if not articles:
        raise ValueError("sport has no knowledge articles")
    manifest: dict[str, int] = {}
    for article in articles:
        version = await session.get(SportKnowledgeArticleVersion, (article.id, article.latest_version))
        if version is None or version.status not in {"draft", "in_review", "published"}:
            raise ValueError(f"{article.slug} has no publishable latest version")
        links = (await session.scalars(select(SportKnowledgeArticleSource).where(SportKnowledgeArticleSource.article_id == article.id, SportKnowledgeArticleSource.article_version == version.content_version))).all()
        if not links:
            raise ValueError(f"{article.slug} requires at least one evidence source")
        if not version.sections or not version.medical_disclaimer:
            raise ValueError(f"{article.slug} is missing content or its safety boundary")
        if article.published_version and article.published_version != version.content_version:
            previous = await session.get(SportKnowledgeArticleVersion, (article.id, article.published_version))
            if previous:
                previous.status = "retired"
        version.status = "published"
        version.updated_at = _now()
        article.published_version = version.content_version
        manifest[article.slug] = version.content_version
    current = await session.scalar(select(SportKnowledgeRelease).where(SportKnowledgeRelease.sport_code == sport_code, SportKnowledgeRelease.status == "published").with_for_update())
    if current:
        current.status = "retired"
    release_version = int(await session.scalar(select(func.coalesce(func.max(SportKnowledgeRelease.release_version), 0)).where(SportKnowledgeRelease.sport_code == sport_code)) or 0) + 1
    content_hash = _hash({"sport_code": sport_code, "title": title, "subtitle": subtitle, "medical_disclaimer": medical_disclaimer, "manifest": manifest})
    session.add(SportKnowledgeRelease(id=uuid7(), sport_code=sport_code, release_version=release_version, title=title, subtitle=subtitle, medical_disclaimer=medical_disclaimer, article_manifest=manifest, content_hash=content_hash, status="published", published_at=_now(), published_by=actor))
    await session.commit()
    return {"release_version": release_version, "article_count": len(manifest), "content_hash": content_hash}


async def create_draft_version(session: AsyncSession, article_id: UUID) -> SportKnowledgeArticleVersion:
    article = await session.scalar(select(SportKnowledgeArticle).where(SportKnowledgeArticle.id == article_id).with_for_update())
    if article is None:
        raise LookupError("article not found")
    source = await session.get(SportKnowledgeArticleVersion, (article.id, article.latest_version))
    assert source is not None
    version_number = article.latest_version + 1
    now = _now()
    draft = SportKnowledgeArticleVersion(article_id=article.id, content_version=version_number, category=source.category, title=source.title, summary=source.summary, icon=source.icon, audiences=source.audiences, events=source.events, sections=source.sections, medical_disclaimer=source.medical_disclaimer, reviewed_on=source.reviewed_on, status="draft", created_at=now, updated_at=now, record_version=1)
    session.add(draft)
    links = (await session.scalars(select(SportKnowledgeArticleSource).where(SportKnowledgeArticleSource.article_id == article.id, SportKnowledgeArticleSource.article_version == source.content_version))).all()
    for link in links:
        session.add(SportKnowledgeArticleSource(article_id=article.id, article_version=version_number, source_id=link.source_id))
    article.latest_version = version_number
    article.version += 1
    await session.commit()
    return draft


async def update_draft_version(session: AsyncSession, article_id: UUID, version_number: int, payload: dict[str, Any]) -> SportKnowledgeArticleVersion:
    row = await session.scalar(select(SportKnowledgeArticleVersion).where(SportKnowledgeArticleVersion.article_id == article_id, SportKnowledgeArticleVersion.content_version == version_number).with_for_update())
    if row is None:
        raise LookupError("article version not found")
    if row.status != "draft":
        raise ValueError("only draft article versions can be edited")
    expected = payload.get("expected_record_version")
    if expected is not None and expected != row.record_version:
        raise ValueError("article version changed; refresh before saving")
    for field in ("category", "title", "summary", "icon", "audiences", "events", "sections", "medical_disclaimer"):
        if field in payload:
            setattr(row, field, payload[field])
    if "reviewed_on" in payload:
        row.reviewed_on = _reviewed(payload["reviewed_on"])
    if not row.title.strip() or not row.summary.strip() or not row.sections:
        raise ValueError("title, summary and at least one section are required")
    source_keys = payload.get("source_ids")
    if source_keys is not None:
        sources = (await session.scalars(select(SportKnowledgeSource).where(SportKnowledgeSource.source_key.in_(set(source_keys))))).all()
        if len(sources) != len(set(source_keys)):
            raise ValueError("one or more source IDs do not exist")
        await session.execute(delete(SportKnowledgeArticleSource).where(SportKnowledgeArticleSource.article_id == article_id, SportKnowledgeArticleSource.article_version == version_number))
        for source in sources:
            session.add(SportKnowledgeArticleSource(article_id=article_id, article_version=version_number, source_id=source.id))
    row.updated_at = _now(); row.record_version += 1
    await session.commit()
    return row
