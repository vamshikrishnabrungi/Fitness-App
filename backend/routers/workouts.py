"""Workout & program routes.

These supersede the in-server.py rule-only generators with the AI-driven
``backend.ai.workout_ai`` pipeline. Endpoint contracts are unchanged.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.ai import workout_ai
from backend.core.db import db
from backend.core.security import deep_clean, get_current_user
from backend.helpers import clean_doc
from backend.models import OnboardingComplete, AthleteProfileUpsert

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _user_profile(user: dict) -> Dict[str, Any]:
    athlete = await db.athlete_profiles.find_one({'user_id': user['id']})
    if athlete and athlete.get('raw_profile'):
        return dict(athlete['raw_profile'])
    return dict(user.get('profile') or {})


async def _build_program_for(user: dict, profile: Dict[str, Any]) -> Dict[str, Any]:
    plan: Dict[str, Any]
    try:
        plan = await workout_ai.generate_program(profile)
        logger.info('AI program generated for user=%s title=%s weeks=%d', user['id'], plan['title'], len(plan['weeks']))
    except Exception as exc:  # pragma: no cover - network / quota
        logger.warning('AI program generation failed (%s); falling back to rules engine', exc)
        plan = workout_ai.fallback_program(profile)

    persisted = await workout_ai.persist_program(db, user['id'], profile, plan)
    return {
        'program': deep_clean(persisted['program']),
        'blocks': deep_clean(persisted['blocks']),
        'weekly_plan': [deep_clean(w) for w in persisted['workouts']],
        'source': plan.get('source', 'ai'),
        'duration_weeks': plan.get('duration_weeks'),
        'assumptions': plan.get('assumptions', []),
        'safety_notes': plan.get('safety_notes', []),
        'nutrition_focus': plan.get('nutrition_focus'),
        'recovery_focus': plan.get('recovery_focus', []),
    }


# ---------------------------------------------------------------------------
# Workout listing & lifecycle
# ---------------------------------------------------------------------------

@router.get('/workouts')
async def list_workouts(current_user: dict = Depends(get_current_user)):
    docs = await db.workouts.find({'user_id': current_user['id']}).sort('scheduled_date', 1).to_list(200)
    return [deep_clean(doc) for doc in docs]


@router.get('/workouts/today')
async def workouts_today(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().strftime('%Y-%m-%d')
    today_workouts = await db.workouts.find({
        'user_id': current_user['id'],
        'scheduled_date': today,
    }).to_list(20)
    if today_workouts:
        return [deep_clean(doc) for doc in today_workouts]
    upcoming = await db.workouts.find({
        'user_id': current_user['id'],
        'completed': {'$ne': True},
        'scheduled_date': {'$gte': today},
    }).sort('scheduled_date', 1).limit(3).to_list(3)
    return [deep_clean(doc) for doc in upcoming]


@router.post('/workouts/{workout_id}/complete')
async def complete_workout(workout_id: str, current_user: dict = Depends(get_current_user)):
    now = datetime.utcnow()
    result = await db.workouts.update_one(
        {'id': workout_id, 'user_id': current_user['id']},
        {'$set': {'completed': True, 'completed_at': now}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Workout not found')
    doc = await db.workouts.find_one({'id': workout_id, 'user_id': current_user['id']})
    return deep_clean(doc or {})


@router.post('/workouts/{workout_id}/feedback')
async def workout_feedback(workout_id: str, payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    result = await db.workouts.update_one(
        {'id': workout_id, 'user_id': current_user['id']},
        {'$set': {'user_feedback': payload, 'feedback_at': datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Workout not found')
    return {'status': 'ok'}


# ---------------------------------------------------------------------------
# Program generation
# ---------------------------------------------------------------------------

@router.post('/workouts/generate-weekly')
async def generate_weekly_program(current_user: dict = Depends(get_current_user)):
    profile = await _user_profile(current_user)
    if not profile:
        raise HTTPException(status_code=400, detail='Complete onboarding first')
    return await _build_program_for(current_user, profile)


@router.post('/onboarding/complete')
async def onboarding_complete(payload: OnboardingComplete, current_user: dict = Depends(get_current_user)):
    # 1) save profile to user + athlete_profiles
    profile_doc = payload.profile.model_dump()
    if profile_doc.get('onboarding_completed_at') is None:
        profile_doc['onboarding_completed_at'] = datetime.utcnow()
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': {'profile': profile_doc, 'updated_at': datetime.utcnow()}},
    )
    await db.athlete_profiles.update_one(
        {'user_id': current_user['id']},
        {
            '$set': {
                'user_id': current_user['id'],
                'email': current_user.get('email'),
                'name': current_user.get('name'),
                'raw_profile': profile_doc,
                'goals': profile_doc.get('selected_goals') or profile_doc.get('goals') or [],
                'primary_goal': profile_doc.get('primary_goal'),
                'sports': profile_doc.get('sports') or [],
                'experience': profile_doc.get('experience'),
                'updated_at': datetime.utcnow(),
            },
            '$setOnInsert': {'created_at': datetime.utcnow()},
        },
        upsert=True,
    )
    # 2) build program
    if not payload.generate_program:
        return {'status': 'profile_saved', 'program': None}
    return await _build_program_for(current_user, profile_doc)
