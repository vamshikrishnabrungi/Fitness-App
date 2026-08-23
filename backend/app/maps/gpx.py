from __future__ import annotations

from html import escape

from defusedxml import ElementTree

from .schemas import Coordinate

MAX_GPX_BYTES = 5 * 1024 * 1024
MAX_GPX_POINTS = 20_000


class InvalidGPX(ValueError):
    pass


def parse_gpx(content: bytes) -> tuple[str | None, list[Coordinate]]:
    if not content or len(content) > MAX_GPX_BYTES:
        raise InvalidGPX("GPX file must be between 1 byte and 5 MB")
    try:
        root = ElementTree.fromstring(content)
    except Exception as exc:
        raise InvalidGPX("GPX XML is invalid") from exc
    name: str | None = None
    points: list[Coordinate] = []
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name == "name" and name is None and element.text:
            name = element.text.strip()[:160]
        if local_name not in {"trkpt", "rtept"}:
            continue
        try:
            latitude = float(element.attrib["lat"])
            longitude = float(element.attrib["lon"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidGPX("GPX point has invalid coordinates") from exc
        elevation = None
        for child in element:
            if child.tag.rsplit("}", 1)[-1] == "ele" and child.text:
                try:
                    elevation = float(child.text)
                except ValueError:
                    elevation = None
                break
        try:
            points.append(Coordinate(latitude=latitude, longitude=longitude, elevation_m=elevation))
        except ValueError as exc:
            raise InvalidGPX("GPX point is outside valid geographic bounds") from exc
        if len(points) > MAX_GPX_POINTS:
            raise InvalidGPX("GPX contains more than 20,000 points")
    if len(points) < 2:
        raise InvalidGPX("GPX must contain at least two track or route points")
    return name, points


def render_gpx(name: str, points: list[Coordinate]) -> bytes:
    track_points = []
    for point in points:
        elevation = f"<ele>{point.elevation_m:.2f}</ele>" if point.elevation_m is not None else ""
        track_points.append(
            f'<trkpt lat="{point.latitude:.7f}" lon="{point.longitude:.7f}">{elevation}</trkpt>'
        )
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<gpx version="1.1" creator="Runlete" xmlns="http://www.topografix.com/GPX/1/1">'
        f"<trk><name>{escape(name)}</name><trkseg>{''.join(track_points)}</trkseg></trk></gpx>"
    )
    return document.encode()
