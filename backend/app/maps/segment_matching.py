from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.models import Activity, ActivityQuality
from backend.app.activities.processing import Sample, haversine_m

from .models import Segment, SegmentEffort

ENDPOINT_TOLERANCE_M = 30.0
MINIMUM_COVERAGE = 0.90
MAX_ATTEMPTS_PER_SEGMENT = 10


@dataclass(frozen=True)
class SegmentAttempt:
    start_index: int
    end_index: int
    elapsed_seconds: float


def find_segment_attempts(
    samples: tuple[Sample, ...],
    *,
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
) -> tuple[SegmentAttempt, ...]:
    attempts: list[SegmentAttempt] = []
    start_indices = [
        index
        for index, sample in enumerate(samples[:-1])
        if haversine_m(
            sample,
            Sample(start_latitude, start_longitude, sample.timestamp),
        ) <= ENDPOINT_TOLERANCE_M
    ]
    for start_index in start_indices:
        for end_index in range(start_index + 1, len(samples)):
            sample = samples[end_index]
            endpoint = Sample(end_latitude, end_longitude, sample.timestamp)
            if haversine_m(sample, endpoint) > ENDPOINT_TOLERANCE_M:
                continue
            elapsed = (sample.timestamp - samples[start_index].timestamp).total_seconds()
            if elapsed > 0:
                attempts.append(SegmentAttempt(start_index, end_index, elapsed))
            break
        if len(attempts) >= MAX_ATTEMPTS_PER_SEGMENT:
            break
    return tuple(attempts)


async def replace_segment_efforts(
    session: AsyncSession,
    activity: Activity,
    samples: tuple[Sample, ...],
    quality: ActivityQuality,
) -> int:
    await session.execute(delete(SegmentEffort).where(SegmentEffort.activity_id == activity.id))
    if len(samples) < 2 or activity.route_geometry is None:
        return 0
    rows = (
        await session.execute(
            select(
                Segment,
                func.ST_AsGeoJSON(Segment.geometry),
                func.least(
                    1.0,
                    func.ST_Length(
                        func.ST_Intersection(
                            func.ST_Transform(Segment.geometry, 3857),
                            func.ST_Buffer(func.ST_Transform(activity.route_geometry, 3857), 25.0),
                        )
                    )
                    / func.nullif(Segment.distance_m, 0),
                ).label("coverage"),
            )
            .where(
                Segment.status == "active",
                ((Segment.visibility == "public") | (Segment.creator_athlete_id == activity.athlete_id)),
                func.ST_DWithin(
                    func.ST_Transform(Segment.geometry, 3857),
                    func.ST_Transform(activity.route_geometry, 3857),
                    30.0,
                ),
            )
            .limit(500)
        )
    ).all()
    created = 0
    for segment, geojson, raw_coverage in rows:
        coordinates = json.loads(geojson)["coordinates"]
        if len(coordinates) < 2:
            continue
        coverage = max(0.0, min(1.0, float(raw_coverage or 0)))
        attempts = find_segment_attempts(
            samples,
            start_latitude=float(coordinates[0][1]),
            start_longitude=float(coordinates[0][0]),
            end_latitude=float(coordinates[-1][1]),
            end_longitude=float(coordinates[-1][0]),
        )
        for attempt_number, attempt in enumerate(attempts, start=1):
            session.add(
                SegmentEffort(
                    activity_id=activity.id,
                    segment_id=segment.id,
                    athlete_id=activity.athlete_id,
                    attempt_number=attempt_number,
                    elapsed_seconds=attempt.elapsed_seconds,
                    coverage=coverage,
                    quality_passed=bool(
                        quality.competition_eligible and coverage >= MINIMUM_COVERAGE
                    ),
                    achieved_at=samples[attempt.end_index].timestamp,
                )
            )
            created += 1
    return created
