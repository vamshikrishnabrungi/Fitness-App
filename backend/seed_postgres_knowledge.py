#!/usr/bin/env python3
"""Seed only controlled PostgreSQL knowledge taxonomy; no content is published."""
from __future__ import annotations

import asyncio

from backend.app.core.database import SessionFactory
from backend.app.knowledge.bootstrap import seed_controlled_taxonomy


async def run() -> None:
    async with SessionFactory() as session:
        print(await seed_controlled_taxonomy(session))


if __name__ == "__main__":
    asyncio.run(run())
