from __future__ import annotations

from bisect import bisect_left
from datetime import datetime
from math import atan2, cos, isfinite, radians, sin, sqrt
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator


SCHEMA_VERSION = 1
COMPUTATION_VERSION = "activity-v1"
MIN_MOVING_SPEED_MPS = 0.5
MAX_RUNNING_SPEED_MPS = 12.5
MAX_ACCEPTED_ACCURACY_M = 100.0
MAX_SAMPLE_GAP_SECONDS = 120.0
MIN_DISTANCE_INCREMENT_M = 2.0
BENCHMARK_DISTANCES_M: Tuple[Tuple[str, float], ...] = (
    ("400m", 400.0),
    ("1k", 1_000.0),
    ("1mile", 1_609.344),
    ("5k", 5_000.0),
    ("10k", 10_000.0),
    ("half_marathon", 21_097.5),
    ("marathon", 42_195.0),
)


class ActivityPoint(BaseModel):
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    accuracy: Optional[float] = None
    heart_rate: Optional[int] = None
    cadence: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if not isfinite(value) or not -90 <= value <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if not isfinite(value) or not -180 <= value <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return value

    @field_validator("accuracy")
    @classmethod
    def validate_accuracy(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (not isfinite(value) or value < 0):
            raise ValueError("accuracy must be a non-negative number")
        return value


class ActivityCreate(BaseModel):
    gps_path: List[ActivityPoint] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    paused_duration_sec: int = Field(default=0, ge=0)
    source: Literal[
        "runlete",
        "manual",
        "apple_health",
        "health_connect",
        "gpx",
        "tcx",
        "fit",
        "garmin",
        "coros",
        "polar",
        "suunto",
    ] = "runlete"
    activity_type: Literal["run", "treadmill"] = "run"
    run_type: Literal["training", "race", "workout", "commute"] = "training"
    title: Optional[str] = None
    visibility: Optional[Literal["private", "clubs", "public"]] = None
    distance_m: Optional[float] = Field(default=None, ge=0)
    moving_time_sec: Optional[int] = Field(default=None, ge=0)
    elapsed_time_sec: Optional[int] = Field(default=None, ge=0)
    elevation_gain_m: Optional[float] = Field(default=None, ge=0)
    calories_kcal: Optional[int] = Field(default=None, ge=0)
    average_heart_rate: Optional[int] = Field(default=None, ge=20, le=260)
    max_heart_rate: Optional[int] = Field(default=None, ge=20, le=260)
    average_cadence: Optional[float] = Field(default=None, ge=0)
    gear_id: Optional[str] = None
    notes: Optional[str] = None
    timezone: str = Field(default="UTC", min_length=1, max_length=80)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value


class ActivityUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    run_type: Optional[Literal["training", "race", "workout", "commute"]] = None
    visibility: Optional[Literal["private", "clubs", "public"]] = None
    gear_id: Optional[str] = Field(default=None, max_length=80)
    notes: Optional[str] = Field(default=None, max_length=4000)


class ActivityCrop(BaseModel):
    start_index: int = Field(ge=0)
    end_index: int = Field(ge=1)


class PrivacySettingsUpdate(BaseModel):
    default_activity_visibility: Optional[Literal["private", "clubs", "public"]] = None
    hide_start_end_m: Optional[int] = Field(default=None, ge=0, le=1_609)
    allow_leaderboards: Optional[bool] = None
    allow_aggregate_heatmaps: Optional[bool] = None
    athlete_intelligence_enabled: Optional[bool] = None
    live_location_enabled: Optional[bool] = None


def parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    normalized = str(value).strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def haversine_m(start: Dict[str, Any], end: Dict[str, Any]) -> float:
    lat1 = radians(float(start["latitude"]))
    lon1 = radians(float(start["longitude"]))
    lat2 = radians(float(end["latitude"]))
    lon2 = radians(float(end["longitude"]))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6_371_000.0 * 2 * atan2(sqrt(a), sqrt(max(0.0, 1 - a)))


def _point_dict(point: Any) -> Dict[str, Any]:
    if isinstance(point, ActivityPoint):
        raw = point.model_dump()
    elif isinstance(point, dict):
        raw = dict(point)
    else:
        return {}
    timestamp = parse_datetime(raw.get("timestamp"))
    return {
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "timestamp": timestamp.isoformat() if timestamp else None,
        "altitude": _finite_float(raw.get("altitude")),
        "speed": _finite_float(raw.get("speed")),
        "accuracy": _finite_float(raw.get("accuracy")),
        "heart_rate": _bounded_int(raw.get("heart_rate"), 20, 260),
        "cadence": _finite_float(raw.get("cadence")),
    }


def _finite_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) else None


def _bounded_int(value: Any, minimum: int, maximum: int) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if minimum <= parsed <= maximum else None


def clean_activity_stream(
    points: Sequence[Any],
    *,
    max_accuracy_m: float = MAX_ACCEPTED_ACCURACY_M,
    max_speed_mps: float = MAX_RUNNING_SPEED_MPS,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Validate a raw stream while preserving enough stops for moving-time analysis.

    The original stream should still be stored by the caller. This output is the
    deterministic, reprocessable stream used by distance and competition logic.
    """
    accepted: List[Dict[str, Any]] = []
    reasons = {
        "invalid_coordinate": 0,
        "poor_accuracy": 0,
        "duplicate_or_reversed_time": 0,
        "implausible_jump": 0,
    }

    for value in points:
        point = _point_dict(value)
        latitude = _finite_float(point.get("latitude"))
        longitude = _finite_float(point.get("longitude"))
        if latitude is None or longitude is None or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            reasons["invalid_coordinate"] += 1
            continue
        point["latitude"] = latitude
        point["longitude"] = longitude

        accuracy = point.get("accuracy")
        if accuracy is not None and accuracy > max_accuracy_m:
            reasons["poor_accuracy"] += 1
            continue

        if accepted:
            previous = accepted[-1]
            previous_time = parse_datetime(previous.get("timestamp"))
            current_time = parse_datetime(point.get("timestamp"))
            if previous_time and current_time:
                delta_seconds = (current_time - previous_time).total_seconds()
                if delta_seconds <= 0:
                    reasons["duplicate_or_reversed_time"] += 1
                    continue
                distance_m = haversine_m(previous, point)
                if distance_m / delta_seconds > max_speed_mps:
                    reasons["implausible_jump"] += 1
                    continue
            elif haversine_m(previous, point) > max_speed_mps * 5:
                # With no timestamps, only accept locally adjacent samples.
                reasons["implausible_jump"] += 1
                continue
        accepted.append(point)

    return accepted, reasons


def _elapsed_seconds(
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    points: Sequence[Dict[str, Any]],
) -> int:
    start = start_time or (parse_datetime(points[0].get("timestamp")) if points else None)
    end = end_time or (parse_datetime(points[-1].get("timestamp")) if points else None)
    if start and end and end > start:
        return int(round((end - start).total_seconds()))
    return 0


def _stream_metrics(points: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    cumulative_distance_m = [0.0]
    cumulative_elapsed_sec = [0.0]
    distance_m = 0.0
    moving_time_sec = 0.0
    elevation_gain_m = 0.0
    speed_samples: List[float] = []
    heart_rates: List[int] = []
    cadence_samples: List[float] = []
    grade_adjusted_distance_m = 0.0
    graded_segments = 0

    for point in points:
        if point.get("heart_rate") is not None:
            heart_rates.append(int(point["heart_rate"]))
        if point.get("cadence") is not None and float(point["cadence"]) >= 0:
            cadence_samples.append(float(point["cadence"]))

    for index in range(1, len(points)):
        previous = points[index - 1]
        point = points[index]
        segment_m = haversine_m(previous, point)
        previous_time = parse_datetime(previous.get("timestamp"))
        current_time = parse_datetime(point.get("timestamp"))
        delta_sec = (
            max(0.0, (current_time - previous_time).total_seconds())
            if previous_time and current_time
            else 0.0
        )

        derived_speed = segment_m / delta_sec if delta_sec > 0 else 0.0
        reported_speed = _finite_float(point.get("speed"))
        speed = reported_speed if reported_speed is not None and reported_speed >= 0 else derived_speed
        if 0 <= speed <= MAX_RUNNING_SPEED_MPS:
            speed_samples.append(speed)

        counted_segment = segment_m if segment_m >= MIN_DISTANCE_INCREMENT_M else 0.0
        distance_m += counted_segment

        if (
            counted_segment > 0
            and delta_sec > 0
            and delta_sec <= MAX_SAMPLE_GAP_SECONDS
            and MIN_MOVING_SPEED_MPS <= derived_speed <= MAX_RUNNING_SPEED_MPS
        ):
            moving_time_sec += delta_sec
            previous_altitude = _finite_float(previous.get("altitude"))
            current_altitude = _finite_float(point.get("altitude"))
            if (
                counted_segment >= 5
                and previous_altitude is not None
                and current_altitude is not None
            ):
                grade = max(-0.3, min(0.3, (current_altitude - previous_altitude) / counted_segment))
                # Runlete's deterministic running-energy approximation.
                cost = (
                    155.4 * grade**5
                    - 30.4 * grade**4
                    - 43.3 * grade**3
                    + 46.3 * grade**2
                    + 19.5 * grade
                    + 3.6
                )
                grade_adjusted_distance_m += counted_segment * max(0.5, cost) / 3.6
                graded_segments += 1

        previous_altitude = _finite_float(previous.get("altitude"))
        current_altitude = _finite_float(point.get("altitude"))
        if previous_altitude is not None and current_altitude is not None:
            gain = current_altitude - previous_altitude
            if gain >= 1.5:
                elevation_gain_m += gain

        cumulative_distance_m.append(distance_m)
        cumulative_elapsed_sec.append(
            cumulative_elapsed_sec[-1] + (delta_sec if delta_sec > 0 else 0.0)
        )

    return {
        "distance_m": distance_m,
        "moving_time_sec": int(round(moving_time_sec)),
        "elevation_gain_m": round(elevation_gain_m, 1),
        "average_speed_mps": round(sum(speed_samples) / len(speed_samples), 3) if speed_samples else None,
        "max_speed_mps": round(max(speed_samples), 3) if speed_samples else None,
        "average_heart_rate": round(sum(heart_rates) / len(heart_rates)) if heart_rates else None,
        "max_heart_rate": max(heart_rates) if heart_rates else None,
        "average_cadence": round(sum(cadence_samples) / len(cadence_samples), 1) if cadence_samples else None,
        "grade_adjusted_distance_m": (
            round(grade_adjusted_distance_m, 1)
            if graded_segments
            else None
        ),
        "cumulative_distance_m": cumulative_distance_m,
        "cumulative_elapsed_sec": cumulative_elapsed_sec,
    }


def _interpolated_time_at_distance(
    distances: Sequence[float],
    times: Sequence[float],
    target_distance: float,
) -> Optional[float]:
    if not distances or target_distance < distances[0] or target_distance > distances[-1]:
        return None
    upper = bisect_left(distances, target_distance)
    if upper == 0:
        return times[0]
    if upper >= len(distances):
        return times[-1]
    lower = upper - 1
    distance_span = distances[upper] - distances[lower]
    if distance_span <= 0:
        return times[upper]
    fraction = (target_distance - distances[lower]) / distance_span
    return times[lower] + fraction * (times[upper] - times[lower])


def calculate_splits(
    distances: Sequence[float],
    times: Sequence[float],
    split_distance_m: float = 1_000.0,
) -> List[Dict[str, Any]]:
    splits: List[Dict[str, Any]] = []
    previous_time = 0.0
    split_number = 1
    target = split_distance_m
    while distances and target <= distances[-1]:
        crossing_time = _interpolated_time_at_distance(distances, times, target)
        if crossing_time is None:
            break
        duration = max(0, int(round(crossing_time - previous_time)))
        splits.append(
            {
                "split": split_number,
                "distance_m": split_distance_m,
                "elapsed_time_sec": duration,
                "pace_sec_per_km": round(duration * 1000.0 / split_distance_m),
            }
        )
        previous_time = crossing_time
        target += split_distance_m
        split_number += 1
    return splits


def calculate_best_efforts(
    distances: Sequence[float],
    times: Sequence[float],
) -> List[Dict[str, Any]]:
    efforts: List[Dict[str, Any]] = []
    if len(distances) < 2 or distances[-1] <= 0:
        return efforts

    for label, benchmark_m in BENCHMARK_DISTANCES_M:
        if distances[-1] < benchmark_m:
            continue
        best_seconds: Optional[float] = None
        start_distance = 0.0
        while start_distance + benchmark_m <= distances[-1]:
            start_time = _interpolated_time_at_distance(distances, times, start_distance)
            end_time = _interpolated_time_at_distance(distances, times, start_distance + benchmark_m)
            if start_time is not None and end_time is not None and end_time >= start_time:
                duration = end_time - start_time
                if best_seconds is None or duration < best_seconds:
                    best_seconds = duration
            next_index = bisect_left(distances, start_distance) + 1
            while next_index < len(distances) and distances[next_index] <= start_distance:
                next_index += 1
            if next_index >= len(distances):
                break
            start_distance = distances[next_index]
        if best_seconds is not None:
            efforts.append(
                {
                    "name": label,
                    "distance_m": benchmark_m,
                    "elapsed_time_sec": int(round(best_seconds)),
                    "pace_sec_per_km": round(best_seconds * 1000.0 / benchmark_m),
                }
            )
    return efforts


def _quality(
    raw_count: int,
    accepted: Sequence[Dict[str, Any]],
    dropped: Dict[str, int],
    distance_m: float,
    elapsed_time_sec: int,
) -> Dict[str, Any]:
    accepted_ratio = len(accepted) / raw_count if raw_count else 0.0
    accuracy_values = [
        float(point["accuracy"])
        for point in accepted
        if point.get("accuracy") is not None
    ]
    average_accuracy = sum(accuracy_values) / len(accuracy_values) if accuracy_values else None
    accuracy_score = (
        max(0.0, min(1.0, 1.0 - average_accuracy / MAX_ACCEPTED_ACCURACY_M))
        if average_accuracy is not None
        else 0.75
    )
    score = round(0.7 * accepted_ratio + 0.3 * accuracy_score, 3)
    average_speed = distance_m / elapsed_time_sec if elapsed_time_sec > 0 else 0.0
    flags: List[str] = []
    if raw_count < 2:
        flags.append("insufficient_samples")
    if accepted_ratio < 0.8:
        flags.append("high_sample_rejection")
    if average_speed > MAX_RUNNING_SPEED_MPS:
        flags.append("implausible_average_speed")
    if distance_m < 50:
        flags.append("too_short")
    return {
        "score": score,
        "status": "accepted" if score >= 0.6 and not flags else "review" if score >= 0.4 else "rejected",
        "leaderboard_eligible": score >= 0.6 and not flags,
        "accepted_samples": len(accepted),
        "raw_samples": raw_count,
        "average_accuracy_m": round(average_accuracy, 1) if average_accuracy is not None else None,
        "dropped_samples": dropped,
        "flags": flags,
    }


def process_activity(
    payload: ActivityCreate,
    *,
    athlete_weight_kg: Optional[float] = None,
) -> Dict[str, Any]:
    raw_points = [_point_dict(point) for point in payload.gps_path]
    cleaned, dropped = clean_activity_stream(raw_points)
    metrics = _stream_metrics(cleaned)

    elapsed_time_sec = payload.elapsed_time_sec or _elapsed_seconds(
        payload.start_time,
        payload.end_time,
        cleaned,
    )
    elapsed_time_sec = max(0, int(elapsed_time_sec))
    paused_time_sec = min(max(0, payload.paused_duration_sec), elapsed_time_sec)

    if payload.activity_type == "treadmill" or payload.source == "manual":
        distance_m = float(payload.distance_m or 0)
        moving_time_sec = int(
            payload.moving_time_sec
            if payload.moving_time_sec is not None
            else max(0, elapsed_time_sec - paused_time_sec)
        )
        elevation_gain_m = float(payload.elevation_gain_m or 0)
    else:
        distance_m = float(metrics["distance_m"])
        derived_moving = int(metrics["moving_time_sec"])
        moving_time_sec = int(
            payload.moving_time_sec
            if payload.moving_time_sec is not None
            else min(derived_moving, max(0, elapsed_time_sec - paused_time_sec))
        )
        elevation_gain_m = float(metrics["elevation_gain_m"])

    weight_kg = athlete_weight_kg if athlete_weight_kg and athlete_weight_kg > 0 else 70.0
    calories = payload.calories_kcal
    if calories is None:
        calories = round(weight_kg * (distance_m / 1000.0))

    pace_sec_per_km = (
        round(moving_time_sec / (distance_m / 1000.0))
        if distance_m > 0 and moving_time_sec > 0
        else None
    )
    grade_adjusted_distance_m = metrics.get("grade_adjusted_distance_m")
    grade_adjusted_pace_sec_per_km = (
        round(moving_time_sec / (float(grade_adjusted_distance_m) / 1000.0))
        if grade_adjusted_distance_m and moving_time_sec > 0
        else None
    )

    splits = calculate_splits(
        metrics["cumulative_distance_m"],
        metrics["cumulative_elapsed_sec"],
    )
    best_efforts = calculate_best_efforts(
        metrics["cumulative_distance_m"],
        metrics["cumulative_elapsed_sec"],
    )
    quality = _quality(len(raw_points), cleaned, dropped, distance_m, elapsed_time_sec)

    average_heart_rate = payload.average_heart_rate or metrics["average_heart_rate"]
    max_heart_rate = payload.max_heart_rate or metrics["max_heart_rate"]
    average_cadence = payload.average_cadence or metrics["average_cadence"]

    return {
        "schema_version": SCHEMA_VERSION,
        "computation_version": COMPUTATION_VERSION,
        "raw_stream": raw_points,
        "cleaned_stream": cleaned,
        "distance_m": round(distance_m, 1),
        "distance_km": round(distance_m / 1000.0, 3),
        "elapsed_time_sec": elapsed_time_sec,
        "moving_time_sec": moving_time_sec,
        "paused_time_sec": paused_time_sec,
        "average_pace_sec_per_km": pace_sec_per_km,
        "grade_adjusted_pace_sec_per_km": grade_adjusted_pace_sec_per_km,
        "elevation_source": "recorded" if grade_adjusted_distance_m else None,
        "elevation_gain_m": round(elevation_gain_m, 1),
        "calories_kcal": int(calories),
        "average_speed_mps": metrics["average_speed_mps"],
        "max_speed_mps": metrics["max_speed_mps"],
        "average_heart_rate": average_heart_rate,
        "max_heart_rate": max_heart_rate,
        "average_cadence": average_cadence,
        "splits": splits,
        "best_efforts": best_efforts,
        "quality": quality,
        "route_geojson": (
            {
                "type": "LineString",
                "coordinates": [
                    [point["longitude"], point["latitude"]]
                    for point in cleaned
                ],
            }
            if len(cleaned) >= 2
            else None
        ),
    }


def public_activity_document(document: Dict[str, Any], *, include_stream: bool = False) -> Dict[str, Any]:
    result = {key: value for key, value in document.items() if key != "_id"}
    if not include_stream:
        result.pop("raw_stream", None)
        result.pop("cleaned_stream", None)
    return result
