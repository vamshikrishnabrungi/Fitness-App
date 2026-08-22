from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, Header
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id, hash_secret
from backend.app.core.encryption import encrypt_json
from backend.app.core.pagination import decode_cursor, encode_cursor
from .models import Notification, PushToken
from .schemas import PushTokenRegister

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(cursor: str | None = None, limit: int = 25, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    limit = max(1, min(limit, 100))
    query = select(Notification).where(Notification.recipient_user_id == user_id)
    if cursor:
        created_at, notification_id = decode_cursor(cursor)
        query = query.where(or_(Notification.created_at < created_at, and_(Notification.created_at == created_at, Notification.id < notification_id)))
    rows = (await session.scalars(query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit + 1))).all()
    page = rows[:limit]
    next_cursor = encode_cursor(page[-1].created_at, page[-1].id) if len(rows) > limit else None
    unread_count = await session.scalar(select(func.count()).select_from(Notification).where(Notification.recipient_user_id == user_id, Notification.read_at.is_(None)))
    return {"items": [{"id": row.id, "type": row.notification_type, "title": row.title, "body": row.body, "created_at": row.created_at, "read": row.read_at is not None, "payload": row.payload_json} for row in page], "next_cursor": next_cursor, "unread_count": int(unread_count or 0)}


@router.post("/{notification_id}/read", status_code=204)
async def read(notification_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    row = await session.scalar(select(Notification).where(Notification.id == notification_id, Notification.recipient_user_id == user_id).with_for_update())
    if row is None: raise ProblemError(404, "notification_not_found", "Notification not found", "The notification does not exist.")
    row.read_at = datetime.now(timezone.utc); await session.commit()


@router.post("/read-all", status_code=204)
async def read_all(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    await session.execute(update(Notification).where(Notification.recipient_user_id == user_id, Notification.read_at.is_(None)).values(read_at=datetime.now(timezone.utc)))
    await session.commit()


@router.post("/push-tokens", status_code=201)
async def register_token(body: PushTokenRegister, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    token = body.token
    digest = hash_secret(token, purpose="push")
    envelope = await encrypt_json({"token": token}, aad=f"push:{user_id}".encode())
    row = await session.scalar(select(PushToken).where(PushToken.token_hash == digest).with_for_update())
    if row is None:
        row = PushToken(user_id=user_id, platform=body.platform, token_hash=digest, encrypted_token=envelope.ciphertext, wrapped_dek=envelope.wrapped_dek, kms_key_version=envelope.key_version, active=True, created_at=datetime.now(timezone.utc))
        session.add(row)
    else:
        row.user_id = user_id; row.platform = body.platform; row.encrypted_token = envelope.ciphertext; row.wrapped_dek = envelope.wrapped_dek; row.kms_key_version = envelope.key_version; row.active = True
    await session.commit()
    return {"id": row.id, "platform": row.platform, "active": row.active}


@router.delete("/push-tokens/{token_id}", status_code=204)
async def unregister_token(token_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> None:
    row = await session.scalar(select(PushToken).where(PushToken.id == token_id, PushToken.user_id == user_id).with_for_update())
    if row is None:
        raise ProblemError(404, "push_token_not_found", "Push token not found", "The registered device token does not exist.")
    row.active = False
    await session.commit()
