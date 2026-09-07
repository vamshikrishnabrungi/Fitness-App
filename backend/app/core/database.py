from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, MetaData
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import get_settings
from .ids import uuid7


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid7)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


settings = get_settings()
cloud_sql_connector: Any | None = None
if settings.environment == "test":
    engine = create_async_engine(
        settings.test_database_url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=10,
        pool_recycle=1_800,
    )
else:
    from google.cloud.sql.connector import Connector, IPTypes, RefreshStrategy

    async def _cloud_sql_connection() -> Any:
        global cloud_sql_connector
        if cloud_sql_connector is None:
            # The connector binds to the currently running event loop. Creating
            # it at module import breaks under Uvicorn, which installs its loop
            # only after importing the application.
            cloud_sql_connector = Connector(
                loop=asyncio.get_running_loop(),
                refresh_strategy=RefreshStrategy.LAZY,
            )
        return await cloud_sql_connector.connect_async(
            settings.cloud_sql_instance,
            "asyncpg",
            user=settings.database_user,
            password=settings.database_password,
            db=settings.database_name,
            ip_type=IPTypes[settings.cloud_sql_ip_type],
            command_timeout=30,
            server_settings={"statement_timeout": "30000", "idle_in_transaction_session_timeout": "30000"},
        )

    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=_cloud_sql_connection,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=10,
        pool_recycle=1_800,
    )
SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session


async def close_database() -> None:
    await engine.dispose()
    if cloud_sql_connector is not None:
        await cloud_sql_connector.close_async()


def model_dict(instance: Any) -> dict[str, Any]:
    return {column.name: getattr(instance, column.name) for column in instance.__table__.columns}
