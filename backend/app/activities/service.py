from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import AthleteProfile
from backend.app.core.problems import ProblemError
from backend.app.operations.outbox import enqueue_event
from backend.app.competition.models import CompetitiveProfile
from .models import Activity, ActivityClubAttribution, ActivityQuality
from .schemas import ActivityStart, ActivityTransition, ActivityView

TRANSITIONS = {"recording": {"paused", "finishing"}, "paused": {"recording", "finishing"}, "finishing": {"uploaded"}, "uploaded": {"processing"}, "processing": {"provisional", "rejected"}, "provisional": {"complete", "rejected"}, "complete": {"processing"}, "rejected": {"processing"}}


async def athlete_id(session: AsyncSession, user_id: UUID) -> UUID:
    value = await session.scalar(select(AthleteProfile.id).where(AthleteProfile.user_id == user_id))
    if value is None: raise ProblemError(409, "onboarding_required", "Onboarding required", "Complete onboarding first.")
    return value


async def view(session: AsyncSession, row: Activity) -> ActivityView:
    quality = await session.scalar(select(ActivityQuality).where(ActivityQuality.activity_id == row.id).order_by(ActivityQuality.created_at.desc()))
    return ActivityView(id=row.id, status=row.status, visibility=row.visibility, started_at=row.started_at, ended_at=row.ended_at, elapsed_seconds=row.elapsed_seconds, moving_seconds=row.moving_seconds, distance_m=float(row.distance_m) if row.distance_m is not None else None, average_pace_s_per_km=float(row.average_pace_s_per_km) if row.average_pace_s_per_km is not None else None, competition_eligible=quality.competition_eligible if quality else None, processing_message="Runlete is verifying GPS and road matches." if row.status in {"uploaded", "processing", "provisional"} else None, version=row.version)


async def start(session: AsyncSession, user_id: UUID, command: ActivityStart, *, source_identity: str) -> ActivityView:
    athlete = await athlete_id(session, user_id)
    existing = await session.scalar(
        select(Activity).where(
            Activity.athlete_id == athlete,
            Activity.source == "runlete",
            Activity.source_identity == source_identity,
        )
    )
    if existing: return await view(session, existing)
    row = Activity(athlete_id=athlete, source="runlete", source_identity=source_identity, started_at=command.started_at, visibility=command.visibility, surface=command.surface, distance_source="device_smoothed_gps")
    session.add(row)
    await session.flush()
    competitive = await session.scalar(select(CompetitiveProfile).where(CompetitiveProfile.athlete_id == athlete))
    session.add(
        ActivityClubAttribution(
            activity_id=row.id,
            athlete_id=athlete,
            club_id=competitive.primary_club_id if competitive else None,
            attributed_at=datetime.now(timezone.utc),
        )
    )
    await enqueue_event(session, aggregate_type="activity", aggregate_id=row.id, event_type="activity.recording.started", payload={"activity_id": str(row.id)})
    await session.commit()
    return await view(session, row)


async def transition(session: AsyncSession, user_id: UUID, activity_id: UUID, target: str, command: ActivityTransition) -> ActivityView:
    athlete = await athlete_id(session, user_id)
    row = await session.scalar(select(Activity).where(Activity.id == activity_id, Activity.athlete_id == athlete).with_for_update())
    if row is None: raise ProblemError(404, "activity_not_found", "Activity not found", "The activity does not exist.")
    if row.version != command.expected_version: raise ProblemError(409, "version_conflict", "Version conflict", "Reload the activity and try again.")
    if target not in TRANSITIONS.get(row.status, set()): raise ProblemError(409, "invalid_activity_transition", "Invalid activity state", f"Cannot move from {row.status} to {target}.")
    row.status = target; row.version += 1
    if command.ended_at: row.ended_at = command.ended_at
    if target == "finishing" and command.device_distance_m is not None:
        row.device_distance_m = command.device_distance_m
    if target == "uploaded": await enqueue_event(session, aggregate_type="activity", aggregate_id=row.id, event_type="activity.uploaded", payload={"activity_id": str(row.id), "athlete_id": str(athlete)})
    await session.commit(); return await view(session, row)
