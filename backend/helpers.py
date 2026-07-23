from datetime import datetime, timedelta
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Dict, List, Optional
import re


def clean_doc(doc: dict) -> dict:
    if doc and '_id' in doc:
        del doc['_id']
    return doc


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    value_str = str(value).strip()
    if value_str.endswith('Z'):
        value_str = value_str[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(value_str)
    except ValueError:
        return None


def _normalize_tags(tags: Any) -> List[str]:
    if not isinstance(tags, list):
        return []
    normalized = []
    for tag in tags:
        tag_str = str(tag).strip().lower()
        if tag_str and tag_str not in normalized:
            normalized.append(tag_str)
    return normalized


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_non_negative_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(round(float(value))))
    except (TypeError, ValueError):
        return default


def _to_non_negative_float(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, round(float(value), 1))
    except (TypeError, ValueError):
        return default


def _sleep_quality_label(score: Optional[float]) -> str:
    if score is None:
        return 'unknown'
    if score >= 85:
        return 'excellent'
    if score >= 70:
        return 'good'
    if score >= 55:
        return 'fair'
    return 'poor'


def _sleep_status_from_score(score: Optional[float]) -> str:
    if score is None:
        return 'moderate'
    if score < 40:
        return 'low'
    if score < 70:
        return 'moderate'
    return 'high'


def _sleep_efficiency_value(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        efficiency = float(value)
    except (TypeError, ValueError):
        return None
    if efficiency > 1.5:
        efficiency = efficiency / 100.0
    return max(0.0, min(1.0, efficiency))


def _sleep_session_duration_hours(session: Dict[str, Any]) -> float:
    start = _parse_iso_datetime(session.get('start_time'))
    end = _parse_iso_datetime(session.get('end_time'))
    if start and end and end >= start:
        return round((end - start).total_seconds() / 3600.0, 2)
    return _to_non_negative_float(session.get('duration_hours'), 0.0)


def _sleep_session_metrics(session: Dict[str, Any]) -> Dict[str, Any]:
    duration_hours = _sleep_session_duration_hours(session)
    deep_sleep_hours = _to_non_negative_float(session.get('deep_sleep_hours'), 0.0)
    rem_sleep_hours = _to_non_negative_float(session.get('rem_sleep_hours'), 0.0)
    efficiency = _sleep_efficiency_value(session.get('efficiency'))
    if efficiency is None and duration_hours > 0:
        efficiency = min(1.0, duration_hours / 8.0)

    sleep_quality = session.get('sleep_quality')
    try:
        sleep_quality_int = int(sleep_quality) if sleep_quality is not None else None
    except (TypeError, ValueError):
        sleep_quality_int = None

    duration_component = min(40.0, (duration_hours / 8.0) * 40.0) if duration_hours > 0 else 0.0
    efficiency_component = (efficiency * 30.0) if efficiency is not None else (15.0 if duration_hours > 0 else 0.0)
    stage_ratio = 0.0
    if duration_hours > 0:
        stage_ratio = min(1.0, (deep_sleep_hours + rem_sleep_hours) / max(duration_hours, 0.1))
    stage_component = stage_ratio * 20.0
    quality_component = (sleep_quality_int * 10.0) if sleep_quality_int is not None else 0.0

    score = round(min(100.0, duration_component + efficiency_component + stage_component + quality_component))
    sleep_debt_hours = round(max(0.0, 8.0 - duration_hours), 1) if duration_hours > 0 else 0.0

    timestamp = _parse_iso_datetime(session.get('created_at')) or _parse_iso_datetime(session.get('start_time'))
    date_value = str(session.get('date') or (timestamp.strftime('%Y-%m-%d') if timestamp else datetime.utcnow().strftime('%Y-%m-%d')))

    return {
        'date': date_value,
        'duration_hours': duration_hours,
        'deep_sleep_hours': deep_sleep_hours,
        'rem_sleep_hours': rem_sleep_hours,
        'efficiency': efficiency,
        'sleep_score': score,
        'sleep_quality': sleep_quality_int,
        'sleep_quality_label': _sleep_quality_label(score),
        'status': _sleep_status_from_score(score),
        'sleep_debt_hours': sleep_debt_hours,
        'deep_ratio': round((deep_sleep_hours / duration_hours), 2) if duration_hours > 0 else 0.0,
        'rem_ratio': round((rem_sleep_hours / duration_hours), 2) if duration_hours > 0 else 0.0,
    }


def _sleep_session_response(session: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = clean_doc(dict(session))
    cleaned.update(_sleep_session_metrics(cleaned))
    cleaned.setdefault('quality_label', cleaned.get('sleep_quality_label', 'unknown'))
    return cleaned


def _terra_level_from_xp(xp: float) -> int:
    if xp <= 0:
        return 1
    return max(1, int((xp / 100.0) ** 0.5) + 1)


def _terra_referral_code(user: dict) -> str:
    user_id = str(user.get('id') or 'terra').replace('-', '')
    suffix = user_id[-6:].upper().rjust(6, '0')
    return f'TERRA-{suffix}'


def _terra_haversine_km(start: Dict[str, Any], end: Dict[str, Any]) -> float:
    lat1 = radians(float(start['latitude']))
    lon1 = radians(float(start['longitude']))
    lat2 = radians(float(end['latitude']))
    lon2 = radians(float(end['longitude']))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(max(0.0, 1 - a)))
    return 6371.0 * c


def _terra_normalize_path(path: Any) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    if not isinstance(path, list):
        return normalized

    for point in path:
        if not isinstance(point, dict):
            continue
        latitude = _optional_float(point.get('latitude'))
        longitude = _optional_float(point.get('longitude'))
        if latitude is None or longitude is None:
            continue

        timestamp = point.get('timestamp')
        parsed_timestamp = _parse_iso_datetime(timestamp)
        normalized.append({
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': parsed_timestamp.isoformat() if parsed_timestamp else (str(timestamp) if timestamp is not None else None),
            'altitude': _optional_float(point.get('altitude')),
            'speed': _optional_float(point.get('speed')),
        })
    return normalized


def _terra_run_distance_km(run: Dict[str, Any]) -> float:
    if run.get('distance') is not None:
        return _to_non_negative_float(run.get('distance'), 0.0)
    if run.get('distance_km') is not None:
        return _to_non_negative_float(run.get('distance_km'), 0.0)
    return 0.0


def _terra_run_duration_seconds(run: Dict[str, Any]) -> int:
    if run.get('duration') is not None:
        return _to_non_negative_int(run.get('duration'), 0)
    if run.get('duration_sec') is not None:
        return _to_non_negative_int(run.get('duration_sec'), 0)
    return 0


# A run claims territory only once it covers at least this distance. Below it the
# run still counts toward distance and leaderboards, but claims no roads.
TERRITORY_MIN_KM = 2.5


def _terra_run_territory_km2(run: Dict[str, Any]) -> float:
    """Kilometres of road this run claims.

    Territory is now the actual road you ran, not a bounding-box area: a run
    claims its full distance once it reaches TERRITORY_MIN_KM, and nothing below
    that. Derived from distance so old runs (which stored a box value) and new
    runs behave identically with no migration.
    """
    distance = _terra_run_distance_km(run)
    return round(distance, 4) if distance >= TERRITORY_MIN_KM else 0.0


def _terra_run_xp(run: Dict[str, Any]) -> int:
    if run.get('xp_earned') is not None:
        return _to_non_negative_int(run.get('xp_earned'), 0)
    if run.get('xp') is not None:
        return _to_non_negative_int(run.get('xp'), 0)
    return 0


def _terra_run_response(run: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = clean_doc(dict(run))
    cleaned['distance'] = _terra_run_distance_km(cleaned)
    cleaned['duration'] = _terra_run_duration_seconds(cleaned)
    cleaned['territory_captured'] = _terra_run_territory_km2(cleaned)
    cleaned['xp_earned'] = _terra_run_xp(cleaned)
    cleaned['is_loop'] = bool(cleaned.get('is_loop'))
    cleaned.setdefault('created_at', cleaned.get('created_at'))
    return cleaned


def _terra_run_history_runs(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    days = [(datetime.utcnow() - timedelta(days=i)) for i in range(6, -1, -1)]
    history = []
    for day in days:
        day_str = day.strftime('%Y-%m-%d')
        day_label = day.strftime('%a')
        day_runs = [run for run in runs if str(run.get('date') or str(run.get('created_at') or '')[:10]) == day_str]
        day_distance = sum(_terra_run_distance_km(run) for run in day_runs)
        history.append({'day': day_label, 'value': round(day_distance, 1)})
    return history


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
