from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from .config import get_settings
from .problems import ProblemError

bearer = HTTPBearer(auto_error=False)
LOCAL_ADMIN_USER_ID = UUID("0198f000-0000-7000-8000-000000000001")
LOCAL_ADMIN_ROLES = ["content_editor", "content_publisher", "moderator", "platform_admin"]


def hash_secret(value: str, *, purpose: str) -> str:
    settings = get_settings()
    return hmac.new(
        settings.otp_pepper.encode(), f"{purpose}:{value}".encode(), hashlib.sha256
    ).hexdigest()


def random_token(size: int = 32) -> str:
    return secrets.token_urlsafe(size)


def create_access_token(user_id: UUID, session_id: UUID, roles: list[str]) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "sid": str(session_id),
        "roles": roles,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except jwt.InvalidTokenError as exc:
        raise ProblemError(401, "invalid_token", "Invalid token", "Authentication is required.") from exc


async def current_claims(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    settings = get_settings()
    is_admin_studio_api = request.url.path.startswith(("/api/v1/admin", "/api/v1/moderation/admin"))
    if settings.admin_studio_open_access and is_admin_studio_api:
        return {
            "sub": str(LOCAL_ADMIN_USER_ID),
            "roles": LOCAL_ADMIN_ROLES,
            "local_admin_studio": True,
        }
    if credentials is None:
        raise ProblemError(401, "authentication_required", "Authentication required", "Sign in to continue.")
    return decode_access_token(credentials.credentials)


async def current_user_id(claims: dict[str, Any] = Depends(current_claims)) -> UUID:
    return UUID(claims["sub"])


def require_roles(*allowed: str):
    async def dependency(claims: dict[str, Any] = Depends(current_claims)) -> dict[str, Any]:
        if not set(claims.get("roles", [])) & set(allowed):
            raise ProblemError(403, "forbidden", "Forbidden", "You do not have permission for this action.")
        return claims

    return dependency
