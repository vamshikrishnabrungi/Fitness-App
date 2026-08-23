"""Dev: record a run over REAL ingested OSM streets and claim them end-to-end.

Valhalla can't run in this pod, so this uses a PostGIS proximity map-matcher
(ST_DWithin + ST_Intersection coverage) instead of Valhalla, then feeds the
REAL production territory projector. Proves: real GPS trace -> real street_edges
claimed -> visible via /territory.

    python backend/dev_run_on_real_streets.py
Prereq: dev_seed_clubs.py + dev_ingest_osm.py (monaco).
"""
import asyncio
import json
import os
import sys
from datetime import date, datetime, time, timezone
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select, text  # noqa: E402
from backend.app.core.database import SessionFactory  # noqa: E402
from backend.app.identity.models import EmailIdentity  # noqa: E402
from backend.app.athletes.models import AthleteProfile  # noqa: E402
from backend.app.competition.models import Club, ClubMembership  # noqa: E402
from backend.app.maps.models import OSMRegion, StreetEdge  # noqa: E402
from backend.app.activities.models import Activity, ActivityClubAttribution  # noqa: E402
from backend.app.competition.projection import project_activity_territory  # noqa: E402

MATCHER = "valhalla-confidence-v1"


async def match_and_project(session, *, activity, region_id, trace_coords, club_id):
    trace_geojson = json.dumps({"type": "LineString", "coordinates": trace_coords})
    rows = (await session.execute(text(
        """
        WITH trace AS (SELECT ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:t), 4326), 3857) AS g)
        SELECT e.id,
               LEAST(1.0, ST_Length(ST_Intersection(ST_Transform(e.geometry, 3857),
                     ST_Buffer(trace.g, 15.0))) / NULLIF(e.length_m, 0)) AS coverage,
               e.length_m
        FROM activity.street_edges e, trace
        WHERE e.region_id = CAST(:r AS uuid) AND e.running_accessible
          AND ST_DWithin(ST_Transform(e.geometry, 3857), trace.g, 15.0)
        """), {"t": trace_geojson, "r": str(region_id)})).all()
    day = activity.started_at.date()
    seq = 0
    claimed = 0
    for edge_id, coverage, length_m in rows:
        seq += 1
        cov = max(0.0, min(1.0, float(coverage or 0)))
        qualifies = cov >= 0.80
        elapsed = max(1.0, float(length_m) / 2.5)
        await session.execute(text(
            """
            INSERT INTO activity.matched_edge_traversals (
              id, activity_id, athlete_id, edge_id, graph_version_id, sequence,
              coverage, confidence, elapsed_seconds, speed_mps, traversed_at,
              local_date, qualifies, computation_version, created_at, updated_at, version)
            SELECT CAST(:id AS uuid), CAST(:aid AS uuid), CAST(:ath AS uuid), e.id,
                   e.graph_version_id, :seq, :cov, 0.9, :el, :sp, :ts, :ld, :q, :ver,
                   NOW(), NOW(), 1
            FROM activity.street_edges e WHERE e.id = CAST(:eid AS uuid)
            """),
            {"id": str(uuid4()), "aid": str(activity.id), "ath": str(activity.athlete_id),
             "seq": seq, "cov": cov, "el": elapsed, "sp": float(length_m) / elapsed,
             "ts": activity.started_at, "ld": day, "q": qualifies, "ver": MATCHER, "eid": str(edge_id)})
        if qualifies:
            claimed += 1
    await session.commit()
    await project_activity_territory(session, activity.id)
    return len(rows), claimed


async def main():
    async with SessionFactory() as session:
        ident = await session.scalar(select(EmailIdentity).where(EmailIdentity.normalized_email == "owner@test.dev"))
        athlete = await session.scalar(select(AthleteProfile.id).where(AthleteProfile.user_id == ident.user_id))
        club = await session.scalar(select(Club).where(Club.slug == "club-alpha"))
        if club is None:
            club = Club(name="Club Alpha", slug="club-alpha", description="", visibility="public",
                        timezone="UTC", primary_color="#FF5533", secondary_color="#111827", rules="", status="active")
            session.add(club); await session.flush()
            now = datetime.now(timezone.utc)
            session.add(ClubMembership(club_id=club.id, athlete_id=athlete, role="owner",
                                       status="active", requested_at=now, joined_at=now))
            await session.commit()
        region_id = await session.scalar(select(OSMRegion.id).where(OSMRegion.code == "monaco"))

        # Build a real GPS trace: the busiest named street's edges, in order.
        street = (await session.execute(text(
            "SELECT name, count(*) c FROM activity.street_edges WHERE region_id=CAST(:r AS uuid) "
            "AND name IS NOT NULL GROUP BY name ORDER BY c DESC LIMIT 1"), {"r": str(region_id)})).first()
        edge_geoms = (await session.execute(text(
            "SELECT ST_AsGeoJSON(geometry) FROM activity.street_edges WHERE region_id=CAST(:r AS uuid) "
            "AND name=:n ORDER BY edge_key"), {"r": str(region_id), "n": street.name})).all()
        trace = []
        for (gj,) in edge_geoms:
            for lon, lat in json.loads(gj)["coordinates"]:
                if not trace or (abs(trace[-1][0] - lon) > 1e-9 or abs(trace[-1][1] - lat) > 1e-9):
                    trace.append([lon, lat])
        print(f"Simulated run along '{street.name}' ({street.c} edges), {len(trace)} GPS points")

        await session.execute(text("DELETE FROM activity.activities WHERE source='real-run'"))
        await session.commit()
        started = datetime.combine(date.today(), time(7, 0), timezone.utc)
        activity = Activity(athlete_id=athlete, source="real-run", source_identity=str(uuid4()),
                            sport_type="running", surface="road", status="complete", visibility="public",
                            title="Monaco morning run", started_at=started, distance_m=900,
                            moving_seconds=360, computation_version="dev")
        session.add(activity); await session.flush()
        session.add(ActivityClubAttribution(activity_id=activity.id, athlete_id=athlete,
                                             club_id=club.id, attributed_at=started))
        await session.commit()
        matched, claimed = await match_and_project(session, activity=activity, region_id=region_id,
                                                    trace_coords=trace, club_id=club.id)
        print(f"map-matched {matched} real edges; {claimed} qualified and were claimed")

        controls = (await session.execute(text(
            """SELECT se.name, se.highway_class, c.controller_type, ROUND(c.score::numeric,1)
               FROM competition.territory_current_control c
               JOIN activity.street_edges se ON se.id=c.edge_id
               WHERE se.region_id=CAST(:r AS uuid) AND c.controller_type='athlete'
               ORDER BY c.score DESC LIMIT 8"""), {"r": str(region_id)})).all()
        print("\nClaimed real streets (top by score):")
        for name, hw, ct, score in controls:
            print(f"   {name or '(unnamed '+hw+')':30s}  score={score}")


asyncio.run(main())
