from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session, model_dict
from backend.app.core.security import current_user_id, require_roles
from backend.app.knowledge.models import SportKnowledgeSource
from backend.app.core.ids import uuid7
from backend.app.knowledge.sport_content_service import (
    admin_article_detail,
    admin_sport_content,
    create_sport_article,
    create_draft_version,
    publish_sport_content,
    update_draft_version,
)

router = APIRouter(prefix="/sport-content", tags=["admin-sport-content"])


@router.post("/articles", dependencies=[Depends(require_roles("content_editor", "platform_admin"))])
async def create_article(body: dict, session: AsyncSession = Depends(get_session)) -> dict:
    try:
        article = await create_sport_article(session, body)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    result = await admin_article_detail(session, article.id)
    assert result is not None
    return result


@router.get("/{sport_code}")
async def list_content(sport_code: str, session: AsyncSession = Depends(get_session)) -> dict:
    return await admin_sport_content(session, sport_code)


@router.get("/articles/{article_id}")
async def article_detail(article_id: UUID, version: int | None = None, session: AsyncSession = Depends(get_session)) -> dict:
    result = await admin_article_detail(session, article_id, version)
    if result is None:
        raise HTTPException(404, "Sport knowledge article not found")
    return result


@router.post("/articles/{article_id}/versions", dependencies=[Depends(require_roles("content_editor", "platform_admin"))])
async def new_version(article_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    try:
        row = await create_draft_version(session, article_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"article_id": row.article_id, "content_version": row.content_version, "status": row.status, "record_version": row.record_version}


@router.put("/articles/{article_id}/versions/{version}", dependencies=[Depends(require_roles("content_editor", "platform_admin"))])
async def save_version(article_id: UUID, version: int, body: dict, session: AsyncSession = Depends(get_session)) -> dict:
    try:
        await update_draft_version(session, article_id, version, body)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    result = await admin_article_detail(session, article_id, version)
    assert result is not None
    return result


@router.get("/sources/all")
async def list_sources(session: AsyncSession = Depends(get_session)) -> dict:
    rows = (await session.scalars(select(SportKnowledgeSource).order_by(SportKnowledgeSource.publication_year.desc(), SportKnowledgeSource.title))).all()
    return {"items": [model_dict(row) for row in rows]}


@router.post("/sources", dependencies=[Depends(require_roles("content_editor", "platform_admin"))])
async def create_source(body: dict, session: AsyncSession = Depends(get_session)) -> dict:
    source_key = str(body.get("source_key", "")).strip().lower()
    canonical_url = str(body.get("canonical_url", "")).strip()
    if not source_key or not canonical_url or not str(body.get("title", "")).strip():
        raise HTTPException(422, "source key, title and canonical URL are required")
    if await session.scalar(select(SportKnowledgeSource).where((SportKnowledgeSource.source_key == source_key) | (SportKnowledgeSource.canonical_url == canonical_url))):
        raise HTTPException(409, "source key or canonical URL already exists")
    row = SportKnowledgeSource(
        id=uuid7(), source_key=source_key, title=str(body["title"]).strip(), canonical_url=canonical_url,
        publication_year=int(body.get("publication_year", 2026)), source_kind=str(body.get("source_kind", "guideline")).strip(),
        editorial_note=str(body.get("editorial_note", "")).strip(),
    )
    session.add(row)
    await session.commit()
    return model_dict(row)


@router.put("/sources/{source_id}", dependencies=[Depends(require_roles("content_editor", "platform_admin"))])
async def update_source(source_id: UUID, body: dict, session: AsyncSession = Depends(get_session)) -> dict:
    row = await session.scalar(select(SportKnowledgeSource).where(SportKnowledgeSource.id == source_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Source not found")
    if body.get("expected_version") != row.version:
        raise HTTPException(409, "Source changed; refresh before saving")
    for field in ("title", "canonical_url", "publication_year", "source_kind", "editorial_note"):
        if field in body:
            setattr(row, field, body[field])
    row.version += 1
    await session.commit()
    return model_dict(row)


@router.post("/{sport_code}/publish", dependencies=[Depends(require_roles("content_publisher", "platform_admin"))])
async def publish(sport_code: str, body: dict, actor: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    try:
        return await publish_sport_content(session, sport_code, actor=actor, title=str(body.get("title", sport_code.title())), subtitle=str(body.get("subtitle", "")), medical_disclaimer=str(body.get("medical_disclaimer", "")))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
