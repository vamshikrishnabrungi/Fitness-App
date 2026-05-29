"""Workout & program routes with non-blocking AI upgrade.

The challenge: Claude Sonnet 4.5 takes 90-110 seconds to produce a full
4-week program. The preview-cluster ingress has a ~100s read timeout, so
serving the AI call on the request path is unreliable.

Strategy:
    1. Build the rules-engine fallback synchronously (fast, deterministic)
       and persist it. The user gets an immediately-usable plan.
    2. Spawn an asyncio background task that calls the AI; when it
       finishes, the same program document is upgraded in place (workouts
       replaced) and ``status`` flips ``generating`` -> ``active``.
    3. The frontend can either ignore the AI upgrade (the fallback is real
       work the user can do) or poll ``GET /api/workouts/program-status``.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from backend.ai import workout_ai
from backend.core.db import db
from backend.core.security import deep_clean, get_current_user
from backend.models import OnboardingComplete

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Profile + builder helpers
# ---------------------------------------------------------------------------

async def _user_profile(user: dict) -> Dict[str, Any]:
    athlete = await db.athlete_profiles.find_one({'user_id': user['id']})
    if athlete and athlete.get('raw_profile'):
        return dict(athlete['raw_profile'])
    return dict(user.get('profile') or {})


async def _upgrade_program_with_ai(user_id: str, program_id: str, profile: Dict[str, Any]) -> None:
    """Run Claude in the background and replace the persisted program."""
    try:
        plan = await workout_ai.generate_program(profile)
    except Exception as exc:
        logger.warning(
            'AI program upgrade failed for user=%s program=%s err=%s', user_id, program_id, exc,
        )
        await db.training_programs.update_one(
            {'id': program_id},
            {'$set': {'status': 'active', 'ai_error': str(exc), 'updated_at': datetime.utcnow()}},
        )
        return
    try:
        await workout_ai.persist_program(
            db, user_id, profile, plan, program_id=program_id, initial_status='active',
        )
        logger.info('AI upgrade persisted for user=%s program=%s title=%s', user_id, program_id, plan['title'])
    except Exception as exc:  # pragma: no cover
        logger.exception('Failed to persist AI upgrade for user=%s: %s', user_id, exc)
        await db.training_programs.update_one(
            {'id': program_id},
            {'$set': {'status': 'active', 'ai_error': str(exc), 'updated_at': datetime.utcnow()}},
        )


async def _build_program_for(user: dict, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a fallback plan synchronously and trigger an async AI upgrade."""
    fallback_plan = workout_ai.fallback_program(profile)
    persisted = await workout_ai.persist_program(
        db, user['id'], profile, fallback_plan, initial_status='generating',
    )

    program_id = persisted['program']['id']
    if workout_ai.llm_available():
        # fire-and-forget: AI runs in the background and upgrades the program
        asyncio.create_task(_upgrade_program_with_ai(user['id'], program_id, profile))

    return {
        'program': deep_clean(persisted['program']),
        'blocks': deep_clean(persisted['blocks']),
        'weekly_plan': [deep_clean(w) for w in persisted['workouts']],
        'source': fallback_plan.get('source', 'rules_engine'),
        'ai_status': 'generating' if workout_ai.llm_available() else 'disabled',
        'duration_weeks': fallback_plan.get('duration_weeks'),
        'assumptions': fallback_plan.get('assumptions', []),
        'safety_notes': fallback_plan.get('safety_notes', []),
        'nutrition_focus': fallback_plan.get('nutrition_focus'),
        'recovery_focus': fallback_plan.get('recovery_focus', []),
    }


def workout_ai_available() -> bool:
    return workout_ai.llm_available()


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


@router.get('/workouts/program-status')
async def program_status(current_user: dict = Depends(get_current_user)):
    """Latest active/generating program for the current user."""
    program = await db.training_programs.find_one(
        {'user_id': current_user['id'], 'status': {'$in': ['active', 'generating']}},
        sort=[('updated_at', -1)],
    )
    if not program:
        return {'has_program': False}
    program = deep_clean(program)
    return {
        'has_program': True,
        'program_id': program['id'],
        'status': program.get('status', 'active'),
        'source': program.get('source', 'rules_engine'),
        'ai_status': 'ready' if program.get('source') == 'ai' else (
            'generating' if program.get('status') == 'generating' else 'fallback'
        ),
        'title': program.get('title'),
        'duration_weeks': program.get('duration_weeks'),
        'ai_error': program.get('ai_error'),
        'updated_at': program.get('updated_at'),
    }


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
    if not payload.generate_program:
        return {'status': 'profile_saved', 'program': None}
    return await _build_program_for(current_user, profile_doc)
