from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.processing import Sample, haversine_m
from backend.app.core.encryption import Envelope, decrypt_json
from backend.app.maps.models import HiddenMapZone


@dataclass(frozen=True)
class DecryptedHiddenZone:
    latitude: float
    longitude: float
    radius_m: int


async def hidden_zones_for_athlete(session: AsyncSession, athlete_id: UUID) -> tuple[DecryptedHiddenZone, ...]:
    rows = (
        await session.scalars(select(HiddenMapZone).where(HiddenMapZone.athlete_id == athlete_id))
    ).all()
    zones: list[DecryptedHiddenZone] = []
    for row in rows:
        value = await decrypt_json(
            Envelope(row.geometry_encrypted, row.wrapped_dek, row.kms_key_version),
            aad=f"hidden-zone:{row.id}".encode(),
        )
        zones.append(
            DecryptedHiddenZone(
                latitude=float(value["latitude"]),
                longitude=float(value["longitude"]),
                radius_m=row.radius_m,
            )
        )
    return tuple(zones)


def redact_start_and_end(
    samples: tuple[Sample, ...], zones: tuple[DecryptedHiddenZone, ...]
) -> tuple[Sample, ...] | None:
    """Remove hidden start/end samples; fail closed for a hidden mid-route section."""

    if not zones:
        return samples

    def hidden(sample: Sample) -> bool:
        return any(
            haversine_m(
                sample,
                Sample(latitude=zone.latitude, longitude=zone.longitude, timestamp=sample.timestamp),
            )
            <= zone.radius_m
            for zone in zones
        )

    start = 0
    while start < len(samples) and hidden(samples[start]):
        start += 1
    end = len(samples)
    while end > start and hidden(samples[end - 1]):
        end -= 1
    remaining = samples[start:end]
    if len(remaining) < 2 or any(hidden(sample) for sample in remaining):
        return None
    return remaining
