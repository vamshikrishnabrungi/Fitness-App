import pytest

from backend.app.maps.polyline import InvalidPolyline, decode_polyline6


def test_decodes_official_valhalla_polyline6_example() -> None:
    assert decode_polyline6("e~epoA|jfpOiDaK") == [
        {"latitude": 42.225139, "longitude": -8.670911},
        {"latitude": 42.225224, "longitude": -8.670718},
    ]


def test_rejects_truncated_polyline() -> None:
    with pytest.raises(InvalidPolyline):
        decode_polyline6("e~epoA|")
