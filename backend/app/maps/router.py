from __future__ import annotations

import hashlib
import json
from datetime import date
from uuid import UUID

import httpx
import anyio
from fastapi import APIRouter, Depends, File, Header, Response, UploadFile
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.service import athlete_id
from backend.app.activities.models import Activity
from backend.app.athletes.models import AthleteProfile
from backend.app.core.database import get_session
from backend.app.core.pagination import decode_cursor, encode_cursor
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from backend.app.core.config import get_settings
from backend.app.identity.models import PrivacySettings, User

from .gpx import InvalidGPX, MAX_GPX_BYTES, parse_gpx, render_gpx
from .models import Route, Segment, SegmentEffort
from .polyline import InvalidPolyline, decode_polyline6
from .regions import UnsupportedMapRegion, valhalla_url_for_point
from .schemas import Coordinate, RouteCreate, RouteGenerate, RouteUpdate, SegmentCreate

router = APIRouter(tags=["maps"])


def _geometry(points: list[Coordinate]):
    coordinates = [[point.longitude, point.latitude] for point in points]
    return func.ST_SetSRID(
        func.ST_GeomFromGeoJSON(json.dumps({"type": "LineString", "coordinates": coordinates})),
        4326,
    )


async def _distance_m(session: AsyncSession, geometry) -> float:
    value = await session.scalar(
        select(func.ST_Length(func.ST_GeogFromText(func.ST_AsText(geometry))))
    )
    return float(value or 0)


def _points(geojson: str) -> list[Coordinate]:
    return [
        Coordinate(longitude=coordinate[0], latitude=coordinate[1])
        for coordinate in json.loads(geojson)["coordinates"]
    ]


async def _assert_public_allowed(session: AsyncSession, athlete: UUID, visibility: str) -> None:
    if visibility != "public":
        return
    user = await session.scalar(
        select(User).join(AthleteProfile, AthleteProfile.user_id == User.id).where(AthleteProfile.id == athlete)
    )
    if user and user.birth_date:
        today = date.today()
        age = today.year - user.birth_date.year - (
            (today.month, today.day) < (user.birth_date.month, user.birth_date.day)
        )
        if age < 18:
            raise ProblemError(403, "minor_map_privacy", "Public map unavailable", "Athletes under 18 cannot publish routes or segments.")


async def _owned_route(session: AsyncSession, route_id: UUID, athlete: UUID, *, lock: bool = False) -> Route:
    query = select(Route).where(Route.id == route_id, Route.owner_athlete_id == athlete)
    if lock:
        query = query.with_for_update()
    row = await session.scalar(query)
    if row is None:
        raise ProblemError(404, "route_not_found", "Route not found", "The route does not exist or is not owned by the athlete.")
    return row


def _route_view(row: Route, geojson: str) -> dict:
    path = _points(geojson)
    return {
        "id": row.id,
        "name": row.name,
        "source": row.source,
        "visibility": row.visibility,
        "distance_m": float(row.distance_m),
        "distance_km": float(row.distance_m) / 1000,
        "elevation_gain_m": float(row.elevation_gain_m or 0),
        "surface": max(row.surface_mix_json, key=row.surface_mix_json.get) if row.surface_mix_json else "unknown",
        "path": [point.model_dump(exclude_none=True) for point in path],
        "version": row.version,
    }


@router.get("/routes")
async def routes(
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    limit = max(1, min(limit, 100))
    athlete = await athlete_id(session, user_id)
    query = select(Route, func.ST_AsGeoJSON(Route.geometry)).where(Route.owner_athlete_id == athlete)
    if cursor:
        created_at, route_id = decode_cursor(cursor)
        query = query.where(or_(Route.created_at < created_at, and_(Route.created_at == created_at, Route.id < route_id)))
    fetched = (
        await session.execute(query.order_by(Route.created_at.desc(), Route.id.desc()).limit(limit + 1))
    ).all()
    rows = fetched[:limit]
    return {
        "items": [_route_view(row, geometry) for row, geometry in rows],
        "next_cursor": encode_cursor(rows[-1][0].created_at, rows[-1][0].id) if len(fetched) > limit else None,
    }


@router.get("/routes/{route_id}")
async def route_detail(
    route_id: UUID,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    result = (
        await session.execute(select(Route, func.ST_AsGeoJSON(Route.geometry)).where(Route.id == route_id))
    ).first()
    if result is None or (result[0].owner_athlete_id != athlete and result[0].visibility != "public"):
        raise ProblemError(404, "route_not_found", "Route not found", "The route is unavailable.")
    return _route_view(result[0], result[1])


@router.post("/routes", status_code=201)
async def save_route(
    body: RouteCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    await _assert_public_allowed(session, athlete, body.visibility)
    geometry = _geometry(body.path)
    distance = await _distance_m(session, geometry)
    if not 100 <= distance <= 200_000:
        raise ProblemError(422, "route_distance_invalid", "Invalid route distance", "Routes must be between 100 metres and 200 kilometres.")
    row = Route(
        owner_athlete_id=athlete,
        name=body.name,
        source="athlete",
        visibility=body.visibility,
        distance_m=distance,
        surface_mix_json={body.surface: 1.0},
        geometry=geometry,
    )
    session.add(row)
    await session.commit()
    return {"id": row.id, "name": row.name, "distance_m": float(row.distance_m), "version": row.version}


@router.patch("/routes/{route_id}")
async def update_route(
    route_id: UUID,
    body: RouteUpdate,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    row = await _owned_route(session, route_id, athlete, lock=True)
    if row.version != body.expected_version:
        raise ProblemError(409, "version_conflict", "Version conflict", "Reload the route and try again.")
    if body.visibility:
        await _assert_public_allowed(session, athlete, body.visibility)
        row.visibility = body.visibility
    if body.name:
        row.name = body.name
    row.version += 1
    await session.commit()
    return {"id": row.id, "name": row.name, "visibility": row.visibility, "version": row.version}


@router.delete("/routes/{route_id}", status_code=204, response_class=Response)
async def delete_route(
    route_id: UUID,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    athlete = await athlete_id(session, user_id)
    row = await _owned_route(session, route_id, athlete, lock=True)
    # PostgreSQL rejects deletion while a scheduled race still references this route.
    try:
        await session.delete(row)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ProblemError(409, "route_in_use", "Route in use", "A scheduled race currently uses this route.") from exc
    return Response(status_code=204)


@router.post("/routes/import-gpx", status_code=201)
async def import_gpx(
    file: UploadFile = File(...),
    visibility: str = "private",
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if visibility not in {"public", "private"}:
        raise ProblemError(422, "route_visibility_invalid", "Invalid visibility", "Choose public or private visibility.")
    content = await file.read(MAX_GPX_BYTES + 1)
    try:
        parsed_name, points = parse_gpx(content)
    except InvalidGPX as exc:
        raise ProblemError(422, "gpx_invalid", "Invalid GPX", str(exc)) from exc
    athlete = await athlete_id(session, user_id)
    await _assert_public_allowed(session, athlete, visibility)
    geometry = _geometry(points)
    distance = await _distance_m(session, geometry)
    if not 100 <= distance <= 200_000:
        raise ProblemError(422, "route_distance_invalid", "Invalid route distance", "Imported routes must be between 100 metres and 200 kilometres.")
    digest = hashlib.sha256(content).hexdigest()
    settings = get_settings()
    object_name = f"routes/{athlete}/{digest}.gpx"
    if settings.import_bucket:
        def upload_original() -> None:
            from google.api_core.exceptions import PreconditionFailed
            from google.cloud import storage

            blob = storage.Client(project=settings.gcp_project_id or None).bucket(settings.import_bucket).blob(object_name)
            try:
                blob.upload_from_string(content, content_type="application/gpx+xml", if_generation_match=0)
            except PreconditionFailed:
                pass

        await anyio.to_thread.run_sync(upload_original)
    row = Route(
        owner_athlete_id=athlete,
        name=parsed_name or (file.filename or "Imported route")[:160],
        source="gpx",
        visibility=visibility,
        distance_m=distance,
        surface_mix_json={"unknown": 1.0},
        geometry=geometry,
        source_object=(f"gs://{settings.import_bucket}/{object_name}" if settings.import_bucket else f"sha256:{digest}"),
    )
    session.add(row)
    await session.commit()
    return {"id": row.id, "name": row.name, "distance_m": float(row.distance_m), "version": row.version}


@router.get("/routes/{route_id}/export.gpx")
async def export_gpx(
    route_id: UUID,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    athlete = await athlete_id(session, user_id)
    result = (
        await session.execute(select(Route, func.ST_AsGeoJSON(Route.geometry)).where(Route.id == route_id))
    ).first()
    if result is None or (result[0].owner_athlete_id != athlete and result[0].visibility != "public"):
        raise ProblemError(404, "route_not_found", "Route not found", "The route is unavailable.")
    content = render_gpx(result[0].name, _points(result[1]))
    return Response(
        content=content,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f'attachment; filename="runlete-route-{result[0].id}.gpx"'},
    )


@router.post("/routes/generate")
async def generate_route(
    body: RouteGenerate,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await athlete_id(session, user_id)
    try:
        valhalla_url = await valhalla_url_for_point(session, body.latitude, body.longitude)
    except UnsupportedMapRegion as exc:
        raise ProblemError(422, "route_region_unsupported", "Region not supported", str(exc)) from exc
    request = {
        "locations": [{"lat": body.latitude, "lon": body.longitude}],
        "costing": "pedestrian",
        "costing_options": {
            "pedestrian": {
                "use_hills": 0.1 if body.avoid_hills else 0.5,
                "use_tracks": 0.8 if body.surface == "trail" else 0.5,
            }
        },
        "directions_options": {"units": "kilometers"},
        "round_trip": {"distance": body.target_distance_km * 1000, "seed": 7},
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{valhalla_url}/route", json=request)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        raise ProblemError(503, "routing_unavailable", "Routing unavailable", "The regional route engine did not return a route.") from exc
    encoded_shape = data.get("trip", {}).get("legs", [{}])[0].get("shape") or ""
    try:
        path = decode_polyline6(encoded_shape)
    except InvalidPolyline as exc:
        raise ProblemError(502, "routing_shape_invalid", "Invalid route response", "The regional route engine returned an invalid route shape.") from exc
    if len(path) < 2:
        raise ProblemError(502, "routing_shape_missing", "Route unavailable", "The regional route engine returned no usable route geometry.")
    return {
        "path": path,
        "distance_km": float(data.get("trip", {}).get("summary", {}).get("length", body.target_distance_km)),
        "encoded_shape": encoded_shape,
    }


@router.get("/segments")
async def segments(
    cursor: str | None = None,
    limit: int = 25,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await athlete_id(session, user_id)
    limit = max(1, min(limit, 100))
    query = select(Segment).where(Segment.status == "active", Segment.visibility == "public")
    if cursor:
        created_at, segment_id = decode_cursor(cursor)
        query = query.where(or_(Segment.created_at < created_at, and_(Segment.created_at == created_at, Segment.id < segment_id)))
    fetched = (
        await session.scalars(query.order_by(Segment.created_at.desc(), Segment.id.desc()).limit(limit + 1))
    ).all()
    rows = fetched[:limit]
    return {
        "items": [
            {
                "id": row.id,
                "name": row.name,
                "distance_m": float(row.distance_m),
                "distance_km": float(row.distance_m) / 1000,
                "elevation_gain_m": 0,
                "quality_votes": row.quality_votes,
            }
            for row in rows
        ],
        "next_cursor": encode_cursor(rows[-1].created_at, rows[-1].id) if len(fetched) > limit else None,
    }


@router.post("/segments", status_code=201)
async def create_segment(
    body: SegmentCreate,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    await _assert_public_allowed(session, athlete, body.visibility)
    geometry = _geometry(body.path)
    distance = await _distance_m(session, geometry)
    if not 100 <= distance <= 50_000:
        raise ProblemError(422, "segment_distance_invalid", "Invalid segment distance", "Segments must be between 100 metres and 50 kilometres.")
    is_simple = await session.scalar(select(func.ST_IsSimple(geometry)))
    if not is_simple:
        raise ProblemError(422, "segment_self_intersection", "Invalid segment", "A segment cannot cross itself.")
    canonical = json.dumps(
        [[round(point.longitude, 6), round(point.latitude, 6)] for point in body.path],
        separators=(",", ":"),
    )
    row = Segment(
        creator_athlete_id=athlete,
        name=body.name,
        status="active",
        visibility=body.visibility,
        distance_m=distance,
        geometry_hash=hashlib.sha256(canonical.encode()).hexdigest(),
        geometry=geometry,
        quality_votes=0,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ProblemError(409, "segment_duplicate", "Segment already exists", "An equivalent segment is already registered.") from exc
    return {"id": row.id, "name": row.name, "distance_m": float(row.distance_m), "status": row.status, "version": row.version}


@router.get("/segments/{segment_id}/efforts")
async def segment_efforts(
    segment_id: UUID,
    limit: int = 50,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await athlete_id(session, user_id)
    segment = await session.get(Segment, segment_id)
    if segment is None or segment.status != "active" or segment.visibility != "public":
        raise ProblemError(404, "segment_not_found", "Segment not found", "The segment is unavailable.")
    limit = max(1, min(limit, 100))
    rows = (
        await session.execute(
            select(SegmentEffort, User.display_name)
            .join(Activity, Activity.id == SegmentEffort.activity_id)
            .join(AthleteProfile, AthleteProfile.id == SegmentEffort.athlete_id)
            .join(User, User.id == AthleteProfile.user_id)
            .join(PrivacySettings, PrivacySettings.user_id == User.id)
            .where(
                SegmentEffort.segment_id == segment_id,
                SegmentEffort.quality_passed.is_(True),
                Activity.visibility == "public",
                PrivacySettings.public_leaderboards.is_(True),
            )
            .order_by(SegmentEffort.elapsed_seconds.asc(), SegmentEffort.achieved_at.asc(), SegmentEffort.id.asc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "rank": index,
                "athlete_id": row.athlete_id,
                "display_name": display_name,
                "elapsed_seconds": float(row.elapsed_seconds),
                "coverage": float(row.coverage),
                "achieved_at": row.achieved_at,
            }
            for index, (row, display_name) in enumerate(rows, start=1)
        ],
        "next_cursor": None,
    }


def _tile_coordinates(z: int, x: int, y: int) -> None:
    if not 0 <= z <= 18:
        raise ProblemError(422, "tile_zoom_invalid", "Invalid tile", "Heatmap zoom must be between 0 and 18.")
    maximum = (1 << z) - 1
    if not 0 <= x <= maximum or not 0 <= y <= maximum:
        raise ProblemError(422, "tile_coordinate_invalid", "Invalid tile", "Heatmap tile coordinates are outside this zoom level.")


@router.get("/heatmaps/personal/tiles/{z}/{x}/{y}.mvt")
async def personal_heatmap_tile(
    z: int,
    x: int,
    y: int,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    _tile_coordinates(z, x, y)
    athlete = await athlete_id(session, user_id)
    statement = text(
        """
        WITH bounds AS (
          SELECT ST_TileEnvelope(:z, :x, :y) AS geom
        ), heat AS (
          SELECT edge.id,
                 COUNT(DISTINCT traversal.activity_id)::integer AS run_count,
                 MAX(traversal.traversed_at) AS last_run_at,
                 ST_AsMVTGeom(ST_Transform(edge.geometry, 3857), bounds.geom, 4096, 64, true) AS geom
          FROM activity.matched_edge_traversals traversal
          JOIN activity.street_edges edge ON edge.id = traversal.edge_id
          CROSS JOIN bounds
          WHERE traversal.athlete_id = :athlete_id
            AND ST_Intersects(ST_Transform(edge.geometry, 3857), bounds.geom)
          GROUP BY edge.id, edge.geometry, bounds.geom
        )
        SELECT ST_AsMVT(heat, 'personal_heatmap', 4096, 'geom') FROM heat
        """
    )
    tile = await session.scalar(statement, {"z": z, "x": x, "y": y, "athlete_id": athlete})
    return Response(
        content=bytes(tile or b""),
        media_type="application/vnd.mapbox-vector-tile",
        headers={"Cache-Control": "private, max-age=60"},
    )


@router.get("/heatmaps/community/tiles/{z}/{x}/{y}.mvt")
async def community_heatmap_tile(
    z: int,
    x: int,
    y: int,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Response:
    _tile_coordinates(z, x, y)
    await athlete_id(session, user_id)
    # An edge is emitted only after at least five distinct adult/public athletes
    # contributed. Individual activity IDs, timestamps and identities never enter
    # the public tile, and the resulting count is deliberately capped.
    statement = text(
        """
        WITH bounds AS (
          SELECT ST_TileEnvelope(:z, :x, :y) AS geom
        ), eligible AS (
          SELECT edge.id,
                 LEAST(COUNT(DISTINCT traversal.athlete_id), 255)::integer AS athlete_count,
                 ST_AsMVTGeom(ST_Transform(edge.geometry, 3857), bounds.geom, 4096, 64, true) AS geom
          FROM activity.matched_edge_traversals traversal
          JOIN activity.street_edges edge ON edge.id = traversal.edge_id
          JOIN activity.activities activity ON activity.id = traversal.activity_id
          JOIN activity.quality quality
            ON quality.activity_id = activity.id
           AND quality.computation_version = activity.computation_version
          CROSS JOIN bounds
          WHERE activity.visibility = 'public'
            AND activity.status = 'complete'
            AND quality.competition_eligible
            AND ST_Intersects(ST_Transform(edge.geometry, 3857), bounds.geom)
          GROUP BY edge.id, edge.geometry, bounds.geom
          HAVING COUNT(DISTINCT traversal.athlete_id) >= 5
        )
        SELECT ST_AsMVT(eligible, 'community_heatmap', 4096, 'geom') FROM eligible
        """
    )
    tile = await session.scalar(statement, {"z": z, "x": x, "y": y})
    return Response(
        content=bytes(tile or b""),
        media_type="application/vnd.mapbox-vector-tile",
        headers={"Cache-Control": "public, max-age=300, s-maxage=3600"},
    )
