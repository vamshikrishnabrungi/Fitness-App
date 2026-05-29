"""AI-driven workout program generation using Claude Sonnet 4.5.

Given a fully populated UserProfile, this module produces a structured
multi-week training program with day-by-day workouts that respect:
  - primary + secondary goals
  - sport context (sport, role, competition level, season phase)
  - experience level
  - equipment + training location
  - schedule constraints (days/week, session duration, preferred days)
  - injuries, pain areas, medical notes
  - fitness assessment (pushups, pullups, squats, plank, run pace)

If the LLM is unavailable or fails, falls back to the deterministic rules
engine in :func:`fallback_program`.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from backend.ai.client import chat_json, llm_available
from backend.core.config import AI_WORKOUT_MODEL

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Profile summarisation for the AI prompt
# ---------------------------------------------------------------------------

def _list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _compact_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Trim a profile to the fields that actually influence a plan."""
    sport_details = profile.get('sport_details') or []
    return {
        'primary_goal': profile.get('primary_goal'),
        'secondary_goals': [g for g in _list(profile.get('selected_goals')) if g != profile.get('primary_goal')],
        'experience': profile.get('experience') or 'intermediate',
        'training_location': profile.get('training_location'),
        'equipment': _list(profile.get('equipment')),
        'sports': _list(profile.get('sports')),
        'sport_details': sport_details,
        'competition_level': profile.get('competition_level'),
        'season_phase': profile.get('season_phase'),
        'training_days_per_week': profile.get('training_days_per_week') or 4,
        'preferred_training_days': _list(profile.get('preferred_training_days')),
        'session_duration_min': profile.get('session_duration_min') or 45,
        'preferred_training_time': profile.get('preferred_training_time'),
        'schedule_constraints': profile.get('schedule_constraints'),
        'gender': profile.get('gender'),
        'age_years': _age_from_dob(profile.get('date_of_birth')),
        'height_cm': profile.get('height_cm'),
        'weight_kg': profile.get('weight_kg'),
        'target_weight_kg': profile.get('target_weight_kg'),
        'city': profile.get('city'),
        'country': profile.get('country'),
        'current_injuries': _list(profile.get('current_injuries')),
        'pain_areas': _list(profile.get('pain_areas')),
        'medical_notes': profile.get('medical_notes'),
        'sleep_avg_hours': profile.get('sleep_avg_hours'),
        'stress_level': profile.get('stress_level'),
        'fitness_assessment': profile.get('fitness_assessment') or {},
        'diet_preference': profile.get('diet_preference'),
        'dietary_restrictions': _list(profile.get('dietary_restrictions')),
        'nutrition_goal': profile.get('nutrition_goal'),
    }


def _age_from_dob(dob: Optional[str]) -> Optional[int]:
    if not dob:
        return None
    s = str(dob).strip()
    if not s:
        return None
    try:
        # frontend stores birth year as 4-digit string
        if len(s) == 4 and s.isdigit():
            return max(0, datetime.utcnow().year - int(s))
        parsed = datetime.fromisoformat(s.replace('Z', '+00:00'))
        return max(0, int((datetime.utcnow() - parsed.replace(tzinfo=None)).days / 365.25))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# AI prompt
# ---------------------------------------------------------------------------

PROGRAM_SCHEMA: Dict[str, Any] = {
    'type': 'object',
    'required': ['title', 'goal', 'duration_weeks', 'weeks'],
    'properties': {
        'title': {'type': 'string'},
        'goal': {'type': 'string'},
        'sports': {'type': 'array', 'items': {'type': 'string'}},
        'duration_weeks': {'type': 'integer', 'minimum': 4, 'maximum': 12},
        'description': {'type': 'string'},
        'nutrition_focus': {'type': 'string'},
        'recovery_focus': {'type': 'array', 'items': {'type': 'string'}},
        'safety_notes': {'type': 'array', 'items': {'type': 'string'}},
        'blocks': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'start_week': {'type': 'integer'},
                    'end_week': {'type': 'integer'},
                    'emphasis': {'type': 'array', 'items': {'type': 'string'}},
                },
            },
        },
        'weeks': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['week_number', 'workouts'],
                'properties': {
                    'week_number': {'type': 'integer'},
                    'theme': {'type': 'string'},
                    'progression_rule': {'type': 'string'},
                    'workouts': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'required': ['day', 'title', 'category', 'duration_min', 'main_work'],
                            'properties': {
                                'day': {'type': 'string'},
                                'title': {'type': 'string'},
                                'category': {'type': 'string'},
                                'duration_min': {'type': 'integer'},
                                'intensity': {'type': 'string'},
                                'description': {'type': 'string'},
                                'injury_modifications': {'type': 'array', 'items': {'type': 'string'}},
                                'main_work': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'required': ['name'],
                                        'properties': {
                                            'name': {'type': 'string'},
                                            'sets': {'type': 'integer'},
                                            'reps': {'type': 'string'},
                                            'duration': {'type': 'string'},
                                            'rest': {'type': 'string'},
                                            'notes': {'type': 'string'},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


SYSTEM_PROMPT = """You are an elite strength & conditioning coach building a personalised, evidence-based training program.

Your output is consumed directly by the app, so it MUST be valid JSON matching the provided schema.

Core principles:
- Respect the athlete's experience, equipment, and time per session - never prescribe what they can't do.
- Honour injuries and pain areas: provide pain-free substitutions, never load painful regions.
- Sport-specific transfer: if the athlete plays a sport, bias exercises toward that sport's demands.
- Progressive overload: week 1 builds movement quality, weeks 2-3 raise volume/load, week 4 consolidates or deloads.
- Recovery & nutrition focus must reflect the goal.
- Use concrete exercise names (e.g. "Goblet Squat", "Dumbbell Bench Press"), realistic sets/reps, and rest periods.
- If equipment is limited, use bodyweight + bands + dumbbells variations. Don't prescribe barbell work without a barbell.
"""


def _user_prompt(profile: Dict[str, Any]) -> str:
    compact = _compact_profile(profile)
    return (
        f'Build a 4-week training program for this athlete.\n\n'
        f'CONSTRAINTS:\n'
        f'- Sessions: {compact.get("session_duration_min")} min, '
        f'{compact.get("training_days_per_week")} days/week.\n'
        f'- Training location: {compact.get("training_location") or "unspecified"}.\n'
        f'- Equipment available: {compact.get("equipment") or "bodyweight only"}.\n'
        f'- Preferred days: {compact.get("preferred_training_days") or "flexible"}.\n'
        f'- Pain areas to protect: {compact.get("pain_areas") or "none"}.\n'
        f'- Current injuries: {compact.get("current_injuries") or "none"}.\n\n'
        f'For each session include 4-7 exercises with concrete sets/reps/rest. '
        f'Use "duration" instead of "reps" only for timed exercises (planks, runs, intervals). '
        f'Week 1 = movement quality + intro load. Week 2 = build. Week 3 = peak. Week 4 = deload (-30% volume).\n\n'
        f'Athlete profile:\n{json.dumps(compact, default=str, indent=2)}\n\n'
        f'Required JSON schema:\n{json.dumps(PROGRAM_SCHEMA)}\n\n'
        f'Return ONLY the JSON object.'
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def generate_program(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an AI program; raise on failure (caller picks fallback)."""
    if not llm_available():
        raise RuntimeError('LLM not configured')

    parsed = await chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_user_prompt(profile),
        model=AI_WORKOUT_MODEL,
        provider='anthropic',
        session_id=f'program-{uuid.uuid4()}',
        max_tokens=16384,
    )
    return _normalise(parsed, profile)


# ---------------------------------------------------------------------------
# Normalisation / shape coercion
# ---------------------------------------------------------------------------

ALLOWED_CATEGORIES = {'Strength', 'Conditioning', 'Power', 'Mobility', 'Hypertrophy', 'Endurance', 'Recovery', 'Skill'}


def _coerce_exercise_list(items: Any) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get('name') or '').strip()
        if not name:
            continue
        out.append({
            'name': name,
            'sets': item.get('sets'),
            'reps': item.get('reps') if item.get('reps') is None else str(item.get('reps')),
            'duration': item.get('duration') if item.get('duration') is None else str(item.get('duration')),
            'rest': item.get('rest') if item.get('rest') is None else str(item.get('rest')),
            'load_guidance': item.get('load_guidance'),
            'tempo': item.get('tempo'),
            'notes': item.get('notes'),
            'substitutions': item.get('substitutions') or [],
        })
    return out


def _normalise(plan: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    weeks_raw = plan.get('weeks') or []
    if not isinstance(weeks_raw, list) or not weeks_raw:
        raise ValueError('Program has no weeks')

    weeks: List[Dict[str, Any]] = []
    for index, week in enumerate(weeks_raw):
        if not isinstance(week, dict):
            continue
        workouts_raw = week.get('workouts') or []
        workouts: List[Dict[str, Any]] = []
        for w in workouts_raw:
            if not isinstance(w, dict):
                continue
            category = str(w.get('category') or 'Strength').title()
            if category not in ALLOWED_CATEGORIES:
                category = 'Strength'
            # exercises may be supplied either as a flat list or split into warmup/main/cooldown
            warmup = _coerce_exercise_list(w.get('warmup'))
            main = _coerce_exercise_list(w.get('main_work') or w.get('exercises'))
            cooldown = _coerce_exercise_list(w.get('cooldown'))
            if not main and not warmup and not cooldown:
                continue
            workouts.append({
                'day': str(w.get('day') or 'Monday'),
                'title': str(w.get('title') or f'{category} Session'),
                'category': category,
                'duration_min': int(w.get('duration_min') or profile.get('session_duration_min') or 45),
                'intensity': str(w.get('intensity') or 'moderate').lower(),
                'description': w.get('description'),
                'adaptation_targets': w.get('adaptation_targets') or [],
                'injury_modifications': w.get('injury_modifications') or [],
                'warmup': warmup,
                'main_work': main,
                'cooldown': cooldown,
                'exercises': main if main else (warmup + cooldown),
            })
        if not workouts:
            continue
        weeks.append({
            'week_number': int(week.get('week_number') or index + 1),
            'theme': week.get('theme') or '',
            'progression_rule': week.get('progression_rule') or '',
            'deload_note': week.get('deload_note'),
            'workouts': workouts,
        })

    if not weeks:
        raise ValueError('Program contained no usable workouts')

    duration_weeks = int(plan.get('duration_weeks') or len(weeks))
    sports = plan.get('sports') or _list(profile.get('sports'))
    title = str(plan.get('title') or f"{(sports[0] if sports else 'Athletic')} Program").strip()

    blocks = plan.get('blocks') or [{
        'name': 'Foundation',
        'start_week': 1,
        'end_week': duration_weeks,
        'emphasis': ['movement quality', 'progressive load', 'sport transfer', 'recovery'],
    }]

    return {
        'title': title,
        'goal': str(plan.get('goal') or profile.get('primary_goal') or 'athletic performance'),
        'sports': sports,
        'duration_weeks': max(duration_weeks, len(weeks)),
        'description': plan.get('description'),
        'nutrition_focus': plan.get('nutrition_focus'),
        'recovery_focus': plan.get('recovery_focus') or [],
        'safety_notes': plan.get('safety_notes') or [],
        'assumptions': plan.get('assumptions') or [],
        'blocks': blocks,
        'weeks': weeks,
        'source': 'ai',
    }


# ---------------------------------------------------------------------------
# Rule-based fallback (kept lightweight - mirrors the original helper)
# ---------------------------------------------------------------------------

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def fallback_program(profile: Dict[str, Any]) -> Dict[str, Any]:
    days_per_week = max(3, min(6, int(profile.get('training_days_per_week') or 4)))
    duration_min = max(30, min(90, int(profile.get('session_duration_min') or 45)))
    sports = _list(profile.get('sports'))
    equipment = [str(e).lower() for e in _list(profile.get('equipment'))]
    has_gym = any(item in equipment for item in ['gym', 'barbell', 'dumbbells', 'machine', 'kettlebell'])
    primary_goal = str(profile.get('primary_goal') or 'athletic performance').lower()
    is_runner = any('run' in str(s).lower() or s in ('5k', '10k', 'marathon') for s in sports)
    field_sport = any(str(s).lower() in ('cricket', 'football', 'soccer', 'basketball', 'volleyball', 'tennis', 'badminton') for s in sports)

    lower_main = 'Back Squat' if has_gym else 'Goblet Squat'
    hinge = 'Romanian Deadlift' if has_gym else 'Single-leg Hip Hinge'
    press = 'Dumbbell Bench Press' if has_gym else 'Push-up'
    pull = 'Seated Cable Row' if has_gym else 'Band Row'

    templates: List[Dict[str, Any]] = [
        {
            'title': 'Lower Strength + Core',
            'category': 'Strength',
            'main_work': [
                {'name': lower_main, 'sets': 4, 'reps': '6-8', 'rest': '90 sec'},
                {'name': hinge, 'sets': 3, 'reps': '8-10', 'rest': '75 sec'},
                {'name': 'Split Squat', 'sets': 3, 'reps': '8/side', 'rest': '60 sec'},
                {'name': 'Dead Bug', 'sets': 3, 'reps': '10/side', 'rest': '45 sec'},
            ],
        },
        {
            'title': 'Speed + Conditioning' if (field_sport or is_runner) else 'Tempo Conditioning',
            'category': 'Conditioning',
            'main_work': [
                {'name': 'Acceleration Runs', 'sets': 6, 'reps': '20 m', 'rest': '60 sec'},
                {'name': 'Zone 2 Run' if is_runner else 'Tempo Intervals', 'duration': '20 min'},
            ],
        },
        {
            'title': 'Upper Strength + Shoulder Care',
            'category': 'Strength',
            'main_work': [
                {'name': press, 'sets': 4, 'reps': '8-10', 'rest': '75 sec'},
                {'name': pull, 'sets': 4, 'reps': '10-12', 'rest': '75 sec'},
                {'name': 'Half-kneeling Press', 'sets': 3, 'reps': '8/side', 'rest': '60 sec'},
                {'name': 'Face Pull', 'sets': 3, 'reps': '15', 'rest': '45 sec'},
            ],
        },
        {
            'title': 'Mobility + Recovery',
            'category': 'Mobility',
            'main_work': [
                {'name': 'Breathing Reset', 'duration': '5 min'},
                {'name': 'Hip Mobility Flow', 'duration': '8 min'},
                {'name': 'Thoracic Rotation', 'sets': 2, 'reps': '10/side'},
                {'name': 'Easy Walk', 'duration': '20 min'},
            ],
        },
    ]
    if field_sport:
        templates.append({
            'title': 'Jump + Change of Direction',
            'category': 'Power',
            'main_work': [
                {'name': 'Pogo Jumps', 'sets': 3, 'reps': '20 sec', 'rest': '45 sec'},
                {'name': 'Broad Jump', 'sets': 4, 'reps': '3', 'rest': '75 sec'},
                {'name': '5-10-5 Shuttle', 'sets': 5, 'reps': '1 rep', 'rest': '90 sec'},
            ],
        })

    weeks: List[Dict[str, Any]] = []
    preferred = _list(profile.get('preferred_training_days')) or DAY_NAMES
    for week_number in range(1, 5):
        week_workouts: List[Dict[str, Any]] = []
        for i in range(days_per_week):
            tmpl = templates[i % len(templates)]
            day = preferred[i % len(preferred)] if preferred else DAY_NAMES[i % 7]
            week_workouts.append({
                'day': str(day),
                'title': f"{day}: {tmpl['title']}",
                'category': tmpl['category'],
                'duration_min': duration_min,
                'intensity': 'high' if week_number == 3 else ('low' if week_number == 4 else 'moderate'),
                'description': f'Week {week_number} - {tmpl["title"]}',
                'adaptation_targets': [primary_goal],
                'injury_modifications': [],
                'warmup': [{'name': 'Dynamic Warm-up', 'duration': '8 min'}],
                'main_work': tmpl['main_work'],
                'cooldown': [{'name': 'Static Stretch', 'duration': '5 min'}],
                'exercises': tmpl['main_work'],
            })
        weeks.append({
            'week_number': week_number,
            'theme': ['Foundation', 'Build', 'Peak', 'Deload'][week_number - 1],
            'progression_rule': 'Add 2.5% load or 1 rep per set if all reps complete with good form.',
            'deload_note': 'Reduce volume by 30% this week.' if week_number == 4 else None,
            'workouts': week_workouts,
        })

    return {
        'title': f"{(sports[0] if sports else 'Athletic')} Foundation Program",
        'goal': primary_goal,
        'sports': sports,
        'duration_weeks': 4,
        'description': 'Auto-generated foundation plan (rules engine).',
        'nutrition_focus': 'Protein at every meal, prioritise carbs around training.',
        'recovery_focus': ['Sleep 7-9 hours', 'Easy walking on off days'],
        'safety_notes': ['Stop any movement above 3/10 pain.'],
        'assumptions': ['Rules-engine fallback used because AI was unavailable.'],
        'blocks': [{'name': 'Foundation', 'start_week': 1, 'end_week': 4, 'emphasis': ['movement quality', 'progressive load']}],
        'weeks': weeks,
        'source': 'rules_engine',
    }


# ---------------------------------------------------------------------------
# Materialise plan into DB documents
# ---------------------------------------------------------------------------

async def persist_program(db: Any, user_id: str, profile: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    """Save program + blocks + per-session workout docs. Returns summary."""
    now = datetime.utcnow()
    program_id = str(uuid.uuid4())
    program_doc = {
        'id': program_id,
        'user_id': user_id,
        'title': plan['title'],
        'goal': plan['goal'],
        'sports': plan.get('sports') or [],
        'status': 'active',
        'source': plan.get('source', 'ai'),
        'model': AI_WORKOUT_MODEL if plan.get('source') == 'ai' else None,
        'duration_weeks': plan.get('duration_weeks', 4),
        'current_week': 1,
        'description': plan.get('description'),
        'nutrition_focus': plan.get('nutrition_focus'),
        'recovery_focus': plan.get('recovery_focus') or [],
        'safety_notes': plan.get('safety_notes') or [],
        'assumptions': plan.get('assumptions') or [],
        'profile_snapshot': profile,
        'created_at': now,
        'updated_at': now,
    }

    # archive previous active programs
    await db.training_programs.update_many(
        {'user_id': user_id, 'status': 'active'},
        {'$set': {'status': 'archived', 'archived_at': now}},
    )
    await db.training_programs.insert_one(dict(program_doc))

    blocks_out: List[Dict[str, Any]] = []
    for block in plan.get('blocks') or []:
        block_doc = {
            'id': str(uuid.uuid4()),
            'program_id': program_id,
            'user_id': user_id,
            'name': block.get('name') or 'Block',
            'week_start': int(block.get('start_week') or 1),
            'week_end': int(block.get('end_week') or plan.get('duration_weeks', 4)),
            'emphasis': block.get('emphasis') or [],
            'created_at': now,
        }
        await db.program_blocks.insert_one(dict(block_doc))
        blocks_out.append(block_doc)

    # only delete pending future workouts (don't trash history)
    today_str = now.strftime('%Y-%m-%d')
    await db.workouts.delete_many({
        'user_id': user_id,
        'completed': {'$ne': True},
        'scheduled_date': {'$gte': today_str},
    })

    workout_docs: List[Dict[str, Any]] = []
    week_one_start = now  # schedule first session today
    for week in plan.get('weeks') or []:
        week_number = int(week.get('week_number') or 1)
        for index, w in enumerate(week.get('workouts') or []):
            scheduled = week_one_start + timedelta(days=(week_number - 1) * 7 + index)
            workout_doc = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'program_id': program_id,
                'week_number': week_number,
                'session_number': index + 1,
                'title': w['title'],
                'category': w['category'],
                'duration': w['duration_min'],
                'difficulty': str(profile.get('experience') or 'intermediate').title(),
                'equipment': profile.get('equipment') or [],
                'exercises': w.get('exercises') or w.get('main_work') or [],
                'warmup': w.get('warmup') or [],
                'main_work': w.get('main_work') or [],
                'cooldown': w.get('cooldown') or [],
                'description': w.get('description') or w['title'],
                'adaptation_targets': w.get('adaptation_targets') or [],
                'injury_modifications': w.get('injury_modifications') or [],
                'intensity': w.get('intensity') or 'moderate',
                'ai_generated': plan.get('source') == 'ai',
                'source': plan.get('source', 'ai'),
                'scheduled_date': scheduled.strftime('%Y-%m-%d'),
                'completed': False,
                'created_at': now,
            }
            await db.workouts.insert_one(dict(workout_doc))
            workout_docs.append(workout_doc)

    return {
        'program': program_doc,
        'blocks': blocks_out,
        'workouts': workout_docs,
    }
