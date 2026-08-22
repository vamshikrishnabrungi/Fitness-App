from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.core.ids import uuid7
from backend.app.core.problems import ProblemError
from backend.app.core.security import create_access_token, hash_secret, random_token

from .models import EmailIdentity, OTPChallenge, PrivacySettings, RefreshSession, User, UserRole
from .schemas import OTPRequest, OTPRequestResult, OTPVerify, TokenPair, UserView


def normalize_email(email: str) -> str:
    return email.strip().casefold()


async def _send_otp(email: str, code: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        if settings.is_production:
            raise ProblemError(503, "email_unavailable", "Email unavailable", "Email delivery is not configured.")
        return
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.resend_from,
                "to": [email],
                "subject": "Your Runlete sign-in code",
                "text": f"Your Runlete verification code is {code}. It expires in 10 minutes.",
            },
        )
        if response.status_code >= 300:
            raise ProblemError(503, "email_unavailable", "Email unavailable", "The sign-in email could not be sent.")


async def request_otp(session: AsyncSession, command: OTPRequest, ip_hash: str | None) -> OTPRequestResult:
    now = datetime.now(timezone.utc)
    normalized = normalize_email(str(command.email))
    recent = await session.scalar(
        select(OTPChallenge)
        .where(OTPChallenge.normalized_email == normalized, OTPChallenge.created_at > now - timedelta(minutes=1))
        .order_by(OTPChallenge.created_at.desc())
    )
    if recent:
        raise ProblemError(429, "otp_rate_limited", "Too many requests", "Wait before requesting another code.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = OTPChallenge(
        normalized_email=normalized,
        purpose=command.purpose,
        code_hash=hash_secret(code, purpose="otp"),
        expires_at=now + timedelta(minutes=10),
        requested_ip_hash=ip_hash,
        created_at=now,
    )
    session.add(challenge)
    await session.flush()
    await _send_otp(str(command.email), code)
    await session.commit()
    settings = get_settings()
    return OTPRequestResult(
        challenge_id=challenge.id,
        expires_at=challenge.expires_at,
        debug_code=code if settings.environment in {"development", "test"} else None,
    )


async def _roles(session: AsyncSession, user_id: UUID) -> list[str]:
    values = (await session.scalars(select(UserRole.role).where(UserRole.user_id == user_id))).all()
    return sorted(values or ["athlete"])


async def _user_view(session: AsyncSession, user: User) -> UserView:
    identity = await session.scalar(
        select(EmailIdentity).where(EmailIdentity.user_id == user.id, EmailIdentity.primary.is_(True))
    )
    if identity is None:
        raise ProblemError(500, "identity_incomplete", "Identity incomplete", "The account has no primary email.")
    return UserView(
        id=user.id,
        email=identity.email,
        display_name=user.display_name,
        birth_date=user.birth_date,
        onboarding_completed=user.onboarding_completed,
        roles=await _roles(session, user.id),
        version=user.version,
    )


async def _issue_pair(
    session: AsyncSession,
    user: User,
    *,
    family_id: UUID | None = None,
    device_name: str | None = None,
    user_agent: str | None = None,
) -> TokenPair:
    settings = get_settings()
    raw_refresh = random_token(48)
    refresh = RefreshSession(
        user_id=user.id,
        family_id=family_id or uuid7(),
        token_hash=hash_secret(raw_refresh, purpose="refresh"),
        device_name=device_name,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
    )
    session.add(refresh)
    await session.flush()
    roles = await _roles(session, user.id)
    access = create_access_token(user.id, refresh.id, roles)
    return TokenPair(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.access_token_minutes * 60,
        user=await _user_view(session, user),
    )


async def verify_otp(
    session: AsyncSession, command: OTPVerify, *, user_agent: str | None
) -> TokenPair:
    now = datetime.now(timezone.utc)
    challenge = await session.get(OTPChallenge, command.challenge_id, with_for_update=True)
    if challenge is None or challenge.normalized_email != normalize_email(str(command.email)):
        raise ProblemError(400, "otp_invalid", "Invalid code", "The verification code is invalid.")
    if challenge.consumed_at or challenge.expires_at <= now or challenge.attempt_count >= challenge.max_attempts:
        raise ProblemError(400, "otp_expired", "Code expired", "Request a new verification code.")
    challenge.attempt_count += 1
    if not secrets.compare_digest(challenge.code_hash, hash_secret(command.code, purpose="otp")):
        await session.commit()
        raise ProblemError(400, "otp_invalid", "Invalid code", "The verification code is invalid.")
    challenge.consumed_at = now
    identity = await session.scalar(
        select(EmailIdentity).where(EmailIdentity.normalized_email == challenge.normalized_email)
    )
    if identity:
        user = await session.get(User, identity.user_id)
        if user is None or user.status != "active":
            raise ProblemError(403, "account_unavailable", "Account unavailable", "This account is not active.")
        if identity.verified_at is None:
            identity.verified_at = now
    else:
        if challenge.purpose != "register":
            raise ProblemError(404, "account_not_found", "Account not found", "Register before signing in.")
        if not command.display_name or not command.birth_date:
            raise ProblemError(422, "registration_details_required", "Registration details required", "Name and birth date are required.")
        age = now.date().year - command.birth_date.year - (
            (now.date().month, now.date().day) < (command.birth_date.month, command.birth_date.day)
        )
        if age < 16:
            raise ProblemError(403, "minimum_age", "Minimum age", "Runlete is available to athletes aged 16 and above.")
        user = User(display_name=command.display_name, birth_date=command.birth_date)
        session.add(user)
        await session.flush()
        session.add(
            EmailIdentity(
                user_id=user.id,
                email=str(command.email),
                normalized_email=challenge.normalized_email,
                verified_at=now,
            )
        )
        session.add(UserRole(user_id=user.id, role="athlete", granted_at=now))
        is_minor = age < 18
        session.add(
            PrivacySettings(
                user_id=user.id,
                default_activity_visibility="private" if is_minor else "club",
                public_leaderboards=False,
                profile_discoverable=False,
            )
        )
    pair = await _issue_pair(
        session, user, device_name=command.device_name, user_agent=user_agent
    )
    user.last_seen_at = now
    await session.commit()
    return pair


async def rotate_refresh(
    session: AsyncSession,
    raw_token: str,
    *,
    device_name: str | None,
    user_agent: str | None,
) -> TokenPair:
    now = datetime.now(timezone.utc)
    token_hash = hash_secret(raw_token, purpose="refresh")
    old = await session.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash).with_for_update()
    )
    if old is None:
        raise ProblemError(401, "invalid_refresh_token", "Invalid session", "Sign in again.")
    if old.revoked_at is not None:
        await session.execute(
            update(RefreshSession)
            .where(RefreshSession.family_id == old.family_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.commit()
        raise ProblemError(401, "refresh_reuse", "Session revoked", "Sign in again.")
    if old.expires_at <= now:
        old.revoked_at = now
        await session.commit()
        raise ProblemError(401, "refresh_expired", "Session expired", "Sign in again.")
    user = await session.get(User, old.user_id)
    if user is None or user.status != "active":
        raise ProblemError(401, "account_unavailable", "Account unavailable", "Sign in again.")
    old.revoked_at = now
    old.last_used_at = now
    pair = await _issue_pair(
        session,
        user,
        family_id=old.family_id,
        device_name=device_name or old.device_name,
        user_agent=user_agent,
    )
    replacement = await session.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_secret(pair.refresh_token, purpose="refresh")
        )
    )
    old.replaced_by_id = replacement.id if replacement else None
    await session.commit()
    return pair


async def get_user_view(session: AsyncSession, user_id: UUID) -> UserView:
    user = await session.get(User, user_id)
    if user is None or user.status != "active":
        raise ProblemError(404, "user_not_found", "User not found", "The user does not exist.")
    return await _user_view(session, user)

