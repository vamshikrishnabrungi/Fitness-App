from __future__ import annotations

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
if settings.cloud_sql_instance:
    from google.cloud.sql.connector import Connector, IPTypes, RefreshStrategy

    cloud_sql_connector = Connector(refresh_strategy=RefreshStrategy.LAZY)

    async def _cloud_sql_connection() -> Any:
        return await cloud_sql_connector.connect_async(
            settings.cloud_sql_instance,
            "asyncpg",
            user=settings.database_user,
            password=settings.database_password,
            db=settings.database_name,
            ip_type=IPTypes.PRIVATE,
        )

    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=_cloud_sql_connection,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )
else:
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
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
