"""Delete every account and user-owned record while preserving released knowledge."""
from __future__ import annotations

import asyncio
from sqlalchemy import text
from backend.app.core.database import engine


async def main() -> None:
    async with engine.begin() as connection:
        before = (await connection.execute(text("SELECT count(*) FROM identity.users"))).scalar_one()
        await connection.execute(text("DELETE FROM activity.edits"))
        await connection.execute(text("DELETE FROM competition.moderation_decisions"))
        await connection.execute(text("DELETE FROM knowledge.content_reviews"))
        await connection.execute(text("UPDATE knowledge.content_releases SET published_by=NULL"))
        await connection.execute(text("UPDATE knowledge.source_imports SET committed_by=NULL"))
        await connection.execute(text("DELETE FROM identity.users"))
        after = (await connection.execute(text("SELECT count(*) FROM identity.users"))).scalar_one()
        print(f"identity.users: {before} -> {after}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
