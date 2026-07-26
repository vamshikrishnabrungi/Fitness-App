from fastapi import FastAPI, APIRouter, HTTPException, Depends, Body, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid
import os
import re
import logging
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import httpx
from backend.helpers import (
    clean_doc,
    _parse_iso_datetime,
    _normalize_tags,
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
    TERRITORY_MIN_KM,
    _terra_run_xp,
    _terra_run_response,
    _terra_run_history_runs,
    _terra_competition_current,
    _terra_vault_catalog,
    _terra_placeholder_training_plans,
    _terra_training_plan_response,
    _terra_plan_weeks,
)
from backend.db_setup import ensure_database_schema
from backend.ai_workout_service import generate_ai_training_program
from backend.knowledge_retrieval import build_workout_knowledge_context, compact_context_for_ai
from backend.level_progression import compute_user_level_assessment
from backend.macro_plan_service import ensure_user_macro_plan, summarize_macro_plan_for_ai
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
    SleepNoteCreate,
    SleepSessionCreate,
    MoodCreate,
    MoodEntry,
    InjuryLog,
    InjuryLogCreate,
    BenchmarkCreate,
    StrainSummary,
    RecoverySummary,
    BiologySummary,
    ProgramSummary,
    Lesson,
    TerraGpsPoint,
    TerraRunCreate,
    TerraReflectionCreate,
    TerraFeedCreate,
    TerraTrainingPlanCreate,
    RunClubCreate,
)
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# -------------------- CONFIG --------------------
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'sftc_database')
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required.")
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_DAYS = 30
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
MEAL_AI_MODEL = os.environ.get('MEAL_AI_MODEL', 'openai/gpt-4o-mini')
WORKOUT_AI_MODEL = os.environ.get('WORKOUT_AI_MODEL', 'claude-opus-4-8')
# Per-user rolling-24h cap on AI workout generations (cost guard). Set to 0 to disable.
WORKOUT_AI_DAILY_QUOTA = int(os.environ.get('WORKOUT_AI_DAILY_QUOTA', '25') or 25)
# Global kill-switch for AI workout generation (saves tokens/credits when paused).
WORKOUT_GENERATION_ENABLED = (os.environ.get('WORKOUT_GENERATION_ENABLED', 'true') or 'true').strip().lower() in {'1', 'true', 'yes', 'on'}
OPENROUTER_SITE_URL = os.environ.get('OPENROUTER_SITE_URL', 'http://localhost')
OPENROUTER_APP_NAME = os.environ.get('OPENROUTER_APP_NAME', 'Runlete')
# Email / OTP. When host + user + pass are all set, OTP codes are emailed;
# otherwise they fall back to the server log (dev).
SMTP_HOST = os.environ.get('SMTP_HOST') or ''
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465') or 465)
SMTP_SECURE = (os.environ.get('SMTP_SECURE', 'true') or 'true').strip().lower() in {'1', 'true', 'yes', 'on'}
SMTP_USER = os.environ.get('INFO_EMAIL_USER') or ''
SMTP_PASS = os.environ.get('INFO_EMAIL_PASS') or ''
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'Runlete')
# Serializes the brief IPv4-forcing during SMTP connects (see _send_otp_email_sync).
import threading as _threading
_smtp_lock = _threading.Lock()
# Resend (HTTPS email API) — preferred over SMTP because cloud hosts can't block
# port 443, and it handles deliverability. When RESEND_API_KEY is set it wins.
RESEND_API_KEY = os.environ.get('RESEND_API_KEY') or ''
# Sender. Use "onboarding@resend.dev" for a quick test to your own inbox before
# the domain verifies; switch to your verified address for real users.
RESEND_FROM = os.environ.get('RESEND_FROM') or (f'{SMTP_FROM_NAME} <{SMTP_USER}>' if SMTP_USER else 'onboarding@resend.dev')

# -------------------- APP --------------------
# Optional error monitoring. Inert unless SENTRY_DSN is set AND sentry-sdk is installed.
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1,
                        environment=os.environ.get('ENVIRONMENT', 'production'))
    except ImportError:
        logging.getLogger(__name__).warning('SENTRY_DSN set but sentry-sdk not installed; skipping.')

app = FastAPI(title='Runlete API', version='2.2.0')

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api_router = APIRouter(prefix='/api')

ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8081,exp://localhost:8081").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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


@app.on_event('startup')
async def startup_database() -> None:
    await ensure_database_schema(db)
    logger.info('MongoDB schema ready: %s', DB_NAME)
    # Pre-warm the exercise-embedding model in the background so the first workout
    # generation doesn't pay the one-time model download/load (tens of seconds).
    import threading
    from backend import embeddings as _embeddings
    if _embeddings.embeddings_enabled():
        threading.Thread(target=_embeddings.embeddings_available, daemon=True).start()
        logger.info('Embedding model pre-warm started in background')

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


def _user_country(user: Dict[str, Any]) -> str:
    profile = user.get('profile') or {}
    return str(profile.get('country') or '').strip()


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


async def _geo_leaderboard(field: str, period: str) -> List[Dict[str, Any]]:
    """Aggregate run distance by a geographic field ('city' or 'country') across all clubs, ranked."""
    clubs = await db.run_clubs.find({}).to_list(2000)
    groups: Dict[str, Dict[str, Any]] = {}
    for club in clubs:
        key = str(club.get(field) or '').strip()
        if not key:
            continue
        group = groups.setdefault(key.title(), {'members': set(), 'clubs': 0})
        group['clubs'] += 1
        for member_id in club.get('member_ids', []):
            group['members'].add(str(member_id))

    period_start = _run_period_start(period)
    rows = []
    for key, group in groups.items():
        users = await _run_club_member_docs(list(group['members']))
        total_distance = 0.0
        total_runs = 0
        active_members = 0
        for user in users:
            runs = [run for run in await _terra_user_run_docs(user['id']) if _run_in_period(run, period_start)]
            distance = sum(_terra_run_distance_km(run) for run in runs)
            total_distance += distance
            total_runs += len(runs)
            if distance > 0:
                active_members += 1
        rows.append({
            field: key,
            'total_distance': round(total_distance, 1),
            'clubs': group['clubs'],
            'members': len(group['members']),
            'active_members': active_members,
            'total_runs': total_runs,
        })
    rows.sort(key=lambda row: (row['total_distance'], row['active_members'], row['total_runs']), reverse=True)
    return [{**row, 'rank': index + 1} for index, row in enumerate(rows)]


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


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Gate operator-only routes.

    There is no admin UI by design — grant the flag directly, e.g.
        db.users.updateOne({email: 'you@example.com'}, {$set: {is_admin: true}})
    """
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail='Admin access required')
    return current_user


def user_response(user: dict) -> dict:
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user['name'],
        'profile': user.get('profile', {}),
        'is_admin': bool(user.get('is_admin', False)),
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


def _exercise_reference_for_name(
    name: str,
    knowledge_context: Optional[Dict[str, Any]],
    exercise_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    if not knowledge_context:
        return None
    ref = None
    if exercise_id:
        ref_by_id = knowledge_context.get('exercise_ref_by_id') or {}
        ref = ref_by_id.get(str(exercise_id).strip())
    if not ref:
        ref_by_name = knowledge_context.get('exercise_ref_by_name') or {}
        ref = ref_by_name.get(str(name).strip().lower())
    if not ref:
        return None
    return {
        'exercise_id': ref.get('id'),
        'exercise_name': ref.get('name'),
        'source_refs': ref.get('source_refs') or [],
        'library_enrichment': {
            'summary': ref.get('summary'),
            'coaching_cues': ref.get('coaching_cues') or [],
            'common_errors': ref.get('common_errors') or [],
            'substitutions': ref.get('substitutions') or [],
            'regressions': ref.get('regressions') or [],
            'progressions': ref.get('progressions') or [],
            'use_when': ref.get('use_when') or [],
            'avoid_when': ref.get('avoid_when') or [],
        },
    }


def _attach_exercise_refs_to_session(session: Dict[str, Any], knowledge_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not knowledge_context:
        return session
    enriched = dict(session)
    for section_name in ['warmup', 'main_work', 'cooldown']:
        items = []
        for item in enriched.get(section_name) or []:
            item_doc = dict(item)
            ref = _exercise_reference_for_name(
                str(item_doc.get('name') or ''),
                knowledge_context,
                item_doc.get('exercise_id'),
            )
            if ref:
                item_doc['knowledge_ref'] = {
                    'exercise_id': ref.get('exercise_id'),
                    'exercise_name': ref.get('exercise_name'),
                    'source_refs': ref.get('source_refs') or [],
                }
                item_doc['library_enrichment'] = ref.get('library_enrichment') or {}
            items.append(item_doc)
        enriched[section_name] = items
    return enriched


def _workout_section_exercises(session: Dict[str, Any]) -> List[WorkoutExercise]:
    exercises: List[WorkoutExercise] = []
    for section_name in ['warmup', 'main_work', 'cooldown']:
        for item in session.get(section_name) or []:
            coaching_notes = item.get('coaching_notes') or []
            substitutions = item.get('substitutions') or []
            notes_parts = []
            if item.get('purpose'):
                notes_parts.append(f"Purpose: {item['purpose']}")
            if item.get('load_guidance'):
                notes_parts.append(str(item['load_guidance']))
            if item.get('rpe'):
                notes_parts.append(f"RPE: {item['rpe']}")
            if item.get('tempo'):
                notes_parts.append(f"Tempo: {item['tempo']}")
            if coaching_notes:
                notes_parts.append(' '.join(str(note) for note in coaching_notes if str(note).strip()))
            if substitutions:
                notes_parts.append(f"Substitutions: {', '.join(str(sub) for sub in substitutions if str(sub).strip())}")
            exercises.append(WorkoutExercise(
                name=str(item.get('name') or 'Exercise'),
                exercise_id=(item.get('knowledge_ref') or {}).get('exercise_id'),
                source_refs=(item.get('knowledge_ref') or {}).get('source_refs') or [],
                purpose=item.get('purpose'),
                sets=item.get('sets'),
                reps=item.get('reps'),
                duration=item.get('duration'),
                rest=item.get('rest'),
                notes=' '.join(notes_parts).strip() or f"{section_name.replace('_', ' ').title()} block",
            ))
    return exercises


def _session_grounding_counts(session_doc: Dict[str, Any]) -> tuple[int, int]:
    """Count main_work exercises resolved to a library exercise_id (grounded) vs total."""
    total = grounded = 0
    for item in (session_doc.get('main_work') or []):
        total += 1
        if (item.get('knowledge_ref') or {}).get('exercise_id'):
            grounded += 1
    return grounded, total


def _program_grounding(workouts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fraction of main-work exercises that resolved to a real library exercise (grounded selection).
    A high rate means the AI selected from the vetted pool, so cues/media/source_refs resolve."""
    grounded = total = 0
    for workout in workouts:
        g, t = _session_grounding_counts(workout.get('session_plan') or {})
        grounded += g
        total += t
    return {
        'grounded_main_exercises': grounded,
        'total_main_exercises': total,
        'grounding_rate': round(grounded / total, 2) if total else None,
    }


def _score_program_rubric(
    workouts: List[Dict[str, Any]],
    profile: Dict[str, Any],
    knowledge_context: Optional[Dict[str, Any]],
    grounding: Dict[str, Any],
) -> Dict[str, Any]:
    """Deterministic S&C quality rubric scored on every program before it ships (0-100 per
    dimension + weighted overall). Cheap, consistent, no extra AI call. Flags low dimensions."""
    kc = knowledge_context or {}
    protocols = kc.get('training_protocols') or []
    has_injury = bool((profile.get('pain_areas') or []) or (profile.get('current_injuries') or []))
    phase = str(profile.get('season_phase') or '').lower()
    needs_testing = has_injury or any(term in phase for term in ('re_entry', 'return', 'recondition', 'rehab', 'bridge'))

    def sessions_of(section: str):
        for w in workouts:
            for ex in ((w.get('session_plan') or {}).get(section) or []):
                yield ex

    all_ex = [ex for s in ('warmup', 'main_work', 'cooldown') for ex in sessions_of(s)]
    main_ex = list(sessions_of('main_work'))

    # Full program text (rationale + prescriptions) for concept-level checks.
    text_parts: List[str] = []
    for w in workouts:
        ad = w.get('adaptation') or {}
        text_parts.append(str(ad.get('why_this_session') or ''))
        text_parts.append(str(w.get('description') or ''))
        text_parts.extend(str(x) for x in (ad.get('injury_modifications') or []))
    for ex in all_ex:
        text_parts.extend([str(ex.get('purpose') or ''), str(ex.get('load_guidance') or ''), str(ex.get('tempo') or '')])
        text_parts.extend(str(n) for n in (ex.get('coaching_notes') or []))
    program_text = " ".join(text_parts).lower()

    def pct(num: int, den: int) -> int:
        return round(100 * num / den) if den else 100

    # 1. Every exercise has (sets & reps) or a duration — catches the "3 x None" defect.
    complete = sum(1 for ex in all_ex if (ex.get('sets') and ex.get('reps')) or ex.get('duration'))
    d_complete = pct(complete, len(all_ex))
    # 2. Loaded (rep-based) main-work anchors to RPE or load guidance (not a bare guessed number).
    #    Pure holds (duration-based) are excluded. With real baselines, expect %/1RM-referenced loads.
    has_1rm = bool((kc.get('benchmarks') or {}).get('strength_1rm_kg'))
    loaded = [ex for ex in main_ex if ex.get('sets') and ex.get('reps')]

    def _load_anchored(ex: Dict[str, Any]) -> bool:
        lg = str(ex.get('load_guidance') or '').lower()
        if has_1rm:
            return bool(ex.get('rpe')) or any(t in lg for t in ('%', '1rm', 'rep max', 'rm '))
        return bool(ex.get('rpe') or ex.get('load_guidance'))

    anchored = sum(1 for ex in loaded if _load_anchored(ex))
    d_load = pct(anchored, len(loaded))
    # 3. Injury context -> injury_modifications present per session.
    if has_injury:
        with_mods = sum(1 for w in workouts if (w.get('adaptation') or {}).get('injury_modifications'))
        d_injury = pct(with_mods, len(workouts))
    else:
        d_injury = 100
    # 4. Rehab/return context -> objective monitoring/testing referenced somewhere.
    if needs_testing:
        terms = ('lsi', 'symmetry', 'visa', ' test', 'assess', 'monitor', 'pain', 'hop test', 'jump height', 'questionnaire')
        d_monitor = 100 if any(t in program_text for t in terms) else 40
    else:
        d_monitor = 100
    # 5. Grounding (from lever #3).
    d_ground = round((grounding.get('grounding_rate') or 0) * 100)
    # 6. Session structure: warmup + main + cooldown present.
    struct_ok = sum(
        1 for w in workouts
        if (w.get('session_plan') or {}).get('warmup') and (w.get('session_plan') or {}).get('main_work')
        and (w.get('session_plan') or {}).get('cooldown')
    )
    d_struct = pct(struct_ok, len(workouts))
    # 7. Protocol adherence (concept-level): did the program follow the retrieved protocols' METHOD
    #    (isometric/tempo/LSI/pain-free/etc.), not their exact exercise names — robust to correctly
    #    avoiding contraindicated recommended exercises (e.g. jumps for an injured knee).
    _CONCEPTS = {
        "isometric", "tempo", "eccentric", "slow", "hold", "pain-free", "lsi", "symmetry",
        "visa", "monitor", "rpe", "rir", "progression", "deload", "nordic", "landing",
        "neutral", "brace", "range", "single-leg", "unilateral", "gate",
    }
    concept_terms: set = set()
    for p in protocols:
        source = " ".join([
            *(str(r) for r in (p.get('key_rules') or [])),
            *(str(s.get('prescription') or '') for s in (p.get('stages') or [])),
            *(str(m) for m in (p.get('monitoring') or [])),
        ]).lower()
        concept_terms.update(term for term in _CONCEPTS if term in source)
    if concept_terms:
        hits = sum(1 for term in concept_terms if term in program_text)
        d_proto = pct(hits, len(concept_terms))
    else:
        d_proto = 100

    dims = {
        'exercise_completeness': d_complete,
        'load_anchoring': d_load,
        'injury_safety': d_injury,
        'monitoring_testing': d_monitor,
        'grounding': d_ground,
        'session_structure': d_struct,
        'protocol_adherence': d_proto,
    }
    weights = {
        'exercise_completeness': 0.20, 'load_anchoring': 0.15, 'injury_safety': 0.15,
        'monitoring_testing': 0.10, 'grounding': 0.15, 'session_structure': 0.10, 'protocol_adherence': 0.15,
    }
    overall = round(sum(dims[k] * weights[k] for k in dims))
    flags = [f"{k}={v}" for k, v in dims.items() if v < 70]
    return {'overall': overall, 'dimensions': dims, 'flags': flags}


def _next_scheduled_date_for_day(day_name: str, base: datetime, used_dates: set[str]) -> str:
    weekdays = {
        'monday': 0,
        'mon': 0,
        'tuesday': 1,
        'tue': 1,
        'wednesday': 2,
        'wed': 2,
        'thursday': 3,
        'thu': 3,
        'friday': 4,
        'fri': 4,
        'saturday': 5,
        'sat': 5,
        'sunday': 6,
        'sun': 6,
    }
    target = weekdays.get(str(day_name).strip().lower(), len(used_dates) % 7)
    days_ahead = (target - base.weekday()) % 7
    candidate = base + timedelta(days=days_ahead)
    while candidate.strftime('%Y-%m-%d') in used_dates:
        candidate += timedelta(days=7)
    scheduled = candidate.strftime('%Y-%m-%d')
    used_dates.add(scheduled)
    return scheduled


def _program_base_date(start_date: Optional[str], now: datetime) -> datetime:
    """Scheduling anchor: the chosen start date if it's today or later, otherwise today."""
    if start_date:
        try:
            parsed = datetime.strptime(start_date, '%Y-%m-%d')
            if parsed.date() >= now.date():
                return parsed
        except (ValueError, TypeError):
            pass
    return now


async def _create_ai_training_program(
    current_user: dict,
    profile: Dict[str, Any],
    start_date: Optional[str] = None,
) -> Dict[str, Any]:
    now = datetime.utcnow()
    base_date = _program_base_date(start_date or profile.get('start_date'), now)
    user_id = current_user['id']
    macro_plan = await ensure_user_macro_plan(db, user_id=user_id, profile=profile)
    profile_for_retrieval = {**profile, 'user_id': user_id}
    knowledge_context = await build_workout_knowledge_context(db, profile_for_retrieval)
    compact_knowledge_context = compact_context_for_ai(knowledge_context)
    compact_knowledge_context['macro_plan'] = summarize_macro_plan_for_ai(macro_plan)
    compact_knowledge_context['athlete_state'] = summarize_athlete_state_for_ai(
        await db.athlete_states.find_one({'user_id': user_id})
    )
    benchmarks_summary = summarize_benchmarks_for_ai(await get_latest_benchmarks(user_id))
    compact_knowledge_context['benchmarks'] = benchmarks_summary
    knowledge_context['benchmarks'] = benchmarks_summary
    workout_ai_max_weeks = int(os.environ.get('WORKOUT_AI_MAX_WEEKS', '1') or 1)
    workout_ai_max_attempts = int(os.environ.get('WORKOUT_AI_MAX_ATTEMPTS', '2') or 2)
    workout_ai_strict_library = os.environ.get('WORKOUT_AI_STRICT_LIBRARY_MATCHES', 'false').lower() in {'1', 'true', 'yes', 'on'}

    try:
        generation = await generate_ai_training_program(
            profile,
            knowledge_context=compact_knowledge_context,
            openrouter_key=OPENROUTER_API_KEY,
            anthropic_key=ANTHROPIC_API_KEY,
            model=WORKOUT_AI_MODEL,
            max_weeks=workout_ai_max_weeks,
            max_attempts=workout_ai_max_attempts,
            strict_library_matches=workout_ai_strict_library,
        )
    except Exception as exc:
        logger.warning('AI workout generation failed: %s', exc)
        raise HTTPException(status_code=503, detail='AI workout generation failed. Please try again.') from exc
    generated_program = generation['program']
    program_doc = generated_program.model_dump()
    knowledge_counts = knowledge_context.get('counts') or {}

    program = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'title': generated_program.title,
        'status': 'active',
        'source': f"ai_workout_generator_v1:{generation['source']}",
        'goal': generated_program.goal,
        'sports': generated_program.sports,
        'duration_weeks': generated_program.duration_weeks,
        'current_week': 1,
        'created_at': now,
        'updated_at': now,
        'profile_snapshot': profile,
        'macro_plan_id': macro_plan.get('id'),
        'macro_plan_template_id': macro_plan.get('template_id'),
        'generation': {
            'start_date': base_date.strftime('%Y-%m-%d'),
            'fallback_used': generation.get('fallback_used', False),
            'model': WORKOUT_AI_MODEL,
            'max_weeks': generation.get('max_weeks'),
            'max_attempts': generation.get('max_attempts'),
            'strict_library_matches': generation.get('strict_library_matches', False),
            'knowledge_context': {
                'source_scope': knowledge_context.get('source_scope'),
                'allowed_primary_exercises': knowledge_counts.get('allowed_primary_exercises'),
                'allowed_variations': knowledge_counts.get('allowed_variations'),
                'progression_paths': knowledge_counts.get('progression_paths'),
                'recent_training_history': knowledge_counts.get('recent_training_history'),
                'exercise_candidates': knowledge_counts.get('exercise_candidates', len(knowledge_context.get('exercise_candidates') or [])),
                'programming_rules': knowledge_counts.get('programming_rules', len(knowledge_context.get('programming_rules') or [])),
                'technical_models': knowledge_counts.get('technical_models'),
                'technical_errors': knowledge_counts.get('technical_errors'),
                'mobility_drills': knowledge_counts.get('mobility_drills'),
                'recovery_rules': knowledge_counts.get('recovery_rules'),
                'nutrition_principles': knowledge_counts.get('nutrition_principles'),
                'macro_plan_template': macro_plan.get('template_id'),
            },
            'athlete_analysis': generated_program.athlete_analysis,
            'nutrition_focus': generated_program.nutrition_focus,
            'recovery_focus': generated_program.recovery_focus,
            'safety_notes': generated_program.safety_notes,
            'assumptions': generated_program.assumptions,
        },
        'plan': program_doc,
    }

    await db.training_programs.update_many(
        {'user_id': user_id, 'status': 'active'},
        {'$set': {'status': 'archived', 'archived_at': now}},
    )
    await db.training_programs.insert_one(program)
    await db.workouts.delete_many({
        'user_id': user_id,
        'completed': {'$ne': True},
        'scheduled_date': {'$gte': now.strftime('%Y-%m-%d')},
    })

    blocks = []
    for block_plan in generated_program.blocks:
        block = {
            'id': str(uuid.uuid4()),
            'program_id': program['id'],
            'user_id': user_id,
            'name': block_plan.name,
            'week_start': block_plan.start_week,
            'week_end': block_plan.end_week,
            'emphasis': block_plan.emphasis,
            'created_at': now,
        }
        await db.program_blocks.insert_one(block)
        blocks.append(clean_doc(block))

    workouts = []
    used_dates: set[str] = set()
    week_one = generated_program.weeks[0] if generated_program.weeks else None
    for index, session in enumerate((week_one.workouts if week_one else []) or []):
        session_doc = _attach_exercise_refs_to_session(session.model_dump(), knowledge_context)
        # Anchor the program to the chosen start date: first session lands on it, rest follow the AI's day pattern.
        if index == 0:
            scheduled_date = base_date.strftime('%Y-%m-%d')
            used_dates.add(scheduled_date)
        else:
            scheduled_date = _next_scheduled_date_for_day(session.day, base_date, used_dates)
        injury_notes = session_doc.get('injury_modifications') or []
        sport_transfer = session_doc.get('sport_transfer') or []
        description_parts = [
            f"{generated_program.title} session.",
            str(session_doc.get('why_this_session') or '').strip(),
            f"Targets: {', '.join(session_doc.get('adaptation_targets') or [])}." if session_doc.get('adaptation_targets') else '',
            f"Sport transfer: {', '.join(sport_transfer)}." if sport_transfer else '',
            f"Safety: {' '.join(injury_notes)}" if injury_notes else '',
        ]
        workout = Workout(
            user_id=user_id,
            title=session.title,
            category=session.category,
            duration=session.duration_min,
            difficulty=str(profile.get('experience') or 'Intermediate').title(),
            equipment=profile.get('equipment') or [],
            exercises=_workout_section_exercises(session_doc),
            description=' '.join(part for part in description_parts if part).strip(),
            ai_generated=True,
            scheduled_date=scheduled_date,
        ).model_dump()
        workout.update({
            'program_id': program['id'],
            'block_id': blocks[0]['id'] if blocks else None,
            'week_number': 1,
            'session_number': index + 1,
            'source': program['source'],
            'intensity': session.intensity,
            'adaptation': {
                'goal': generated_program.goal,
                'sports': generated_program.sports,
                'targets': session.adaptation_targets,
                'sport_transfer': session.sport_transfer,
                'why_this_session': session.why_this_session,
                'injury_modifications': session.injury_modifications,
                'progression_rule': week_one.progression_rule if week_one else None,
                'week_theme': week_one.theme if week_one else None,
            },
            'session_plan': session_doc,
        })
        await db.workouts.insert_one(workout)
        workouts.append(clean_doc(workout))

    grounding = _program_grounding(workouts)
    quality_report = _score_program_rubric(workouts, profile, knowledge_context, grounding)
    await db.training_programs.update_one(
        {'id': program['id']},
        {'$set': {'generation.grounding': grounding, 'generation.quality_report': quality_report}},
    )
    logger.info("Program quality=%s grounding=%s flags=%s program=%s",
                quality_report['overall'], grounding['grounding_rate'], quality_report['flags'], program['id'])

    return {
        'program': clean_doc(program),
        'macro_plan': clean_doc(macro_plan),
        'blocks': blocks,
        'weekly_plan': workouts,
        'generation': {
            'source': generation['source'],
            'fallback_used': generation.get('fallback_used', False),
            'error': generation.get('error'),
        },
    }


def _build_previous_block_summary(program: Dict[str, Any], week_workouts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compact summary of a completed week, fed back to the AI so the next block progresses from it."""
    sessions = []
    for w in week_workouts:
        fb = w.get('user_feedback') or {}
        adaptation = w.get('adaptation') or {}
        main = [e.get('name') for e in (w.get('exercises') or []) if isinstance(e, dict) and e.get('name')][:6]
        sessions.append({
            'title': w.get('title'),
            'category': w.get('category'),
            'duration_min': w.get('duration'),
            'main_exercises': main,
            'completed': bool(w.get('completed')),
            'completion_percentage': fb.get('completion_percentage'),
            'rpe': fb.get('rpe') if fb.get('rpe') is not None else fb.get('intensity_rating'),
            'pain_score': fb.get('pain_score'),
            'sport_transfer': adaptation.get('sport_transfer') or [],
        })
    week_number = max((w.get('week_number') or 1) for w in week_workouts) if week_workouts else 1
    return {
        'program_title': program.get('title'),
        'goal': program.get('goal'),
        'completed_week_number': week_number,
        'sessions': sessions,
    }


async def _extend_ai_training_program(current_user: dict, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the NEXT week of the active program, progressing from the last completed week.

    Unlike _create_ai_training_program this does NOT archive or wipe anything: it appends a new
    week and advances the program / macro-plan week counters.
    """
    now = datetime.utcnow()
    user_id = current_user['id']
    program = await db.training_programs.find_one(
        {'user_id': user_id, 'status': 'active'}, sort=[('created_at', -1)]
    )
    if not program:
        raise HTTPException(status_code=404, detail='No active program to continue')

    existing_workouts = await db.workouts.find({'user_id': user_id, 'program_id': program['id']}).to_list(500)
    max_week = max((w.get('week_number') or 1) for w in existing_workouts) if existing_workouts else 1
    # current_week is the source of truth (advanced transactionally at the end); fall back to max.
    current_week = int(program.get('current_week') or max_week)
    next_week = current_week + 1
    week_workouts = [w for w in existing_workouts if (w.get('week_number') or 1) == current_week]
    previous_block_summary = _build_previous_block_summary(program, week_workouts)

    macro_plan = await ensure_user_macro_plan(db, user_id=user_id, profile=profile)
    profile_for_retrieval = {**profile, 'user_id': user_id}
    knowledge_context = await build_workout_knowledge_context(db, profile_for_retrieval)
    compact_knowledge_context = compact_context_for_ai(knowledge_context)
    compact_knowledge_context['macro_plan'] = summarize_macro_plan_for_ai(macro_plan)
    compact_knowledge_context['athlete_state'] = summarize_athlete_state_for_ai(
        await db.athlete_states.find_one({'user_id': user_id})
    )
    benchmarks_summary = summarize_benchmarks_for_ai(await get_latest_benchmarks(user_id))
    compact_knowledge_context['benchmarks'] = benchmarks_summary
    knowledge_context['benchmarks'] = benchmarks_summary

    workout_ai_max_attempts = int(os.environ.get('WORKOUT_AI_MAX_ATTEMPTS', '2') or 2)
    workout_ai_strict_library = os.environ.get('WORKOUT_AI_STRICT_LIBRARY_MATCHES', 'false').lower() in {'1', 'true', 'yes', 'on'}

    # Deload enforcement: force a deload week on a fixed cadence OR when athlete_state says to back off.
    state_doc = await db.athlete_states.find_one({'user_id': user_id}) or {}
    deload_every = int(os.environ.get('WORKOUT_AI_DELOAD_EVERY', '4') or 4)
    is_deload = (
        state_doc.get('progression_signal') in ('hold_or_deload', 'reduce_volume_or_difficulty')
        or (deload_every > 0 and next_week % deload_every == 0)
    )
    if is_deload:
        logger.info("Week %s is a DELOAD (signal=%s, cadence every %s) user=%s",
                    next_week, state_doc.get('progression_signal'), deload_every, user_id)

    try:
        generation = await generate_ai_training_program(
            profile,
            knowledge_context=compact_knowledge_context,
            openrouter_key=OPENROUTER_API_KEY,
            anthropic_key=ANTHROPIC_API_KEY,
            model=WORKOUT_AI_MODEL,
            max_weeks=1,
            max_attempts=workout_ai_max_attempts,
            strict_library_matches=workout_ai_strict_library,
            previous_block_summary=previous_block_summary,
            deload_week=is_deload,
        )
    except Exception as exc:
        logger.warning('AI next-block generation failed: %s', exc)
        raise HTTPException(status_code=503, detail='AI next-block generation failed. Please try again.') from exc

    generated_program = generation['program']
    new_week = generated_program.weeks[0] if generated_program.weeks else None
    if not new_week:
        raise HTTPException(status_code=503, detail='AI did not return a next week')

    blocks = await db.program_blocks.find(
        {'user_id': user_id, 'program_id': program['id']}
    ).sort('week_start', 1).to_list(50)

    def _block_for_week(week_num: int) -> Optional[Dict[str, Any]]:
        for b in blocks:
            if (b.get('week_start') or 1) <= week_num <= (b.get('week_end') or week_num):
                return b
        return blocks[-1] if blocks else None

    block = _block_for_week(next_week)
    # Clear any partial week left by a previously failed attempt so retries are idempotent.
    await db.workouts.delete_many({'user_id': user_id, 'program_id': program['id'], 'week_number': next_week})
    used_dates = {
        w.get('scheduled_date') for w in existing_workouts
        if w.get('scheduled_date') and (w.get('week_number') or 1) != next_week
    }
    workouts = []
    for index, session in enumerate(new_week.workouts or []):
        session_doc = _attach_exercise_refs_to_session(session.model_dump(), knowledge_context)
        scheduled_date = _next_scheduled_date_for_day(session.day, now, used_dates)
        injury_notes = session_doc.get('injury_modifications') or []
        sport_transfer = session_doc.get('sport_transfer') or []
        description_parts = [
            f"{generated_program.title} session.",
            str(session_doc.get('why_this_session') or '').strip(),
            f"Targets: {', '.join(session_doc.get('adaptation_targets') or [])}." if session_doc.get('adaptation_targets') else '',
            f"Sport transfer: {', '.join(sport_transfer)}." if sport_transfer else '',
            f"Safety: {' '.join(injury_notes)}" if injury_notes else '',
        ]
        workout = Workout(
            user_id=user_id,
            title=session.title,
            category=session.category,
            duration=session.duration_min,
            difficulty=str(profile.get('experience') or 'Intermediate').title(),
            equipment=profile.get('equipment') or [],
            exercises=_workout_section_exercises(session_doc),
            description=' '.join(part for part in description_parts if part).strip(),
            ai_generated=True,
            scheduled_date=scheduled_date,
        ).model_dump()
        workout.update({
            'program_id': program['id'],
            'block_id': block['id'] if block else None,
            'week_number': next_week,
            'session_number': index + 1,
            'source': program.get('source'),
            'intensity': session.intensity,
            'adaptation': {
                'goal': generated_program.goal,
                'sports': generated_program.sports,
                'targets': session.adaptation_targets,
                'sport_transfer': session.sport_transfer,
                'why_this_session': session.why_this_session,
                'injury_modifications': session.injury_modifications,
                'progression_rule': new_week.progression_rule,
                'week_theme': new_week.theme,
            },
            'session_plan': session_doc,
            'continuation_of_week': current_week,
            'is_deload_week': is_deload,
        })
        await db.workouts.insert_one(workout)
        workouts.append(clean_doc(workout))

    grounding = _program_grounding(workouts)
    quality_report = _score_program_rubric(workouts, profile, knowledge_context, grounding)
    logger.info("Next-block quality=%s grounding=%s flags=%s program=%s",
                quality_report['overall'], grounding['grounding_rate'], quality_report['flags'], program['id'])

    # Advance the macro-plan block based on which phase covers the new week.
    next_block = macro_plan.get('current_block') or 1
    active_phase = None
    for phase in macro_plan.get('phases') or []:
        if (phase.get('start_week') or 1) <= next_week <= (phase.get('end_week') or next_week):
            next_block = phase.get('block') or next_block
            active_phase = phase.get('phase')
            break

    await db.training_programs.update_one(
        {'id': program['id']},
        {'$set': {'current_week': next_week, 'current_block': next_block, 'updated_at': now}},
    )
    if macro_plan.get('id'):
        await db.macro_plans.update_one(
            {'id': macro_plan['id']},
            {'$set': {'current_week': next_week, 'current_block': next_block, 'updated_at': now}},
        )

    return {
        'program_id': program['id'],
        'week_number': next_week,
        'block_number': next_block,
        'phase': active_phase,
        'weekly_plan': workouts,
        'generation': {
            'source': generation['source'],
            'continuation': True,
            'from_week': current_week,
            'is_deload_week': is_deload,
            'grounding': grounding,
            'quality_report': quality_report,
        },
    }


async def _run_next_block_with_durability(current_user: dict, profile: Dict[str, Any], program_id: str, next_week: int) -> None:
    """Run continuation generation with a job record (observability) and a retry, always releasing the
    generation claim afterwards so a manual /workouts/generate-next can recover from a failure."""
    job_id = str(uuid.uuid4())
    await db.job_status.insert_one({
        'job_id': job_id,
        'user_id': current_user['id'],
        'kind': 'next_block',
        'program_id': program_id,
        'target_week': next_week,
        'status': 'processing',
        'created_at': datetime.utcnow(),
    })
    attempts = max(1, int(os.environ.get('WORKOUT_AI_CONTINUATION_ATTEMPTS', '2') or 2))
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            result = await _extend_ai_training_program(current_user, profile)
            await db.job_status.update_one(
                {'job_id': job_id},
                {'$set': {'status': 'completed', 'result_week': result.get('week_number')}},
            )
            await db.training_programs.update_one({'id': program_id}, {'$unset': {'generating_week': ''}})
            logger.info("Next-block generation completed user=%s week=%s", current_user['id'], result.get('week_number'))
            return
        except Exception as exc:
            last_error = exc
            logger.warning("Next-block generation attempt %s/%s failed: %s", attempt, attempts, exc)
    await db.job_status.update_one(
        {'job_id': job_id},
        {'$set': {'status': 'failed', 'error_message': str(last_error)[:400]}},
    )
    await db.training_programs.update_one({'id': program_id}, {'$unset': {'generating_week': ''}})


async def _maybe_generate_next_block(current_user: dict) -> None:
    """Auto-trigger after a workout completes: if the current week is fully completed and the next
    week does not exist yet, generate the next block. Failure-isolated (never breaks completion) and
    concurrency-safe via an atomic claim on the program (prevents double-generation)."""
    if not WORKOUT_GENERATION_ENABLED:
        return
    try:
        user_id = current_user['id']
        program = await db.training_programs.find_one(
            {'user_id': user_id, 'status': 'active'}, sort=[('created_at', -1)]
        )
        if not program:
            return
        workouts = await db.workouts.find({'user_id': user_id, 'program_id': program['id']}).to_list(500)
        if not workouts:
            return
        current_week = int(program.get('current_week') or max((w.get('week_number') or 1) for w in workouts))
        # Horizon comes from the macro plan length (program.duration_weeks is trimmed to 1 per generation).
        macro = await db.macro_plans.find_one({'id': program.get('macro_plan_id')}) or {}
        horizon = int(macro.get('duration_weeks') or 12)
        if current_week >= max(1, horizon):
            return
        week_workouts = [w for w in workouts if (w.get('week_number') or 1) == current_week]
        if not week_workouts or not all(w.get('completed') for w in week_workouts):
            return
        next_week = current_week + 1
        if any((w.get('week_number') or 1) == next_week for w in workouts):
            return  # next week already generated

        # Atomic claim: only the first caller for this target week proceeds (TOCTOU / double-gen guard).
        claim = await db.training_programs.update_one(
            {'id': program['id'], 'generating_week': {'$ne': next_week}},
            {'$set': {'generating_week': next_week}},
        )
        if claim.modified_count == 0:
            logger.info("Next-block for week=%s already claimed/in-progress; skipping", next_week)
            return

        profile_doc = await db.athlete_profiles.find_one({'user_id': user_id})
        profile = (profile_doc or {}).get('raw_profile') or current_user.get('profile') or {}
        logger.info("Auto-generating next block user=%s after completed week=%s", user_id, current_week)
        await _run_next_block_with_durability(current_user, profile, program['id'], next_week)
    except Exception as exc:
        logger.warning("Auto next-block trigger skipped/failed: %s", exc)




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
        'model': MEAL_AI_MODEL if source == 'ai' else None,
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





def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def _send_otp_email_sync(to_email: str, code: str) -> None:
    """Blocking SMTP send. Call via asyncio.to_thread so it never stalls the loop."""
    import smtplib
    from email.message import EmailMessage
    from email.utils import formataddr

    msg = EmailMessage()
    msg['Subject'] = 'Your Runlete verification code'
    msg['From'] = formataddr((SMTP_FROM_NAME, SMTP_USER))
    msg['To'] = to_email
    msg.set_content(
        f"Your Runlete verification code is {code}.\n\n"
        "It expires in 10 minutes. If you didn't request this, ignore this email."
    )
    msg.add_alternative(
        f"""<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:420px">
          <h2 style="margin:0 0 8px">Verify your email</h2>
          <p style="color:#555;margin:0 0 16px">Enter this code in Runlete:</p>
          <div style="font-size:34px;font-weight:800;letter-spacing:6px">{code}</div>
          <p style="color:#999;font-size:13px;margin-top:16px">Expires in 10 minutes.
          If you didn't request this, you can ignore this email.</p>
        </div>""",
        subtype='html',
    )
    # Force IPv4. Cloud hosts (Render) often have no IPv6 route, and
    # smtp.hostinger.com publishes an AAAA record, so a default connect picks
    # IPv6 and fails with [Errno 101] Network is unreachable. The getaddrinfo
    # override is global, so it's held under a lock (OTP sends are infrequent).
    import socket
    real_getaddrinfo = socket.getaddrinfo

    def _ipv4_first(host, port, *args, **kwargs):
        results = real_getaddrinfo(host, port, *args, **kwargs)
        return [r for r in results if r[0] == socket.AF_INET] or results

    with _smtp_lock:
        socket.getaddrinfo = _ipv4_first
        try:
            if SMTP_SECURE:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as server:
                    server.login(SMTP_USER, SMTP_PASS)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASS)
                    server.send_message(msg)
        finally:
            socket.getaddrinfo = real_getaddrinfo


def _otp_email_bodies(code: str) -> tuple:
    text = (
        f"Your Runlete verification code is {code}.\n\n"
        "It expires in 10 minutes. If you didn't request this, ignore this email."
    )
    html = (
        f'<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:420px">'
        f'<h2 style="margin:0 0 8px">Verify your email</h2>'
        f'<p style="color:#555;margin:0 0 16px">Enter this code in Runlete:</p>'
        f'<div style="font-size:34px;font-weight:800;letter-spacing:6px">{code}</div>'
        f'<p style="color:#999;font-size:13px;margin-top:16px">Expires in 10 minutes. '
        f"If you didn't request this, you can ignore this email.</p></div>"
    )
    return text, html


async def _send_otp_via_resend(to_email: str, code: str) -> None:
    """Send the OTP through Resend's HTTPS API (port 443 — unblockable by hosts)."""
    text, html = _otp_email_bodies(code)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            'https://api.resend.com/emails',
            headers={'Authorization': f'Bearer {RESEND_API_KEY}'},
            json={
                'from': RESEND_FROM,
                'to': [to_email],
                'subject': 'Your Runlete verification code',
                'text': text,
                'html': html,
            },
        )
        resp.raise_for_status()


async def create_and_store_otp(email: str) -> str:
    code = f"{uuid.uuid4().int % 1000000:06d}"
    await db.otps.insert_one({
        'email': email,
        'code': code,
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(minutes=10),
    })
    # Prefer Resend (HTTPS) → fall back to SMTP → last resort log the code (dev).
    if RESEND_API_KEY:
        try:
            await _send_otp_via_resend(email, code)
            logger.info("OTP emailed (Resend) to %s", email)
            return code
        except Exception as exc:
            detail = getattr(getattr(exc, 'response', None), 'text', '') or str(exc)
            logger.error("Resend send failed for %s: %s", email, detail[:300])
            # fall through to SMTP / log
    if _smtp_configured():
        try:
            await asyncio.to_thread(_send_otp_email_sync, email, code)
            logger.info("OTP emailed to %s", email)
        except Exception as exc:
            logger.error("Failed to email OTP to %s: %s", email, exc)
            logger.info("OTP for %s: %s (email failed, dev fallback)", email, code)
    else:
        logger.info("OTP for %s: %s (email not configured — dev fallback)", email, code)
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
    foods_identified = [str(food).strip() for food in (payload.foods_identified or []) if str(food).strip()]
    return {
        'name': payload.name or 'Meal',
        'foods_identified': foods_identified or ([payload.name] if payload.name else ['Meal']),
        'calories': _to_non_negative_int(payload.calories, 0),
        'protein': _to_non_negative_float(payload.protein, 0),
        'carbs': _to_non_negative_float(payload.carbs, 0),
        'fat': _to_non_negative_float(payload.fat, 0),
        'fiber': _to_non_negative_float(payload.fiber, 0),
        'status': payload.status or 'Logged',
        'portion_size': '1 serving',
        'confidence': 'ai-reviewed' if payload.ai_analyzed else 'manual',
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

    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail='No AI key configured (OPENROUTER_API_KEY)')

    content: Any = user_text
    if payload.image_base64:
        image_data = payload.image_base64
        if not image_data.startswith('data:'):
            image_data = f"data:image/jpeg;base64,{image_data}"
        content = [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": image_data}},
        ]

    request_body = {
        "model": MEAL_AI_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
        "temperature": 0.2,
        "max_tokens": 900,
        "usage": {"include": True},
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_APP_NAME,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=request_body,
        )
    if response.status_code >= 400:
        logger.warning("OpenRouter meal analysis failed status=%s body=%s", response.status_code, response.text[:800])
        raise HTTPException(status_code=503, detail='AI meal analysis failed. Please try again.')

    data = response.json()
    logger.info("OpenRouter meal analysis model=%s usage=%s", data.get("model"), data.get("usage"))
    raw = str(data["choices"][0]["message"]["content"]).strip()

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
@limiter.limit("5/minute")
async def request_otp(request: Request, payload: OtpRequest):
    await create_and_store_otp(payload.email)
    return {'status': 'otp_sent'}


@api_router.post('/auth/register')
@limiter.limit("5/minute")
async def register(request: Request, payload: UserCreate):
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
        'profile': profile,
        'created_at': datetime.utcnow()
    }
    await db.users.insert_one(user)
    token = create_access_token({'sub': user['id']})
    return {'access_token': token, 'token_type': 'bearer', 'user': user_response(user)}


@api_router.post('/auth/login')
@limiter.limit("10/minute")
async def login(request: Request, payload: UserLogin):
    user = await db.users.find_one({'email': payload.email})
    if not user or not verify_password(payload.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    token = create_access_token({'sub': user['id']})
    return {'access_token': token, 'token_type': 'bearer', 'user': user_response(user)}


@api_router.post('/auth/login-otp')
@limiter.limit("10/minute")
async def login_otp(request: Request, payload: OtpVerify):
    user = await db.users.find_one({'email': payload.email})
    if not user or not await verify_latest_otp(payload.email, payload.code):
        raise HTTPException(status_code=401, detail='Invalid email or code')
    token = create_access_token({'sub': user['id']})
    return {'access_token': token, 'token_type': 'bearer', 'user': user_response(user)}


@api_router.post('/auth/reset-password')
@limiter.limit("5/minute")
async def reset_password(request: Request, payload: PasswordReset):
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


def _current_day_streak(completed_dates: set[str]) -> int:
    """Consecutive-day streak ending today or yesterday, from a set of 'YYYY-MM-DD' strings."""
    if not completed_dates:
        return 0
    days = sorted((datetime.strptime(d, '%Y-%m-%d').date() for d in completed_dates), reverse=True)
    today = datetime.utcnow().date()
    if days[0] < today - timedelta(days=1):
        return 0  # last workout was before yesterday → streak broken
    streak = 1
    for prev, cur in zip(days, days[1:]):
        if cur == prev - timedelta(days=1):
            streak += 1
        else:
            break
    return streak


@api_router.get('/profile/stats')
async def profile_stats(current_user: dict = Depends(get_current_user)):
    """Real headline stats for the profile screen: completed workouts, day streak, total hours."""
    workouts = await db.workouts.find(
        {'user_id': current_user['id'], 'completed': True},
        {'duration_min': 1, 'completed_at': 1},
    ).to_list(2000)
    total_minutes = sum(int(w.get('duration_min') or 0) for w in workouts)
    dates = {str(w['completed_at'])[:10] for w in workouts if w.get('completed_at')}
    return {
        'workouts': len(workouts),
        'streak_days': _current_day_streak(dates),
        'hours': round(total_minutes / 60),
    }


@api_router.put('/auth/profile')
async def update_profile(update: UserUpdate, current_user: dict = Depends(get_current_user)):
    update_dict = {}
    if update.name:
        update_dict['name'] = update.name
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
        response.update(await _create_ai_training_program(current_user, profile_doc.get('raw_profile') or {}))
    return response


async def _generate_full_week_background(current_user: dict, profile: Dict[str, Any], start_date: Optional[str]) -> None:
    """Background: generate the athlete's first week after onboarding. Failure-isolated (never crashes the request)."""
    if not WORKOUT_GENERATION_ENABLED:
        return
    try:
        await _create_ai_training_program(current_user, profile, start_date=start_date)
    except Exception as exc:
        logger.warning('Background full-week generation failed user=%s: %s', current_user.get('id'), exc)


@api_router.post('/onboarding/complete')
async def complete_onboarding(payload: OnboardingComplete, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    profile = payload.profile
    if profile.onboarding_completed_at is None:
        profile.onboarding_completed_at = datetime.utcnow()
    profile_doc = await _upsert_athlete_profile(current_user, profile)
    response = {'athlete_profile': profile_doc, 'onboarding_completed': True}
    if payload.generate_program and WORKOUT_GENERATION_ENABLED:
        raw_profile = profile_doc.get('raw_profile') or {}
        start_date = raw_profile.get('start_date')
        # Generate the program in the background so onboarding returns immediately; the app polls for it.
        background_tasks.add_task(_generate_full_week_background, current_user, raw_profile, start_date)
        response['program_generating'] = True
    else:
        response['program_generating'] = False
        response['generation_paused'] = not WORKOUT_GENERATION_ENABLED
    return response


@api_router.get('/workouts/generation-status')
async def workout_generation_status(current_user: dict = Depends(get_current_user)):
    return {'paused': not WORKOUT_GENERATION_ENABLED}


# -------------------- KNOWLEDGE LIBRARY --------------------
# Operator diagnostics only. Browsing and editing the knowledge base is done
# with MongoDB Compass / mongosh, which does it better than a hand-rolled API.
@api_router.get('/library/summary')
async def library_summary(current_user: dict = Depends(require_admin)):
    collections = [
        'exercise_library',
        'primary_exercise_library',
        'exercise_variation_library',
        'exercise_progression_graph',
        'user_exercise_history',
        'user_level_assessments',
        'movement_patterns',
        'physical_qualities',
        'sport_profiles',
        'sport_roles',
        'sport_training_rules',
        'sport_teaching_progressions',
        'sport_skill_assessments',
        'sport_level_transition_rules',
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


# -------------------- MACRO PLAN --------------------
@api_router.get('/macro-plan/active')
async def get_active_macro_plan(current_user: dict = Depends(get_current_user)):
    macro_plan = await db.macro_plans.find_one(
        {'user_id': current_user['id'], 'status': 'active'},
        sort=[('created_at', -1)],
    )
    if not macro_plan:
        raise HTTPException(status_code=404, detail='No active macro plan found')
    athlete_state = await db.athlete_states.find_one({'user_id': current_user['id']})
    return {
        'macro_plan': clean_doc(macro_plan),
        'athlete_state': clean_doc(athlete_state) if athlete_state else None,
    }


@api_router.post('/macro-plan/generate')
async def generate_macro_plan(payload: Optional[Dict[str, Any]] = Body(default=None), current_user: dict = Depends(get_current_user)):
    if payload:
        profile = _profile_from_payload(payload, current_user)
        profile_doc = await _upsert_athlete_profile(current_user, profile)
        profile_payload = profile_doc.get('raw_profile') or {}
    else:
        profile_doc = await db.athlete_profiles.find_one({'user_id': current_user['id']})
        profile_payload = (profile_doc or {}).get('raw_profile') or current_user.get('profile') or {}
    macro_plan = await ensure_user_macro_plan(
        db,
        user_id=current_user['id'],
        profile=profile_payload,
        force_new=True,
    )
    athlete_state = await db.athlete_states.find_one({'user_id': current_user['id']})
    return {
        'macro_plan': clean_doc(macro_plan),
        'athlete_state': clean_doc(athlete_state) if athlete_state else None,
    }


# -------------------- WORKOUTS --------------------
async def _enforce_ai_generation_quota(user_id: str) -> None:
    """Rolling-24h per-user cap on expensive AI workout generations. Cost guard for prod."""
    if WORKOUT_AI_DAILY_QUOTA <= 0:
        return
    since = datetime.utcnow() - timedelta(days=1)
    used = await db.ai_generation_log.count_documents({'user_id': user_id, 'created_at': {'$gte': since}})
    if used >= WORKOUT_AI_DAILY_QUOTA:
        raise HTTPException(
            status_code=429,
            detail=f'Daily workout-generation limit reached ({WORKOUT_AI_DAILY_QUOTA}/day). Try again later.',
        )
    await db.ai_generation_log.insert_one({'user_id': user_id, 'created_at': datetime.utcnow()})


@api_router.post('/workouts/generate-weekly')
@limiter.limit("2/minute")
async def generate_weekly_plan(request: Request, payload: Optional[Dict[str, Any]] = Body(default=None), current_user: dict = Depends(get_current_user)):
    """Generate (or regenerate) the active program's first week synchronously.

    Previously this enqueued an ARQ job to a worker that is not run locally; generation now happens
    inline (matching /onboarding/complete) so the plan actually materializes."""
    if not WORKOUT_GENERATION_ENABLED:
        raise HTTPException(status_code=503, detail='Workout generation is paused.')
    await _enforce_ai_generation_quota(current_user['id'])
    profile = _profile_from_payload(payload, current_user)
    profile_doc = await _upsert_athlete_profile(current_user, profile)
    return await _create_ai_training_program(current_user, profile_doc.get('raw_profile') or {})


@api_router.post('/workouts/generate-next')
@limiter.limit("4/minute")
async def generate_next_block(request: Request, current_user: dict = Depends(get_current_user)):
    """Manually generate the next block for the active program, progressing from the last week.

    The same logic also runs automatically in the background when a week is fully completed."""
    if not WORKOUT_GENERATION_ENABLED:
        raise HTTPException(status_code=503, detail='Workout generation is paused.')
    await _enforce_ai_generation_quota(current_user['id'])
    profile_doc = await db.athlete_profiles.find_one({'user_id': current_user['id']})
    profile = (profile_doc or {}).get('raw_profile') or current_user.get('profile') or {}
    return await _extend_ai_training_program(current_user, profile)


@api_router.get('/workouts/generate-status/{job_id}')
async def get_generation_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job_status = await db.job_status.find_one({"job_id": job_id, "user_id": current_user["id"]})
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_status["job_id"],
        "status": job_status["status"],
        "result_program_id": job_status.get("result_program_id"),
        "error_message": job_status.get("error_message")
    }


@api_router.get('/programs/active')
async def active_program(current_user: dict = Depends(get_current_user)):
    program = await db.training_programs.find_one(
        {'user_id': current_user['id'], 'status': 'active'},
        sort=[('created_at', -1)],
    )
    if not program:
        raise HTTPException(status_code=404, detail='No active program found')
    workouts = await db.workouts.find({
        'user_id': current_user['id'],
        'program_id': program['id'],
    }).sort([('week_number', 1), ('session_number', 1)]).to_list(200)
    blocks = await db.program_blocks.find({
        'user_id': current_user['id'],
        'program_id': program['id'],
    }).sort('week_start', 1).to_list(20)
    return {
        'program': clean_doc(program),
        'blocks': [clean_doc(block) for block in blocks],
        'workouts': [clean_doc(workout) for workout in workouts],
    }


@api_router.get('/workouts')
async def list_workouts(current_user: dict = Depends(get_current_user)):
    docs = await db.workouts.find({'user_id': current_user['id']}).sort([('scheduled_date', 1), ('session_number', 1), ('created_at', -1)]).to_list(100)
    return [clean_doc(d) for d in docs]


def _train_section_for_workout(workout: Dict[str, Any], profile: Dict[str, Any]) -> str:
    category = str(workout.get('category') or '').lower()
    title = str(workout.get('title') or '').lower()
    targets = [str(item).lower() for item in ((workout.get('adaptation') or {}).get('targets') or [])]
    sports = [str(item).lower() for item in profile.get('sports') or []]
    is_runner = any(item in ['running', 'runner'] for item in sports) or 'runner' in title or 'run' in title
    if is_runner and any(term in title or term in ' '.join(targets) for term in ['speed', 'hamstring', 'glute', 'lower', 'calf', 'landing', 'mechanics']):
        return 'The Run Down'
    if category in ['power', 'conditioning'] or any(term in title for term in ['speed', 'jump', 'rotation', 'condition']):
        return 'Power'
    if category in ['mobility', 'recovery', 'flexibility'] or any(term in title for term in ['mobility', 'recovery', 'reset']):
        return 'Mobility'
    if any(sport in title for sport in sports) or sports:
        return 'Strength for Your Sport'
    return 'Lock in and Lift'


@api_router.get('/workouts/recommended')
async def recommended_workout_sections(current_user: dict = Depends(get_current_user)):
    profile = current_user.get('profile') or {}
    docs = await db.workouts.find({
        'user_id': current_user['id'],
        'completed': {'$ne': True},
    }).sort([('scheduled_date', 1), ('session_number', 1), ('created_at', -1)]).to_list(100)
    sections: Dict[str, Dict[str, Any]] = {}
    section_copy = {
        'The Run Down': 'Balanced sessions for runners to build endurance, strength, mechanics, and resilience.',
        'Power': 'Explosive work for speed, jumping, cutting, and repeatable athletic output.',
        'Strength for Your Sport': 'Strength and accessory sessions that support your selected sports.',
        'Mobility': 'Lower-intensity sessions to recover, restore range, and keep training consistent.',
        'Lock in and Lift': 'Focused strength sessions for durable muscle and performance.',
    }
    for workout in docs:
        section = _train_section_for_workout(workout, profile)
        if section not in sections:
            sections[section] = {
                'id': section.lower().replace(' ', '-'),
                'title': section,
                'description': section_copy.get(section, 'Recommended sessions for you.'),
                'workouts': [],
            }
        sections[section]['workouts'].append(clean_doc(workout))
    return list(sections.values())


@api_router.get('/workouts/today')
async def workout_today(current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().strftime('%Y-%m-%d')
    workout = await db.workouts.find_one({'user_id': current_user['id'], 'scheduled_date': today})
    if not workout:
        raise HTTPException(status_code=404, detail='No AI-generated workout scheduled for today')
    return clean_doc(workout)


async def _record_workout_exercise_history(current_user: dict, workout: Dict[str, Any], feedback: Optional[Dict[str, Any]] = None) -> None:
    now = datetime.utcnow()
    date_str = str(workout.get('completed_at') or now.strftime('%Y-%m-%d'))[:10]
    exercises = workout.get('exercises') or []
    if not exercises:
        return
    await db.user_exercise_history.delete_many({
        'user_id': current_user['id'],
        'workout_id': workout.get('id'),
    })
    intensity = None
    completion_percentage = None
    pain_score = None
    performed: Dict[str, Dict[str, Any]] = {}
    if feedback:
        intensity = feedback.get('rpe') if feedback.get('rpe') is not None else feedback.get('intensity_rating')
        completion_percentage = feedback.get('completion_percentage')
        pain_score = feedback.get('pain_score')
        for p in (feedback.get('performed_exercises') or []):
            if not isinstance(p, dict):
                continue
            if p.get('exercise_id'):
                performed[str(p['exercise_id'])] = p
            if p.get('name'):
                performed[re.sub(r'[^a-z0-9]+', ' ', str(p['name']).lower()).strip()] = p
    entries = []
    for exercise in exercises:
        if not isinstance(exercise, dict):
            continue
        # Prefer the athlete's actual logged load/reps (numeric) over the prescribed text, so
        # strength_trends is driven by real performance.
        perf = performed.get(str(exercise.get('exercise_id'))) or performed.get(
            re.sub(r'[^a-z0-9]+', ' ', str(exercise.get('name') or '').lower()).strip()
        )
        actual_load = perf.get('weight_kg') if perf else None
        actual_reps = perf.get('reps') if perf else None
        entries.append({
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'date': date_str,
            'workout_id': workout.get('id'),
            'program_id': workout.get('program_id'),
            'exercise_id': exercise.get('exercise_id'),
            'exercise_name': exercise.get('name'),
            'sets': exercise.get('sets'),
            'reps': actual_reps if actual_reps is not None else exercise.get('reps'),
            'duration': exercise.get('duration'),
            'load': actual_load if actual_load is not None else (exercise.get('load') or exercise.get('load_guidance')),
            'logged_load_kg': actual_load,
            'rpe': intensity,
            'pain_score': pain_score,
            'completion_percentage': completion_percentage,
            'completed': True,
            'source': workout.get('source') or 'workout_completion',
            'created_at': now,
        })
    if entries:
        await db.user_exercise_history.insert_many(entries)


def _parse_load_value(value: Any) -> Optional[float]:
    """Extract a numeric working load (kg/lb) from a history entry. Returns None for
    bodyweight / RPE-only / guidance-text loads so they don't pollute the trend."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).lower()
    if 'rpe' in text or '%' in text or 'bodyweight' in text:
        return None
    match = re.search(r'(\d+(?:\.\d+)?)', text)
    return float(match.group(1)) if match else None


def _reps_first_int(value: Any) -> Optional[int]:
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r'\d+', str(value or ''))
    return int(match.group()) if match else None


def _compute_strength_trends(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Per-exercise load (or volume fallback) progression from logged history.

    Groups by exercise, compares earliest vs latest data point over the window, and classifies
    each as progressing / plateau / regressing. Prefers actual load; falls back to sets*reps volume
    when numeric loads were not logged."""
    by_ex: Dict[str, Dict[str, Any]] = {}
    for h in history:
        key = h.get('exercise_id') or str(h.get('exercise_name') or '').strip().lower()
        if not key:
            continue
        load = _parse_load_value(h.get('load'))
        reps = _reps_first_int(h.get('reps'))
        sets = h.get('sets') if isinstance(h.get('sets'), (int, float)) else _reps_first_int(h.get('sets'))
        entry = by_ex.setdefault(key, {'name': h.get('exercise_name') or key, 'loads': [], 'volumes': []})
        if load is not None:
            entry['loads'].append((h.get('date'), load))
        if sets and reps:
            entry['volumes'].append((h.get('date'), float(sets) * float(reps) * float(load or 1)))

    trends: List[Dict[str, Any]] = []
    for data in by_ex.values():
        use_load = len(data['loads']) >= 2
        series = data['loads'] if use_load else (data['volumes'] if len(data['volumes']) >= 2 else [])
        if len(series) < 2:
            continue
        series = sorted(series, key=lambda point: point[0] or "")  # chronological, independent of caller order
        first, last = series[0][1], series[-1][1]
        if first <= 0:
            continue
        change = (last - first) / first
        direction = 'progressing' if change > 0.03 else 'regressing' if change < -0.03 else 'plateau'
        trends.append({
            'exercise': data['name'],
            'metric': 'load' if use_load else 'volume',
            'direction': direction,
            'from': round(first, 1),
            'to': round(last, 1),
            'change_pct': round(change * 100, 1),
            'data_points': len(series),
        })
    return sorted(trends, key=lambda t: -t['data_points'])[:8]


async def update_athlete_state(current_user: dict) -> Dict[str, Any]:
    """Recompute the rolling athlete_state from real training data (completion, RPE, pain, readiness).

    Called after workout completion/feedback so the next generation can progress from trends rather
    than guesswork. Failure-isolated: never raises into the completion flow."""
    try:
        user_id = current_user['id']
        now = datetime.utcnow()
        d28 = (now - timedelta(days=28)).strftime('%Y-%m-%d')
        d14 = (now - timedelta(days=14)).strftime('%Y-%m-%d')

        # Completion rate (28d): completed vs scheduled workouts.
        recent = await db.workouts.find({'user_id': user_id, 'scheduled_date': {'$gte': d28}}).to_list(500)
        scheduled = [w for w in recent if w.get('scheduled_date')]
        completed = [w for w in scheduled if w.get('completed')]
        completion_rate = round(len(completed) / len(scheduled), 2) if scheduled else None

        # Rolling RPE / pain (14d) from logged exercise history.
        hist = await db.user_exercise_history.find({'user_id': user_id, 'date': {'$gte': d14}}).to_list(1000)
        rpes = [float(h['rpe']) for h in hist if h.get('rpe') is not None]
        pains = [float(h['pain_score']) for h in hist if h.get('pain_score') is not None]
        avg_rpe = round(sum(rpes) / len(rpes), 1) if rpes else None
        avg_pain = round(sum(pains) / len(pains), 1) if pains else None

        # Pain trends from active injuries + recent soreness reports.
        active_injuries = await db.injury_logs.find({'user_id': user_id, 'is_active': True}).to_list(50)
        quick = await db.quick_logs.find({'user_id': user_id, 'date': {'$gte': d14}}).sort('date', -1).to_list(50)
        soreness: Dict[str, int] = {}
        for q in quick:
            for region in (q.get('soreness_regions') or []):
                key = str(region).lower()
                soreness[key] = soreness.get(key, 0) + 1
        pain_trends = [
            {'area': inj.get('body_area'), 'severity': inj.get('severity'),
             'pain_scale': inj.get('pain_scale'), 'trend': 'active_injury'}
            for inj in active_injuries
        ]
        for area, count in soreness.items():
            if not any(p.get('area') and area in str(p['area']).lower() for p in pain_trends):
                pain_trends.append({'area': area, 'severity': 'soreness', 'trend': f'reported {count}x/14d'})

        latest = quick[0] if quick else None
        readiness = {
            'energy': latest.get('energy') if latest else None,
            'stress': latest.get('stress') if latest else None,
            'sleep_quality': latest.get('sleep_quality') if latest else None,
            'fatigue_flag': bool(avg_rpe and avg_rpe >= 8.5) or bool(completion_rate is not None and completion_rate < 0.5),
        }

        # Per-exercise load/volume progression over a longer (56d) window.
        d56 = (now - timedelta(days=56)).strftime('%Y-%m-%d')
        long_hist = await db.user_exercise_history.find(
            {'user_id': user_id, 'date': {'$gte': d56}}
        ).sort('date', 1).to_list(2000)
        strength_trends = _compute_strength_trends(long_hist)

        # Progression signal the AI consumes to decide progress vs hold vs deload.
        if completion_rate is not None and completion_rate < 0.5:
            progression_signal = 'reduce_volume_or_difficulty'
        elif (avg_rpe is not None and avg_rpe >= 8.5) or (avg_pain is not None and avg_pain >= 5):
            progression_signal = 'hold_or_deload'
        elif avg_rpe is not None and avg_rpe <= 6 and (completion_rate is None or completion_rate >= 0.8):
            progression_signal = 'progress_load'
        else:
            progression_signal = 'progress_steady'

        update = {
            'completion_rate_28d': completion_rate,
            'sessions_completed_28d': len(completed),
            'average_rpe_14d': avg_rpe,
            'average_pain_14d': avg_pain,
            'pain_trends': pain_trends,
            'strength_trends': strength_trends,
            'readiness': readiness,
            'progression_signal': progression_signal,
            'updated_at': now,
        }
        await db.athlete_states.update_one({'user_id': user_id}, {'$set': update}, upsert=True)
        return update
    except Exception as exc:
        logger.warning("update_athlete_state failed for user=%s: %s", current_user.get('id'), exc)
        return {}


def summarize_athlete_state_for_ai(state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Compact athlete_state for the generation prompt."""
    if not state:
        return {}
    return {
        'completion_rate_28d': state.get('completion_rate_28d'),
        'sessions_completed_28d': state.get('sessions_completed_28d'),
        'average_rpe_14d': state.get('average_rpe_14d'),
        'average_pain_14d': state.get('average_pain_14d'),
        'pain_trends': (state.get('pain_trends') or [])[:6],
        'strength_trends': (state.get('strength_trends') or [])[:8],
        'readiness': state.get('readiness') or {},
        'progression_signal': state.get('progression_signal'),
    }


def _estimate_1rm(weight_kg: Any, reps: Any) -> Optional[float]:
    """Estimate a one-rep max from a submaximal set (Epley). Returns None for invalid input."""
    try:
        w = float(weight_kg)
        r = int(reps)
    except (TypeError, ValueError):
        return None
    if w <= 0 or r <= 0:
        return None
    if r == 1:
        return round(w, 1)
    return round(w * (1 + r / 30.0), 1)


async def get_latest_benchmarks(current_user_id: str) -> Dict[str, Any]:
    """Reduce a user's benchmark history to the most-recent value for each metric."""
    docs = await db.user_benchmarks.find({'user_id': current_user_id}).sort('date', -1).to_list(50)
    if not docs:
        return {}
    one_rm: Dict[str, float] = {}
    for doc in docs:  # newest first — keep the first (latest) est_1rm per lift
        for lift in doc.get('lifts') or []:
            key = str(lift.get('exercise') or '').strip().lower()
            if key and key not in one_rm and lift.get('est_1rm_kg') is not None:
                one_rm[key] = lift['est_1rm_kg']

    def latest(field: str, sub: Optional[str] = None):
        for doc in docs:
            value = (doc.get(field) or {}).get(sub) if sub else doc.get(field)
            if value is not None:
                return value
        return None

    return {
        'strength_1rm_kg': one_rm,
        'cmj_cm': latest('cmj_cm'),
        'broad_jump_cm': latest('broad_jump_cm'),
        'single_leg_hop_lsi_pct': latest('single_leg_hop', 'lsi_pct'),
        'visa_p': latest('visa_p'),
        'visa_a': latest('visa_a'),
        'measured_on': docs[0].get('date'),
    }


def summarize_benchmarks_for_ai(benchmarks: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Compact benchmarks for the generation prompt (drop empty metrics)."""
    if not benchmarks:
        return {}
    return {k: v for k, v in benchmarks.items() if v not in (None, {}, [])}


async def _create_level_assessment_for_user(current_user: dict) -> Dict[str, Any]:
    profile = current_user.get('profile') or {}
    profile_doc = await db.athlete_profiles.find_one({'user_id': current_user['id']})
    if profile_doc and profile_doc.get('raw_profile'):
        profile = profile_doc['raw_profile']
    return await compute_user_level_assessment(
        db,
        user_id=current_user['id'],
        profile=profile,
        persist=True,
    )


@api_router.post('/workouts/{workout_id}/complete')
async def complete_workout(workout_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    workout = await db.workouts.find_one({'id': workout_id, 'user_id': current_user['id']})
    if not workout:
        raise HTTPException(status_code=404, detail='Workout not found')
    if workout.get('completed'):
        return {'message': 'Workout completed', 'already_completed': True}

    completed_at = datetime.utcnow()
    await db.workouts.update_one(
        {'id': workout_id, 'user_id': current_user['id']},
        {'$set': {'completed': True, 'completed_at': completed_at}},
    )
    workout['completed'] = True
    workout['completed_at'] = completed_at
    await _record_workout_exercise_history(current_user, workout, workout.get('user_feedback'))
    await update_athlete_state(current_user)
    assessment = await _create_level_assessment_for_user(current_user)
    # Auto-generate the next block in the background once the current week is fully completed.
    background_tasks.add_task(_maybe_generate_next_block, current_user)
    return {'message': 'Workout completed', 'level_assessment': clean_doc(assessment)}


@api_router.post('/workouts/{workout_id}/feedback')
async def feedback_workout(workout_id: str, feedback: WorkoutFeedback, current_user: dict = Depends(get_current_user)):
    feedback_doc = feedback.model_dump()
    result = await db.workouts.update_one(
        {'id': workout_id, 'user_id': current_user['id']},
        {'$set': {'user_feedback': feedback_doc}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail='Workout not found')
    workout = await db.workouts.find_one({'id': workout_id, 'user_id': current_user['id']})
    if workout and workout.get('completed'):
        await _record_workout_exercise_history(current_user, workout, feedback_doc)
        await update_athlete_state(current_user)
        assessment = await _create_level_assessment_for_user(current_user)
        return {'message': 'Feedback saved', 'level_assessment': clean_doc(assessment)}
    return {'message': 'Feedback saved'}


@api_router.post('/athlete/benchmarks')
async def create_benchmark(payload: BenchmarkCreate, current_user: dict = Depends(get_current_user)):
    """Log a baseline testing session (rep-max lifts, jumps, hop symmetry, tendon questionnaires).

    Estimated 1RMs and limb-symmetry are computed server-side so generation can prescribe loads as a
    % of real capacity and gate progression on objective criteria instead of guessing."""
    now = datetime.utcnow()
    date_str = payload.date or now.strftime('%Y-%m-%d')
    lifts = [
        {
            'exercise': lift.exercise,
            'weight_kg': lift.weight_kg,
            'reps': lift.reps,
            'est_1rm_kg': _estimate_1rm(lift.weight_kg, lift.reps),
        }
        for lift in payload.lifts
    ]
    lsi_pct = None
    left, right = payload.single_leg_hop_left_cm, payload.single_leg_hop_right_cm
    if left and right and max(left, right) > 0:
        lsi_pct = round(100 * min(left, right) / max(left, right), 1)
    doc = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'date': date_str,
        'lifts': lifts,
        'cmj_cm': payload.cmj_cm,
        'broad_jump_cm': payload.broad_jump_cm,
        'single_leg_hop': {'left_cm': left, 'right_cm': right, 'lsi_pct': lsi_pct},
        'visa_p': payload.visa_p,
        'visa_a': payload.visa_a,
        'notes': payload.notes,
        'created_at': now,
    }
    await db.user_benchmarks.insert_one(doc)
    return {
        'message': 'Benchmark saved',
        'benchmark': clean_doc(doc),
        'summary': summarize_benchmarks_for_ai(await get_latest_benchmarks(current_user['id'])),
    }


@api_router.get('/athlete/benchmarks')
async def list_benchmarks(current_user: dict = Depends(get_current_user)):
    history = await db.user_benchmarks.find({'user_id': current_user['id']}).sort('date', -1).to_list(50)
    return {
        'latest': summarize_benchmarks_for_ai(await get_latest_benchmarks(current_user['id'])),
        'history': [clean_doc(doc) for doc in history],
    }


@api_router.get('/athlete/level-assessment')
async def get_user_level_assessment(refresh: bool = False, current_user: dict = Depends(get_current_user)):
    if not refresh:
        existing = await db.user_level_assessments.find_one(
            {'user_id': current_user['id']},
            sort=[('created_at', -1)],
        )
        if existing:
            return clean_doc(existing)
    return clean_doc(await _create_level_assessment_for_user(current_user))


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
    if docs:
        return [clean_doc(d) for d in docs]

    profile = current_user.get('profile') or {}
    user_sports = [
        str(sport).strip().lower()
        for sport in (profile.get('sports') or [])
        if str(sport).strip()
    ]
    user_level = str(profile.get('experience') or '').strip().lower()
    query: Dict[str, Any] = {}
    if user_sports:
        query['sport'] = {'$in': user_sports}
    if user_level in {'beginner', 'intermediate', 'advanced'}:
        query['level'] = user_level

    progressions = await db.sport_teaching_progressions.find(query).sort(
        [('sport', 1), ('level', 1), ('domain', 1)]
    ).to_list(120)

    if not progressions:
        fallback_query: Dict[str, Any] = {}
        if user_sports:
            fallback_query['sport'] = {'$in': user_sports}
        progressions = await db.sport_teaching_progressions.find(fallback_query).sort(
            [('sport', 1), ('level', 1), ('domain', 1)]
        ).to_list(120)

    level_rank = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
    if user_level in level_rank:
        progressions = sorted(
            progressions,
            key=lambda doc: (
                0 if str(doc.get('level') or '').lower() == user_level else 1,
                str(doc.get('sport') or ''),
                level_rank.get(str(doc.get('level') or '').lower(), 9),
                str(doc.get('domain') or ''),
            ),
        )
    else:
        progressions = sorted(
            progressions,
            key=lambda doc: (
                str(doc.get('sport') or ''),
                level_rank.get(str(doc.get('level') or '').lower(), 9),
                str(doc.get('domain') or ''),
            ),
        )

    def _lesson_domain_label(raw_domain: Any) -> str:
        label = str(raw_domain or 'fundamentals').replace('_', ' ').title()
        return (
            label
            .replace(' Snc', ' S&C')
            .replace(' Iq', ' IQ')
            .replace(' Mma', ' MMA')
        )

    lessons: List[Dict[str, Any]] = []
    for doc in progressions:
        sport = str(doc.get('sport') or 'sport').replace('_', ' ').title()
        domain = _lesson_domain_label(doc.get('domain'))
        level = str(doc.get('level') or 'all levels').replace('_', ' ').title()
        learning_goal = str(doc.get('learning_goal') or doc.get('summary') or '').strip()
        teaching_priorities = [
            str(item).strip()
            for item in (doc.get('teaching_priorities') or [])
            if str(item).strip()
        ]
        typical_drills = [
            str(item).strip()
            for item in (doc.get('typical_drills') or doc.get('practice_design') or [])
            if str(item).strip()
        ]
        tactical_focus = [
            str(item).strip()
            for item in (doc.get('tactical_focus') or [])
            if str(item).strip()
        ]

        base_description = learning_goal or ', '.join(teaching_priorities[:3]) or f'{sport} lesson progression.'
        lessons.append({
            'id': f"{doc.get('id') or uuid.uuid4()}_fundamentals",
            'sport': sport,
            'title': f"{domain}: {level} Foundation",
            'category': 'Fundamentals',
            'description': base_description,
            'difficulty': level,
            'duration': 10,
        })

        if typical_drills:
            lessons.append({
                'id': f"{doc.get('id') or uuid.uuid4()}_drills",
                'sport': sport,
                'title': f"{domain}: Practice Drills",
                'category': 'Drills',
                'description': ', '.join(typical_drills[:4]),
                'difficulty': level,
                'duration': 12,
            })

        if tactical_focus:
            lessons.append({
                'id': f"{doc.get('id') or uuid.uuid4()}_tactics",
                'sport': sport,
                'title': f"{domain}: Tactical Focus",
                'category': 'Tactics',
                'description': ', '.join(tactical_focus[:4]),
                'difficulty': level,
                'duration': 8,
            })

    return lessons[:200]


@api_router.get('/goals')
async def get_goals(current_user: dict = Depends(get_current_user)):
    docs = await db.goals.find({'user_id': current_user['id']}).to_list(50)
    return [clean_doc(d) for d in docs]


# -------------------- NUTRITION --------------------
@api_router.post('/meals/analyze')
async def analyze_meal(payload: MealCreate, save: bool = True, current_user: dict = Depends(get_current_user)):
    manual_only = payload.calories is not None
    ai_analyzed = False
    if manual_only:
        result = _manual_meal_result(payload)
        ai_analyzed = bool(payload.ai_analyzed)
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
@api_router.post('/terra/clubs')
async def create_run_club(payload: RunClubCreate, current_user: dict = Depends(get_current_user)):
    name = payload.name.strip()
    city = payload.city.strip()
    if not name:
        raise HTTPException(status_code=400, detail='Club name is required')
    if not city:
        raise HTTPException(status_code=400, detail='City is required')

    country = (payload.country or _user_country(current_user) or '').strip() or None
    emoji = (payload.emoji or '🏃').strip()[:4] or '🏃'
    now = datetime.utcnow()
    club = {
        'id': str(uuid.uuid4()),
        'name': name,
        'city': city,
        'country': country,
        'emoji': emoji,
        'description': payload.description.strip() if payload.description else None,
        'is_public': payload.is_public,
        'owner_id': current_user['id'],
        'member_ids': [current_user['id']],
        'created_at': now,
        'updated_at': now,
    }
    await db.run_clubs.insert_one(club)
    await db.run_club_memberships.insert_one({
        'club_id': club['id'],
        'user_id': current_user['id'],
        'role': 'owner',
        'status': 'active',
        'joined_at': now
    })
    await _emit_activity(current_user, 'club_created', club=club)
    return await _run_club_response(club, current_user)


@api_router.get('/terra/clubs/my')
async def my_run_clubs(current_user: dict = Depends(get_current_user)):
    docs = await db.run_clubs.find({'member_ids': current_user['id']}).sort('created_at', -1).to_list(100)
    return [await _run_club_response(doc, current_user) for doc in docs]


@api_router.post('/terra/clubs/{club_id}/join')
async def join_run_club(club_id: str, current_user: dict = Depends(get_current_user)):
    club = await db.run_clubs.find_one({'id': club_id})
    if not club:
        raise HTTPException(status_code=404, detail='Run club not found')
    if not club.get('is_public', True):
        # Private club: check if membership already exists
        existing_membership = await db.run_club_memberships.find_one({'club_id': club_id, 'user_id': current_user['id']})
        if existing_membership:
            raise HTTPException(status_code=400, detail='Membership already requested or active')
        
        await db.run_club_memberships.insert_one({
            'club_id': club_id,
            'user_id': current_user['id'],
            'role': 'member',
            'status': 'pending',
            'joined_at': datetime.utcnow()
        })
        return {"status": "pending_approval", "message": "Request to join sent to club admins."}
    
    # Public club
    member_ids = [str(member_id) for member_id in club.get('member_ids', [])]
    if current_user['id'] not in member_ids:
        member_ids.append(current_user['id'])
        await db.run_clubs.update_one(
            {'id': club_id},
            {'$set': {'member_ids': member_ids, 'updated_at': datetime.utcnow()}},
        )
        club['member_ids'] = member_ids
        
        await db.run_club_memberships.insert_one({
            'club_id': club_id,
            'user_id': current_user['id'],
            'role': 'member',
            'status': 'active',
            'joined_at': datetime.utcnow()
        })
        await _emit_activity(current_user, 'member_joined', club=club)
    return await _run_club_response(club, current_user)


@api_router.get('/terra/clubs/{club_id}/members')
async def get_run_club_members(club_id: str, current_user: dict = Depends(get_current_user)):
    club = await db.run_clubs.find_one({'id': club_id})
    if not club:
        raise HTTPException(status_code=404, detail='Run club not found')
        
    memberships = await db.run_club_memberships.find({'club_id': club_id, 'status': {'$ne': 'removed'}}).to_list(1000)
    user_ids = [m['user_id'] for m in memberships]
    users = await db.users.find({'id': {'$in': user_ids}}).to_list(1000)
    user_map = {u['id']: u for u in users}
    
    results = []
    for m in memberships:
        user_info = user_map.get(m['user_id'])
        if user_info:
            results.append({
                'user_id': m['user_id'],
                'name': user_info.get('name') or user_info.get('email', 'Runner'),
                'role': m.get('role', 'member'),
                'status': m.get('status', 'active'),
                'joined_at': m.get('joined_at')
            })
    return results


@api_router.put('/terra/clubs/{club_id}/members/{user_id}/approve')
async def approve_run_club_member(club_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    club = await db.run_clubs.find_one({'id': club_id})
    if not club:
        raise HTTPException(status_code=404, detail='Run club not found')
        
    admin_membership = await db.run_club_memberships.find_one({'club_id': club_id, 'user_id': current_user['id']})
    if not admin_membership or admin_membership.get('role') not in ('owner', 'admin'):
        raise HTTPException(status_code=403, detail='Must be a club admin to approve members')
        
    membership = await db.run_club_memberships.find_one({'club_id': club_id, 'user_id': user_id, 'status': 'pending'})
    if not membership:
        raise HTTPException(status_code=404, detail='Pending membership not found')
        
    await db.run_club_memberships.update_one(
        {'_id': membership['_id']},
        {'$set': {'status': 'active', 'joined_at': datetime.utcnow()}}
    )
    
    member_ids = club.get('member_ids', [])
    if user_id not in member_ids:
        member_ids.append(user_id)
        await db.run_clubs.update_one({'id': club_id}, {'$set': {'member_ids': member_ids}})
        
    return {"status": "approved", "user_id": user_id}


@api_router.delete('/terra/clubs/{club_id}/members/{user_id}')
async def remove_run_club_member(club_id: str, user_id: str, current_user: dict = Depends(get_current_user)):
    club = await db.run_clubs.find_one({'id': club_id})
    if not club:
        raise HTTPException(status_code=404, detail='Run club not found')
        
    if current_user['id'] != user_id:
        admin_membership = await db.run_club_memberships.find_one({'club_id': club_id, 'user_id': current_user['id']})
        if not admin_membership or admin_membership.get('role') not in ('owner', 'admin'):
            raise HTTPException(status_code=403, detail='Must be an admin to remove other members')
            
    await db.run_club_memberships.update_one(
        {'club_id': club_id, 'user_id': user_id},
        {'$set': {'status': 'removed'}}
    )
    
    member_ids = club.get('member_ids', [])
    if user_id in member_ids:
        member_ids.remove(user_id)
        await db.run_clubs.update_one({'id': club_id}, {'$set': {'member_ids': member_ids}})
        
    return {"status": "removed", "user_id": user_id}


@api_router.get('/terra/clubs/{club_id}/feed')
async def run_club_feed(club_id: str, limit: int = 20, current_user: dict = Depends(get_current_user)):
    club = await db.run_clubs.find_one({'id': club_id})
    if not club:
        raise HTTPException(status_code=404, detail='Run club not found')
        
    membership = await db.run_club_memberships.find_one({'club_id': club_id, 'user_id': current_user['id']})
    if (not membership or membership.get('status') != 'active') and not club.get('is_public', True):
        raise HTTPException(status_code=403, detail='Must be an active member to view the feed')
        
    member_ids = club.get('member_ids', [])
    if not member_ids:
        return []
    runs = await db.terra_runs.find({'user_id': {'$in': member_ids}}).sort('start_time', -1).limit(limit).to_list(limit)
    return [clean_doc(run) for run in runs]


@api_router.get('/terra/clubs/{club_id}/members/leaderboard')
async def run_club_member_leaderboard(club_id: str, period: str = 'week', current_user: dict = Depends(get_current_user)):
    club = await db.run_clubs.find_one({'id': club_id})
    if not club:
        raise HTTPException(status_code=404, detail='Run club not found')
    if current_user['id'] not in club.get('member_ids', []) and not club.get('is_public', True):
        raise HTTPException(status_code=403, detail='Not a club member')
    return await _run_club_member_leaderboard(club, period)


@api_router.get('/terra/clubs/leaderboard/city')
async def run_club_city_leaderboard(city: Optional[str] = None, period: str = 'week', current_user: dict = Depends(get_current_user)):
    city_name = (city or _user_city(current_user)).strip()
    docs = await db.run_clubs.find({'city': {'$regex': f'^{city_name}$', '$options': 'i'}}).to_list(200)
    rows = [await _run_club_response(doc, current_user, period) for doc in docs]
    rows.sort(key=lambda row: (row['total_distance'], row['active_members'], row['total_runs']), reverse=True)
    return [{**row, 'rank': index + 1} for index, row in enumerate(rows)]


async def _user_active_club_ids(user_id: str) -> List[str]:
    clubs = await db.run_clubs.find({'member_ids': user_id}, {'id': 1}).to_list(100)
    return [c['id'] for c in clubs]


async def _emit_activity(actor: dict, event_type: str, *, distance_km: float = 0.0,
                         territory_km2: float = 0.0, club: Optional[dict] = None,
                         target: Optional[str] = None) -> None:
    """Record a club activity event, visible to members of the actor's clubs. Failure-isolated."""
    try:
        club_ids = await _user_active_club_ids(actor['id'])
        if club and club.get('id') and club['id'] not in club_ids:
            club_ids = club_ids + [club['id']]
        await db.club_activity_events.insert_one({
            'id': str(uuid.uuid4()),
            'type': event_type,
            'user_id': actor['id'],
            'actor_name': actor.get('name') or (actor.get('email') or 'Runner').split('@')[0],
            'club_ids': club_ids,
            'club_id': club.get('id') if club else None,
            'club_name': club.get('name') if club else None,
            'club_emoji': club.get('emoji') if club else None,
            'target': target,
            'distance_km': round(float(distance_km or 0), 2),
            'territory_km2': round(float(territory_km2 or 0), 4),
            'created_at': datetime.utcnow(),
        })
    except Exception as exc:
        logger.warning('emit_activity failed: %s', exc)


@api_router.get('/terra/activity')
async def club_activity_feed(limit: int = 40, current_user: dict = Depends(get_current_user)):
    """Auto-generated activity from the user's clubs (runs, joins, new clubs)."""
    my_clubs = await _user_active_club_ids(current_user['id'])
    conditions: List[Dict[str, Any]] = [{'user_id': current_user['id']}]
    if my_clubs:
        conditions.append({'club_ids': {'$in': my_clubs}})
    events = await db.club_activity_events.find({'$or': conditions}).sort('created_at', -1).limit(limit).to_list(limit)
    return [{
        'id': e['id'],
        'type': e['type'],
        'actor_name': e.get('actor_name') or 'Runner',
        'is_me': e.get('user_id') == current_user['id'],
        'club_name': e.get('club_name'),
        'club_emoji': e.get('club_emoji'),
        'target': e.get('target'),
        'distance_km': e.get('distance_km', 0),
        'territory_km2': e.get('territory_km2', 0),
        'created_at': e['created_at'].isoformat() if e.get('created_at') else None,
    } for e in events]


# -------------------- TERRITORY (the game) --------------------
@api_router.get('/territory/mine')
async def my_territory(current_user: dict = Depends(get_current_user)):
    """Roads this user has claimed: every run that reached TERRITORY_MIN_KM,
    returned as its actual GPS path for drawing on the map."""
    runs = await _terra_user_run_docs(current_user['id'])
    roads: List[dict] = []
    total_km = 0.0
    for r in runs:
        dist = _terra_run_distance_km(r)
        if dist < TERRITORY_MIN_KM:
            continue
        coords = [
            [p['latitude'], p['longitude']]
            for p in (r.get('gps_path') or [])
            if isinstance(p, dict) and p.get('latitude') is not None and p.get('longitude') is not None
        ]
        if len(coords) < 2:
            continue
        total_km += dist
        created = r.get('created_at')
        roads.append({
            'id': str(r.get('id')),
            'path': coords,
            'distance_km': round(dist, 2),
            'date': r.get('date') or (created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else None),
        })
    return {
        'claimed_km': round(total_km, 2),
        'road_count': len(roads),
        'threshold_km': TERRITORY_MIN_KM,
        'roads': roads,
    }


@api_router.get('/terra/clubs/cities')
async def run_club_cities(current_user: dict = Depends(get_current_user)):
    """Distinct cities that have clubs (with counts) — powers the city picker."""
    clubs = await db.run_clubs.find({}, {'city': 1, 'country': 1}).to_list(2000)
    by_city: Dict[str, Dict[str, Any]] = {}
    for club in clubs:
        city = str(club.get('city') or '').strip()
        if not city:
            continue
        key = city.title()
        entry = by_city.setdefault(key, {'city': key, 'country': (str(club.get('country') or '').strip().title() or None), 'club_count': 0})
        entry['club_count'] += 1
    return sorted(by_city.values(), key=lambda item: (-item['club_count'], item['city']))


@api_router.get('/terra/leaderboard/cities')
async def city_vs_city_leaderboard(period: str = 'week', current_user: dict = Depends(get_current_user)):
    """City vs city: total distance aggregated across every club in each city, ranked."""
    return await _geo_leaderboard('city', period)


@api_router.get('/terra/leaderboard/countries')
async def country_vs_country_leaderboard(period: str = 'week', current_user: dict = Depends(get_current_user)):
    """Country vs country: total distance aggregated across every club in each country, ranked."""
    return await _geo_leaderboard('country', period)


@api_router.get('/terra/stats')
async def terra_stats(current_user: dict = Depends(get_current_user)):
    return await _terra_stats_bundle(current_user)


@api_router.get('/runs/stats')
async def run_stats(current_user: dict = Depends(get_current_user)):
    bundle = await _terra_stats_bundle(current_user)
    return {
        'total_distance': bundle['total_distance'],
        'average_pace': bundle['average_pace'],
        'fatigue': bundle['fatigue'],
        'consistency': bundle['consistency'],
        'history': bundle['history'],
    }


@api_router.get('/terra/runs')
async def terra_runs(current_user: dict = Depends(get_current_user)):
    docs = await _terra_user_run_docs(current_user['id'])
    return [_terra_run_response(doc) for doc in docs]


@api_router.post('/terra/runs')
async def create_terra_run(payload: TerraRunCreate, current_user: dict = Depends(get_current_user)):
    # payload.gps_path is a list of TerraGpsPoint models; normalize expects dicts.
    path = _terra_normalize_path([pt.model_dump() for pt in payload.gps_path])
    now = datetime.utcnow()
    start_dt = _parse_iso_datetime(payload.start_time)
    end_dt = _parse_iso_datetime(payload.end_time)

    duration_seconds = 0
    if start_dt and end_dt:
        duration_seconds = max(1, int(round((end_dt - start_dt).total_seconds())))
    elif path and len(path) > 1:
        first_ts = _parse_iso_datetime(path[0].get('timestamp'))
        last_ts = _parse_iso_datetime(path[-1].get('timestamp'))
        if first_ts and last_ts and last_ts > first_ts:
            duration_seconds = max(1, int(round((last_ts - first_ts).total_seconds())))

    if duration_seconds <= 0 and start_dt and not end_dt:
        duration_seconds = max(1, int(round((now - start_dt).total_seconds())))

    # Distance is exactly what the GPS trace covered — never fabricated. A
    # stationary "run" is 0 km, not an invented minimum.
    distance_km = 0.0
    for index in range(1, len(path)):
        distance_km += _terra_haversine_km(path[index - 1], path[index])
    distance_km = round(distance_km, 3)

    is_loop = False
    if len(path) >= 4:
        is_loop = _terra_haversine_km(path[0], path[-1]) <= 0.1

    # Territory is the actual road you ran, claimed once the run reaches the
    # threshold. No bounding boxes: below 2.5 km the run still counts toward
    # distance and leaderboards but claims nothing.
    claimed = distance_km >= TERRITORY_MIN_KM
    territory_captured = round(distance_km, 4) if claimed else 0.0

    run_doc = {
        'id': str(uuid.uuid4()),
        'user_id': current_user['id'],
        'gps_path': path,
        'start_time': payload.start_time,
        'end_time': payload.end_time,
        'date': (start_dt or end_dt or now).strftime('%Y-%m-%d'),
        'distance': distance_km,
        'distance_km': distance_km,
        'duration': duration_seconds,
        'duration_sec': duration_seconds,
        'territory_captured': territory_captured,
        'territory_km2': territory_captured,
        'claimed_territory': claimed,
        'is_loop': is_loop,
        'created_at': now,
        'updated_at': now,
    }
    await db.terra_runs.insert_one(run_doc)
    await _emit_activity(current_user, 'run_completed', distance_km=distance_km, territory_km2=territory_captured)
    resp = _terra_run_response(run_doc)
    resp['territory'] = {
        'claimed': claimed,
        'road_km': territory_captured,
        'threshold_km': TERRITORY_MIN_KM,
    }
    return resp


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


app.include_router(api_router)
