from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Any, Dict

from backend.activity_pipeline import release_activity_derived_facts
from backend.helpers import clean_doc
from backend.object_storage import delete_stored_object


USER_DATA_COLLECTIONS = (
    'athlete_profiles',
    'macro_plans',
    'athlete_states',
    'training_programs',
    'program_blocks',
    'workouts',
    'workout_sessions',
    'exercise_results',
    'user_exercise_history',
    'user_level_assessments',
    'user_benchmarks',
    'meals',
    'nutrition_targets',
    'health_metrics',
    'injuries',
    'injury_logs',
    'quick_logs',
    'moods',
    'daily_snapshots',
    'coach_daily_analyses',
    'activities',
    'activity_outbox',
    'activity_import_jobs',
    'activity_upload_sessions',
    'activity_upload_chunks',
    'activity_insights',
    'integration_connections',
    'privacy_settings',
    'routes',
    'segment_efforts',
    'territory_ownership',
    'goals',
    'challenge_entries',
    'race_entries',
    'live_location_sessions',
    'safety_reports',
    'terra_runs',
    'terra_reflections',
    'terra_feed_posts',
    'terra_training_plans',
    'run_club_memberships',
    'lessons',
    'ai_generation_log',
    'club_activity_events',
    'sport_library_progress',
)


async def export_user_data(db: Any, user: Dict[str, Any]) -> Dict[str, Any]:
    safe_user = clean_doc(user)
    for secret_key in ('password', 'password_hash', 'hashed_password', 'reset_token'):
        safe_user.pop(secret_key, None)

    data: Dict[str, Any] = {'user': safe_user}
    for collection_name in USER_DATA_COLLECTIONS:
        documents = await db[collection_name].find({'user_id': user['id']}).to_list(50_000)
        if collection_name == 'integration_connections':
            for document in documents:
                for secret_key in ('access_token', 'refresh_token', 'token', 'client_secret'):
                    document.pop(secret_key, None)
        data[collection_name] = [clean_doc(document) for document in documents]

    created_clubs = await db.run_clubs.find({'owner_id': user['id']}).to_list(1_000)
    data['owned_run_clubs'] = [clean_doc(document) for document in created_clubs]
    created_segments = await db.segments.find({'creator_user_id': user['id']}).to_list(10_000)
    data['created_segments'] = [clean_doc(document) for document in created_segments]
    created_challenges = await db.challenges.find({'creator_user_id': user['id']}).to_list(10_000)
    data['created_challenges'] = [clean_doc(document) for document in created_challenges]
    created_races = await db.races.find({'creator_user_id': user['id']}).to_list(10_000)
    data['created_races'] = [clean_doc(document) for document in created_races]
    reports = await db.safety_reports.find({'reporter_user_id': user['id']}).to_list(10_000)
    data['safety_reports'] = [clean_doc(document) for document in reports]
    return {
        'export_schema_version': 1,
        'generated_at': datetime.utcnow(),
        'data': data,
    }


async def delete_user_data(db: Any, request: Dict[str, Any]) -> Dict[str, Any]:
    user_id = request['user_id']
    import_jobs = await db.activity_import_jobs.find({'user_id': user_id}).to_list(50_000)
    for job in import_jobs:
        await delete_stored_object(
            job.get('original_object_bucket'),
            job.get('original_object_key'),
        )

    activities = await db.activities.find({'user_id': user_id}, {'id': 1}).to_list(50_000)
    for activity in activities:
        await release_activity_derived_facts(db, activity['id'])

    now = datetime.utcnow()
    await db.run_clubs.update_many(
        {'owner_id': user_id},
        {'$set': {
            'status': 'archived',
            'owner_id': None,
            'archived_reason': 'owner_account_deleted',
            'updated_at': now,
        }, '$pull': {'member_ids': user_id}},
    )
    await db.run_clubs.update_many(
        {'member_ids': user_id},
        {'$pull': {'member_ids': user_id}, '$set': {'updated_at': now}},
    )
    await db.segments.update_many(
        {'creator_user_id': user_id},
        {'$set': {'creator_user_id': None, 'creator_deleted': True, 'updated_at': now}},
    )
    await db.challenges.update_many(
        {'creator_user_id': user_id},
        {'$set': {
            'creator_user_id': None,
            'creator_deleted': True,
            'status': 'archived',
            'updated_at': now,
        }},
    )
    await db.races.update_many(
        {'creator_user_id': user_id},
        {'$set': {
            'creator_user_id': None,
            'creator_deleted': True,
            'status': 'archived',
            'updated_at': now,
        }},
    )
    safety_result = await db.safety_reports.delete_many({'reporter_user_id': user_id})

    deleted_counts: Dict[str, int] = {}
    for collection_name in USER_DATA_COLLECTIONS:
        result = await db[collection_name].delete_many({'user_id': user_id})
        deleted_counts[collection_name] = int(result.deleted_count)
    user_result = await db.users.delete_one({'id': user_id})
    deleted_counts['users'] = int(user_result.deleted_count)
    deleted_counts['safety_reports'] = int(safety_result.deleted_count)

    audit_secret = os.environ.get('ACCOUNT_DELETION_AUDIT_SECRET')
    audit_hash = (
        hashlib.sha256(f'{audit_secret}:{user_id}'.encode('utf-8')).hexdigest()
        if audit_secret
        else None
    )
    await db.account_deletion_requests.update_one(
        {'id': request['id']},
        {'$set': {
            'status': 'completed',
            'user_id': None,
            'user_id_hash': audit_hash,
            'completed_at': now,
            'deleted_counts': deleted_counts,
            'updated_at': now,
        }},
    )
    return {'request_id': request['id'], 'deleted_counts': deleted_counts}


async def process_due_account_deletions(db: Any, limit: int = 10) -> Dict[str, int]:
    now = datetime.utcnow()
    requests = await db.account_deletion_requests.find({
        'status': {'$in': ['scheduled', 'retry']},
        'execute_after': {'$lte': now},
    }).sort('execute_after', 1).to_list(min(max(limit, 1), 50))
    completed = 0
    failed = 0
    for request in requests:
        await db.account_deletion_requests.update_one(
            {'id': request['id'], 'status': {'$in': ['scheduled', 'retry']}},
            {'$set': {'status': 'processing', 'updated_at': now}},
        )
        try:
            await delete_user_data(db, request)
            completed += 1
        except Exception as exc:
            await db.account_deletion_requests.update_one(
                {'id': request['id']},
                {'$set': {
                    'status': 'retry',
                    'last_error': str(exc)[:1_000],
                    'updated_at': datetime.utcnow(),
                }},
            )
            failed += 1
    return {'selected': len(requests), 'completed': completed, 'failed': failed}
