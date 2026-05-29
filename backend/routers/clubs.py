"""Run-club CRUD, leaderboards, membership, and shared territory.

Existing contracts kept identical:
    POST   /terra/clubs
    GET    /terra/clubs/my
    GET    /terra/clubs/city
    POST   /terra/clubs/{id}/join
    GET    /terra/clubs/{id}/members/leaderboard
    GET    /terra/clubs/leaderboard/city

New endpoints added:
    GET    /terra/clubs/{id}                - club detail
    GET    /terra/clubs/{id}/members        - full member list
    POST   /terra/clubs/{id}/leave          - leave (owners forbidden)
    DELETE /terra/clubs/{id}                - delete (owner only)
    GET    /terra/clubs/{id}/territory      - shared GeoJSON of all member cells
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.core.db import db
from backend.core.run_helpers import (
    club_member_leaderboard,
    club_response,
    user_city,
)
from backend.core.security import get_current_user
from backend.models import RunClubCreate
from backend.territory.claim import cells_to_feature_collection, club_cells

router = APIRouter()


async def _get_club_or_404(club_id: str) -> Dict[str, Any]:
    club = await db.run_clubs.find_one({'id': club_id})
    if not club:
        raise HTTPException(status_code=404, detail='Run club not found')
    return club


# ---------------------------------------------------------------------------
# Create / list
# ---------------------------------------------------------------------------

@router.post('/terra/clubs')
async def create_club(payload: RunClubCreate, current_user: dict = Depends(get_current_user)):
    name = payload.name.strip()
    city = payload.city.strip()
    if not name:
        raise HTTPException(status_code=400, detail='Club name is required')
    if not city:
        raise HTTPException(status_code=400, detail='City is required')

    now = datetime.utcnow()
    club = {
        'id': str(uuid.uuid4()),
        'name': name,
        'city': city,
        'description': payload.description.strip() if payload.description else None,
        'is_public': bool(payload.is_public),
        'owner_id': current_user['id'],
        'owner_name': current_user.get('name') or current_user.get('email'),
        'member_ids': [current_user['id']],
        'invite_code': uuid.uuid4().hex[:8].upper(),
        'created_at': now,
        'updated_at': now,
    }
    await db.run_clubs.insert_one(club)
    return await club_response(club, current_user)


@router.get('/terra/clubs/my')
async def list_my_clubs(current_user: dict = Depends(get_current_user)):
    docs = await db.run_clubs.find({'member_ids': current_user['id']}).sort('created_at', -1).to_list(200)
    return [await club_response(doc, current_user) for doc in docs]


@router.get('/terra/clubs/city')
async def list_city_clubs(city: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    city_name = (city or user_city(current_user)).strip()
    docs = await db.run_clubs.find(
        {'city': {'$regex': f'^{city_name}$', '$options': 'i'}, 'is_public': True}
    ).sort('created_at', -1).to_list(200)
    return [await club_response(doc, current_user) for doc in docs]


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

@router.get('/terra/clubs/{club_id}')
async def get_club(club_id: str, current_user: dict = Depends(get_current_user)):
    club = await _get_club_or_404(club_id)
    if not club.get('is_public', True) and current_user['id'] not in club.get('member_ids', []):
        raise HTTPException(status_code=403, detail='Private club')
    return await club_response(club, current_user)


@router.get('/terra/clubs/{club_id}/members')
async def list_members(club_id: str, current_user: dict = Depends(get_current_user)):
    club = await _get_club_or_404(club_id)
    if current_user['id'] not in club.get('member_ids', []) and not club.get('is_public', True):
        raise HTTPException(status_code=403, detail='Not a club member')
    member_ids = club.get('member_ids', [])
    users = await db.users.find({'id': {'$in': member_ids}}).to_list(len(member_ids) or 1)
    return [
        {
            'id': u['id'],
            'username': u.get('name') or u.get('email'),
            'is_owner': u['id'] == club.get('owner_id'),
        }
        for u in users
    ]


@router.get('/terra/clubs/{club_id}/territory')
async def club_territory(club_id: str, current_user: dict = Depends(get_current_user)):
    club = await _get_club_or_404(club_id)
    if not club.get('is_public', True) and current_user['id'] not in club.get('member_ids', []):
        raise HTTPException(status_code=403, detail='Private club')
    docs = await club_cells(db, club.get('member_ids', []))
    return cells_to_feature_collection(docs, current_user_id=current_user['id'])


# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------

@router.post('/terra/clubs/{club_id}/join')
async def join_club(club_id: str, current_user: dict = Depends(get_current_user)):
    club = await _get_club_or_404(club_id)
    if not club.get('is_public', True) and club.get('owner_id') != current_user['id']:
        raise HTTPException(status_code=403, detail='This club is private')
    member_ids = [str(m) for m in club.get('member_ids', [])]
    if current_user['id'] not in member_ids:
        member_ids.append(current_user['id'])
        await db.run_clubs.update_one(
            {'id': club_id},
            {'$set': {'member_ids': member_ids, 'updated_at': datetime.utcnow()}},
        )
        club['member_ids'] = member_ids
    return await club_response(club, current_user)


@router.post('/terra/clubs/{club_id}/leave')
async def leave_club(club_id: str, current_user: dict = Depends(get_current_user)):
    club = await _get_club_or_404(club_id)
    if club.get('owner_id') == current_user['id']:
        raise HTTPException(status_code=400, detail='Owners cannot leave - delete the club instead')
    if current_user['id'] not in club.get('member_ids', []):
        raise HTTPException(status_code=400, detail='Not a member')
    member_ids = [m for m in club.get('member_ids', []) if m != current_user['id']]
    await db.run_clubs.update_one(
        {'id': club_id},
        {'$set': {'member_ids': member_ids, 'updated_at': datetime.utcnow()}},
    )
    club['member_ids'] = member_ids
    return await club_response(club, current_user)


@router.delete('/terra/clubs/{club_id}')
async def delete_club(club_id: str, current_user: dict = Depends(get_current_user)):
    club = await _get_club_or_404(club_id)
    if club.get('owner_id') != current_user['id']:
        raise HTTPException(status_code=403, detail='Only the owner can delete this club')
    await db.run_clubs.delete_one({'id': club_id})
    return {'status': 'deleted', 'id': club_id}


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------

@router.get('/terra/clubs/{club_id}/members/leaderboard')
async def members_leaderboard(club_id: str, period: str = 'week', current_user: dict = Depends(get_current_user)):
    club = await _get_club_or_404(club_id)
    if current_user['id'] not in club.get('member_ids', []) and not club.get('is_public', True):
        raise HTTPException(status_code=403, detail='Not a club member')
    return await club_member_leaderboard(club, period)


@router.get('/terra/clubs/leaderboard/city')
async def city_leaderboard(city: Optional[str] = None, period: str = 'week', current_user: dict = Depends(get_current_user)):
    city_name = (city or user_city(current_user)).strip()
    docs = await db.run_clubs.find(
        {'city': {'$regex': f'^{city_name}$', '$options': 'i'}}
    ).to_list(500)
    rows = [await club_response(doc, current_user, period) for doc in docs]
    rows.sort(key=lambda r: (r['total_distance'], r['active_members'], r['total_runs']), reverse=True)
    return [{**r, 'rank': i + 1} for i, r in enumerate(rows)]
