from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.competition_domain import match_segment_effort
from backend.geo_db import (
    candidate_segment_ids,
    candidate_street_edge_ids,
    mirror_activity_geometry,
    release_competition_activity,
    sync_segment_effort,
    sync_competition_activity,
)
from backend.helpers import TERRITORY_MIN_KM, _parse_iso_datetime
from backend.territory_engine import (
    TerritoryMatcherUnavailable,
    match_activity_to_edges,
    recompute_edges,
)
from backend.competition_workers import verify_activity_race_results


logger = logging.getLogger(__name__)
MAX_ATTEMPTS = max(1, int(os.environ.get('ACTIVITY_OUTBOX_MAX_ATTEMPTS', '8') or 8))
LEASE_SECONDS = 300


def outbox_retry_delay(attempts: int) -> int:
    return min(3600, 15 * (2 ** max(0, attempts - 1)))


async def match_activity_segments(db: Any, activity: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not activity.get('leaderboard_eligible'):
        return []
    candidate_ids = await candidate_segment_ids(activity['id'])
    query: Dict[str, Any] = {'status': 'active'}
    if candidate_ids:
        query['id'] = {'$in': candidate_ids}
    segments = await db.segments.find(query).to_list(2_000)
    efforts: List[Dict[str, Any]] = []
    for segment in segments:
        match = match_segment_effort(
            activity.get('cleaned_stream') or [],
            segment.get('path') or [],
        )
        if not match:
            continue
        effort_id = str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            f'runlete:segment-effort:{activity["id"]}:{segment["id"]}',
        ))
        effort = {
            'id': effort_id,
            'activity_id': activity['id'],
            'segment_id': segment['id'],
            'user_id': activity['user_id'],
            'started_at': match['started_at'],
            'ended_at': match['ended_at'],
            'elapsed_time_sec': match['elapsed_time_sec'],
            'max_deviation_m': match['max_deviation_m'],
            'quality_score': (activity.get('quality') or {}).get('score'),
            'leaderboard_eligible': True,
            'created_at': datetime.utcnow(),
        }
        await db.segment_efforts.update_one(
            {'activity_id': activity['id'], 'segment_id': segment['id']},
            {'$set': effort},
            upsert=True,
        )
        await sync_segment_effort(effort)
        efforts.append(effort)
    return efforts


async def match_activity_territory(db: Any, activity: Dict[str, Any]) -> Dict[str, Any]:
    if (
        float(activity.get('distance_km') or 0) < TERRITORY_MIN_KM
        or not activity.get('leaderboard_eligible')
    ):
        result = {
            'territory_captured': 0.0,
            'territory_status': 'not_eligible',
            'matched_street_edges': [],
            'updated_at': datetime.utcnow(),
        }
        await db.activities.update_one({'id': activity['id']}, {'$set': result})
        return result

    candidate_ids = await candidate_street_edge_ids(activity['id'])
    query: Dict[str, Any] = {'status': 'active'}
    if candidate_ids:
        query['id'] = {'$in': candidate_ids}
    street_edges = await db.street_edges.find(query).to_list(50_000)
    matched_edges: List[str] = []
    claimed_km = 0.0
    claimed_at = activity.get('started_at') or activity.get('created_at') or datetime.utcnow()
    claimed_datetime = _parse_iso_datetime(claimed_at) or datetime.utcnow()
    for edge in street_edges:
        match = match_segment_effort(
            activity.get('cleaned_stream') or [],
            edge.get('path') or [],
            endpoint_tolerance_m=35,
            shape_tolerance_m=45,
        )
        if not match:
            continue
        ownership = {
            'id': f'edge-owner:{edge["id"]}',
            'street_edge_id': edge['id'],
            'user_id': activity['user_id'],
            'activity_id': activity['id'],
            'club_id': None,
            'claimed_at': claimed_datetime,
            'updated_at': datetime.utcnow(),
            'quality_score': (activity.get('quality') or {}).get('score'),
        }
        try:
            result = await db.territory_ownership.update_one(
                {
                    'street_edge_id': edge['id'],
                    '$or': [
                        {'claimed_at': {'$lte': claimed_datetime}},
                        {'claimed_at': {'$exists': False}},
                    ],
                },
                {'$set': ownership},
                upsert=True,
            )
        except DuplicateKeyError:
            continue
        if not (getattr(result, 'matched_count', 0) or getattr(result, 'upserted_id', None)):
            continue
        matched_edges.append(edge['id'])
        claimed_km += float(edge.get('distance_km') or 0)

    result = {
        'territory_captured': round(claimed_km, 3),
        'territory_status': 'matched',
        'matched_street_edges': matched_edges,
        'updated_at': datetime.utcnow(),
    }
    await db.activities.update_one({'id': activity['id']}, {'$set': result})
    return result


async def release_activity_derived_facts(db: Any, activity_id: str) -> Dict[str, int]:
    """Remove derived facts and restore the newest previous owner for released roads."""
    relational_edge_ids = await release_competition_activity(activity_id)
    if relational_edge_ids:
        await recompute_edges(relational_edge_ids)
    ownership = await db.territory_ownership.find({'activity_id': activity_id}).to_list(50_000)
    edge_ids = [item['street_edge_id'] for item in ownership]
    effort_delete = await db.segment_efforts.delete_many({'activity_id': activity_id})
    await db.territory_ownership.delete_many({'activity_id': activity_id})

    restored = 0
    for edge_id in edge_ids:
        predecessor = await db.activities.find_one(
            {
                'id': {'$ne': activity_id},
                'status': {'$ne': 'deleted'},
                'leaderboard_eligible': True,
                'matched_street_edges': edge_id,
            },
            sort=[('started_at', -1)],
        )
        if not predecessor:
            continue
        claimed_at = predecessor.get('started_at') or predecessor.get('created_at') or datetime.utcnow()
        await db.territory_ownership.update_one(
            {'street_edge_id': edge_id},
            {'$set': {
                'id': f'edge-owner:{edge_id}',
                'street_edge_id': edge_id,
                'user_id': predecessor['user_id'],
                'activity_id': predecessor['id'],
                'club_id': None,
                'claimed_at': claimed_at,
                'updated_at': datetime.utcnow(),
                'quality_score': (predecessor.get('quality') or {}).get('score'),
            }},
            upsert=True,
        )
        restored += 1
    return {
        'segment_efforts_removed': int(getattr(effort_delete, 'deleted_count', 0)),
        'territory_edges_released': len(edge_ids),
        'territory_edges_restored': restored,
        'relational_territory_edges_recomputed': len(relational_edge_ids),
    }


async def process_activity_event(db: Any, event: Dict[str, Any]) -> Dict[str, Any]:
    activity = await db.activities.find_one({
        'id': event['activity_id'],
        'status': {'$ne': 'deleted'},
    })
    if not activity:
        raise LookupError(f'Activity {event["activity_id"]} was not found')

    # Every execution starts by releasing mutable projections. This makes retries
    # and forced reprocessing converge instead of temporarily retaining stale
    # territory, segment, race, timeline, or leaderboard facts.
    await release_activity_derived_facts(db, activity['id'])
    mirrored = await mirror_activity_geometry(activity)
    # The initial relational write creates the canonical activity/attribution but
    # cannot publish competition facts before asynchronous checks complete.
    relational = await sync_competition_activity(
        {**activity, 'competition_checks_complete': False}
    )
    efforts: List[Dict[str, Any]] = []
    matcher_completed = True
    try:
        territory_match = await match_activity_to_edges(activity)
        territory = {
            'territory_captured': round(
                sum(
                    float(item.get('distance_m') or 0)
                    for item in territory_match.get('traversals') or []
                ) / 1000,
                3,
            ),
            'territory_status': territory_match.get('status') or 'failed_match',
            'matched_street_edges': [
                item['street_edge_id']
                for item in territory_match.get('traversals') or []
            ],
            'territory_match_confidence': territory_match.get('confidence'),
            'territory_rejection_reasons': (
                [territory_match['reason']]
                if territory_match.get('reason')
                else []
            ),
            'updated_at': datetime.utcnow(),
        }
    except TerritoryMatcherUnavailable as exc:
        matcher_completed = False
        territory = {
            'territory_captured': 0.0,
            'territory_status': 'unsupported_region',
            'matched_street_edges': [],
            'territory_error': str(exc),
            'territory_rejection_reasons': ['unsupported_region'],
            'updated_at': datetime.utcnow(),
        }
    competition_checks_complete = bool(
        matcher_completed and activity.get('leaderboard_eligible')
    )
    competition_update = {
        **territory,
        'competition_checks_complete': competition_checks_complete,
    }
    await db.activities.update_one(
        {'id': activity['id']},
        {'$set': competition_update},
    )
    verified_activity = {
        **activity,
        **competition_update,
    }
    relational = await sync_competition_activity(verified_activity)
    if competition_checks_complete:
        efforts = await match_activity_segments(db, verified_activity)
        matched_edges = territory.get('matched_street_edges') or []
        if matched_edges:
            await recompute_edges(
                matched_edges,
                source_activity_id=str(activity['id']),
            )
    race_results = (
        await verify_activity_race_results(activity['id'])
        if competition_checks_complete
        else {'evaluated': 0, 'verified': 0}
    )
    downstream = {
        'status': 'complete',
        'postgis_mirrored': mirrored,
        'relational_activity_synced': bool(relational.get('synced')),
        'attributed_club_id': relational.get('club_id'),
        'segment_effort_count': len(efforts),
        'territory_edge_count': len(territory.get('matched_street_edges') or []),
        'race_results_evaluated': race_results.get('evaluated', 0),
        'competition_checks_complete': competition_checks_complete,
        'completed_at': datetime.utcnow(),
    }
    await db.activities.update_one(
        {'id': activity['id']},
        {'$set': {'downstream_processing': downstream, 'updated_at': datetime.utcnow()}},
    )
    return downstream


async def _claim_event(db: Any, event_id: str) -> Optional[Dict[str, Any]]:
    now = datetime.utcnow()
    return await db.activity_outbox.find_one_and_update(
        {
            'id': event_id,
            'available_at': {'$lte': now},
            '$or': [
                {'status': {'$in': ['pending', 'retry']}},
                {'status': 'processing', 'lease_expires_at': {'$lte': now}},
            ],
        },
        {'$set': {
            'status': 'processing',
            'lease_expires_at': now + timedelta(seconds=LEASE_SECONDS),
            'updated_at': now,
        }},
        return_document=ReturnDocument.AFTER,
    )


async def process_outbox_event(db: Any, event_id: str) -> Optional[Dict[str, Any]]:
    event = await _claim_event(db, event_id)
    if not event:
        return None
    attempts = int(event.get('attempts') or 0) + 1
    try:
        result = await process_activity_event(db, event)
    except Exception as exc:
        terminal = attempts >= MAX_ATTEMPTS or isinstance(exc, LookupError)
        now = datetime.utcnow()
        await db.activity_outbox.update_one(
            {'id': event_id},
            {'$set': {
                'status': 'dead_letter' if terminal else 'retry',
                'attempts': attempts,
                'last_error': str(exc)[:1000],
                'available_at': now + timedelta(seconds=outbox_retry_delay(attempts)),
                'lease_expires_at': None,
                'updated_at': now,
            }},
        )
        logger.exception('Activity outbox event %s failed', event_id)
        return {'id': event_id, 'status': 'dead_letter' if terminal else 'retry'}

    now = datetime.utcnow()
    await db.activity_outbox.update_one(
        {'id': event_id},
        {'$set': {
            'status': 'completed',
            'attempts': attempts,
            'result': result,
            'completed_at': now,
            'lease_expires_at': None,
            'updated_at': now,
        }},
    )
    return {'id': event_id, 'status': 'completed', 'result': result}


async def process_pending_outbox(db: Any, limit: int = 25) -> Dict[str, Any]:
    now = datetime.utcnow()
    events = await db.activity_outbox.find({
        'available_at': {'$lte': now},
        '$or': [
            {'status': {'$in': ['pending', 'retry']}},
            {'status': 'processing', 'lease_expires_at': {'$lte': now}},
        ],
    }).sort('available_at', 1).to_list(min(max(limit, 1), 100))
    results = []
    for event in events:
        processed = await process_outbox_event(db, event['id'])
        if processed:
            results.append(processed)
    return {
        'selected': len(events),
        'processed': len(results),
        'completed': sum(item['status'] == 'completed' for item in results),
        'retrying': sum(item['status'] == 'retry' for item in results),
        'dead_lettered': sum(item['status'] == 'dead_letter' for item in results),
    }
