"""City-map territory endpoints (H3-based).

    GET /territory/me                     - my owned cells (GeoJSON)
    GET /territory/cells?south=..&west=..&north=..&east=..
                                          - cells in a viewport, with owner info
    GET /territory/leaderboard?city=...   - top territory holders in a city
    GET /territory/peaks/me               - tracked peaks for the user
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.core.config import H3_RESOLUTION
from backend.core.db import db
from backend.core.security import get_current_user
from backend.territory.claim import (
    cells_in_bbox as bbox_cells_docs,
    cells_to_feature_collection,
    my_cells,
)
from backend.territory.h3_grid import cells_in_bbox

router = APIRouter()


@router.get('/territory/me')
async def my_territory(current_user: dict = Depends(get_current_user)):
    docs = await my_cells(db, current_user['id'])
    fc = cells_to_feature_collection(docs, current_user_id=current_user['id'])
    fc['total_cells'] = len(docs)
    return fc


@router.get('/territory/cells')
async def territory_in_bbox(
    south: float = Query(...),
    west: float = Query(...),
    north: float = Query(...),
    east: float = Query(...),
    resolution: int = Query(H3_RESOLUTION, ge=6, le=11),
    current_user: dict = Depends(get_current_user),
):
    if south >= north or west >= east:
        raise HTTPException(status_code=400, detail='Invalid bounding box')
    cells = cells_in_bbox(south, west, north, east, resolution=resolution)
    if not cells:
        return {'type': 'FeatureCollection', 'features': [], 'cells_in_view': 0}
    docs = await bbox_cells_docs(db, cells, resolution=resolution)
    fc = cells_to_feature_collection(docs, current_user_id=current_user['id'])
    fc['cells_in_view'] = len(cells)
    fc['cells_owned'] = len(docs)
    return fc


@router.get('/territory/leaderboard')
async def territory_leaderboard(
    city: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    pipeline = [
        {'$group': {'_id': '$owner_id', 'owner_name': {'$first': '$owner_name'}, 'cells': {'$sum': 1}, 'takeovers': {'$sum': '$takeovers'}}},
        {'$sort': {'cells': -1}},
        {'$limit': max(1, min(100, limit))},
    ]
    if city:
        # filter to users whose profile.city matches; we resolve owner_ids via users collection
        users = await db.users.find({'profile.city': {'$regex': f'^{city}$', '$options': 'i'}}).to_list(500)
        ids = [u['id'] for u in users]
        if not ids:
            return []
        pipeline.insert(0, {'$match': {'owner_id': {'$in': ids}}})

    rows = await db.territory_cells.aggregate(pipeline).to_list(limit)
    return [
        {
            'rank': index + 1,
            'user_id': row['_id'],
            'username': row.get('owner_name'),
            'cells_owned': row['cells'],
            'takeovers': row.get('takeovers', 0),
            'is_me': row['_id'] == current_user['id'],
        }
        for index, row in enumerate(rows)
    ]


@router.get('/territory/peaks/me')
async def my_peaks(current_user: dict = Depends(get_current_user)):
    """Trek/peak summary: runs with significant elevation gain."""
    runs = await db.terra_runs.find(
        {'user_id': current_user['id'], 'elevation_gain_m': {'$gte': 50}}
    ).sort('elevation_gain_m', -1).to_list(50)
    return [
        {
            'run_id': r.get('id'),
            'date': r.get('date'),
            'distance_km': r.get('distance_km'),
            'duration_sec': r.get('duration_sec'),
            'elevation_gain_m': r.get('elevation_gain_m', 0),
            'cells_claimed': len(r.get('cells_claimed') or []),
        }
        for r in runs
    ]
