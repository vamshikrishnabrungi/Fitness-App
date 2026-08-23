from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

import anyio
from sqlalchemy import select

from backend.app.core.config import get_settings
from backend.app.core.database import SessionFactory
from backend.app.operations.models import OutboxEvent


async def publish_outbox_ids(event_ids: tuple[UUID, ...]) -> int:
    settings = get_settings()
    if not event_ids or not settings.gcp_project_id:
        return 0
    async with SessionFactory() as session:
        rows = (
            await session.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.id.in_(event_ids), OutboxEvent.published_at.is_(None))
                .order_by(OutboxEvent.created_at)
            )
        ).all()
    if not rows:
        return 0

    def publish() -> None:
        from google.cloud import pubsub_v1

        publisher = pubsub_v1.PublisherClient()
        futures = []
        for row in rows:
            topic = publisher.topic_path(
                settings.gcp_project_id,
                f"runlete-{settings.environment}-{row.topic}",
            )
            futures.append(
                publisher.publish(
                    topic,
                    json.dumps({"event_id": str(row.id)}, separators=(",", ":")).encode(),
                    event_type=row.event_type,
                    aggregate_type=row.aggregate_type,
                )
            )
        for future in futures:
            future.result(timeout=20)

    try:
        await anyio.to_thread.run_sync(publish)
    except Exception as exc:
        async with SessionFactory() as session:
            failed = (
                await session.scalars(select(OutboxEvent).where(OutboxEvent.id.in_(event_ids)))
            ).all()
            for row in failed:
                row.attempts += 1
                row.last_error = type(exc).__name__[:120]
            await session.commit()
        return 0

    async with SessionFactory() as session:
        published = (
            await session.scalars(select(OutboxEvent).where(OutboxEvent.id.in_(event_ids)))
        ).all()
        now = datetime.now(timezone.utc)
        for row in published:
            if row.published_at is None:
                row.published_at = now
                row.attempts += 1
                row.last_error = None
        await session.commit()
    return len(rows)
