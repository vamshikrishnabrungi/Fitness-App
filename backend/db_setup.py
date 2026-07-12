from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from pymongo import ASCENDING, DESCENDING, GEOSPHERE


PLANNING_SEED_PATH = Path(__file__).resolve().parent / 'data' / 'sftc_backend_planning_collections.json'
PLANNING_SEED_COLLECTIONS = {
    'planning_rules',
    'sport_profiles',
    'macro_plan_templates',
    'competition_week_rules',
}


COLLECTIONS: List[str] = [
    'users',
    'otps',
    'athlete_profiles',
    'macro_plans',
    'athlete_states',
    'training_programs',
    'program_blocks',
    'workouts',
    'workout_sessions',
    'exercise_results',
    'exercise_library',
    'primary_exercise_library',
    'exercise_variation_library',
    'exercise_progression_graph',
    'user_exercise_history',
    'user_level_assessments',
    'user_benchmarks',
    'source_sections',
    'knowledge_extraction_runs',
    'training_principles',
    'programming_rules',
    'technical_models',
    'technical_errors',
    'coaching_progressions',
    'mobility_drills',
    'recovery_rules',
    'nutrition_principles',
    'glossary_terms',
    'movement_patterns',
    'physical_qualities',
    'sport_profiles',
    'sport_roles',
    'sport_training_rules',
    'sport_teaching_progressions',
    'sport_skill_assessments',
    'sport_level_transition_rules',
    'planning_rules',
    'training_protocols',
    'macro_plan_templates',
    'competition_week_rules',
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
    'lessons',
    'ai_generation_log',
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
    'macro_plans': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('status', ASCENDING)]},
        {'keys': [('user_id', ASCENDING), ('created_at', DESCENDING)]},
        {'keys': [('template_id', ASCENDING)]},
        {'keys': [('sports', ASCENDING)]},
    ],
    'athlete_states': [
        {'keys': [('user_id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('macro_plan_id', ASCENDING)]},
        {'keys': [('current_level', ASCENDING)]},
        {'keys': [('updated_at', DESCENDING)]},
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
        {'keys': [('source_book_id', ASCENDING)]},
    ],
    'primary_exercise_library': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('name', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('base_exercise', ASCENDING)]},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('patterns', ASCENDING)]},
        {'keys': [('qualities', ASCENDING)]},
        {'keys': [('equipment', ASCENDING)]},
        {'keys': [('default_user_level', ASCENDING)]},
        {'keys': [('technical_complexity', ASCENDING)]},
        {'keys': [('impact_level', ASCENDING)]},
    ],
    'exercise_variation_library': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('name', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('base_exercise', ASCENDING)]},
        {'keys': [('variation_type', ASCENDING)]},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('patterns', ASCENDING)]},
        {'keys': [('qualities', ASCENDING)]},
        {'keys': [('equipment', ASCENDING)]},
        {'keys': [('default_user_level', ASCENDING)]},
        {'keys': [('coaching_requirement', ASCENDING)]},
    ],
    'exercise_progression_graph': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('base_exercise', ASCENDING)]},
        {'keys': [('from_exercise_id', ASCENDING)]},
        {'keys': [('to_exercise_id', ASCENDING)]},
        {'keys': [('direction', ASCENDING)]},
        {'keys': [('min_user_level', ASCENDING)]},
    ],
    'user_exercise_history': [
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('user_id', ASCENDING), ('exercise_id', ASCENDING), ('date', DESCENDING)]},
        {'keys': [('workout_id', ASCENDING)]},
        {'keys': [('source', ASCENDING)]},
    ],
    'user_level_assessments': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('created_at', DESCENDING)]},
        {'keys': [('user_id', ASCENDING), ('status', ASCENDING)]},
        {'keys': [('current_level', ASCENDING), ('recommended_level', ASCENDING)]},
    ],
    'user_benchmarks': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('user_id', ASCENDING), ('date', DESCENDING)]},
    ],
    'source_sections': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING), ('section_order', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('domain', ASCENDING)]},
        {'keys': [('topics', ASCENDING)]},
    ],
    'knowledge_extraction_runs': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING), ('created_at', DESCENDING)]},
    ],
    'training_principles': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('domain', ASCENDING)]},
        {'keys': [('topics', ASCENDING)]},
    ],
    'programming_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('rule_type', ASCENDING)]},
        {'keys': [('applies_to', ASCENDING)]},
    ],
    'technical_models': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('lift', ASCENDING)]},
        {'keys': [('phase', ASCENDING)]},
        {'keys': [('topics', ASCENDING)]},
    ],
    'technical_errors': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('lift', ASCENDING)]},
        {'keys': [('error_name', ASCENDING)]},
        {'keys': [('topics', ASCENDING)]},
    ],
    'coaching_progressions': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('lift', ASCENDING)]},
        {'keys': [('stage', ASCENDING)]},
        {'keys': [('topics', ASCENDING)]},
    ],
    'mobility_drills': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('addresses', ASCENDING)]},
        {'keys': [('body_regions', ASCENDING)]},
    ],
    'recovery_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('topics', ASCENDING)]},
    ],
    'nutrition_principles': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('topics', ASCENDING)]},
    ],
    'glossary_terms': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('source_book_id', ASCENDING)]},
        {'keys': [('term', ASCENDING)]},
        {'keys': [('topics', ASCENDING)]},
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
    'sport_teaching_progressions': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport', ASCENDING)]},
        {'keys': [('domain', ASCENDING)]},
        {'keys': [('level', ASCENDING)]},
        {'keys': [('role_tags', ASCENDING)]},
        {'keys': [('source_pack_id', ASCENDING)]},
    ],
    'sport_skill_assessments': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport', ASCENDING)]},
        {'keys': [('domain', ASCENDING)]},
        {'keys': [('level_bands.level', ASCENDING)]},
        {'keys': [('source_pack_id', ASCENDING)]},
    ],
    'sport_level_transition_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport', ASCENDING)]},
        {'keys': [('from_level', ASCENDING), ('to_level', ASCENDING)]},
        {'keys': [('applies_to', ASCENDING)]},
        {'keys': [('source_pack_id', ASCENDING)]},
    ],
    'planning_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('applies_to', ASCENDING)]},
        {'keys': [('priority', DESCENDING)]},
    ],
    'training_protocols': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('scope', ASCENDING)]},
        {'keys': [('match.injury_areas', ASCENDING)]},
    ],
    'macro_plan_templates': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('name', ASCENDING)]},
        {'keys': [('applies_when', ASCENDING)]},
        {'keys': [('macro_length_weeks', ASCENDING)]},
    ],
    'competition_week_rules': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('category', ASCENDING)]},
        {'keys': [('applies_to', ASCENDING)]},
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
    'lessons': [
        {'keys': [('id', ASCENDING)], 'kwargs': {'unique': True}},
        {'keys': [('sport', ASCENDING), ('category', ASCENDING)]},
    ],
    'ai_generation_log': [
        {'keys': [('user_id', ASCENDING), ('created_at', DESCENDING)]},
        # TTL: auto-purge quota records after 2 days (quota window is rolling 24h).
        {'keys': [('created_at', ASCENDING)], 'kwargs': {'expireAfterSeconds': 172800}},
    ],
}


async def seed_planning_collections(db: Any, seed_path: Path = PLANNING_SEED_PATH) -> Dict[str, int]:
    if not seed_path.exists():
        return {}

    with seed_path.open('r', encoding='utf-8') as handle:
        payload = json.load(handle)

    seeded_at = datetime.utcnow()
    counts: Dict[str, int] = {}
    for collection_name, records in payload.items():
        if collection_name not in PLANNING_SEED_COLLECTIONS or not isinstance(records, list):
            continue
        collection = db[collection_name]
        count = 0
        for record in records:
            if not isinstance(record, dict) or not record.get('id'):
                continue
            if collection_name == 'sport_profiles':
                existing = await collection.find_one({'id': record['id']})
                if existing and not existing.get('seed_source'):
                    continue
            doc = {
                **record,
                'seed_source': seed_path.name,
                'seeded_at': seeded_at,
                'updated_at': seeded_at,
            }
            await collection.replace_one({'id': doc['id']}, doc, upsert=True)
            count += 1
        counts[collection_name] = count
    return counts


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

    await seed_planning_collections(db)
