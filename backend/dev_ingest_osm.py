"""Dev: ingest a real OpenStreetMap city into activity.street_edges.

Uses the production osmium pipeline (build_edge_file / load_edge_file /
activate_graph). No Valhalla needed for ingestion.

    python backend/dev_ingest_osm.py /tmp/monaco.osm.pbf monaco 7.40 43.71 7.45 43.76
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select  # noqa: E402
from backend.app.core.database import SessionFactory  # noqa: E402
from backend.app.maps.models import OSMGraphVersion, OSMRegion, StreetEdge  # noqa: E402
from backend.app.maps.osm_ingestion import activate_graph, build_edge_file, load_edge_file  # noqa: E402


async def main(pbf: str, code: str, w: float, s: float, e: float, n: float):
    async with SessionFactory() as session:
        region = await session.scalar(select(OSMRegion).where(OSMRegion.code == code))
        if region is not None:
            active = await session.scalar(
                select(OSMGraphVersion).where(OSMGraphVersion.region_id == region.id,
                                              OSMGraphVersion.status == "active"))
            count = await session.scalar(
                select(func.count()).select_from(StreetEdge).where(StreetEdge.region_id == region.id))
            if active and count:
                print(f"region '{code}' already ingested: {count} edges, graph {active.id}")
                return
        wkt = f"POLYGON(({w} {s}, {e} {s}, {e} {n}, {w} {n}, {w} {s}))"
        boundary = func.ST_Multi(func.ST_SetSRID(func.ST_GeomFromText(wkt), 4326))
        if region is None:
            region = OSMRegion(code=code, name=code.title(), pbf_object=Path(pbf).name,
                               status="validating", boundary=boundary)
            session.add(region); await session.flush()
        graph = OSMGraphVersion(region_id=region.id, version_code=f"{code}-v1",
                                source_timestamp=datetime.now(timezone.utc), graph_object="none",
                                graph_hash="0" * 64, status="validating",
                                activated_at=None)
        session.add(graph); await session.flush()
        region_id, graph_id = region.id, graph.id
        await session.commit()

    out = Path("/tmp") / f"{code}-edges.jsonl"
    written = build_edge_file(Path(pbf), graph_id, region_id, out)
    print(f"parsed {written} street-edge records from {pbf}")

    async with SessionFactory() as session:
        loaded = await load_edge_file(session, out)
        result = await activate_graph(session, graph_id)
        await session.commit()
    print(f"loaded {loaded} edges; activated graph {result}")


if __name__ == "__main__":
    pbf, code = sys.argv[1], sys.argv[2]
    w, s, e, n = map(float, sys.argv[3:7])
    asyncio.run(main(pbf, code, w, s, e, n))
