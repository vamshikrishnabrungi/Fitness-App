from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from .elevation import sustained_elevation_gain


@dataclass(frozen=True)
class Sample:
    latitude: float
    longitude: float
    timestamp: datetime
    accuracy: float | None = None
    altitude: float | None = None
    speed: float | None = None
    heart_rate: int | None = None
    cadence: float | None = None
    # Device barometer altitude, when the phone/watch exposes it. Preferred
    # over GPS altitude and DEM for elevation gain.
    barometric_altitude: float | None = None
    # Device-provided smoothed coordinates are retained separately from the
    # raw fix. They are the authoritative live-stat source when present.
    smoothed_latitude: float | None = None
    smoothed_longitude: float | None = None


@dataclass(frozen=True)
class ProcessedActivity:
    samples: tuple[Sample, ...]
    elapsed_seconds: int
    moving_seconds: int
    paused_seconds: int
    distance_m: float
    elevation_gain_m: float
    average_pace_s_per_km: float | None
    average_hr: int | None
    average_cadence: float | None
    gps_score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DerivedSplit:
    sequence: int
    distance_m: float
    elapsed_seconds: float


@dataclass(frozen=True)
class DerivedBestEffort:
    distance_code: str
    distance_m: float
    elapsed_seconds: float
    start_offset_seconds: float


def haversine_m(a: Sample, b: Sample) -> float:
    radius = 6_371_008.8
    lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
    dlat, dlon = lat2 - lat1, math.radians(b.longitude - a.longitude)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def smooth_samples(rows: list[Sample]) -> tuple[list[Sample], list[str]]:
    """Apply the shared light-weight position smoother used for confirmation.

    This is deliberately conservative: raw fixes remain evidence, while the
    returned samples carry the smoothed coordinates used for distance/pace.
    Accuracy controls the blend, so a good fix is changed very little and a
    noisy fix cannot create a large jump.
    """
    if not rows:
        return [], []
    output: list[Sample] = []
    reasons: list[str] = []
    lat = rows[0].latitude
    lon = rows[0].longitude
    for row in rows:
        if output:
            accuracy = max(1.0, min(100.0, row.accuracy or 50.0))
            # 0.85 for a high-quality fix, tapering to 0.35 for noisy fixes.
            alpha = max(0.35, min(0.85, 1.0 - accuracy / 140.0))
            lat = lat + alpha * (row.latitude - lat)
            lon = lon + alpha * (row.longitude - lon)
        output.append(Sample(
            latitude=row.latitude,
            longitude=row.longitude,
            timestamp=row.timestamp,
            accuracy=row.accuracy,
            altitude=row.altitude,
            speed=row.speed,
            heart_rate=row.heart_rate,
            cadence=row.cadence,
            barometric_altitude=row.barometric_altitude,
            smoothed_latitude=lat,
            smoothed_longitude=lon,
        ))
    reasons.append("on_device_smoothing_confirmed")
    return output, reasons


def metric_sample(sample: Sample) -> Sample:
    """Return the coordinate view used for authoritative metric calculations."""
    if sample.smoothed_latitude is None or sample.smoothed_longitude is None:
        return sample
    return Sample(
        latitude=sample.smoothed_latitude,
        longitude=sample.smoothed_longitude,
        timestamp=sample.timestamp,
        accuracy=sample.accuracy,
        altitude=sample.altitude,
        speed=sample.speed,
        heart_rate=sample.heart_rate,
        cadence=sample.cadence,
        barometric_altitude=sample.barometric_altitude,
        smoothed_latitude=sample.smoothed_latitude,
        smoothed_longitude=sample.smoothed_longitude,
    )


def clean_samples(rows: list[Sample]) -> tuple[list[Sample], list[str]]:
    rows = sorted(rows, key=lambda row: row.timestamp)
    output: list[Sample] = []
    reasons: list[str] = []
    seen = set()
    for row in rows:
        key = row.timestamp
        if key in seen:
            reasons.append("duplicate_timestamp_removed"); continue
        seen.add(key)
        if not (-90 <= row.latitude <= 90 and -180 <= row.longitude <= 180):
            reasons.append("invalid_coordinate_removed"); continue
        if row.accuracy is not None and row.accuracy > 100:
            reasons.append("poor_accuracy_removed"); continue
        if output:
            dt = (row.timestamp - output[-1].timestamp).total_seconds()
            if dt <= 0: continue
            implied_speed = haversine_m(output[-1], row) / dt
            if implied_speed > 15:
                reasons.append("impossible_jump_removed"); continue
        output.append(row)
    return output, reasons


def process_samples(rows: list[Sample]) -> ProcessedActivity:
    cleaned, reasons = clean_samples(rows)
    samples, smoothing_reasons = smooth_samples(cleaned)
    reasons.extend(smoothing_reasons)
    if len(samples) < 2: raise ValueError("activity requires at least two usable GPS samples")
    elapsed = max(0, int((samples[-1].timestamp - samples[0].timestamp).total_seconds()))
    distance = 0.0; moving = 0.0
    metric_samples = [metric_sample(sample) for sample in samples]
    for previous, current in zip(metric_samples, metric_samples[1:]):
        dt = (current.timestamp - previous.timestamp).total_seconds(); segment = haversine_m(previous, current); speed = segment / dt if dt else 0
        distance += segment
        if speed >= .5 and dt <= 120: moving += dt
    elevation_gain = sustained_elevation_gain([sample.altitude for sample in samples])
    accuracy_values = [row.accuracy for row in samples if row.accuracy is not None]
    accuracy_component = max(0.0, 1 - ((sum(accuracy_values) / len(accuracy_values)) / 100)) if accuracy_values else .5
    retention_component = len(samples) / max(1, len(rows))
    gps_score = min(1.0, max(0.0, .65 * accuracy_component + .35 * retention_component))
    hrs = [row.heart_rate for row in samples if row.heart_rate and 30 <= row.heart_rate <= 240]
    cadence = [row.cadence for row in samples if row.cadence and 0 < row.cadence <= 300]
    moving_int = min(elapsed, int(round(moving)))
    return ProcessedActivity(tuple(samples), elapsed, moving_int, elapsed - moving_int, distance, elevation_gain, moving / (distance / 1000) if distance > 0 and moving > 0 else None, round(sum(hrs) / len(hrs)) if hrs else None, sum(cadence) / len(cadence) if cadence else None, gps_score, tuple(sorted(set(reasons))))


def calories_for_run(distance_m: float, weight_kg: float | None) -> float | None:
    if not weight_kg or weight_kg <= 0: return None
    return distance_m / 1000 * weight_kg


def _distance_time_curve(samples: tuple[Sample, ...]) -> list[tuple[float, float]]:
    origin = samples[0].timestamp
    curve = [(0.0, 0.0)]
    distance = 0.0
    for previous, current in zip(samples, samples[1:]):
        distance += haversine_m(metric_sample(previous), metric_sample(current))
        curve.append((distance, (current.timestamp - origin).total_seconds()))
    return curve


def _time_at_distance(curve: list[tuple[float, float]], target_m: float) -> float:
    if target_m <= 0:
        return curve[0][1]
    for (distance_a, time_a), (distance_b, time_b) in zip(curve, curve[1:]):
        if target_m <= distance_b:
            span = distance_b - distance_a
            ratio = 0.0 if span <= 0 else (target_m - distance_a) / span
            return time_a + ratio * (time_b - time_a)
    return curve[-1][1]


def kilometre_splits(samples: tuple[Sample, ...]) -> list[DerivedSplit]:
    curve = _distance_time_curve(samples)
    total = curve[-1][0]
    splits: list[DerivedSplit] = []
    start_distance = start_time = 0.0
    sequence = 1
    while start_distance < total - 0.5:
        end_distance = min(total, start_distance + 1000.0)
        end_time = _time_at_distance(curve, end_distance)
        splits.append(DerivedSplit(sequence, end_distance - start_distance, end_time - start_time))
        sequence += 1
        start_distance, start_time = end_distance, end_time
    return splits


BEST_EFFORT_DISTANCES: tuple[tuple[str, float], ...] = (
    ("400m", 400.0),
    ("1k", 1000.0),
    ("1mile", 1609.344),
    ("5k", 5000.0),
    ("10k", 10_000.0),
    ("half_marathon", 21_097.5),
    ("marathon", 42_195.0),
)


def best_efforts(samples: tuple[Sample, ...]) -> list[DerivedBestEffort]:
    """Return elapsed-time sliding-window best efforts with interpolated boundaries."""

    curve = _distance_time_curve(samples)
    total = curve[-1][0]
    efforts: list[DerivedBestEffort] = []
    for code, target in BEST_EFFORT_DISTANCES:
        if total + 0.5 < target:
            continue
        best: tuple[float, float] | None = None
        starts = {0.0, *(distance for distance, _ in curve if distance <= total - target)}
        for start_distance in starts:
            start_time = _time_at_distance(curve, start_distance)
            end_time = _time_at_distance(curve, start_distance + target)
            elapsed = end_time - start_time
            if elapsed > 0 and (best is None or elapsed < best[0]):
                best = (elapsed, start_time)
        if best:
            efforts.append(DerivedBestEffort(code, target, best[0], best[1]))
    return efforts
