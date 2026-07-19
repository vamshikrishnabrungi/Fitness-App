"""Territory capture engine — pure functions (no DB / map / AI).

The core game math: a GPS trace earns *influence* on the running-corridor segments it
covers; influence decays over a rolling window; the club with the most fresh influence
owns a segment/corridor; ownership + the gap yields a human status
(Strong / Under attack / Easy capture / Contested / Enemy stronghold / Neutral).

Ownership is presence-based (meters run), never effort/pace/elevation — fair across
terrain. Road *value* (popularity/connectivity) is applied as a multiplier elsewhere;
this module is the geometry + influence + status core.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from math import radians, sin, cos, asin, sqrt
from typing import Dict, List, Sequence, Tuple

Point = Tuple[float, float]  # (lat, lng)

EARTH_M = 6_371_000.0
DEFAULT_SEGMENT_M = 150.0     # ~150 m capture units (invisible to users)
MATCH_TOLERANCE_M = 30.0      # GPS point counts as "on" a segment within this
INFLUENCE_WINDOW_DAYS = 30    # older runs stop counting
INFLUENCE_HALF_LIFE_DAYS = 15 # fresh runs count double a 15-day-old run


# ---------- geometry ----------
def haversine_m(a: Point, b: Point) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (a[0], a[1], b[0], b[1]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_M * asin(sqrt(h))


def polyline_length_m(points: Sequence[Point]) -> float:
    return sum(haversine_m(points[i - 1], points[i]) for i in range(1, len(points)))


def _to_local_m(p: Point, ref: Point) -> Tuple[float, float]:
    """Equirectangular projection to meters relative to ref — accurate at running scale."""
    x = radians(p[1] - ref[1]) * cos(radians(ref[0])) * EARTH_M
    y = radians(p[0] - ref[0]) * EARTH_M
    return x, y


def _point_to_edge_m(p: Point, a: Point, b: Point) -> float:
    px, py = _to_local_m(p, p)  # (0,0)
    ax, ay = _to_local_m(a, p)
    bx, by = _to_local_m(b, p)
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return sqrt(ax * ax + ay * ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return sqrt((px - cx) ** 2 + (py - cy) ** 2)


def point_to_polyline_m(p: Point, line: Sequence[Point]) -> float:
    return min(_point_to_edge_m(p, line[i - 1], line[i]) for i in range(1, len(line)))


def split_into_segments(points: Sequence[Point], seg_len_m: float = DEFAULT_SEGMENT_M) -> List[List[Point]]:
    """Cut a corridor polyline into ~seg_len_m pieces (the invisible capture units)."""
    if len(points) < 2:
        return []
    segments: List[List[Point]] = []
    cur: List[Point] = [tuple(points[0])]
    acc = 0.0
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        d = haversine_m(a, b)
        if d == 0:
            continue
        remaining = d
        start = a
        while acc + remaining >= seg_len_m:
            need = seg_len_m - acc
            frac = need / remaining
            cut = (start[0] + (b[0] - start[0]) * frac, start[1] + (b[1] - start[1]) * frac)
            cur.append(cut)
            segments.append(cur)
            cur = [cut]
            start = cut
            remaining -= need
            acc = 0.0
        cur.append(tuple(b))
        acc += remaining
    if len(cur) >= 2:
        # Merge a short trailing remainder into the previous segment (no degenerate stubs).
        if segments and polyline_length_m(cur) < seg_len_m * 0.5:
            segments[-1].extend(cur[1:])
        else:
            segments.append(cur)
    return segments


# ---------- map-matching (proximity) ----------
def match_trace_to_segments(trace: Sequence[Point], segments: Sequence[Sequence[Point]],
                            tol_m: float = MATCH_TOLERANCE_M) -> Dict[int, float]:
    """Meters of `trace` that ran on each corridor segment (nearest within tol). No OSRM needed."""
    meters: Dict[int, float] = defaultdict(float)
    for i in range(1, len(trace)):
        p0, p1 = trace[i - 1], trace[i]
        step = haversine_m(p0, p1)
        if step == 0:
            continue
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        best_idx, best_dist = None, tol_m
        for idx, seg in enumerate(segments):
            d = point_to_polyline_m(mid, seg)
            if d < best_dist:
                best_dist, best_idx = d, idx
        if best_idx is not None:
            meters[best_idx] += step
    return dict(meters)


# ---------- influence + ownership ----------
def freshness_weight(ts: datetime, now: datetime,
                     half_life_days: float = INFLUENCE_HALF_LIFE_DAYS,
                     window_days: int = INFLUENCE_WINDOW_DAYS) -> float:
    age_days = (now - ts).total_seconds() / 86400.0
    if age_days < 0:
        age_days = 0.0
    if age_days >= window_days:
        return 0.0
    return 0.5 ** (age_days / half_life_days)


def influence_by_club(contributions: Sequence[dict], now: datetime) -> Dict[str, float]:
    """contributions: [{club_id, meters, ts}] -> fresh influence per club (decayed)."""
    out: Dict[str, float] = defaultdict(float)
    for c in contributions:
        w = freshness_weight(c["ts"], now)
        if w > 0:
            out[c["club_id"]] += float(c["meters"]) * w
    return dict(out)


def owner_of(contributions: Sequence[dict], now: datetime) -> Tuple[str | None, Dict[str, float]]:
    by_club = influence_by_club(contributions, now)
    if not by_club:
        return None, {}
    owner = max(by_club, key=by_club.get)
    return owner, by_club


# ---------- status (player's-club view) ----------
def corridor_status(your_influence: float, rival_influence: float, you_own: bool) -> str:
    """Human status from the perspective of the player's club."""
    total = your_influence + rival_influence
    share = (your_influence / total) if total > 0 else 0.0
    if you_own:
        return "strong" if share >= 0.6 else "under_attack"
    if total == 0:
        return "neutral"
    if share >= 0.45:
        return "easy_capture"
    if share >= 0.30:
        return "contested"
    return "enemy_stronghold"


def meters_to_flip(your_influence: float, rival_influence: float) -> float:
    """Fresh meters you must add to overtake the current leader (rough — ignores their decay)."""
    return max(0.0, (rival_influence - your_influence) + 1.0)
