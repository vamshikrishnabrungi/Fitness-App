"""MongoDB client and DB instance shared across modules."""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient

from backend.core.config import MONGO_URL, DB_NAME

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
