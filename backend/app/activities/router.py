from datetime import datetime, timedelta, timezone
from uuid import UUID

import anyio
from fastapi import APIRouter, Depends, Header
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from backend.app.core.storage import signed_gcs_url
from backend.app.athletes.models import AthleteProfile
from backend.app.competition.models import CompetitiveProfile
from backend.app.competition.projection import release_activity_territory
from backend.app.identity.models import User
from backend.app.operations.outbox import enqueue_event
from backend.app.core.pagination import decode_cursor, encode_cursor
from backend.app.maps.models import MatchedEdgeTraversal, Segment, SegmentEffort, StreetEdge
from .models import Activity, ActivityClubAttribution, ActivityEdit, ActivityFeedback, ActivityQuality, ActivitySplit, ActivityStreamObject, BestEffort, ImportJob, UploadChunk
from .processing import calories_for_run
from .schemas import ActivityCropCommand, ActivityDetailView, ActivityEditCommand, ActivityFeedbackCommand, ActivityListPage, ActivityQualityView, ActivitySplitView, ActivityStart, ActivityTransition, ActivityView, BestEffortView, ChunkUploadRequest, ChunkUploadView, ManualActivityCreate, SegmentEffortView
from .service import athlete_id, start, transition, view

router = APIRouter(prefix="/activities", tags=["activities"])


async def _owned_activity(session: AsyncSession, user_id: UUID, activity_id: UUID, *, lock: bool = False) -> Activity:
    athlete = await athlete_id(session, user_id)
    query = select(Activity).where(Activity.id == activity_id, Activity.athlete_id == athlete)
    if lock:
        query = query.with_for_update()
    row = await session.scalar(query)
    if row is None:
        raise ProblemError(404, "activity_not_found", "Activity not found", "The activity does not exist.")
    return row


async def _assert_visibility_allowed(session: AsyncSession, user_id: UUID, visibility: str) -> None:
    if visibility == "private":
        return
    user = await session.get(User, user_id)
    today = datetime.now(timezone.utc).date()
    if user and user.birth_date:
        age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month, user.birth_date.day))
        if age < 18:
            raise ProblemError(403, "minor_privacy_restricted", "Privacy setting unavailable", "Public and club-visible activities are unavailable for minors.")


@router.get("", response_model=ActivityListPage)
async def list_activities(cursor: str | None = None, limit: int = 25, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ActivityListPage:
    athlete = await athlete_id(session, user_id)
    limit = max(1, min(limit, 100))
    query = select(Activity).where(Activity.athlete_id == athlete)
    if cursor:
        started_at, activity_id = decode_cursor(cursor)
        query = query.where(or_(Activity.started_at < started_at, and_(Activity.started_at == started_at, Activity.id < activity_id)))
    fetched = (await session.scalars(query.order_by(Activity.started_at.desc(), Activity.id.desc()).limit(limit + 1))).all()
    rows = fetched[:limit]
    return ActivityListPage(
        items=[await view(session, row) for row in rows],
        next_cursor=encode_cursor(rows[-1].started_at, rows[-1].id) if len(fetched) > limit else None,
    )


@router.get("/{activity_id}", response_model=ActivityDetailView)
async def get_activity(activity_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ActivityDetailView:
    row = await _owned_activity(session, user_id, activity_id)
    geometry_json = await session.scalar(select(func.ST_AsGeoJSON(row.route_geometry))) if row.route_geometry is not None else None
    route = []
    if geometry_json:
        import json

        route = [
            {"longitude": float(point[0]), "latitude": float(point[1])}
            for point in json.loads(geometry_json).get("coordinates", [])
        ]
    split_rows = (await session.scalars(select(ActivitySplit).where(ActivitySplit.activity_id == row.id).order_by(ActivitySplit.sequence))).all()
    effort_rows = (await session.scalars(select(BestEffort).where(BestEffort.activity_id == row.id).order_by(BestEffort.distance_m))).all()
    segment_rows = (
        await session.execute(
            select(SegmentEffort, Segment.name)
            .join(Segment, Segment.id == SegmentEffort.segment_id)
            .where(SegmentEffort.activity_id == row.id)
            .order_by(SegmentEffort.elapsed_seconds)
        )
    ).all()
    quality = await session.scalar(select(ActivityQuality).where(ActivityQuality.activity_id == row.id).order_by(ActivityQuality.created_at.desc()))
    attribution = await session.scalar(select(ActivityClubAttribution).where(ActivityClubAttribution.activity_id == row.id))
    roads_verified = await session.scalar(
        select(func.coalesce(func.sum(StreetEdge.length_m), 0))
        .join(MatchedEdgeTraversal, MatchedEdgeTraversal.edge_id == StreetEdge.id)
        .where(MatchedEdgeTraversal.activity_id == row.id, MatchedEdgeTraversal.qualifies.is_(True))
    )
    return ActivityDetailView(
        id=row.id, source=row.source, sport_type=row.sport_type, surface=row.surface, distance_source=row.distance_source,
        device_distance_m=float(row.device_distance_m) if row.device_distance_m is not None else None,
        server_confirmation_delta_m=float(row.server_confirmation_delta_m) if row.server_confirmation_delta_m is not None else None,
        elevation_source=row.elevation_source, status=row.status, visibility=row.visibility,
        title=row.title, started_at=row.started_at, ended_at=row.ended_at, elapsed_seconds=row.elapsed_seconds,
        moving_seconds=row.moving_seconds, paused_seconds=row.paused_seconds,
        distance_m=float(row.distance_m) if row.distance_m is not None else None,
        elevation_gain_m=float(row.elevation_gain_m) if row.elevation_gain_m is not None else None,
        average_pace_s_per_km=float(row.average_pace_s_per_km) if row.average_pace_s_per_km is not None else None,
        calories_kcal=float(row.calories_kcal) if row.calories_kcal is not None else None,
        average_hr=row.average_hr, average_cadence=float(row.average_cadence) if row.average_cadence is not None else None,
        route=route,
        splits=[ActivitySplitView(sequence=item.sequence, distance_m=float(item.distance_m), elapsed_seconds=float(item.elapsed_seconds), pace_s_per_km=float(item.elapsed_seconds) / (float(item.distance_m) / 1000) if float(item.distance_m) else None, elevation_delta_m=float(item.elevation_delta_m) if item.elevation_delta_m is not None else None, average_hr=item.average_hr) for item in split_rows],
        best_efforts=[BestEffortView(distance_code=item.distance_code, distance_m=float(item.distance_m), elapsed_seconds=float(item.elapsed_seconds), pace_s_per_km=float(item.elapsed_seconds) / (float(item.distance_m) / 1000), quality_passed=item.quality_passed, is_personal_record=item.is_personal_record) for item in effort_rows],
        segment_efforts=[SegmentEffortView(segment_id=item.segment_id, segment_name=name, elapsed_seconds=float(item.elapsed_seconds), coverage=float(item.coverage), quality_passed=item.quality_passed) for item, name in segment_rows],
        quality=ActivityQualityView(gps_score=float(quality.gps_score), duplicate_status=quality.duplicate_status, speed_status=quality.speed_status, vehicle_status=quality.vehicle_status, matcher_confidence=float(quality.matcher_confidence) if quality.matcher_confidence is not None else None, competition_eligible=quality.competition_eligible, territory_eligible=quality.territory_eligible, reasons=quality.reasons) if quality else None,
        attributed_club_id=attribution.club_id if attribution else None, roads_verified_m=float(roads_verified or 0),
        processing_message="Runlete is verifying GPS and road matches." if row.status in {"uploaded", "processing", "provisional"} else None,
        rejection_code=row.rejection_code, processing_error_code=row.processing_error_code,
        schema_version=row.schema_version, computation_version=row.computation_version, version=row.version,
    )


@router.post("", response_model=ActivityView, status_code=201)
async def create_activity(body: ActivityStart, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ActivityView:
    await _assert_visibility_allowed(session, user_id, body.visibility)
    return await start(session, user_id, body, source_identity=idempotency_key)


@router.post("/manual", response_model=ActivityView, status_code=201)
async def create_manual_activity(
    body: ManualActivityCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ActivityView:
    await _assert_visibility_allowed(session, user_id, body.visibility)
    athlete = await athlete_id(session, user_id)
    source = "treadmill" if body.treadmill else "manual"
    existing = await session.scalar(
        select(Activity).where(Activity.athlete_id == athlete, Activity.source == source, Activity.source_identity == idempotency_key)
    )
    if existing:
        if existing.athlete_id != athlete:
            raise ProblemError(409, "idempotency_conflict", "Request conflict", "This idempotency key belongs to another activity.")
        return await view(session, existing)
    profile = await session.get(AthleteProfile, athlete)
    pace = body.duration_seconds / (body.distance_m / 1000) if body.distance_m > 0 else None
    row = Activity(
        athlete_id=athlete,
        source=source,
        source_identity=idempotency_key,
        status="complete",
        surface="treadmill" if body.treadmill else "road",
        distance_source="manual_or_sensor",
        device_distance_m=body.distance_m,
        elevation_source=None,
        visibility=body.visibility,
        title=body.title,
        started_at=body.started_at,
        ended_at=body.started_at + timedelta(seconds=body.duration_seconds),
        elapsed_seconds=body.duration_seconds,
        moving_seconds=body.duration_seconds,
        paused_seconds=0,
        distance_m=body.distance_m,
        average_pace_s_per_km=pace,
        calories_kcal=calories_for_run(
            body.distance_m,
            float(profile.weight_kg) if profile and profile.weight_kg else None,
        ),
        computation_version="manual-v1",
    )
    session.add(row)
    await session.flush()
    competitive = await session.scalar(
        select(CompetitiveProfile).where(CompetitiveProfile.athlete_id == athlete)
    )
    session.add(
        ActivityClubAttribution(
            activity_id=row.id,
            athlete_id=athlete,
            club_id=competitive.primary_club_id if competitive else None,
            attributed_at=datetime.now(timezone.utc),
        )
    )
    session.add(
        ActivityQuality(
            activity_id=row.id,
            computation_version="manual-v1",
            gps_score=0,
            duplicate_status="passed",
            speed_status="not_applicable",
            vehicle_status="not_applicable",
            competition_eligible=False,
            territory_eligible=False,
            reasons=["manual_activity_not_competitive"],
        )
    )
    await session.commit()
    return await view(session, row)


@router.post("/{activity_id}/pause", response_model=ActivityView)
async def pause(activity_id: UUID, body: ActivityTransition, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ActivityView: return await transition(session, user_id, activity_id, "paused", body)


@router.post("/{activity_id}/resume", response_model=ActivityView)
async def resume(activity_id: UUID, body: ActivityTransition, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ActivityView: return await transition(session, user_id, activity_id, "recording", body)


@router.post("/{activity_id}/finish", response_model=ActivityView)
async def finish(activity_id: UUID, body: ActivityTransition, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ActivityView: return await transition(session, user_id, activity_id, "finishing", body)


@router.post("/{activity_id}/uploaded", response_model=ActivityView)
async def uploaded(activity_id: UUID, body: ActivityTransition, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ActivityView: return await transition(session, user_id, activity_id, "uploaded", body)


@router.post("/{activity_id}/chunks/upload-url", response_model=ChunkUploadView)
async def chunk_upload_url(activity_id: UUID, body: ChunkUploadRequest, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> ChunkUploadView:
    from backend.app.core.config import get_settings
    from backend.app.core.problems import ProblemError
    athlete = await athlete_id(session, user_id); activity = await session.scalar(select(Activity).where(Activity.id == activity_id, Activity.athlete_id == athlete))
    if activity is None: raise ProblemError(404, "activity_not_found", "Activity not found", "The activity does not exist.")
    settings = get_settings(); bucket = settings.raw_activity_bucket or "runlete-raw-local"; object_name = f"activities/{athlete}/{activity.id}/chunks/{body.chunk_number:06d}-{body.content_hash}.json"; expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    if settings.raw_activity_bucket:
        try:
            url = await signed_gcs_url(
                project_id=settings.gcp_project_id,
                bucket=bucket,
                object_name=object_name,
                method="PUT",
                content_type=body.content_type,
            )
        except Exception as exc: raise ProblemError(503, "storage_signing_failed", "Upload unavailable", "A signed upload URL could not be created.") from exc
    else: url = f"http://localhost:4443/upload/storage/v1/b/{bucket}/o?uploadType=media&name={object_name}"
    existing = await session.scalar(select(UploadChunk).where(UploadChunk.activity_id == activity.id, UploadChunk.chunk_number == body.chunk_number).with_for_update())
    if existing is None: session.add(UploadChunk(activity_id=activity.id, chunk_number=body.chunk_number, object_name=object_name, content_hash=body.content_hash, sample_count=body.sample_count))
    elif existing.content_hash != body.content_hash: raise ProblemError(409, "chunk_conflict", "Upload conflict", "This chunk number already has different content.")
    await session.commit(); return ChunkUploadView(chunk_number=body.chunk_number, object_name=object_name, upload_url=url, expires_at=expires)


@router.put("/{activity_id}/feedback", status_code=200)
async def feedback(activity_id: UUID, body: ActivityFeedbackCommand, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); activity = await session.scalar(select(Activity).where(Activity.id == activity_id, Activity.athlete_id == athlete))
    from backend.app.core.problems import ProblemError
    if activity is None: raise ProblemError(404, "activity_not_found", "Activity not found", "The activity does not exist.")
    row = await session.scalar(select(ActivityFeedback).where(ActivityFeedback.activity_id == activity_id).with_for_update())
    if row is None: row = ActivityFeedback(activity_id=activity_id, athlete_id=athlete, **body.model_dump()); session.add(row)
    else:
        for key, value in body.model_dump().items(): setattr(row, key, value)
        row.version += 1
    await session.commit(); return {"id": row.id, "saved": True}


async def _queue_reprocess(session: AsyncSession, row: Activity, reason: str) -> None:
    row.status = "processing" if row.source.startswith("import_") else "uploaded"
    row.rejection_code = None
    row.processing_error_code = None
    row.version += 1
    if row.source.startswith("import_"):
        import_job = await session.scalar(
            select(ImportJob).where(ImportJob.activity_id == row.id).with_for_update()
        )
        if import_job is None:
            raise ProblemError(409, "activity_source_unavailable", "Source unavailable", "The original import file is unavailable.")
        import_job.status = "queued"
        import_job.version += 1
        await enqueue_event(
            session,
            topic="activity",
            event_type="activity.import.requested",
            aggregate_type="import_job",
            aggregate_id=import_job.id,
            payload={"import_job_id": str(import_job.id), "reason": reason},
        )
    else:
        await enqueue_event(
            session,
            topic="activity",
            event_type="activity.uploaded",
            aggregate_type="activity",
            aggregate_id=row.id,
            payload={"activity_id": str(row.id), "reason": reason},
        )


@router.patch("/{activity_id}", response_model=ActivityView)
async def edit_activity(
    activity_id: UUID,
    body: ActivityEditCommand,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ActivityView:
    row = await _owned_activity(session, user_id, activity_id, lock=True)
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the activity and try again.")
    before = {"title": row.title, "visibility": row.visibility}
    changed_visibility = body.visibility is not None and body.visibility != row.visibility
    if body.visibility is not None:
        await _assert_visibility_allowed(session, user_id, body.visibility)
        row.visibility = body.visibility
    if body.title is not None:
        row.title = body.title.strip()
    session.add(
        ActivityEdit(
            activity_id=row.id,
            actor_user_id=user_id,
            edit_type="metadata",
            before_json=before,
            after_json={"title": row.title, "visibility": row.visibility},
            created_at=datetime.now(timezone.utc),
        )
    )
    row.version += 1
    await session.commit()
    if changed_visibility:
        await release_activity_territory(session, row.id)
        row = await _owned_activity(session, user_id, activity_id, lock=True)
        row.public_route_geometry = None
        quality = await session.scalar(
            select(ActivityQuality)
            .where(ActivityQuality.activity_id == row.id)
            .order_by(ActivityQuality.created_at.desc())
            .with_for_update()
        )
        if row.visibility == "private":
            if quality:
                quality.competition_eligible = False
                quality.territory_eligible = False
                quality.reasons = sorted(set(quality.reasons + ["private_activity_not_competitive"]))
            await enqueue_event(
                session,
                topic="competition",
                event_type="activity.competition.recompute",
                aggregate_type="activity",
                aggregate_id=row.id,
                payload={"activity_id": str(row.id), "athlete_id": str(row.athlete_id)},
            )
        elif row.source == "runlete" or row.source.startswith("import_"):
            await _queue_reprocess(session, row, "visibility_changed")
        await session.commit()
    return await view(session, row)


@router.post("/{activity_id}/crop", response_model=ActivityView, status_code=202)
async def crop_activity(
    activity_id: UUID,
    body: ActivityCropCommand,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ActivityView:
    row = await _owned_activity(session, user_id, activity_id, lock=True)
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the activity and try again.")
    if row.source != "runlete" and not row.source.startswith("import_"):
        raise ProblemError(409, "activity_crop_unavailable", "Crop unavailable", "Only GPS activities can be cropped.")
    if row.elapsed_seconds is not None and body.start_offset_seconds + body.end_offset_seconds >= row.elapsed_seconds:
        raise ProblemError(422, "activity_crop_invalid", "Invalid crop", "The crop must leave part of the activity.")
    session.add(
        ActivityEdit(
            activity_id=row.id,
            actor_user_id=user_id,
            edit_type="crop",
            before_json={},
            after_json=body.model_dump(exclude={"expected_version"}),
            created_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()
    await release_activity_territory(session, row.id)
    row = await _owned_activity(session, user_id, activity_id, lock=True)
    row.public_route_geometry = None
    await _queue_reprocess(session, row, "activity_cropped")
    await session.commit()
    return await view(session, row)


@router.post("/{activity_id}/reprocess", response_model=ActivityView, status_code=202)
async def reprocess_activity(
    activity_id: UUID,
    body: ActivityTransition,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ActivityView:
    row = await _owned_activity(session, user_id, activity_id, lock=True)
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the activity and try again.")
    if row.source != "runlete" and not row.source.startswith("import_"):
        raise ProblemError(409, "activity_reprocess_unavailable", "Reprocess unavailable", "This activity has no GPS stream.")
    await session.commit()
    await release_activity_territory(session, row.id)
    row = await _owned_activity(session, user_id, activity_id, lock=True)
    row.public_route_geometry = None
    await _queue_reprocess(session, row, "athlete_requested")
    await session.commit()
    return await view(session, row)


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: UUID,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    row = await _owned_activity(session, user_id, activity_id, lock=True)
    await session.commit()
    await release_activity_territory(session, row.id)
    row = await _owned_activity(session, user_id, activity_id, lock=True)
    attribution = await session.scalar(
        select(ActivityClubAttribution).where(ActivityClubAttribution.activity_id == row.id)
    )
    streams = (
        await session.scalars(select(ActivityStreamObject).where(ActivityStreamObject.activity_id == row.id))
    ).all()
    chunks = (await session.scalars(select(UploadChunk).where(UploadChunk.activity_id == row.id))).all()
    from backend.app.core.config import get_settings

    settings = get_settings()
    objects = {(item.bucket, item.object_name) for item in streams}
    if settings.raw_activity_bucket:
        objects.update((settings.raw_activity_bucket, item.object_name) for item in chunks)
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
    await enqueue_event(
        session,
        topic="competition",
        event_type="activity.competition.recompute",
        aggregate_type="activity",
        aggregate_id=row.id,
        payload={
            "activity_id": str(row.id),
            "athlete_id": str(row.athlete_id),
            "club_id": str(attribution.club_id) if attribution and attribution.club_id else None,
            "started_at": row.started_at.isoformat(),
            "deleted": True,
        },
    )
    await session.delete(row)
    await session.commit()
