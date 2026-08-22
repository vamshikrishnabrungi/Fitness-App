from __future__ import annotations

import secrets
import threading
import time
from uuid import UUID


_lock = threading.Lock()
_last_ms = -1
_sequence = 0


def uuid7() -> UUID:
    """Return an RFC 9562 compatible, time-ordered UUIDv7."""
    global _last_ms, _sequence
    with _lock:
        unix_ms = time.time_ns() // 1_000_000
        if unix_ms > _last_ms:
            _last_ms = unix_ms
            _sequence = secrets.randbits(12)
        else:
            unix_ms = _last_ms
            _sequence += 1
            if _sequence > 0xFFF:
                while unix_ms <= _last_ms:
                    unix_ms = time.time_ns() // 1_000_000
                _last_ms = unix_ms
                _sequence = secrets.randbits(12)
        random_a = _sequence
        random_b = secrets.randbits(62)
    value = (
        (unix_ms & ((1 << 48) - 1)) << 80
        | 0x7 << 76
        | random_a << 64
        | 0b10 << 62
        | random_b
    )
    return UUID(int=value)
