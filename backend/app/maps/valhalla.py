from __future__ import annotations

import math
from dataclasses import dataclass

import httpx

from backend.app.activities.processing import Sample
from backend.app.maps.polyline import InvalidPolyline, decode_polyline6


class MapMatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class MatchedWay:
    sequence: int
    way_id: int
    length_m: float
    source_percent: float
    target_percent: float
    begin_shape_index: int
    end_shape_index: int


@dataclass(frozen=True)
class MatchResult:
    path: tuple[dict[str, float], ...]
    ways: tuple[MatchedWay, ...]
    confidence: float
    matched_point_ratio: float
    mean_snap_distance_m: float
    osm_changeset: int | None


def normalized_confidence(matched_points: list[dict]) -> tuple[float, float, float]:
    """Return the versioned Runlete match score, coverage, and mean snap distance."""

    if not matched_points:
        return 0.0, 0.0, math.inf
    accepted = [point for point in matched_points if point.get("type") not in {"unmatched", None}]
    ratio = len(accepted) / len(matched_points)
    distances = [max(0.0, float(point.get("distance_from_trace_point", 50.0))) for point in accepted]
    mean_distance = sum(distances) / len(distances) if distances else math.inf
    distance_quality = max(0.0, 1.0 - mean_distance / 50.0) if math.isfinite(mean_distance) else 0.0
    return min(1.0, 0.7 * distance_quality + 0.3 * ratio), ratio, mean_distance


async def match_trace(base_url: str, samples: tuple[Sample, ...]) -> MatchResult:
    request = {
        "shape": [
            {
                "lat": sample.latitude,
                "lon": sample.longitude,
                "time": int(sample.timestamp.timestamp()),
                "accuracy": sample.accuracy,
            }
            for sample in samples
        ],
        "shape_match": "map_snap",
        "costing": "pedestrian",
        "use_timestamps": True,
        "directions_options": {"units": "kilometers"},
        "filters": {
            "action": "include",
            "attributes": [
                "edge.way_id",
                "edge.length",
                "edge.source_percent_along",
                "edge.target_percent_along",
                "edge.begin_shape_index",
                "edge.end_shape_index",
                "shape",
                "matched.point",
                "matched.type",
                "matched.distance_from_trace_point",
                "osm_changeset",
            ],
        },
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{base_url.rstrip('/')}/trace_attributes", json=request)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise MapMatchError("Valhalla map matching failed") from exc
    confidence, ratio, mean_distance = normalized_confidence(data.get("matched_points") or [])
    try:
        path = tuple(decode_polyline6(data.get("shape") or ""))
    except InvalidPolyline as exc:
        raise MapMatchError("Valhalla returned an invalid matched shape") from exc
    if len(path) < 2:
        raise MapMatchError("Valhalla returned no matched geometry")
    ways = tuple(
        MatchedWay(
            sequence=index,
            way_id=int(edge["way_id"]),
            length_m=float(edge.get("length", 0)) * 1000,
            source_percent=float(edge.get("source_percent_along", 0.0)),
            target_percent=float(edge.get("target_percent_along", 1.0)),
            begin_shape_index=int(edge.get("begin_shape_index", 0)),
            end_shape_index=int(edge.get("end_shape_index", 0)),
        )
        for index, edge in enumerate(data.get("edges") or [])
        if edge.get("way_id") is not None
    )
    return MatchResult(path, ways, confidence, ratio, mean_distance, data.get("osm_changeset"))
