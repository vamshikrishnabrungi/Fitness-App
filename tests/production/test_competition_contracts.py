from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.competition.schemas import ChallengeCreate, RaceCreate
from backend.app.competition.leaderboards import current_period_code, metric_code
from backend.app.competition.progress import activity_period_codes
from backend.app.competition.race_results import race_evidence_passes


NOW = datetime(2026, 8, 8, 8, 0, tzinfo=timezone.utc)


def test_distance_challenge_uses_canonical_units() -> None:
    challenge = ChallengeCreate(
        name="August distance",
        challenge_type="distance",
        starts_at=NOW,
        ends_at=NOW + timedelta(days=28),
        target=100_000,
    )
    assert challenge.canonical_rules() == {
        "schema_version": 1,
        "target": 100_000,
        "unit": "metres",
        "segment_id": None,
        "minimum_activity_distance_m": 0,
    }


def test_fastest_segment_requires_segment_and_rejects_target() -> None:
    with pytest.raises(ValidationError):
        ChallengeCreate(
            name="Fastest hill",
            challenge_type="fastest_segment",
            starts_at=NOW,
            ends_at=NOW + timedelta(days=7),
        )
    with pytest.raises(ValidationError):
        ChallengeCreate(
            name="Fastest hill",
            challenge_type="fastest_segment",
            starts_at=NOW,
            ends_at=NOW + timedelta(days=7),
            segment_id=uuid4(),
            target=60,
        )


def test_challenge_rejects_unbounded_or_naive_windows() -> None:
    with pytest.raises(ValidationError):
        ChallengeCreate(
            name="Too long",
            challenge_type="run_count",
            starts_at=NOW.replace(tzinfo=None),
            ends_at=(NOW + timedelta(days=400)).replace(tzinfo=None),
            target=10,
        )


def test_race_validates_timezone_and_result_window() -> None:
    race = RaceCreate(
        name="Club 5K",
        route_id=uuid4(),
        timezone="Asia/Kolkata",
        starts_at=NOW,
        start_window_minutes=30,
        result_cutoff_at=NOW + timedelta(hours=2),
        participant_capacity=200,
    )
    assert race.eligibility.minimum_age == 16

    with pytest.raises(ValidationError):
        RaceCreate(
            name="Broken race",
            route_id=uuid4(),
            timezone="Not/A_Timezone",
            starts_at=NOW,
            result_cutoff_at=NOW + timedelta(hours=2),
        )

    with pytest.raises(ValidationError):
        RaceCreate(
            name="No result window",
            route_id=uuid4(),
            timezone="UTC",
            starts_at=NOW,
            start_window_minutes=60,
            result_cutoff_at=NOW + timedelta(minutes=30),
        )


def test_leaderboard_periods_and_metric_aliases_are_canonical() -> None:
    assert activity_period_codes(NOW) == ("all_time", "week:2026-W32", "month:2026-08")
    assert current_period_code("week", NOW) == "week:2026-W32"
    assert current_period_code("month", NOW) == "month:2026-08"
    assert metric_code("distance") == "distance_m"
    with pytest.raises(ValueError):
        current_period_code("yesterday", NOW)
    with pytest.raises(ValueError):
        metric_code("calories")


def test_race_verification_requires_every_gate() -> None:
    valid = {
        "competition_eligible": True,
        "unresolved_flag": False,
        "within_schedule": True,
        "route_coverage": 0.90,
        "start_distance_m": 100,
        "end_distance_m": 100,
    }
    assert race_evidence_passes(**valid)
    for field, invalid in {
        "competition_eligible": False,
        "unresolved_flag": True,
        "within_schedule": False,
        "route_coverage": 0.899,
        "start_distance_m": 100.1,
        "end_distance_m": 100.1,
    }.items():
        candidate = {**valid, field: invalid}
        assert not race_evidence_passes(**candidate)
