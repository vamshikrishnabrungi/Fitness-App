from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id, hash_secret
from backend.app.operations.outbox import enqueue_event
from .models import ClubBan, ClubInvitation, ClubMembership
from .service import athlete_id

router = APIRouter(prefix="/club-invitations", tags=["clubs"])


@router.post("/{token}/accept", status_code=204)
async def accept(
    token: str,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    athlete = await athlete_id(session, user_id)
    now = datetime.now(timezone.utc)
    row = await session.scalar(
        select(ClubInvitation)
        .where(ClubInvitation.token_hash == hash_secret(token, purpose="club-invite"))
        .with_for_update()
    )
    if row is None or row.revoked_at or row.expires_at <= now or row.use_count >= row.maximum_uses:
        raise ProblemError(410, "invitation_unavailable", "Invitation unavailable", "This invitation is invalid or expired.")
    ban = await session.scalar(
        select(ClubBan).where(ClubBan.club_id == row.club_id, ClubBan.athlete_id == athlete)
    )
    if ban and (ban.expires_at is None or ban.expires_at > now):
        raise ProblemError(403, "club_banned", "Unable to join", "This athlete is banned from the club.")
    member = await session.scalar(
        select(ClubMembership)
        .where(ClubMembership.club_id == row.club_id, ClubMembership.athlete_id == athlete)
        .with_for_update()
    )
    if member is None:
        session.add(
            ClubMembership(
                club_id=row.club_id,
                athlete_id=athlete,
                role="member",
                status="active",
                requested_at=now,
                joined_at=now,
            )
        )
    elif member.status != "active":
        member.status = "active"
        member.role = "member"
        member.joined_at = now
        member.version += 1
    row.use_count += 1
    await enqueue_event(
        session,
        aggregate_type="club",
        aggregate_id=row.club_id,
        event_type="club.invitation.accepted",
        payload={"club_id": str(row.club_id), "athlete_id": str(athlete), "invitation_id": str(row.id)},
    )
    await session.commit()
