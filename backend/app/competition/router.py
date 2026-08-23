from uuid import UUID

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from backend.app.core.pagination import decode_cursor, decode_numeric_cursor, encode_cursor, encode_numeric_cursor
from backend.app.athletes.models import AthleteProfile
from backend.app.identity.models import User
from backend.app.core.security import hash_secret, random_token
from backend.app.operations.models import AuditEvent
from backend.app.operations.outbox import enqueue_event
from backend.app.maps.models import Route, Segment
from .models import Achievement, Challenge, ChallengeEntry, Club, ClubBan, ClubInvitation, ClubMembership, LeaderboardSnapshot, Race, RaceEntry, RaceResult, SystemActivityEvent
from .policies import require_club_role
from .leaderboards import current_period_code, metric_code as canonical_metric_code
from .schemas import (
    BanCommand,
    ClubCreate,
    ClubStatusCommand,
    ClubUpdate,
    ClubView,
    ChallengeCreate,
    InvitationCreate,
    MembershipDecision,
    MembershipMutationCommand,
    MembershipRoleCommand,
    OwnershipTransferCommand,
    PrimaryClubCommand,
    RaceCreate,
)
from .service import athlete_id, club_view, create_club, decide_membership, join_club, select_primary

router = APIRouter(prefix="/clubs", tags=["clubs"])


@router.get("")
async def discover(q: str | None = None, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); query = select(Club).where(Club.status == "active")
    if q: query = query.where(Club.name.ilike(f"%{q[:80]}%"))
    rows = (await session.scalars(query.order_by(Club.name).limit(50))).all()
    return {"items": [(await club_view(session, row, athlete)).model_dump() for row in rows], "next_cursor": None}


@router.get("/mine")
async def mine(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id)
    rows = (await session.scalars(select(Club).join(ClubMembership).where(ClubMembership.athlete_id == athlete, ClubMembership.status == "active").order_by(Club.name))).all()
    return {"items": [(await club_view(session, row, athlete)).model_dump() for row in rows], "next_cursor": None}


@router.post("", response_model=ClubView, status_code=201)
async def create(body: ClubCreate, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ClubView:
    return await create_club(session, user_id, body)


@router.put("/primary", response_model=ClubView)
async def primary(body: PrimaryClubCommand, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ClubView:
    return await select_primary(session, user_id, body)


@router.get("/{club_id}", response_model=ClubView)
async def detail(club_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ClubView:
    club = await session.get(Club, club_id)
    if club is None: raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    return await club_view(session, club, await athlete_id(session, user_id))


@router.patch("/{club_id}", response_model=ClubView)
async def update_club(
    club_id: UUID,
    body: ClubUpdate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ClubView:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin"})
    club = await session.get(Club, club_id, with_for_update=True)
    if club is None:
        raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    if club.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the club and try again.")
    before = {"name": club.name, "visibility": club.visibility, "status": club.status, "version": club.version}
    for field, value in body.model_dump(exclude={"expected_version"}, exclude_none=True).items():
        setattr(club, field, value)
    club.version += 1
    session.add(
        AuditEvent(
            actor_user_id=user_id,
            action="club.updated",
            subject_type="club",
            subject_id=club.id,
            before=before,
            after={"name": club.name, "visibility": club.visibility, "status": club.status, "version": club.version},
            created_at=datetime.now(timezone.utc),
        )
    )
    await enqueue_event(session, aggregate_type="club", aggregate_id=club.id, event_type="club.updated", payload={"club_id": str(club.id)})
    await session.commit()
    return await club_view(session, club, actor)


@router.post("/{club_id}/join", response_model=ClubView)
async def join(club_id: UUID, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ClubView:
    return await join_club(session, user_id, club_id)


@router.post("/{club_id}/memberships/{membership_id}/decision", response_model=ClubView)
async def decide(club_id: UUID, membership_id: UUID, body: MembershipDecision, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ClubView:
    return await decide_membership(session, user_id, club_id, membership_id, body)


@router.post("/{club_id}/membership/cancel", status_code=204)
async def cancel_join_request(
    club_id: UUID,
    body: MembershipMutationCommand,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    actor = await athlete_id(session, user_id)
    row = await session.scalar(
        select(ClubMembership)
        .where(ClubMembership.club_id == club_id, ClubMembership.athlete_id == actor)
        .with_for_update()
    )
    if row is None or row.status != "requested":
        raise ProblemError(409, "membership_not_pending", "No pending request", "There is no pending request to cancel.")
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the membership and try again.")
    row.status = "cancelled"
    row.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.membership.cancelled", payload={"membership_id": str(row.id)})
    await session.commit()


@router.post("/{club_id}/membership/leave", status_code=204)
async def leave_club(
    club_id: UUID,
    body: MembershipMutationCommand,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    actor = await athlete_id(session, user_id)
    row = await session.scalar(
        select(ClubMembership)
        .where(ClubMembership.club_id == club_id, ClubMembership.athlete_id == actor)
        .with_for_update()
    )
    if row is None or row.status != "active":
        raise ProblemError(409, "active_membership_required", "Membership required", "Only active members can leave.")
    if row.role == "owner":
        raise ProblemError(409, "ownership_transfer_required", "Transfer ownership", "Transfer ownership before leaving the club.")
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the membership and try again.")
    row.status = "left"
    row.version += 1
    from .models import CompetitiveProfile
    profile = await session.scalar(select(CompetitiveProfile).where(CompetitiveProfile.athlete_id == actor).with_for_update())
    if profile and profile.primary_club_id == club_id:
        profile.primary_club_id = None
        profile.primary_changed_at = datetime.now(timezone.utc)
        profile.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.membership.left", payload={"membership_id": str(row.id)})
    await session.commit()


@router.patch("/{club_id}/memberships/{membership_id}/role", status_code=204)
async def change_role(club_id: UUID, membership_id: UUID, body: MembershipRoleCommand, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner"})
    row = await session.scalar(select(ClubMembership).where(ClubMembership.id == membership_id, ClubMembership.club_id == club_id).with_for_update())
    if row is None or row.status != "active":
        raise ProblemError(404, "membership_not_found", "Membership not found", "The active membership does not exist.")
    if row.role == "owner":
        raise ProblemError(409, "ownership_transfer_required", "Transfer ownership", "The owner role changes only through ownership transfer.")
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the member and try again.")
    row.role = body.role
    row.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.member.role_changed", payload={"membership_id": str(row.id), "role": row.role})
    await session.commit()


@router.post("/{club_id}/memberships/{membership_id}/remove", status_code=204)
async def remove_member(club_id: UUID, membership_id: UUID, body: MembershipMutationCommand, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin"})
    row = await session.scalar(select(ClubMembership).where(ClubMembership.id == membership_id, ClubMembership.club_id == club_id).with_for_update())
    if row is None:
        raise ProblemError(404, "membership_not_found", "Membership not found", "The membership does not exist.")
    if row.role == "owner":
        raise ProblemError(409, "owner_cannot_be_removed", "Transfer ownership", "Transfer ownership before removing the owner.")
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the member and try again.")
    row.status = "removed"
    row.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.member.removed", payload={"membership_id": str(row.id)})
    await session.commit()


@router.post("/{club_id}/memberships/{membership_id}/ban", status_code=204)
async def ban_member(club_id: UUID, membership_id: UUID, body: BanCommand, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin"})
    row = await session.scalar(select(ClubMembership).where(ClubMembership.id == membership_id, ClubMembership.club_id == club_id).with_for_update())
    if row is None or row.role == "owner":
        raise ProblemError(409, "member_cannot_be_banned", "Unable to ban member", "The membership cannot be banned.")
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the member and try again.")
    existing = await session.scalar(select(ClubBan).where(ClubBan.club_id == club_id, ClubBan.athlete_id == row.athlete_id).with_for_update())
    if existing is None:
        session.add(ClubBan(club_id=club_id, athlete_id=row.athlete_id, banned_by=actor, reason=body.reason, expires_at=body.expires_at))
    else:
        existing.banned_by = actor
        existing.reason = body.reason
        existing.expires_at = body.expires_at
        existing.version += 1
    row.status = "banned"
    row.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.member.banned", payload={"membership_id": str(row.id)})
    await session.commit()


@router.post("/{club_id}/memberships/{membership_id}/unban", status_code=204)
async def unban_member(club_id: UUID, membership_id: UUID, body: MembershipMutationCommand, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin"})
    row = await session.scalar(select(ClubMembership).where(ClubMembership.id == membership_id, ClubMembership.club_id == club_id).with_for_update())
    if row is None:
        raise ProblemError(404, "membership_not_found", "Membership not found", "The membership does not exist.")
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the member and try again.")
    ban = await session.scalar(select(ClubBan).where(ClubBan.club_id == club_id, ClubBan.athlete_id == row.athlete_id).with_for_update())
    if ban:
        await session.delete(ban)
    row.status = "removed"
    row.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.member.unbanned", payload={"membership_id": str(row.id)})
    await session.commit()


@router.get("/{club_id}/invitations")
async def invitations(club_id:UUID,user_id:UUID=Depends(current_user_id),session:AsyncSession=Depends(get_session))->dict:
    from .policies import require_club_role
    actor=await athlete_id(session,user_id);await require_club_role(session,club_id,actor,{"owner","admin"});rows=(await session.scalars(select(ClubInvitation).where(ClubInvitation.club_id==club_id).order_by(ClubInvitation.created_at.desc()).limit(100))).all();return {"items":[{"id":row.id,"expires_at":row.expires_at,"revoked_at":row.revoked_at,"maximum_uses":row.maximum_uses,"use_count":row.use_count} for row in rows],"next_cursor":None}


@router.post("/{club_id}/invitations",status_code=201)
async def create_invitation(club_id: UUID, body: InvitationCreate, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin"})
    raw = random_token(32)
    row = ClubInvitation(club_id=club_id, token_hash=hash_secret(raw, purpose="club-invite"), created_by=actor, expires_at=datetime.now(timezone.utc) + timedelta(days=body.expires_days), maximum_uses=body.maximum_uses, use_count=0)
    session.add(row)
    await session.commit()
    return {"id": row.id, "accept_token": raw, "expires_at": row.expires_at}


@router.delete("/{club_id}/invitations/{invitation_id}",status_code=204)
async def revoke_invitation(club_id:UUID,invitation_id:UUID,idempotency_key:str=Header(alias="Idempotency-Key"),user_id:UUID=Depends(current_user_id),session:AsyncSession=Depends(get_session))->None:
    from datetime import datetime,timezone
    from .policies import require_club_role
    actor=await athlete_id(session,user_id);await require_club_role(session,club_id,actor,{"owner","admin"});row=await session.scalar(select(ClubInvitation).where(ClubInvitation.id==invitation_id,ClubInvitation.club_id==club_id).with_for_update())
    if row:row.revoked_at=datetime.now(timezone.utc);await session.commit()


@router.post("/{club_id}/transfer-ownership",status_code=204)
async def transfer_ownership(club_id: UUID, body: OwnershipTransferCommand, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    actor = await athlete_id(session, user_id)
    owner = await require_club_role(session, club_id, actor, {"owner"})
    target = await session.scalar(select(ClubMembership).where(ClubMembership.id == body.membership_id, ClubMembership.club_id == club_id, ClubMembership.status == "active").with_for_update())
    if target is None:
        raise ProblemError(404, "membership_not_found", "Membership not found", "Choose an active club member.")
    if target.id == owner.id:
        return
    if owner.version != body.owner_expected_version or target.version != body.target_expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the member list and try again.")
    owner.role = "admin"
    owner.version += 1
    await session.flush()
    target.role = "owner"
    target.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.ownership.transferred", payload={"previous_owner_membership_id": str(owner.id), "owner_membership_id": str(target.id)})
    await session.commit()


@router.post("/{club_id}/archive",status_code=204)
async def archive(club_id: UUID, body: ClubStatusCommand, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner"})
    club = await session.get(Club, club_id, with_for_update=True)
    if club is None:
        raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    if club.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the club and try again.")
    club.status = "archived"
    club.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.archived", payload={"club_id": str(club_id)})
    await session.commit()


@router.post("/{club_id}/restore", status_code=204)
async def restore(club_id: UUID, body: ClubStatusCommand, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner"})
    club = await session.get(Club, club_id, with_for_update=True)
    if club is None:
        raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    if club.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the club and try again.")
    club.status = "active"
    club.version += 1
    await enqueue_event(session, aggregate_type="club", aggregate_id=club_id, event_type="club.restored", payload={"club_id": str(club_id)})
    await session.commit()


@router.get("/{club_id}/members")
async def members(club_id: UUID, status: str = "active", user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin", "member"})
    rows = (
        await session.execute(
            select(ClubMembership, AthleteProfile, User)
            .join(AthleteProfile, AthleteProfile.id == ClubMembership.athlete_id)
            .join(User, User.id == AthleteProfile.user_id)
            .where(ClubMembership.club_id == club_id, ClubMembership.status == status)
            .order_by(ClubMembership.joined_at, ClubMembership.id)
            .limit(100)
        )
    ).all()
    return {
        "items": [
            {
                "id": membership.id,
                "user_id": user.id,
                "athlete_id": athlete.id,
                "role": membership.role,
                "status": membership.status,
                "joined_at": membership.joined_at,
                "version": membership.version,
                "athlete": {"id": athlete.id, "name": user.display_name},
            }
            for membership, athlete, user in rows
        ],
        "next_cursor": None,
    }


@router.get("/{club_id}/leaderboards")
async def club_leaderboard(
    club_id: UUID,
    period: str = "week",
    metric: str = "distance",
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    actor = await athlete_id(session, user_id)
    club = await session.get(Club, club_id)
    if club is None or club.status != "active":
        raise ProblemError(404, "club_not_found", "Club not found", "The club is unavailable.")
    membership = await session.scalar(
        select(ClubMembership.id).where(
            ClubMembership.club_id == club_id,
            ClubMembership.athlete_id == actor,
            ClubMembership.status == "active",
        )
    )
    if club.visibility == "private" and membership is None:
        raise ProblemError(403, "club_membership_required", "Membership required", "Join this private club to view its leaderboard.")
    try:
        resolved_period = current_period_code(period)
        resolved_metric = canonical_metric_code(metric)
    except ValueError as exc:
        raise ProblemError(422, "leaderboard_filter_invalid", "Invalid leaderboard filter", str(exc)) from exc
    scope_type = "club" if membership else "club_public"
    row = await session.scalar(
        select(LeaderboardSnapshot)
        .where(
            LeaderboardSnapshot.scope_type == scope_type,
            LeaderboardSnapshot.scope_id == club_id,
            LeaderboardSnapshot.period_code == resolved_period,
            LeaderboardSnapshot.metric_code == resolved_metric,
        )
        .order_by(LeaderboardSnapshot.computed_at.desc())
    )
    entries = [dict(entry, is_me=str(entry.get("athlete_id")) == str(actor)) for entry in (row.entries_json if row else [])]
    return {
        "metric_code": resolved_metric,
        "period_code": resolved_period,
        "items": entries,
        "computed_at": row.computed_at if row else None,
    }


@router.get("/{club_id}/activity")
async def activity_feed(
    club_id: UUID,
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    actor = await athlete_id(session, user_id)
    club = await session.get(Club, club_id)
    if club is None:
        raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    membership = await session.scalar(
        select(ClubMembership).where(
            ClubMembership.club_id == club_id,
            ClubMembership.athlete_id == actor,
            ClubMembership.status == "active",
        )
    )
    if club.visibility == "private" and membership is None:
        raise ProblemError(403, "club_membership_required", "Membership required", "Join this private club to view its activity.")
    query = select(SystemActivityEvent).where(SystemActivityEvent.club_id == club_id)
    if membership is None:
        query = query.where(SystemActivityEvent.visibility == "public")
    if cursor:
        occurred_at, event_id = decode_cursor(cursor)
        query = query.where(
            or_(
                SystemActivityEvent.occurred_at < occurred_at,
                and_(SystemActivityEvent.occurred_at == occurred_at, SystemActivityEvent.id < event_id),
            )
        )
    rows = (
        await session.scalars(
            query.order_by(SystemActivityEvent.occurred_at.desc(), SystemActivityEvent.id.desc()).limit(limit + 1)
        )
    ).all()
    page = rows[:limit]
    next_cursor = encode_cursor(page[-1].occurred_at, page[-1].id) if len(rows) > limit else None
    return {
        "items": [
            {
                "id": row.id,
                "event_type": row.event_type,
                "athlete_id": row.athlete_id,
                "occurred_at": row.occurred_at,
                "payload": row.payload_json,
            }
            for row in page
        ],
        "next_cursor": next_cursor,
    }


@router.get("/{club_id}/challenges")
async def club_challenges(
    club_id: UUID,
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin", "member"})
    query = select(Challenge).where(Challenge.club_id == club_id)
    if cursor:
        starts_at, challenge_id = decode_cursor(cursor)
        query = query.where(
            or_(Challenge.starts_at < starts_at, and_(Challenge.starts_at == starts_at, Challenge.id < challenge_id))
        )
    fetched = (
        await session.scalars(query.order_by(Challenge.starts_at.desc(), Challenge.id.desc()).limit(limit + 1))
    ).all()
    rows = fetched[:limit]
    entry_rows = (
        await session.execute(
            select(ChallengeEntry.challenge_id, func.count(ChallengeEntry.id))
            .where(ChallengeEntry.challenge_id.in_([row.id for row in rows]))
            .group_by(ChallengeEntry.challenge_id)
        )
    ).all() if rows else []
    counts = {challenge_id: int(count) for challenge_id, count in entry_rows}
    actor_entries = (
        await session.scalars(
            select(ChallengeEntry).where(
                ChallengeEntry.challenge_id.in_([row.id for row in rows]),
                ChallengeEntry.athlete_id == actor,
            )
        )
    ).all() if rows else []
    entries_by_challenge = {entry.challenge_id: entry for entry in actor_entries}
    next_cursor = encode_cursor(rows[-1].starts_at, rows[-1].id) if len(fetched) > limit else None
    return {"items": [{"id": row.id, "name": row.name, "challenge_type": row.challenge_type, "metric": row.challenge_type, "target": row.rules_json.get("target"), "target_unit": row.rules_json.get("unit"), "starts_at": row.starts_at, "ends_at": row.ends_at, "status": row.status, "participant_count": counts.get(row.id, 0), "is_joined": row.id in entries_by_challenge, "progress": float(entries_by_challenge[row.id].progress_value) if row.id in entries_by_challenge else None, "result_status": entries_by_challenge[row.id].result_status if row.id in entries_by_challenge else None} for row in rows], "next_cursor": next_cursor}


@router.post("/{club_id}/challenges", status_code=201)
async def create_challenge(
    club_id: UUID,
    body: ChallengeCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin"})
    club = await session.get(Club, club_id)
    if club is None or club.status != "active":
        raise ProblemError(409, "club_inactive", "Club unavailable", "Challenges can only be created for an active club.")
    if body.segment_id:
        segment = await session.get(Segment, body.segment_id)
        if segment is None or segment.status != "active" or segment.visibility != "public":
            raise ProblemError(422, "challenge_segment_invalid", "Segment unavailable", "Select an active public segment.")
    row = Challenge(
        club_id=club_id,
        name=body.name,
        challenge_type=body.challenge_type,
        visibility="club",
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        rules_json=body.canonical_rules(),
        status="scheduled",
    )
    session.add(row)
    await session.flush()
    await enqueue_event(
        session,
        topic="competition",
        event_type="challenge.created",
        aggregate_type="challenge",
        aggregate_id=row.id,
        payload={"challenge_id": str(row.id), "club_id": str(club_id)},
    )
    await session.commit()
    return {"id": row.id, "version": row.version}


@router.get("/{club_id}/races")
async def club_races(
    club_id: UUID,
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin", "member"})
    query = select(Race, Route.distance_m).join(Route, Route.id == Race.route_id).where(Race.club_id == club_id)
    if cursor:
        starts_at, race_id = decode_cursor(cursor)
        query = query.where(or_(Race.starts_at < starts_at, and_(Race.starts_at == starts_at, Race.id < race_id)))
    rows = (
        await session.execute(
            query.order_by(Race.starts_at.desc(), Race.id.desc()).limit(limit + 1)
        )
    ).all()
    page = rows[:limit]
    race_ids = [row.id for row, _ in page]
    count_rows = (
        await session.execute(
            select(RaceEntry.race_id, func.count(RaceEntry.id))
            .where(RaceEntry.race_id.in_(race_ids), RaceEntry.status == "registered")
            .group_by(RaceEntry.race_id)
        )
    ).all() if race_ids else []
    counts = {race_id: int(count) for race_id, count in count_rows}
    joined = set(
        await session.scalars(
            select(RaceEntry.race_id).where(
                RaceEntry.race_id.in_(race_ids),
                RaceEntry.athlete_id == actor,
                RaceEntry.status == "registered",
            )
        )
    ) if race_ids else set()
    next_cursor = encode_cursor(page[-1][0].starts_at, page[-1][0].id) if len(rows) > limit else None
    return {"items": [{"id": row.id, "name": row.name, "starts_at": row.starts_at, "status": row.status, "route_distance_m": float(distance_m), "participant_count": counts.get(row.id, 0), "participant_capacity": row.capacity, "is_joined": row.id in joined} for row, distance_m in page], "next_cursor": next_cursor}


@router.post("/{club_id}/races", status_code=201)
async def create_race(
    club_id: UUID,
    body: RaceCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin"})
    club = await session.get(Club, club_id)
    if club is None or club.status != "active":
        raise ProblemError(409, "club_inactive", "Club unavailable", "Races can only be created for an active club.")
    route = await session.get(Route, body.route_id)
    if route is None or (route.owner_athlete_id != actor and route.visibility != "public"):
        raise ProblemError(422, "race_route_invalid", "Route unavailable", "Use a public route or a route owned by the race creator.")
    if float(route.distance_m) < 400:
        raise ProblemError(422, "race_route_too_short", "Route too short", "Race routes must be at least 400 metres.")
    row = Race(
        club_id=club_id,
        route_id=body.route_id,
        name=body.name,
        timezone=body.timezone,
        starts_at=body.starts_at,
        start_window_minutes=body.start_window_minutes,
        result_cutoff_at=body.result_cutoff_at,
        capacity=body.participant_capacity,
        eligibility_json={"schema_version": 1, **body.eligibility.model_dump()},
        status="scheduled",
    )
    session.add(row)
    await session.flush()
    await enqueue_event(
        session,
        topic="competition",
        event_type="race.created",
        aggregate_type="race",
        aggregate_id=row.id,
        payload={"race_id": str(row.id), "club_id": str(club_id), "route_id": str(body.route_id)},
    )
    await session.commit()
    return {"id": row.id, "version": row.version}


@router.get("/{club_id}/races/{race_id}/results")
async def race_results(
    club_id: UUID,
    race_id: UUID,
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    actor = await athlete_id(session, user_id)
    await require_club_role(session, club_id, actor, {"owner", "admin", "member"})
    race = await session.scalar(select(Race).where(Race.id == race_id, Race.club_id == club_id))
    if race is None:
        raise ProblemError(404, "race_not_found", "Race not found", "The club race does not exist.")
    query = (
        select(RaceResult, User.display_name)
        .join(AthleteProfile, AthleteProfile.id == RaceResult.athlete_id)
        .join(User, User.id == AthleteProfile.user_id)
        .where(RaceResult.race_id == race_id, RaceResult.status == "verified")
    )
    if cursor:
        elapsed, result_id = decode_numeric_cursor(cursor)
        query = query.where(
            or_(
                RaceResult.elapsed_seconds > elapsed,
                and_(RaceResult.elapsed_seconds == elapsed, RaceResult.id > result_id),
            )
        )
    fetched = (
        await session.execute(
            query.order_by(RaceResult.elapsed_seconds.asc(), RaceResult.id.asc()).limit(limit + 1)
        )
    ).all()
    rows = fetched[:limit]
    return {
        "items": [
            {
                "id": result.id,
                "rank": result.rank,
                "athlete_id": result.athlete_id,
                "display_name": display_name,
                "elapsed_seconds": float(result.elapsed_seconds),
                "route_coverage": float(result.route_coverage),
                "status": result.status,
            }
            for result, display_name in rows
        ],
        "next_cursor": (
            encode_numeric_cursor(float(rows[-1][0].elapsed_seconds), rows[-1][0].id)
            if len(fetched) > limit
            else None
        ),
    }


@router.get("/{club_id}/achievements")
async def achievements(
    club_id: UUID,
    cursor: str | None = None,
    limit: int = 20,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    actor = await athlete_id(session, user_id)
    club = await session.get(Club, club_id)
    if club is None:
        raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    membership = await session.scalar(
        select(ClubMembership).where(
            ClubMembership.club_id == club_id,
            ClubMembership.athlete_id == actor,
            ClubMembership.status == "active",
        )
    )
    if club.visibility == "private" and membership is None:
        raise ProblemError(403, "club_membership_required", "Membership required", "Join this private club to view its achievements.")
    query = (
        select(Achievement, User.display_name)
        .join(AthleteProfile, AthleteProfile.id == Achievement.athlete_id)
        .join(User, User.id == AthleteProfile.user_id)
        .where(Achievement.club_id == club_id)
    )
    if membership is None:
        query = query.where(Achievement.visibility == "public")
    if cursor:
        achieved_at, achievement_id = decode_cursor(cursor)
        query = query.where(
            or_(
                Achievement.achieved_at < achieved_at,
                and_(Achievement.achieved_at == achieved_at, Achievement.id < achievement_id),
            )
        )
    rows = (
        await session.execute(
            query.order_by(Achievement.achieved_at.desc(), Achievement.id.desc()).limit(limit + 1)
        )
    ).all()
    page = rows[:limit]
    next_cursor = encode_cursor(page[-1][0].achieved_at, page[-1][0].id) if len(rows) > limit else None
    return {
        "items": [
            {
                "id": row.id,
                "title": row.title,
                "achievement_code": row.achievement_code,
                "awarded_at": row.achieved_at,
                "athlete": {"id": row.athlete_id, "name": display_name},
                "payload": row.payload_json,
            }
            for row, display_name in page
        ],
        "next_cursor": next_cursor,
    }
