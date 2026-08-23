from datetime import datetime, timedelta, timezone

from backend.app.activities.processing import Sample
from backend.app.maps.privacy import DecryptedHiddenZone, redact_start_and_end


def _samples() -> tuple[Sample, ...]:
    start = datetime(2026, 8, 7, tzinfo=timezone.utc)
    return tuple(
        Sample(17.4, 78.4 + index * 0.001, start + timedelta(seconds=index * 30), accuracy=5)
        for index in range(8)
    )


def test_hidden_zone_crops_route_start_without_exposing_private_samples():
    result = redact_start_and_end(_samples(), (DecryptedHiddenZone(17.4, 78.4, 150),))
    assert result is not None
    assert result[0].longitude >= 78.402
    assert result[-1] == _samples()[-1]


def test_mid_route_hidden_zone_fails_closed_instead_of_bridging_geometry():
    result = redact_start_and_end(_samples(), (DecryptedHiddenZone(17.4, 78.404, 60),))
    assert result is None
