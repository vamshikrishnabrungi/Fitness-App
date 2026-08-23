"""Territory claim/ownership/takeover logic.

Storage model — collection ``territory_cells``::

    {
        'cell':       'H3 cell id (str, primary key)',
        'resolution': int,
        'owner_id':   'user id currently holding the cell',
        'owner_name': 'display name cached for fast leaderboards',
        'club_id':    'club id of owner at time of claim (nullable)',
        'first_claimed_at': datetime,
        'last_claimed_at':  datetime,
        'last_run_id':      str,
        'takeovers':        int,           # how many ownership changes
        'claim_history':    [ {user_id, run_id, claimed_at} ]  # capped at 20
    }
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

from backend.core.config import H3_RESOLUTION
from backend.territory.h3_grid import cell_area_km2, cell_polygon


HISTORY_CAP = 20


async def ensure_indexes(db: Any) -> None:
    coll = db.territory_cells
    await coll.create_index('cell', unique=True)
    await coll.create_index([('owner_id', 1)])
    await coll.create_index([('club_id', 1)])
    await coll.create_index([('resolution', 1)])


async def claim_cells(
    db: Any,
    *,
    user_id: str,
    user_name: str,
    cells: Sequence[str],
    run_id: str,
    club_id: Optional[str] = None,
    resolution: int = H3_RESOLUTION,
) -> Dict[str, Any]:
    """Claim the given cells for ``user_id``.

    Returns a summary: ``{ claimed: [...], taken_over: [...], retained: [...] }``
    where ``retained`` lists cells already owned by this user.
    """
    now = datetime.utcnow()
    claimed: List[str] = []
    taken_over: List[Dict[str, Any]] = []
    retained: List[str] = []

    if not cells:
        return {'claimed': [], 'taken_over': [], 'retained': [], 'territory_km2': 0.0}

    existing_docs = await db.territory_cells.find({'cell': {'$in': list(cells)}}).to_list(len(cells))
    by_cell = {doc['cell']: doc for doc in existing_docs}

    for cell in cells:
        existing = by_cell.get(cell)
        history_entry = {'user_id': user_id, 'run_id': run_id, 'claimed_at': now}
        if existing is None:
            await db.territory_cells.insert_one({
                'cell': cell,
                'resolution': resolution,
                'owner_id': user_id,
                'owner_name': user_name,
                'club_id': club_id,
                'first_claimed_at': now,
                'last_claimed_at': now,
                'last_run_id': run_id,
                'takeovers': 0,
                'claim_history': [history_entry],
            })
            claimed.append(cell)
        elif existing.get('owner_id') == user_id:
            await db.territory_cells.update_one(
                {'cell': cell},
                {
                    '$set': {'last_claimed_at': now, 'last_run_id': run_id, 'club_id': club_id, 'owner_name': user_name},
                    '$push': {'claim_history': {'$each': [history_entry], '$slice': -HISTORY_CAP}},
                },
            )
            retained.append(cell)
        else:
            taken_over.append({
                'cell': cell,
                'previous_owner_id': existing.get('owner_id'),
                'previous_owner_name': existing.get('owner_name'),
            })
            await db.territory_cells.update_one(
                {'cell': cell},
                {
                    '$set': {
                        'owner_id': user_id,
                        'owner_name': user_name,
                        'club_id': club_id,
                        'last_claimed_at': now,
                        'last_run_id': run_id,
                    },
                    '$inc': {'takeovers': 1},
                    '$push': {'claim_history': {'$each': [history_entry], '$slice': -HISTORY_CAP}},
                },
            )
            claimed.append(cell)

    total_km2 = round(sum(cell_area_km2(c) for c in cells), 4)
    return {
        'claimed': claimed,
        'taken_over': taken_over,
        'retained': retained,
        'territory_km2': total_km2,
    }


async def my_cells(db: Any, user_id: str) -> List[Dict[str, Any]]:
    return await db.territory_cells.find({'owner_id': user_id}).to_list(20000)


async def cells_in_bbox(
    db: Any,
    cells_in_view: Iterable[str],
    *,
    resolution: int = H3_RESOLUTION,
) -> List[Dict[str, Any]]:
    cells_list = list(cells_in_view)
    if not cells_list:
        return []
    docs = await db.territory_cells.find(
        {'cell': {'$in': cells_list}, 'resolution': resolution}
    ).to_list(len(cells_list))
    return docs


async def club_cells(db: Any, member_ids: Sequence[str]) -> List[Dict[str, Any]]:
    if not member_ids:
        return []
    return await db.territory_cells.find(
        {'owner_id': {'$in': list(member_ids)}}, {'_id': 0}
    ).to_list(40000)


def cells_to_feature_collection(
    docs: Iterable[Dict[str, Any]],
    *,
    current_user_id: Optional[str] = None,
) -> Dict[str, Any]:
    features = []
    for doc in docs:
        cell = doc.get('cell')
        if not cell:
            continue
        ring = cell_polygon(cell)
        if not ring:
            continue
        owner_id = doc.get('owner_id')
        features.append({
            'type': 'Feature',
            'id': cell,
            'geometry': {'type': 'Polygon', 'coordinates': [ring]},
            'properties': {
                'cell': cell,
                'owner_id': owner_id,
                'owner_name': doc.get('owner_name'),
                'club_id': doc.get('club_id'),
                'mine': bool(current_user_id and owner_id == current_user_id),
                'takeovers': doc.get('takeovers', 0),
                'last_claimed_at': doc.get('last_claimed_at'),
            },
        })
    return {'type': 'FeatureCollection', 'features': features}
