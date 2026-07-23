from __future__ import annotations

from backend import helpers, models, server


def test_backend_package_split_keeps_server_bound_to_shared_modules():
    assert server.clean_doc is helpers.clean_doc
    assert server.UserProfile is models.UserProfile
    assert server.Workout is models.Workout
    assert server.TerraRunCreate is models.TerraRunCreate

    route_paths = {getattr(route, 'path', None) for route in server.app.routes}
    assert '/api/terra/stats' in route_paths
    assert '/api/workouts/today' in route_paths

    assert server._parse_iso_datetime('2026-03-30T10:00:00Z') == helpers._parse_iso_datetime('2026-03-30T10:00:00Z')
    assert server._terra_run_response(
        {'id': 'x', 'distance_km': '1.25', 'duration_sec': '60', 'territory_km2': '0.2', 'xp': '10'}
    ) == helpers._terra_run_response(
        {'id': 'x', 'distance_km': '1.25', 'duration_sec': '60', 'territory_km2': '0.2', 'xp': '10'}
    )
    assert server._terra_plan_weeks('5K', 'beginner') == helpers._terra_plan_weeks('5K', 'beginner')
    assert server._terra_plan_weeks('marathon', 'advanced', override=14) == helpers._terra_plan_weeks(
        'marathon',
        'advanced',
        override=14,
    )


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
