from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from backend.app.core.database import SessionFactory
from backend.app.core.problems import ProblemError
from backend.app.core.security import decode_access_token

from .models import IdempotencyRecord


MAX_REPLAY_BODY_BYTES = 512 * 1024
PROCESSING_LEASE = timedelta(minutes=5)
RECORD_TTL = timedelta(hours=24)


def _problem(request: Request, status: int, code: str, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://api.runlete.com/problems/{code}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": request.url.path,
            "code": code,
        },
    )


def _actor_id(request: Request) -> UUID | None:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    try:
        return UUID(decode_access_token(authorization.removeprefix("Bearer ").strip())["sub"])
    except (ProblemError, ValueError, KeyError):
        return None


def _replay(record: IdempotencyRecord) -> Response:
    stored = record.response_body or {}
    body = base64.b64decode(stored.get("body_base64", ""))
    headers = dict(stored.get("headers") or {})
    headers["Idempotency-Replayed"] = "true"
    return Response(content=body, status_code=record.status_code or 200, headers=headers)


async def idempotency_middleware(request: Request, call_next) -> Response:
    key = request.headers.get("Idempotency-Key")
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"} or not request.url.path.startswith("/api/v1/"):
        return await call_next(request)
    actor_id = _actor_id(request)
    if actor_id is None:
        return await call_next(request)
    if not key:
        return _problem(
            request,
            400,
            "idempotency_key_required",
            "Idempotency key required",
            "Authenticated mutations require an Idempotency-Key header.",
        )
    if len(key) > 180:
        return _problem(request, 400, "idempotency_key_invalid", "Invalid idempotency key", "Idempotency-Key must be at most 180 characters.")

    body = await request.body()
    operation = f"{request.method}:{request.url.path}"
    digest = hashlib.sha256(
        b"\x00".join(
            (
                request.method.encode(),
                request.url.path.encode(),
                request.url.query.encode(),
                body,
            )
        )
    ).hexdigest()
    now = datetime.now(timezone.utc)
    record: IdempotencyRecord | None = None
    async with SessionFactory() as session:
        record = await session.scalar(
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.actor_id == actor_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.key == key,
            )
            .with_for_update()
        )
        if record:
            if record.request_hash != digest:
                return _problem(request, 409, "idempotency_conflict", "Idempotency conflict", "This key was already used with a different request.")
            if record.status_code is not None:
                return _replay(record)
            if record.created_at > now - PROCESSING_LEASE:
                return _problem(request, 409, "request_in_progress", "Request in progress", "The original request is still being processed.")
            record.created_at = now
            record.expires_at = now + RECORD_TTL
        else:
            record = IdempotencyRecord(
                actor_id=actor_id,
                operation=operation,
                key=key,
                request_hash=digest,
                created_at=now,
                expires_at=now + RECORD_TTL,
            )
            session.add(record)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return _problem(request, 409, "request_in_progress", "Request in progress", "A matching request is already being processed.")

    try:
        response = await call_next(request)
        response_body = b"".join([chunk async for chunk in response.body_iterator])
    except Exception:
        async with SessionFactory() as session:
            await session.execute(delete(IdempotencyRecord).where(IdempotencyRecord.id == record.id))
            await session.commit()
        raise

    safe_headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in {"content-length", "transfer-encoding", "connection"}
    }
    if response.status_code >= 500 or len(response_body) > MAX_REPLAY_BODY_BYTES:
        async with SessionFactory() as session:
            await session.execute(delete(IdempotencyRecord).where(IdempotencyRecord.id == record.id))
            await session.commit()
    else:
        async with SessionFactory() as session:
            stored = await session.get(IdempotencyRecord, record.id, with_for_update=True)
            if stored:
                stored.status_code = response.status_code
                stored.response_body = {
                    "body_base64": base64.b64encode(response_body).decode(),
                    "headers": safe_headers,
                }
                await session.commit()
    return Response(content=response_body, status_code=response.status_code, headers=safe_headers)
