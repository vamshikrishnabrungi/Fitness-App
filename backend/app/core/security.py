from __future__ import annotations

import hashlib
import hmac
import secrets
import anyio
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_session
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
    claims = decode_access_token(credentials.credentials)
    try:
        UUID(str(claims["sub"])); UUID(str(claims["sid"]))
        roles = claims.get("roles", [])
        if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
            raise ValueError("invalid roles")
    except (KeyError, TypeError, ValueError) as exc:
        raise ProblemError(401, "invalid_token", "Invalid token", "Authentication is required.") from exc
    if is_admin_studio_api and settings.environment in {"staging", "production"}:
        assertion = request.headers.get("x-goog-iap-jwt-assertion", "")
        if not assertion:
            raise ProblemError(403, "iap_required", "Admin access denied", "Use the protected Admin Studio hostname.")

        def verify_iap() -> dict[str, Any]:
            from google.auth.transport.requests import Request as GoogleRequest
            from google.oauth2 import id_token

            return id_token.verify_token(assertion, GoogleRequest(), audience=settings.admin_iap_audience)

        try:
            iap_claims = await anyio.to_thread.run_sync(verify_iap)
        except Exception as exc:
            raise ProblemError(403, "invalid_iap_assertion", "Admin access denied", "The Admin Studio identity could not be verified.") from exc
        email = str(iap_claims.get("email", "")).strip().lower()
        if not email:
            raise ProblemError(403, "invalid_iap_identity", "Admin access denied", "The Admin Studio identity has no verified email.")
        claims["iap_email"] = email
    return claims


async def current_user_id(claims: dict[str, Any] = Depends(current_claims)) -> UUID:
    try:
        return UUID(str(claims["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ProblemError(401, "invalid_token", "Invalid token", "Authentication is required.") from exc


def require_roles(*allowed: str):
    async def dependency(
        claims: dict[str, Any] = Depends(current_claims),
        session: AsyncSession = Depends(get_session),
    ) -> dict[str, Any]:
        if claims.get("local_admin_studio"):
            return claims
        from backend.app.identity.models import EmailIdentity, RefreshSession, User, UserRole

        user_id = UUID(str(claims["sub"])); session_id = UUID(str(claims["sid"])); now = datetime.now(timezone.utc)
        user = await session.get(User, user_id)
        refresh = await session.get(RefreshSession, session_id)
        if user is None or user.status != "active" or refresh is None or refresh.user_id != user_id or refresh.revoked_at is not None or refresh.expires_at <= now:
            raise ProblemError(401, "session_inactive", "Session inactive", "Sign in again.")
        current_roles = set(await session.scalars(select(UserRole.role).where(UserRole.user_id == user_id)))
        iap_email = claims.get("iap_email")
        if iap_email:
            identity_user_id = await session.scalar(select(EmailIdentity.user_id).where(EmailIdentity.normalized_email == iap_email, EmailIdentity.verified_at.is_not(None)))
            if identity_user_id != user_id:
                raise ProblemError(403, "iap_identity_mismatch", "Admin access denied", "The Admin Studio identity does not match the signed-in account.")
        if not current_roles & set(allowed):
            raise ProblemError(403, "forbidden", "Forbidden", "You do not have permission for this action.")
        claims["roles"] = sorted(current_roles)
        return claims

    return dependency
