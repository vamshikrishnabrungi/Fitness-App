from __future__ import annotations

from typing import Any, Dict, List

from pymongo import ASCENDING, DESCENDING, GEOSPHERE


COLLECTIONS: List[str] = [
    'users',
    'otps',
    'athlete_profiles',
    'training_programs',
    'program_blocks',
    'workouts',
    'workout_sessions',
    'exercise_results',
    'exercise_library',
    'movement_patterns',
    'physical_qualities',
    'sport_profiles',
    'sport_roles',
    'sport_training_rules',
    'workout_templates',
    'injury_modifications',
    'progression_rules',
    'readiness_rules',
    'benchmark_tests',
    'equipment_library',
    'knowledge_sources',
    'source_registry',
    'nutrition_guidelines',
    'running_workouts',
    'running_plan_rules',
    'meals',
    'nutrition_targets',
    'sleep_sessions',
    'health_metrics',
    'injuries',
    'injury_logs',
    'quick_logs',
    'moods',
    'daily_snapshots',
    'coach_daily_analyses',
    'terra_runs',
    'run_clubs',
    'run_club_memberships',
    'terra_reflections',
    'terra_feed_posts',
    'terra_training_plans',
    'coach_requests',
    'coach_relationships',
    'coach_workouts',
    'coach_meals',
    'coach_goals',
    'journal_entries',
    'lessons',
]


INDEXES: Dict[str, List[Dict[str, Any]]] = {
    'users': [
        {'keys': [('email', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('mode', ASCENDING)]},
        {'keys': [('profile.city', ASCENDING)]},
        {'keys': [('profile.sports', ASCENDING)]},
    ],
    'otps': [
        {'keys': [('email', ASCENDING), ('created_at', DESCENDING)]},
        {'keys': [('expires_at', ASCENDING)], 'kwargs': {'expireAfterSeconds': 0}},
    ],
    'athlete_profiles': [
        {'keys': [('user_id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sports', ASCENDING)]},
        {'keys': [('city', ASCENDING)]},
    ],
    'training_programs': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('status', ASCENDING)]},
        {'keys': [('user_id', ASCENDING), ('created_at', DESCENDING)]},
    ],
    'program_blocks': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('program_id', ASCENDING), ('week_number', ASCENDING)]},
    ],
    'workouts': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('scheduled_date', ASCENDING)]},
        {'keys': [('user_id', ASCENDING), ('completed', ASCENDING)]},
        {'keys': [('program_id', ASCENDING), ('week_number', ASCENDING)]},
    ],
    'workout_sessions': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('workout_id', ASCENDING)]},
    ],
    'exercise_results': [
        {'keys': [('user_id', ASCENDING), ('exercise_id', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('session_id', ASCENDING)]},
    ],
    'exercise_library': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('name', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('movement_patterns', ASCENDING)]},
        {'keys': [('equipment', ASCENDING)]},
        {'keys': [('difficulty', ASCENDING)]},
        {'keys': [('sport_tags', ASCENDING)]},
        {'keys': [('injury_flags', ASCENDING)]},
    ],
    'movement_patterns': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('pattern', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport_transfer', ASCENDING)]},
    ],
    'physical_qualities': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('quality', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('group', ASCENDING)]},
    ],
    'sport_profiles': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('training_priorities', ASCENDING)]},
        {'keys': [('common_injuries', ASCENDING)]},
    ],
    'sport_roles': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport', ASCENDING), ('role', ASCENDING)], 'kwargs': {'unique': True}},
    ],
    'sport_training_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport', ASCENDING)]},
        {'keys': [('condition', ASCENDING)]},
    ],
    'workout_templates': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('level', ASCENDING)]},
        {'keys': [('sport_tags', ASCENDING)]},
        {'keys': [('equipment_required', ASCENDING)]},
    ],
    'injury_modifications': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('body_area', ASCENDING)]},
        {'keys': [('avoid_patterns', ASCENDING)]},
    ],
    'progression_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('rule_type', ASCENDING)]},
        {'keys': [('applies_to', ASCENDING)]},
    ],
    'readiness_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('factors', ASCENDING)]},
    ],
    'benchmark_tests': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('test_name', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('qualities', ASCENDING)]},
        {'keys': [('sport_tags', ASCENDING)]},
    ],
    'equipment_library': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('name', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('setting', ASCENDING)]},
    ],
    'knowledge_sources': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('title', ASCENDING)]},
    ],
    'source_registry': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('title', ASCENDING)]},
        {'keys': [('evidence_rank', DESCENDING)]},
    ],
    'nutrition_guidelines': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('goal_tags', ASCENDING)]},
        {'keys': [('category', ASCENDING)]},
    ],
    'running_workouts': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('workout_type', ASCENDING)]},
        {'keys': [('suitable_user_level', ASCENDING)]},
    ],
    'running_plan_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('rule_type', ASCENDING)]},
        {'keys': [('applies_to', ASCENDING)]},
    ],
    'meals': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('user_id', ASCENDING), ('meal_type', ASCENDING)]},
    ],
    'nutrition_targets': [
        {'keys': [('user_id', ASCENDING), ('effective_from', DESCENDING)]},
    ],
    'sleep_sessions': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
    ],
    'health_metrics': [
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('user_id', ASCENDING), ('metric_type', ASCENDING), ('date', DESCENDING)]},
    ],
    'injuries': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('is_active', ASCENDING)]},
    ],
    'injury_logs': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('is_active', ASCENDING)]},
        {'keys': [('user_id', ASCENDING), ('logged_at', DESCENDING)]},
    ],
    'quick_logs': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
    ],
    'moods': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
    ],
    'daily_snapshots': [
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('created_at', DESCENDING)]},
    ],
    'coach_daily_analyses': [
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('snapshot_id', ASCENDING)]},
    ],
    'terra_runs': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('user_id', ASCENDING), ('created_at', DESCENDING)]},
        {'keys': [('city', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('route_geojson', GEOSPHERE)], 'kwargs': {'sparse': True}},
    ],
    'run_clubs': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('city', ASCENDING), ('is_public', ASCENDING)]},
        {'keys': [('member_ids', ASCENDING)]},
        {'keys': [('owner_id', ASCENDING)]},
    ],
    'run_club_memberships': [
        {'keys': [('club_id', ASCENDING), ('user_id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('status', ASCENDING)]},
        {'keys': [('club_id', ASCENDING), ('status', ASCENDING)]},
    ],
    'terra_reflections': [
        {'keys': [('user_id', ASCENDING), ('run_id', ASCENDING)], 'kwargs': {'unique': True}},
    ],
    'terra_feed_posts': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('created_at', DESCENDING)]},
        {'keys': [('user_id', ASCENDING), ('created_at', DESCENDING)]},
    ],
    'terra_training_plans': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('created_at', DESCENDING)]},
    ],
    'coach_requests': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('client_id', ASCENDING), ('status', ASCENDING)]},
        {'keys': [('coach_id', ASCENDING), ('status', ASCENDING)]},
    ],
    'coach_relationships': [
        {'keys': [('coach_id', ASCENDING), ('client_id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('client_id', ASCENDING), ('status', ASCENDING)]},
    ],
    'coach_workouts': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('client_id', ASCENDING), ('scheduled_date', DESCENDING)]},
        {'keys': [('coach_id', ASCENDING), ('created_at', DESCENDING)]},
    ],
    'coach_meals': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('client_id', ASCENDING), ('date', DESCENDING)]},
    ],
    'coach_goals': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('client_id', ASCENDING), ('created_at', DESCENDING)]},
    ],
    'journal_entries': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('user_id', ASCENDING), ('entry_type', ASCENDING)]},
        {'keys': [('tags', ASCENDING)]},
    ],
    'lessons': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport', ASCENDING), ('category', ASCENDING)]},
    ],
}


async def ensure_database_schema(db: Any) -> None:
    existing = set(await db.list_collection_names())
    for name in COLLECTIONS:
        if name not in existing:
            await db.create_collection(name)

    for collection_name, indexes in INDEXES.items():
        collection = db[collection_name]
        for index in indexes:
            keys = index['keys']
            kwargs = index.get('kwargs', {})
            await collection.create_index(keys, **kwargs)
