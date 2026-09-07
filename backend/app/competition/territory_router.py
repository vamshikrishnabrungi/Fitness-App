from datetime import datetime, timedelta, timezone
import json
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.core.database import get_session
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id
from backend.app.maps.models import StreetEdge
from .models import Club, ClubMembership, CompetitiveProfile, TerritoryCurrentControl, TerritoryScore
from .service import athlete_id

router = APIRouter(prefix="/territory", tags=["territory"])


async def _features(session: AsyncSession, *, athlete: UUID | None = None, club: UUID | None = None) -> dict:
    query = select(
        TerritoryCurrentControl,
        StreetEdge,
        func.ST_AsGeoJSON(StreetEdge.geometry).label("geometry_json"),
    ).join(StreetEdge, StreetEdge.id == TerritoryCurrentControl.edge_id)
    if athlete: query = query.where(TerritoryCurrentControl.controller_type == "athlete", TerritoryCurrentControl.athlete_id == athlete)
    if club: query = query.where(TerritoryCurrentControl.controller_type == "club", TerritoryCurrentControl.club_id == club)
    rows = (await session.execute(query.limit(5000))).all()
    features = []
    for control, edge, geometry in rows:
        features.append({"type": "Feature", "id": str(edge.id), "geometry": json.loads(geometry), "properties": {"edge_id": str(edge.id), "controller_type": control.controller_type, "controller_id": str(control.athlete_id or control.club_id), "score": float(control.score), "expires_at": control.expires_at.isoformat(), "state": "expiring" if control.expires_at < datetime.now(timezone.utc) + timedelta(days=3) else "controlled"}})
    return {"type": "FeatureCollection", "features": features}


@router.get("/mine")
async def mine(user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict: return await _features(session, athlete=await athlete_id(session, user_id))


async def _authorize_club_map(session: AsyncSession, club_id: UUID, athlete: UUID) -> Club:
    club_row = await session.get(Club, club_id)
    if club_row is None or club_row.status != "active":
        raise ProblemError(404, "club_not_found", "Club not found", "The club does not exist.")
    if club_row.visibility == "private":
        membership = await session.scalar(
            select(ClubMembership.id).where(
                ClubMembership.club_id == club_id,
                ClubMembership.athlete_id == athlete,
                ClubMembership.status == "active",
            )
        )
        if membership is None:
            raise ProblemError(403, "club_territory_private", "Private club", "Join this club to view its territory.")
    return club_row


@router.get("/club/{club_id}")
async def club(
    club_id: UUID,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    athlete = await athlete_id(session, user_id)
    await _authorize_club_map(session, club_id, athlete)
    return await _features(session, club=club_id)


@router.get("/edges/{edge_id}")
async def edge(edge_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); edge_row = await session.get(StreetEdge, edge_id)
    if edge_row is None: raise ProblemError(404, "territory_edge_not_found", "Road not found", "The road edge does not exist.")
    controls = (await session.scalars(select(TerritoryCurrentControl).where(TerritoryCurrentControl.edge_id == edge_id))).all(); contributions = (await session.scalars(select(TerritoryScore).where(TerritoryScore.edge_id == edge_id, TerritoryScore.athlete_id == athlete))).all()
    return {"id": edge_row.id, "name": edge_row.name or "Unnamed path", "length_m": float(edge_row.length_m), "surface": edge_row.surface, "controls": [{"controller_type": row.controller_type, "controller_id": row.athlete_id or row.club_id, "score": float(row.score), "expires_at": row.expires_at} for row in controls], "athlete_contribution": sum(float(row.base_points) for row in contributions)}


@router.post("/tile-session")
async def tile_session(body: dict, request: Request, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); settings = get_settings(); now = datetime.now(timezone.utc); scope = body.get("scope", "mine"); club_id = body.get("club_id")
    if scope not in {"mine", "club"}:
        raise ProblemError(422, "territory_scope_invalid", "Invalid map scope", "Use mine or club territory scope.")
    if scope == "club":
        try:
            club_uuid = UUID(str(club_id))
        except (TypeError, ValueError) as exc:
            raise ProblemError(422, "club_id_required", "Club required", "Choose a club for this map layer.") from exc
        await _authorize_club_map(session, club_uuid, athlete)
        club_id = str(club_uuid)
    token = jwt.encode({"sub": str(athlete), "scope": scope, "club_id": club_id, "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=15)).timestamp()), "iss": settings.jwt_issuer, "aud": "runlete-tiles"}, settings.jwt_secret, algorithm="HS256")
    base_url = str(request.base_url).rstrip("/")
    return {"tile_url": f"{base_url}/api/v1/territory/tiles/{{z}}/{{x}}/{{y}}.mvt?token={token}", "expires_at": now + timedelta(minutes=15)}


@router.get("/tiles/{z}/{x}/{y}.mvt", include_in_schema=True)
async def tile(z: int, x: int, y: int, token: str = Query(), session: AsyncSession = Depends(get_session)) -> Response:
    settings = get_settings()
    try: claims = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], issuer=settings.jwt_issuer, audience="runlete-tiles")
    except jwt.InvalidTokenError as exc: raise ProblemError(401, "tile_token_invalid", "Map session expired", "Refresh the territory map.") from exc
    controller_type = "club" if claims.get("scope") == "club" else "athlete"; controller_id = claims.get("club_id") if controller_type == "club" else claims["sub"]
    sql = text("""WITH bounds AS (SELECT ST_TileEnvelope(:z,:x,:y) AS geom), rows AS (SELECT e.id, c.score, c.expires_at, ST_AsMVTGeom(ST_Transform(e.geometry,3857), bounds.geom,4096,64,true) AS geom FROM activity.street_edges e JOIN competition.territory_current_control c ON c.edge_id=e.id CROSS JOIN bounds WHERE c.controller_type=:controller_type AND COALESCE(c.club_id,c.athlete_id)=CAST(:controller_id AS uuid) AND ST_Transform(e.geometry,3857) && bounds.geom) SELECT ST_AsMVT(rows,'territory',4096,'geom') FROM rows""")
    data = await session.scalar(sql, {"z": z, "x": x, "y": y, "controller_type": controller_type, "controller_id": controller_id})
    return Response(content=bytes(data or b""), media_type="application/vnd.mapbox-vector-tile", headers={"Cache-Control": "private, max-age=60"})
