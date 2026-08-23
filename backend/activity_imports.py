from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from backend.activity_domain import ActivityCreate


MAX_ACTIVITY_FILE_BYTES = 25 * 1024 * 1024
SUPPORTED_ACTIVITY_EXTENSIONS = {".gpx", ".tcx", ".fit"}


class ActivityImportError(ValueError):
    pass


def _text(element: Optional[ElementTree.Element]) -> Optional[str]:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def _float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _activity_from_points(points: List[Dict[str, Any]], source: str) -> ActivityCreate:
    if not points:
        raise ActivityImportError("The activity file does not contain track points")
    timestamps = [point.get("timestamp") for point in points if point.get("timestamp")]
    return ActivityCreate(
        gps_path=points,
        start_time=min(timestamps) if timestamps else None,
        end_time=max(timestamps) if timestamps else None,
        source=source,
        activity_type="run",
    )


def parse_gpx(content: bytes) -> ActivityCreate:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ActivityImportError("Invalid GPX XML") from exc

    points: List[Dict[str, Any]] = []
    for trackpoint in root.findall(".//{*}trkpt"):
        latitude = _float(trackpoint.attrib.get("lat"))
        longitude = _float(trackpoint.attrib.get("lon"))
        if latitude is None or longitude is None:
            continue
        heart_rate = None
        cadence = None
        for extension in trackpoint.findall(".//{*}extensions//*"):
            tag = extension.tag.rsplit("}", 1)[-1].lower()
            if tag in {"hr", "heartrate", "heart_rate"}:
                heart_rate = _int(_text(extension))
            elif tag in {"cad", "cadence"}:
                cadence = _float(_text(extension))
        points.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": _text(trackpoint.find("{*}time")),
                "altitude": _float(_text(trackpoint.find("{*}ele"))),
                "heart_rate": heart_rate,
                "cadence": cadence,
            }
        )
    return _activity_from_points(points, "gpx")


def parse_tcx(content: bytes) -> ActivityCreate:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ActivityImportError("Invalid TCX XML") from exc

    points: List[Dict[str, Any]] = []
    for trackpoint in root.findall(".//{*}Trackpoint"):
        position = trackpoint.find("{*}Position")
        if position is None:
            continue
        latitude = _float(_text(position.find("{*}LatitudeDegrees")))
        longitude = _float(_text(position.find("{*}LongitudeDegrees")))
        if latitude is None or longitude is None:
            continue
        heart_rate_element = trackpoint.find("{*}HeartRateBpm/{*}Value")
        cadence_element = trackpoint.find("{*}Cadence")
        speed = None
        for extension in trackpoint.findall(".//{*}Extensions//*"):
            tag = extension.tag.rsplit("}", 1)[-1].lower()
            if tag == "speed":
                speed = _float(_text(extension))
        points.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": _text(trackpoint.find("{*}Time")),
                "altitude": _float(_text(trackpoint.find("{*}AltitudeMeters"))),
                "speed": speed,
                "heart_rate": _int(_text(heart_rate_element)),
                "cadence": _float(_text(cadence_element)),
            }
        )
    return _activity_from_points(points, "tcx")


def _fit_value(frame: Any, field: str) -> Any:
    try:
        return frame.get_value(field)
    except (KeyError, TypeError):
        return None


def _semicircles_to_degrees(value: Any) -> Optional[float]:
    parsed = _float(value)
    if parsed is None:
        return None
    return parsed * (180.0 / 2**31)


def parse_fit(content: bytes) -> ActivityCreate:
    try:
        import fitdecode
    except ImportError as exc:
        raise ActivityImportError("FIT support is not installed on this server") from exc

    points: List[Dict[str, Any]] = []
    try:
        with fitdecode.FitReader(BytesIO(content)) as reader:
            for frame in reader:
                if not isinstance(frame, fitdecode.FitDataMessage) or frame.name != "record":
                    continue
                latitude = _semicircles_to_degrees(_fit_value(frame, "position_lat"))
                longitude = _semicircles_to_degrees(_fit_value(frame, "position_long"))
                if latitude is None or longitude is None:
                    continue
                timestamp = _fit_value(frame, "timestamp")
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.isoformat()
                points.append(
                    {
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": timestamp,
                        "altitude": _float(_fit_value(frame, "enhanced_altitude"))
                        or _float(_fit_value(frame, "altitude")),
                        "speed": _float(_fit_value(frame, "enhanced_speed"))
                        or _float(_fit_value(frame, "speed")),
                        "heart_rate": _int(_fit_value(frame, "heart_rate")),
                        "cadence": _float(_fit_value(frame, "cadence")),
                    }
                )
    except Exception as exc:
        raise ActivityImportError("Invalid or unsupported FIT file") from exc
    return _activity_from_points(points, "fit")


def parse_activity_file(filename: str, content: bytes) -> ActivityCreate:
    if len(content) > MAX_ACTIVITY_FILE_BYTES:
        raise ActivityImportError("Activity files must be 25 MB or smaller")
    extension = Path(filename or "").suffix.lower()
    if extension not in SUPPORTED_ACTIVITY_EXTENSIONS:
        raise ActivityImportError("Supported activity files are GPX, TCX, and FIT")
    if extension == ".gpx":
        return parse_gpx(content)
    if extension == ".tcx":
        return parse_tcx(content)
    return parse_fit(content)
