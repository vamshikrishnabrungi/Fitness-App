from __future__ import annotations


class InvalidPolyline(ValueError):
    pass


def decode_polyline6(value: str) -> list[dict[str, float]]:
    """Decode Valhalla's six-decimal encoded route shape.

    The decoder is intentionally local so route coordinates are validated by the
    backend and every mobile client receives the same canonical representation.
    """

    if not value:
        return []
    index = latitude = longitude = 0
    coordinates: list[dict[str, float]] = []

    def component(previous: int) -> int:
        nonlocal index
        shift = result = 0
        while True:
            if index >= len(value):
                raise InvalidPolyline("truncated encoded polyline")
            byte = ord(value[index]) - 63
            index += 1
            if byte < 0 or byte > 63:
                raise InvalidPolyline("invalid encoded polyline character")
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
            if shift > 35:
                raise InvalidPolyline("encoded polyline component is too large")
        delta = ~(result >> 1) if result & 1 else result >> 1
        return previous + delta

    while index < len(value):
        latitude = component(latitude)
        longitude = component(longitude)
        coordinates.append({"latitude": latitude / 1_000_000, "longitude": longitude / 1_000_000})
    return coordinates
