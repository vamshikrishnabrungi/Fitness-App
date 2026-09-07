from __future__ import annotations

import base64
import gzip
import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

import anyio
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.imports import ActivityImportError, parse_activity_file
from backend.app.activities.models import (
    Activity,
    ActivityClubAttribution,
    ActivityEdit,
    ActivityStreamObject,
    ImportJob,
    UploadChunk,
)
from backend.app.athletes.models import AthleteProfile
from backend.app.activities.pipeline import process_activity_stream
from backend.app.activities.processing import Sample
from backend.app.nutrition.models import FoodAnalysis, FoodImage
from backend.app.maps.models import MatchedEdgeTraversal
from backend.app.nutrition.provider import OpenAIFoodAnalysisProvider
from backend.app.notifications.delivery import check_delivery_receipts, deliver_notification
from backend.app.competition.models import ClubMembership, CompetitiveProfile
from backend.app.competition.projection import project_activity_territory
from backend.app.competition.projection import release_activity_territory
from backend.app.competition.event_projection import project_domain_event
from backend.app.core.config import get_settings
from backend.app.core.database import get_session
from backend.app.core.storage import download_gcs_bytes
from backend.app.identity.models import AccountDeletionRequest, User
from backend.app.identity.exporter import build_user_export
from backend.app.operations.models import AuditEvent, IdempotencyRecord, Job
from backend.app.operations.outbox import enqueue_event
from backend.app.operations.publisher import publish_outbox_ids
from .models import ConsumerReceipt, OutboxEvent

router = APIRouter(prefix="/internal", include_in_schema=False)


async def _load_chunks(chunks: list[UploadChunk]) -> list[dict]:
    settings = get_settings()
    def download() -> list[dict]:
        from google.cloud import storage
        client = storage.Client(project=settings.gcp_project_id or None); output=[]
        for chunk in chunks:
            bucket = settings.raw_activity_bucket or "runlete-raw-local"
            content = client.bucket(bucket).blob(chunk.object_name).download_as_bytes()
            if hashlib.sha256(content).hexdigest() != chunk.content_hash:
                raise ValueError(f"chunk {chunk.chunk_number} content hash mismatch")
            value = json.loads(content)
            if value.get("sequence") != chunk.chunk_number or len(value.get("points") or []) != chunk.sample_count:
                raise ValueError(f"chunk {chunk.chunk_number} manifest mismatch")
            output.extend(value.get("points", []))
        return output
    return await anyio.to_thread.run_sync(download)


async def process_activity(session: AsyncSession, activity_id: UUID, *, force: bool = False) -> None:
    row = await session.get(Activity, activity_id, with_for_update=True)
    if row is None or (not force and row.status in {"complete", "rejected"}): return
    if force:
        await session.rollback()
        await release_activity_territory(session, activity_id)
        row = await session.get(Activity, activity_id, with_for_update=True)
        if row is None:
            return
    row.status = "processing"
    row.processing_error_code = None
    row.processing_attempts += 1
    row.version += 1
    await session.commit()
    chunks = (await session.scalars(select(UploadChunk).where(UploadChunk.activity_id == row.id).order_by(UploadChunk.chunk_number))).all()
    try:
        raw = await _load_chunks(chunks)
        samples = [Sample(latitude=float(x["latitude"]), longitude=float(x["longitude"]), timestamp=datetime.fromisoformat(str(x["timestamp"]).replace("Z", "+00:00")), accuracy=x.get("accuracy"), altitude=x.get("altitude"), barometric_altitude=x.get("barometric_altitude"), speed=x.get("speed"), heart_rate=x.get("heart_rate"), cadence=x.get("cadence"), smoothed_latitude=x.get("smoothed_latitude"), smoothed_longitude=x.get("smoothed_longitude")) for x in raw]
        crop = await session.scalar(
            select(ActivityEdit)
            .where(ActivityEdit.activity_id == row.id, ActivityEdit.edit_type == "crop")
            .order_by(ActivityEdit.created_at.desc())
        )
        if crop and samples:
            start_offset = int(crop.after_json.get("start_offset_seconds", 0))
            end_offset = int(crop.after_json.get("end_offset_seconds", 0))
            first = min(sample.timestamp for sample in samples) + timedelta(seconds=start_offset)
            last = max(sample.timestamp for sample in samples) - timedelta(seconds=end_offset)
            samples = [sample for sample in samples if first <= sample.timestamp <= last]
            if len(samples) < 2:
                raise ValueError("activity crop removed all usable samples")
        await process_activity_stream(session, row, samples)
    except Exception as exc:
        await session.rollback()
        row = await session.get(Activity, activity_id, with_for_update=True)
        if row is not None:
            # Infrastructure, object-storage and dependency failures are retriable.
            # A Pub/Sub dead-letter exhaustion path below performs the terminal rejection.
            # A failed historical reprocess must not hide a previously complete
            # activity; its last accepted facts remain visible until retry wins.
            row.status = "complete" if force else "uploaded"
            row.processing_error_code = type(exc).__name__[:80]
            row.version += 1
            await session.commit()
        raise


async def _download_import(job: ImportJob) -> bytes:
    settings = get_settings()

    def download() -> bytes:
        from google.cloud import storage

        blob = storage.Client(project=settings.gcp_project_id or None).bucket(job.bucket).blob(job.object_name)
        blob.reload()
        if int(blob.size or 0) != job.size_bytes:
            raise ActivityImportError("Uploaded file size does not match the import manifest")
        generation = (job.diagnostics_json or {}).get("object_generation")
        if generation is not None and int(blob.generation or 0) != int(generation):
            raise ActivityImportError("Uploaded file changed after completion")
        return blob.download_as_bytes(end=job.size_bytes - 1, if_generation_match=int(generation) if generation is not None else None)

    return await anyio.to_thread.run_sync(download)


async def process_activity_import(session: AsyncSession, import_job_id: UUID) -> None:
    job = await session.get(ImportJob, import_job_id, with_for_update=True)
    if job is None or job.status == "complete":
        return
    if job.status == "failed":
        return
    if job.status not in {"queued", "processing"}:
        raise ValueError("activity import is not ready for processing")
    job.status = "processing"
    job.processing_attempts += 1
    job.version += 1
    await session.commit()

    try:
        content = await _download_import(job)
        digest = hashlib.sha256(content).hexdigest()
        if len(content) != job.size_bytes:
            raise ActivityImportError("Uploaded file size does not match the import manifest")
        if digest != job.content_hash:
            raise ActivityImportError("Uploaded file hash does not match the import manifest")
        provider, samples = parse_activity_file(job.filename, content)
    except ActivityImportError as exc:
        await session.rollback()
        job = await session.get(ImportJob, import_job_id, with_for_update=True)
        if job is not None:
            job.status = "failed"
            job.diagnostics_json = {
                **(job.diagnostics_json or {}),
                "error_code": "activity_import_invalid",
                "message": str(exc),
            }
            job.version += 1
            await session.commit()
        return
    except Exception as exc:
        await session.rollback()
        job = await session.get(ImportJob, import_job_id, with_for_update=True)
        if job is not None:
            job.status = "queued"
            job.diagnostics_json = {
                **(job.diagnostics_json or {}),
                "error_code": type(exc).__name__[:80],
            }
            job.version += 1
            await session.commit()
        raise

    job = await session.get(ImportJob, import_job_id, with_for_update=True)
    if job is None:
        return
    crop = None
    if job.activity_id:
        crop = await session.scalar(
            select(ActivityEdit)
            .where(ActivityEdit.activity_id == job.activity_id, ActivityEdit.edit_type == "crop")
            .order_by(ActivityEdit.created_at.desc())
        )
    if crop:
        start_offset = int(crop.after_json.get("start_offset_seconds", 0))
        end_offset = int(crop.after_json.get("end_offset_seconds", 0))
        first = samples[0].timestamp + timedelta(seconds=start_offset)
        last = samples[-1].timestamp - timedelta(seconds=end_offset)
        samples = tuple(sample for sample in samples if first <= sample.timestamp <= last)
        if len(samples) < 2:
            job.status = "failed"
            job.diagnostics_json = {
                **(job.diagnostics_json or {}),
                "error_code": "activity_crop_invalid",
                "message": "The crop removed all usable imported samples.",
            }
            job.version += 1
            await session.commit()
            return
    activity = await session.scalar(
        select(Activity).where(
            Activity.athlete_id == job.athlete_id,
            Activity.source == f"import_{provider}",
            Activity.source_identity == job.content_hash,
        )
    )
    if activity is None:
        activity = Activity(
            athlete_id=job.athlete_id,
            source=f"import_{provider}",
            source_identity=job.content_hash,
            status="processing",
            visibility=str((job.diagnostics_json or {}).get("visibility", "private")),
            title=job.filename.rsplit(".", 1)[0][:160],
            started_at=samples[0].timestamp,
            ended_at=samples[-1].timestamp,
            processing_attempts=1,
        )
        session.add(activity)
        await session.flush()
        competitive = await session.scalar(
            select(CompetitiveProfile).where(CompetitiveProfile.athlete_id == job.athlete_id)
        )
        session.add(
            ActivityClubAttribution(
                activity_id=activity.id,
                athlete_id=job.athlete_id,
                club_id=competitive.primary_club_id if competitive else None,
                attributed_at=datetime.now(timezone.utc),
            )
        )
        raw_stream = ActivityStreamObject(
            activity_id=activity.id,
            variant="raw",
            bucket=job.bucket,
            object_name=job.object_name,
            content_hash=job.content_hash,
            sample_count=len(samples),
            schema_version=1,
        )
        session.add(raw_stream)
        await session.flush()
        activity.raw_stream_object_id = raw_stream.id
        await session.commit()
    try:
        await process_activity_stream(session, activity, list(samples))
    except Exception as exc:
        await session.rollback()
        job = await session.get(ImportJob, import_job_id, with_for_update=True)
        if job is not None:
            job.status = "queued"
            job.activity_id = activity.id
            job.diagnostics_json = {
                **(job.diagnostics_json or {}),
                "error_code": type(exc).__name__[:80],
            }
            job.version += 1
            await session.commit()
        raise
    job = await session.get(ImportJob, import_job_id, with_for_update=True)
    if job is not None:
        job.status = "complete"
        job.activity_id = activity.id
        job.diagnostics_json = {
            **(job.diagnostics_json or {}),
            "sample_count": len(samples),
            "source": f"import_{provider}",
        }
        job.version += 1
        await session.commit()


async def process_food_analysis(session: AsyncSession, analysis_id: UUID) -> None:
    row=await session.get(FoodAnalysis,analysis_id,with_for_update=True)
    if row is None or row.status in {"complete","failed"}:return
    image=await session.get(FoodImage,row.image_id)
    if image is None:
        raise ValueError("food image does not exist")
    row.status="processing";row.error_code=None;row.processing_attempts += 1;await session.commit()
    try:
        settings = get_settings()
        image_bytes = await download_gcs_bytes(
            project_id=settings.gcp_project_id,
            bucket=image.bucket,
            object_name=image.object_name,
            max_bytes=20 * 1024 * 1024,
            generation=image.object_generation,
        )
        if len(image_bytes) != image.size_bytes:
            raise ValueError("food image does not match the validated upload manifest")
        verified_hash = hashlib.sha256(image_bytes).hexdigest()
        image.content_hash = verified_hash
        row.source_object_hash = verified_hash
        output=await OpenAIFoodAnalysisProvider().analyze(
            image_bytes=image_bytes,
            content_type=image.content_type,
            content_hash=verified_hash,
        )
        row.result_json=output.result.model_dump(mode="json");row.confidence=output.result.overall_confidence;row.latency_ms=output.latency_ms;row.input_tokens=output.input_tokens;row.output_tokens=output.output_tokens;row.status="complete"
    except Exception as exc:
        row.status="queued";row.error_code=type(exc).__name__[:80];await session.commit();raise
    await session.commit()


async def process_account_deletion(session: AsyncSession, request_id: UUID) -> None:
    request_row = await session.get(AccountDeletionRequest, request_id, with_for_update=True)
    if request_row is None or request_row.status == "completed":
        return
    if request_row.user_id is None:
        request_row.status = "completed"
        request_row.completed_at = datetime.now(timezone.utc)
        await session.commit()
        return
    user = await session.get(User, request_row.user_id, with_for_update=True)
    if user is None:
        request_row.user_id = None
        request_row.status = "completed"
        request_row.completed_at = datetime.now(timezone.utc)
        await session.commit()
        return
    athlete = await session.scalar(
        select(AthleteProfile).where(AthleteProfile.user_id == user.id).with_for_update()
    )
    if athlete is not None:
        owns_club = await session.scalar(
            select(ClubMembership.id).where(
                ClubMembership.athlete_id == athlete.id,
                ClubMembership.status == "active",
                ClubMembership.role == "owner",
            )
        )
        if owns_club:
            request_row.status = "blocked"
            await session.commit()
            return

    objects: set[tuple[str, str]] = set()
    settings = get_settings()
    if athlete is not None:
        activity_ids = list(
            await session.scalars(select(Activity.id).where(Activity.athlete_id == athlete.id))
        )
        if activity_ids:
            streams = (
                await session.scalars(
                    select(ActivityStreamObject).where(ActivityStreamObject.activity_id.in_(activity_ids))
                )
            ).all()
            objects.update((row.bucket, row.object_name) for row in streams)
            chunks = (
                await session.scalars(select(UploadChunk).where(UploadChunk.activity_id.in_(activity_ids)))
            ).all()
            if settings.raw_activity_bucket:
                objects.update((settings.raw_activity_bucket, row.object_name) for row in chunks)
        images = (
            await session.scalars(select(FoodImage).where(FoodImage.athlete_id == athlete.id))
        ).all()
        objects.update((row.bucket, row.object_name) for row in images)
    jobs = (await session.scalars(select(Job).where(Job.owner_user_id == user.id))).all()
    for job in jobs:
        if job.output and job.output.get("bucket") and job.output.get("object_name"):
            objects.add((str(job.output["bucket"]), str(job.output["object_name"])))

    if objects:
        def delete_objects() -> None:
            from google.api_core.exceptions import NotFound
            from google.cloud import storage

            client = storage.Client(project=settings.gcp_project_id or None)
            for bucket, object_name in sorted(objects):
                try:
                    client.bucket(bucket).blob(object_name).delete()
                except NotFound:
                    continue

        await anyio.to_thread.run_sync(delete_objects)

    now = datetime.now(timezone.utc)
    audit_hash = hashlib.sha256(
        f"{user.id}:{request_row.requested_at.isoformat()}".encode()
    ).hexdigest()
    session.add(
        AuditEvent(
            actor_user_id=None,
            action="identity.account_deleted",
            subject_type="deleted_user_hash",
            subject_id=None,
            before=None,
            after={"audit_hash": audit_hash},
            request_id=None,
            created_at=now,
        )
    )
    request_row.user_id = None
    request_row.status = "completed"
    request_row.completed_at = now
    request_row.audit_hash = audit_hash
    await session.delete(user)
    await session.commit()


async def process_account_export(session: AsyncSession, job_id: UUID) -> None:
    job = await session.get(Job, job_id, with_for_update=True)
    if job is None or job.status in {"complete", "failed"}:
        return
    if job.owner_user_id is None:
        job.status = "failed"
        job.error_code = "export_owner_missing"
        await session.commit()
        return
    job.status = "processing"
    job.started_at = datetime.now(timezone.utc)
    job.attempts += 1
    await session.commit()
    settings = get_settings()
    try:
        payload = await build_user_export(session, job.owner_user_id)
        content = gzip.compress(json.dumps(payload, separators=(",", ":")).encode())
        digest = hashlib.sha256(content).hexdigest()
        bucket = settings.export_bucket or "runlete-exports-local"
        object_name = f"users/{job.owner_user_id}/exports/{job.id}-{digest}.json.gz"

        def upload() -> None:
            from google.cloud import storage

            blob = storage.Client(project=settings.gcp_project_id or None).bucket(bucket).blob(object_name)
            blob.upload_from_string(content, content_type="application/json")
            blob.content_encoding = "gzip"
            blob.metadata = {"sha256": digest, "schema_version": "1"}
            blob.patch()

        await anyio.to_thread.run_sync(upload)
        job.status = "complete"
        job.completed_at = datetime.now(timezone.utc)
        job.output = {
            "bucket": bucket,
            "object_name": object_name,
            "content_hash": digest,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }
        job.error_code = None
        await session.commit()
    except Exception as exc:
        await session.rollback()
        job = await session.get(Job, job_id, with_for_update=True)
        if job:
            job.status = "queued"
            job.error_code = type(exc).__name__[:80]
            await session.commit()
        raise


async def enqueue_graph_reprocessing(session: AsyncSession, event: OutboxEvent) -> None:
    old_graph_ids = [UUID(value) for value in event.payload.get("retired_graph_ids", [])]
    if not old_graph_ids:
        return
    query = (
        select(Activity.started_at, Activity.id)
        .join(MatchedEdgeTraversal, MatchedEdgeTraversal.activity_id == Activity.id)
        .where(
            MatchedEdgeTraversal.graph_version_id.in_(old_graph_ids),
            Activity.started_at >= datetime.now(timezone.utc) - timedelta(days=28),
        )
        .distinct()
    )
    after_started_at = event.payload.get("after_started_at")
    after_activity_id = event.payload.get("after_activity_id")
    if after_started_at and after_activity_id:
        cursor_time = datetime.fromisoformat(str(after_started_at).replace("Z", "+00:00"))
        cursor_id = UUID(str(after_activity_id))
        query = query.where(
            or_(Activity.started_at > cursor_time, and_(Activity.started_at == cursor_time, Activity.id > cursor_id))
        )
    rows = (await session.execute(query.order_by(Activity.started_at, Activity.id).limit(1_000))).all()
    for _, activity_id in rows:
        await enqueue_event(
            session,
            topic="activity",
            event_type="activity.reprocess.requested",
            aggregate_type="activity",
            aggregate_id=activity_id,
            payload={"activity_id": str(activity_id), "reason": "osm_graph_activated"},
        )
    if len(rows) == 1_000:
        last_started_at, last_activity_id = rows[-1]
        await enqueue_event(
            session,
            topic="maintenance",
            event_type="maps.graph.reprocess.continue",
            aggregate_type="osm_graph_version",
            aggregate_id=event.aggregate_id,
            payload={
                **event.payload,
                "after_started_at": last_started_at.isoformat(),
                "after_activity_id": str(last_activity_id),
            },
        )
    await session.commit()


@router.post("/pubsub/{topic}", status_code=204)
async def consume(topic: str, request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    envelope = await request.json()
    message = envelope.get("message", {})
    payload = json.loads(base64.b64decode(message.get("data", "")).decode() or "{}")
    event_id = UUID(payload["event_id"])
    consumer = f"{topic}-worker-v1"
    now = datetime.now(timezone.utc)
    receipt = await session.scalar(
        select(ConsumerReceipt)
        .where(ConsumerReceipt.event_id == event_id, ConsumerReceipt.consumer_code == consumer)
        .with_for_update()
    )
    if receipt and receipt.status == "complete":
        return Response(status_code=204)
    if receipt and receipt.status == "processing" and receipt.started_at > now - timedelta(minutes=5):
        # Never acknowledge a duplicate while another delivery owns the lease:
        # acknowledgement is message-wide and could otherwise suppress recovery
        # if the original worker dies before committing its receipt.
        return Response(status_code=409)
    if receipt is None:
        receipt = ConsumerReceipt(event_id=event_id, consumer_code=consumer, status="processing", started_at=now, attempts=1)
        session.add(receipt)
    else:
        receipt.status = "processing"
        receipt.started_at = now
        receipt.attempts += 1
        receipt.last_error = None
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return Response(status_code=409)
    try:
        event = await session.get(OutboxEvent, event_id)
        if event is None:
            raise ValueError("outbox event does not exist")
        if event.event_type == "activity.uploaded":
            await process_activity(session, event.aggregate_id)
        elif event.event_type == "activity.import.requested":
            await process_activity_import(session, event.aggregate_id)
        elif event.event_type == "activity.reprocess.requested":
            await process_activity(session, event.aggregate_id, force=True)
        elif event.event_type == "activity.competition.ready":
            await project_activity_territory(session, event.aggregate_id)
        elif event.event_type == "activity.competition.disqualified":
            await release_activity_territory(session, event.aggregate_id)
            await project_domain_event(session, event)
        elif event.event_type == "nutrition.food_analysis.requested":
            await process_food_analysis(session, event.aggregate_id)
        elif event.event_type == "identity.account_deletion.due":
            await process_account_deletion(session, event.aggregate_id)
        elif event.event_type == "identity.data_export.requested":
            await process_account_export(session, event.aggregate_id)
        elif topic in {"club", "competition"}:
            await project_domain_event(session, event)
        elif event.event_type == "notification.delivery.requested":
            await deliver_notification(session, event.aggregate_id)
        elif event.event_type in {"maps.graph.activated", "maps.graph.reprocess.continue"}:
            await enqueue_graph_reprocessing(session, event)
        # Other event types are deliberately acknowledged by their dedicated
        # consumer version only when that topic is wired below.
        receipt = await session.scalar(select(ConsumerReceipt).where(ConsumerReceipt.event_id == event_id, ConsumerReceipt.consumer_code == consumer).with_for_update())
        receipt.status = "complete"
        receipt.completed_at = datetime.now(timezone.utc)
        await session.commit()
    except Exception as exc:
        await session.rollback()
        receipt = await session.scalar(select(ConsumerReceipt).where(ConsumerReceipt.event_id == event_id, ConsumerReceipt.consumer_code == consumer).with_for_update())
        if receipt:
            receipt.status = "retry"
            receipt.last_error = type(exc).__name__
            if receipt.attempts >= 10:
                event = await session.get(OutboxEvent, event_id)
                if event and event.event_type == "activity.uploaded":
                    activity = await session.get(Activity, event.aggregate_id, with_for_update=True)
                    if activity and activity.status not in {"complete", "rejected"}:
                        activity.status = "rejected"
                        activity.rejection_code = "processing_retry_exhausted"
                        activity.processing_error_code = type(exc).__name__[:80]
                        activity.version += 1
                elif event and event.event_type == "activity.import.requested":
                    import_job = await session.get(ImportJob, event.aggregate_id, with_for_update=True)
                    if import_job and import_job.status != "complete":
                        import_job.status = "failed"
                        import_job.diagnostics_json = {
                            **(import_job.diagnostics_json or {}),
                            "error_code": "processing_retry_exhausted",
                        }
                        import_job.version += 1
                elif event and event.event_type == "nutrition.food_analysis.requested":
                    analysis = await session.get(FoodAnalysis, event.aggregate_id, with_for_update=True)
                    if analysis and analysis.status != "complete":
                        analysis.status = "failed"
                        analysis.error_code = "processing_retry_exhausted"
                elif event and event.event_type == "identity.account_deletion.due":
                    deletion = await session.get(AccountDeletionRequest, event.aggregate_id, with_for_update=True)
                    if deletion and deletion.status != "completed":
                        deletion.status = "blocked"
                elif event and event.event_type == "identity.data_export.requested":
                    export_job = await session.get(Job, event.aggregate_id, with_for_update=True)
                    if export_job and export_job.status != "complete":
                        export_job.status = "failed"
                        export_job.error_code = "processing_retry_exhausted"
            await session.commit()
        raise
    return Response(status_code=204)


@router.post("/maintenance/outbox", status_code=204)
async def publish_outbox(session: AsyncSession = Depends(get_session)) -> Response:
    event_ids = tuple(
        await session.scalars(
            select(OutboxEvent.id)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.created_at)
            .limit(100)
        )
    )
    await publish_outbox_ids(event_ids)
    return Response(status_code=204)


@router.post("/maintenance/account-deletions", status_code=204)
async def enqueue_due_account_deletions(
    session: AsyncSession = Depends(get_session),
) -> Response:
    now = datetime.now(timezone.utc)
    rows = (
        await session.scalars(
            select(AccountDeletionRequest)
            .where(
                AccountDeletionRequest.status == "pending",
                AccountDeletionRequest.execute_after <= now,
            )
            .order_by(AccountDeletionRequest.execute_after)
            .limit(100)
            .with_for_update(skip_locked=True)
        )
    ).all()
    for row in rows:
        row.status = "processing"
        await enqueue_event(
            session,
            topic="maintenance",
            event_type="identity.account_deletion.due",
            aggregate_type="account_deletion_request",
            aggregate_id=row.id,
            payload={"request_id": str(row.id)},
        )
    await session.commit()
    return Response(status_code=204)


@router.post("/maintenance/push-receipts", status_code=204)
async def reconcile_push_receipts(session: AsyncSession = Depends(get_session)) -> Response:
    await check_delivery_receipts(session)
    return Response(status_code=204)


@router.post("/maintenance/idempotency-retention", status_code=204)
async def purge_expired_idempotency(session: AsyncSession = Depends(get_session)) -> Response:
    from sqlalchemy import delete

    await session.execute(
        delete(IdempotencyRecord).where(IdempotencyRecord.expires_at <= datetime.now(timezone.utc))
    )
    await session.commit()
    return Response(status_code=204)
