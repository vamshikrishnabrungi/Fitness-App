from __future__ import annotations

import argparse
import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.activity_domain import ActivityCreate, process_activity
from backend.db_setup import ensure_database_schema
from backend.helpers import _parse_iso_datetime


ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / '.env')


def _naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _is_minor(user: Dict[str, Any]) -> bool:
    profile = user.get('profile') or {}
    birth = _parse_iso_datetime(profile.get('date_of_birth') or profile.get('birth_date'))
    if not birth:
        return False
    today = datetime.utcnow().date()
    born = birth.date()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age < 18


def _weight_kg(user: Dict[str, Any]) -> Optional[float]:
    profile = user.get('profile') or {}
    for value in (profile.get('weight_kg'), profile.get('weight'), user.get('weight_kg')):
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if 25 <= parsed <= 350:
            return parsed
    return None


def build_canonical_legacy_activity(
    source_collection: str,
    legacy: Dict[str, Any],
    user: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    raw_path = legacy.get('raw_stream') or legacy.get('gps_path') or []
    if len(raw_path) < 2:
        return None
    started_at = _naive_utc(
        _parse_iso_datetime(legacy.get('started_at'))
        or _parse_iso_datetime(legacy.get('start_time'))
        or _parse_iso_datetime(legacy.get('date'))
    )
    ended_at = _naive_utc(
        _parse_iso_datetime(legacy.get('ended_at'))
        or _parse_iso_datetime(legacy.get('end_time'))
    )
    payload = ActivityCreate(
        gps_path=raw_path,
        start_time=started_at,
        end_time=ended_at,
        paused_duration_sec=int(legacy.get('paused_duration_sec') or 0),
        source='runlete',
        activity_type='run',
        title=legacy.get('title') or 'Migrated run',
        visibility='private' if _is_minor(user) else 'clubs',
        notes=f'Migrated from {source_collection}',
    )
    processed = process_activity(payload, athlete_weight_kg=_weight_kg(user))
    legacy_id = str(legacy.get('id') or legacy.get('_id'))
    activity_id = str(uuid.uuid5(
        uuid.NAMESPACE_URL,
        f'runlete:legacy:{source_collection}:{legacy_id}',
    ))
    quality = processed.get('quality') or {}
    visibility = payload.visibility or 'private'
    now = datetime.utcnow()
    return {
        'id': activity_id,
        'user_id': user['id'],
        'source': 'runlete',
        'source_collection': source_collection,
        'source_legacy_id': legacy_id,
        'idempotency_key': f'legacy:{source_collection}:{legacy_id}',
        'activity_type': 'run',
        'run_type': 'training',
        'title': payload.title,
        'notes': payload.notes,
        'visibility': visibility,
        'status': 'complete',
        'processing_status': 'complete',
        'started_at': started_at,
        'ended_at': ended_at,
        'start_time': started_at,
        'end_time': ended_at,
        'date': (started_at or ended_at or now).strftime('%Y-%m-%d'),
        'territory_captured': 0.0,
        'territory_status': 'pending' if processed.get('route_geojson') else 'not_applicable',
        'leaderboard_eligible': bool(quality.get('leaderboard_eligible')) and visibility != 'private',
        'created_at': now,
        'updated_at': now,
        **processed,
    }


async def migrate(*, apply: bool, limit: int) -> Dict[str, int]:
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'sftc_database')]
    stats = {'scanned': 0, 'migratable': 0, 'created': 0, 'existing': 0, 'skipped': 0}
    try:
        if apply:
            await ensure_database_schema(db)
        for collection_name in ('terra_runs', 'runs'):
            cursor = db[collection_name].find({}).sort('created_at', 1)
            async for legacy in cursor:
                if limit and stats['scanned'] >= limit:
                    return stats
                stats['scanned'] += 1
                user = await db.users.find_one({'id': legacy.get('user_id')})
                if not user:
                    stats['skipped'] += 1
                    continue
                document = build_canonical_legacy_activity(collection_name, legacy, user)
                if not document:
                    stats['skipped'] += 1
                    continue
                stats['migratable'] += 1
                existing = await db.activities.find_one({'id': document['id']}, {'id': 1})
                if existing:
                    stats['existing'] += 1
                    continue
                if not apply:
                    continue
                await db.activities.insert_one(document)
                now = datetime.utcnow()
                await db.activity_outbox.update_one(
                    {'activity_id': document['id'], 'event_type': 'activity.completed'},
                    {'$setOnInsert': {
                        'id': str(uuid.uuid4()),
                        'activity_id': document['id'],
                        'user_id': document['user_id'],
                        'event_type': 'activity.completed',
                        'status': 'pending',
                        'attempts': 0,
                        'available_at': now,
                        'created_at': now,
                        'updated_at': now,
                    }},
                    upsert=True,
                )
                stats['created'] += 1
        return stats
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Recompute legacy GPS runs into canonical activities. Dry-run is the default.',
    )
    parser.add_argument('--apply', action='store_true', help='Write canonical activities and outbox events')
    parser.add_argument('--limit', type=int, default=0, help='Maximum legacy documents to inspect')
    args = parser.parse_args()
    stats = asyncio.run(migrate(apply=args.apply, limit=max(0, args.limit)))
    mode = 'APPLY' if args.apply else 'DRY RUN'
    print(f'{mode}: {stats}')


if __name__ == '__main__':
    main()
