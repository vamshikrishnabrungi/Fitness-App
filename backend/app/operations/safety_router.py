from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.activities.service import athlete_id
from backend.app.core.database import get_session
from backend.app.core.encryption import encrypt_json
from backend.app.core.security import current_user_id, hash_secret, random_token
from .models import LiveLocationSession

router = APIRouter(prefix="/safety/live-location", tags=["safety"])


@router.post("", status_code=201)
async def create(body: dict, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete=await athlete_id(session,user_id); raw=random_token(32); now=datetime.now(timezone.utc); expires=now+timedelta(hours=min(24,max(1,int(body.get("duration_hours",4)))));row=LiveLocationSession(athlete_id=athlete,share_token_hash=hash_secret(raw,purpose="live-location"),expires_at=expires);session.add(row);await session.commit();return {"id":row.id,"share_url":f"https://app.runlete.com/live/{raw}","expires_at":expires}


@router.put("/{session_id}", status_code=204)
async def update(session_id: UUID, body: dict, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    athlete=await athlete_id(session,user_id);row=await session.scalar(select(LiveLocationSession).where(LiveLocationSession.id==session_id,LiveLocationSession.athlete_id==athlete,LiveLocationSession.stopped_at.is_(None)).with_for_update())
    if row:
        envelope=await encrypt_json({"latitude":body.get("latitude"),"longitude":body.get("longitude"),"accuracy_m":body.get("accuracy_m"),"timestamp":body.get("timestamp")},aad=f"live:{row.id}".encode());row.location_ciphertext=envelope.ciphertext;row.wrapped_dek=envelope.wrapped_dek;row.kms_key_version=envelope.key_version;row.last_published_at=datetime.now(timezone.utc);await session.commit()


@router.delete("/{session_id}", status_code=204)
async def stop(session_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    athlete=await athlete_id(session,user_id);row=await session.scalar(select(LiveLocationSession).where(LiveLocationSession.id==session_id,LiveLocationSession.athlete_id==athlete).with_for_update())
    if row: row.stopped_at=datetime.now(timezone.utc);await session.commit()

