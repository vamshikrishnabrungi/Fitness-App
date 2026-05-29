"""H3 hexagonal grid helpers for territory features.

Resolution 9 → ~174m edge, ~0.105 km² per cell. Good balance between
"city block" granularity and total cell count for a moderate-size urban map.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

import h3

from backend.core.config import H3_RESOLUTION


# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------

def cell_for(lat: float, lng: float, resolution: int = H3_RESOLUTION) -> str:
    return h3.latlng_to_cell(lat, lng, resolution)


def cell_centre(cell: str) -> Tuple[float, float]:
    """Return (lat, lng) of the hex centre."""
    lat, lng = h3.cell_to_latlng(cell)
    return lat, lng


def cell_polygon(cell: str) -> List[List[float]]:
    """Return the hex boundary as [[lng, lat], ...] suitable for GeoJSON."""
    boundary = h3.cell_to_boundary(cell)
    # h3 returns [(lat, lng), ...]; GeoJSON wants [lng, lat]
    ring = [[lng, lat] for lat, lng in boundary]
    # close the ring
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def cell_area_km2(cell: str) -> float:
    try:
        return float(h3.cell_area(cell, unit='km^2'))
    except Exception:
        return 0.0


def cells_in_bbox(
    south: float,
    west: float,
    north: float,
    east: float,
    resolution: int = H3_RESOLUTION,
    cap: int = 5000,
) -> List[str]:
    """Return the H3 cells whose centres fall inside the lat/lng bbox.

    The bbox is provided as (south, west, north, east) - south < north, west < east.
    Uses ``h3.polygon_to_cells`` against a rectangular polygon.
    """
    if south >= north or west >= east:
        return []
    # GeoJSON-style polygon: [[lng, lat], ...] with first==last, h3 expects LatLngPoly
    poly = h3.LatLngPoly(
        [
            (south, west),
            (south, east),
            (north, east),
            (north, west),
        ]
    )
    cells = h3.polygon_to_cells(poly, res=resolution)
    if len(cells) > cap:
        return list(cells)[:cap]
    return list(cells)


def cells_for_path(path: Sequence[Dict[str, Any]], resolution: int = H3_RESOLUTION) -> List[str]:
    """Convert a GPS path (list of {latitude, longitude}) into the set of unique
    H3 cells visited, preserving order of first visit."""
    seen: Dict[str, None] = {}
    prev_cell: str | None = None

    for point in path:
        lat = point.get('latitude')
        lng = point.get('longitude')
        if lat is None or lng is None:
            continue
        cell = cell_for(float(lat), float(lng), resolution)
        if cell != prev_cell:
            # fill any gap (two adjacent points may sit in non-neighbouring cells)
            if prev_cell is not None:
                try:
                    line = h3.grid_path_cells(prev_cell, cell)
                except Exception:
                    line = [cell]
                for c in line:
                    if c not in seen:
                        seen[c] = None
            elif cell not in seen:
                seen[cell] = None
            prev_cell = cell

    return list(seen.keys())


def cells_to_geojson(cells: Iterable[str], properties_fn=None) -> Dict[str, Any]:
    """Return a FeatureCollection of hex polygons. ``properties_fn`` may take a
    cell id and return the per-feature properties dict."""
    features: List[Dict[str, Any]] = []
    for cell in cells:
        if not cell:
            continue
        ring = cell_polygon(cell)
        if not ring:
            continue
        props = properties_fn(cell) if properties_fn else {'cell': cell}
        features.append({
            'type': 'Feature',
            'id': cell,
            'geometry': {'type': 'Polygon', 'coordinates': [ring]},
            'properties': props,
        })
    return {'type': 'FeatureCollection', 'features': features}
