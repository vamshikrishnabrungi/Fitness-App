from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.models import Activity, ActivityClubAttribution
from backend.app.maps.models import MatchedEdgeTraversal
from backend.app.operations.outbox import enqueue_event
from .models import TerritoryControlHistory, TerritoryCurrentControl, TerritoryScore
from .territory import DailyTraversal, club_winner, daily_points, personal_winner, strongest_distinct_days

ACTIVE_MATCHER_VERSION = "valhalla-confidence-v1"


def _winner_details(rows: list[DailyTraversal], controller_id: UUID, today: date, *, club: bool) -> tuple[float, float, datetime, datetime]:
    selected = strongest_distinct_days(rows, today)
    if club:
        athlete_totals: dict[UUID, float] = {}
        relevant = [row for row in selected if row.club_id == controller_id]
        for row in relevant:
            athlete_totals[row.athlete_id] = athlete_totals.get(row.athlete_id, 0.0) + daily_points(row, today)
        strongest_athletes = {athlete for athlete, _ in sorted(athlete_totals.items(), key=lambda item: (-item[1], str(item[0])))[:5]}
        relevant = [row for row in relevant if row.athlete_id in strongest_athletes]
    else:
        relevant = [row for row in selected if row.athlete_id == controller_id]
    score = sum(daily_points(row, today) for row in relevant)
    speed = max((row.speed_mps for row in relevant), default=0.0)
    reached = max((row.reached_at for row in relevant), default=datetime.now(timezone.utc))
    last_day = max((row.local_date for row in relevant), default=today)
    expires = datetime.combine(last_day + timedelta(days=28), time.min, timezone.utc)
    return score, speed, reached, expires


async def _upsert_control(
    session: AsyncSession,
    *,
    edge_id: UUID,
    controller_type: str,
    winner: tuple[UUID, float] | None,
    rows: list[DailyTraversal],
    today: date,
    activity_id: UUID | None,
) -> None:
    current = await session.scalar(
        select(TerritoryCurrentControl)
        .where(TerritoryCurrentControl.edge_id == edge_id, TerritoryCurrentControl.controller_type == controller_type)
        .with_for_update()
    )
    if winner is None:
        if current:
            previous = current.athlete_id or current.club_id
            session.add(
                TerritoryControlHistory(
                    edge_id=edge_id,
                    event_type="expiry",
                    controller_type=controller_type,
                    previous_controller_id=previous,
                    new_controller_id=None,
                    score=float(current.score),
                    reason_activity_id=activity_id,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            await session.delete(current)
        return
    winner_id, _ = winner
    score, speed, reached, expires = _winner_details(rows, winner_id, today, club=controller_type == "club")
    previous = (current.athlete_id or current.club_id) if current else None
    previous_score = float(current.score) if current else None
    if current is None:
        current = TerritoryCurrentControl(
            edge_id=edge_id,
            controller_type=controller_type,
            athlete_id=winner_id if controller_type == "athlete" else None,
            club_id=winner_id if controller_type == "club" else None,
            score=score,
            speed_tiebreaker=speed,
            winning_score_reached_at=reached,
            expires_at=expires,
        )
        session.add(current)
    else:
        current.athlete_id = winner_id if controller_type == "athlete" else None
        current.club_id = winner_id if controller_type == "club" else None
        current.score = score
        current.speed_tiebreaker = speed
        current.winning_score_reached_at = reached
        current.expires_at = expires
        current.version += 1
    # Scheduled expiry/rebuild passes must not manufacture repeated defence
    # history.  A defence is meaningful only when a concrete activity increases
    # the incumbent's score; ownership changes and first claims always persist.
    event_type = None
    if previous is None:
        event_type = "claim"
    elif previous != winner_id:
        event_type = "loss"
    elif activity_id is not None and previous_score is not None and score > previous_score + 0.00005:
        event_type = "defence"
    if event_type:
        session.add(
            TerritoryControlHistory(
                edge_id=edge_id,
                event_type=event_type,
                controller_type=controller_type,
                previous_controller_id=previous,
                new_controller_id=winner_id,
                score=score,
                reason_activity_id=activity_id,
                occurred_at=datetime.now(timezone.utc),
            )
        )


async def recompute_edge(session: AsyncSession, edge_id: UUID, *, activity_id: UUID | None = None, today: date | None = None) -> None:
    today = today or datetime.now(timezone.utc).date()
    score_rows = (
        await session.execute(
            select(TerritoryScore, MatchedEdgeTraversal.traversed_at)
            .join(MatchedEdgeTraversal, MatchedEdgeTraversal.id == TerritoryScore.traversal_id)
            .where(
                TerritoryScore.edge_id == edge_id,
                TerritoryScore.local_date >= today - timedelta(days=27),
                TerritoryScore.local_date <= today,
            )
        )
    ).all()
    rows = [
        DailyTraversal(
            athlete_id=score.athlete_id,
            club_id=score.club_id,
            local_date=score.local_date,
            confidence=float(score.confidence),
            coverage=float(score.coverage),
            speed_mps=float(score.speed_mps),
            reached_at=traversed_at,
        )
        for score, traversed_at in score_rows
    ]
    await _upsert_control(session, edge_id=edge_id, controller_type="athlete", winner=personal_winner(rows, today), rows=rows, today=today, activity_id=activity_id)
    await _upsert_control(session, edge_id=edge_id, controller_type="club", winner=club_winner(rows, today), rows=rows, today=today, activity_id=activity_id)


async def project_activity_territory(session: AsyncSession, activity_id: UUID) -> list[UUID]:
    activity = await session.get(Activity, activity_id)
    if activity is None or activity.status != "complete" or activity.visibility == "private":
        return []
    attribution = await session.scalar(select(ActivityClubAttribution).where(ActivityClubAttribution.activity_id == activity.id))
    traversals = (
        await session.scalars(
            select(MatchedEdgeTraversal).where(
                MatchedEdgeTraversal.activity_id == activity.id,
                MatchedEdgeTraversal.qualifies.is_(True),
                MatchedEdgeTraversal.computation_version == ACTIVE_MATCHER_VERSION,
            )
        )
    ).all()
    affected: set[UUID] = set()
    for traversal in traversals:
        score_row = (
            await session.execute(
            select(TerritoryScore, MatchedEdgeTraversal.traversed_at)
            .outerjoin(MatchedEdgeTraversal, MatchedEdgeTraversal.id == TerritoryScore.traversal_id)
            .where(
                TerritoryScore.edge_id == traversal.edge_id,
                TerritoryScore.athlete_id == activity.athlete_id,
                TerritoryScore.local_date == traversal.local_date,
            )
            .with_for_update(of=TerritoryScore)
            )
        ).first()
        score = score_row[0] if score_row else None
        candidate = (100.0 * float(traversal.confidence) * float(traversal.coverage), float(traversal.speed_mps), -traversal.traversed_at.timestamp())
        if score is None:
            session.add(
                TerritoryScore(
                    edge_id=traversal.edge_id,
                    athlete_id=activity.athlete_id,
                    club_id=attribution.club_id if attribution else None,
                    traversal_id=traversal.id,
                    local_date=traversal.local_date,
                    confidence=traversal.confidence,
                    coverage=traversal.coverage,
                    speed_mps=traversal.speed_mps,
                    base_points=candidate[0],
                )
            )
        else:
            existing_reached_at = score_row[1] or score.created_at
            existing = (float(score.base_points), float(score.speed_mps), -existing_reached_at.timestamp())
            if candidate > existing:
                score.club_id = attribution.club_id if attribution else None
                score.traversal_id = traversal.id
                score.confidence = traversal.confidence
                score.coverage = traversal.coverage
                score.speed_mps = traversal.speed_mps
                score.base_points = candidate[0]
                score.version += 1
        affected.add(traversal.edge_id)
    await session.flush()
    for edge_id in sorted(affected, key=str):
        await recompute_edge(session, edge_id, activity_id=activity.id)
    # This is also the hand-off to the club timeline and achievement projector.
    # A valid visible run must reach that projector even when map matching found
    # no territory-eligible edge.
    await enqueue_event(
        session,
        topic="competition",
        event_type="territory.activity.projected",
        aggregate_type="activity",
        aggregate_id=activity.id,
        payload={"activity_id": str(activity.id), "edge_ids": [str(edge) for edge in sorted(affected, key=str)]},
    )
    await session.commit()
    return sorted(affected, key=str)


async def release_activity_territory(session: AsyncSession, activity_id: UUID) -> list[UUID]:
    traversals = (await session.scalars(select(MatchedEdgeTraversal).where(MatchedEdgeTraversal.activity_id == activity_id))).all()
    affected = sorted({row.edge_id for row in traversals}, key=str)
    await session.execute(delete(TerritoryScore).where(TerritoryScore.traversal_id.in_([row.id for row in traversals])))
    for edge_id in affected:
        await recompute_edge(session, edge_id, activity_id=activity_id)
    await session.commit()
    return affected
