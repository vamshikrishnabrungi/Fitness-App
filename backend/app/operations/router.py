from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import require_roles
from .models import ConsumerReceipt, OutboxEvent

router = APIRouter(prefix="/operations", tags=["operations"])


@router.post("/events/{event_id}/consume/{consumer_code}", status_code=204, include_in_schema=False)
async def claim_event(event_id: UUID, consumer_code: str, session: AsyncSession = Depends(get_session)) -> None:
    event = await session.get(OutboxEvent, event_id)
    if event is None: raise ProblemError(404, "event_not_found", "Event not found", "The event does not exist.")
    existing = await session.scalar(select(ConsumerReceipt).where(ConsumerReceipt.event_id == event.id, ConsumerReceipt.consumer_code == consumer_code))
    if existing: return
    now = datetime.now(timezone.utc)
    session.add(ConsumerReceipt(event_id=event.id, consumer_code=consumer_code, status="complete", started_at=now, completed_at=now))
    await session.commit()
