from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import anyio
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import AthleteProfile
from backend.app.competition.models import Club
from backend.app.core.config import get_settings
from backend.app.maps.models import MatchedEdgeTraversal, OSMGraphVersion, StreetEdge
from backend.app.maps.regions import UnsupportedMapRegion, valhalla_url_for_point
from backend.app.maps.privacy import hidden_zones_for_athlete, redact_start_and_end
from backend.app.maps.valhalla import MapMatchError, MatchResult, MatchedWay, match_trace
from backend.app.maps.segment_matching import replace_segment_efforts
from backend.app.moderation.models import CompetitionFlag
from backend.app.identity.models import User
from backend.app.operations.outbox import enqueue_event
from .models import (
    Activity,
    ActivityClubAttribution,
    ActivityQuality,
    ActivitySplit,
    ActivityStreamObject,
    BestEffort,
)
from .processing import Sample, best_efforts, calories_for_run, haversine_m, kilometre_splits, process_samples

COMPUTATION_VERSION = "activity-v3-device-smoothed-authority"
MATCHER_VERSION = "valhalla-confidence-v1"
CONFIRMATION_TOLERANCE_M = 25.0
CONFIRMATION_TOLERANCE_RATIO = 0.02


def _sample_dict(sample: Sample) -> dict:
    return {
        "latitude": sample.latitude,
        "longitude": sample.longitude,
        "timestamp": sample.timestamp.isoformat(),
        "accuracy": sample.accuracy,
        "altitude": sample.altitude,
        "speed": sample.speed,
        "heart_rate": sample.heart_rate,
        "cadence": sample.cadence,
        "smoothed_latitude": sample.smoothed_latitude,
        "smoothed_longitude": sample.smoothed_longitude,
    }


async def _store_cleaned(activity: Activity, samples: tuple[Sample, ...]) -> ActivityStreamObject:
    settings = get_settings()
    payload = gzip.compress(json.dumps({"schema_version": 1, "points": [_sample_dict(x) for x in samples]}, separators=(",", ":")).encode())
    digest = hashlib.sha256(payload).hexdigest()
    bucket = settings.raw_activity_bucket or "runlete-raw-local"
    name = f"activities/{activity.athlete_id}/{activity.id}/derived/{COMPUTATION_VERSION}/cleaned-{digest}.json.gz"

    def upload() -> None:
        from google.cloud import storage

        blob = storage.Client(project=settings.gcp_project_id or None).bucket(bucket).blob(name)
        blob.upload_from_string(payload, content_type="application/json")
        blob.content_encoding = "gzip"
        blob.metadata = {"sha256": digest, "computation_version": COMPUTATION_VERSION}
        blob.patch()

    await anyio.to_thread.run_sync(upload)
    return ActivityStreamObject(
        activity_id=activity.id,
        variant="cleaned",
        bucket=bucket,
        object_name=name,
        content_hash=digest,
        sample_count=len(samples),
        schema_version=1,
    )


def _raw_speed_evidence(samples: list[Sample]) -> tuple[str, str, int]:
    suspicious = 0
    for previous, current in zip(sorted(samples, key=lambda x: x.timestamp), sorted(samples, key=lambda x: x.timestamp)[1:]):
        seconds = (current.timestamp - previous.timestamp).total_seconds()
        if 2 <= seconds <= 120 and haversine_m(previous, current) / seconds > 12.5:
            suspicious += 1
    if suspicious >= 2:
        return "flagged", "flagged", suspicious
    return "passed", "passed", suspicious


async def _replace_metrics(session: AsyncSession, activity: Activity, raw_samples: list[Sample]) -> tuple[tuple[Sample, ...], ActivityQuality]:
    result = process_samples(raw_samples)
    athlete = await session.get(AthleteProfile, activity.athlete_id)
    speed_status, vehicle_status, suspicious = _raw_speed_evidence(raw_samples)
    reasons = list(result.reasons)
    if result.gps_score < 0.75:
        reasons.append("gps_quality_below_competition_threshold")
    if suspicious:
        reasons.append("sustained_implausible_speed")
    user = await session.get(User, athlete.user_id) if athlete else None
    age = None
    if user and user.birth_date:
        activity_day = activity.started_at.date()
        age = activity_day.year - user.birth_date.year - (
            (activity_day.month, activity_day.day) < (user.birth_date.month, user.birth_date.day)
        )
    competition_eligible = (
        result.gps_score >= 0.75
        and speed_status == "passed"
        and vehicle_status == "passed"
        and activity.visibility != "private"
        and (age is None or age >= 18)
    )
    if activity.visibility == "private":
        reasons.append("private_activity_not_competitive")
    if age is not None and age < 18:
        reasons.append("minor_competition_restricted")

    await session.execute(delete(ActivitySplit).where(ActivitySplit.activity_id == activity.id))
    await session.execute(delete(BestEffort).where(BestEffort.activity_id == activity.id))
    await session.execute(delete(ActivityQuality).where(ActivityQuality.activity_id == activity.id, ActivityQuality.computation_version == COMPUTATION_VERSION))
    for split in kilometre_splits(result.samples):
        session.add(ActivitySplit(activity_id=activity.id, split_type="kilometre", sequence=split.sequence, distance_m=split.distance_m, elapsed_seconds=split.elapsed_seconds))
    for effort in best_efforts(result.samples):
        previous = await session.scalar(
            select(func.min(BestEffort.elapsed_seconds)).where(
                BestEffort.athlete_id == activity.athlete_id,
                BestEffort.distance_code == effort.distance_code,
                BestEffort.quality_passed.is_(True),
                BestEffort.activity_id != activity.id,
            )
        )
        is_pr = previous is None or effort.elapsed_seconds < float(previous)
        if is_pr:
            await session.execute(
                update(BestEffort)
                .where(BestEffort.athlete_id == activity.athlete_id, BestEffort.distance_code == effort.distance_code)
                .values(is_personal_record=False)
            )
        session.add(
            BestEffort(
                activity_id=activity.id,
                athlete_id=activity.athlete_id,
                distance_code=effort.distance_code,
                distance_m=effort.distance_m,
                elapsed_seconds=effort.elapsed_seconds,
                start_offset_seconds=effort.start_offset_seconds,
                quality_passed=result.gps_score >= 0.75 and speed_status == "passed",
                is_personal_record=is_pr,
            )
        )

    coordinates = [[sample.longitude, sample.latitude] for sample in result.samples]
    geometry = func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps({"type": "LineString", "coordinates": coordinates})), 4326)
    activity.route_geometry = geometry
    activity.public_route_geometry = None
    if activity.visibility != "private":
        zones = await hidden_zones_for_athlete(session, activity.athlete_id)
        public_samples = redact_start_and_end(result.samples, zones)
        if public_samples:
            public_coordinates = [[sample.longitude, sample.latitude] for sample in public_samples]
            activity.public_route_geometry = func.ST_SetSRID(
                func.ST_GeomFromGeoJSON(
                    json.dumps({"type": "LineString", "coordinates": public_coordinates})
                ),
                4326,
            )
    activity.elapsed_seconds = result.elapsed_seconds
    activity.moving_seconds = result.moving_seconds
    activity.paused_seconds = result.paused_seconds
    # Distance remains the device-smoothed GPS metric. Server processing only
    # confirms it and records the small verification delta.
    if activity.device_distance_m is None:
        activity.device_distance_m = result.distance_m
    delta = result.distance_m - float(activity.device_distance_m)
    activity.server_confirmation_delta_m = delta
    allowed_delta = max(CONFIRMATION_TOLERANCE_M, float(activity.device_distance_m) * CONFIRMATION_TOLERANCE_RATIO)
    if abs(delta) > allowed_delta:
        reasons.append("server_metric_confirmation_outside_tolerance")
        # Never replace the number the athlete saw live. The server result is
        # retained only as evidence for diagnostics and reprocessing.
        result_distance = float(activity.device_distance_m)
    else:
        result_distance = result.distance_m
    activity.distance_m = result.distance_m
    activity.distance_m = result_distance
    activity.distance_source = "device_smoothed_gps"
    activity.elevation_source = "device_barometer_or_dem_pending"
    activity.elevation_gain_m = result.elevation_gain_m
    activity.average_pace_s_per_km = (
        result.moving_seconds / (result_distance / 1000)
        if result_distance > 0 and result.moving_seconds > 0 else None
    )
    activity.calories_kcal = calories_for_run(result.distance_m, float(athlete.weight_kg) if athlete and athlete.weight_kg else None)
    activity.average_hr = result.average_hr
    activity.average_cadence = result.average_cadence
    activity.computation_version = COMPUTATION_VERSION
    quality = ActivityQuality(
        activity_id=activity.id,
        computation_version=COMPUTATION_VERSION,
        gps_score=result.gps_score,
        duplicate_status="passed",
        speed_status=speed_status,
        vehicle_status=vehicle_status,
        matcher_confidence=None,
        competition_eligible=competition_eligible,
        territory_eligible=False,
        reasons=sorted(set(reasons)),
    )
    session.add(quality)
    if suspicious:
        existing_flag = await session.scalar(
            select(CompetitionFlag).where(
                CompetitionFlag.subject_type == "activity",
                CompetitionFlag.subject_id == activity.id,
                CompetitionFlag.flag_code == "implausible_running_speed",
                CompetitionFlag.computation_version == COMPUTATION_VERSION,
            )
        )
        if existing_flag is None:
            session.add(
                CompetitionFlag(
                    subject_type="activity",
                    subject_id=activity.id,
                    athlete_id=activity.athlete_id,
                    flag_code="implausible_running_speed",
                    severity="high",
                    evidence_json={"suspicious_segment_count": suspicious},
                    computation_version=COMPUTATION_VERSION,
                    status="open",
                )
            )
    return result.samples, quality


async def _candidate_edges(session: AsyncSession, match: MatchResult, way: MatchedWay) -> list[tuple[StreetEdge, float]]:
    if way.end_shape_index <= way.begin_shape_index or way.end_shape_index >= len(match.path):
        return []
    coordinates = [[point["longitude"], point["latitude"]] for point in match.path[way.begin_shape_index : way.end_shape_index + 1]]
    if len(coordinates) < 2:
        return []
    path_json = json.dumps({"type": "LineString", "coordinates": coordinates})
    statement = text(
        """
        WITH matched AS (
          SELECT ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:path), 4326), 3857) AS geom
        )
        SELECT edge.id,
               LEAST(1.0, ST_Length(ST_Intersection(ST_Transform(edge.geometry, 3857), ST_Buffer(matched.geom, 12.0))) / NULLIF(edge.length_m, 0)) AS coverage
        FROM activity.street_edges edge
        JOIN activity.osm_graph_versions graph ON graph.id = edge.graph_version_id
        CROSS JOIN matched
        WHERE edge.osm_way_id = :way_id
          AND edge.running_accessible
          AND graph.status = 'active'
          AND ST_DWithin(ST_Transform(edge.geometry, 3857), matched.geom, 15.0)
        ORDER BY edge.id
        """
    )
    rows = (await session.execute(statement, {"path": path_json, "way_id": way.way_id})).all()
    output: list[tuple[StreetEdge, float]] = []
    for edge_id, coverage in rows:
        edge = await session.get(StreetEdge, edge_id)
        if edge is not None:
            output.append((edge, max(0.0, min(1.0, float(coverage or 0)))))
    return output


async def _replace_matches(session: AsyncSession, activity: Activity, samples: tuple[Sample, ...], quality: ActivityQuality) -> list[UUID]:
    if activity.surface == "track":
        quality.reasons = sorted(set(quality.reasons + ["map_matching_skipped_for_track_surface"]))
        quality.territory_eligible = False
        return []
    await session.execute(delete(MatchedEdgeTraversal).where(MatchedEdgeTraversal.activity_id == activity.id, MatchedEdgeTraversal.computation_version == MATCHER_VERSION))
    if not samples:
        raise MapMatchError("No cleaned samples are available for map matching")
    matching_samples = samples
    if activity.visibility != "private":
        matching_samples = redact_start_and_end(
            samples,
            await hidden_zones_for_athlete(session, activity.athlete_id),
        )
        if matching_samples is None:
            quality.reasons = sorted(set(quality.reasons + ["hidden_zone_prevents_competitive_geometry"]))
            quality.territory_eligible = False
            return []
    try:
        valhalla_url = await valhalla_url_for_point(
            session, matching_samples[0].latitude, matching_samples[0].longitude
        )
    except UnsupportedMapRegion as exc:
        raise MapMatchError(str(exc)) from exc
    match = await match_trace(valhalla_url, matching_samples)
    quality.matcher_confidence = match.confidence
    attribution = await session.scalar(select(ActivityClubAttribution).where(ActivityClubAttribution.activity_id == activity.id))
    timezone_name = "UTC"
    if attribution and attribution.club_id:
        club = await session.get(Club, attribution.club_id)
        if club:
            timezone_name = club.timezone
    else:
        athlete = await session.get(AthleteProfile, activity.athlete_id)
        if athlete:
            timezone_name = athlete.timezone
    try:
        local_date = activity.started_at.astimezone(ZoneInfo(timezone_name)).date()
    except ZoneInfoNotFoundError:
        local_date = activity.started_at.date()

    athlete_profile = await session.get(AthleteProfile, activity.athlete_id)
    user = await session.get(User, athlete_profile.user_id) if athlete_profile else None
    today = activity.started_at.date()
    age = None
    if user and user.birth_date:
        age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month, user.birth_date.day))
    activity_passes = (
        float(quality.gps_score) >= 0.75
        and quality.speed_status == "passed"
        and quality.vehicle_status == "passed"
        and match.confidence >= 0.85
        and activity.visibility != "private"
        and (age is None or age >= 18)
    )
    qualified_edges: list[UUID] = []
    sequence = 0
    for way in match.ways:
        for edge, coverage in await _candidate_edges(session, match, way):
            sequence += 1
            qualifies = activity_passes and coverage >= 0.80
            elapsed = max(1.0, float(activity.moving_seconds or 1) * float(edge.length_m) / max(float(activity.distance_m or 1), 1.0))
            session.add(
                MatchedEdgeTraversal(
                    activity_id=activity.id,
                    athlete_id=activity.athlete_id,
                    edge_id=edge.id,
                    graph_version_id=edge.graph_version_id,
                    sequence=sequence,
                    coverage=coverage,
                    confidence=match.confidence,
                    elapsed_seconds=elapsed,
                    speed_mps=float(edge.length_m) / elapsed,
                    traversed_at=activity.started_at,
                    local_date=local_date,
                    qualifies=qualifies,
                    computation_version=MATCHER_VERSION,
                )
            )
            if qualifies:
                qualified_edges.append(edge.id)
    quality.territory_eligible = bool(qualified_edges)
    if not activity_passes:
        if match.confidence < 0.85:
            quality.reasons = sorted(set(quality.reasons + ["matcher_confidence_below_threshold"]))
        if activity.visibility == "private":
            quality.reasons = sorted(set(quality.reasons + ["private_activity_not_competitive"]))
        if age is not None and age < 18:
            quality.reasons = sorted(set(quality.reasons + ["minor_competition_restricted"]))
    elif not qualified_edges:
        quality.reasons = sorted(set(quality.reasons + ["no_edge_met_coverage_threshold"]))
    return qualified_edges


async def process_activity_stream(session: AsyncSession, activity: Activity, raw_samples: list[Sample]) -> None:
    samples, quality = await _replace_metrics(session, activity, raw_samples)
    stream = await _store_cleaned(activity, samples)
    existing_stream = await session.scalar(
        select(ActivityStreamObject).where(
            ActivityStreamObject.bucket == stream.bucket,
            ActivityStreamObject.object_name == stream.object_name,
        )
    )
    if existing_stream is None:
        session.add(stream)
        await session.flush()
        existing_stream = stream
    activity.cleaned_stream_object_id = existing_stream.id
    activity.status = "provisional"
    activity.version += 1
    await session.commit()

    qualified_edges: list[UUID] = []
    try:
        qualified_edges = await _replace_matches(session, activity, samples, quality)
    except MapMatchError:
        quality.reasons = sorted(set(quality.reasons + ["map_matching_unavailable_or_failed"]))
        quality.territory_eligible = False
    await replace_segment_efforts(session, activity, samples, quality)
    activity.status = "complete"
    activity.version += 1
    await enqueue_event(
        session,
        topic="territory",
        event_type="activity.competition.ready",
        aggregate_type="activity",
        aggregate_id=activity.id,
        payload={"activity_id": str(activity.id), "edge_ids": [str(edge) for edge in sorted(set(qualified_edges), key=str)]},
    )
    await session.commit()
