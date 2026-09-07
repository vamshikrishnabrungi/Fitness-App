from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DailyCheckIn(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "daily_check_ins"
    __table_args__ = (UniqueConstraint("athlete_id", "local_date", name="uq_athlete_daily_checkin"), {"schema": "health"})
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    sleep_minutes: Mapped[int | None] = mapped_column(Integer)
    sleep_quality: Mapped[int | None] = mapped_column(Integer)
    mood: Mapped[int | None] = mapped_column(Integer)
    stress: Mapped[int | None] = mapped_column(Integer)
    readiness: Mapped[int | None] = mapped_column(Integer)
    acute_illness: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sensitive_payload_ciphertext: Mapped[str | None] = mapped_column(Text)
    wrapped_dek: Mapped[str | None] = mapped_column(Text)
    kms_key_version: Mapped[str | None] = mapped_column(String(300))


class PainReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pain_reports"
    __table_args__ = ({"schema": "health"},)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    region_code: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    during_activity: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    payload_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    wrapped_dek: Mapped[str] = mapped_column(Text, nullable=False)
    kms_key_version: Mapped[str] = mapped_column(String(300), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)


class HealthMetricRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "metric_records"
    __table_args__ = (
        UniqueConstraint("athlete_id", "provider", "provider_record_hash", name="uq_health_metric_provider_record"),
        {"schema": "health"},
    )
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    wrapped_dek: Mapped[str] = mapped_column(Text, nullable=False)
    kms_key_version: Mapped[str] = mapped_column(String(300), nullable=False)
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
