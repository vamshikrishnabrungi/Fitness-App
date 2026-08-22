from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Sequence

from pydantic import BaseModel, Field, field_validator

from backend.activity_domain import haversine_m, parse_datetime


class GeoPoint(BaseModel):
    latitude: float
    longitude: float
    altitude: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if not -180 <= value <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return value


class RouteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    path: List[GeoPoint] = Field(min_length=2, max_length=10_000)
    visibility: Literal["private", "clubs", "public"] = "private"
    club_ids: List[str] = Field(default_factory=list, max_length=100)
    surface: Literal["any", "paved", "trail", "mixed"] = "any"
    description: Optional[str] = Field(default=None, max_length=1_000)


class RouteGenerate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    target_distance_km: float = Field(ge=1, le=50)
    surface: Literal["any", "paved", "trail", "mixed"] = "any"
    minimize_hills: bool = False


class SegmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    path: List[GeoPoint] = Field(min_length=2, max_length=5_000)
    visibility: Literal["clubs", "public"] = "public"
    club_ids: List[str] = Field(default_factory=list, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1_000)


class StreetEdgeCreate(BaseModel):
    id: str = Field(min_length=1, max_length=160)
    name: Optional[str] = Field(default=None, max_length=200)
    path: List[GeoPoint] = Field(min_length=2, max_length=1_000)
    highway: Optional[str] = Field(default=None, max_length=80)
    surface: Optional[str] = Field(default=None, max_length=80)


class StreetEdgeBatch(BaseModel):
    edges: List[StreetEdgeCreate] = Field(min_length=1, max_length=10_000)


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    metric: Literal["distance_km", "moving_time_sec", "run_count", "elevation_gain_m"]
    target: float = Field(gt=0)
    period_start: datetime
    period_end: datetime

    @field_validator("period_end")
    @classmethod
    def validate_period_end(cls, value: datetime, info):
        start = info.data.get("period_start")
        if start and value <= start:
            raise ValueError("period_end must be after period_start")
        return value


class ChallengeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    challenge_type: Literal[
        "distance",
        "moving_time",
        "consistency",
        "fastest_5k",
        "club_distance",
    ]
    starts_at: datetime
    ends_at: datetime
    target: Optional[float] = Field(default=None, gt=0)
    club_ids: List[str] = Field(default_factory=list)
    visibility: Literal["private", "clubs", "public"] = "private"

    @field_validator("ends_at")
    @classmethod
    def validate_ends_at(cls, value: datetime, info):
        start = info.data.get("starts_at")
        if start and value <= start:
            raise ValueError("ends_at must be after starts_at")
        return value


class RaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    route_id: str = Field(min_length=1, max_length=160)
    starts_at: datetime
    start_window_minutes: int = Field(default=30, ge=5, le=180)
    max_finish_minutes: int = Field(default=360, ge=15, le=1_440)
    visibility: Literal["clubs", "public"] = "clubs"
    club_ids: List[str] = Field(default_factory=list, max_length=100)


def path_metrics(path: Sequence[Any]) -> Dict[str, Any]:
    points = [point.model_dump() if isinstance(point, GeoPoint) else dict(point) for point in path]
    distance_m = 0.0
    elevation_gain_m = 0.0
    for index in range(1, len(points)):
        distance_m += haversine_m(points[index - 1], points[index])
        previous_altitude = points[index - 1].get("altitude")
        altitude = points[index].get("altitude")
        if previous_altitude is not None and altitude is not None:
            gain = float(altitude) - float(previous_altitude)
            if gain >= 1.5:
                elevation_gain_m += gain
    return {
        "distance_m": round(distance_m, 1),
        "distance_km": round(distance_m / 1000.0, 3),
        "elevation_gain_m": round(elevation_gain_m, 1),
        "geometry": {
            "type": "LineString",
            "coordinates": [[point["longitude"], point["latitude"]] for point in points],
        },
        "path": points,
    }


def _distance_to_path(point: Dict[str, Any], path: Sequence[Dict[str, Any]]) -> float:
    return min((haversine_m(point, candidate) for candidate in path), default=float("inf"))


def match_segment_effort(
    activity_stream: Sequence[Dict[str, Any]],
    segment_path: Sequence[Dict[str, Any]],
    *,
    endpoint_tolerance_m: float = 50.0,
    shape_tolerance_m: float = 75.0,
) -> Optional[Dict[str, Any]]:
    """Match ordered endpoints and reject shortcuts that do not follow the shape."""
    if len(activity_stream) < 2 or len(segment_path) < 2:
        return None
    segment_start = segment_path[0]
    segment_end = segment_path[-1]

    best: Optional[Dict[str, Any]] = None
    for start_index, activity_point in enumerate(activity_stream[:-1]):
        if haversine_m(activity_point, segment_start) > endpoint_tolerance_m:
            continue
        for end_index in range(start_index + 1, len(activity_stream)):
            end_point = activity_stream[end_index]
            if haversine_m(end_point, segment_end) > endpoint_tolerance_m:
                continue
            matched_path = activity_stream[start_index:end_index + 1]
            # Check representative segment points against the athlete trace.
            sample_step = max(1, len(segment_path) // 12)
            shape_samples = list(segment_path[::sample_step])
            if segment_path[-1] not in shape_samples:
                shape_samples.append(segment_path[-1])
            max_deviation = max(_distance_to_path(point, matched_path) for point in shape_samples)
            if max_deviation > shape_tolerance_m:
                continue

            start_time = parse_datetime(activity_point.get("timestamp"))
            end_time = parse_datetime(end_point.get("timestamp"))
            if not start_time or not end_time or end_time <= start_time:
                continue
            elapsed = int(round((end_time - start_time).total_seconds()))
            candidate = {
                "start_index": start_index,
                "end_index": end_index,
                "started_at": start_time,
                "ended_at": end_time,
                "elapsed_time_sec": elapsed,
                "max_deviation_m": round(max_deviation, 1),
            }
            if best is None or elapsed < best["elapsed_time_sec"]:
                best = candidate
    return best


def goal_progress(goal: Dict[str, Any], activities: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    metric = goal["metric"]
    start = parse_datetime(goal.get("period_start"))
    end = parse_datetime(goal.get("period_end"))
    eligible = []
    for activity in activities:
        started_at = parse_datetime(activity.get("started_at") or activity.get("start_time"))
        if not started_at or (start and started_at < start) or (end and started_at > end):
            continue
        if activity.get("status") == "deleted":
            continue
        eligible.append(activity)
    if metric == "run_count":
        current = float(len(eligible))
    else:
        current = sum(float(activity.get(metric) or 0) for activity in eligible)
        if metric == "distance_km" and not current:
            current = sum(float(activity.get("distance_m") or 0) / 1000.0 for activity in eligible)
    target = float(goal["target"])
    return {
        "current": round(current, 2),
        "target": target,
        "progress": round(min(1.0, current / target), 4) if target > 0 else 0,
        "completed": current >= target,
    }


def challenge_score(challenge_type: str, activities: Sequence[Dict[str, Any]]) -> Optional[float]:
    if challenge_type == "distance" or challenge_type == "club_distance":
        return round(sum(float(item.get("distance_km") or 0) for item in activities), 3)
    if challenge_type == "moving_time":
        return float(sum(int(item.get("moving_time_sec") or 0) for item in activities))
    if challenge_type == "consistency":
        days = {
            str(item.get("date") or str(item.get("started_at") or "")[:10])
            for item in activities
        }
        return float(len(days - {""}))
    if challenge_type == "fastest_5k":
        efforts = [
            effort["elapsed_time_sec"]
            for activity in activities
            for effort in activity.get("best_efforts") or []
            if effort.get("name") == "5k"
        ]
        # Negative time makes the normal descending leaderboard put faster first.
        return float(-min(efforts)) if efforts else None
    return None
