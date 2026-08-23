from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class DailyTraversal:
    athlete_id: UUID
    club_id: UUID | None
    local_date: date
    confidence: float
    coverage: float
    speed_mps: float
    reached_at: datetime


def daily_points(row: DailyTraversal, today: date) -> float:
    age_days = max(0, (today - row.local_date).days)
    return 100.0 * row.confidence * row.coverage * math.pow(0.5, age_days / 14.0)


def strongest_distinct_days(rows: list[DailyTraversal], today: date) -> list[DailyTraversal]:
    eligible = [r for r in rows if 0 <= (today - r.local_date).days < 28 and r.confidence >= .85 and r.coverage >= .80]
    best: dict[tuple[UUID, date], DailyTraversal] = {}
    for row in eligible:
        key = (row.athlete_id, row.local_date)
        current = best.get(key)
        if current is None or (daily_points(row, today), row.speed_mps, -row.reached_at.timestamp()) > (daily_points(current, today), current.speed_mps, -current.reached_at.timestamp()): best[key] = row
    by_athlete: dict[UUID, list[DailyTraversal]] = {}
    for row in best.values(): by_athlete.setdefault(row.athlete_id, []).append(row)
    output: list[DailyTraversal] = []
    for values in by_athlete.values(): output.extend(sorted(values, key=lambda x: (daily_points(x, today), x.speed_mps), reverse=True)[:7])
    return output


def personal_winner(rows: list[DailyTraversal], today: date) -> tuple[UUID, float] | None:
    totals: dict[UUID, float] = {}
    speeds: dict[UUID, float] = {}
    reached: dict[UUID, datetime] = {}
    for row in strongest_distinct_days(rows, today):
        totals[row.athlete_id] = totals.get(row.athlete_id, 0) + daily_points(row, today)
        speeds[row.athlete_id] = max(speeds.get(row.athlete_id, 0), row.speed_mps)
        # A controller reaches its aggregate score only when the latest of its
        # contributing daily efforts has occurred.  This timestamp is the final
        # deterministic tie-breaker after score and speed.
        reached[row.athlete_id] = max(reached.get(row.athlete_id, row.reached_at), row.reached_at)
    if not totals: return None
    winner = min(totals, key=lambda athlete: (-totals[athlete], -speeds[athlete], reached[athlete], str(athlete)))
    return winner, totals[winner]


def club_winner(rows: list[DailyTraversal], today: date) -> tuple[UUID, float] | None:
    selected = strongest_distinct_days(rows, today)
    athlete_totals: dict[tuple[UUID, UUID], float] = {}
    athlete_speeds: dict[tuple[UUID, UUID], float] = {}
    athlete_reached: dict[tuple[UUID, UUID], datetime] = {}
    for row in selected:
        if row.club_id:
            key = (row.club_id, row.athlete_id)
            athlete_totals[key] = athlete_totals.get(key, 0) + daily_points(row, today)
            athlete_speeds[key] = max(athlete_speeds.get(key, 0), row.speed_mps)
            athlete_reached[key] = max(athlete_reached.get(key, row.reached_at), row.reached_at)
    clubs: dict[UUID, list[tuple[float, float, datetime, UUID]]] = {}
    for (club_id, athlete_id), score in athlete_totals.items():
        clubs.setdefault(club_id, []).append(
            (score, athlete_speeds[(club_id, athlete_id)], athlete_reached[(club_id, athlete_id)], athlete_id)
        )
    strongest = {
        club_id: sorted(values, key=lambda value: (-value[0], -value[1], value[2], str(value[3])))[:5]
        for club_id, values in clubs.items()
    }
    totals = {club_id: sum(value[0] for value in values) for club_id, values in strongest.items()}
    if not totals: return None
    speeds = {club_id: max((value[1] for value in values), default=0.0) for club_id, values in strongest.items()}
    reached = {club_id: max(value[2] for value in values) for club_id, values in strongest.items()}
    winner = min(totals, key=lambda club: (-totals[club], -speeds[club], reached[club], str(club)))
    return winner, totals[winner]
