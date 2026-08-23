from __future__ import annotations

from datetime import datetime, timezone

from backend.competition_domain import (
    RaceCreate,
    challenge_score,
    goal_progress,
    match_segment_effort,
    path_metrics,
)


def test_path_metrics_builds_geojson_and_distance():
    metrics = path_metrics([
        {"latitude": 17.4200, "longitude": 78.4700, "altitude": 500},
        {"latitude": 17.4210, "longitude": 78.4700, "altitude": 503},
    ])
    assert 110 <= metrics["distance_m"] <= 112
    assert metrics["elevation_gain_m"] == 3
    assert metrics["geometry"]["type"] == "LineString"


def test_segment_match_requires_ordered_endpoints_and_shape():
    activity = [
        {"latitude": 17.4200, "longitude": 78.4700, "timestamp": "2026-07-27T06:00:00Z"},
        {"latitude": 17.4210, "longitude": 78.4700, "timestamp": "2026-07-27T06:01:00Z"},
        {"latitude": 17.4220, "longitude": 78.4700, "timestamp": "2026-07-27T06:02:00Z"},
    ]
    segment = [
        {"latitude": 17.4200, "longitude": 78.4700},
        {"latitude": 17.4210, "longitude": 78.4700},
        {"latitude": 17.4220, "longitude": 78.4700},
    ]
    effort = match_segment_effort(activity, segment)
    reversed_effort = match_segment_effort(activity, list(reversed(segment)))
    assert effort is not None
    assert effort["elapsed_time_sec"] == 120
    assert reversed_effort is None


def test_goal_progress_uses_only_period_activities():
    goal = {
        "metric": "distance_km",
        "target": 10,
        "period_start": datetime(2026, 7, 1, tzinfo=timezone.utc),
        "period_end": datetime(2026, 7, 31, tzinfo=timezone.utc),
    }
    activities = [
        {"started_at": "2026-07-10T06:00:00Z", "distance_km": 4},
        {"started_at": "2026-07-20T06:00:00Z", "distance_km": 6},
        {"started_at": "2026-08-01T06:00:00Z", "distance_km": 20},
    ]
    progress = goal_progress(goal, activities)
    assert progress["current"] == 10
    assert progress["progress"] == 1
    assert progress["completed"] is True


def test_challenge_scores_distance_consistency_and_fastest_5k():
    activities = [
        {
            "date": "2026-07-20",
            "distance_km": 5,
            "best_efforts": [{"name": "5k", "elapsed_time_sec": 1_500}],
        },
        {
            "date": "2026-07-21",
            "distance_km": 6,
            "best_efforts": [{"name": "5k", "elapsed_time_sec": 1_440}],
        },
    ]
    assert challenge_score("distance", activities) == 11
    assert challenge_score("consistency", activities) == 2
    assert challenge_score("fastest_5k", activities) == -1_440


def test_race_model_enforces_safe_start_and_finish_windows():
    race = RaceCreate(
        name="Hussain Sagar 5K",
        route_id="route-1",
        starts_at="2026-08-01T06:00:00Z",
        start_window_minutes=20,
        max_finish_minutes=120,
    )
    assert race.start_window_minutes == 20
    assert race.max_finish_minutes == 120
