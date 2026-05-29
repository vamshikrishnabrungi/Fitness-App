"""Shared helpers for runs / clubs / leaderboards.

These were previously inline in server.py; they live here so multiple
routers can reuse the same logic without circular imports.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from backend.core.db import db
from backend.helpers import (
    _parse_iso_datetime,
    _terra_level_from_xp,
    _terra_referral_code,
    _terra_run_distance_km,
    _terra_run_duration_seconds,
    _terra_run_history_runs,
    _terra_run_response,
    _terra_run_territory_km2,
    _terra_run_xp,
)


# ---------------------------------------------------------------------------
# Run aggregation
# ---------------------------------------------------------------------------

async def user_run_docs(user_id: str) -> List[Dict[str, Any]]:
    terra = await db.terra_runs.find({'user_id': user_id}).to_list(500)
    legacy = await db.runs.find({'user_id': user_id}).to_list(500)
    docs: Dict[str, Dict[str, Any]] = {}
    for run in [*legacy, *terra]:
        rid = str(run.get('id') or uuid.uuid4())
        docs[rid] = dict(run)
    return sorted(
        docs.values(),
        key=lambda d: _parse_iso_datetime(d.get('created_at')) or _parse_iso_datetime(d.get('date')) or datetime.min,
        reverse=True,
    )


async def user_summary(user: Dict[str, Any], is_me: bool = False) -> Dict[str, Any]:
    runs = await user_run_docs(user['id'])
    total_distance = round(sum(_terra_run_distance_km(r) for r in runs), 1)
    total_territory = round(sum(_terra_run_territory_km2(r) for r in runs), 4)
    xp = sum(_terra_run_xp(r) for r in runs)
    return {
        'id': user['id'],
        'username': user.get('name') or user.get('email', 'Runner'),
        'xp': xp,
        'level': _terra_level_from_xp(float(xp)),
        'total_territory': total_territory,
        'total_distance': total_distance,
        'is_me': is_me,
    }


async def stats_bundle(current_user: dict) -> Dict[str, Any]:
    runs = await user_run_docs(current_user['id'])
    total_runs = len(runs)
    total_distance = round(sum(_terra_run_distance_km(r) for r in runs), 1)
    total_duration = sum(_terra_run_duration_seconds(r) for r in runs)
    total_territory = round(sum(_terra_run_territory_km2(r) for r in runs), 4)
    total_xp = sum(_terra_run_xp(r) for r in runs)
    level = _terra_level_from_xp(float(total_xp))

    history = _terra_run_history_runs(runs)
    days_with_runs = sum(1 for d in history if d['value'] > 0)
    consistency = int((days_with_runs / 7) * 100) if history else 0

    average_pace = None
    if total_distance > 0:
        pace_seconds = total_duration / total_distance
        mins = int(pace_seconds // 60)
        secs = int(pace_seconds % 60)
        average_pace = f"{mins}'{secs:02d}"

    leaderboard = await all_user_summaries(include_placeholders=False, current_user=current_user)
    friends_count = max(0, len([e for e in leaderboard if e['id'] != current_user['id']]))

    return {
        'total_runs': total_runs,
        'total_distance': total_distance,
        'total_territory': total_territory,
        'xp': total_xp,
        'level': level,
        'competition_entries': total_runs,
        'territories_owned': sum(1 for r in runs if _terra_run_territory_km2(r) > 0),
        'referral_code': _terra_referral_code(current_user),
        'friends_count': friends_count,
        'average_pace': average_pace,
        'fatigue': 'Low' if total_distance == 0 else ('High' if total_distance > 20 else 'Moderate'),
        'consistency': consistency,
        'history': history,
    }


async def all_user_summaries(include_placeholders: bool = True, current_user: Optional[dict] = None) -> List[Dict[str, Any]]:
    users = await db.users.find({'mode': {'$ne': 'coach'}}).to_list(500)
    summaries: List[Dict[str, Any]] = []
    for user in users:
        if not await user_run_docs(user['id']):
            continue
        summaries.append(await user_summary(user, is_me=bool(current_user and user['id'] == current_user['id'])))
    if current_user and not any(e['id'] == current_user['id'] for e in summaries):
        summaries.append(await user_summary(current_user, is_me=True))
    summaries.sort(key=lambda i: (i['xp'], i['total_distance'], i['total_territory']), reverse=True)

    if include_placeholders and len(summaries) < 5:
        placeholders = ['Trail Nova', 'Runner Atlas', 'Mira Ridge', 'Pace Orion', 'Summit Ember', 'Beacon Vale']
        existing = {s['username'] for s in summaries}
        base_xp = summaries[0]['xp'] if summaries else 480
        for i, name in enumerate(placeholders):
            if name in existing:
                continue
            xp = max(120, base_xp - (i + 1) * 55)
            total_distance = round(max(4.0, xp / 32.0), 1)
            total_territory = round(max(0.2, xp / 1800.0), 4)
            summaries.append({
                'id': f'placeholder-{i + 1}',
                'username': name,
                'xp': xp,
                'level': _terra_level_from_xp(float(xp)),
                'total_territory': total_territory,
                'total_distance': total_distance,
                'is_me': False,
            })
            if len(summaries) >= 5:
                break
        summaries.sort(key=lambda i: (i['xp'], i['total_distance'], i['total_territory']), reverse=True)
    return summaries


# ---------------------------------------------------------------------------
# Run-club helpers
# ---------------------------------------------------------------------------

def period_start(period: str) -> Optional[datetime]:
    today = datetime.utcnow().date()
    p = (period or 'week').lower()
    if p == 'all':
        return None
    if p == 'month':
        return datetime(today.year, today.month, 1)
    week_start = today - timedelta(days=today.weekday())
    return datetime.combine(week_start, datetime.min.time())


def run_in_period(run: Dict[str, Any], start: Optional[datetime]) -> bool:
    if start is None:
        return True
    when = (
        _parse_iso_datetime(run.get('date'))
        or _parse_iso_datetime(run.get('end_time'))
        or _parse_iso_datetime(run.get('created_at'))
    )
    return bool(when and when >= start)


def user_city(user: Dict[str, Any]) -> str:
    profile = user.get('profile') or {}
    for key in ('city', 'hometown', 'location'):
        value = str(profile.get(key) or '').strip()
        if value:
            return value
    return 'Your City'


async def club_member_docs(member_ids: List[str]) -> List[Dict[str, Any]]:
    if not member_ids:
        return []
    users = await db.users.find({'id': {'$in': member_ids}}).to_list(500)
    by_id = {u['id']: u for u in users}
    return [by_id[mid] for mid in member_ids if mid in by_id]


async def club_totals(club: Dict[str, Any], period: str = 'week') -> Dict[str, Any]:
    member_ids = [str(m) for m in club.get('member_ids', []) if str(m).strip()]
    start = period_start(period)
    total_distance = 0.0
    total_territory = 0.0
    total_runs = 0
    active_members = 0
    for mid in member_ids:
        runs = [r for r in await user_run_docs(mid) if run_in_period(r, start)]
        d = sum(_terra_run_distance_km(r) for r in runs)
        total_distance += d
        total_territory += sum(_terra_run_territory_km2(r) for r in runs)
        total_runs += len(runs)
        if d > 0:
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


async def club_response(club: Dict[str, Any], current_user: Optional[dict] = None, period: str = 'week') -> Dict[str, Any]:
    cleaned = dict(club)
    cleaned.pop('_id', None)
    cleaned.setdefault('member_ids', [])
    cleaned['member_count'] = len(cleaned['member_ids'])
    cleaned['is_member'] = bool(current_user and current_user['id'] in cleaned['member_ids'])
    cleaned['is_owner'] = bool(current_user and current_user['id'] == cleaned.get('owner_id'))
    cleaned.update(await club_totals(cleaned, period))
    return cleaned


async def club_member_leaderboard(club: Dict[str, Any], period: str = 'week') -> List[Dict[str, Any]]:
    member_ids = [str(m) for m in club.get('member_ids', []) if str(m).strip()]
    users = await club_member_docs(member_ids)
    start = period_start(period)
    rows = []
    for user in users:
        runs = [r for r in await user_run_docs(user['id']) if run_in_period(r, start)]
        rows.append({
            'user_id': user['id'],
            'username': user.get('name') or user.get('email', 'Runner'),
            'total_distance': round(sum(_terra_run_distance_km(r) for r in runs), 1),
            'total_territory': round(sum(_terra_run_territory_km2(r) for r in runs), 4),
            'total_runs': len(runs),
        })
    rows.sort(key=lambda r: (r['total_distance'], r['total_runs'], r['total_territory']), reverse=True)
    return [{**r, 'rank': i + 1} for i, r in enumerate(rows)]


# re-export for backward compatibility
run_response = _terra_run_response
