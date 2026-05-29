"""Run tracking with H3 territory claiming + anti-cheat.

Endpoints (kept compatible with existing frontend contracts):
    POST   /terra/runs                   - submit a GPS run
    GET    /terra/runs                   - list my runs
    GET    /terra/runs/{run_id}          - single run + territory feature collection
    GET    /terra/stats                  - aggregate stats
    GET    /runs/stats                   - alias

Anti-cheat: see :mod:`backend.territory.anticheat`.
Territory: each unique H3 cell visited becomes a claim. Cells already owned
by someone else are taken over.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.core.config import H3_RESOLUTION, RUN_MAX_SPEED_MPS
from backend.core.db import db
from backend.core.run_helpers import stats_bundle, user_run_docs
from backend.core.security import get_current_user
from backend.helpers import (
    _parse_iso_datetime,
    _terra_normalize_path,
    _terra_run_response,
)
from backend.models import TerraRunCreate
from backend.territory.anticheat import elevation_gain_m, validate_run
from backend.territory.claim import claim_cells, cells_to_feature_collection
from backend.territory.h3_grid import cell_area_km2, cells_for_path, cells_to_geojson

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Create a run
# ---------------------------------------------------------------------------

@router.post('/terra/runs')
async def create_run(
    payload: TerraRunCreate,
    current_user: dict = Depends(get_current_user),
):
    activity = 'run'
    raw_path = [p.model_dump() if hasattr(p, 'model_dump') else p for p in payload.gps_path]
    path = _terra_normalize_path(raw_path)
    now = datetime.utcnow()
    start_dt = _parse_iso_datetime(payload.start_time)
    end_dt = _parse_iso_datetime(payload.end_time)

    duration_seconds = 0
    if start_dt and end_dt:
        duration_seconds = max(1, int(round((end_dt - start_dt).total_seconds())))
    elif path:
        first_ts = _parse_iso_datetime(path[0].get('timestamp'))
        last_ts = _parse_iso_datetime(path[-1].get('timestamp'))
        if first_ts and last_ts and last_ts > first_ts:
            duration_seconds = max(1, int(round((last_ts - first_ts).total_seconds())))

    verdict = validate_run(path, duration_seconds=duration_seconds or 0, activity=activity)
    distance_km = round(verdict['distance_m'] / 1000.0, 3)

    # Permit very short demo runs - mark them as unverified rather than reject
    if not verdict['valid']:
        logger.info('Run anti-cheat: invalid for user=%s reasons=%s', current_user['id'], verdict['reasons'])

    is_loop = False
    if len(path) >= 4:
        # use first / last haversine
        from backend.territory.anticheat import haversine_m
        is_loop = haversine_m(path[0], path[-1]) <= 100  # within 100m

    # extract cells & claim
    cells: List[str] = []
    territory_km2 = 0.0
    claim_result: Dict[str, Any] = {'claimed': [], 'taken_over': [], 'retained': []}

    if verdict['valid'] and path:
        cells = cells_for_path(path)
        if cells:
            user_name = current_user.get('name') or current_user.get('email') or 'Runner'
            claim_result = await claim_cells(
                db,
                user_id=current_user['id'],
                user_name=user_name,
                cells=cells,
                run_id='',  # patched below
                resolution=H3_RESOLUTION,
            )
            territory_km2 = round(claim_result['territory_km2'], 4)

    # XP: 1 XP per 0.1 km + 5 XP per cell claimed + 1 XP per cell retained
    base_xp = int(distance_km * 10)
    cell_xp = len(claim_result.get('claimed', [])) * 5 + len(claim_result.get('retained', [])) * 1
    xp_earned = max(0, base_xp + cell_xp)

    run_id = str(uuid.uuid4())
    # patch run_id into history of claimed cells
    if claim_result.get('claimed'):
        await db.territory_cells.update_many(
            {'cell': {'$in': claim_result['claimed']}, 'last_run_id': ''},
            {'$set': {'last_run_id': run_id}},
        )

    run_doc = {
        'id': run_id,
        'user_id': current_user['id'],
        'activity': activity,
        'gps_path': path,
        'start_time': payload.start_time,
        'end_time': payload.end_time,
        'date': (start_dt or end_dt or now).strftime('%Y-%m-%d'),
        'distance': distance_km,
        'distance_km': distance_km,
        'duration': duration_seconds,
        'duration_sec': duration_seconds,
        'territory_captured': territory_km2,
        'territory_km2': territory_km2,
        'is_loop': is_loop,
        'cells': cells,
        'cells_claimed': claim_result.get('claimed', []),
        'cells_taken_over': [t['cell'] for t in claim_result.get('taken_over', [])],
        'cells_retained': claim_result.get('retained', []),
        'taken_over_from': claim_result.get('taken_over', []),
        'xp_earned': xp_earned,
        'xp': xp_earned,
        'anti_cheat': verdict,
        'elevation_gain_m': elevation_gain_m(path),
        'city': (current_user.get('profile') or {}).get('city'),
        'created_at': now,
        'updated_at': now,
    }
    await db.terra_runs.insert_one(dict(run_doc))

    response = _terra_run_response(run_doc)
    response['territory_geojson'] = cells_to_geojson(cells)
    response['claim'] = {
        'claimed': claim_result.get('claimed', []),
        'taken_over': claim_result.get('taken_over', []),
        'retained': claim_result.get('retained', []),
        'cells_total': len(cells),
        'cell_area_km2_avg': round(cell_area_km2(cells[0]), 4) if cells else 0,
    }
    return response


# ---------------------------------------------------------------------------
# Listing & stats
# ---------------------------------------------------------------------------

@router.get('/terra/runs')
async def list_runs(current_user: dict = Depends(get_current_user)):
    docs = await user_run_docs(current_user['id'])
    return [_terra_run_response(d) for d in docs]


@router.get('/terra/runs/{run_id}')
async def get_run(run_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.terra_runs.find_one({'id': run_id, 'user_id': current_user['id']})
    if not doc:
        doc = await db.runs.find_one({'id': run_id, 'user_id': current_user['id']})
    if not doc:
        raise HTTPException(status_code=404, detail='Run not found')
    response = _terra_run_response(doc)
    cells = doc.get('cells') or []
    response['territory_geojson'] = cells_to_geojson(cells)
    return response


@router.get('/terra/stats')
async def terra_stats(current_user: dict = Depends(get_current_user)):
    return await stats_bundle(current_user)


@router.get('/runs/stats')
async def runs_stats(current_user: dict = Depends(get_current_user)):
    bundle = await stats_bundle(current_user)
    return {
        'total_distance': bundle['total_distance'],
        'average_pace': bundle['average_pace'],
        'fatigue': bundle['fatigue'],
        'consistency': bundle['consistency'],
        'history': bundle['history'],
    }
