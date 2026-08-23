from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.core.config import get_settings
from backend.app.core.encryption import encrypt_json
from backend.app.core.ids import uuid7
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from backend.app.core.storage import signed_gcs_url

from backend.app.activities.models import Activity, UploadChunk
from backend.app.athletes.models import AthleteProfile
from backend.app.competition.models import ClubMembership, TerritoryCurrentControl, TerritoryScore
from backend.app.maps.models import HiddenMapZone, MatchedEdgeTraversal
from backend.app.operations.outbox import enqueue_event
from backend.app.operations.models import Job

from .models import AccountDeletionRequest, ConsentRecord, PrivacySettings, RefreshSession, User
from .schemas import (
    OTPRequest,
    OTPRequestResult,
    OTPVerify,
    HiddenZoneCreate,
    HiddenZoneView,
    AccountDeletionCommand,
    AccountDeletionView,
    DataExportView,
    PrivacyUpdate,
    PrivacyView,
    ProfileUpdate,
    RefreshRequest,
    TokenPair,
    UserView,
    SessionView,
    ConsentUpdate,
)
from .service import get_user_view, request_otp, rotate_refresh, verify_otp

router = APIRouter(prefix="/auth", tags=["identity"])
privacy_router = APIRouter(prefix="/privacy", tags=["privacy"])


@privacy_router.get("/consents")
async def list_consents(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> dict:
    rows = (
        await session.scalars(
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .order_by(ConsentRecord.recorded_at.desc(), ConsentRecord.id.desc())
        )
    ).all()
    latest: dict[str, ConsentRecord] = {}
    for row in rows:
        latest.setdefault(row.consent_type, row)
    return {"items": [{"consent_type": row.consent_type, "policy_version": row.policy_version, "granted": row.granted, "recorded_at": row.recorded_at} for row in latest.values()]}


@privacy_router.post("/consents", status_code=201)
async def record_consent(
    body: ConsentUpdate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    row = ConsentRecord(
        user_id=user_id,
        consent_type=body.consent_type,
        policy_version=body.policy_version,
        granted=body.granted,
        recorded_at=datetime.now(timezone.utc),
        metadata_json={"source": "authenticated_user"},
    )
    session.add(row)
    await session.commit()
    return {"id": row.id, "consent_type": row.consent_type, "policy_version": row.policy_version, "granted": row.granted, "recorded_at": row.recorded_at}


async def _athlete_profile_id(session: AsyncSession, user_id: UUID) -> UUID:
    athlete_id = await session.scalar(select(AthleteProfile.id).where(AthleteProfile.user_id == user_id))
    if athlete_id is None:
        raise ProblemError(409, "athlete_profile_missing", "Athlete profile required", "Complete onboarding before configuring location privacy.")
    return athlete_id


async def _invalidate_location_derivatives(session: AsyncSession, athlete_id: UUID) -> None:
    activity_ids = list(
        await session.scalars(select(Activity.id).where(Activity.athlete_id == athlete_id))
    )
    if not activity_ids:
        return
    traversals = (
        await session.scalars(
            select(MatchedEdgeTraversal).where(MatchedEdgeTraversal.activity_id.in_(activity_ids))
        )
    ).all()
    traversal_ids = [row.id for row in traversals]
    edge_ids = sorted({row.edge_id for row in traversals}, key=str)
    if traversal_ids:
        await session.execute(delete(TerritoryScore).where(TerritoryScore.traversal_id.in_(traversal_ids)))
        await session.execute(delete(MatchedEdgeTraversal).where(MatchedEdgeTraversal.id.in_(traversal_ids)))
    if edge_ids:
        # Drop stale winners immediately. Reprocessing repopulates deterministic controls.
        await session.execute(delete(TerritoryCurrentControl).where(TerritoryCurrentControl.edge_id.in_(edge_ids)))
    await session.execute(
        update(Activity)
        .where(Activity.id.in_(activity_ids))
        .values(public_route_geometry=None)
    )
    reprocessable = list(
        await session.scalars(
            select(Activity.id)
            .join(UploadChunk, UploadChunk.activity_id == Activity.id)
            .where(Activity.id.in_(activity_ids), Activity.status.in_(["complete", "rejected"]))
            .distinct()
        )
    )
    for activity_id in reprocessable:
        activity = await session.get(Activity, activity_id)
        if activity is None:
            continue
        activity.status = "uploaded"
        activity.rejection_code = None
        activity.processing_error_code = None
        activity.version += 1
        await enqueue_event(
            session,
            topic="activity",
            event_type="activity.uploaded",
            aggregate_type="activity",
            aggregate_id=activity.id,
            payload={"activity_id": str(activity.id), "reason": "hidden_zone_changed"},
        )


@router.post("/otp/request", response_model=OTPRequestResult, status_code=202)
async def request_code(
    body: OTPRequest, request: Request, session: AsyncSession = Depends(get_session)
) -> OTPRequestResult:
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
    return await request_otp(session, body, ip_hash)


@router.post("/otp/verify", response_model=TokenPair)
async def verify_code(
    body: OTPVerify, request: Request, session: AsyncSession = Depends(get_session)
) -> TokenPair:
    return await verify_otp(session, body, user_agent=request.headers.get("user-agent"))


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest, request: Request, session: AsyncSession = Depends(get_session)
) -> TokenPair:
    return await rotate_refresh(
        session,
        body.refresh_token,
        device_name=body.device_name,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/logout", status_code=204)
async def logout(
    refresh_token: str = Header(alias="X-Refresh-Token"),
    session: AsyncSession = Depends(get_session),
) -> Response:
    from backend.app.core.security import hash_secret

    item = await session.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_secret(refresh_token, purpose="refresh")
        )
    )
    if item:
        from datetime import datetime, timezone

        item.revoked_at = datetime.now(timezone.utc)
        await session.commit()
    return Response(status_code=204)


@router.get("/sessions", response_model=list[SessionView])
async def sessions(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> list[SessionView]:
    rows = (
        await session.scalars(
            select(RefreshSession)
            .where(RefreshSession.user_id == user_id)
            .order_by(RefreshSession.created_at.desc())
        )
    ).all()
    return [SessionView.model_validate(row, from_attributes=True) for row in rows]


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(
    session_id: UUID,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    row = await session.scalar(
        select(RefreshSession)
        .where(RefreshSession.id == session_id, RefreshSession.user_id == user_id)
        .with_for_update()
    )
    if row is None:
        raise ProblemError(404, "session_not_found", "Session not found", "The device session does not exist.")
    row.revoked_at = datetime.now(timezone.utc)
    await session.commit()
    return Response(status_code=204)


@router.post("/logout-all", status_code=204)
async def logout_all(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> Response:
    await session.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    await session.commit()
    return Response(status_code=204)


@router.get("/me", response_model=UserView)
async def me(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> UserView:
    return await get_user_view(session, user_id)


@router.patch("/me", response_model=UserView)
async def update_me(
    body: ProfileUpdate,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> UserView:
    user = await session.get(User, user_id, with_for_update=True)
    if user is None:
        raise ProblemError(404, "user_not_found", "User not found", "The user does not exist.")
    if user.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the profile and try again.")
    if body.display_name is not None:
        user.display_name = body.display_name.strip()
    if body.birth_date is not None:
        today = datetime.now(timezone.utc).date()
        age = today.year - body.birth_date.year - ((today.month, today.day) < (body.birth_date.month, body.birth_date.day))
        if age < 16:
            raise ProblemError(403, "minimum_age", "Minimum age", "Runlete is available to athletes aged 16 and above.")
        user.birth_date = body.birth_date
        if age < 18:
            privacy = await session.scalar(select(PrivacySettings).where(PrivacySettings.user_id == user_id).with_for_update())
            if privacy:
                privacy.default_activity_visibility = "private"
                privacy.public_leaderboards = False
                privacy.profile_discoverable = False
                privacy.version += 1
    user.version += 1
    await session.commit()
    return await get_user_view(session, user_id)


@privacy_router.get("", response_model=PrivacyView)
async def get_privacy(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> PrivacyView:
    item = await session.scalar(select(PrivacySettings).where(PrivacySettings.user_id == user_id))
    if item is None:
        raise ProblemError(404, "privacy_not_found", "Privacy settings not found", "Privacy settings are unavailable.")
    return PrivacyView.model_validate(item, from_attributes=True)


@privacy_router.patch("", response_model=PrivacyView)
async def update_privacy(
    body: PrivacyUpdate,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PrivacyView:
    item = await session.scalar(
        select(PrivacySettings).where(PrivacySettings.user_id == user_id).with_for_update()
    )
    if item is None:
        raise ProblemError(404, "privacy_not_found", "Privacy settings not found", "Privacy settings are unavailable.")
    if item.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload privacy settings and try again.")
    user = await session.get(User, user_id)
    today = datetime.now(timezone.utc).date()
    age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month, user.birth_date.day)) if user and user.birth_date else None
    requested = body.model_dump(exclude={"expected_version"}, exclude_none=True)
    if age is not None and age < 18 and (
        requested.get("default_activity_visibility") not in {None, "private"}
        or requested.get("public_leaderboards") is True
        or requested.get("profile_discoverable") is True
    ):
        raise ProblemError(403, "minor_privacy_restricted", "Privacy setting unavailable", "Public activity and profile visibility are unavailable for minors.")
    for field, value in requested.items():
        setattr(item, field, value)
    item.version += 1
    await session.commit()
    return PrivacyView.model_validate(item, from_attributes=True)


@privacy_router.get("/hidden-zones", response_model=list[HiddenZoneView])
async def list_hidden_zones(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> list[HiddenZoneView]:
    athlete_id = await _athlete_profile_id(session, user_id)
    rows = (
        await session.scalars(
            select(HiddenMapZone)
            .where(HiddenMapZone.athlete_id == athlete_id)
            .order_by(HiddenMapZone.created_at)
        )
    ).all()
    return [HiddenZoneView.model_validate(row, from_attributes=True) for row in rows]


@privacy_router.post("/hidden-zones", response_model=HiddenZoneView, status_code=201)
async def create_hidden_zone(
    body: HiddenZoneCreate,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> HiddenZoneView:
    athlete_id = await _athlete_profile_id(session, user_id)
    zone_id = uuid7()
    envelope = await encrypt_json(
        {"latitude": body.latitude, "longitude": body.longitude},
        aad=f"hidden-zone:{zone_id}".encode(),
    )
    row = HiddenMapZone(
        id=zone_id,
        athlete_id=athlete_id,
        label=body.label.strip(),
        radius_m=body.radius_m,
        geometry_encrypted=envelope.ciphertext,
        wrapped_dek=envelope.wrapped_dek,
        kms_key_version=envelope.key_version,
    )
    session.add(row)
    privacy = await session.scalar(
        select(PrivacySettings).where(PrivacySettings.user_id == user_id).with_for_update()
    )
    if privacy is not None and row.id not in privacy.hidden_zone_ids:
        privacy.hidden_zone_ids = [*privacy.hidden_zone_ids, row.id]
        privacy.version += 1
    await _invalidate_location_derivatives(session, athlete_id)
    await session.commit()
    return HiddenZoneView.model_validate(row, from_attributes=True)


@privacy_router.delete("/hidden-zones/{zone_id}", status_code=204)
async def delete_hidden_zone(
    zone_id: UUID,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    athlete_id = await _athlete_profile_id(session, user_id)
    row = await session.scalar(
        select(HiddenMapZone)
        .where(HiddenMapZone.id == zone_id, HiddenMapZone.athlete_id == athlete_id)
        .with_for_update()
    )
    if row is None:
        raise ProblemError(404, "hidden_zone_not_found", "Hidden zone not found", "The hidden zone does not exist.")
    await session.delete(row)
    privacy = await session.scalar(
        select(PrivacySettings).where(PrivacySettings.user_id == user_id).with_for_update()
    )
    if privacy is not None:
        privacy.hidden_zone_ids = [item for item in privacy.hidden_zone_ids if item != zone_id]
        privacy.version += 1
    await _invalidate_location_derivatives(session, athlete_id)
    await session.commit()
    return Response(status_code=204)


@privacy_router.get("/account-deletion", response_model=AccountDeletionView | None)
async def account_deletion_status(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> AccountDeletionView | None:
    row = await session.scalar(
        select(AccountDeletionRequest)
        .where(
            AccountDeletionRequest.user_id == user_id,
            AccountDeletionRequest.status.in_(["pending", "processing", "blocked"]),
        )
        .order_by(AccountDeletionRequest.requested_at.desc())
    )
    return AccountDeletionView.model_validate(row, from_attributes=True) if row else None


@privacy_router.post("/account-deletion", response_model=AccountDeletionView, status_code=202)
async def request_account_deletion(
    body: AccountDeletionCommand,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> AccountDeletionView:
    user = await session.get(User, user_id, with_for_update=True)
    if user is None:
        raise ProblemError(404, "user_not_found", "User not found", "The user does not exist.")
    if user.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the account and try again.")
    existing = await session.scalar(
        select(AccountDeletionRequest)
        .where(
            AccountDeletionRequest.user_id == user_id,
            AccountDeletionRequest.status.in_(["pending", "processing", "blocked"]),
        )
        .with_for_update()
    )
    if existing:
        return AccountDeletionView.model_validate(existing, from_attributes=True)
    athlete_id = await _athlete_profile_id(session, user_id)
    owns_club = await session.scalar(
        select(ClubMembership.id).where(
            ClubMembership.athlete_id == athlete_id,
            ClubMembership.status == "active",
            ClubMembership.role == "owner",
        )
    )
    if owns_club:
        raise ProblemError(
            409,
            "club_ownership_transfer_required",
            "Transfer club ownership",
            "Transfer or archive every club you own before deleting the account.",
        )
    now = datetime.now(timezone.utc)
    row = AccountDeletionRequest(
        user_id=user_id,
        status="pending",
        requested_at=now,
        execute_after=now + timedelta(days=7),
    )
    session.add(row)
    user.version += 1
    await session.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    await session.commit()
    return AccountDeletionView.model_validate(row, from_attributes=True)


@privacy_router.delete("/account-deletion", status_code=204)
async def cancel_account_deletion(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> Response:
    row = await session.scalar(
        select(AccountDeletionRequest)
        .where(AccountDeletionRequest.user_id == user_id, AccountDeletionRequest.status == "pending")
        .with_for_update()
    )
    if row is None:
        raise ProblemError(409, "deletion_not_cancellable", "Deletion cannot be cancelled", "There is no pending deletion request.")
    row.status = "cancelled"
    user = await session.get(User, user_id, with_for_update=True)
    if user:
        user.status = "active"
        user.version += 1
    await session.commit()
    return Response(status_code=204)


async def _export_view(job: Job) -> DataExportView:
    download_url = None
    expires_at = None
    if job.status == "complete" and job.output:
        settings = get_settings()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        download_url = await signed_gcs_url(
            project_id=settings.gcp_project_id,
            bucket=str(job.output["bucket"]),
            object_name=str(job.output["object_name"]),
            method="GET",
        )
    return DataExportView(
        id=job.id,
        status=job.status,
        requested_at=job.created_at,
        completed_at=job.completed_at,
        download_url=download_url,
        expires_at=expires_at,
    )


@privacy_router.post("/exports", response_model=DataExportView, status_code=202)
async def request_data_export(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> DataExportView:
    now = datetime.now(timezone.utc)
    active = await session.scalar(
        select(Job)
        .where(
            Job.owner_user_id == user_id,
            Job.job_type == "identity.data_export",
            Job.status.in_(["queued", "processing"]),
        )
        .order_by(Job.created_at.desc())
        .with_for_update()
    )
    if active:
        return await _export_view(active)
    job = Job(
        job_type="identity.data_export",
        status="queued",
        owner_user_id=user_id,
        input={"schema_version": 1},
        attempts=0,
        max_attempts=10,
        available_at=now,
    )
    session.add(job)
    await session.flush()
    await enqueue_event(
        session,
        topic="maintenance",
        event_type="identity.data_export.requested",
        aggregate_type="job",
        aggregate_id=job.id,
        payload={"job_id": str(job.id)},
    )
    await session.commit()
    return await _export_view(job)


@privacy_router.get("/exports", response_model=list[DataExportView])
async def list_data_exports(
    user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> list[DataExportView]:
    rows = (
        await session.scalars(
            select(Job)
            .where(Job.owner_user_id == user_id, Job.job_type == "identity.data_export")
            .order_by(Job.created_at.desc())
            .limit(20)
        )
    ).all()
    return [await _export_view(row) for row in rows]
