from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import AthleteProfile
from backend.app.core.database import get_session
from backend.app.core.pagination import decode_cursor, encode_cursor
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from backend.app.identity.models import User
from backend.app.maps.models import Route
from backend.app.operations.outbox import enqueue_event

from .models import Challenge, ChallengeEntry, ClubMembership, Race, RaceEntry
from .service import athlete_id

router = APIRouter(tags=["competition"])


def _active_club_ids(athlete: UUID):
    return select(ClubMembership.club_id).where(
        ClubMembership.athlete_id == athlete,
        ClubMembership.status == "active",
    )


@router.get("/challenges")
async def challenges(
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    athlete = await athlete_id(session, user_id)
    now = datetime.now(timezone.utc)
    query = select(Challenge).where(
        Challenge.status.in_(["scheduled", "active"]),
        Challenge.ends_at > now,
        or_(
            and_(Challenge.club_id.is_(None), Challenge.visibility == "public"),
            Challenge.club_id.in_(_active_club_ids(athlete)),
        ),
    )
    if cursor:
        starts_at, challenge_id = decode_cursor(cursor)
        query = query.where(
            or_(Challenge.starts_at > starts_at, and_(Challenge.starts_at == starts_at, Challenge.id > challenge_id))
        )
    fetched = (
        await session.scalars(query.order_by(Challenge.starts_at.asc(), Challenge.id.asc()).limit(limit + 1))
    ).all()
    rows = fetched[:limit]
    actor_entries = (
        await session.scalars(
            select(ChallengeEntry).where(
                ChallengeEntry.athlete_id == athlete,
                ChallengeEntry.challenge_id.in_([row.id for row in rows]),
            )
        )
    ).all() if rows else []
    entries_by_challenge = {entry.challenge_id: entry for entry in actor_entries}
    return {
        "items": [
            {
                "id": row.id,
                "club_id": row.club_id,
                "name": row.name,
                "challenge_type": row.challenge_type,
                "target": row.rules_json.get("target"),
                "target_unit": row.rules_json.get("unit"),
                "starts_at": row.starts_at,
                "ends_at": row.ends_at,
                "joined": row.id in entries_by_challenge,
                "progress": float(entries_by_challenge[row.id].progress_value) if row.id in entries_by_challenge else None,
                "result_status": entries_by_challenge[row.id].result_status if row.id in entries_by_challenge else None,
            }
            for row in rows
        ],
        "next_cursor": encode_cursor(rows[-1].starts_at, rows[-1].id) if len(fetched) > limit else None,
    }


@router.post("/challenges/{challenge_id}/join", status_code=204, response_class=Response)
async def join_challenge(
    challenge_id: UUID,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    athlete = await athlete_id(session, user_id)
    challenge = await session.get(Challenge, challenge_id, with_for_update=True)
    if challenge is None:
        raise ProblemError(404, "challenge_not_found", "Challenge not found", "The challenge does not exist.")
    now = datetime.now(timezone.utc)
    if challenge.status not in {"scheduled", "active"} or challenge.ends_at <= now:
        raise ProblemError(409, "challenge_not_open", "Challenge unavailable", "This challenge is not accepting entries.")
    if challenge.club_id:
        membership = await session.scalar(
            select(ClubMembership.id).where(
                ClubMembership.club_id == challenge.club_id,
                ClubMembership.athlete_id == athlete,
                ClubMembership.status == "active",
            )
        )
        if membership is None:
            raise ProblemError(403, "club_membership_required", "Membership required", "Join the club before entering this challenge.")
    elif challenge.visibility != "public":
        raise ProblemError(403, "challenge_not_visible", "Challenge unavailable", "This challenge is not visible to the athlete.")
    result = await session.execute(
        pg_insert(ChallengeEntry)
        .values(challenge_id=challenge_id, athlete_id=athlete, progress_value=0, result_status="provisional")
        .on_conflict_do_nothing(index_elements=["challenge_id", "athlete_id"])
        .returning(ChallengeEntry.id)
    )
    entry_id = result.scalar_one_or_none()
    if entry_id:
        await enqueue_event(
            session,
            topic="competition",
            event_type="challenge.entry.created",
            aggregate_type="challenge_entry",
            aggregate_id=entry_id,
            payload={"challenge_id": str(challenge_id), "athlete_id": str(athlete)},
        )
    await session.commit()
    return Response(status_code=204)


@router.get("/races")
async def races(
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    athlete = await athlete_id(session, user_id)
    query = (
        select(Race, Route.distance_m)
        .join(Route, Route.id == Race.route_id)
        .where(
            Race.status.in_(["scheduled", "active"]),
            Race.result_cutoff_at > datetime.now(timezone.utc),
            or_(Race.club_id.is_(None), Race.club_id.in_(_active_club_ids(athlete))),
        )
    )
    if cursor:
        starts_at, race_id = decode_cursor(cursor)
        query = query.where(or_(Race.starts_at > starts_at, and_(Race.starts_at == starts_at, Race.id > race_id)))
    fetched = (
        await session.execute(query.order_by(Race.starts_at.asc(), Race.id.asc()).limit(limit + 1))
    ).all()
    rows = fetched[:limit]
    joined = set(
        await session.scalars(
            select(RaceEntry.race_id).where(
                RaceEntry.athlete_id == athlete,
                RaceEntry.status == "registered",
                RaceEntry.race_id.in_([row.id for row, _ in rows]),
            )
        )
    ) if rows else set()
    return {
        "items": [
            {
                "id": row.id,
                "club_id": row.club_id,
                "name": row.name,
                "starts_at": row.starts_at,
                "result_cutoff_at": row.result_cutoff_at,
                "route_distance_m": float(distance_m),
                "participant_capacity": row.capacity,
                "joined": row.id in joined,
            }
            for row, distance_m in rows
        ],
        "next_cursor": encode_cursor(rows[-1][0].starts_at, rows[-1][0].id) if len(fetched) > limit else None,
    }


@router.post("/races/{race_id}/join", status_code=204, response_class=Response)
async def join_race(
    race_id: UUID,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    athlete = await athlete_id(session, user_id)
    race = await session.get(Race, race_id, with_for_update=True)
    if race is None:
        raise ProblemError(404, "race_not_found", "Race not found", "The race does not exist.")
    now = datetime.now(timezone.utc)
    registration_end = race.starts_at + timedelta(minutes=race.start_window_minutes)
    if race.status not in {"scheduled", "active"} or registration_end <= now:
        raise ProblemError(409, "race_not_open", "Race unavailable", "Registration for this race is closed.")
    if race.club_id:
        membership = await session.scalar(
            select(ClubMembership.id).where(
                ClubMembership.club_id == race.club_id,
                ClubMembership.athlete_id == athlete,
                ClubMembership.status == "active",
            )
        )
        if membership is None:
            raise ProblemError(403, "club_membership_required", "Membership required", "Join the club before entering this race.")
    profile_and_user = (
        await session.execute(
            select(AthleteProfile, User)
            .join(User, User.id == AthleteProfile.user_id)
            .where(AthleteProfile.id == athlete)
        )
    ).one()
    profile, user = profile_and_user
    eligibility = race.eligibility_json or {}
    if user.birth_date:
        today = date.today()
        age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month, user.birth_date.day))
        minimum_age = int(eligibility.get("minimum_age", 16))
        maximum_age = eligibility.get("maximum_age")
        if age < minimum_age or (maximum_age is not None and age > int(maximum_age)):
            raise ProblemError(403, "race_age_ineligible", "Not eligible", "The athlete does not meet this race's age requirement.")
    required_level = eligibility.get("competition_level", "any")
    if required_level != "any" and profile.competition_level != required_level:
        raise ProblemError(403, "race_level_ineligible", "Not eligible", "The athlete does not meet this race's competition-level requirement.")
    registered = await session.scalar(
        select(func.count()).select_from(RaceEntry).where(RaceEntry.race_id == race_id, RaceEntry.status == "registered")
    )
    existing = await session.scalar(
        select(RaceEntry.id).where(RaceEntry.race_id == race_id, RaceEntry.athlete_id == athlete)
    )
    if existing is None and int(registered or 0) >= race.capacity:
        raise ProblemError(409, "race_capacity_reached", "Race full", "This race has reached participant capacity.")
    result = await session.execute(
        pg_insert(RaceEntry)
        .values(race_id=race_id, athlete_id=athlete, status="registered")
        .on_conflict_do_nothing(index_elements=["race_id", "athlete_id"])
        .returning(RaceEntry.id)
    )
    entry_id = result.scalar_one_or_none()
    if entry_id:
        await enqueue_event(
            session,
            topic="competition",
            event_type="race.entry.created",
            aggregate_type="race_entry",
            aggregate_id=entry_id,
            payload={"race_id": str(race_id), "athlete_id": str(athlete)},
        )
    await session.commit()
    return Response(status_code=204)
