from __future__ import annotations

import pytest

from backend.activity_imports import ActivityImportError, parse_activity_file, parse_gpx, parse_tcx


GPX = b"""<?xml version="1.0"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
  <trk><name>Morning Run</name><trkseg>
    <trkpt lat="17.4200" lon="78.4700">
      <ele>500</ele><time>2026-07-27T06:00:00Z</time>
      <extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>145</gpxtpx:hr><gpxtpx:cad>82</gpxtpx:cad></gpxtpx:TrackPointExtension></extensions>
    </trkpt>
    <trkpt lat="17.4210" lon="78.4700">
      <ele>503</ele><time>2026-07-27T06:01:00Z</time>
    </trkpt>
  </trkseg></trk>
</gpx>
"""


TCX = b"""<?xml version="1.0"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities><Activity Sport="Running"><Lap StartTime="2026-07-27T06:00:00Z"><Track>
    <Trackpoint>
      <Time>2026-07-27T06:00:00Z</Time>
      <Position><LatitudeDegrees>17.4200</LatitudeDegrees><LongitudeDegrees>78.4700</LongitudeDegrees></Position>
      <AltitudeMeters>500</AltitudeMeters><HeartRateBpm><Value>140</Value></HeartRateBpm><Cadence>80</Cadence>
    </Trackpoint>
    <Trackpoint>
      <Time>2026-07-27T06:01:00Z</Time>
      <Position><LatitudeDegrees>17.4210</LatitudeDegrees><LongitudeDegrees>78.4700</LongitudeDegrees></Position>
      <AltitudeMeters>502</AltitudeMeters>
    </Trackpoint>
  </Track></Lap></Activity></Activities>
</TrainingCenterDatabase>
"""


def test_parse_gpx_normalizes_sensor_points():
    activity = parse_gpx(GPX)
    assert activity.source == "gpx"
    assert len(activity.gps_path) == 2
    assert activity.gps_path[0].heart_rate == 145
    assert activity.gps_path[0].cadence == 82
    assert activity.start_time is not None
    assert activity.end_time is not None


def test_parse_tcx_normalizes_sensor_points():
    activity = parse_tcx(TCX)
    assert activity.source == "tcx"
    assert len(activity.gps_path) == 2
    assert activity.gps_path[0].heart_rate == 140
    assert activity.gps_path[0].cadence == 80


def test_dispatch_rejects_unknown_activity_file():
    with pytest.raises(ActivityImportError, match="GPX, TCX, and FIT"):
        parse_activity_file("run.csv", b"lat,lon")
