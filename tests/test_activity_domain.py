from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.activity_domain import (
    ActivityCreate,
    ActivityPoint,
    calculate_best_efforts,
    calculate_splits,
    clean_activity_stream,
    process_activity,
)


def _point(
    latitude: float,
    longitude: float,
    seconds: int,
    *,
    altitude: float | None = None,
    accuracy: float = 5,
) -> ActivityPoint:
    return ActivityPoint(
        latitude=latitude,
        longitude=longitude,
        timestamp=datetime(2026, 7, 27, 6, 0, tzinfo=timezone.utc) + timedelta(seconds=seconds),
        altitude=altitude,
        accuracy=accuracy,
    )


def test_stream_cleaning_rejects_poor_accuracy_and_impossible_jumps():
    points = [
        _point(17.4200, 78.4700, 0),
        _point(17.4201, 78.4700, 10, accuracy=150),
        _point(17.5200, 78.5700, 20),
        _point(17.4202, 78.4700, 30),
    ]

    cleaned, dropped = clean_activity_stream(points)

    assert len(cleaned) == 2
    assert dropped["poor_accuracy"] == 1
    assert dropped["implausible_jump"] == 1


def test_activity_processing_calculates_server_owned_metrics():
    start = datetime(2026, 7, 27, 6, 0, tzinfo=timezone.utc)
    # Roughly 111 m north every minute: a plausible easy run.
    points = [
        _point(17.4200, 78.4700, 0, altitude=500),
        _point(17.4210, 78.4700, 60, altitude=503),
        _point(17.4220, 78.4700, 120, altitude=504),
        _point(17.4230, 78.4700, 180, altitude=507),
    ]
    payload = ActivityCreate(
        gps_path=points,
        start_time=start,
        end_time=start + timedelta(seconds=210),
        paused_duration_sec=30,
    )

    result = process_activity(payload, athlete_weight_kg=60)

    assert 330 <= result["distance_m"] <= 335
    assert result["elapsed_time_sec"] == 210
    assert result["moving_time_sec"] == 180
    assert result["paused_time_sec"] == 30
    assert result["elevation_gain_m"] == 6
    assert result["calories_kcal"] == 20
    assert result["average_pace_sec_per_km"] is not None
    assert result["quality"]["status"] == "accepted"
    assert result["route_geojson"]["type"] == "LineString"


def test_manual_treadmill_activity_does_not_require_gps():
    payload = ActivityCreate(
        source="manual",
        activity_type="treadmill",
        distance_m=5_000,
        elapsed_time_sec=1_800,
        moving_time_sec=1_800,
        elevation_gain_m=0,
    )

    result = process_activity(payload, athlete_weight_kg=65)

    assert result["distance_km"] == 5
    assert result["moving_time_sec"] == 1_800
    assert result["average_pace_sec_per_km"] == 360
    assert result["calories_kcal"] == 325
    assert result["route_geojson"] is None


def test_uphill_activity_reports_faster_grade_adjusted_equivalent_pace():
    start = datetime(2026, 7, 27, 6, 0, tzinfo=timezone.utc)
    payload = ActivityCreate(
        gps_path=[
            _point(17.4200, 78.4700, 0, altitude=500),
            _point(17.4210, 78.4700, 60, altitude=511),
        ],
        start_time=start,
        end_time=start + timedelta(seconds=60),
    )

    result = process_activity(payload)

    assert result["grade_adjusted_pace_sec_per_km"] is not None
    assert result["grade_adjusted_pace_sec_per_km"] < result["average_pace_sec_per_km"]
    assert result["elevation_source"] == "recorded"


def test_splits_interpolate_boundary_crossings():
    splits = calculate_splits(
        [0, 600, 1_200, 2_000],
        [0, 180, 360, 600],
    )

    assert splits == [
        {
            "split": 1,
            "distance_m": 1_000.0,
            "elapsed_time_sec": 300,
            "pace_sec_per_km": 300,
        },
        {
            "split": 2,
            "distance_m": 1_000.0,
            "elapsed_time_sec": 300,
            "pace_sec_per_km": 300,
        },
    ]


def test_best_efforts_use_fastest_sliding_distance_window():
    efforts = calculate_best_efforts(
        [0, 400, 800, 1_200, 1_600, 2_000],
        [0, 150, 300, 420, 540, 660],
    )

    effort_400 = next(item for item in efforts if item["name"] == "400m")
    effort_1k = next(item for item in efforts if item["name"] == "1k")
    assert effort_400["elapsed_time_sec"] == 120
    assert effort_1k["elapsed_time_sec"] == 300
