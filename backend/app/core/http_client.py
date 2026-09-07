from __future__ import annotations

import httpx


_client: httpx.AsyncClient | None = None


def http_client() -> httpx.AsyncClient:
    """Process-wide outbound client with connection reuse and bounded resources."""

    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20, keepalive_expiry=30.0),
            follow_redirects=False,
        )
    return _client


async def close_http_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
