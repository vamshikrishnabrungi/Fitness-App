from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.core.database import get_session
from backend.app.core.pagination import decode_cursor, encode_cursor
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from backend.app.core.storage import signed_gcs_url
from backend.app.operations.outbox import enqueue_event
from backend.app.core.encryption import encrypt_json
from backend.app.health.models import HealthMetricRecord
from backend.app.identity.models import ConsentRecord

from .imports import SUPPORTED_EXTENSIONS
from .models import ImportJob, IntegrationConnection
from .router import _assert_visibility_allowed
from .schemas import HealthBatchCommand, ImportCompleteCommand, ImportUploadRequest, ImportUploadView
from .service import athlete_id

router = APIRouter(prefix="/imports", tags=["activity imports"])


@router.get("/connections")
async def list_connections(
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    rows = (
        await session.scalars(
            select(IntegrationConnection)
            .where(IntegrationConnection.athlete_id == athlete)
            .order_by(IntegrationConnection.provider)
        )
    ).all()
    return {"items": [{"provider": row.provider, "status": row.status, "revoked_at": row.revoked_at, "updated_at": row.updated_at} for row in rows]}


@router.delete("/connections/{provider}", status_code=204, response_class=Response)
async def revoke_connection(
    provider: str,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    if provider not in {"apple_health", "health_connect", "garmin", "coros", "polar", "suunto"}:
        raise ProblemError(422, "integration_provider_invalid", "Invalid provider", "Choose a supported integration provider.")
    athlete = await athlete_id(session, user_id)
    row = await session.scalar(
        select(IntegrationConnection)
        .where(IntegrationConnection.athlete_id == athlete, IntegrationConnection.provider == provider)
        .with_for_update()
    )
    if row is not None:
        row.status = "revoked"
        row.access_token_encrypted = None
        row.refresh_token_encrypted = None
        row.revoked_at = datetime.now(timezone.utc)
        row.version += 1
        await session.commit()
    return Response(status_code=204)


@router.post("/health/batches", status_code=202)
async def import_health_batch(
    body: HealthBatchCommand,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    consent = await session.scalar(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user_id, ConsentRecord.consent_type == "connected_health")
        .order_by(ConsentRecord.recorded_at.desc())
    )
    if consent is None or not consent.granted:
        raise ProblemError(403, "health_consent_required", "Consent required", "Enable connected-health consent before importing records.")
    existing_hashes = set(
        await session.scalars(
            select(HealthMetricRecord.provider_record_hash).where(
                HealthMetricRecord.athlete_id == athlete,
                HealthMetricRecord.provider == body.provider,
            )
        )
    )
    accepted = 0
    duplicates = 0
    for record in body.records:
        if record.ended_at < record.started_at:
            raise ProblemError(422, "health_record_time_invalid", "Invalid health record", "A record cannot end before it starts.")
        record_hash = hashlib.sha256(record.provider_record_id.encode()).hexdigest()
        if record_hash in existing_hashes:
            duplicates += 1
            continue
        envelope = await encrypt_json(
            {"value": record.value, "unit": record.unit, "source_name": record.source_name},
            aad=f"health-metric:{athlete}:{body.provider}:{record_hash}".encode(),
        )
        session.add(
            HealthMetricRecord(
                athlete_id=athlete,
                provider=body.provider,
                provider_record_hash=record_hash,
                metric_code=record.metric_code,
                started_at=record.started_at,
                ended_at=record.ended_at,
                payload_ciphertext=envelope.ciphertext,
                wrapped_dek=envelope.wrapped_dek,
                kms_key_version=envelope.key_version,
                source_metadata={"schema_version": 1},
            )
        )
        existing_hashes.add(record_hash)
        accepted += 1
    connection = await session.scalar(
        select(IntegrationConnection)
        .where(IntegrationConnection.athlete_id == athlete, IntegrationConnection.provider == body.provider)
        .with_for_update()
    )
    if connection is None:
        session.add(IntegrationConnection(athlete_id=athlete, provider=body.provider, status="active"))
    else:
        connection.status = "active"
        connection.revoked_at = None
        connection.version += 1
    await session.commit()
    return {"provider": body.provider, "accepted": accepted, "duplicates": duplicates}


@router.get("")
async def list_imports(
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    athlete = await athlete_id(session, user_id)
    query = select(ImportJob).where(ImportJob.athlete_id == athlete)
    if cursor:
        created_at, job_id = decode_cursor(cursor)
        query = query.where(or_(ImportJob.created_at < created_at, and_(ImportJob.created_at == created_at, ImportJob.id < job_id)))
    fetched = (
        await session.scalars(query.order_by(ImportJob.created_at.desc(), ImportJob.id.desc()).limit(limit + 1))
    ).all()
    rows = fetched[:limit]
    return {
        "items": [
            {
                "id": row.id,
                "filename": row.filename,
                "provider": row.provider,
                "status": row.status,
                "activity_id": row.activity_id,
                "diagnostics": row.diagnostics_json,
                "created_at": row.created_at,
                "version": row.version,
            }
            for row in rows
        ],
        "next_cursor": encode_cursor(rows[-1].created_at, rows[-1].id) if len(fetched) > limit else None,
    }


@router.post("/uploads", response_model=ImportUploadView, status_code=201)
async def create_import_upload(
    body: ImportUploadRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ImportUploadView:
    extension = Path(body.filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ProblemError(422, "activity_import_type_unsupported", "Unsupported file", "Choose a GPX, TCX or FIT file.")
    await _assert_visibility_allowed(session, user_id, body.visibility)
    athlete = await athlete_id(session, user_id)
    deduplication_key = f"file:{body.content_hash}"
    existing = await session.scalar(
        select(ImportJob).where(
            ImportJob.athlete_id == athlete,
            ImportJob.deduplication_key == deduplication_key,
        )
    )
    settings = get_settings()
    bucket = settings.import_bucket
    if settings.is_production and not bucket:
        raise ProblemError(503, "imports_storage_unavailable", "Imports unavailable", "The production import bucket is not configured.")
    bucket = bucket or "runlete-imports-local"
    now = datetime.now(timezone.utc)
    if existing:
        object_name = existing.object_name
        row = existing
    else:
        object_name = f"activities/{athlete}/imports/{body.content_hash}{extension}"
        row = ImportJob(
            athlete_id=athlete,
            provider=extension[1:],
            filename=body.filename,
            content_type=body.content_type,
            bucket=bucket,
            object_name=object_name,
            content_hash=body.content_hash,
            size_bytes=body.size_bytes,
            deduplication_key=deduplication_key,
            status="awaiting_upload",
            diagnostics_json={"visibility": body.visibility},
        )
        session.add(row)
        await session.flush()
    try:
        upload_url = (
            await signed_gcs_url(
                project_id=settings.gcp_project_id,
                bucket=bucket,
                object_name=object_name,
                method="PUT",
                content_type=body.content_type,
            )
            if settings.import_bucket
            else f"http://localhost:4443/upload/storage/v1/b/{bucket}/o?uploadType=media&name={object_name}"
        )
    except Exception as exc:
        raise ProblemError(503, "storage_signing_failed", "Upload unavailable", "A signed import upload URL could not be created.") from exc
    await session.commit()
    return ImportUploadView(
        id=row.id,
        status=row.status,
        object_name=row.object_name,
        upload_url=upload_url,
        expires_at=now + timedelta(minutes=15),
    )


@router.post("/{job_id}/complete", status_code=202)
async def complete_import(
    job_id: UUID,
    body: ImportCompleteCommand,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    row = await session.scalar(
        select(ImportJob)
        .where(ImportJob.id == job_id, ImportJob.athlete_id == athlete)
        .with_for_update()
    )
    if row is None:
        raise ProblemError(404, "import_not_found", "Import not found", "The import job does not exist.")
    if row.status in {"queued", "processing", "complete"}:
        return {"id": row.id, "status": row.status, "activity_id": row.activity_id, "version": row.version}
    if row.status != "awaiting_upload":
        raise ProblemError(409, "import_not_completable", "Import unavailable", "This import job cannot be completed.")
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the import and try again.")
    row.status = "queued"
    row.version += 1
    await enqueue_event(
        session,
        topic="activity",
        event_type="activity.import.requested",
        aggregate_type="import_job",
        aggregate_id=row.id,
        payload={"import_job_id": str(row.id)},
    )
    await session.commit()
    return {"id": row.id, "status": row.status, "activity_id": row.activity_id, "version": row.version}
