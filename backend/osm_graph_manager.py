from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict

from sqlalchemy import text

from backend.geo_db import get_geo_engine
from backend.osm_ingestion import build_edge_file, load_edge_file
from backend.platform_ids import new_id
from backend.territory_engine import recompute_edges


async def register_region(
    code: str,
    name: str,
    pbf_url: str,
    replication_url: str | None,
) -> Dict[str, str]:
    engine = get_geo_engine()
    if engine is None:
        raise RuntimeError("POSTGRES_URL is required")
    region_id, osm_region_id = new_id(), new_id()
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                INSERT INTO regions (id, code, name, kind)
                VALUES (CAST(:id AS uuid), :code, :name, 'osm_shard')
                ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, updated_at=NOW()
                """
            ),
            {"id": region_id, "code": code, "name": name},
        )
        canonical_region = await connection.scalar(
            text("SELECT id FROM regions WHERE code=:code"), {"code": code}
        )
        await connection.execute(
            text(
                """
                INSERT INTO osm_regions (
                    id, region_id, code, pbf_source_url, replication_url, status
                ) VALUES (
                    CAST(:id AS uuid), :region, :code, :pbf, :replication, 'pending'
                )
                ON CONFLICT (code) DO UPDATE SET
                    pbf_source_url=EXCLUDED.pbf_source_url,
                    replication_url=EXCLUDED.replication_url,
                    updated_at=NOW()
                """
            ),
            {
                "id": osm_region_id,
                "region": canonical_region,
                "code": code,
                "pbf": pbf_url,
                "replication": replication_url,
            },
        )
        canonical_osm_region = await connection.scalar(
            text("SELECT id FROM osm_regions WHERE code=:code"), {"code": code}
        )
    return {
        "region_id": str(canonical_region),
        "osm_region_id": str(canonical_osm_region),
    }


async def ingest_graph(
    code: str,
    version: str,
    pbf: Path,
    source_timestamp: datetime,
    valhalla_object_key: str | None,
) -> Dict[str, Any]:
    engine = get_geo_engine()
    if engine is None:
        raise RuntimeError("POSTGRES_URL is required")
    graph_id = new_id()
    async with engine.begin() as connection:
        osm_region_id = await connection.scalar(
            text("SELECT id FROM osm_regions WHERE code=:code"), {"code": code}
        )
        if not osm_region_id:
            raise RuntimeError(f"OSM region {code!r} is not registered")
        await connection.execute(
            text(
                """
                INSERT INTO osm_graph_versions (
                    id, osm_region_id, version, source_timestamp,
                    valhalla_object_key, status
                ) VALUES (
                    CAST(:id AS uuid), :region, :version, :timestamp,
                    :object_key, 'building'
                )
                ON CONFLICT (osm_region_id, version) DO UPDATE SET
                    source_timestamp=EXCLUDED.source_timestamp,
                    valhalla_object_key=EXCLUDED.valhalla_object_key,
                    status='building'
                """
            ),
            {
                "id": graph_id,
                "region": osm_region_id,
                "version": version,
                "timestamp": source_timestamp,
                "object_key": valhalla_object_key,
            },
        )
        graph_id = str(
            await connection.scalar(
                text(
                    """
                    SELECT id FROM osm_graph_versions
                    WHERE osm_region_id=:region AND version=:version
                    """
                ),
                {"region": osm_region_id, "version": version},
            )
        )
        await connection.execute(
            text("UPDATE osm_regions SET status='building', updated_at=NOW() WHERE id=:id"),
            {"id": osm_region_id},
        )
    with TemporaryDirectory(prefix="runlete-osm-") as directory:
        edge_file = Path(directory) / "edges.ndjson"
        built = build_edge_file(pbf, version, edge_file)
        loaded = await load_edge_file(edge_file, str(osm_region_id), graph_id)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                UPDATE osm_graph_versions SET status='validating'
                WHERE id=CAST(:graph AS uuid)
                """
            ),
            {"graph": graph_id},
        )
    return {"graph_version_id": graph_id, "edges_built": built, "edges_loaded": loaded}


async def activate_graph(graph_id: str) -> Dict[str, int]:
    engine = get_geo_engine()
    if engine is None:
        raise RuntimeError("POSTGRES_URL is required")
    async with engine.begin() as connection:
        graph = (
            await connection.execute(
                text(
                    """
                    SELECT id, osm_region_id, status
                    FROM osm_graph_versions
                    WHERE id=CAST(:graph AS uuid)
                    FOR UPDATE
                    """
                ),
                {"graph": graph_id},
            )
        ).first()
        if not graph or graph.status not in {"validating", "active"}:
            raise RuntimeError("Graph must be in validating state")
        edge_count = int(
            await connection.scalar(
                text("SELECT COUNT(*) FROM street_edges WHERE graph_version_id=:graph"),
                {"graph": graph_id},
            )
            or 0
        )
        if edge_count < 1:
            raise RuntimeError("Graph has no claim edges")
        old_graph_ids = [
            row[0]
            for row in await connection.execute(
                text(
                    """
                    SELECT id FROM osm_graph_versions
                    WHERE osm_region_id=:region AND status='active' AND id!=:graph
                    """
                ),
                {"region": graph.osm_region_id, "graph": graph_id},
            )
        ]
        alias_pairs = [
            dict(row._mapping)
            for row in await connection.execute(
                text(
                    """
                    SELECT old.id AS old_street_edge_id,
                           fresh.id AS new_street_edge_id,
                           old.graph_version_id AS old_graph_version_id,
                           fresh.graph_version_id AS new_graph_version_id,
                           LEAST(old.distance_m, fresh.distance_m)
                             / NULLIF(GREATEST(old.distance_m, fresh.distance_m), 0)
                             AS overlap_ratio
                    FROM street_edges old
                    JOIN street_edges fresh
                      ON fresh.graph_version_id=CAST(:graph AS uuid)
                     AND fresh.osm_way_id=old.osm_way_id
                     AND ST_HausdorffDistance(
                           ST_Transform(old.edge, 3857),
                           ST_Transform(fresh.edge, 3857)
                         ) <= 15
                    WHERE old.graph_version_id=ANY(CAST(:old_graphs AS uuid[]))
                      AND LEAST(old.distance_m, fresh.distance_m)
                            / NULLIF(GREATEST(old.distance_m, fresh.distance_m), 0) >= 0.80
                    """
                ),
                {"graph": graph_id, "old_graphs": old_graph_ids},
            )
        ]
        for alias in alias_pairs:
            await connection.execute(
                text(
                    """
                    INSERT INTO street_edge_aliases (
                        id, old_street_edge_id, new_street_edge_id,
                        old_graph_version_id, new_graph_version_id, overlap_ratio
                    ) VALUES (
                        CAST(:id AS uuid), :old_street_edge_id, :new_street_edge_id,
                        :old_graph_version_id, :new_graph_version_id, :overlap_ratio
                    )
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"id": new_id(), **alias},
            )
        traversal_rows = [
            dict(row._mapping)
            for row in await connection.execute(
                text(
                    """
                    SELECT t.activity_id, alias.new_street_edge_id, t.user_id,
                           t.club_id, t.local_activity_date, t.coverage,
                           t.confidence, t.elapsed_time_sec, t.speed_mps,
                           t.qualified, t.rejection_reasons
                    FROM street_edge_aliases alias
                    JOIN matched_edge_traversals t
                      ON t.street_edge_id=alias.old_street_edge_id
                    WHERE alias.new_graph_version_id=CAST(:graph AS uuid)
                      AND alias.overlap_ratio>=0.90
                      AND t.local_activity_date>=CURRENT_DATE - 28
                    """
                ),
                {"graph": graph_id},
            )
        ]
        copied = 0
        for traversal in traversal_rows:
            result = await connection.execute(
                text(
                    """
                    INSERT INTO matched_edge_traversals (
                        id, activity_id, street_edge_id, user_id, club_id,
                        graph_version_id, local_activity_date, coverage,
                        confidence, elapsed_time_sec, speed_mps, qualified,
                        rejection_reasons
                    ) VALUES (
                        CAST(:id AS uuid), :activity, :edge, :user, :club,
                        CAST(:graph AS uuid), :local_date, :coverage,
                        :confidence, :elapsed, :speed, :qualified,
                        CAST(:reasons AS jsonb)
                    )
                    ON CONFLICT (activity_id, street_edge_id) DO NOTHING
                    """
                ),
                {
                    "id": new_id(),
                    "activity": traversal["activity_id"],
                    "edge": traversal["new_street_edge_id"],
                    "user": traversal["user_id"],
                    "club": traversal["club_id"],
                    "graph": graph_id,
                    "local_date": traversal["local_activity_date"],
                    "coverage": traversal["coverage"],
                    "confidence": traversal["confidence"],
                    "elapsed": traversal["elapsed_time_sec"],
                    "speed": traversal["speed_mps"],
                    "qualified": traversal["qualified"],
                    "reasons": json.dumps(traversal["rejection_reasons"]),
                },
            )
            copied += max(0, int(result.rowcount or 0))
        await connection.execute(
            text(
                """
                UPDATE street_edges SET status='retired'
                WHERE graph_version_id=ANY(CAST(:old_graphs AS uuid[]))
                """
            ),
            {"old_graphs": old_graph_ids},
        )
        await connection.execute(
            text(
                """
                UPDATE osm_graph_versions SET status='retired'
                WHERE id=ANY(CAST(:old_graphs AS uuid[]))
                """
            ),
            {"old_graphs": old_graph_ids},
        )
        await connection.execute(
            text(
                """
                UPDATE street_edges SET status='active'
                WHERE graph_version_id=CAST(:graph AS uuid)
                """
            ),
            {"graph": graph_id},
        )
        await connection.execute(
            text(
                """
                UPDATE osm_graph_versions SET status='active', activated_at=NOW()
                WHERE id=CAST(:graph AS uuid)
                """
            ),
            {"graph": graph_id},
        )
        await connection.execute(
            text(
                """
                UPDATE osm_regions SET status='active', updated_at=NOW()
                WHERE id=:region
                """
            ),
            {"region": graph.osm_region_id},
        )
        affected = [
            str(row[0])
            for row in await connection.execute(
                text(
                    """
                    SELECT old_street_edge_id FROM street_edge_aliases
                    WHERE new_graph_version_id=CAST(:graph AS uuid)
                    UNION
                    SELECT new_street_edge_id FROM street_edge_aliases
                    WHERE new_graph_version_id=CAST(:graph AS uuid)
                    """
                ),
                {"graph": graph_id},
            )
        ]
    await recompute_edges(affected)
    return {"edges": edge_count, "traversals_copied": copied, "edges_recomputed": len(affected)}


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage versioned Runlete OSM graph shards")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register = subparsers.add_parser("register")
    register.add_argument("--code", required=True)
    register.add_argument("--name", required=True)
    register.add_argument("--pbf-url", required=True)
    register.add_argument("--replication-url")
    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("--code", required=True)
    ingest.add_argument("--version", required=True)
    ingest.add_argument("--pbf", required=True, type=Path)
    ingest.add_argument("--source-timestamp", required=True)
    ingest.add_argument("--valhalla-object-key")
    activate = subparsers.add_parser("activate")
    activate.add_argument("--graph-id", required=True)
    args = parser.parse_args()
    if args.command == "register":
        result = asyncio.run(
            register_region(args.code, args.name, args.pbf_url, args.replication_url)
        )
    elif args.command == "ingest":
        result = asyncio.run(
            ingest_graph(
                args.code,
                args.version,
                args.pbf,
                parse_timestamp(args.source_timestamp),
                args.valhalla_object_key,
            )
        )
    else:
        result = asyncio.run(activate_graph(args.graph_id))
    print(result)


if __name__ == "__main__":
    main()
