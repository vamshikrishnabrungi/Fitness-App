from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.geo_db import (
    mirror_activity_geometry,
    mirror_segment_geometry,
    mirror_street_edge,
    postgis_configured,
)


load_dotenv(Path(__file__).resolve().parent / '.env')


async def backfill(limit: int = 0) -> dict[str, int]:
    if not postgis_configured():
        raise RuntimeError('POSTGRES_URL is required')
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'sftc_database')]
    counts = {'activities': 0, 'segments': 0, 'street_edges': 0}
    try:
        specifications = (
            ('activities', {'status': {'$ne': 'deleted'}, 'route_geojson': {'$ne': None}}, mirror_activity_geometry),
            ('segments', {'status': 'active'}, mirror_segment_geometry),
            ('street_edges', {'status': 'active'}, mirror_street_edge),
        )
        for collection_name, query, mirror in specifications:
            cursor = db[collection_name].find(query).sort('created_at', 1)
            if limit:
                cursor = cursor.limit(limit)
            async for document in cursor:
                if await mirror(document):
                    counts[collection_name] += 1
        return counts
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description='Idempotently mirror Mongo geospatial records into PostGIS')
    parser.add_argument('--limit', type=int, default=0, help='Maximum records per collection')
    args = parser.parse_args()
    print(asyncio.run(backfill(max(0, args.limit))))


if __name__ == '__main__':
    main()
