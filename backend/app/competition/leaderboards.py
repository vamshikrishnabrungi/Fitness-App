from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import AthleteProfile
from backend.app.identity.models import PrivacySettings, User

from .models import ClubMembership, LeaderboardFact, LeaderboardSnapshot
from .progress import activity_period_codes

COMPUTATION_VERSION = "additive-facts-v1"
METRIC_ALIASES = {
    "distance": "distance_m",
    "distance_m": "distance_m",
    "duration": "moving_seconds",
    "moving_time": "moving_seconds",
    "moving_seconds": "moving_seconds",
    "runs": "run_count",
    "run_count": "run_count",
}


def current_period_code(period: str, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if period in {"all", "all_time"}:
        return "all_time"
    if period.startswith(("week:", "month:", "season:")):
        return period
    codes = activity_period_codes(now)
    if period in {"week", "weekly"}:
        return codes[1]
    if period in {"month", "monthly"}:
        return codes[2]
    raise ValueError("unsupported leaderboard period")


def metric_code(metric: str) -> str:
    try:
        return METRIC_ALIASES[metric]
    except KeyError as exc:
        raise ValueError("unsupported leaderboard metric") from exc


async def rebuild_club_snapshot(
    session: AsyncSession,
    *,
    club_id: UUID,
    metric: str,
    period: str,
    public_only: bool,
) -> LeaderboardSnapshot:
    query = (
        select(
            LeaderboardFact.athlete_id,
            User.display_name,
            func.sum(LeaderboardFact.value).label("total"),
        )
        .join(AthleteProfile, AthleteProfile.id == LeaderboardFact.athlete_id)
        .join(User, User.id == AthleteProfile.user_id)
        .join(PrivacySettings, PrivacySettings.user_id == User.id)
        .join(
            ClubMembership,
            (ClubMembership.club_id == club_id)
            & (ClubMembership.athlete_id == LeaderboardFact.athlete_id)
            & (ClubMembership.status == "active"),
        )
        .where(
            LeaderboardFact.club_id == club_id,
            LeaderboardFact.metric_code == metric,
            LeaderboardFact.period_code == period,
            LeaderboardFact.eligible.is_(True),
        )
    )
    if public_only:
        query = query.where(
            LeaderboardFact.visibility == "public",
            PrivacySettings.public_leaderboards.is_(True),
        )
    else:
        query = query.where(LeaderboardFact.visibility.in_(("public", "club")))
    rows = (
        await session.execute(
            query.group_by(LeaderboardFact.athlete_id, User.display_name)
            .order_by(func.sum(LeaderboardFact.value).desc(), LeaderboardFact.athlete_id.asc())
            .limit(500)
        )
    ).all()
    entries: list[dict] = []
    prior_value: float | None = None
    prior_rank = 0
    for position, (athlete_id, display_name, total) in enumerate(rows, start=1):
        value = float(total)
        rank = prior_rank if prior_value == value else position
        entries.append(
            {
                "rank": rank,
                "athlete_id": str(athlete_id),
                "club_id": str(club_id),
                "display_name": display_name,
                "value": value,
            }
        )
        prior_value, prior_rank = value, rank
    snapshot = LeaderboardSnapshot(
        scope_type="club_public" if public_only else "club",
        scope_id=club_id,
        metric_code=metric,
        period_code=period,
        entries_json=entries,
        computed_at=datetime.now(timezone.utc),
        computation_version=COMPUTATION_VERSION,
    )
    session.add(snapshot)
    return snapshot


async def rebuild_activity_club_snapshots(
    session: AsyncSession,
    club_id: UUID,
    started_at: datetime,
) -> None:
    for period in activity_period_codes(started_at):
        for metric in ("distance_m", "moving_seconds", "run_count"):
            await rebuild_club_snapshot(
                session,
                club_id=club_id,
                metric=metric,
                period=period,
                public_only=False,
            )
            await rebuild_club_snapshot(
                session,
                club_id=club_id,
                metric=metric,
                period=period,
                public_only=True,
            )
