from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.models import Activity, ActivityClubAttribution, ActivityQuality
from backend.app.athletes.models import AthleteProfile
from backend.app.maps.models import SegmentEffort, StreetEdge
from backend.app.operations.outbox import enqueue_event

from .models import (
    Challenge,
    ChallengeEntry,
    LeaderboardFact,
    Season,
    TerritoryControlHistory,
)


def activity_period_codes(started_at: datetime, season_code: str | None = None) -> tuple[str, ...]:
    iso_year, iso_week, _ = started_at.isocalendar()
    values = ["all_time", f"week:{iso_year}-W{iso_week:02d}", f"month:{started_at:%Y-%m}"]
    if season_code:
        values.append(f"season:{season_code}")
    return tuple(values)


async def project_activity_leaderboard_facts(session: AsyncSession, activity: Activity) -> None:
    """Rebuild one activity's additive facts; retries and edits cannot double-count."""

    await session.execute(
        delete(LeaderboardFact).where(
            LeaderboardFact.source_type == "activity",
            LeaderboardFact.source_id == activity.id,
        )
    )
    quality = await session.scalar(
        select(ActivityQuality).where(
            ActivityQuality.activity_id == activity.id,
            ActivityQuality.computation_version == activity.computation_version,
        )
    )
    if activity.status != "complete" or quality is None:
        return
    attribution = await session.scalar(
        select(ActivityClubAttribution).where(ActivityClubAttribution.activity_id == activity.id)
    )
    profile = await session.get(AthleteProfile, activity.athlete_id)
    season = await session.scalar(
        select(Season).where(
            Season.starts_on <= activity.started_at.date(),
            Season.ends_on >= activity.started_at.date(),
        )
    )
    eligible = bool(quality.competition_eligible and activity.visibility != "private")
    metric_values = {
        "distance_m": float(activity.distance_m or 0),
        "moving_seconds": float(activity.moving_seconds or 0),
        "run_count": 1.0,
    }
    for period_code in activity_period_codes(activity.started_at, season.code if season else None):
        for metric_code, value in metric_values.items():
            session.add(
                LeaderboardFact(
                    source_type="activity",
                    source_id=activity.id,
                    athlete_id=activity.athlete_id,
                    club_id=attribution.club_id if attribution else None,
                    region_id=profile.region_id if profile else None,
                    metric_code=metric_code,
                    period_code=period_code,
                    value=value,
                    eligible=eligible,
                    visibility=activity.visibility,
                )
            )


async def _eligible_activities(
    session: AsyncSession,
    challenge: Challenge,
    entry: ChallengeEntry,
) -> list[Activity]:
    participation_start = max(challenge.starts_at, entry.created_at)
    query = (
        select(Activity)
        .join(
            ActivityQuality,
            (ActivityQuality.activity_id == Activity.id)
            & (ActivityQuality.computation_version == Activity.computation_version),
        )
        .where(
            Activity.athlete_id == entry.athlete_id,
            Activity.status == "complete",
            Activity.started_at >= participation_start,
            Activity.started_at < challenge.ends_at,
            ActivityQuality.competition_eligible.is_(True),
            Activity.distance_m >= float(challenge.rules_json.get("minimum_activity_distance_m") or 0),
        )
    )
    if challenge.club_id:
        query = query.join(
            ActivityClubAttribution,
            ActivityClubAttribution.activity_id == Activity.id,
        ).where(
            ActivityClubAttribution.club_id == challenge.club_id,
            Activity.visibility.in_(("public", "club")),
        )
    else:
        query = query.where(Activity.visibility == "public")
    return list(await session.scalars(query.order_by(Activity.started_at, Activity.id)))


async def _challenge_progress(
    session: AsyncSession,
    challenge: Challenge,
    entry: ChallengeEntry,
    activities: list[Activity],
) -> float:
    if not activities:
        return 0.0
    if challenge.challenge_type == "distance":
        return sum(float(row.distance_m or 0) for row in activities)
    if challenge.challenge_type == "duration":
        return sum(float(row.moving_seconds or 0) for row in activities)
    if challenge.challenge_type == "run_count":
        return float(len(activities))
    if challenge.challenge_type == "consistency":
        timezone_name = "UTC"
        if challenge.club_id:
            from .models import Club

            club = await session.get(Club, challenge.club_id)
            timezone_name = club.timezone if club else "UTC"
        else:
            profile = await session.get(AthleteProfile, entry.athlete_id)
            timezone_name = profile.timezone if profile else "UTC"
        try:
            zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            zone = timezone.utc
        return float(len({row.started_at.astimezone(zone).date() for row in activities}))
    activity_ids = [row.id for row in activities]
    if challenge.challenge_type == "fastest_segment":
        segment_id = challenge.rules_json.get("segment_id")
        if not segment_id:
            return 0.0
        value = await session.scalar(
            select(func.min(SegmentEffort.elapsed_seconds)).where(
                SegmentEffort.activity_id.in_(activity_ids),
                SegmentEffort.segment_id == UUID(str(segment_id)),
                SegmentEffort.quality_passed.is_(True),
            )
        )
        return float(value or 0)
    if challenge.challenge_type == "territory_gain":
        rows = (
            await session.execute(
                select(TerritoryControlHistory.edge_id, StreetEdge.length_m)
                .join(StreetEdge, StreetEdge.id == TerritoryControlHistory.edge_id)
                .where(
                    TerritoryControlHistory.reason_activity_id.in_(activity_ids),
                    TerritoryControlHistory.controller_type == "athlete",
                    TerritoryControlHistory.new_controller_id == entry.athlete_id,
                    TerritoryControlHistory.event_type.in_(("claim", "loss")),
                )
            )
        ).all()
        # Count each road edge once per challenge, even if it is lost and reclaimed.
        return sum(float(length) for _, length in {edge_id: length for edge_id, length in rows}.items())
    return 0.0


async def recompute_challenge_entries_for_athlete(session: AsyncSession, athlete_id: UUID) -> None:
    rows = (
        await session.execute(
            select(ChallengeEntry, Challenge)
            .join(Challenge, Challenge.id == ChallengeEntry.challenge_id)
            .where(
                ChallengeEntry.athlete_id == athlete_id,
                Challenge.status.in_(("scheduled", "active", "completed")),
            )
            .with_for_update()
        )
    ).all()
    now = datetime.now(timezone.utc)
    for entry, challenge in rows:
        activities = await _eligible_activities(session, challenge, entry)
        previous = float(entry.progress_value)
        progress = await _challenge_progress(session, challenge, entry, activities)
        entry.progress_value = progress
        entry.result_status = "verified"
        entry.version += 1
        target = challenge.rules_json.get("target")
        completed_now = target is not None and progress >= float(target)
        completed_before = target is not None and previous >= float(target)
        if completed_now and not completed_before:
            await enqueue_event(
                session,
                topic="competition",
                event_type="challenge.milestone.completed",
                aggregate_type="challenge_entry",
                aggregate_id=entry.id,
                payload={
                    "challenge_id": str(challenge.id),
                    "athlete_id": str(athlete_id),
                    "progress": progress,
                    "completed_at": now.isoformat(),
                },
            )
