import pytest
from pydantic import ValidationError
from datetime import datetime, timedelta, timezone

from backend.app.activities.processing import Sample
from backend.app.core.pagination import decode_numeric_cursor, encode_numeric_cursor
from backend.app.maps.gpx import InvalidGPX, parse_gpx, render_gpx
from backend.app.maps.schemas import Coordinate, RouteCreate, SegmentCreate
from backend.app.maps.segment_matching import find_segment_attempts
from backend.app.core.ids import uuid7


def test_gpx_round_trip_preserves_route_points_and_escapes_name() -> None:
    points = [
        Coordinate(latitude=17.385, longitude=78.4867, elevation_m=510),
        Coordinate(latitude=17.386, longitude=78.49, elevation_m=515),
    ]
    document = render_gpx("Run & repeat", points)
    assert b"Run &amp; repeat" in document
    name, parsed = parse_gpx(document)
    assert name == "Run & repeat"
    assert [(row.latitude, row.longitude) for row in parsed] == [
        (17.385, 78.4867),
        (17.386, 78.49),
    ]


def test_gpx_rejects_invalid_or_empty_xml() -> None:
    with pytest.raises(InvalidGPX):
        parse_gpx(b"")
    with pytest.raises(InvalidGPX):
        parse_gpx(b"<gpx><trk></gpx>")
    with pytest.raises(InvalidGPX):
        parse_gpx(b"<gpx><trk><trkseg><trkpt lat='200' lon='1'/></trkseg></trk></gpx>")


def test_route_and_segment_contracts_bound_geometry() -> None:
    route = RouteCreate(
        name="Morning loop",
        path=[
            {"latitude": 17.38, "longitude": 78.48},
            {"latitude": 17.39, "longitude": 78.49},
        ],
    )
    assert route.visibility == "private"
    with pytest.raises(ValidationError):
        RouteCreate(name="X", path=[{"latitude": 17.38, "longitude": 78.48}])
    with pytest.raises(ValidationError):
        SegmentCreate(
            name="Closed endpoint",
            path=[
                {"latitude": 17.38, "longitude": 78.48},
                {"latitude": 17.38, "longitude": 78.48},
            ],
        )


def test_segment_matching_requires_ordered_endpoint_passage() -> None:
    started = datetime(2026, 8, 8, tzinfo=timezone.utc)
    samples = tuple(
        Sample(latitude=17.38 + index * 0.001, longitude=78.48, timestamp=started + timedelta(seconds=index * 30))
        for index in range(4)
    )
    attempts = find_segment_attempts(
        samples,
        start_latitude=17.38,
        start_longitude=78.48,
        end_latitude=17.383,
        end_longitude=78.48,
    )
    assert len(attempts) == 1
    assert attempts[0].elapsed_seconds == 90
    reverse = find_segment_attempts(
        samples,
        start_latitude=17.383,
        start_longitude=78.48,
        end_latitude=17.38,
        end_longitude=78.48,
    )
    assert reverse == ()


def test_numeric_cursor_round_trip() -> None:
    entity_id = uuid7()
    assert decode_numeric_cursor(encode_numeric_cursor(123.456, entity_id)) == (123.456, entity_id)
