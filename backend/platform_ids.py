from __future__ import annotations

import secrets
import threading
import time
import uuid


_lock = threading.Lock()
_last_timestamp_ms = -1
_last_random_bits = 0


def uuid7() -> uuid.UUID:
    """Generate an RFC 9562 UUIDv7 without requiring a runtime-only package."""
    global _last_timestamp_ms, _last_random_bits
    with _lock:
        timestamp_ms = int(time.time_ns() // 1_000_000) & ((1 << 48) - 1)
        if timestamp_ms > _last_timestamp_ms:
            random_bits = secrets.randbits(74)
            _last_timestamp_ms = timestamp_ms
            _last_random_bits = random_bits
        else:
            # Monotonicity matters for database locality and cursor ordering.
            timestamp_ms = _last_timestamp_ms
            random_bits = (_last_random_bits + 1) & ((1 << 74) - 1)
            if random_bits == 0:
                timestamp_ms = (_last_timestamp_ms + 1) & ((1 << 48) - 1)
            _last_timestamp_ms = timestamp_ms
            _last_random_bits = random_bits
    value = timestamp_ms << 80
    value |= 0x7 << 76
    value |= ((random_bits >> 62) & 0xFFF) << 64
    value |= 0b10 << 62
    value |= random_bits & ((1 << 62) - 1)
    return uuid.UUID(int=value)


def new_id() -> str:
    return str(uuid7())
