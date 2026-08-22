from datetime import datetime, timedelta, timezone
import pytest
from backend.app.activities.processing import Sample, best_efforts, calories_for_run, kilometre_splits, process_samples


def test_straight_run_has_server_authoritative_moving_time_and_distance():
    start=datetime(2026,8,6,tzinfo=timezone.utc);rows=[Sample(17.4+(index*.00225),78.4,start+timedelta(minutes=index),accuracy=5) for index in range(5)]
    result=process_samples(rows)
    assert result.distance_m==pytest.approx(1000.7,rel=.02)
    assert result.elapsed_seconds==240
    assert result.moving_seconds==240
    assert result.gps_score>.9


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
