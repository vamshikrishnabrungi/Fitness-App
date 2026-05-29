"""Anti-cheat GPS validation for runs and treks.

Catches obvious garbage:
- Too few points / too short duration / too short distance
- Single-segment teleport (speed > config.RUN_TELEPORT_SPEED_MPS)
- Average speed exceeding the activity ceiling
"""
from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from typing import Any, Dict, List, Sequence, Tuple

from backend.core.config import (
    RUN_MAX_SPEED_MPS,
    RUN_MIN_DISTANCE_KM,
    RUN_MIN_DURATION_SEC,
    RUN_MIN_POINTS,
    RUN_TELEPORT_SPEED_MPS,
    TREK_MAX_SPEED_MPS,
)


def haversine_m(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    lat1, lng1 = radians(float(a['latitude'])), radians(float(a['longitude']))
    lat2, lng2 = radians(float(b['latitude'])), radians(float(b['longitude']))
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * 6371000.0 * atan2(sqrt(h), sqrt(max(0.0, 1 - h)))


def _ts_seconds(point: Dict[str, Any]) -> float | None:
    ts = point.get('timestamp')
    if ts is None:
        return None
    try:
        from datetime import datetime
        s = str(ts)
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return None


def validate_run(
    path: Sequence[Dict[str, Any]],
    *,
    duration_seconds: float,
    activity: str = 'run',
) -> Dict[str, Any]:
    """Return a verdict dict.

    {
        'valid': bool,
        'reasons': [str],
        'flags': [str],          # non-fatal warnings
        'distance_m': float,
        'avg_speed_mps': float,
        'max_segment_speed_mps': float,
    }
    """
    reasons: List[str] = []
    flags: List[str] = []
    points = [p for p in path if p.get('latitude') is not None and p.get('longitude') is not None]
    n = len(points)

    if n < RUN_MIN_POINTS:
        reasons.append(f'fewer_than_{RUN_MIN_POINTS}_points')

    distance_m = 0.0
    max_seg_speed = 0.0
    teleport_segments = 0
    for i in range(1, n):
        seg = haversine_m(points[i - 1], points[i])
        distance_m += seg
        t0 = _ts_seconds(points[i - 1])
        t1 = _ts_seconds(points[i])
        if t0 is not None and t1 is not None and t1 > t0:
            seg_speed = seg / (t1 - t0)
            if seg_speed > max_seg_speed:
                max_seg_speed = seg_speed
            if seg_speed > RUN_TELEPORT_SPEED_MPS:
                teleport_segments += 1

    if teleport_segments:
        reasons.append(f'{teleport_segments}_teleport_segment(s)')

    if distance_m < RUN_MIN_DISTANCE_KM * 1000:
        reasons.append('distance_below_minimum')

    if duration_seconds < RUN_MIN_DURATION_SEC:
        reasons.append('duration_below_minimum')

    avg_speed = distance_m / duration_seconds if duration_seconds > 0 else 0.0
    ceiling = RUN_MAX_SPEED_MPS if activity == 'run' else TREK_MAX_SPEED_MPS
    if avg_speed > ceiling:
        reasons.append(f'avg_speed_above_{ceiling}_mps')
    elif max_seg_speed > ceiling * 1.4 and not teleport_segments:
        flags.append(f'segment_above_{ceiling * 1.4}_mps')

    return {
        'valid': not reasons,
        'reasons': reasons,
        'flags': flags,
        'distance_m': round(distance_m, 1),
        'avg_speed_mps': round(avg_speed, 2),
        'max_segment_speed_mps': round(max_seg_speed, 2),
    }


def elevation_gain_m(path: Sequence[Dict[str, Any]]) -> float:
    gain = 0.0
    prev: float | None = None
    for p in path:
        alt = p.get('altitude')
        if alt is None:
            continue
        try:
            value = float(alt)
        except Exception:
            continue
        if prev is not None and value > prev:
            gain += value - prev
        prev = value
    return round(gain, 1)
