from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import exp
from typing import Any, Dict, List, Optional, Sequence

from backend.activity_domain import haversine_m, parse_datetime


def activity_effort(activity: Dict[str, Any], max_heart_rate: Optional[int] = None) -> float:
    moving_minutes = float(activity.get("moving_time_sec") or 0) / 60.0
    average_hr = activity.get("average_heart_rate")
    if average_hr and max_heart_rate and max_heart_rate > 0:
        intensity = max(0.35, min(1.2, float(average_hr) / max_heart_rate))
        return round(moving_minutes * intensity**2, 1)
    distance_km = float(activity.get("distance_km") or 0)
    elevation_gain = float(activity.get("elevation_gain_m") or 0)
    return round(distance_km * 10.0 + elevation_gain / 25.0, 1)


def fitness_fatigue_series(
    activities: Sequence[Dict[str, Any]],
    *,
    max_heart_rate: Optional[int] = None,
    end_date: Optional[datetime] = None,
    days: int = 90,
) -> List[Dict[str, Any]]:
    end = end_date or datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    start = (end - timedelta(days=days - 1)).date()
    load_by_day: Dict[str, float] = {}
    for activity in activities:
        started_at = parse_datetime(activity.get("started_at") or activity.get("start_time"))
        if not started_at:
            continue
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        day = started_at.date().isoformat()
        load_by_day[day] = load_by_day.get(day, 0.0) + activity_effort(activity, max_heart_rate)

    fitness = 0.0
    fatigue = 0.0
    fitness_decay = exp(-1 / 42.0)
    fatigue_decay = exp(-1 / 7.0)
    series: List[Dict[str, Any]] = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        load = load_by_day.get(day.isoformat(), 0.0)
        fitness = fitness * fitness_decay + load * (1 - fitness_decay)
        fatigue = fatigue * fatigue_decay + load * (1 - fatigue_decay)
        series.append(
            {
                "date": day.isoformat(),
                "load": round(load, 1),
                "fitness": round(fitness, 1),
                "fatigue": round(fatigue, 1),
                "form": round(fitness - fatigue, 1),
            }
        )
    return series


def heart_rate_zones(max_heart_rate: int) -> List[Dict[str, Any]]:
    bands = [
        ("Recovery", 0.50, 0.60),
        ("Easy", 0.60, 0.70),
        ("Tempo", 0.70, 0.80),
        ("Threshold", 0.80, 0.90),
        ("VO2 Max", 0.90, 1.00),
    ]
    return [
        {
            "zone": index + 1,
            "name": name,
            "min_bpm": round(max_heart_rate * lower),
            "max_bpm": round(max_heart_rate * upper),
        }
        for index, (name, lower, upper) in enumerate(bands)
    ]


def pace_zones(threshold_pace_sec_per_km: int) -> List[Dict[str, Any]]:
    # Higher seconds means slower running pace.
    definitions = [
        ("Recovery", 1.30, 1.60),
        ("Easy", 1.15, 1.30),
        ("Steady", 1.05, 1.15),
        ("Threshold", 0.95, 1.05),
        ("Interval", 0.80, 0.95),
    ]
    return [
        {
            "zone": index + 1,
            "name": name,
            "fast_sec_per_km": round(threshold_pace_sec_per_km * fast),
            "slow_sec_per_km": round(threshold_pace_sec_per_km * slow),
        }
        for index, (name, fast, slow) in enumerate(definitions)
    ]


def routes_are_matched(
    first: Dict[str, Any],
    second: Dict[str, Any],
    *,
    endpoint_tolerance_m: float = 150.0,
    distance_tolerance: float = 0.08,
) -> bool:
    first_stream = first.get("cleaned_stream") or []
    second_stream = second.get("cleaned_stream") or []
    if len(first_stream) < 2 or len(second_stream) < 2:
        return False
    first_distance = float(first.get("distance_m") or 0)
    second_distance = float(second.get("distance_m") or 0)
    if max(first_distance, second_distance) <= 0:
        return False
    if abs(first_distance - second_distance) / max(first_distance, second_distance) > distance_tolerance:
        return False
    return (
        haversine_m(first_stream[0], second_stream[0]) <= endpoint_tolerance_m
        and haversine_m(first_stream[-1], second_stream[-1]) <= endpoint_tolerance_m
    )


def deterministic_activity_insight(
    activity: Dict[str, Any],
    recent_activities: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    distance = float(activity.get("distance_km") or 0)
    pace = activity.get("average_pace_sec_per_km")
    effort = activity_effort(activity)
    comparable = [
        item
        for item in recent_activities
        if item.get("id") != activity.get("id")
        and float(item.get("distance_km") or 0) > 0
    ]
    average_distance = (
        sum(float(item.get("distance_km") or 0) for item in comparable) / len(comparable)
        if comparable
        else None
    )
    observations = [
        f"You completed {distance:.2f} km"
        + (f" at {int(pace // 60)}:{int(pace % 60):02d} per km." if pace else ".")
    ]
    if average_distance:
        difference = (distance - average_distance) / average_distance
        if abs(difference) >= 0.1:
            observations.append(
                f"This was {abs(difference) * 100:.0f}% {'longer' if difference > 0 else 'shorter'} "
                "than your recent average."
            )
    quality = activity.get("quality") or {}
    if quality.get("status") != "accepted":
        observations.append("GPS quality needs review, so competitive results are withheld.")
    recommendation = (
        "Prioritize an easy or recovery session next."
        if effort >= 70
        else "This load should fit a normal training progression if recovery remains stable."
    )
    return {
        "summary": " ".join(observations),
        "recommendation": recommendation,
        "effort": effort,
        "visibility": "owner_only",
        "generated_by": "deterministic-v1",
    }
