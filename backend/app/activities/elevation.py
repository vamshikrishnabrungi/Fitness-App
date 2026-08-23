"""Elevation gain computation.

Source priority (most to least accurate):
  1. device barometer altitude, when the device reports it
  2. DEM (digital elevation model) lookup along the GPS track
  3. GPS altitude (last resort)

In every case the profile is smoothed and only *sustained* climbs past a
threshold are counted, so GPS/barometer wobble is not mistaken for climbing.
"""
from __future__ import annotations

from typing import Protocol, Sequence

from backend.app.core.config import get_settings

SUSTAINED_CLIMB_THRESHOLD_M = 3.0
SMOOTHING_WINDOW = 5
MIN_SOURCE_COVERAGE = 0.5
DEM_BATCH_SIZE = 100


def _forward_fill(values: Sequence[float | None]) -> list[float]:
    filled: list[float] = []
    last: float | None = None
    for value in values:
        if value is not None:
            last = float(value)
        if last is not None:
            filled.append(last)
    return filled


def smooth_series(values: Sequence[float], window: int = SMOOTHING_WINDOW) -> list[float]:
    """Centred moving-average smoother."""
    values = list(values)
    if window <= 1 or len(values) <= 2:
        return values
    half = window // 2
    smoothed: list[float] = []
    n = len(values)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        segment = values[lo:hi]
        smoothed.append(sum(segment) / len(segment))
    return smoothed


def sustained_elevation_gain(
    values: Sequence[float | None],
    threshold: float = SUSTAINED_CLIMB_THRESHOLD_M,
    window: int = SMOOTHING_WINDOW,
) -> float:
    """Total ascent, smoothed and gated so only climbs >= threshold count.

    A running reference low is tracked: only once the profile rises `threshold`
    metres above that low is the gain committed (and the reference advanced).
    Descents lower the reference, so minor oscillations never accumulate.
    """
    series = _forward_fill(values)
    if len(series) < 2:
        return 0.0
    smoothed = smooth_series(series, window)
    gain = 0.0
    reference = smoothed[0]
    for value in smoothed[1:]:
        diff = value - reference
        if diff >= threshold:
            gain += diff
            reference = value
        elif value < reference:
            reference = value
    return round(gain, 2)


class DemProvider(Protocol):
    async def lookup(self, coordinates: list[tuple[float, float]]) -> list[float | None]:
        ...


class NullDemProvider:
    """No DEM configured — forces the GPS-altitude fallback."""

    async def lookup(self, coordinates: list[tuple[float, float]]) -> list[float | None]:
        return [None] * len(coordinates)


class HttpDemProvider:
    """Open-Elevation / OpenTopoData compatible HTTP DEM.

    Expects POST {"locations": [{"latitude","longitude"}...]} ->
    {"results": [{"elevation": <m>} ...]}. Any failure degrades to None so the
    pipeline falls back to GPS altitude instead of erroring.
    """

    def __init__(self, base_url: str) -> None:
        self._url = base_url.rstrip("/")

    async def lookup(self, coordinates: list[tuple[float, float]]) -> list[float | None]:
        if not coordinates:
            return []
        results: list[float | None] = [None] * len(coordinates)
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                for start in range(0, len(coordinates), DEM_BATCH_SIZE):
                    batch = coordinates[start:start + DEM_BATCH_SIZE]
                    resp = await client.post(self._url, json={
                        "locations": [{"latitude": lat, "longitude": lon} for lat, lon in batch]})
                    resp.raise_for_status()
                    for i, item in enumerate(resp.json().get("results", [])):
                        results[start + i] = item.get("elevation")
        except Exception:
            return [None] * len(coordinates)
        return results


def get_dem_provider() -> DemProvider:
    url = get_settings().dem_provider_url
    return HttpDemProvider(url) if url else NullDemProvider()


def _has_coverage(values: Sequence[float | None]) -> bool:
    if not values:
        return False
    present = sum(1 for v in values if v is not None)
    return present >= max(2, int(len(values) * MIN_SOURCE_COVERAGE))


async def resolve_elevation(
    *,
    barometric: Sequence[float | None],
    coordinates: list[tuple[float, float]],
    gps_gain_m: float | None,
    provider: DemProvider,
) -> tuple[float, str]:
    """Return (elevation_gain_m, elevation_source) using the best source available."""
    if _has_coverage(barometric):
        return sustained_elevation_gain(barometric), "device_barometer"
    dem = await provider.lookup(coordinates)
    if _has_coverage(dem):
        return sustained_elevation_gain(dem), "dem_lookup"
    if gps_gain_m is not None:
        return round(float(gps_gain_m), 2), "gps_altitude"
    return 0.0, "unavailable"
