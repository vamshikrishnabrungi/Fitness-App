from __future__ import annotations

from datetime import datetime, timezone

from backend.training_analytics import (
    activity_effort,
    deterministic_activity_insight,
    fitness_fatigue_series,
    heart_rate_zones,
    pace_zones,
    routes_are_matched,
)


def test_activity_effort_prefers_heart_rate_and_has_distance_fallback():
    activity = {
        "moving_time_sec": 3_600,
        "distance_km": 10,
        "average_heart_rate": 152,
    }
    assert activity_effort(activity, 190) == 38.4
    assert activity_effort({**activity, "average_heart_rate": None}) == 100


def test_fitness_fatigue_series_applies_different_decay_windows():
    activities = [{
        "started_at": "2026-07-27T06:00:00Z",
        "distance_km": 10,
        "moving_time_sec": 3_600,
    }]
    series = fitness_fatigue_series(
        activities,
        end_date=datetime(2026, 7, 27, tzinfo=timezone.utc),
        days=7,
    )
    assert len(series) == 7
    assert series[-1]["load"] == 100
    assert series[-1]["fatigue"] > series[-1]["fitness"]
    assert series[-1]["form"] < 0


def test_zone_generation_has_five_ordered_zones():
    hr = heart_rate_zones(190)
    pace = pace_zones(300)
    assert len(hr) == 5
    assert hr[-1]["max_bpm"] == 190
    assert len(pace) == 5
    assert pace[3]["fast_sec_per_km"] < pace[3]["slow_sec_per_km"]


def test_matched_routes_require_similar_distance_and_endpoints():
    first = {
        "distance_m": 1_000,
        "cleaned_stream": [
            {"latitude": 17.4200, "longitude": 78.4700},
            {"latitude": 17.4290, "longitude": 78.4700},
        ],
    }
    second = {
        "distance_m": 1_030,
        "cleaned_stream": [
            {"latitude": 17.4201, "longitude": 78.4701},
            {"latitude": 17.4291, "longitude": 78.4701},
        ],
    }
    assert routes_are_matched(first, second) is True
    assert routes_are_matched(first, {**second, "distance_m": 1_500}) is False


def test_insight_never_changes_calculated_metrics():
    activity = {
        "id": "run-1",
        "distance_km": 10,
        "average_pace_sec_per_km": 360,
        "quality": {"status": "accepted"},
    }
    insight = deterministic_activity_insight(
        activity,
        [{"id": "run-2", "distance_km": 5}],
    )
    assert "10.00 km" in insight["summary"]
    assert "longer" in insight["summary"]
    assert insight["visibility"] == "owner_only"
