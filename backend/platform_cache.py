from __future__ import annotations

import os
from typing import Optional

import redis.asyncio as redis


_client: Optional[redis.Redis] = None


def get_cache() -> Optional[redis.Redis]:
    """Return the shared Redis client, or None when caching is not configured."""
    global _client
    url = (os.environ.get("REDIS_URL") or "").strip()
    if not url:
        return None
    if _client is None:
        _client = redis.from_url(
            url,
            encoding=None,
            socket_connect_timeout=1,
            socket_timeout=2,
            health_check_interval=30,
        )
    return _client


async def cache_get_bytes(key: str) -> Optional[bytes]:
    client = get_cache()
    if client is None:
        return None
    try:
        value = await client.get(key)
        return bytes(value) if value is not None else None
    except redis.RedisError:
        # Territory reads stay available if the cache has an incident.
        return None


async def cache_set_bytes(key: str, value: bytes, ttl_seconds: int = 60) -> None:
    client = get_cache()
    if client is None:
        return
    try:
        await client.set(key, value, ex=max(1, ttl_seconds))
    except redis.RedisError:
        return
