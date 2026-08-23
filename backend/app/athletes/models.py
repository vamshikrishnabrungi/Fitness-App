from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AthleteProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("training_age_years >= 0", name="training_age_nonnegative"),
        {"schema": "athlete"},
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2))
    region_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    competition_level: Mapped[str] = mapped_column(String(24), default="recreational", nullable=False)
    training_age_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maximum_session_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    post_clearance_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AthleteSport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sports"
    __table_args__ = (
        UniqueConstraint("athlete_id", "sport_code", name="uq_athlete_sport"),
        {"schema": "athlete"},
    )

    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False)
    event_code: Mapped[str | None] = mapped_column(String(60))
    role_code: Mapped[str | None] = mapped_column(String(60))
    discipline_code: Mapped[str | None] = mapped_column(String(60))
    format_code: Mapped[str | None] = mapped_column(String(60))
    weight_class_code: Mapped[str | None] = mapped_column(String(40))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weekly_external_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sessions_per_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AthleteGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "goals"
    __table_args__ = ({"schema": "athlete"},)

    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[float | None] = mapped_column(Numeric(12, 3))
    target_unit: Mapped[str | None] = mapped_column(String(24))
    target_date: Mapped[date | None] = mapped_column(Date)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)


class AvailabilityWindow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "availability_windows"
    __table_args__ = (
        UniqueConstraint("athlete_id", "weekday", "start_minute", name="uq_availability_slot"),
        CheckConstraint("weekday BETWEEN 0 AND 6", name="valid_weekday"),
        CheckConstraint("start_minute BETWEEN 0 AND 1439", name="valid_start_minute"),
        CheckConstraint("duration_minutes > 0", name="positive_duration"),
        {"schema": "athlete"},
    )

    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_minute: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)


class ExternalLoad(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_loads"
    __table_args__ = ({"schema": "athlete"},)

    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    sport_code: Mapped[str] = mapped_column(String(40), nullable=False)
    load_type: Mapped[str] = mapped_column(String(30), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    intensity: Mapped[str] = mapped_column(String(16), nullable=False)
    recurrence_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class EquipmentAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "equipment_access"
    __table_args__ = (UniqueConstraint("athlete_id", "equipment_code", name="uq_athlete_equipment"), {"schema": "athlete"})

    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    equipment_code: Mapped[str] = mapped_column(String(60), nullable=False)
    environments: Mapped[list[str]] = mapped_column(ARRAY(String(30)), default=list, nullable=False)


class Assessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessments"
    __table_args__ = ({"schema": "athlete"},)

    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_code: Mapped[str] = mapped_column(String(60), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(24), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
