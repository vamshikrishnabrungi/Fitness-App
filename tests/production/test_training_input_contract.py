import pytest
from pydantic import ValidationError

from backend.app.athletes.schemas import ExternalLoadInput, GoalInput, OnboardingCommand, SportInput
from backend.app.knowledge.training_contract import (
    SPORT_SCOPE_VALUES,
    athlete_level,
    normalize_goal,
    normalize_phase,
    sport_scope_key,
)


def test_contract_covers_exactly_all_matrix_sports():
    assert set(SPORT_SCOPE_VALUES) == {
        "badminton", "basketball", "boxing", "cricket", "cycling", "football",
        "mma", "running", "swimming", "tennis", "volleyball",
    }
    assert sum(len(values) for _, values in SPORT_SCOPE_VALUES.values()) == 54


@pytest.mark.parametrize(
    ("competition_level", "expected"),
    [
        ("recreational", "beginner"),
        ("club", "intermediate"),
        ("regional", "advanced"),
        ("national", "advanced"),
        ("international", "advanced"),
    ],
)
def test_competition_levels_resolve_to_reference_levels(competition_level, expected):
    assert athlete_level(competition_level) == expected


def test_ui_aliases_normalize_to_matrix_codes():
    assert normalize_goal("athletic") == "general_performance"
    assert normalize_goal("strength") == "strength_power"
    assert normalize_goal("endurance") == "conditioning"
    assert normalize_phase("off_season") == "general_preparation"
    assert normalize_phase("pre_season") == "specific_preparation"
    assert normalize_phase("in_season") == "competition"


def test_sport_scope_is_required_and_exact():
    assert sport_scope_key(
        "swimming",
        event_code="middle_distance",
        discipline_code="freestyle",
        role_code=None,
        format_code=None,
    ) == ("event_discipline", "middle_distance:freestyle")
    with pytest.raises(ValueError, match="requires a valid role"):
        sport_scope_key("football", event_code=None, role_code=None, discipline_code=None, format_code=None)
    with pytest.raises(ValidationError):
        SportInput(sport_code="running", event_code="ultramarathon", is_primary=True)


def test_onboarding_normalizes_goal_phase_and_scope():
    command = OnboardingCommand(
        competition_level="club",
        training_age_years=2,
        maximum_session_minutes=60,
        season_phase="pre_season",
        sports=[SportInput(sport_code="running", event_code="5k", is_primary=True)],
        availability=[{
            "weekday": 0,
            "start_minute": 420,
            "duration_minutes": 60,
            "environments": ["road"],
        }],
        goal=GoalInput(goal_type="endurance"),
    )
    assert command.season_phase == "specific_preparation"
    assert command.goal.goal_type == "conditioning"


def test_external_load_contract_requires_timezone_and_explicit_weekly_recurrence():
    value = ExternalLoadInput(
        sport_code="running",
        load_type="practice",
        starts_at="2026-09-07T18:00:00+05:30",
        duration_minutes=90,
        intensity="hard",
        recurrence={"frequency": "weekly", "interval_weeks": 1, "until": "2026-10-05"},
    )
    assert value.recurrence and value.recurrence.frequency == "weekly"
    with pytest.raises(ValidationError, match="timezone"):
        ExternalLoadInput(
            sport_code="running",
            load_type="practice",
            starts_at="2026-09-07T18:00:00",
            duration_minutes=90,
            intensity="hard",
        )
    with pytest.raises(ValidationError):
        ExternalLoadInput(
            sport_code="running",
            load_type="practice",
            starts_at="2026-09-07T18:00:00Z",
            duration_minutes=90,
            intensity="hard",
            recurrence={"frequency": "daily"},
        )
    with pytest.raises(ValidationError, match="cannot end before"):
        ExternalLoadInput(
            sport_code="running",
            load_type="practice",
            starts_at="2026-09-07T18:00:00Z",
            duration_minutes=90,
            intensity="hard",
            recurrence={"frequency": "weekly", "until": "2026-09-06"},
        )
