from datetime import timezone

import pytest

from backend.app.activities.imports import ActivityImportError, parse_activity_file, parse_gpx, parse_tcx


def test_gpx_import_normalizes_order_and_duplicate_timestamps() -> None:
    content = b"""<?xml version="1.0"?>
    <gpx xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>
      <trkpt lat="17.4002" lon="78.4802"><ele>510</ele><time>2026-08-09T05:00:02Z</time></trkpt>
      <trkpt lat="17.4000" lon="78.4800"><ele>508</ele><time>2026-08-09T05:00:00Z</time></trkpt>
      <trkpt lat="17.4001" lon="78.4801"><time>2026-08-09T05:00:00Z</time></trkpt>
    </trkseg></trk></gpx>"""
    provider, samples = parse_activity_file("morning-run.gpx", content)
    assert provider == "gpx"
    assert len(samples) == 2
    assert samples[0].timestamp.tzinfo == timezone.utc
    assert samples[0].latitude == pytest.approx(17.4)
    assert samples[1].altitude == pytest.approx(510)


def test_tcx_import_reads_position_heart_rate_and_cadence() -> None:
    content = b"""<?xml version="1.0"?>
    <TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
      <Activities><Activity Sport="Running"><Lap StartTime="2026-08-09T05:00:00Z"><Track>
        <Trackpoint><Time>2026-08-09T05:00:00Z</Time><Position><LatitudeDegrees>51.5</LatitudeDegrees><LongitudeDegrees>-0.1</LongitudeDegrees></Position><HeartRateBpm><Value>140</Value></HeartRateBpm><Cadence>82</Cadence></Trackpoint>
        <Trackpoint><Time>2026-08-09T05:00:03Z</Time><Position><LatitudeDegrees>51.5002</LatitudeDegrees><LongitudeDegrees>-0.0998</LongitudeDegrees></Position><HeartRateBpm><Value>143</Value></HeartRateBpm><Cadence>84</Cadence></Trackpoint>
      </Track></Lap></Activity></Activities>
    </TrainingCenterDatabase>"""
    samples = parse_tcx(content)
    assert len(samples) == 2
    assert samples[0].heart_rate == 140
    assert samples[1].cadence == pytest.approx(84)


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("activity.csv", b"a,b"),
        ("activity.gpx", b"not xml"),
        ("activity.tcx", b"<TrainingCenterDatabase />"),
    ],
)
def test_activity_import_rejects_unsupported_or_unusable_files(filename: str, content: bytes) -> None:
    with pytest.raises(ActivityImportError):
        parse_activity_file(filename, content)


def test_activity_import_enforces_size_limit() -> None:
    with pytest.raises(ActivityImportError, match="25 MB"):
        parse_activity_file("activity.gpx", b"x" * (25 * 1024 * 1024 + 1))


def test_gpx_ignores_invalid_coordinates_but_requires_two_valid_points() -> None:
    content = b"""<gpx><trk><trkseg>
      <trkpt lat="91" lon="1"><time>2026-08-09T05:00:00Z</time></trkpt>
      <trkpt lat="10" lon="10"><time>2026-08-09T05:00:01Z</time></trkpt>
    </trkseg></trk></gpx>"""
    with pytest.raises(ActivityImportError, match="at least two"):
        parse_gpx(content)
