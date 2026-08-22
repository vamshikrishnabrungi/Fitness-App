from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import osmium
from shapely.geometry import LineString
from shapely.ops import substring
from sqlalchemy import text

from backend.geo_db import get_geo_engine
from backend.platform_ids import new_id


MAX_EDGE_LENGTH_M = 100.0
RUNNABLE_HIGHWAYS = {
    "footway",
    "path",
    "pedestrian",
    "living_street",
    "residential",
    "service",
    "track",
    "steps",
    "unclassified",
    "tertiary",
}
BLOCKED_ACCESS = {"no", "private"}


def runnable_way(tags: Any) -> bool:
    highway = tags.get("highway")
    if highway not in RUNNABLE_HIGHWAYS:
        return False
    if tags.get("access") in BLOCKED_ACCESS or tags.get("foot") in BLOCKED_ACCESS:
        return False
    if tags.get("construction") or highway in {"construction", "proposed"}:
        return False
    if highway == "tertiary" and tags.get("sidewalk") in {None, "no", "none"} and tags.get("foot") not in {"yes", "designated"}:
        return False
    return True


class JunctionCounter(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.node_use: Counter[int] = Counter()

    def way(self, way: Any) -> None:
        if not runnable_way(way.tags):
            return
        self.node_use.update(node.ref for node in way.nodes)


def _haversine_m(a: Sequence[float], b: Sequence[float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _line_length_m(coordinates: Sequence[Sequence[float]]) -> float:
    return sum(_haversine_m(coordinates[index - 1], coordinates[index]) for index in range(1, len(coordinates)))


def _split_max_length(coordinates: List[Tuple[float, float]], max_length_m: float) -> List[List[Tuple[float, float]]]:
    if len(coordinates) < 2:
        return []
    total_m = _line_length_m(coordinates)
    if total_m <= max_length_m:
        return [coordinates]
    line = LineString(coordinates)
    chunks = max(1, math.ceil(total_m / max_length_m))
    parts = []
    for index in range(chunks):
        start = line.length * index / chunks
        end = line.length * (index + 1) / chunks
        part = substring(line, start, end)
        coords = list(part.coords)
        if len(coords) >= 2:
            parts.append(coords)
    return parts


class EdgeWriter(osmium.SimpleHandler):
    def __init__(
        self,
        node_use: Counter[int],
        graph_version: str,
        output_path: Path,
    ):
        super().__init__()
        self.node_use = node_use
        self.graph_version = graph_version
        self.output = output_path.open("w", encoding="utf-8")
        self.count = 0

    def close(self) -> None:
        self.output.close()

    def way(self, way: Any) -> None:
        if not runnable_way(way.tags):
            return
        nodes = []
        for node in way.nodes:
            try:
                nodes.append((node.ref, float(node.lon), float(node.lat)))
            except osmium.InvalidLocationError:
                return
        if len(nodes) < 2:
            return
        split_indices = [0]
        split_indices.extend(
            index
            for index in range(1, len(nodes) - 1)
            if self.node_use[nodes[index][0]] > 1
        )
        split_indices.append(len(nodes) - 1)
        for section_index in range(1, len(split_indices)):
            start_index = split_indices[section_index - 1]
            end_index = split_indices[section_index]
            section_nodes = nodes[start_index : end_index + 1]
            coordinates = [(item[1], item[2]) for item in section_nodes]
            for chunk_index, chunk in enumerate(_split_max_length(coordinates, MAX_EDGE_LENGTH_M)):
                stable_key = (
                    f"runlete:osm-edge:{self.graph_version}:{way.id}:"
                    f"{section_nodes[0][0]}:{section_nodes[-1][0]}:{chunk_index}"
                )
                edge_id = new_id()
                record = {
                    "id": edge_id,
                    "source_key": stable_key,
                    "osm_way_id": int(way.id),
                    "osm_from_node_id": int(section_nodes[0][0]),
                    "osm_to_node_id": int(section_nodes[-1][0]),
                    "name": way.tags.get("name"),
                    "highway": way.tags.get("highway"),
                    "surface": way.tags.get("surface"),
                    "distance_m": round(_line_length_m(chunk), 3),
                    "access": {
                        "access": way.tags.get("access"),
                        "foot": way.tags.get("foot"),
                        "sidewalk": way.tags.get("sidewalk"),
                        "lit": way.tags.get("lit"),
                    },
                    "geometry": {"type": "LineString", "coordinates": chunk},
                }
                self.output.write(json.dumps(record, separators=(",", ":")) + "\n")
                self.count += 1


def build_edge_file(pbf_path: Path, graph_version: str, output_path: Path) -> int:
    counter = JunctionCounter()
    counter.apply_file(str(pbf_path), locations=False)
    writer = EdgeWriter(counter.node_use, graph_version, output_path)
    try:
        writer.apply_file(
            str(pbf_path),
            locations=True,
            idx="sparse_mmap_array",
        )
    finally:
        writer.close()
    return writer.count


async def load_edge_file(
    edge_file: Path,
    osm_region_id: str,
    graph_version_id: str,
    *,
    batch_size: int = 2_000,
) -> int:
    engine = get_geo_engine()
    if engine is None:
        raise RuntimeError("POSTGRES_URL is required")
    loaded = 0
    batch: List[Dict[str, Any]] = []

    async def flush(items: List[Dict[str, Any]]) -> None:
        nonlocal loaded
        if not items:
            return
        async with engine.begin() as connection:
            for edge in items:
                await connection.execute(
                    text(
                        """
                        INSERT INTO street_edges (
                            street_edge_id, id, osm_region_id, graph_version_id,
                            osm_way_id, osm_from_node_id, osm_to_node_id,
                            spatial_cell, name, highway, surface, distance_m, edge, access,
                            metadata, status, updated_at
                        ) VALUES (
                            :source_key, CAST(:id AS uuid), CAST(:region AS uuid),
                            CAST(:graph AS uuid), :way, :from_node, :to_node,
                            ST_GeoHash(
                                ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326)),
                                5
                            ),
                            :name, :highway, :surface, :distance,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                            CAST(:access AS jsonb),
                            jsonb_build_object('source', 'openstreetmap'), 'staging', NOW()
                        )
                        ON CONFLICT (street_edge_id) DO UPDATE SET
                            graph_version_id=EXCLUDED.graph_version_id,
                            name=EXCLUDED.name, highway=EXCLUDED.highway,
                            surface=EXCLUDED.surface, distance_m=EXCLUDED.distance_m,
                            edge=EXCLUDED.edge, access=EXCLUDED.access,
                            spatial_cell=EXCLUDED.spatial_cell,
                            status='staging', updated_at=NOW()
                        """
                    ),
                    {
                        "source_key": edge["source_key"],
                        "id": edge["id"],
                        "region": osm_region_id,
                        "graph": graph_version_id,
                        "way": edge["osm_way_id"],
                        "from_node": edge["osm_from_node_id"],
                        "to_node": edge["osm_to_node_id"],
                        "name": edge["name"],
                        "highway": edge["highway"],
                        "surface": edge["surface"],
                        "distance": edge["distance_m"],
                        "geometry": json.dumps(edge["geometry"]),
                        "access": json.dumps(edge["access"]),
                    },
                )
            loaded += len(items)

    with edge_file.open(encoding="utf-8") as handle:
        for line in handle:
            batch.append(json.loads(line))
            if len(batch) >= batch_size:
                await flush(batch)
                batch = []
        await flush(batch)
    return loaded


async def main_async(args: argparse.Namespace) -> None:
    count = build_edge_file(args.pbf, args.graph_version, args.output)
    print(f"built {count} canonical road edges at {args.output}")
    if args.osm_region_id and args.graph_version_id:
        loaded = await load_edge_file(
            args.output, args.osm_region_id, args.graph_version_id
        )
        print(f"loaded {loaded} edges into PostGIS")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Runlete claim edges from an OSM PBF")
    parser.add_argument("pbf", type=Path)
    parser.add_argument("--graph-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--osm-region-id")
    parser.add_argument("--graph-version-id")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
