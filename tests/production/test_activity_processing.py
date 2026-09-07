from datetime import datetime, timedelta, timezone
import pytest
from backend.app.activities.models import Activity
from backend.app.activities.processing import (
    ACTIVITY_METRICS_VERSION,
    MAX_GPS_ACCURACY_M,
    MAX_RUNNING_SPEED_MPS,
    Sample,
    best_efforts,
    calories_for_run,
    kilometre_splits,
    process_samples,
)


def test_straight_run_replays_device_metrics_for_confirmation():
    start = datetime(2026, 8, 6, tzinfo=timezone.utc)
    rows = [
        Sample(17.4 + (index * .000225), 78.4, start + timedelta(seconds=index * 10), accuracy=5)
        for index in range(41)
    ]
    result=process_samples(rows)
    assert result.distance_m==pytest.approx(1000.7,rel=.02)
    assert result.elapsed_seconds==400
    assert result.moving_seconds==400
    assert result.gps_score>.9


def test_activity_metric_contract_is_versioned_and_uses_hardened_thresholds():
    assert ACTIVITY_METRICS_VERSION == "activity-metrics-v1"
    assert MAX_GPS_ACCURACY_M == 100
    assert MAX_RUNNING_SPEED_MPS == 15
    assert "region_id" in Activity.__table__.columns


def test_small_valid_movements_are_not_discarded():
    start = datetime(2026, 8, 6, tzinfo=timezone.utc)
    rows = [
        Sample(17.4, 78.4, start, accuracy=5),
        Sample(17.400009, 78.4, start + timedelta(seconds=1), accuracy=5),
        Sample(17.400018, 78.4, start + timedelta(seconds=2), accuracy=5),
    ]
    assert process_samples(rows).distance_m > 1


def test_impossible_jump_is_removed_without_destroying_raw_evidence():
    start=datetime(2026,8,6,tzinfo=timezone.utc);rows=[Sample(17.4,78.4,start,accuracy=5),Sample(18.4,79.4,start+timedelta(seconds=1),accuracy=5),Sample(17.401,78.4,start+timedelta(minutes=1),accuracy=5)]
    result=process_samples(rows)
    assert len(result.samples)==2
    assert "impossible_jump_removed" in result.reasons


def test_calories_requires_athlete_weight():
    assert calories_for_run(5000,None) is None
    assert calories_for_run(5000,70)==350


def test_splits_and_best_efforts_interpolate_distance_boundaries():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    samples = tuple(
        Sample(0, index * 0.001, start + timedelta(seconds=index * 30), accuracy=5)
        for index in range(21)
    )
    splits = kilometre_splits(samples)
    efforts = best_efforts(samples)
    assert len(splits) == 3
    assert splits[0].distance_m == pytest.approx(1000, rel=0.001)
    assert {effort.distance_code for effort in efforts} == {"400m", "1k", "1mile"}
