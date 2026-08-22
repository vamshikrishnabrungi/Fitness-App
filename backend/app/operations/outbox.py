from __future__ import annotations

from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.ids import uuid7
from .models import OutboxEvent


request_outbox_events: ContextVar[tuple[UUID, ...]] = ContextVar("request_outbox_events", default=())
ALLOWED_TOPICS = frozenset(
    {"activity", "territory", "training", "nutrition", "health", "club", "competition", "notifications", "maintenance"}
)


async def enqueue_event(
    session: AsyncSession,
    *,
    topic: str | None = None,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID,
    payload: dict[str, Any],
) -> OutboxEvent:
    resolved_topic = topic or event_type.split(".", 1)[0]
    if resolved_topic not in ALLOWED_TOPICS:
        raise ValueError(f"Unsupported outbox topic: {resolved_topic}")
    event = OutboxEvent(
        id=uuid7(),
        topic=resolved_topic,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        created_at=datetime.now(timezone.utc),
    )
    session.add(event)
    request_outbox_events.set((*request_outbox_events.get(), event.id))
    return event
