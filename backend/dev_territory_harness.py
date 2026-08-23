"""Territory verification harness (dev-only).

Proves the street-based territory engine end-to-end WITHOUT Valhalla/GCS by
seeding a synthetic OSM region + street edges and driving the real
`project_activity_territory` / `recompute_edge` code with matched-edge
traversals. Demonstrates: claim -> defend -> take over -> decay -> expire, at
both athlete and club control levels.

Run:  python backend/dev_territory_harness.py
Prereq: python backend/dev_seed_clubs.py  (creates the two athletes)
"""
import asyncio
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, func, select, text  # noqa: E402
from backend.app.core.database import SessionFactory  # noqa: E402
from backend.app.identity.models import EmailIdentity  # noqa: E402
from backend.app.athletes.models import AthleteProfile  # noqa: E402
from backend.app.competition.models import (  # noqa: E402
    Club, ClubMembership, TerritoryControlHistory, TerritoryCurrentControl, TerritoryScore,
)
from backend.app.maps.models import MatchedEdgeTraversal, OSMGraphVersion, OSMRegion, StreetEdge  # noqa: E402
from backend.app.activities.models import Activity, ActivityClubAttribution  # noqa: E402
from backend.app.competition.projection import project_activity_territory, recompute_edge  # noqa: E402

MATCHER = "valhalla-confidence-v1"
TODAY = date.today()


async def athlete_for(session, email):
    ident = await session.scalar(select(EmailIdentity).where(EmailIdentity.normalized_email == email))
    return await session.scalar(select(AthleteProfile.id).where(AthleteProfile.user_id == ident.user_id))


async def ensure_club(session, name, slug, owner_athlete):
    club = await session.scalar(select(Club).where(Club.slug == slug))
    if club is None:
        club = Club(name=name, slug=slug, description="", visibility="public", timezone="UTC",
                    primary_color="#FF5533", secondary_color="#111827", rules="", status="active")
        session.add(club)
        await session.flush()
    membership = await session.scalar(
        select(ClubMembership).where(ClubMembership.club_id == club.id, ClubMembership.athlete_id == owner_athlete)
    )
    if membership is None:
        now = datetime.now(timezone.utc)
        session.add(ClubMembership(club_id=club.id, athlete_id=owner_athlete, role="owner",
                                   status="active", requested_at=now, joined_at=now))
    return club


async def seed_geo(session):
    await session.execute(delete(StreetEdge).where(StreetEdge.edge_key.like("harness-%")))
    await session.execute(delete(OSMGraphVersion).where(OSMGraphVersion.version_code == "harness-v1"))
    await session.execute(delete(OSMRegion).where(OSMRegion.code == "harness-region"))
    await session.flush()
    boundary = func.ST_Multi(func.ST_SetSRID(func.ST_GeomFromText(
        "POLYGON((-0.01 -0.01, 0.02 -0.01, 0.02 0.02, -0.01 0.02, -0.01 -0.01))"), 4326))
    region = OSMRegion(code="harness-region", name="Harness City", pbf_object="none",
                       status="active", boundary=boundary)
    session.add(region); await session.flush()
    graph = OSMGraphVersion(region_id=region.id, version_code="harness-v1",
                            source_timestamp=datetime.now(timezone.utc), graph_object="none",
                            graph_hash="0" * 64, status="active", activated_at=datetime.now(timezone.utc))
    session.add(graph); await session.flush()
    edges = {}
    for key, wkt, way in [("harness-E1", "LINESTRING(0 0, 0.001 0)", 101),
                          ("harness-E2", "LINESTRING(0.001 0, 0.002 0)", 102)]:
        edge = StreetEdge(region_id=region.id, graph_version_id=graph.id, edge_key=key,
                          osm_way_id=way, from_node_id=way * 10, to_node_id=way * 10 + 1,
                          name=key, highway_class="residential", surface="asphalt",
                          length_m=111.0, running_accessible=True, spatial_cell="0,0",
                          geometry=func.ST_SetSRID(func.ST_GeomFromText(wkt), 4326))
        session.add(edge); await session.flush()
        edges[key] = edge.id
    return edges


async def run_activity(session, *, athlete, club_id, edge_id, day, coverage=0.95, confidence=0.95):
    """Create a complete public activity with one qualifying matched traversal, then project it."""
    started = datetime.combine(day, time(7, 0), timezone.utc)
    activity = Activity(athlete_id=athlete, source="harness", source_identity=str(uuid4()),
                        sport_type="running", surface="road", status="complete", visibility="public",
                        title="Harness run", started_at=started, ended_at=started + timedelta(minutes=10),
                        elapsed_seconds=600, moving_seconds=600, distance_m=800, computation_version="harness")
    session.add(activity); await session.flush()
    session.add(ActivityClubAttribution(activity_id=activity.id, athlete_id=athlete,
                                         club_id=club_id, attributed_at=started))
    session.add(MatchedEdgeTraversal(activity_id=activity.id, athlete_id=athlete, edge_id=edge_id,
                                     graph_version_id=(await session.get(StreetEdge, edge_id)).graph_version_id,
                                     sequence=1, coverage=coverage, confidence=confidence,
                                     elapsed_seconds=90.0, speed_mps=1.23, traversed_at=started,
                                     local_date=day, qualifies=True, computation_version=MATCHER))
    await session.commit()
    await project_activity_territory(session, activity.id)


async def show(session, edge_id, label):
    controls = (await session.scalars(
        select(TerritoryCurrentControl).where(TerritoryCurrentControl.edge_id == edge_id))).all()
    print(f"\n[{label}] edge control:")
    if not controls:
        print("   (no controller — vacant)")
    for c in controls:
        owner = c.athlete_id if c.controller_type == "athlete" else c.club_id
        print(f"   {c.controller_type:7s} owner={str(owner)[:8]} score={float(c.score):7.2f} "
              f"expires={c.expires_at.date()}")


async def history(session, edge_id):
    rows = (await session.scalars(
        select(TerritoryControlHistory).where(TerritoryControlHistory.edge_id == edge_id)
        .order_by(TerritoryControlHistory.occurred_at))).all()
    print("   history:", [f"{r.controller_type}:{r.event_type}" for r in rows])


async def main():
    async with SessionFactory() as session:
        a = await athlete_for(session, "owner@test.dev")
        b = await athlete_for(session, "member@test.dev")
        alpha = await ensure_club(session, "Club Alpha", "club-alpha", a)
        beta = await ensure_club(session, "Club Beta", "club-beta", b)
        await session.execute(delete(Activity).where(Activity.source == "harness"))
        await session.commit()
        edges = await seed_geo(session)
        await session.commit()
        e1 = edges["harness-E1"]

        print("=" * 60)
        print("SCENARIO: Athlete A (Club Alpha) vs Athlete B (Club Beta) over street E1")
        print("=" * 60)

        # 1. CLAIM — A runs E1 once
        await run_activity(session, athlete=a, club_id=alpha.id, edge_id=e1, day=TODAY - timedelta(days=5))
        await show(session, e1, "1. A claims E1"); await history(session, e1)

        # 2. DEFEND — A runs E1 again on a new day (raises aggregate)
        await run_activity(session, athlete=a, club_id=alpha.id, edge_id=e1, day=TODAY - timedelta(days=3))
        await show(session, e1, "2. A defends E1"); await history(session, e1)

        # 3. TAKEOVER — B runs E1 on 3 distinct recent days, out-scoring A
        for d in (2, 1, 0):
            await run_activity(session, athlete=b, club_id=beta.id, edge_id=e1, day=TODAY - timedelta(days=d))
        await show(session, e1, "3. B takes over E1"); await history(session, e1)

        # 4. DECAY + EXPIRE — simulate 40 days passing with no new runs
        await recompute_edge(session, e1, today=TODAY + timedelta(days=40))
        await session.commit()
        await show(session, e1, "4. E1 after 40 idle days"); await history(session, e1)

    print("\nDone. Engine verified: claim -> defend -> takeover -> expire (athlete + club).")


asyncio.run(main())
