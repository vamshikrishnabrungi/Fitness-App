from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.app.athletes.models import AthleteProfile
from backend.app.core.problems import ProblemError
from backend.app.operations.models import AuditEvent
from backend.app.operations.outbox import enqueue_event
from .models import Club, ClubBan, ClubMembership, CompetitiveProfile
from .policies import require_club_role
from .schemas import ClubCreate, ClubView, MembershipDecision, PrimaryClubCommand


async def athlete_id(session: AsyncSession, user_id: UUID) -> UUID:
    value = await session.scalar(select(AthleteProfile.id).where(AthleteProfile.user_id == user_id))
    if value is None: raise ProblemError(409, "onboarding_required", "Onboarding required", "Complete onboarding first.")
    return value


async def club_view(session: AsyncSession, club: Club, athlete_id: UUID) -> ClubView:
    membership = await session.scalar(select(ClubMembership).where(ClubMembership.club_id == club.id, ClubMembership.athlete_id == athlete_id))
    competitive = await session.scalar(select(CompetitiveProfile).where(CompetitiveProfile.athlete_id == athlete_id))
    member_count = await session.scalar(
        select(func.count()).select_from(ClubMembership).where(
            ClubMembership.club_id == club.id,
            ClubMembership.status == "active",
        )
    )
    return ClubView(id=club.id, name=club.name, slug=club.slug, description=club.description, rules=club.rules, visibility=club.visibility, timezone=club.timezone, primary_color=club.primary_color, secondary_color=club.secondary_color, status=club.status, membership_status=membership.status if membership else None, membership_role=membership.role if membership else None, is_primary=bool(competitive and competitive.primary_club_id == club.id), member_count=int(member_count or 0), competitive_profile_version=competitive.version if competitive else 1, version=club.version)


async def create_club(session: AsyncSession, user_id: UUID, body: ClubCreate) -> ClubView:
    athlete = await athlete_id(session, user_id)
    now = datetime.now(timezone.utc)
    club = Club(**body.model_dump(), status="active")
    session.add(club); await session.flush()
    membership = ClubMembership(club_id=club.id, athlete_id=athlete, role="owner", status="active", requested_at=now, joined_at=now)
    session.add(membership)
    session.add(AuditEvent(actor_user_id=user_id, action="club.created", subject_type="club", subject_id=club.id, before=None, after={"name": club.name, "slug": club.slug}, created_at=now))
    await enqueue_event(session, aggregate_type="club", aggregate_id=club.id, event_type="club.created", payload={"club_id": str(club.id), "owner_athlete_id": str(athlete)})
    try: await session.commit()
    except IntegrityError as exc:
        await session.rollback(); raise ProblemError(409, "club_slug_exists", "Club already exists", "Choose a different club slug.") from exc
    return await club_view(session, club, athlete)


async def join_club(session: AsyncSession, user_id: UUID, club_id: UUID) -> ClubView:
    athlete = await athlete_id(session, user_id); now = datetime.now(timezone.utc)
    club = await session.get(Club, club_id)
    if club is None or club.status != "active": raise ProblemError(404, "club_not_found", "Club not found", "The club is unavailable.")
    ban = await session.scalar(select(ClubBan).where(ClubBan.club_id == club.id, ClubBan.athlete_id == athlete))
    if ban and (ban.expires_at is None or ban.expires_at > now): raise ProblemError(403, "club_banned", "Unable to join", "This athlete is banned from the club.")
    membership = await session.scalar(select(ClubMembership).where(ClubMembership.club_id == club.id, ClubMembership.athlete_id == athlete).with_for_update())
    target = "active" if club.visibility == "public" else "requested"
    if membership and membership.status in {"active", "requested"}: return await club_view(session, club, athlete)
    if membership:
        membership.status = target; membership.requested_at = now; membership.joined_at = now if target == "active" else None; membership.role = "member"; membership.version += 1
    else:
        # Two mobile retries can both observe no row. PostgreSQL arbitrates that
        # race without exposing a uniqueness error to the athlete.
        result = await session.execute(
            pg_insert(ClubMembership)
            .values(
                club_id=club.id,
                athlete_id=athlete,
                role="member",
                status=target,
                requested_at=now,
                joined_at=now if target == "active" else None,
            )
            .on_conflict_do_nothing(index_elements=["club_id", "athlete_id"])
        )
        if not result.rowcount:
            await session.commit()
            return await club_view(session, club, athlete)
    await enqueue_event(session, aggregate_type="club", aggregate_id=club.id, event_type=f"club.membership.{target}", payload={"club_id": str(club.id), "athlete_id": str(athlete)})
    await session.commit(); return await club_view(session, club, athlete)


async def decide_membership(session: AsyncSession, user_id: UUID, club_id: UUID, membership_id: UUID, body: MembershipDecision) -> ClubView:
    actor = await athlete_id(session, user_id); await require_club_role(session, club_id, actor, {"owner", "admin"})
    member = await session.scalar(select(ClubMembership).where(ClubMembership.id == membership_id, ClubMembership.club_id == club_id).with_for_update())
    if member is None: raise ProblemError(404, "membership_not_found", "Membership not found", "The request does not exist.")
    if member.version != body.expected_version: raise ProblemError(409, "version_conflict", "Version conflict", "Reload the membership and try again.")
    if member.status != "requested": raise ProblemError(409, "membership_not_pending", "Request already decided", "Only pending requests can be decided.")
    member.status = "active" if body.approve else "rejected"; member.decided_by = actor; member.joined_at = datetime.now(timezone.utc) if body.approve else None; member.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.membership.decided", payload={"membership_id": str(member.id), "approved": body.approve})
    await session.commit(); return await club_view(session, await session.get(Club, club_id), member.athlete_id)


async def select_primary(session: AsyncSession, user_id: UUID, body: PrimaryClubCommand) -> ClubView:
    athlete = await athlete_id(session, user_id); now = datetime.now(timezone.utc)
    membership = await session.scalar(select(ClubMembership).where(ClubMembership.club_id == body.club_id, ClubMembership.athlete_id == athlete, ClubMembership.status == "active"))
    if membership is None: raise ProblemError(409, "primary_club_membership_required", "Membership required", "Join the club before making it primary.")
    profile = await session.scalar(select(CompetitiveProfile).where(CompetitiveProfile.athlete_id == athlete).with_for_update())
    if profile is None:
        profile = CompetitiveProfile(athlete_id=athlete); session.add(profile); await session.flush()
    if profile.primary_club_id == body.club_id:
        return await club_view(session, await session.get(Club, body.club_id), athlete)
    if profile.version != body.expected_version: raise ProblemError(409, "version_conflict", "Version conflict", "Reload club settings and try again.")
    if profile.primary_changed_at and profile.primary_changed_at > now - timedelta(days=7): raise ProblemError(409, "primary_club_cooldown", "Primary club cooldown", "Primary club can be changed once every seven days.")
    previous = profile.primary_club_id; profile.primary_club_id = body.club_id; profile.primary_changed_at = now; profile.version += 1
    await enqueue_event(session, aggregate_type="competitive_profile", aggregate_id=profile.id, event_type="club.primary.changed", payload={"athlete_id": str(athlete), "previous_club_id": str(previous) if previous else None, "club_id": str(body.club_id)})
    await session.commit(); return await club_view(session, await session.get(Club, body.club_id), athlete)
