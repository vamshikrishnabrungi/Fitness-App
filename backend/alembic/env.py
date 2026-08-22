from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context


config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

url = (os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")).strip()
if url.startswith("postgres://"):
    url = "postgresql+asyncpg://" + url[len("postgres://") :]
elif url.startswith("postgresql://"):
    url = "postgresql+asyncpg://" + url[len("postgresql://") :]
config.set_main_option("sqlalchemy.url", url)
from backend.app.core.database import Base, close_database, engine as app_engine
import backend.app.models  # noqa: F401,E402

target_metadata = Base.metadata


def include_object(object_, name: str | None, type_: str, reflected: bool, compare_to) -> bool:
    # Owned by the PostGIS extension, not by Runlete migrations.
    return not (type_ == "table" and name == "spatial_ref_sys" and reflected)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, include_schemas=True, compare_type=True, include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    try:
        async with app_engine.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await close_database()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
