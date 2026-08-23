"""Cross-scope leaderboards: solo/global, city, city-vs-city, country-vs-country.

Live aggregations over competition.leaderboard_facts. Facts carry athlete_id,
club_id and region_id, so every scope is a grouped SUM with tie-aware ranking.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import AthleteProfile
from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from backend.app.identity.models import PrivacySettings, User
from backend.app.maps.models import GeographicRegion

from .leaderboards import current_period_code, metric_code as canonical_metric_code
from .models import Club, LeaderboardFact

router = APIRouter(prefix="/leaderboards", tags=["leaderboards"])

COUNTRY_NAMES = {
    "US": "United States", "GB": "United Kingdom", "FR": "France", "DE": "Germany",
    "ES": "Spain", "IT": "Italy", "IN": "India", "AU": "Australia", "CA": "Canada",
    "JP": "Japan", "MC": "Monaco", "NL": "Netherlands", "BR": "Brazil", "KE": "Kenya",
}


def _resolve(metric: str, period: str) -> tuple[str, str]:
    try:
        return canonical_metric_code(metric), current_period_code(period)
    except ValueError as exc:
        raise ProblemError(422, "leaderboard_filter_invalid", "Invalid leaderboard filter", str(exc)) from exc


def _rank(rows: list[dict]) -> list[dict]:
    ranked: list[dict] = []
    prior_value: float | None = None
    prior_rank = 0
    for position, row in enumerate(rows, start=1):
        value = float(row["value"])
        rank = prior_rank if prior_value == value else position
        ranked.append({**row, "rank": rank, "value": value})
        prior_value, prior_rank = value, rank
    return ranked


async def _actor_athlete(session: AsyncSession, user_id: UUID) -> UUID | None:
    return await session.scalar(select(AthleteProfile.id).where(AthleteProfile.user_id == user_id))


def _base(metric: str, period: str):
    return (
        LeaderboardFact.metric_code == metric,
        LeaderboardFact.period_code == period,
        LeaderboardFact.eligible.is_(True),
        LeaderboardFact.visibility == "public",
    )


async def _athlete_rows(session: AsyncSession, metric: str, period: str, *, region_id: UUID | None):
    query = (
        select(LeaderboardFact.athlete_id, User.display_name, func.sum(LeaderboardFact.value))
        .join(AthleteProfile, AthleteProfile.id == LeaderboardFact.athlete_id)
        .join(User, User.id == AthleteProfile.user_id)
        .join(PrivacySettings, PrivacySettings.user_id == User.id)
        .where(*_base(metric, period), LeaderboardFact.athlete_id.isnot(None), PrivacySettings.public_leaderboards.is_(True))
        .group_by(LeaderboardFact.athlete_id, User.display_name)
        .order_by(func.sum(LeaderboardFact.value).desc(), LeaderboardFact.athlete_id.asc())
        .limit(100)
    )
    if region_id is not None:
        query = query.where(LeaderboardFact.region_id == region_id)
    return (await session.execute(query)).all()


async def _club_rows(session: AsyncSession, metric: str, period: str, *, region_id: UUID | None):
    query = (
        select(LeaderboardFact.club_id, Club.name, Club.emoji, func.sum(LeaderboardFact.value))
        .join(Club, Club.id == LeaderboardFact.club_id)
        .where(*_base(metric, period), LeaderboardFact.club_id.isnot(None), Club.status == "active")
        .group_by(LeaderboardFact.club_id, Club.name, Club.emoji)
        .order_by(func.sum(LeaderboardFact.value).desc(), LeaderboardFact.club_id.asc())
        .limit(100)
    )
    if region_id is not None:
        query = query.where(LeaderboardFact.region_id == region_id)
    return (await session.execute(query)).all()


@router.get("/global")
async def global_leaderboard(
    metric: str = Query("distance"),
    period: str = Query("week"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    m, p = _resolve(metric, period)
    me = await _actor_athlete(session, user_id)
    rows = await _athlete_rows(session, m, p, region_id=None)
    items = _rank([
        {"athlete_id": str(aid), "display_name": name, "value": total, "is_me": aid == me}
        for aid, name, total in rows
    ])
    return {"scope": "global", "subject": "athlete", "metric_code": m, "period_code": p, "items": items}


@router.get("/regions/{region_id}")
async def region_leaderboard(
    region_id: UUID,
    subject: str = Query("athlete", pattern="^(athlete|club)$"),
    metric: str = Query("distance"),
    period: str = Query("week"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    m, p = _resolve(metric, period)
    region = await session.get(GeographicRegion, region_id)
    if region is None:
        raise ProblemError(404, "region_not_found", "Region not found", "The region does not exist.")
    if subject == "club":
        rows = await _club_rows(session, m, p, region_id=region_id)
        items = _rank([
            {"club_id": str(cid), "display_name": name, "emoji": emoji, "value": total}
            for cid, name, emoji, total in rows
        ])
    else:
        me = await _actor_athlete(session, user_id)
        rows = await _athlete_rows(session, m, p, region_id=region_id)
        items = _rank([
            {"athlete_id": str(aid), "display_name": name, "value": total, "is_me": aid == me}
            for aid, name, total in rows
        ])
    return {"scope": "region", "subject": subject, "region_id": str(region_id),
            "region_name": region.name, "metric_code": m, "period_code": p, "items": items}


@router.get("/cities")
async def cities_leaderboard(
    metric: str = Query("distance"),
    period: str = Query("week"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    m, p = _resolve(metric, period)
    rows = (await session.execute(
        select(GeographicRegion.id, GeographicRegion.name, GeographicRegion.country_code, func.sum(LeaderboardFact.value))
        .select_from(LeaderboardFact)
        .join(GeographicRegion, GeographicRegion.id == LeaderboardFact.region_id)
        .where(*_base(m, p), GeographicRegion.region_type == "city")
        .group_by(GeographicRegion.id, GeographicRegion.name, GeographicRegion.country_code)
        .order_by(func.sum(LeaderboardFact.value).desc())
        .limit(100)
    )).all()
    items = _rank([
        {"region_id": str(rid), "display_name": name, "country_code": cc, "value": total}
        for rid, name, cc, total in rows
    ])
    return {"scope": "cities", "subject": "city", "metric_code": m, "period_code": p, "items": items}


@router.get("/countries")
async def countries_leaderboard(
    metric: str = Query("distance"),
    period: str = Query("week"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    m, p = _resolve(metric, period)
    rows = (await session.execute(
        select(GeographicRegion.country_code, func.sum(LeaderboardFact.value))
        .select_from(LeaderboardFact)
        .join(GeographicRegion, GeographicRegion.id == LeaderboardFact.region_id)
        .where(*_base(m, p))
        .group_by(GeographicRegion.country_code)
        .order_by(func.sum(LeaderboardFact.value).desc())
        .limit(100)
    )).all()
    items = _rank([
        {"country_code": cc, "display_name": COUNTRY_NAMES.get(cc, cc), "value": total}
        for cc, total in rows
    ])
    return {"scope": "countries", "subject": "country", "metric_code": m, "period_code": p, "items": items}
