from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.problems import ProblemError
from .models import ClubMembership


async def require_club_role(session: AsyncSession, club_id: UUID, athlete_id: UUID, roles: set[str]) -> ClubMembership:
    membership = await session.scalar(select(ClubMembership).where(ClubMembership.club_id == club_id, ClubMembership.athlete_id == athlete_id, ClubMembership.status == "active"))
    if membership is None or membership.role not in roles:
        raise ProblemError(403, "club_permission_denied", "Permission denied", "Your club role cannot perform this action.")
    return membership

