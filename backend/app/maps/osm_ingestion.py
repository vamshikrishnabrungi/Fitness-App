from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

import osmium
import anyio
from shapely.geometry import LineString
from shapely.ops import substring
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.ids import uuid7
from backend.app.core.config import get_settings
from backend.app.operations.outbox import enqueue_event

from .models import OSMGraphVersion, OSMRegion


MAX_EDGE_LENGTH_M = 100.0
RUNNING_HIGHWAYS = {
    "bridleway",
    "cycleway",
    "footway",
    "living_street",
    "path",
    "pedestrian",
    "residential",
    "secondary",
    "service",
    "steps",
    "tertiary",
    "track",
    "unclassified",
}
BLOCKED_ACCESS = {"no", "private"}


def runnable_way(tags: Any) -> bool:
    highway = tags.get("highway")
    if highway not in RUNNING_HIGHWAYS:
        return False
    if tags.get("access") in BLOCKED_ACCESS or tags.get("foot") in BLOCKED_ACCESS:
        return False
    if tags.get("construction") or tags.get("proposed"):
        return False
    if highway in {"secondary", "tertiary"}:
        has_foot_access = tags.get("foot") in {"yes", "designated", "permissive"}
        has_sidewalk = tags.get("sidewalk") not in {None, "no", "none", "separate"}
        if not has_foot_access and not has_sidewalk:
            return False
    if highway == "cycleway" and tags.get("foot") not in {"yes", "designated", "permissive"}:
        return False
    return True


def haversine_m(a: Sequence[float], b: Sequence[float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def line_length_m(coordinates: Sequence[Sequence[float]]) -> float:
    return sum(haversine_m(coordinates[index - 1], coordinates[index]) for index in range(1, len(coordinates)))


def split_max_length(coordinates: list[tuple[float, float]], maximum_m: float = MAX_EDGE_LENGTH_M) -> list[list[tuple[float, float]]]:
    if len(coordinates) < 2:
        return []
    total_m = line_length_m(coordinates)
    if total_m <= maximum_m:
        return [coordinates]
    line = LineString(coordinates)
    chunks = max(1, math.ceil(total_m / maximum_m))
    output: list[list[tuple[float, float]]] = []
    for index in range(chunks):
        part = substring(line, line.length * index / chunks, line.length * (index + 1) / chunks)
        values = [(float(lon), float(lat)) for lon, lat in part.coords]
        if len(values) >= 2:
            output.append(values)
    return output


class _JunctionCounter(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        self.node_use: Counter[int] = Counter()

    def way(self, way: Any) -> None:
        if runnable_way(way.tags):
            self.node_use.update(node.ref for node in way.nodes)


class _EdgeWriter(osmium.SimpleHandler):
    def __init__(self, node_use: Counter[int], graph_version_id: UUID, region_id: UUID, output_path: Path) -> None:
        super().__init__()
        self.node_use = node_use
        self.graph_version_id = graph_version_id
        self.region_id = region_id
        self.output = output_path.open("w", encoding="utf-8")
        self.count = 0

    def close(self) -> None:
        self.output.close()

    def way(self, way: Any) -> None:
        if not runnable_way(way.tags):
            return
        nodes: list[tuple[int, float, float]] = []
        for node in way.nodes:
            try:
                nodes.append((int(node.ref), float(node.lon), float(node.lat)))
            except osmium.InvalidLocationError:
                return
        if len(nodes) < 2:
            return
        split_indices = [0, *(index for index in range(1, len(nodes) - 1) if self.node_use[nodes[index][0]] > 1), len(nodes) - 1]
        for section_number, (start, end) in enumerate(zip(split_indices, split_indices[1:])):
            section = nodes[start : end + 1]
            coordinates = [(node[1], node[2]) for node in section]
            for chunk_number, chunk in enumerate(split_max_length(coordinates)):
                record = {
                    "id": str(uuid7()),
                    "region_id": str(self.region_id),
                    "graph_version_id": str(self.graph_version_id),
                    "edge_key": f"{way.id}:{section_number}:{chunk_number}",
                    "osm_way_id": int(way.id),
                    "from_node_id": section[0][0],
                    "to_node_id": section[-1][0],
                    "name": way.tags.get("name"),
                    "highway_class": way.tags.get("highway"),
                    "surface": way.tags.get("surface"),
                    "length_m": round(line_length_m(chunk), 3),
                    "geometry": {"type": "LineString", "coordinates": chunk},
                }
                self.output.write(json.dumps(record, separators=(",", ":")) + "\n")
                self.count += 1


def build_edge_file(pbf_path: Path, graph_version_id: UUID, region_id: UUID, output_path: Path) -> int:
    counter = _JunctionCounter()
    counter.apply_file(str(pbf_path), locations=False)
    writer = _EdgeWriter(counter.node_use, graph_version_id, region_id, output_path)
    try:
        writer.apply_file(str(pbf_path), locations=True, idx="sparse_mmap_array")
    finally:
        writer.close()
    return writer.count


async def load_edge_file(session: AsyncSession, edge_file: Path, *, batch_size: int = 2_000) -> int:
    statement = text(
        """
        INSERT INTO activity.street_edges (
          id, region_id, graph_version_id, edge_key, osm_way_id,
          from_node_id, to_node_id, name, highway_class, surface,
          length_m, running_accessible, spatial_cell, geometry,
          created_at, updated_at, version
        ) VALUES (
          CAST(:id AS uuid), CAST(:region_id AS uuid), CAST(:graph_version_id AS uuid),
          :edge_key, :osm_way_id, :from_node_id, :to_node_id, :name,
          :highway_class, :surface, :length_m, TRUE,
          ST_GeoHash(ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326)), 7),
          ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326), NOW(), NOW(), 1
        )
        ON CONFLICT (graph_version_id, edge_key) DO UPDATE SET
          name=EXCLUDED.name, highway_class=EXCLUDED.highway_class,
          surface=EXCLUDED.surface, length_m=EXCLUDED.length_m,
          spatial_cell=EXCLUDED.spatial_cell, geometry=EXCLUDED.geometry,
          running_accessible=TRUE, updated_at=NOW(),
          version=activity.street_edges.version + 1
        """
    )
    loaded = 0
    batch: list[dict] = []
    with edge_file.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            record["geometry"] = json.dumps(record["geometry"], separators=(",", ":"))
            batch.append(record)
            if len(batch) >= batch_size:
                await session.execute(statement, batch)
                await session.commit()
                loaded += len(batch)
                batch = []
    if batch:
        await session.execute(statement, batch)
        await session.commit()
        loaded += len(batch)
    return loaded


async def activate_graph(session: AsyncSession, graph_version_id: UUID) -> dict[str, int | str]:
    graph = await session.get(OSMGraphVersion, graph_version_id, with_for_update=True)
    if graph is None or graph.status not in {"validating", "active"}:
        raise ValueError("graph must be in validating state")
    region = await session.get(OSMRegion, graph.region_id, with_for_update=True)
    if region is None:
        raise ValueError("OSM region does not exist")
    await session.execute(
        select(OSMGraphVersion.id).where(OSMGraphVersion.region_id == region.id).with_for_update()
    )
    edge_count = int(
        await session.scalar(
            text("SELECT COUNT(*) FROM activity.street_edges WHERE graph_version_id=:graph"),
            {"graph": graph.id},
        )
        or 0
    )
    if edge_count < 1:
        raise ValueError("graph has no claim edges")
    settings = get_settings()
    if settings.is_production or settings.valhalla_graph_bucket:
        if not settings.valhalla_graph_bucket:
            raise ValueError("VALHALLA_GRAPH_BUCKET is required for graph activation")

        def verify_graph_artifact() -> None:
            from google.cloud import storage

            blob = storage.Client(project=settings.gcp_project_id or None).bucket(settings.valhalla_graph_bucket).blob(graph.graph_object)
            blob.reload()
            artifact_hash = (blob.metadata or {}).get("sha256")
            if artifact_hash != graph.graph_hash:
                raise ValueError("Valhalla graph artifact hash does not match the registered graph")

        try:
            await anyio.to_thread.run_sync(verify_graph_artifact)
        except Exception as exc:
            raise ValueError("Valhalla graph artifact is missing or failed integrity verification") from exc
    if graph.status == "active":
        return {"graph_version_id": str(graph.id), "edge_count": edge_count, "alias_count": 0}
    old_graph_ids = list(
        await session.scalars(
            select(OSMGraphVersion.id).where(
                OSMGraphVersion.region_id == region.id,
                OSMGraphVersion.status == "active",
                OSMGraphVersion.id != graph.id,
            )
        )
    )
    alias_count = 0
    if old_graph_ids:
        candidates = await session.stream(
            text(
                """
                SELECT old.id AS old_edge_id, fresh.id AS new_edge_id,
                  LEAST(old.length_m, fresh.length_m) /
                    NULLIF(GREATEST(old.length_m, fresh.length_m), 0) AS overlap_ratio
                FROM activity.street_edges old
                JOIN activity.street_edges fresh
                  ON fresh.graph_version_id=:new_graph
                 AND fresh.osm_way_id=old.osm_way_id
                 AND ST_HausdorffDistance(
                   ST_Transform(old.geometry, 3857),
                   ST_Transform(fresh.geometry, 3857)
                 ) <= 15
                WHERE old.graph_version_id=ANY(CAST(:old_graphs AS uuid[]))
                  AND LEAST(old.length_m, fresh.length_m) /
                    NULLIF(GREATEST(old.length_m, fresh.length_m), 0) >= 0.80
                """
            ),
            {"new_graph": graph.id, "old_graphs": old_graph_ids},
        )
        alias_insert = text(
            """
            INSERT INTO activity.street_edge_aliases (
              id, old_edge_id, new_edge_id, overlap_ratio, relation_type
            ) VALUES (
              CAST(:id AS uuid), :old_edge_id, :new_edge_id,
              :overlap_ratio, 'graph_lineage'
            ) ON CONFLICT (old_edge_id, new_edge_id) DO NOTHING
            """
        )
        async for partition in candidates.partitions(2_000):
            values = [
                {
                    "id": str(uuid7()),
                    "old_edge_id": row.old_edge_id,
                    "new_edge_id": row.new_edge_id,
                    "overlap_ratio": row.overlap_ratio,
                }
                for row in partition
            ]
            await session.execute(alias_insert, values)
        alias_count = int(
            await session.scalar(
                text(
                    """
                    SELECT COUNT(*)
                    FROM activity.street_edge_aliases alias
                    JOIN activity.street_edges fresh ON fresh.id=alias.new_edge_id
                    WHERE fresh.graph_version_id=:graph
                    """
                ),
                {"graph": graph.id},
            )
            or 0
        )
        await session.execute(
            text("UPDATE activity.osm_graph_versions SET status='retired', updated_at=NOW(), version=version+1 WHERE id=ANY(CAST(:ids AS uuid[]))"),
            {"ids": old_graph_ids},
        )
    graph.status = "active"
    graph.activated_at = datetime.now(timezone.utc)
    graph.version += 1
    region.status = "active"
    region.version += 1
    await enqueue_event(
        session,
        topic="maintenance",
        event_type="maps.graph.activated",
        aggregate_type="osm_graph_version",
        aggregate_id=graph.id,
        payload={
            "region_id": str(region.id),
            "graph_version_id": str(graph.id),
            "retired_graph_ids": [str(value) for value in old_graph_ids],
        },
    )
    await session.flush()
    return {"graph_version_id": str(graph.id), "edge_count": edge_count, "alias_count": alias_count}
