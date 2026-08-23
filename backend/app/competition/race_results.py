from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.models import Activity, ActivityQuality
from backend.app.maps.models import Route
from backend.app.moderation.models import CompetitionFlag
from backend.app.operations.outbox import enqueue_event

from .models import Race, RaceEntry, RaceResult

ROUTE_COVERAGE_THRESHOLD = 0.90
ENDPOINT_TOLERANCE_M = 100.0


def race_evidence_passes(
    *,
    competition_eligible: bool,
    unresolved_flag: bool,
    within_schedule: bool,
    route_coverage: float,
    start_distance_m: float,
    end_distance_m: float,
) -> bool:
    return (
        competition_eligible
        and not unresolved_flag
        and within_schedule
        and route_coverage >= ROUTE_COVERAGE_THRESHOLD
        and start_distance_m <= ENDPOINT_TOLERANCE_M
        and end_distance_m <= ENDPOINT_TOLERANCE_M
    )


async def create_provisional_race_results(session: AsyncSession, activity: Activity) -> None:
    entries = (
        await session.execute(
            select(RaceEntry, Race)
            .join(Race, Race.id == RaceEntry.race_id)
            .where(
                RaceEntry.athlete_id == activity.athlete_id,
                RaceEntry.status == "registered",
                Race.status.in_(("scheduled", "active")),
                Race.starts_at <= activity.started_at,
                Race.result_cutoff_at >= activity.started_at,
            )
        )
    ).all()
    for entry, race in entries:
        if activity.started_at > race.starts_at + timedelta(minutes=race.start_window_minutes):
            continue
        existing = await session.scalar(
            select(RaceResult).where(
                (RaceResult.race_id == race.id)
                & ((RaceResult.athlete_id == activity.athlete_id) | (RaceResult.activity_id == activity.id))
            )
        )
        if existing is not None:
            if existing.activity_id != activity.id:
                continue
            result = existing
            result.status = "provisional"
            result.rank = None
            result.version += 1
        else:
            result = RaceResult(
                race_id=race.id,
                athlete_id=activity.athlete_id,
                activity_id=activity.id,
                elapsed_seconds=float(activity.elapsed_seconds or 0),
                route_coverage=0,
                status="provisional",
            )
            session.add(result)
            await session.flush()
        await enqueue_event(
            session,
            topic="competition",
            event_type="race.result.verify.requested",
            aggregate_type="race_result",
            aggregate_id=result.id,
            payload={"race_id": str(race.id), "activity_id": str(activity.id)},
        )


async def _route_evidence(
    session: AsyncSession,
    activity: Activity,
    route: Route,
) -> tuple[float, float, float]:
    if activity.route_geometry is None:
        return 0.0, float("inf"), float("inf")
    activity_metric = func.ST_Transform(activity.route_geometry, 3857)
    route_metric = func.ST_Transform(route.geometry, 3857)
    coverage = func.least(
        1.0,
        func.ST_Length(func.ST_Intersection(route_metric, func.ST_Buffer(activity_metric, 25.0)))
        / func.nullif(route.distance_m, 0),
    )
    values = (
        await session.execute(
            select(
                coverage,
                func.ST_Distance(func.ST_StartPoint(activity_metric), func.ST_StartPoint(route_metric)),
                func.ST_Distance(func.ST_EndPoint(activity_metric), func.ST_EndPoint(route_metric)),
            )
        )
    ).one()
    return float(values[0] or 0), float(values[1] or 0), float(values[2] or 0)


async def _recompute_ranks(session: AsyncSession, race_id: UUID) -> None:
    rows = (
        await session.scalars(
            select(RaceResult)
            .where(RaceResult.race_id == race_id, RaceResult.status == "verified")
            .order_by(RaceResult.elapsed_seconds.asc(), RaceResult.created_at.asc(), RaceResult.id.asc())
            .with_for_update()
        )
    ).all()
    prior_time: float | None = None
    prior_rank = 0
    for position, row in enumerate(rows, start=1):
        elapsed = float(row.elapsed_seconds)
        rank = prior_rank if prior_time == elapsed else position
        row.rank = rank
        prior_time, prior_rank = elapsed, rank


async def verify_race_result(session: AsyncSession, result_id: UUID) -> None:
    result = await session.get(RaceResult, result_id, with_for_update=True)
    if result is None or result.status in {"verified", "rejected"}:
        return
    activity = await session.get(Activity, result.activity_id)
    race = await session.get(Race, result.race_id)
    if activity is None or race is None:
        result.status = "rejected"
        return
    route = await session.get(Route, race.route_id)
    quality = await session.scalar(
        select(ActivityQuality).where(
            ActivityQuality.activity_id == activity.id,
            ActivityQuality.computation_version == activity.computation_version,
        )
    )
    unresolved_flag = await session.scalar(
        select(CompetitionFlag.id).where(
            CompetitionFlag.subject_type == "activity",
            CompetitionFlag.subject_id == activity.id,
            CompetitionFlag.status.in_(("open", "under_review", "appealed")),
        )
    )
    coverage, start_distance, end_distance = (
        await _route_evidence(session, activity, route) if route else (0.0, float("inf"), float("inf"))
    )
    result.route_coverage = coverage
    result.elapsed_seconds = float(activity.elapsed_seconds or 0)
    within_schedule = (
        race.starts_at <= activity.started_at <= race.starts_at + timedelta(minutes=race.start_window_minutes)
        and activity.ended_at is not None
        and activity.ended_at <= race.result_cutoff_at
    )
    passed = race_evidence_passes(
        competition_eligible=bool(
            activity.status == "complete"
            and activity.visibility != "private"
            and quality is not None
            and quality.competition_eligible
        ),
        unresolved_flag=unresolved_flag is not None,
        within_schedule=within_schedule,
        route_coverage=coverage,
        start_distance_m=start_distance,
        end_distance_m=end_distance,
    )
    result.status = "verified" if passed else "rejected"
    result.rank = None
    result.version += 1
    await _recompute_ranks(session, race.id)
    await enqueue_event(
        session,
        topic="competition",
        event_type=f"race.result.{result.status}",
        aggregate_type="race_result",
        aggregate_id=result.id,
        payload={
            "race_id": str(race.id),
            "activity_id": str(activity.id),
            "athlete_id": str(activity.athlete_id),
            "coverage": coverage,
            "start_distance_m": start_distance,
            "end_distance_m": end_distance,
        },
    )
