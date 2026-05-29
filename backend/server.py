from fastapi import FastAPI, APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid
import os
import logging
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from backend.helpers import (
    clean_doc,
    _parse_iso_datetime,
    _normalize_tags,
    _journal_word_count,
    _journal_responses_text,
    _journal_entry_text,
    _journal_entry_response,
    _journal_program_definitions,
    _journal_template_definitions,
    _journal_template_by_id,
    _journal_program_by_id,
    _journal_program_day,
    _journal_entry_date_for,
    _journal_searchable_text,
    _optional_float,
    _to_non_negative_int,
    _to_non_negative_float,
    _sleep_quality_label,
    _sleep_status_from_score,
    _sleep_efficiency_value,
    _sleep_session_duration_hours,
    _sleep_session_metrics,
    _sleep_session_response,
    _terra_level_from_xp,
    _terra_referral_code,
    _terra_haversine_km,
    _terra_normalize_path,
    _terra_run_distance_km,
    _terra_run_duration_seconds,
    _terra_run_territory_km2,
    _terra_run_xp,
    _terra_run_response,
    _terra_run_history_runs,
    _terra_competition_current,
    _terra_vault_catalog,
    _terra_placeholder_training_plans,
    _terra_feed_post_response,
    _terra_training_plan_response,
    _terra_plan_weeks,
)
from backend.db_setup import ensure_database_schema
from backend.models import (
    UserProfile,
    UserCreate,
    UserLogin,
    OtpRequest,
    OtpVerify,
    PasswordReset,
    UserUpdate,
    AthleteProfileUpsert,
    OnboardingComplete,
    WorkoutExercise,
    Workout,
    WorkoutFeedback,
    ProgramGenerationOutput,
    DailyActivitySnapshot,
    DailySnapshotTotals,
    DailyCoachAnalysis,
    Meal,
    MealCreate,
    QuickLog,
    QuickLogCreate,
    SleepNoteCreate,
    SleepSessionCreate,
    MoodCreate,
    MoodEntry,
    InjuryLog,
    InjuryLogCreate,
    StrainSummary,
    RecoverySummary,
    BiologySummary,
    ProgramSummary,
    Lesson,
    DeepJournalCreate,
    GuidedJournalCreate,
    JournalSearchRequest,
    TerraGpsPoint,
    TerraRunCreate,
    TerraReflectionCreate,
    TerraFeedCreate,
    TerraTrainingPlanCreate,
    RunClubCreate,
)
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
except Exception:
    LlmChat = None  # type: ignore
    UserMessage = None  # type: ignore
    ImageContent = None  # type: ignore

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# -------------------- CONFIG --------------------
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'sftc_database')
JWT_SECRET = os.environ.get('JWT_SECRET', 'sftc-dev-secret')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_DAYS = 30
LLM_API_KEY = (
    os.environ.get('OPENAI_API_KEY')
    or os.environ.get('EXPO_PUBLIC_VIBECODE_OPENAI_API_KEY')
    or os.environ.get('EMERGENT_LLM_KEY')
)
LLM_BASE_URL = os.environ.get('OPENAI_BASE_URL')
LLM_MODEL = os.environ.get('MEAL_AI_MODEL', 'gpt-4o-mini')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# -------------------- APP --------------------
app = FastAPI(title='SFTC API', version='2.2.0')
api_router = APIRouter(prefix='/api')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
security = HTTPBearer()
_openai_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('EXPO_PUBLIC_VIBECODE_OPENAI_API_KEY')
openai_client = OpenAI(api_key=_openai_key, base_url=LLM_BASE_URL) if _openai_key else None


@app.on_event('startup')
async def startup_database() -> None:
    await ensure_database_schema(db)
    logger.info('MongoDB schema ready: %s', DB_NAME)

# -------------------- HELPERS --------------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


async def _terra_user_run_docs(user_id: str) -> List[Dict[str, Any]]:
    terra_runs = await db.terra_runs.find({'user_id': user_id}).to_list(200)
    legacy_runs = await db.runs.find({'user_id': user_id}).to_list(200)
    docs: Dict[str, Dict[str, Any]] = {}
    for run in [*legacy_runs, *terra_runs]:
        run_id = str(run.get('id') or uuid.uuid4())
        docs[run_id] = dict(run)
    ordered = sorted(
        docs.values(),
        key=lambda doc: _parse_iso_datetime(doc.get('created_at')) or _parse_iso_datetime(doc.get('date')) or datetime.min,
        reverse=True,
    )
    return ordered


async def _terra_user_summary(user: Dict[str, Any], is_me: bool = False) -> Dict[str, Any]:
    run_docs = await _terra_user_run_docs(user['id'])
    total_distance = round(sum(_terra_run_distance_km(run) for run in run_docs), 1)
    total_territory = round(sum(_terra_run_territory_km2(run) for run in run_docs), 4)
    xp = sum(_terra_run_xp(run) for run in run_docs)
    return {
        'id': user['id'],
        'username': user.get('name') or user.get('email', 'Runner'),
        'xp': xp,
        'level': _terra_level_from_xp(float(xp)),
        'total_territory': total_territory,
        'total_distance': total_distance,
        'is_me': is_me,
    }


async def _terra_all_user_summaries(include_placeholders: bool = True, current_user: Optional[dict] = None) -> List[Dict[str, Any]]:
    users = await db.users.find({'mode': {'$ne': 'coach'}}).to_list(200)
    summaries: List[Dict[str, Any]] = []

    for user in users:
        run_docs = await _terra_user_run_docs(user['id'])
        if not run_docs:
            continue
        summaries.append(await _terra_user_summary(user, is_me=bool(current_user and user['id'] == current_user['id'])))

    if current_user and not any(entry['id'] == current_user['id'] for entry in summaries):
        summaries.append(await _terra_user_summary(current_user, is_me=True))

    summaries.sort(key=lambda item: (item['xp'], item['total_distance'], item['total_territory']), reverse=True)

    if include_placeholders and len(summaries) < 5:
        placeholder_names = [
            'Trail Nova',
            'Runner Atlas',
            'Mira Ridge',
            'Pace Orion',
            'Summit Ember',
            'Beacon Vale',
        ]
        existing_names = {summary['username'] for summary in summaries}
        base_xp = summaries[0]['xp'] if summaries else 480
        for index, name in enumerate(placeholder_names):
            if name in existing_names:
                continue
            xp = max(120, base_xp - (index + 1) * 55)
            total_distance = round(max(4.0, xp / 32.0), 1)
            total_territory = round(max(0.2, xp / 1800.0), 4)
            summaries.append({
                'id': f'placeholder-{index + 1}',
                'username': name,
                'xp': xp,
                'level': _terra_level_from_xp(float(xp)),
                'total_territory': total_territory,
                'total_distance': total_distance,
                'is_me': False,
            })
            if len(summaries) >= 5:
                break
        summaries.sort(key=lambda item: (item['xp'], item['total_distance'], item['total_territory']), reverse=True)

    return summaries


async def _terra_stats_bundle(current_user: dict) -> Dict[str, Any]:
    runs = await _terra_user_run_docs(current_user['id'])
    total_runs = len(runs)
    total_distance = round(sum(_terra_run_distance_km(run) for run in runs), 1)
    total_duration = sum(_terra_run_duration_seconds(run) for run in runs)
    total_territory = round(sum(_terra_run_territory_km2(run) for run in runs), 4)
    total_xp = sum(_terra_run_xp(run) for run in runs)
    level = _terra_level_from_xp(float(total_xp))

    history = _terra_run_history_runs(runs)
    days_with_runs = sum(1 for day in history if day['value'] > 0)
    consistency = int((days_with_runs / 7) * 100) if history else 0
    average_pace = None
    if total_distance > 0:
        pace_seconds = total_duration / total_distance
        mins = int(pace_seconds // 60)
        secs = int(pace_seconds % 60)
        average_pace = f"{mins}'{secs:02d}"

    leaderboard = await _terra_all_user_summaries(include_placeholders=False, current_user=current_user)
    friends_count = max(0, len([entry for entry in leaderboard if entry['id'] != current_user['id']]))

    return {
        'total_runs': total_runs,
        'total_distance': total_distance,
        'total_territory': total_territory,
        'xp': total_xp,
        'level': level,
        'competition_entries': total_runs,
        'territories_owned': sum(1 for run in runs if _terra_run_territory_km2(run) > 0),
        'referral_code': _terra_referral_code(current_user),
        'friends_count': friends_count,
        'average_pace': average_pace,
        'fatigue': 'Low' if total_distance == 0 else ('High' if total_distance > 20 else 'Moderate'),
        'consistency': consistency,
        'history': history,
    }


def _run_period_start(period: str) -> Optional[datetime]:
    today = datetime.utcnow().date()
    period = (period or 'week').lower()
    if period == 'all':
        return None
    if period == 'month':
        return datetime(today.year, today.month, 1)
    week_start = today - timedelta(days=today.weekday())
    return datetime.combine(week_start, datetime.min.time())


def _run_in_period(run: Dict[str, Any], period_start: Optional[datetime]) -> bool:
    if period_start is None:
        return True
    run_dt = (
        _parse_iso_datetime(run.get('date'))
        or _parse_iso_datetime(run.get('end_time'))
        or _parse_iso_datetime(run.get('created_at'))
    )
    return bool(run_dt and run_dt >= period_start)


def _user_city(user: Dict[str, Any]) -> str:
    profile = user.get('profile') or {}
    for key in ('city', 'hometown', 'location'):
        value = str(profile.get(key) or '').strip()
        if value:
            return value
    return 'Your City'


async def _run_club_member_docs(member_ids: List[str]) -> List[Dict[str, Any]]:
    users = await db.users.find({'id': {'$in': member_ids}}).to_list(200)
    by_id = {user['id']: user for user in users}
    return [by_id[user_id] for user_id in member_ids if user_id in by_id]


async def _run_club_totals(club: Dict[str, Any], period: str = 'week') -> Dict[str, Any]:
    member_ids = [str(member_id) for member_id in club.get('member_ids', []) if str(member_id).strip()]
    period_start = _run_period_start(period)
    total_distance = 0.0
    total_territory = 0.0
    total_runs = 0
    active_members = 0

    for member_id in member_ids:
        member_runs = [run for run in await _terra_user_run_docs(member_id) if _run_in_period(run, period_start)]
        member_distance = sum(_terra_run_distance_km(run) for run in member_runs)
        total_distance += member_distance
        total_territory += sum(_terra_run_territory_km2(run) for run in member_runs)
        total_runs += len(member_runs)
        if member_distance > 0:
            active_members += 1

    member_count = len(member_ids)
    return {
        'total_distance': round(total_distance, 1),
        'total_territory': round(total_territory, 4),
        'total_runs': total_runs,
        'active_members': active_members,
        'member_count': member_count,
        'average_distance_per_member': round(total_distance / member_count, 1) if member_count else 0.0,
    }


async def _run_club_response(club: Dict[str, Any], current_user: Optional[dict] = None, period: str = 'week') -> Dict[str, Any]:
    cleaned = clean_doc(dict(club))
    cleaned.setdefault('member_ids', [])
    cleaned['member_count'] = len(cleaned['member_ids'])
    cleaned['is_member'] = bool(current_user and current_user['id'] in cleaned['member_ids'])
    cleaned.update(await _run_club_totals(cleaned, period))
    return cleaned


async def _run_club_member_leaderboard(club: Dict[str, Any], period: str = 'week') -> List[Dict[str, Any]]:
    member_ids = [str(member_id) for member_id in club.get('member_ids', []) if str(member_id).strip()]
    users = await _run_club_member_docs(member_ids)
    period_start = _run_period_start(period)
    rows = []
    for user in users:
        runs = [run for run in await _terra_user_run_docs(user['id']) if _run_in_period(run, period_start)]
        total_distance = round(sum(_terra_run_distance_km(run) for run in runs), 1)
        total_territory = round(sum(_terra_run_territory_km2(run) for run in runs), 4)
        rows.append({
            'user_id': user['id'],
            'username': user.get('name') or user.get('email', 'Runner'),
            'total_distance': total_distance,
            'total_territory': total_territory,
            'total_runs': len(runs),
        })
    rows.sort(key=lambda row: (row['total_distance'], row['total_runs'], row['total_territory']), reverse=True)
    return [{**row, 'rank': index + 1} for index, row in enumerate(rows)]


def _terra_competition_current() -> Dict[str, Any]:
    now = datetime.utcnow()
    return {
        'name': 'Terra Weekly Frontier',
        'prize': 'Top run clubs earn the city distance crown.',
        'description': 'Run, reflect, and keep the streak alive to lift your club on the city leaderboard.',
        'days_remaining': max(1, 7 - now.weekday()),
    }


def _terra_vault_catalog(stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    level = int(stats.get('level') or 1)
    territory = float(stats.get('total_territory') or 0.0)

    catalog = [
        {'id': 'vault-ember', 'type': 'territory_color', 'name': 'Ember Trail', 'value': '#FF7A45', 'unlock_level': 1},
        {'id': 'vault-aqua', 'type': 'territory_color', 'name': 'Aqua Drift', 'value': '#2D9CDB', 'unlock_level': 2},
        {'id': 'vault-badge', 'type': 'badge', 'name': 'Loop Hunter', 'value': '🔁', 'unlock_level': 2},
        {'id': 'vault-flame', 'type': 'badge', 'name': 'Frontier Flame', 'value': '🔥', 'unlock_level': 3},
        {'id': 'vault-crown', 'type': 'badge', 'name': 'Trail Crown', 'value': '👑', 'unlock_level': 4},
        {'id': 'vault-aurora', 'type': 'territory_color', 'name': 'Aurora Line', 'value': '#52D273', 'unlock_level': 4},
        {'id': 'vault-titan', 'type': 'badge', 'name': 'Titan Crest', 'value': '🏔️', 'unlock_level': 5},
        {'id': 'vault-legend', 'type': 'badge', 'name': 'Legend Mark', 'value': '⭐', 'unlock_level': 6},
    ]

    unlocked_by_territory = 1 + int(territory // 0.5)
    unlocked_threshold = max(level, unlocked_by_territory)
    return [
        {
            **item,
            'unlocked': unlocked_threshold >= item['unlock_level'],
        }
        for item in catalog
    ]


def _terra_placeholder_training_plans(current_user: dict) -> List[Dict[str, Any]]:
    return [
        {
            'id': f'starter-{current_user["id"]}-5k',
            'goal': '5K',
            'fitness_level': 'beginner',
            'total_weeks': 6,
            'current_week': 1,
            'completed_sessions': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_seeded': True,
        },
        {
            'id': f'starter-{current_user["id"]}-tempo',
            'goal': '10K',
            'fitness_level': 'intermediate',
            'total_weeks': 8,
            'current_week': 2,
            'completed_sessions': ['week1-session1'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_seeded': True,
        },
    ]


async def _terra_ensure_seed_feed_posts() -> None:
    existing = await db.terra_feed_posts.find({}).to_list(10)
    if len(existing) >= 3:
        return

    now = datetime.utcnow()
    seed_posts = [
        {
            'id': 'terra-seed-1',
            'user_id': 'system-1',
            'username': 'Trail Nova',
            'content': 'Logged a clean loop at sunrise. The frontier feels wide open today.',
            'likes': ['system-2'],
            'comments': [{'id': 'seed-comment-1', 'username': 'Runner Atlas', 'content': 'Strong start.'}],
            'run': {'distance': 6.2, 'duration': 1860, 'territory_captured': 0.032},
            'created_at': now - timedelta(hours=5),
            'updated_at': now - timedelta(hours=5),
            'is_seeded': True,
        },
        {
            'id': 'terra-seed-2',
            'user_id': 'system-2',
            'username': 'Runner Atlas',
            'content': 'Kept the streak alive with a recovery jog and a full cooldown.',
            'likes': ['system-1', 'system-3'],
            'comments': [],
            'run': {'distance': 4.1, 'duration': 1440, 'territory_captured': 0.019},
            'created_at': now - timedelta(hours=9),
            'updated_at': now - timedelta(hours=9),
            'is_seeded': True,
        },
        {
            'id': 'terra-seed-3',
            'user_id': 'system-3',
            'username': 'Mira Ridge',
            'content': 'Race week starts with discipline: one hard session, one recovery day, no noise.',
            'likes': [],
            'comments': [{'id': 'seed-comment-2', 'username': 'Trail Nova', 'content': 'Good mindset.'}],
            'created_at': now - timedelta(days=1, hours=2),
            'updated_at': now - timedelta(days=1, hours=2),
            'is_seeded': True,
        },
    ]

    existing_ids = {str(post.get('id')) for post in existing}
    for post in seed_posts:
        if post['id'] in existing_ids:
            continue
        await db.terra_feed_posts.insert_one(post)


def _terra_feed_post_response(post: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = clean_doc(dict(post))
    cleaned['username'] = cleaned.get('username') or cleaned.get('author_name') or 'Runner'
    cleaned['content'] = str(cleaned.get('content') or '').strip()
    cleaned['likes'] = [str(user_id) for user_id in cleaned.get('likes', []) if str(user_id).strip()]
    cleaned['comments'] = cleaned.get('comments') or []
    run = cleaned.get('run')
    if isinstance(run, dict):
        cleaned['run'] = {
            'distance': _terra_run_distance_km(run),
            'duration': _terra_run_duration_seconds(run),
            'territory_captured': _terra_run_territory_km2(run),
        }
    else:
        cleaned['run'] = None
    return cleaned


def _terra_training_plan_response(plan: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = clean_doc(dict(plan))
    cleaned['goal'] = cleaned.get('goal') or cleaned.get('title') or 'Goal'
    cleaned['fitness_level'] = cleaned.get('fitness_level') or 'intermediate'
    cleaned['total_weeks'] = _to_non_negative_int(cleaned.get('total_weeks'), 8) or 8
    cleaned['current_week'] = max(1, _to_non_negative_int(cleaned.get('current_week'), 1))
    cleaned['completed_sessions'] = [str(session) for session in cleaned.get('completed_sessions', []) if str(session).strip()]
    return cleaned


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail='Invalid token')
        user = await db.users.find_one({'id': user_id})
        if not user:
            raise HTTPException(status_code=401, detail='User not found')
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')


def user_response(user: dict) -> dict:
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user['name'],
        'mode': user.get('mode', 'user'),
        'profile': user.get('profile', {}),
        'created_at': user.get('created_at')
    }


def _list_value(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _profile_from_payload(payload: Optional[Dict[str, Any]], current_user: Optional[dict] = None) -> UserProfile:
    existing = {}
    if current_user:
        existing = dict(current_user.get('profile') or {})
    incoming = dict(payload or {})
    if 'profile' in incoming and isinstance(incoming['profile'], dict):
        incoming = dict(incoming['profile'])

    normalized = {**existing, **incoming}
    if incoming.get('fitness_level') and not incoming.get('experience'):
        normalized['experience'] = incoming.get('fitness_level')
    if incoming.get('location') and not any(incoming.get(k) for k in ['country', 'city', 'training_location']):
        normalized['country'] = incoming.get('location')
    if incoming.get('sport') and not incoming.get('sports'):
        normalized['sports'] = [incoming.get('sport')]
    if incoming.get('selectedGoals') and not incoming.get('selected_goals'):
        normalized['selected_goals'] = incoming.get('selectedGoals')
    if incoming.get('fitnessAssessment') and not incoming.get('fitness_assessment'):
        normalized['fitness_assessment'] = incoming.get('fitnessAssessment')

    for key in [
        'goals',
        'selected_goals',
        'sports',
        'equipment',
        'facilities',
        'preferred_training_days',
        'pain_areas',
        'dietary_restrictions',
        'allergies',
    ]:
        normalized[key] = _list_value(normalized.get(key))

    if not normalized.get('primary_goal'):
        goals = normalized.get('selected_goals') or normalized.get('goals') or []
        normalized['primary_goal'] = goals[0] if goals else None
    if normalized.get('onboarding_completed_at') is None and incoming:
        normalized['onboarding_completed_at'] = datetime.utcnow()

    return UserProfile(**normalized)


def _profile_dict(profile: UserProfile) -> Dict[str, Any]:
    return profile.model_dump()


async def _upsert_athlete_profile(current_user: dict, profile: UserProfile) -> Dict[str, Any]:
    now = datetime.utcnow()
    profile_doc = _profile_dict(profile)
    goals = list(dict.fromkeys([*profile.selected_goals, *profile.goals]))
    sports = list(dict.fromkeys(profile.sports))
    doc = {
        'user_id': current_user['id'],
        'email': current_user.get('email'),
        'name': current_user.get('name'),
        'raw_profile': profile_doc,
        'goals': goals,
        'primary_goal': profile.primary_goal or (goals[0] if goals else None),
        'sports': sports,
        'experience': profile.experience,
        'training_days_per_week': profile.training_days_per_week,
        'session_duration_min': profile.session_duration_min,
        'equipment': profile.equipment,
        'injury_flags': {
            'current_injuries': profile.current_injuries,
            'pain_areas': profile.pain_areas,
            'medical_notes': profile.medical_notes,
        },
        'recovery_baseline': {
            'sleep_avg_hours': profile.sleep_avg_hours,
            'stress_level': profile.stress_level,
            'recovery_score_baseline': profile.recovery_score_baseline,
        },
        'updated_at': now,
    }
    await db.athlete_profiles.update_one(
        {'user_id': current_user['id']},
        {
            '$set': doc,
            '$setOnInsert': {
                'id': str(uuid.uuid4()),
                'created_at': now,
            },
        },
        upsert=True,
    )
    await db.users.update_one(
        {'id': current_user['id']},
        {'$set': {'profile': profile_doc, 'updated_at': now}},
    )
    saved = await db.athlete_profiles.find_one({'user_id': current_user['id']})
    return clean_doc(saved)


def _profile_focus(profile: Dict[str, Any]) -> Dict[str, Any]:
    sports = [str(item).strip().lower() for item in (profile.get('sports') or []) if str(item).strip()]
    raw_goals = [*(profile.get('selected_goals') or []), *(profile.get('goals') or [])]
    goals = [str(item).strip().lower() for item in raw_goals if str(item).strip()]
    primary_goal = str(profile.get('primary_goal') or (goals[0] if goals else 'athletic performance')).lower()
    is_runner = any(sport in ['running', 'runner', 'marathon', '5k', '10k'] for sport in sports + goals)
    field_sport = any(sport in ['cricket', 'football', 'soccer', 'basketball', 'volleyball', 'tennis', 'badminton'] for sport in sports)
    muscle_gain = any('muscle' in goal or 'strength' in goal for goal in goals) or 'muscle' in primary_goal
    fat_loss = any('weight' in goal or 'fat' in goal or 'loss' in goal for goal in goals) or 'loss' in primary_goal
    return {
        'sports': sports,
        'goals': goals,
        'primary_goal': primary_goal,
        'is_runner': is_runner,
        'field_sport': field_sport,
        'muscle_gain': muscle_gain,
        'fat_loss': fat_loss,
    }


def _program_title(profile: Dict[str, Any]) -> str:
    focus = _profile_focus(profile)
    sports = [sport.title() for sport in (profile.get('sports') or []) if str(sport).strip()]
    if len(sports) >= 2:
        return f"{' + '.join(sports[:2])} Hybrid S&C"
    if sports:
        return f"{sports[0]} S&C Program"
    if focus['muscle_gain']:
        return 'Muscle Gain Strength Program'
    if focus['fat_loss']:
        return 'Fat Loss Conditioning Program'
    return 'Athletic Foundation Program'


def _session_count(profile: Dict[str, Any]) -> int:
    requested = profile.get('training_days_per_week')
    try:
        requested_count = int(requested) if requested is not None else 4
    except (TypeError, ValueError):
        requested_count = 4
    return min(6, max(3, requested_count))


def _session_duration(profile: Dict[str, Any]) -> int:
    duration = profile.get('session_duration_min')
    try:
        return min(90, max(30, int(duration))) if duration is not None else 45
    except (TypeError, ValueError):
        return 45


def _exercise_plan(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    focus = _profile_focus(profile)
    equipment = [str(item).lower() for item in (profile.get('equipment') or [])]
    has_gym = any(item in equipment for item in ['gym', 'barbell', 'dumbbells', 'machine', 'kettlebell'])
    lower_main = 'Back Squat' if has_gym else 'Goblet Squat'
    hinge = 'Romanian Deadlift' if has_gym else 'Single-leg Hip Hinge'
    press = 'Dumbbell Bench Press' if has_gym else 'Push-up'
    pull = 'Seated Cable Row' if has_gym else 'Band Row'

    plan = [
        {
            'category': 'Strength',
            'title': 'Lower Strength + Core',
            'exercises': [
                WorkoutExercise(name=lower_main, sets=4, reps='6-8', rest='90 sec', notes='Controlled reps, leave 2 reps in reserve'),
                WorkoutExercise(name=hinge, sets=3, reps='8-10', rest='75 sec'),
                WorkoutExercise(name='Split Squat', sets=3, reps='8 each side', rest='60 sec'),
                WorkoutExercise(name='Dead Bug', sets=3, reps='10 each side', rest='45 sec'),
            ],
        },
        {
            'category': 'Conditioning' if focus['fat_loss'] or focus['is_runner'] else 'Power',
            'title': 'Speed, Agility + Conditioning',
            'exercises': [
                WorkoutExercise(name='Dynamic Warm-up', duration='8 min'),
                WorkoutExercise(name='Acceleration Runs', sets=6, reps='20 m', rest='60 sec'),
                WorkoutExercise(name='Lateral Shuffle to Sprint', sets=4, reps='each side', rest='60 sec'),
                WorkoutExercise(name='Zone 2 Run' if focus['is_runner'] else 'Tempo Intervals', duration='20 min', notes='Finish with easy breathing, not exhaustion'),
            ],
        },
        {
            'category': 'Strength',
            'title': 'Upper Strength + Shoulder Care',
            'exercises': [
                WorkoutExercise(name=press, sets=4, reps='8-10', rest='75 sec'),
                WorkoutExercise(name=pull, sets=4, reps='10-12', rest='75 sec'),
                WorkoutExercise(name='Half-kneeling Press', sets=3, reps='8 each side', rest='60 sec'),
                WorkoutExercise(name='Face Pull', sets=3, reps='15', rest='45 sec'),
            ],
        },
        {
            'category': 'Mobility',
            'title': 'Recovery + Mobility',
            'exercises': [
                WorkoutExercise(name='Breathing Reset', duration='5 min'),
                WorkoutExercise(name='Hip Mobility Flow', duration='8 min'),
                WorkoutExercise(name='Thoracic Rotation', sets=2, reps='10 each side'),
                WorkoutExercise(name='Easy Walk or Cycle', duration='20 min'),
            ],
        },
    ]

    if focus['field_sport']:
        plan.append({
            'category': 'Power',
            'title': 'Jump, Rotation + Change of Direction',
            'exercises': [
                WorkoutExercise(name='Pogo Jumps', sets=3, reps='20 sec', rest='45 sec'),
                WorkoutExercise(name='Broad Jump', sets=4, reps='3', rest='75 sec'),
                WorkoutExercise(name='Medicine Ball Rotational Throw' if has_gym else 'Rotational Shadow Throw', sets=4, reps='5 each side', rest='60 sec'),
                WorkoutExercise(name='5-10-5 Shuttle', sets=5, reps='1 rep', rest='90 sec'),
            ],
        })
    if focus['muscle_gain']:
        plan.append({
            'category': 'Hypertrophy',
            'title': 'Full Body Muscle Builder',
            'exercises': [
                WorkoutExercise(name=lower_main, sets=3, reps='10-12', rest='75 sec'),
                WorkoutExercise(name=press, sets=3, reps='10-12', rest='75 sec'),
                WorkoutExercise(name=pull, sets=3, reps='12', rest='60 sec'),
                WorkoutExercise(name='Farmer Carry' if has_gym else 'Loaded Carry', sets=4, reps='30 m', rest='60 sec'),
            ],
        })

    return plan


async def _create_training_program(current_user: dict, profile: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow()
    user_id = current_user['id']
    duration = _session_duration(profile)
    session_count = _session_count(profile)
    title = _program_title(profile)
    focus = _profile_focus(profile)

    program = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'title': title,
        'status': 'active',
        'source': 'rules_engine_v1',
        'goal': focus['primary_goal'],
        'sports': profile.get('sports', []),
        'duration_weeks': 4,
        'current_week': 1,
        'created_at': now,
        'updated_at': now,
        'profile_snapshot': profile,
    }
    block = {
        'id': str(uuid.uuid4()),
        'program_id': program['id'],
        'user_id': user_id,
        'name': 'Foundation Block',
        'week_start': 1,
        'week_end': 4,
        'emphasis': ['movement quality', 'strength base', 'sport transfer', 'recovery'],
        'created_at': now,
    }

    await db.training_programs.update_many({'user_id': user_id, 'status': 'active'}, {'$set': {'status': 'archived', 'archived_at': now}})
    await db.training_programs.insert_one(program)
    await db.program_blocks.insert_one(block)
    await db.workouts.delete_many({'user_id': user_id, 'completed': {'$ne': True}, 'scheduled_date': {'$gte': now.strftime('%Y-%m-%d')}})

    days = profile.get('preferred_training_days') or ['Monday', 'Tuesday', 'Wednesday', 'Friday', 'Saturday', 'Sunday']
    sports = profile.get('sports') or []
    templates = _exercise_plan(profile)
    workouts = []
    for i in range(session_count):
        template = templates[i % len(templates)]
        scheduled = now + timedelta(days=i)
        day_label = days[i % len(days)] if days else scheduled.strftime('%A')
        workout = Workout(
            user_id=user_id,
            title=f"{day_label}: {template['title']}",
            category=template['category'],
            duration=duration if template['category'] != 'Mobility' else min(duration, 40),
            difficulty=str(profile.get('experience') or 'Intermediate').title(),
            equipment=profile.get('equipment') or [],
            exercises=template['exercises'],
            description=f"{title} session for {', '.join(sports[:2]) or focus['primary_goal']}.",
            ai_generated=True,
            scheduled_date=scheduled.strftime('%Y-%m-%d'),
        ).model_dump()
        workout.update({
            'program_id': program['id'],
            'block_id': block['id'],
            'week_number': 1,
            'session_number': i + 1,
            'source': 'rules_engine_v1',
            'adaptation': {
                'goal': focus['primary_goal'],
                'sports': sports,
                'injury_flags': {
                    'pain_areas': profile.get('pain_areas') or [],
                    'current_injuries': profile.get('current_injuries') or [],
                },
            },
        })
        await db.workouts.insert_one(workout)
        workouts.append(clean_doc(workout))

    return {
        'program': clean_doc(program),
        'block': clean_doc(block),
        'weekly_plan': workouts,
    }


def _date_window(date_str: Optional[str] = None) -> tuple[str, datetime, datetime]:
    if date_str:
        try:
            day = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail='date must be YYYY-MM-DD')
    else:
        day = datetime.utcnow()
    normalized = day.strftime('%Y-%m-%d')
    start = datetime(day.year, day.month, day.day)
    end = start + timedelta(days=1)
    return normalized, start, end


def _sum_float(docs: List[Dict[str, Any]], *keys: str) -> float:
    total = 0.0
    for doc in docs:
        for key in keys:
            value = doc.get(key)
            if value is not None:
                total += _to_non_negative_float(value, 0)
                break
    return round(total, 3)


def _sum_int(docs: List[Dict[str, Any]], *keys: str) -> int:
    return int(round(_sum_float(docs, *keys)))


def _first_present(doc: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = doc.get(key)
        if value is not None:
            return value
    return None


def _sleep_session_date_filter(date_str: str, start: datetime, end: datetime) -> Dict[str, Any]:
    return {
        '$or': [
            {'date': date_str},
            {'start_time': {'$regex': f'^{date_str}'}},
            {'end_time': {'$regex': f'^{date_str}'}},
            {'created_at': {'$gte': start, '$lt': end}},
        ]
    }


def _snapshot_data_quality(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    sections = {
        'profile': bool(snapshot.get('profile')),
        'workouts': bool(snapshot.get('scheduled_workouts') or snapshot.get('workout_sessions')),
        'runs': bool(snapshot.get('runs')),
        'meals': bool(snapshot.get('meals')),
        'sleep': bool(snapshot.get('sleep_sessions')),
        'quick_logs': bool(snapshot.get('quick_logs')),
        'injuries': bool(snapshot.get('injuries')),
    }
    missing = [key for key, present in sections.items() if not present]
    return {
        'sections': sections,
        'missing_sections': missing,
        'score': round(((len(sections) - len(missing)) / len(sections)) * 100),
    }


async def _build_daily_snapshot(current_user: dict, date: Optional[str] = None) -> Dict[str, Any]:
    date_str, start, end = _date_window(date)
    user_id = current_user['id']

    athlete_profile = await db.athlete_profiles.find_one({'user_id': user_id})
    active_program = await db.training_programs.find_one({'user_id': user_id, 'status': 'active'}, sort=[('created_at', -1)])
    scheduled_workouts = await db.workouts.find({
        'user_id': user_id,
        '$or': [
            {'scheduled_date': date_str},
            {'completed_at': {'$gte': start, '$lt': end}},
        ],
    }).sort('session_number', 1).to_list(50)
    workout_sessions = await db.workout_sessions.find({'user_id': user_id, 'date': date_str}).sort('created_at', -1).to_list(50)
    exercise_results = await db.exercise_results.find({'user_id': user_id, 'date': date_str}).sort('created_at', -1).to_list(200)
    all_run_docs = await _terra_user_run_docs(user_id)
    runs = [doc for doc in all_run_docs if str(doc.get('date') or '').startswith(date_str)]
    meals = await db.meals.find({'user_id': user_id, 'date': date_str}).sort('created_at', 1).to_list(50)
    sleep_sessions = await db.sleep_sessions.find({'user_id': user_id, **_sleep_session_date_filter(date_str, start, end)}).sort('created_at', -1).to_list(20)
    quick_logs = await db.quick_logs.find({'user_id': user_id, 'date': date_str}).sort('created_at', -1).to_list(20)
    moods = await db.moods.find({'user_id': user_id, 'date': date_str}).sort('timestamp', -1).to_list(50)
    health_metrics = await db.health_metrics.find({'user_id': user_id, 'date': date_str}).sort('created_at', -1).to_list(50)
    injuries = await db.injury_logs.find({
        'user_id': user_id,
        '$or': [
            {'is_active': True},
            {'logged_at': {'$gte': start, '$lt': end}},
        ],
    }).sort('logged_at', -1).to_list(50)
    coach_assignments = await db.coach_workouts.find({'client_id': user_id, 'scheduled_date': date_str}).sort('created_at', -1).to_list(50)

    sleep_metrics = [_sleep_session_metrics(session) for session in sleep_sessions]
    avg_sleep_hours = None
    avg_sleep_score = None
    if sleep_metrics:
        avg_sleep_hours = round(sum(item['duration_hours'] for item in sleep_metrics) / len(sleep_metrics), 2)
        avg_sleep_score = round(sum(item['sleep_score'] for item in sleep_metrics) / len(sleep_metrics), 1)

    totals = DailySnapshotTotals(
        scheduled_workouts=len(scheduled_workouts),
        completed_workouts=len([workout for workout in scheduled_workouts if workout.get('completed')]),
        workout_sessions=len(workout_sessions),
        exercise_results=len(exercise_results),
        run_count=len(runs),
        run_distance_km=_sum_float(runs, 'distance_km', 'distance'),
        run_duration_sec=_sum_int(runs, 'duration_sec', 'duration'),
        territory_km2=_sum_float(runs, 'territory_km2', 'territory_captured'),
        meals_logged=len(meals),
        calories=_sum_int(meals, 'calories'),
        protein=_sum_float(meals, 'protein'),
        carbs=_sum_float(meals, 'carbs'),
        fat=_sum_float(meals, 'fat'),
        fiber=_sum_float(meals, 'fiber'),
        sleep_hours=avg_sleep_hours,
        sleep_score=avg_sleep_score,
    )

    latest_quick_log = quick_logs[0] if quick_logs else {}
    snapshot_doc = DailyActivitySnapshot(
        user_id=user_id,
        date=date_str,
        profile=clean_doc(athlete_profile).get('raw_profile', current_user.get('profile') or {}) if athlete_profile else current_user.get('profile') or {},
        active_program=clean_doc(active_program) if active_program else None,
        scheduled_workouts=[clean_doc(doc) for doc in scheduled_workouts],
        workout_sessions=[clean_doc(doc) for doc in workout_sessions],
        exercise_results=[clean_doc(doc) for doc in exercise_results],
        runs=[_terra_run_response(doc) for doc in runs],
        meals=[clean_doc(doc) for doc in meals],
        sleep_sessions=[_sleep_session_response(doc) for doc in sleep_sessions],
        quick_logs=[clean_doc(doc) for doc in quick_logs],
        moods=[clean_doc(doc) for doc in moods],
        injuries=[clean_doc(doc) for doc in injuries],
        health_metrics=[clean_doc(doc) for doc in health_metrics],
        coach_assignments=[clean_doc(doc) for doc in coach_assignments],
        totals=totals,
        readiness_inputs={
            'energy': latest_quick_log.get('energy'),
            'stress': latest_quick_log.get('stress'),
            'mood': latest_quick_log.get('mood'),
            'sleep_quality': latest_quick_log.get('sleep_quality'),
            'soreness_regions': latest_quick_log.get('soreness_regions') or [],
            'active_pain_areas': [doc.get('body_area') for doc in injuries if doc.get('is_active')],
        },
    ).model_dump()
    snapshot_doc['data_quality'] = _snapshot_data_quality(snapshot_doc)
    return clean_doc(snapshot_doc)


async def _save_daily_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow()
    snapshot = dict(snapshot)
    snapshot['updated_at'] = now
    await db.daily_snapshots.update_one(
        {'user_id': snapshot['user_id'], 'date': snapshot['date']},
        {
            '$set': snapshot,
            '$setOnInsert': {'created_at': now},
        },
        upsert=True,
    )
    saved = await db.daily_snapshots.find_one({'user_id': snapshot['user_id'], 'date': snapshot['date']})
    return clean_doc(saved)


def _schema_response() -> Dict[str, Any]:
    return {
        'program_generation_output': ProgramGenerationOutput.model_json_schema(),
        'daily_activity_snapshot': DailyActivitySnapshot.model_json_schema(),
        'daily_coach_analysis': DailyCoachAnalysis.model_json_schema(),
    }


def _compact_snapshot_for_ai(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    profile = snapshot.get('profile') or {}
    active_program = snapshot.get('active_program') or {}
    totals = snapshot.get('totals') or {}
    return {
        'date': snapshot.get('date'),
        'profile': {
            'goals': profile.get('selected_goals') or profile.get('goals') or [],
            'primary_goal': profile.get('primary_goal'),
            'sports': profile.get('sports') or [],
            'experience': profile.get('experience'),
            'equipment': profile.get('equipment') or [],
            'training_days_per_week': profile.get('training_days_per_week'),
            'session_duration_min': profile.get('session_duration_min'),
            'pain_areas': profile.get('pain_areas') or [],
            'medical_notes': profile.get('medical_notes'),
            'nutrition_goal': profile.get('nutrition_goal'),
        },
        'active_program': {
            'title': active_program.get('title'),
            'goal': active_program.get('goal'),
            'sports': active_program.get('sports') or [],
            'current_week': active_program.get('current_week'),
        },
        'totals': totals,
        'readiness_inputs': snapshot.get('readiness_inputs') or {},
        'scheduled_workouts': [
            {
                'title': workout.get('title'),
                'category': workout.get('category'),
                'duration': workout.get('duration'),
                'completed': workout.get('completed'),
                'feedback': workout.get('user_feedback'),
            }
            for workout in (snapshot.get('scheduled_workouts') or [])[:4]
        ],
        'runs': [
            {
                'distance_km': _first_present(run, 'distance_km', 'distance'),
                'duration_sec': _first_present(run, 'duration_sec', 'duration'),
                'pace': run.get('pace'),
                'territory_km2': _first_present(run, 'territory_km2', 'territory_captured'),
            }
            for run in (snapshot.get('runs') or [])[:5]
        ],
        'meals': [
            {
                'meal_type': meal.get('meal_type'),
                'name': meal.get('name'),
                'calories': meal.get('calories'),
                'protein': meal.get('protein'),
                'carbs': meal.get('carbs'),
                'fat': meal.get('fat'),
            }
            for meal in (snapshot.get('meals') or [])[:6]
        ],
        'sleep': [
            {
                'duration_hours': session.get('duration_hours'),
                'sleep_score': session.get('sleep_score'),
                'quality': session.get('sleep_quality_label'),
            }
            for session in (snapshot.get('sleep_sessions') or [])[:3]
        ],
        'quick_logs': [
            {
                'mood': log.get('mood'),
                'energy': log.get('energy'),
                'stress': log.get('stress'),
                'sleep_quality': log.get('sleep_quality'),
                'soreness_regions': log.get('soreness_regions') or [],
                'note': log.get('note'),
            }
            for log in (snapshot.get('quick_logs') or [])[:3]
        ],
        'injuries': [
            {
                'body_area': injury.get('body_area'),
                'severity': injury.get('severity'),
                'pain_scale': injury.get('pain_scale'),
                'restrictions': injury.get('restrictions') or [],
                'notes': injury.get('notes'),
            }
            for injury in (snapshot.get('injuries') or [])[:5]
        ],
        'data_quality': snapshot.get('data_quality') or {},
    }


def _daily_coach_fallback(snapshot: Dict[str, Any]) -> DailyCoachAnalysis:
    totals = snapshot.get('totals') or {}
    readiness_inputs = snapshot.get('readiness_inputs') or {}
    injuries = snapshot.get('injuries') or []
    meals = snapshot.get('meals') or []
    scheduled = snapshot.get('scheduled_workouts') or []

    score = 75
    risk_flags: List[str] = []
    workout_modifications: List[str] = []
    trend_notes: List[str] = []
    questions: List[str] = []

    sleep_hours = totals.get('sleep_hours')
    sleep_score = totals.get('sleep_score')
    if sleep_hours is not None:
        if sleep_hours < 6:
            score -= 15
            risk_flags.append('Low sleep duration')
            workout_modifications.append('Reduce working sets by 20% and avoid max-effort conditioning.')
        elif sleep_hours >= 8:
            score += 5
            trend_notes.append('Sleep duration supports a normal training day.')
    elif readiness_inputs.get('sleep_quality') is not None:
        sleep_quality_score = _to_non_negative_float(readiness_inputs.get('sleep_quality'), 0) * 20
        if sleep_quality_score < 60:
            score -= 10
            risk_flags.append('Low reported sleep quality')
    else:
        questions.append('How many hours did you sleep last night?')

    if sleep_score is not None and sleep_score < 60:
        score -= 8
        risk_flags.append('Sleep score is below target')

    stress = str(readiness_inputs.get('stress') or '').lower()
    if stress == 'high':
        score -= 10
        risk_flags.append('High stress')
        workout_modifications.append('Keep intensity moderate and extend warm-up breathing.')

    energy = str(readiness_inputs.get('energy') or '').lower()
    if energy in ['low', 'tired', 'poor']:
        score -= 10
        risk_flags.append('Low energy')
    elif energy in ['high', 'great']:
        score += 5

    soreness = readiness_inputs.get('soreness_regions') or []
    active_pain = [area for area in readiness_inputs.get('active_pain_areas') or [] if area]
    if soreness:
        score -= min(10, len(soreness) * 3)
        workout_modifications.append(f"Avoid loading sore regions aggressively: {', '.join(soreness[:3])}.")
    if injuries or active_pain:
        score -= 15
        risk_flags.append('Active pain or injury logged')
        workout_modifications.append('Use pain-free substitutions and stop any movement above 3/10 pain.')

    completed = _to_non_negative_int(totals.get('completed_workouts'), 0)
    scheduled_count = _to_non_negative_int(totals.get('scheduled_workouts'), 0)
    run_distance = _to_non_negative_float(totals.get('run_distance_km'), 0)
    protein = _to_non_negative_float(totals.get('protein'), 0)

    if scheduled_count and completed >= scheduled_count:
        trend_notes.append('All scheduled workouts for the day are complete.')
    if run_distance >= 5:
        trend_notes.append(f"Running volume today is {run_distance:g} km.")
        if scheduled_count and not completed:
            workout_modifications.append('If strength is still pending, keep it technique-focused after the run.')
    if not meals:
        questions.append('What have you eaten today?')
    elif protein < 80:
        trend_notes.append('Protein is still low for most strength and recovery goals.')

    score = max(25, min(95, score))
    if score >= 80:
        label = 'ready'
        training = 'Proceed with today’s planned session. Keep the main lifts crisp and log feedback after training.'
    elif score >= 60:
        label = 'moderate'
        training = 'Train today, but keep intensity controlled and use the listed modifications.'
    else:
        label = 'recovery'
        training = 'Prioritize recovery or a light technical session today instead of hard loading.'

    nutrition = 'Log meals and aim for a protein serving at each meal.'
    if meals:
        nutrition = 'Keep hydration steady and add protein/carbs around training based on today’s workload.'
    if protein and protein < 80:
        nutrition = 'Add a high-protein meal or snack to support recovery.'

    recovery = 'Protect sleep tonight and add 5-10 minutes of mobility or breathing.'
    if risk_flags:
        recovery = 'Treat recovery as part of training today: sleep, hydration, and pain-free movement only.'

    return DailyCoachAnalysis(
        date=str(snapshot.get('date')),
        readiness_score=score,
        readiness_label=label,
        training_recommendation=training,
        workout_modifications=workout_modifications,
        nutrition_recommendation=nutrition,
        recovery_recommendation=recovery,
        risk_flags=risk_flags,
        trend_notes=trend_notes,
        questions_for_user=questions,
        should_regenerate_plan=score < 45 or len([flag for flag in risk_flags if 'injury' in flag.lower()]) > 0,
    )


async def _ai_daily_coach_analysis(snapshot: Dict[str, Any]) -> Optional[DailyCoachAnalysis]:
    if not openai_client:
        return None

    compact = _compact_snapshot_for_ai(snapshot)
    schema = DailyCoachAnalysis.model_json_schema()
    prompt = (
        "You are an evidence-based strength and conditioning coach for a fitness app. "
        "Analyze the athlete's daily snapshot and return ONLY valid JSON matching the provided schema. "
        "Be practical, concise, and conservative with injury or pain. "
        "Do not invent data that is missing. Use questions_for_user for missing important inputs."
    )
    user_text = json.dumps(
        {
            'schema': schema,
            'snapshot': compact,
        },
        default=str,
    )

    def _call_openai() -> str:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': user_text},
            ],
            temperature=0.2,
        )
        return (response.choices[0].message.content or '{}').strip()

    try:
        raw = await asyncio.to_thread(_call_openai)
        if raw.startswith('```json'):
            raw = raw[7:]
        if raw.startswith('```'):
            raw = raw[3:]
        if raw.endswith('```'):
            raw = raw[:-3]
        parsed = json.loads(raw.strip())
        parsed['date'] = str(parsed.get('date') or snapshot.get('date'))
        return DailyCoachAnalysis(**parsed)
    except Exception as exc:
        logger.warning(f'Daily coach AI failed, falling back to rules analysis: {exc}')
        return None


async def _save_daily_analysis(
    current_user: dict,
    snapshot: Dict[str, Any],
    analysis: DailyCoachAnalysis,
    source: str,
) -> Dict[str, Any]:
    now = datetime.utcnow()
    doc = analysis.model_dump()
    doc.update({
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'snapshot_id': snapshot.get('id'),
        'source': source,
        'model': LLM_MODEL if source == 'ai' else None,
        'created_at': now,
        'updated_at': now,
    })
    await db.coach_daily_analyses.update_one(
        {'user_id': current_user['id'], 'date': analysis.date},
        {
            '$set': doc,
            '$setOnInsert': {'first_created_at': now},
        },
        upsert=True,
    )
    saved = await db.coach_daily_analyses.find_one({'user_id': current_user['id'], 'date': analysis.date})
    return clean_doc(saved)


async def _generate_daily_analysis(current_user: dict, date: Optional[str] = None) -> Dict[str, Any]:
    snapshot = await _save_daily_snapshot(await _build_daily_snapshot(current_user, date))
    analysis = await _ai_daily_coach_analysis(snapshot)
    source = 'ai'
    if analysis is None:
        analysis = _daily_coach_fallback(snapshot)
        source = 'rules_engine_v1'
    return await _save_daily_analysis(current_user, snapshot, analysis, source)


def _user_mode(user: dict) -> str:
    return str(user.get('mode') or 'user').strip().lower()


def _require_coach_user(current_user: dict) -> None:
    if _user_mode(current_user) != 'coach':
        raise HTTPException(status_code=403, detail='Coach access required')


def _require_client_user(current_user: dict) -> None:
    if _user_mode(current_user) == 'coach':
        raise HTTPException(status_code=403, detail='Client access required')


async def _coach_client_request(coach_id: str, client_id: str) -> Optional[dict]:
    return await db.coach_requests.find_one({'coach_id': coach_id, 'client_id': client_id}, sort=[('created_at', -1)])


async def _coach_client_is_accepted(coach_id: str, client_id: str) -> bool:
    request = await _coach_client_request(coach_id, client_id)
    return bool(request and request.get('status') == 'accepted')


async def create_and_store_otp(email: str) -> str:
    code = f"{uuid.uuid4().int % 1000000:06d}"
    await db.otps.insert_one({
        'email': email,
        'code': code,
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(minutes=10),
    })
    logger.info(f"OTP for {email}: {code}")
    return code


async def verify_latest_otp(email: str, code: str) -> bool:
    otp = await db.otps.find_one({'email': email}, sort=[('created_at', -1)])
    if not otp:
        return False
    if otp.get('expires_at') and otp['expires_at'] < datetime.utcnow():
        return False
    return otp.get('code') == code


async def _sleep_user_summary(user_id: str) -> Dict[str, Any]:
    sessions = await db.sleep_sessions.find({'user_id': user_id}).sort('created_at', -1).to_list(200)
    quick_logs = await db.quick_logs.find({'user_id': user_id}).sort('date', -1).to_list(14)

    if sessions:
        session_metrics = [_sleep_session_metrics(session) for session in sessions]
        avg_score = round(sum(item['sleep_score'] for item in session_metrics) / len(session_metrics), 1)
        avg_duration = round(sum(item['duration_hours'] for item in session_metrics) / len(session_metrics), 1)
        avg_deep_sleep = round(sum(item['deep_sleep_hours'] for item in session_metrics) / len(session_metrics), 1)
        avg_rem_sleep = round(sum(item['rem_sleep_hours'] for item in session_metrics) / len(session_metrics), 1)
        sleep_debt_hours = round(sum(item['sleep_debt_hours'] for item in session_metrics), 1)
        latest_session = _sleep_session_response(sessions[0])

        recent_scores = [item['sleep_score'] for item in session_metrics[:3]]
        previous_scores = [item['sleep_score'] for item in session_metrics[3:6]]
        if len(recent_scores) >= 2 and len(previous_scores) >= 2:
            recent_avg = sum(recent_scores) / len(recent_scores)
            previous_avg = sum(previous_scores) / len(previous_scores)
            if recent_avg - previous_avg > 3:
                trend = 'up'
            elif previous_avg - recent_avg > 3:
                trend = 'down'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        return {
            'avg_score': avg_score,
            'avg_duration': avg_duration,
            'avg_deep_sleep': avg_deep_sleep,
            'avg_rem_sleep': avg_rem_sleep,
            'total_sessions': len(session_metrics),
            'sleep_debt': {'total_debt_hours': sleep_debt_hours},
            'latest_session': latest_session,
            'latest_score': session_metrics[0]['sleep_score'],
            'latest_duration': session_metrics[0]['duration_hours'],
            'latest_quality_label': session_metrics[0]['sleep_quality_label'],
            'trend': trend,
            'last_updated': latest_session.get('created_at') or latest_session.get('updated_at') or latest_session.get('date'),
        }

    if quick_logs:
        avg_score = round(sum(float(log.get('sleep_quality', 0)) * 20.0 for log in quick_logs) / len(quick_logs), 1)
        latest_log = clean_doc(dict(quick_logs[0]))
        latest_score = float(latest_log.get('sleep_quality', 0)) * 20.0
        return {
            'avg_score': avg_score,
            'avg_duration': 0.0,
            'avg_deep_sleep': 0.0,
            'avg_rem_sleep': 0.0,
            'total_sessions': 0,
            'sleep_debt': {'total_debt_hours': 0.0},
            'latest_session': None,
            'latest_score': latest_score,
            'latest_duration': 0.0,
            'latest_quality_label': _sleep_quality_label(latest_score),
            'trend': 'stable',
            'last_updated': latest_log.get('created_at') or latest_log.get('date'),
        }

    return {
        'avg_score': 0.0,
        'avg_duration': 0.0,
        'avg_deep_sleep': 0.0,
        'avg_rem_sleep': 0.0,
        'total_sessions': 0,
        'sleep_debt': {'total_debt_hours': 0.0},
        'latest_session': None,
        'latest_score': None,
        'latest_duration': None,
        'latest_quality_label': 'unknown',
        'trend': 'stable',
        'last_updated': None,
    }


def _manual_meal_result(payload: "MealCreate") -> Dict[str, Any]:
    return {
        'name': payload.name or 'Meal',
        'foods_identified': [payload.name] if payload.name else ['Meal'],
        'calories': _to_non_negative_int(payload.calories, 0),
        'protein': _to_non_negative_float(payload.protein, 0),
        'carbs': _to_non_negative_float(payload.carbs, 0),
        'fat': _to_non_negative_float(payload.fat, 0),
        'fiber': _to_non_negative_float(payload.fiber, 0),
        'status': 'Logged',
        'portion_size': '1 serving',
        'confidence': 'manual',
        'notes': 'Manual nutrition entry',
    }


async def _ai_analyze_meal(payload: "MealCreate") -> Dict[str, Any]:
    prompt = (
        "Estimate meal nutrition. Return ONLY valid JSON with keys: "
        "name, foods_identified (array of strings), calories (int), protein (float), carbs (float), "
        "fat (float), fiber (float), status (string), portion_size (string), confidence (string), notes (string)."
    )
    user_text = (
        "Analyze this meal and provide nutrition as JSON with keys: "
        "name, foods_identified, calories, protein, carbs, fat, fiber, status, portion_size, confidence, notes. "
        f"Meal type: {payload.meal_type}. Name hint: {payload.name or 'not provided'}."
    )

    if openai_client:
        content: List[Dict[str, Any]] = [{'type': 'text', 'text': user_text}]
        if payload.image_base64:
            content.append({
                'type': 'image_url',
                'image_url': {'url': f'data:image/jpeg;base64,{payload.image_base64}'}
            })

        def _call_openai() -> str:
            response = openai_client.chat.completions.create(
                model=LLM_MODEL,
                response_format={'type': 'json_object'},
                messages=[
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': content},
                ],
                temperature=0.2,
            )
            return (response.choices[0].message.content or '{}').strip()

        raw = await asyncio.to_thread(_call_openai)
    else:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=503, detail='No AI key configured (OPENAI_API_KEY or EMERGENT_LLM_KEY)')
        if not (LlmChat and UserMessage and ImageContent):
            raise HTTPException(status_code=503, detail='emergentintegrations is not installed')

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"meal-{uuid.uuid4()}",
            system_message=prompt
        )
        chat.with_model("openai", LLM_MODEL)

        file_contents = []
        if payload.image_base64:
            file_contents = [ImageContent(image_base64=payload.image_base64)]

        raw_resp = await chat.send_message(
            UserMessage(
                text=user_text,
                file_contents=file_contents if file_contents else None
            )
        )
        raw = str(raw_resp).strip()

    if raw.startswith('```json'):
        raw = raw[7:]
    if raw.startswith('```'):
        raw = raw[3:]
    if raw.endswith('```'):
        raw = raw[:-3]
    raw = raw.strip()
    parsed = json.loads(raw)

    foods = parsed.get('foods_identified')
    if not isinstance(foods, list):
        foods = [payload.name or 'Meal']

    return {
        'name': parsed.get('name') or payload.name or 'Meal',
        'foods_identified': [str(f) for f in foods if str(f).strip()] or [payload.name or 'Meal'],
        'calories': _to_non_negative_int(parsed.get('calories'), _to_non_negative_int(payload.calories, 0)),
        'protein': _to_non_negative_float(parsed.get('protein'), _to_non_negative_float(payload.protein, 0)),
        'carbs': _to_non_negative_float(parsed.get('carbs'), _to_non_negative_float(payload.carbs, 0)),
        'fat': _to_non_negative_float(parsed.get('fat'), _to_non_negative_float(payload.fat, 0)),
        'fiber': _to_non_negative_float(parsed.get('fiber'), _to_non_negative_float(payload.fiber, 0)),
        'status': parsed.get('status') or 'Estimated',
        'portion_size': parsed.get('portion_size') or '1 serving',
        'confidence': parsed.get('confidence') or 'medium',
        'notes': parsed.get('notes') or 'AI-estimated values',
    }




# -------------------- AUTH --------------------
@api_router.post('/auth/request-otp')
async def request_otp(payload: OtpRequest):
    await create_and_store_otp(payload.email)
    return {'status': 'otp_sent'}


@api_router.post('/auth/register')
async def register(payload: UserCreate):
    if await db.users.find_one({'email': payload.email}):
        raise HTTPException(status_code=409, detail='Email already registered')
    if not await verify_latest_otp(payload.email, payload.otp_code):
        raise HTTPException(status_code=400, detail='Invalid or expired OTP code')

    profile = payload.profile.model_dump() if payload.profile else UserProfile().model_dump()
    user = {
        'id': str(uuid.uuid4()),
        'email': payload.email,
        'name': payload.name,
        'hashed_password': hash_password(payload.password),
        'mode': 'user',
        'profile': profile,
        'created_at': datetime.utcnow()
    }
    await db.users.insert_one(user)
    token = create_access_token({'sub': user['id']})
    return {'access_token': token, 'token_type': 'bearer', 'user': user_response(user)}


@api_router.post('/auth/login')
async def login(payload: UserLogin):
    user = await db.users.find_one({'email': payload.email})
    if not user or not verify_password(payload.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    token = create_access_token({'sub': user['id']})
    return {'access_token': token, 'token_type': 'bearer', 'user': user_response(user)}


@api_router.post('/auth/login-otp')
async def login_otp(payload: OtpVerify):
    user = await db.users.find_one({'email': payload.email})
    if not user or not await verify_latest_otp(payload.email, payload.code):
        raise HTTPException(status_code=401, detail='Invalid email or code')
    token = create_access_token({'sub': user['id']})
    return {'access_token': token, 'token_type': 'bearer', 'user': user_response(user)}


@api_router.post('/auth/reset-password')
async def reset_password(payload: PasswordReset):
    user = await db.users.find_one({'email': payload.email})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    if not await verify_latest_otp(payload.email, payload.otp_code):
        raise HTTPException(status_code=400, detail='Invalid or expired OTP code')
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'hashed_password': hash_password(payload.new_password)}}
    )
    return {'message': 'Password reset successful'}


@api_router.get('/auth/me')
async def me(current_user: dict = Depends(get_current_user)):
    return user_response(current_user)


@api_router.put('/auth/profile')
async def update_profile(update: UserUpdate, current_user: dict = Depends(get_current_user)):
    update_dict = {}
    if update.name:
        update_dict['name'] = update.name
    if update.mode:
        update_dict['mode'] = update.mode
    if update.profile:
        update_dict['profile'] = _profile_dict(update.profile)

    if update_dict:
        await db.users.update_one({'id': current_user['id']}, {'$set': update_dict})
    if update.profile:
        await _upsert_athlete_profile({**current_user, **update_dict}, update.profile)

    user = await db.users.find_one({'id': current_user['id']})
    return user_response(user)


@api_router.get('/athlete/profile')
async def get_athlete_profile(current_user: dict = Depends(get_current_user)):
    doc = await db.athlete_profiles.find_one({'user_id': current_user['id']})
    if doc:
        return clean_doc(doc)
    profile = _profile_from_payload(current_user.get('profile') or {}, current_user)
    return await _upsert_athlete_profile(current_user, profile)


@api_router.put('/athlete/profile')
async def upsert_athlete_profile(payload: AthleteProfileUpsert, current_user: dict = Depends(get_current_user)):
    profile_doc = await _upsert_athlete_profile(current_user, payload.profile)
    response = {'athlete_profile': profile_doc}
    if payload.generate_program:
        response.update(await _create_training_program(current_user, profile_doc.get('raw_profile') or {}))
    return response


@api_router.get('/coach/schemas')
async def coach_ai_schemas(current_user: dict = Depends(get_current_user)):
    return _schema_response()


@api_router.get('/coach/daily-snapshot')
async def get_daily_snapshot(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    return await _build_daily_snapshot(current_user, date)


@api_router.post('/coach/daily-snapshot')
async def save_daily_snapshot(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    snapshot = await _build_daily_snapshot(current_user, date)
    return await _save_daily_snapshot(snapshot)


@api_router.get('/coach/daily-analysis')
async def get_daily_analysis(
    date: Optional[str] = None,
    refresh: bool = False,
    current_user: dict = Depends(get_current_user),
):
    date_str, _, _ = _date_window(date)
    if not refresh:
        existing = await db.coach_daily_analyses.find_one({'user_id': current_user['id'], 'date': date_str})
        if existing:
            return clean_doc(existing)
    return await _generate_daily_analysis(current_user, date_str)


@api_router.post('/coach/daily-analysis')
async def create_daily_analysis(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    return await _generate_daily_analysis(current_user, date)


# -------------------- KNOWLEDGE LIBRARY --------------------
@api_router.get('/library/summary')
async def library_summary(current_user: dict = Depends(get_current_user)):
    collections = [
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
    ]
    summary = {}
    for collection_name in collections:
        summary[collection_name] = await db[collection_name].count_documents({})
    return summary


@api_router.get('/library/exercises')
async def list_library_exercises(
    category: Optional[str] = None,
    sport: Optional[str] = None,
    equipment: Optional[str] = None,
    difficulty: Optional[str] = None,
    movement: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    query: Dict[str, Any] = {}
    if category:
        query['category'] = category
    if sport:
        query['sport_tags'] = sport
    if equipment:
        query['equipment'] = equipment
    if difficulty:
        query['difficulty'] = difficulty
    if movement:
        query['movement_patterns'] = movement
    docs = await db.exercise_library.find(query).sort('name', 1).to_list(300)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/sports')
async def list_library_sports(sport: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'sport': sport} if sport else {}
    docs = await db.sport_profiles.find(query).sort('sport', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/sport-roles')
async def list_library_sport_roles(sport: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'sport': sport} if sport else {}
    docs = await db.sport_roles.find(query).sort([('sport', 1), ('role', 1)]).to_list(200)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/sport-training-rules')
async def list_library_sport_training_rules(sport: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'sport': sport} if sport else {}
    docs = await db.sport_training_rules.find(query).sort([('sport', 1), ('id', 1)]).to_list(300)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/movement-patterns')
async def list_library_movement_patterns(current_user: dict = Depends(get_current_user)):
    docs = await db.movement_patterns.find({}).sort('pattern', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/physical-qualities')
async def list_library_physical_qualities(group: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'group': group} if group else {}
    docs = await db.physical_qualities.find(query).sort([('group', 1), ('quality', 1)]).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/workout-templates')
async def list_library_workout_templates(
    category: Optional[str] = None,
    sport: Optional[str] = None,
    level: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    query: Dict[str, Any] = {}
    if category:
        query['category'] = category
    if sport:
        query['sport_tags'] = sport
    if level:
        query['level'] = level
    docs = await db.workout_templates.find(query).sort('title', 1).to_list(200)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/injury-modifications')
async def list_library_injury_modifications(body_area: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'body_area': body_area} if body_area else {}
    docs = await db.injury_modifications.find(query).sort('body_area', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/progression-rules')
async def list_library_progression_rules(rule_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'rule_type': rule_type} if rule_type else {}
    docs = await db.progression_rules.find(query).sort('id', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/readiness-rules')
async def list_library_readiness_rules(category: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'category': category} if category else {}
    docs = await db.readiness_rules.find(query).sort('id', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/benchmark-tests')
async def list_library_benchmark_tests(sport: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'sport_tags': sport} if sport else {}
    docs = await db.benchmark_tests.find(query).sort('test_name', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/equipment')
async def list_library_equipment(setting: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'setting': setting} if setting else {}
    docs = await db.equipment_library.find(query).sort('name', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/sources')
async def list_library_sources(current_user: dict = Depends(get_current_user)):
    docs = await db.knowledge_sources.find({}).sort('title', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/source-registry')
async def list_library_source_registry(current_user: dict = Depends(get_current_user)):
    docs = await db.source_registry.find({}).sort([('evidence_rank', -1), ('id', 1)]).to_list(200)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/nutrition-guidelines')
async def list_library_nutrition_guidelines(goal: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'goal_tags': goal} if goal else {}
    docs = await db.nutrition_guidelines.find(query).sort('id', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/running-workouts')
async def list_library_running_workouts(level: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'suitable_user_level': level} if level else {}
    docs = await db.running_workouts.find(query).sort('id', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


@api_router.get('/library/running-plan-rules')
async def list_library_running_plan_rules(rule_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'rule_type': rule_type} if rule_type else {}
    docs = await db.running_plan_rules.find(query).sort('id', 1).to_list(100)
    return [clean_doc(doc) for doc in docs]


# -------------------- WORKOUTS --------------------
@api_router.get('/training-load')
async def training_load(current_user: dict = Depends(get_current_user)):
    return {
        'today': {'load_au': 420, 'intensity': 'moderate', 'recovery_status': 'good', 'notes': ''},
        'yesterday_au': 380
    }


@api_router.get('/program/summary')
async def program_summary(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    week_start_str = week_start.strftime('%Y-%m-%d')
    week_end_str = week_end.strftime('%Y-%m-%d')

    workouts = await db.workouts.find({
        'user_id': current_user['id'],
        'scheduled_date': {'$gte': week_start_str, '$lte': week_end_str}
    }).to_list(200)

    total_count = len(workouts)
    completed_count = len([w for w in workouts if w.get('completed')])

    next_workout = await db.workouts.find_one({
        'user_id': current_user['id'],
        'scheduled_date': {'$gt': today.strftime('%Y-%m-%d')}
    }, sort=[('scheduled_date', 1)])

    sports = current_user.get('profile', {}).get('sports', [])
    program_title = 'Your Program'
    program_subtitle = None
    if sports:
        program_subtitle = f"{sports[0]} Training"

    return ProgramSummary(
        title=program_title,
        subtitle=program_subtitle,
        next_session=next_workout.get('title') if next_workout else None,
        week_label=f"Week of {week_start.strftime('%b %d')}",
        progress_completed=completed_count,
        progress_total=total_count
    ).model_dump()


@api_router.get('/lessons')
async def list_lessons(current_user: dict = Depends(get_current_user)):
    docs = await db.lessons.find({}).sort('title', 1).to_list(200)
    return [clean_doc(d) for d in docs]


@api_router.get('/goals')
async def get_goals(current_user: dict = Depends(get_current_user)):
    docs = await db.goals.find({'user_id': current_user['id']}).to_list(50)
    return [clean_doc(d) for d in docs]


# -------------------- NUTRITION --------------------
@api_router.post('/meals/analyze')
async def analyze_meal(payload: MealCreate, save: bool = True, current_user: dict = Depends(get_current_user)):
    manual_only = payload.calories is not None and payload.image_base64 is None
    ai_analyzed = False
    if manual_only:
        result = _manual_meal_result(payload)
    else:
        try:
            result = await _ai_analyze_meal(payload)
            ai_analyzed = True
        except Exception as exc:
            logger.warning(f'Meal AI analysis failed, falling back to manual/default values: {exc}')
            result = _manual_meal_result(payload)

    if not save:
        return {**result, 'saved': False, 'ai_analyzed': ai_analyzed}

    meal = Meal(
        user_id=current_user['id'],
        date=datetime.utcnow().strftime('%Y-%m-%d'),
        meal_type=payload.meal_type,
        name=result['name'],
        calories=result['calories'],
        protein=result['protein'],
        carbs=result['carbs'],
        fat=result['fat'],
        fiber=result['fiber'],
        foods_identified=result['foods_identified'],
        status=result['status'],
        ai_analyzed=ai_analyzed,
    )
    await db.meals.insert_one(meal.model_dump())
    return {**result, 'id': meal.id, 'saved': True, 'ai_analyzed': ai_analyzed}


@api_router.get('/meals')
async def get_meals(current_user: dict = Depends(get_current_user)):
    docs = await db.meals.find({'user_id': current_user['id']}).sort('date', -1).to_list(100)
    return [clean_doc(d) for d in docs]


@api_router.get('/meals/daily-summary')
async def daily_summary(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    date_str = date or datetime.utcnow().strftime('%Y-%m-%d')
    meals = await db.meals.find({'user_id': current_user['id'], 'date': date_str}).to_list(100)
    total_calories = sum(m.get('calories', 0) for m in meals)
    total_protein = sum(m.get('protein', 0) for m in meals)
    total_carbs = sum(m.get('carbs', 0) for m in meals)
    total_fat = sum(m.get('fat', 0) for m in meals)
    total_fiber = sum(m.get('fiber', 0) for m in meals)

    # simple targets
    calorie_goal = 2200
    protein_goal = 140
    carbs_goal = 250
    fat_goal = 70
    fiber_goal = 25

    return {
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs,
        'total_fat': total_fat,
        'total_fiber': total_fiber,
        'calorie_goal': calorie_goal,
        'protein_goal': protein_goal,
        'carbs_goal': carbs_goal,
        'fat_goal': fat_goal,
        'fiber_goal': fiber_goal,
        'meals': [clean_doc(m) for m in meals]
    }


@api_router.get('/daily-summary')
async def daily_summary_compat(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    return await daily_summary(date=date, current_user=current_user)


# -------------------- COMPATIBILITY SHIMS --------------------
@api_router.post('/sleep/notes')
async def save_sleep_note(payload: SleepNoteCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.utcnow()
    note = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'date': now.strftime('%Y-%m-%d'),
        'mood': payload.mood or 'relaxed',
        'activities': _normalize_tags(payload.activities),
        'note': payload.note,
        'created_at': now,
        'updated_at': now,
    }
    existing = await db.sleep_notes.find_one({'user_id': current_user['id'], 'date': note['date']})
    if existing:
        note['id'] = existing['id']
        note['created_at'] = existing.get('created_at', now)
        await db.sleep_notes.update_one(
            {'id': existing['id'], 'user_id': current_user['id']},
            {'$set': note},
            upsert=True,
        )
    else:
        await db.sleep_notes.insert_one(note)
    return clean_doc(note)


@api_router.post('/sleep/sessions')
async def create_sleep_session(payload: SleepSessionCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.utcnow()
    session = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'start_time': payload.start_time,
        'end_time': payload.end_time,
        'alarm_time': payload.alarm_time,
        'pre_sleep_mood': payload.pre_sleep_mood,
        'pre_sleep_activities': _normalize_tags(payload.pre_sleep_activities),
        'note': payload.note,
        'duration_hours': payload.duration_hours,
        'deep_sleep_hours': payload.deep_sleep_hours,
        'rem_sleep_hours': payload.rem_sleep_hours,
        'efficiency': payload.efficiency,
        'sleep_quality': payload.sleep_quality,
        'source': payload.source or 'sleep_tracker',
        'created_at': now,
        'updated_at': now,
    }
    session.update(_sleep_session_metrics(session))

    lookup: Dict[str, Any] = {'user_id': current_user['id']}
    if payload.start_time:
        lookup['start_time'] = payload.start_time
    if payload.end_time:
        lookup['end_time'] = payload.end_time
    if payload.alarm_time:
        lookup['alarm_time'] = payload.alarm_time

    existing = await db.sleep_sessions.find_one(lookup)
    if existing:
        session['id'] = existing['id']
        session['created_at'] = existing.get('created_at', now)
        await db.sleep_sessions.update_one(
            {'id': existing['id'], 'user_id': current_user['id']},
            {'$set': session},
            upsert=True,
        )
    else:
        await db.sleep_sessions.insert_one(session)
    return clean_doc(session)


@api_router.get('/sleep/sessions')
async def list_sleep_sessions(current_user: dict = Depends(get_current_user)):
    docs = await db.sleep_sessions.find({'user_id': current_user['id']}).sort('created_at', -1).to_list(100)
    return [_sleep_session_response(d) for d in docs]


@api_router.get('/sleep/stats')
async def sleep_stats(current_user: dict = Depends(get_current_user)):
    summary = await _sleep_user_summary(current_user['id'])
    return {
        'avg_score': summary['avg_score'],
        'avg_duration': summary['avg_duration'],
        'avg_deep_sleep': summary['avg_deep_sleep'],
        'avg_rem_sleep': summary['avg_rem_sleep'],
        'total_sessions': summary['total_sessions'],
        'sleep_debt': summary['sleep_debt'],
        'trend': summary['trend'],
        'latest_session': summary['latest_session'],
    }


@api_router.get('/coach/clients')
async def coach_clients(current_user: dict = Depends(get_current_user)):
    _require_coach_user(current_user)

    accepted_requests = await db.coach_requests.find({
        'coach_id': current_user['id'],
        'status': 'accepted',
    }).sort('created_at', -1).to_list(100)

    client_ids = []
    for request in accepted_requests:
        client_id = request.get('client_id')
        if client_id and client_id not in client_ids:
            client_ids.append(client_id)
    if not client_ids:
        return []

    clients = await db.users.find({'id': {'$in': client_ids}}).to_list(100)
    result = []
    for client in clients:
        workouts = await db.workouts.find({'user_id': client['id']}).to_list(100)
        completed = len([w for w in workouts if w.get('completed')])
        result.append({
            'id': client['id'],
            'name': client.get('name', ''),
            'email': client.get('email', ''),
            'avatar': None,
            'profile': client.get('profile', {}),
            'total_workouts': len(workouts),
            'completed_workouts': completed,
            'compliance_rate': round((completed / len(workouts)) * 100, 1) if workouts else 0,
        })
    return result


@api_router.get('/coach/search-users')
async def coach_search_users(query: str = '', current_user: dict = Depends(get_current_user)):
    _require_coach_user(current_user)

    term = query.strip()
    if len(term) < 2:
        return []

    docs = await db.users.find({
        'id': {'$ne': current_user['id']},
        'mode': {'$ne': 'coach'},
        '$or': [
            {'name': {'$regex': term, '$options': 'i'}},
            {'email': {'$regex': term, '$options': 'i'}},
        ],
    }).to_list(20)
    return [{'id': d['id'], 'name': d.get('name', ''), 'email': d.get('email', '')} for d in docs]


@api_router.post('/coach/send-request')
async def coach_send_request(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    _require_coach_user(current_user)

    client_id = payload.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id is required')
    if client_id == current_user['id']:
        raise HTTPException(status_code=400, detail='client_id cannot match coach')

    client_user = await db.users.find_one({'id': client_id})
    if not client_user:
        raise HTTPException(status_code=404, detail='Client not found')

    existing_request = await _coach_client_request(current_user['id'], client_id)
    now = datetime.utcnow()
    if existing_request:
        existing_status = existing_request.get('status')
        if existing_status == 'accepted':
            raise HTTPException(status_code=409, detail='Client already connected')
        request_update = {
            'message': payload.get('message'),
            'status': 'pending',
            'updated_at': now,
        }
        await db.coach_requests.update_one(
            {'id': existing_request['id'], 'coach_id': current_user['id'], 'client_id': client_id},
            {'$set': request_update},
        )
        existing_request.update(request_update)
        return clean_doc(existing_request)

    request_doc = {
        'id': str(uuid.uuid4()),
        'coach_id': current_user['id'],
        'coach_name': current_user.get('name', 'Coach'),
        'client_id': client_id,
        'client_name': client_user.get('name', ''),
        'message': payload.get('message'),
        'status': 'pending',
        'created_at': now,
        'updated_at': now,
    }
    await db.coach_requests.insert_one(request_doc)
    return clean_doc(request_doc)


@api_router.post('/coach/workouts')
async def coach_create_workout(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    _require_coach_user(current_user)

    client_id = payload.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id is required')
    if not await _coach_client_is_accepted(current_user['id'], client_id):
        raise HTTPException(status_code=403, detail='Client connection required')

    workout = Workout(
        user_id=client_id,
        title=payload.get('title') or 'Coach Workout',
        category=payload.get('workout_type') or 'Workout',
        duration=_to_non_negative_int(payload.get('duration'), 45),
        difficulty=payload.get('difficulty') or 'Intermediate',
        equipment=[],
        exercises=[
            WorkoutExercise(
                name=str(ex.get('name', 'Exercise'))
            )
            for ex in payload.get('exercises', [])
            if isinstance(ex, dict)
        ],
        description=payload.get('description'),
        ai_generated=False,
        scheduled_date=datetime.utcnow().strftime('%Y-%m-%d'),
    )
    workout_doc = workout.model_dump()
    workout_doc.update({
        'source': 'coach',
        'assigned_by': current_user['id'],
        'assigned_by_name': current_user.get('name', 'Coach'),
    })
    await db.workouts.insert_one(workout_doc)
    return clean_doc(workout_doc)


@api_router.post('/coach/meals')
async def coach_create_meal(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    _require_coach_user(current_user)

    client_id = payload.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id is required')
    if not await _coach_client_is_accepted(current_user['id'], client_id):
        raise HTTPException(status_code=403, detail='Client connection required')

    meal = {
        'id': str(uuid.uuid4()),
        'coach_id': current_user['id'],
        'coach_name': current_user.get('name', 'Coach'),
        'client_id': client_id,
        'title': payload.get('title') or 'Meal Plan',
        'description': payload.get('description'),
        'meal_type': payload.get('meal_type') or 'lunch',
        'total_calories': _to_non_negative_int(payload.get('total_calories'), 0),
        'is_completed': False,
        'created_at': datetime.utcnow(),
    }
    await db.coach_meals.insert_one(meal)
    return clean_doc(meal)


@api_router.post('/coach/goals')
async def coach_create_goal(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    _require_coach_user(current_user)

    client_id = payload.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id is required')
    if not await _coach_client_is_accepted(current_user['id'], client_id):
        raise HTTPException(status_code=403, detail='Client connection required')

    goal = {
        'id': str(uuid.uuid4()),
        'coach_id': current_user['id'],
        'coach_name': current_user.get('name', 'Coach'),
        'client_id': client_id,
        'title': payload.get('title') or 'Goal',
        'description': payload.get('description'),
        'goal_type': payload.get('goal_type') or 'general_fitness',
        'target_value': payload.get('target_value'),
        'unit': payload.get('unit'),
        'target_date': payload.get('target_date'),
        'current_value': None,
        'is_completed': False,
        'created_at': datetime.utcnow(),
    }
    await db.coach_goals.insert_one(goal)
    return clean_doc(goal)


@api_router.get('/client/pending-requests')
async def client_pending_requests(current_user: dict = Depends(get_current_user)):
    _require_client_user(current_user)

    docs = await db.coach_requests.find({
        'client_id': current_user['id'],
        'status': 'pending',
    }).sort('created_at', -1).to_list(100)
    return [clean_doc(d) for d in docs]


@api_router.post('/client/respond-request/{request_id}')
async def client_respond_request(request_id: str, approve: bool = True, current_user: dict = Depends(get_current_user)):
    _require_client_user(current_user)

    request = await db.coach_requests.find_one({'id': request_id, 'client_id': current_user['id']})
    if not request:
        raise HTTPException(status_code=404, detail='Request not found')
    if request.get('status') != 'pending':
        raise HTTPException(status_code=409, detail='Request is not pending')

    status = 'accepted' if approve else 'declined'
    await db.coach_requests.update_one(
        {'id': request_id, 'client_id': current_user['id']},
        {'$set': {'status': status, 'responded_at': datetime.utcnow(), 'updated_at': datetime.utcnow()}},
    )
    return {'message': f'Request {status}'}


@api_router.get('/my-coach-workouts')
async def my_coach_workouts(current_user: dict = Depends(get_current_user)):
    _require_client_user(current_user)

    docs = await db.workouts.find({
        'user_id': current_user['id'],
        'source': 'coach',
    }).sort('created_at', -1).to_list(100)
    return [
        {
            'id': doc['id'],
            'title': doc.get('title', ''),
            'description': doc.get('description'),
            'workout_type': doc.get('category', ''),
            'difficulty': doc.get('difficulty', ''),
            'duration': doc.get('duration', 0),
            'scheduled_date': doc.get('scheduled_date'),
            'is_completed': doc.get('completed', False),
        }
        for doc in docs
    ]


@api_router.get('/my-coach-meals')
async def my_coach_meals(current_user: dict = Depends(get_current_user)):
    _require_client_user(current_user)

    docs = await db.coach_meals.find({'client_id': current_user['id']}).sort('created_at', -1).to_list(100)
    return [clean_doc(d) for d in docs]


@api_router.get('/my-coach-goals')
async def my_coach_goals(current_user: dict = Depends(get_current_user)):
    _require_client_user(current_user)

    docs = await db.coach_goals.find({'client_id': current_user['id']}).sort('created_at', -1).to_list(100)
    return [clean_doc(d) for d in docs]


@api_router.post('/coach/workouts/{workout_id}/complete')
async def complete_coach_workout(workout_id: str, current_user: dict = Depends(get_current_user)):
    _require_client_user(current_user)
    return await complete_workout(workout_id, current_user)


# -------------------- HEALTH + LOGS --------------------
@api_router.post('/health/metrics')
async def log_health_metric(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    payload['user_id'] = current_user['id']
    payload['recorded_at'] = datetime.utcnow()
    await db.health_metrics.insert_one(payload)
    return {'message': 'metric logged'}


@api_router.get('/health/summary')
async def health_summary(current_user: dict = Depends(get_current_user)):
    sleep_summary = await _sleep_user_summary(current_user['id'])
    # very simple summary
    return {
        'resting_hr': {'value': None, 'trend': 'stable', 'last_updated': None},
        'hrv': {'value': None, 'trend': 'stable', 'last_updated': None},
        'sleep': {
            'value': sleep_summary['avg_duration'] or None,
            'trend': sleep_summary['trend'],
            'last_updated': sleep_summary['last_updated'],
        },
        'weight': {'value': None, 'trend': 'stable', 'last_updated': None},
    }


@api_router.get('/health/strain')
async def strain_summary(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().strftime('%Y-%m-%d')
    days = [(datetime.utcnow() - timedelta(days=i)) for i in range(6, -1, -1)]
    history = []
    total_week = 0
    for day in days:
        day_str = day.strftime('%Y-%m-%d')
        day_label = day.strftime('%a')
        workouts = await db.workouts.find({'user_id': current_user['id'], 'scheduled_date': day_str}).to_list(100)
        day_load = sum(w.get('duration', 0) for w in workouts)
        total_week += day_load
        history.append({'day': day_label, 'value': day_load})

    today_value = next((h['value'] for h in history if h['day'] == datetime.utcnow().strftime('%a')), None)
    weekly_avg = round(total_week / 7, 1) if history else None

    if today_value is None:
        status = 'moderate'
    elif today_value < 30:
        status = 'low'
    elif today_value < 90:
        status = 'moderate'
    else:
        status = 'high'

    return StrainSummary(
        today=round(today_value, 1) if today_value is not None else None,
        status=status,
        weeklyAvg=weekly_avg,
        history=history
    ).model_dump()


@api_router.get('/health/recovery')
async def recovery_summary(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().strftime('%Y-%m-%d')
    log = await db.quick_logs.find_one({'user_id': current_user['id'], 'date': today})
    sleep_quality = log.get('sleep_quality') if log else None
    sleep_summary = await _sleep_user_summary(current_user['id'])

    score_from_quick_log = int(sleep_quality * 20) if sleep_quality is not None else None
    score_from_sleep = int(sleep_summary['avg_score']) if sleep_summary['total_sessions'] else None
    if score_from_quick_log is not None and score_from_sleep is not None:
        score = round((score_from_quick_log + score_from_sleep) / 2)
    else:
        score = score_from_sleep if score_from_sleep is not None else score_from_quick_log

    if score is None:
        status = 'moderate'
    elif score < 40:
        status = 'low'
    elif score < 70:
        status = 'moderate'
    else:
        status = 'high'

    return RecoverySummary(
        score=score,
        status=status,
        sleep={
            'value': (
                sleep_summary['latest_duration'] if sleep_summary['total_sessions']
                else None
            ),
            'quality': sleep_summary['latest_quality_label'],
        },
        hrv={'value': None, 'unit': 'ms', 'trend': 'stable'},
        rhr={'value': None, 'unit': 'bpm', 'trend': 'stable'},
    ).model_dump()


@api_router.get('/health/biology')
async def biology_summary(current_user: dict = Depends(get_current_user)):
    latest = await db.health_metrics.find_one({'user_id': current_user['id']}, sort=[('recorded_at', -1)])
    weight_value = latest.get('weight') if latest else None
    body_fat_value = latest.get('body_fat') if latest else None
    lean_mass_value = latest.get('lean_mass') if latest else None

    status = 'stable' if latest else 'needs_update'
    insight = None
    if weight_value is not None:
        insight = 'Latest weight recorded'

    return BiologySummary(
        leanMass={'value': lean_mass_value, 'unit': 'kg', 'trend': 'stable'},
        bodyFat={'value': body_fat_value, 'unit': '%', 'trend': 'stable'},
        weight={'value': weight_value, 'unit': 'kg'},
        status=status,
        insight=insight
    ).model_dump()


@api_router.post('/health/injuries')
async def log_injury(payload: InjuryLogCreate, current_user: dict = Depends(get_current_user)):
    injury = InjuryLog(user_id=current_user['id'], **payload.model_dump())
    await db.injury_logs.insert_one(injury.model_dump())
    return clean_doc(injury.model_dump())


@api_router.get('/health/injuries')
async def get_injuries(active: bool = True, current_user: dict = Depends(get_current_user)):
    query = {'user_id': current_user['id']}
    if active:
        query['is_active'] = True
    docs = await db.injury_logs.find(query).to_list(100)
    return [clean_doc(d) for d in docs]


@api_router.put('/health/injuries/{injury_id}/resolve')
async def resolve_injury(injury_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.injury_logs.update_one({'id': injury_id, 'user_id': current_user['id']}, {'$set': {'is_active': False}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail='Injury not found')
    return {'message': 'Injury marked as resolved'}


@api_router.post('/log/quick')
async def create_quick_log(payload: QuickLogCreate, current_user: dict = Depends(get_current_user)):
    energy = payload.energy or 'moderate'
    stress = payload.stress or 'moderate'
    log = QuickLog(
        user_id=current_user['id'],
        date=datetime.utcnow().strftime('%Y-%m-%d'),
        mood=payload.mood,
        energy=energy,
        stress=stress,
        sleep_quality=payload.sleep_quality,
        soreness_regions=payload.soreness_regions,
        note=payload.note,
    )
    await db.quick_logs.insert_one(log.model_dump())
    return clean_doc(log.model_dump())


@api_router.get('/log/quick/today')
async def get_quick_log_today(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().strftime('%Y-%m-%d')
    log = await db.quick_logs.find_one({'user_id': current_user['id'], 'date': today})
    return clean_doc(log) if log else None


@api_router.get('/log/quick')
async def list_quick_logs(year: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    query = {'user_id': current_user['id']}
    docs = await db.quick_logs.find(query).sort('date', -1).to_list(200)
    if year is not None:
        docs = [doc for doc in docs if str(doc.get('date', '')).startswith(str(year))]
    return [clean_doc(doc) for doc in docs]


# -------------------- JOURNAL --------------------
@api_router.get('/journal/templates')
async def journal_templates(current_user: dict = Depends(get_current_user)):
    return [dict(template) for template in _journal_template_definitions()]


@api_router.get('/journal/programs')
async def journal_programs(current_user: dict = Depends(get_current_user)):
    programs = [dict(program) for program in _journal_program_definitions()]
    docs = await db.journal_program_enrollments.find({'user_id': current_user['id']}).sort('updated_at', -1).to_list(100)
    active_enrollments = []
    for doc in docs:
        if not doc.get('is_active', True):
            continue
        enrollment = clean_doc(doc)
        enrollment['current_day'] = _journal_program_day(doc, doc.get('program_id', ''))
        active_enrollments.append(enrollment)
    return {'programs': programs, 'active_enrollments': active_enrollments}


@api_router.post('/journal/programs/{program_id}/start')
async def start_journal_program(program_id: str, current_user: dict = Depends(get_current_user)):
    program = _journal_program_by_id(program_id)
    if not program:
        raise HTTPException(status_code=404, detail='Program not found')

    existing = await db.journal_program_enrollments.find_one({
        'user_id': current_user['id'],
        'program_id': program_id,
    })
    if existing and existing.get('is_active', True):
        raise HTTPException(status_code=409, detail='Already enrolled in this program')

    now = datetime.utcnow()
    enrollment = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'program_id': program_id,
        'program_name': program['name'],
        'current_day': 1,
        'is_active': True,
        'start_date': now,
        'updated_at': now,
        'duration_days': program['duration_days'],
    }
    if existing:
        enrollment['id'] = existing['id']
        await db.journal_program_enrollments.update_one(
            {'id': existing['id'], 'user_id': current_user['id']},
            {'$set': enrollment},
            upsert=True,
        )
    else:
        await db.journal_program_enrollments.insert_one(enrollment)
    return clean_doc(enrollment)


@api_router.post('/journal/deep')
async def create_deep_journal_entry(payload: DeepJournalCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.utcnow()
    entry = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'entry_type': 'deep',
        'title': payload.title.strip() if payload.title else None,
        'content': payload.content.strip(),
        'tags': _normalize_tags(payload.tags),
        'is_pinned': bool(payload.is_pinned),
        'date': now.strftime('%Y-%m-%d'),
        'created_at': now,
        'updated_at': now,
        'word_count': _journal_word_count(payload.content),
    }
    await db.journal_entries.insert_one(entry)
    return clean_doc(entry)


@api_router.get('/journal/deep')
async def list_deep_journal_entries(limit: int = 20, current_user: dict = Depends(get_current_user)):
    docs = await db.journal_entries.find({
        'user_id': current_user['id'],
        'entry_type': 'deep',
    }).sort('created_at', -1).to_list(max(1, min(limit, 200)))
    return [_journal_entry_response(doc) for doc in docs]


@api_router.get('/journal/deep/{entry_id}')
async def get_deep_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    entry = await db.journal_entries.find_one({
        'id': entry_id,
        'user_id': current_user['id'],
        'entry_type': 'deep',
    })
    if not entry:
        raise HTTPException(status_code=404, detail='Journal entry not found')
    return _journal_entry_response(entry)


@api_router.put('/journal/deep/{entry_id}')
async def update_deep_journal_entry(entry_id: str, payload: DeepJournalCreate, current_user: dict = Depends(get_current_user)):
    update_doc = {
        'title': payload.title.strip() if payload.title else None,
        'content': payload.content.strip(),
        'tags': _normalize_tags(payload.tags),
        'is_pinned': bool(payload.is_pinned),
        'updated_at': datetime.utcnow(),
        'word_count': _journal_word_count(payload.content),
    }
    result = await db.journal_entries.update_one(
        {'id': entry_id, 'user_id': current_user['id'], 'entry_type': 'deep'},
        {'$set': update_doc},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail='Journal entry not found')
    entry = await db.journal_entries.find_one({'id': entry_id, 'user_id': current_user['id'], 'entry_type': 'deep'})
    return _journal_entry_response(entry)


@api_router.delete('/journal/deep/{entry_id}')
async def delete_deep_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.journal_entries.delete_one({'id': entry_id, 'user_id': current_user['id'], 'entry_type': 'deep'})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Journal entry not found')
    return {'message': 'Journal entry deleted'}


@api_router.post('/journal/guided')
async def create_guided_journal_entry(payload: GuidedJournalCreate, current_user: dict = Depends(get_current_user)):
    template = _journal_template_by_id(payload.template_id)
    now = datetime.utcnow()
    responses = {str(k): str(v).strip() for k, v in payload.responses.items()}
    content = _journal_responses_text(responses)
    tags = [template['category']] if template else ['guided']
    if payload.program_id:
        tags.append(str(payload.program_id))
    if payload.cbt_distortion:
        tags.append('cbt')
    entry = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'entry_type': 'guided',
        'title': payload.template_name or (template['name'] if template else 'Guided Journal'),
        'content': content,
        'responses': responses,
        'template_id': payload.template_id,
        'template_name': payload.template_name or (template['name'] if template else None),
        'program_id': payload.program_id,
        'program_day': payload.program_day,
        'cbt_distortion': payload.cbt_distortion,
        'tags': _normalize_tags(tags),
        'is_pinned': False,
        'date': now.strftime('%Y-%m-%d'),
        'created_at': now,
        'updated_at': now,
        'word_count': _journal_word_count(content),
    }
    await db.journal_entries.insert_one(entry)

    if payload.program_id:
        enrollment = await db.journal_program_enrollments.find_one({
            'user_id': current_user['id'],
            'program_id': payload.program_id,
        })
        program = _journal_program_by_id(payload.program_id)
        duration = int(program['duration_days']) if program else 7
        next_day = max(1, min(duration, _to_non_negative_int(payload.program_day, 1) + 1))
        if enrollment:
            await db.journal_program_enrollments.update_one(
                {'id': enrollment['id'], 'user_id': current_user['id']},
                {'$set': {'current_day': next_day, 'updated_at': now, 'is_active': True}},
            )
        else:
            await db.journal_program_enrollments.insert_one({
                'id': str(uuid.uuid4()),
                'user_id': current_user['id'],
                'program_id': payload.program_id,
                'program_name': payload.template_name or (program['name'] if program else payload.program_id),
                'current_day': next_day,
                'is_active': True,
                'start_date': now,
                'updated_at': now,
                'duration_days': duration,
            })

    return clean_doc(entry)


@api_router.get('/journal/on-this-day')
async def journal_on_this_day(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow()
    docs = await db.journal_entries.find({
        'user_id': current_user['id'],
    }).sort('created_at', -1).to_list(200)
    matches = []
    for doc in docs:
        created_at = _parse_iso_datetime(doc.get('created_at'))
        if not created_at:
            continue
        if created_at.month == today.month and created_at.day == today.day and created_at.year < today.year:
            item = _journal_entry_response(doc)
            item['years_ago'] = max(1, today.year - created_at.year)
            matches.append(item)
    return matches[:20]


@api_router.get('/journal/calendar')
async def journal_calendar(year: Optional[int] = None, month: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    now = datetime.utcnow()
    year = year or now.year
    month = month or now.month
    month_start = datetime(year, month, 1)
    next_month = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    month_end = next_month - timedelta(seconds=1)

    calendar: Dict[str, Dict[str, Any]] = {}

    journal_entries = await db.journal_entries.find({
        'user_id': current_user['id'],
        'date': {'$gte': month_start.strftime('%Y-%m-%d'), '$lte': month_end.strftime('%Y-%m-%d')},
    }).to_list(500)
    for entry in journal_entries:
        date_key = str(entry.get('date') or month_start.strftime('%Y-%m-%d'))
        bucket = calendar.setdefault(date_key, {'quick_log': False, 'guided': 0, 'deep': 0, 'mood': None})
        if entry.get('entry_type') == 'guided':
            bucket['guided'] += 1
        elif entry.get('entry_type') == 'deep':
            bucket['deep'] += 1

    quick_logs = await db.quick_logs.find({
        'user_id': current_user['id'],
        'date': {'$gte': month_start.strftime('%Y-%m-%d'), '$lte': month_end.strftime('%Y-%m-%d')},
    }).to_list(500)
    for log in quick_logs:
        date_key = str(log.get('date'))
        bucket = calendar.setdefault(date_key, {'quick_log': False, 'guided': 0, 'deep': 0, 'mood': None})
        bucket['quick_log'] = True
        bucket['mood'] = log.get('mood') or bucket['mood']

    mood_entries = await db.moods.find({
        'user_id': current_user['id'],
        'date': {'$gte': month_start.strftime('%Y-%m-%d'), '$lte': month_end.strftime('%Y-%m-%d')},
    }).sort('timestamp', -1).to_list(500)
    for mood_entry in mood_entries:
        date_key = str(mood_entry.get('date'))
        bucket = calendar.setdefault(date_key, {'quick_log': False, 'guided': 0, 'deep': 0, 'mood': None})
        if not bucket.get('mood'):
            mood_value = mood_entry.get('mood_emoji') or mood_entry.get('mood_value')
            if isinstance(mood_value, int):
                mood_value = {5: 'great', 4: 'good', 3: 'okay', 2: 'bad', 1: 'awful'}.get(mood_value, 'okay')
            bucket['mood'] = mood_value if isinstance(mood_value, str) else bucket['mood']

    return calendar


# -------------------- AI JOURNAL --------------------
def _journal_search_matches(entry: Dict[str, Any], query: str) -> bool:
    haystack = _journal_searchable_text(entry)
    if query in haystack:
        return True
    return any(query in str(tag).lower() for tag in (entry.get('tags') or []))


def _journal_result_summary(results: List[Dict[str, Any]], query: str) -> str:
    if not results:
        return f"No journal entries matched '{query}'. Try different keywords or search by mood, workout, or event."
    type_counts = Counter(result['type'] for result in results)
    parts = [f"Found {len(results)} match{'es' if len(results) != 1 else ''} for '{query}'."]
    if type_counts:
        parts.append(", ".join(f"{count} {kind.replace('_', ' ')}" for kind, count in type_counts.items()))
    return " ".join(parts)


def _journal_patterns(inspected_entries: List[Dict[str, Any]], quick_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    mood_counts = Counter()
    for log in quick_logs:
        mood = str(log.get('mood') or '').strip()
        if mood:
            mood_counts[mood] += 1

    tag_counts = Counter()
    for entry in inspected_entries:
        for tag in entry.get('tags') or []:
            tag_counts[str(tag)] += 1

    positive = mood_counts.get('great', 0) + mood_counts.get('good', 0)
    negative = mood_counts.get('bad', 0) + mood_counts.get('awful', 0)
    guided_count = sum(1 for entry in inspected_entries if entry.get('entry_type') == 'guided')
    deep_count = sum(1 for entry in inspected_entries if entry.get('entry_type') == 'deep')
    quick_count = len(quick_logs)

    summary = f"{len(inspected_entries)} journal entries and {quick_count} quick logs in this period."
    if mood_counts:
        summary += f" Mood leaned {mood_counts.most_common(1)[0][0]}."

    strength = 'You are building a reflection habit.' if len(inspected_entries) + quick_count >= 5 else 'Your logging habit is still small, which makes patterns hard to spot.'
    if positive > negative:
        strength = 'Your recent mood trend looks more positive than negative.'
    elif deep_count >= guided_count and deep_count > 0:
        strength = 'Your free-write entries show strong self-reflection depth.'

    improvement = 'Add a quick log on tougher days so patterns become easier to see.'
    if guided_count == 0:
        improvement = 'Try one guided journal entry this week to surface a more structured pattern.'
    elif negative > positive:
        improvement = 'Capture one recovery-focused note after harder days to offset the negative trend.'

    recommendation = 'Keep it simple: one quick log after training and one longer reflection each week.'
    if tag_counts:
        recommendation = f"Lean into the themes you write about most: {tag_counts.most_common(2)[0][0]}."

    return {
        'summary': summary,
        'strength': strength,
        'improvement': improvement,
        'recommendation': recommendation,
    }


async def _journal_ai_insights(period: str, entries: List[Dict[str, Any]], quick_logs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not openai_client:
        return None

    snippet_lines = []
    for entry in entries[:8]:
        text = _journal_entry_text(entry)
        if text:
            snippet_lines.append(f"{entry.get('entry_type', 'entry')}: {text[:500]}")
    for log in quick_logs[:5]:
        snippet_lines.append(
            f"quick_log: mood={log.get('mood')}, energy={log.get('energy')}, stress={log.get('stress')}, note={str(log.get('note') or '')[:200]}"
        )

    prompt = (
        "Summarize journal patterns for an athlete. Return only valid JSON with keys "
        "summary, strength, improvement, recommendation. Keep each value concise."
    )
    user_text = (
        f"Period: {period}\n"
        f"Entries: {len(entries)}\n"
        f"Quick logs: {len(quick_logs)}\n"
        "Snippets:\n"
        + "\n".join(snippet_lines[:12])
    )

    def _call_openai() -> str:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': user_text},
            ],
            temperature=0.2,
        )
        return (response.choices[0].message.content or '{}').strip()

    try:
        raw = await asyncio.to_thread(_call_openai)
        if raw.startswith('```json'):
            raw = raw[7:]
        if raw.startswith('```'):
            raw = raw[3:]
        if raw.endswith('```'):
            raw = raw[:-3]
        parsed = json.loads(raw.strip())
        return {
            'summary': str(parsed.get('summary') or '').strip(),
            'strength': str(parsed.get('strength') or '').strip() or None,
            'improvement': str(parsed.get('improvement') or '').strip() or None,
            'recommendation': str(parsed.get('recommendation') or '').strip() or None,
        }
    except Exception as exc:
        logger.warning(f'Journal AI insights failed, falling back to heuristic summary: {exc}')
        return None


@api_router.post('/ai/journal/search')
async def ai_journal_search(payload: JournalSearchRequest, current_user: dict = Depends(get_current_user)):
    query = payload.query.strip().lower()
    if not query:
        return {'results': [], 'summary': 'Enter a search term to find matching journal entries.'}

    journal_entries = await db.journal_entries.find({'user_id': current_user['id']}).sort('created_at', -1).to_list(200)
    quick_logs = await db.quick_logs.find({'user_id': current_user['id']}).sort('date', -1).to_list(100)

    results: List[Dict[str, Any]] = []
    for entry in journal_entries:
        if _journal_search_matches(entry, query):
            results.append({
                'id': entry['id'],
                'type': entry.get('entry_type', 'deep'),
                'text': _journal_entry_text(entry) or entry.get('content') or entry.get('title') or '',
                'date': entry.get('date') or _journal_entry_date_for(entry),
            })

    for log in quick_logs:
        haystack = " ".join([
            str(log.get('mood') or ''),
            str(log.get('energy') or ''),
            str(log.get('stress') or ''),
            str(log.get('note') or ''),
        ]).lower()
        if query in haystack:
            results.append({
                'id': log['id'],
                'type': 'quick_log',
                'text': f"Mood: {log.get('mood')}, Energy: {log.get('energy')}, Stress: {log.get('stress')}, Note: {log.get('note') or ''}".strip(),
                'date': log.get('date'),
            })

    results = sorted(results, key=lambda item: item.get('date') or '', reverse=True)[:max(1, min(payload.limit, 50))]
    summary = _journal_result_summary(results, query)
    return {'results': results, 'summary': summary}


@api_router.get('/ai/journal/insights')
async def ai_journal_insights(period: str = 'week', current_user: dict = Depends(get_current_user)):
    period_normalized = period if period in {'week', 'month'} else 'week'
    now = datetime.utcnow()
    days_back = 7 if period_normalized == 'week' else 30
    start_date = (now - timedelta(days=days_back)).strftime('%Y-%m-%d')
    journal_entries = await db.journal_entries.find({
        'user_id': current_user['id'],
        'date': {'$gte': start_date, '$lte': now.strftime('%Y-%m-%d')},
    }).sort('created_at', -1).to_list(200)
    quick_logs = await db.quick_logs.find({
        'user_id': current_user['id'],
        'date': {'$gte': start_date, '$lte': now.strftime('%Y-%m-%d')},
    }).sort('date', -1).to_list(100)

    ai_result = await _journal_ai_insights(period_normalized, journal_entries, quick_logs)
    if ai_result is None or not ai_result.get('summary'):
        ai_result = _journal_patterns(journal_entries, quick_logs)

    return {'insights': ai_result, 'period': period_normalized}


@api_router.post('/ai/coach/chat')
async def ai_coach_chat(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    message = str(payload.get('message') or '').strip()
    if not message:
        raise HTTPException(status_code=400, detail='message is required')

    insights_response = await ai_journal_insights(period='week', current_user=current_user)
    insights = insights_response.get('insights') if isinstance(insights_response, dict) else {}
    journal_entries = await db.journal_entries.find({'user_id': current_user['id']}).sort('created_at', -1).to_list(5)
    recent_snippets = [text for text in (_journal_entry_text(entry) for entry in journal_entries) if text][:3]

    lowered = message.lower()
    focus = 'consistency'
    if any(term in lowered for term in ('sleep', 'recover', 'recovery', 'rest')):
        focus = 'recovery'
    elif any(term in lowered for term in ('anxious', 'anxiety', 'stress', 'nervous', 'race')):
        focus = 'mindset'
    elif any(term in lowered for term in ('plan', 'week', 'training', 'workout')):
        focus = 'training'

    summary = str((insights or {}).get('summary') or '').strip()
    strength = str((insights or {}).get('strength') or '').strip()
    improvement = str((insights or {}).get('improvement') or '').strip()
    recommendation = str((insights or {}).get('recommendation') or '').strip()

    reply_parts = []
    if focus == 'recovery':
        reply_parts.append(recommendation or 'Keep recovery simple: protect sleep, reduce intensity for a day if needed, and choose one calming routine you can repeat.')
    elif focus == 'mindset':
        reply_parts.append('Treat nerves as useful energy. Narrow your attention to one controllable cue, one simple action, and one reminder that your preparation already counts.')
    elif focus == 'training':
        reply_parts.append(summary or 'Keep your training week balanced: one priority session, one supportive session, one recovery-focused day, and avoid stacking hard efforts without a clear reason.')
    else:
        reply_parts.append(summary or 'Progress usually comes from repeatable basics. Keep the next step small enough to execute even on a low-motivation day.')

    if strength:
        reply_parts.append(f"One strength I'm seeing: {strength}.")
    if improvement:
        reply_parts.append(f"Primary focus next: {improvement}.")
    if recent_snippets:
        reply_parts.append(f"Recent journal theme: {recent_snippets[0][:160]}.")

    return {'response': ' '.join(part for part in reply_parts if part).strip()}


@api_router.post('/mood')
async def create_mood(payload: MoodCreate, current_user: dict = Depends(get_current_user)):
    mood = MoodEntry(
        user_id=current_user['id'],
        mood_value=payload.mood_value,
        mood_emoji=payload.mood_emoji,
        note=payload.note,
        activities=payload.activities,
        trigger=payload.trigger,
        trigger_id=payload.trigger_id,
        date=datetime.utcnow().strftime('%Y-%m-%d'),
    )
    await db.moods.insert_one(mood.model_dump())
    return clean_doc(mood.model_dump())


@api_router.get('/mood')
async def get_moods(current_user: dict = Depends(get_current_user)):
    docs = await db.moods.find({'user_id': current_user['id']}).sort('timestamp', -1).to_list(200)
    return [clean_doc(d) for d in docs]


# -------------------- TERRA / RUN SOCIAL --------------------
# NOTE: run-club CRUD, run submission with H3 territory, run stats, and
# territory endpoints now live in backend.routers.{clubs,runs,territory}.
# The handlers for reflections, feed, leaderboards, training plans, and the
# vault stay below.


@api_router.get('/terra/reflections/{run_id}')
async def get_terra_reflection(run_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.terra_reflections.find_one({'user_id': current_user['id'], 'run_id': run_id})
    if not doc:
        raise HTTPException(status_code=404, detail='Reflection not found')
    return clean_doc(doc)


@api_router.post('/terra/reflections')
async def create_terra_reflection(payload: TerraReflectionCreate, current_user: dict = Depends(get_current_user)):
    run_doc = await db.terra_runs.find_one({'id': payload.run_id, 'user_id': current_user['id']})
    if not run_doc:
        run_doc = await db.runs.find_one({'id': payload.run_id, 'user_id': current_user['id']})
    if not run_doc:
        raise HTTPException(status_code=404, detail='Run not found')

    now = datetime.utcnow()
    reflection = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'run_id': payload.run_id,
        'feeling': payload.feeling.strip().lower(),
        'notes': payload.notes.strip() if payload.notes else None,
        'created_at': now,
        'updated_at': now,
    }

    existing = await db.terra_reflections.find_one({'user_id': current_user['id'], 'run_id': payload.run_id})
    if existing:
        reflection['id'] = existing['id']
        reflection['created_at'] = existing.get('created_at', now)
        await db.terra_reflections.update_one(
            {'id': existing['id'], 'user_id': current_user['id']},
            {'$set': reflection},
            upsert=True,
        )
    else:
        await db.terra_reflections.insert_one(reflection)
    return clean_doc(reflection)


@api_router.get('/terra/feed')
async def get_terra_feed(current_user: dict = Depends(get_current_user)):
    await _terra_ensure_seed_feed_posts()
    docs = await db.terra_feed_posts.find({}).sort('created_at', -1).to_list(200)
    return [_terra_feed_post_response(doc) for doc in docs]


@api_router.post('/terra/feed')
async def create_terra_feed_post(payload: TerraFeedCreate, current_user: dict = Depends(get_current_user)):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail='content is required')

    now = datetime.utcnow()
    run_payload = None
    if payload.run_id:
        run_doc = await db.terra_runs.find_one({'id': payload.run_id, 'user_id': current_user['id']})
        if not run_doc:
            run_doc = await db.runs.find_one({'id': payload.run_id, 'user_id': current_user['id']})
        if run_doc:
            run_payload = {
                'distance': _terra_run_distance_km(run_doc),
                'duration': _terra_run_duration_seconds(run_doc),
                'territory_captured': _terra_run_territory_km2(run_doc),
            }

    post = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'username': current_user.get('name') or current_user.get('email', 'Runner'),
        'content': content,
        'likes': [],
        'comments': [],
        'run': run_payload,
        'created_at': now,
        'updated_at': now,
    }
    await db.terra_feed_posts.insert_one(post)
    return _terra_feed_post_response(post)


@api_router.post('/terra/feed/{post_id}/like')
async def like_terra_feed_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = await db.terra_feed_posts.find_one({'id': post_id})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    likes = [str(user_id) for user_id in post.get('likes', []) if str(user_id).strip()]
    user_id = current_user['id']
    if user_id in likes:
        likes = [like for like in likes if like != user_id]
    else:
        likes.append(user_id)

    updated = {'likes': likes, 'updated_at': datetime.utcnow()}
    await db.terra_feed_posts.update_one({'id': post_id}, {'$set': updated})
    post.update(updated)
    return _terra_feed_post_response(post)


@api_router.post('/terra/feed/{post_id}/comments')
async def add_terra_feed_comment(post_id: str, payload: dict, current_user: dict = Depends(get_current_user)):
    content = str(payload.get('content', '')).strip()
    if not content:
        raise HTTPException(status_code=400, detail='content is required')

    post = await db.terra_feed_posts.find_one({'id': post_id})
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')

    comment = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'username': current_user.get('name') or current_user.get('email', 'Runner'),
        'content': content,
        'created_at': datetime.utcnow().isoformat(),
    }
    await db.terra_feed_posts.update_one(
        {'id': post_id},
        {'$push': {'comments': comment}, '$set': {'updated_at': datetime.utcnow()}},
    )
    post = await db.terra_feed_posts.find_one({'id': post_id})
    return _terra_feed_post_response(post)


@api_router.get('/terra/leaderboard/global')
async def terra_leaderboard_global(current_user: dict = Depends(get_current_user)):
    entries = await _terra_all_user_summaries(include_placeholders=True, current_user=current_user)
    entries = sorted(entries, key=lambda item: (item['xp'], item['total_distance'], item['total_territory']), reverse=True)
    return [
        {
            'rank': index + 1,
            'username': entry['username'],
            'xp': entry['xp'],
            'level': entry['level'],
            'total_territory': entry['total_territory'],
            'total_distance': entry['total_distance'],
            'is_me': entry.get('id') == current_user['id'],
        }
        for index, entry in enumerate(entries[:10])
    ]


@api_router.get('/terra/leaderboard/friends')
async def terra_leaderboard_friends(current_user: dict = Depends(get_current_user)):
    entries = await _terra_all_user_summaries(include_placeholders=False, current_user=current_user)
    if len(entries) < 5:
        placeholder_entries = await _terra_all_user_summaries(include_placeholders=True, current_user=current_user)
        entries.extend([entry for entry in placeholder_entries if entry['id'].startswith('placeholder-')])
    entries = sorted(entries, key=lambda item: (item['xp'], item['total_distance'], item['total_territory']), reverse=True)
    return [
        {
            'rank': index + 1,
            'username': entry['username'],
            'xp': entry['xp'],
            'level': entry['level'],
            'total_territory': entry['total_territory'],
            'total_distance': entry['total_distance'],
            'is_me': entry.get('id') == current_user['id'],
        }
        for index, entry in enumerate(entries[:10])
    ]


@api_router.get('/terra/competition/current')
async def terra_competition_current(current_user: dict = Depends(get_current_user)):
    return _terra_competition_current()


def _terra_plan_weeks(goal: str, fitness_level: str, override: Optional[int] = None) -> int:
    if override is not None and override > 0:
        return override

    goal_lower = goal.lower()
    if 'marathon' in goal_lower:
        weeks = 16
    elif 'half' in goal_lower:
        weeks = 10
    elif '10k' in goal_lower or '10 k' in goal_lower:
        weeks = 8
    elif '5k' in goal_lower or '5 k' in goal_lower:
        weeks = 6
    else:
        weeks = 8

    fitness_lower = fitness_level.lower()
    if fitness_lower == 'beginner':
        weeks += 2
    elif fitness_lower == 'advanced':
        weeks = max(4, weeks - 1)
    return max(4, weeks)


@api_router.get('/terra/training-plans')
async def get_terra_training_plans(current_user: dict = Depends(get_current_user)):
    docs = await db.terra_training_plans.find({'user_id': current_user['id']}).sort('created_at', -1).to_list(100)
    if docs:
        return [_terra_training_plan_response(doc) for doc in docs]
    return [_terra_training_plan_response(plan) for plan in _terra_placeholder_training_plans(current_user)]


@api_router.post('/terra/training-plans')
async def create_terra_training_plan(payload: TerraTrainingPlanCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.utcnow()
    plan = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'goal': payload.goal.strip(),
        'fitness_level': payload.fitness_level.strip().lower(),
        'total_weeks': _terra_plan_weeks(payload.goal, payload.fitness_level, payload.total_weeks),
        'current_week': max(1, _to_non_negative_int(payload.current_week, 1)),
        'completed_sessions': [str(session).strip() for session in payload.completed_sessions if str(session).strip()],
        'created_at': now,
        'updated_at': now,
    }
    await db.terra_training_plans.insert_one(plan)
    return _terra_training_plan_response(plan)


@api_router.get('/terra/vault')
async def terra_vault(current_user: dict = Depends(get_current_user)):
    stats = await _terra_stats_bundle(current_user)
    return _terra_vault_catalog(stats)


@api_router.get('/')
async def root():
    return {'status': 'ok'}


# ---------------------------------------------------------------------------
# Modular routers (new architecture). These supersede the legacy handlers
# that were previously inline in server.py.
# ---------------------------------------------------------------------------
from backend.routers.workouts import router as _workouts_router
from backend.routers.runs import router as _runs_router
from backend.routers.clubs import router as _clubs_router
from backend.routers.territory import router as _territory_router

api_router.include_router(_workouts_router)
api_router.include_router(_runs_router)
api_router.include_router(_clubs_router)
api_router.include_router(_territory_router)


@app.on_event('startup')
async def startup_territory_indexes() -> None:
    from backend.territory.claim import ensure_indexes
    await ensure_indexes(db)


app.include_router(api_router)
