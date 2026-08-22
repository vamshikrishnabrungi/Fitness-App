from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings


class UnsupportedMapRegion(RuntimeError):
    pass


async def valhalla_url_for_point(session: AsyncSession, latitude: float, longitude: float) -> str:
    """Resolve a point through the versioned OSM-region boundary stored in PostGIS."""

    settings = get_settings()
    if settings.valhalla_urls:
        code = await session.scalar(
            text(
                """
                SELECT code
                FROM activity.osm_regions
                WHERE status = 'active'
                  AND ST_Covers(boundary, ST_SetSRID(ST_Point(:longitude, :latitude), 4326))
                ORDER BY ST_Area(boundary::geography)
                LIMIT 1
                """
            ),
            {"latitude": latitude, "longitude": longitude},
        )
        if not code:
            raise UnsupportedMapRegion("No active OSM region covers this coordinate")
        url = settings.valhalla_url_for_region(str(code))
        if not url:
            raise UnsupportedMapRegion(f"No Valhalla pool is configured for region {code}")
        return url
    if settings.valhalla_url:
        return settings.valhalla_url.rstrip("/")
    raise UnsupportedMapRegion("No Valhalla service is configured")
