"""Verify the elevation upgrade: sustained-climb smoothing + source priority."""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.activities.elevation import resolve_elevation, sustained_elevation_gain  # noqa: E402
from backend.app.activities.processing import Sample, process_samples  # noqa: E402


def naive_gain(alts):
    g = 0.0
    for a, b in zip(alts, alts[1:]):
        if b - a >= 1.0:
            g += b - a
    return round(g, 2)


class FakeDem:
    def __init__(self, values):
        self._values = values

    async def lookup(self, coordinates):
        return list(self._values)


async def main():
    # 1. Flat road with +/-2m GPS noise (should NOT count as climbing)
    noisy_flat = [100 + (2 if i % 2 else -2) for i in range(40)]
    print("1. Flat + GPS noise:")
    print(f"   naive(>=1m per sample) = {naive_gain(noisy_flat)} m  (garbage)")
    print(f"   sustained              = {sustained_elevation_gain(noisy_flat)} m  (correct ~0)")

    # 2. A real 50 m hill with noise on top
    climb = [100 + i * 2.5 + (1.5 if i % 2 else -1.5) for i in range(21)]  # ~50 m gain
    print("2. Real ~50 m climb + noise:")
    print(f"   naive     = {naive_gain(climb)} m  (inflated by noise)")
    print(f"   sustained = {sustained_elevation_gain(climb)} m  (~50)")

    # 3. Source priority
    base = datetime(2026, 6, 1, 7, 0, tzinfo=timezone.utc)
    samples = [Sample(latitude=43.73 + i * 1e-4, longitude=7.42, timestamp=base + timedelta(seconds=i),
                      accuracy=5.0, altitude=100 + (3 if i % 2 else -3),  # noisy GPS altitude
                      barometric_altitude=100 + i * 2.0) for i in range(30)]  # clean baro climb ~58 m
    coords = [(s.latitude, s.longitude) for s in samples]
    baro = [s.barometric_altitude for s in samples]
    gps = [s.altitude for s in samples]

    g, src = await resolve_elevation(barometric=baro, coordinates=coords,
                                     gps_gain_m=sustained_elevation_gain(gps), provider=FakeDem([None] * 30))
    print(f"3a. Barometer present -> source={src}, gain={g} m (expect device_barometer, ~58)")

    dem = [100 + i * 2.0 for i in range(30)]
    g, src = await resolve_elevation(barometric=[None] * 30, coordinates=coords,
                                     gps_gain_m=sustained_elevation_gain(gps), provider=FakeDem(dem))
    print(f"3b. No baro, DEM available -> source={src}, gain={g} m (expect dem_lookup, ~58)")

    g, src = await resolve_elevation(barometric=[None] * 30, coordinates=coords,
                                     gps_gain_m=sustained_elevation_gain(gps), provider=FakeDem([None] * 30))
    print(f"3c. No baro, no DEM -> source={src}, gain={g} m (expect gps_altitude fallback)")

    # 4. End-to-end through process_samples (uses sustained gain on GPS altitude)
    result = process_samples(samples)
    print(f"4. process_samples elevation_gain_m = {result.elevation_gain_m} m (GPS noise rejected)")


asyncio.run(main())
