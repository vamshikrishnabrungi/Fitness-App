"""Dev-only local outbox drainer for club/competition domain events.

Replaces the GCP Pub/Sub push subscription that is unavailable in this
environment. Projects unpublished club/competition events into the read models
(activity feed, notifications, achievements, leaderboards) and marks them
published. Run on demand: python backend/dev_drain_outbox.py
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402
from backend.app.core.database import SessionFactory  # noqa: E402
from backend.app.operations.models import OutboxEvent  # noqa: E402
from backend.app.competition.event_projection import project_domain_event  # noqa: E402

PROJECTED_TOPICS = {"club", "competition"}


async def main():
    projected = 0
    async with SessionFactory() as session:
        rows = (
            await session.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None), OutboxEvent.topic.in_(PROJECTED_TOPICS))
                .order_by(OutboxEvent.created_at)
            )
        ).all()
        for event in rows:
            await project_domain_event(session, event)  # commits internally
            fresh = await session.get(OutboxEvent, event.id)
            fresh.published_at = datetime.now(timezone.utc)
            fresh.attempts += 1
            await session.commit()
            projected += 1
    print(f"projected {projected} club/competition events")


asyncio.run(main())
