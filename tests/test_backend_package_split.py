from __future__ import annotations

from backend import helpers, models


def test_model_defaults_remain_stable_after_extraction():
    profile = models.UserProfile()
    assert profile.goals == []
    assert profile.selected_goals == []
    assert profile.sports == []
    assert profile.equipment == []

    workout = models.Workout(
        user_id='user-1',
        title='Strength Session',
        category='Strength',
        duration=45,
        difficulty='Intermediate',
    )
    assert workout.completed is False
    assert workout.exercises == []
    assert workout.user_feedback is None


def test_terra_run_response_normalizes_legacy_fields():
    normalized = helpers._terra_run_response(
        {
            'id': 'run-1',
            'distance_km': '7.25',
            'duration_sec': '1800',
            'territory_km2': '0.3',
            'xp': '90',
            'is_loop': 1,
        }
    )

    assert normalized['distance'] == 7.2
    assert normalized['duration'] == 1800
    # Territory now derives from distance (>= 2.5km claims the run's road km),
    # so the stored box value 0.3 is ignored in favour of the distance.
    assert normalized['territory_captured'] == 7.2
    assert normalized['xp_earned'] == 90
    assert normalized['is_loop'] is True

    # A run below the threshold claims no territory.
    short = helpers._terra_run_response({'id': 'r2', 'distance_km': '1.2', 'duration_sec': '300'})
    assert short['territory_captured'] == 0.0
