from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from defusedxml import ElementTree

from .processing import Sample

MAX_ACTIVITY_FILE_BYTES = 25 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".gpx", ".tcx", ".fit"}


class ActivityImportError(ValueError):
    pass


def _float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif value:
        try:
            parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _sample(latitude: Any, longitude: Any, timestamp: Any, **values: Any) -> Sample | None:
    lat, lon, occurred = _float(latitude), _float(longitude), _timestamp(timestamp)
    if lat is None or lon is None or occurred is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return Sample(
        latitude=lat,
        longitude=lon,
        timestamp=occurred,
        altitude=_float(values.get("altitude")),
        barometric_altitude=_float(values.get("barometric_altitude")),
        speed=_float(values.get("speed")),
        heart_rate=int(float(values["heart_rate"])) if _float(values.get("heart_rate")) is not None else None,
        cadence=_float(values.get("cadence")),
    )


def _validated(samples: list[Sample]) -> tuple[Sample, ...]:
    ordered = sorted(samples, key=lambda row: row.timestamp)
    deduplicated: list[Sample] = []
    for sample in ordered:
        if deduplicated and sample.timestamp == deduplicated[-1].timestamp:
            continue
        deduplicated.append(sample)
    if len(deduplicated) < 2:
        raise ActivityImportError("The activity file needs at least two timestamped GPS points")
    if len(deduplicated) > 200_000:
        raise ActivityImportError("The activity file contains more than 200,000 samples")
    return tuple(deduplicated)


def parse_gpx(content: bytes) -> tuple[Sample, ...]:
    try:
        root = ElementTree.fromstring(content)
    except Exception as exc:
        raise ActivityImportError("Invalid GPX XML") from exc
    samples: list[Sample] = []
    for point in root.findall(".//{*}trkpt"):
        extensions = {child.tag.rsplit("}", 1)[-1].lower(): child.text for child in point.findall(".//{*}extensions//*")}
        sample = _sample(
            point.attrib.get("lat"),
            point.attrib.get("lon"),
            point.findtext("{*}time"),
            altitude=point.findtext("{*}ele"),
            heart_rate=extensions.get("hr") or extensions.get("heartrate"),
            cadence=extensions.get("cad") or extensions.get("cadence"),
        )
        if sample:
            samples.append(sample)
    return _validated(samples)


def parse_tcx(content: bytes) -> tuple[Sample, ...]:
    try:
        root = ElementTree.fromstring(content)
    except Exception as exc:
        raise ActivityImportError("Invalid TCX XML") from exc
    samples: list[Sample] = []
    for point in root.findall(".//{*}Trackpoint"):
        position = point.find("{*}Position")
        if position is None:
            continue
        speed = None
        for child in point.findall(".//{*}Extensions//*"):
            if child.tag.rsplit("}", 1)[-1].lower() == "speed":
                speed = child.text
                break
        sample = _sample(
            position.findtext("{*}LatitudeDegrees"),
            position.findtext("{*}LongitudeDegrees"),
            point.findtext("{*}Time"),
            altitude=point.findtext("{*}AltitudeMeters"),
            speed=speed,
            heart_rate=point.findtext("{*}HeartRateBpm/{*}Value"),
            cadence=point.findtext("{*}Cadence"),
        )
        if sample:
            samples.append(sample)
    return _validated(samples)


def _fit_value(frame: Any, field: str) -> Any:
    try:
        return frame.get_value(field)
    except (KeyError, TypeError):
        return None


def _degrees(value: Any) -> float | None:
    parsed = _float(value)
    return parsed * (180.0 / 2**31) if parsed is not None else None


def parse_fit(content: bytes) -> tuple[Sample, ...]:
    import fitdecode

    samples: list[Sample] = []
    try:
        with fitdecode.FitReader(BytesIO(content)) as reader:
            for frame in reader:
                if not isinstance(frame, fitdecode.FitDataMessage) or frame.name != "record":
                    continue
                sample = _sample(
                    _degrees(_fit_value(frame, "position_lat")),
                    _degrees(_fit_value(frame, "position_long")),
                    _fit_value(frame, "timestamp"),
                    altitude=_fit_value(frame, "enhanced_altitude") or _fit_value(frame, "altitude"),
                    speed=_fit_value(frame, "enhanced_speed") or _fit_value(frame, "speed"),
                    heart_rate=_fit_value(frame, "heart_rate"),
                    cadence=_fit_value(frame, "cadence"),
                )
                if sample:
                    samples.append(sample)
    except Exception as exc:
        raise ActivityImportError("Invalid or unsupported FIT file") from exc
    return _validated(samples)


def parse_activity_file(filename: str, content: bytes) -> tuple[str, tuple[Sample, ...]]:
    if not content or len(content) > MAX_ACTIVITY_FILE_BYTES:
        raise ActivityImportError("Activity files must be between 1 byte and 25 MB")
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ActivityImportError("Supported activity files are GPX, TCX and FIT")
    parser = {".gpx": parse_gpx, ".tcx": parse_tcx, ".fit": parse_fit}[extension]
    return extension[1:], parser(content)
