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
    cross_training_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    season_phase: Mapped[str] = mapped_column(String(32), default="general_preparation", nullable=False)
    health_context_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    distance_unit: Mapped[str] = mapped_column(String(2), default="km", nullable=False)
    running_experience: Mapped[str] = mapped_column(String(20), default="beginner", nullable=False)
    runs_per_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weekly_distance_m: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    longest_recent_run_m: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    recent_race_event: Mapped[str | None] = mapped_column(String(40))
    recent_race_time_seconds: Mapped[float | None] = mapped_column(Numeric(10, 2))
    training_interruption: Mapped[str] = mapped_column(String(24), default="none", nullable=False)
    terrains: Mapped[list[str]] = mapped_column(ARRAY(String(30)), default=list, nullable=False)


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
    target_event: Mapped[str | None] = mapped_column(String(40))
    target_distance_m: Mapped[float | None] = mapped_column(Numeric(12, 2))
    target_time_seconds: Mapped[float | None] = mapped_column(Numeric(10, 2))
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
    environments: Mapped[list[str]] = mapped_column(ARRAY(String(30)), default=list, nullable=False)


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


class AthleteMethodFamiliarity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "method_familiarity"
    __table_args__ = (
        UniqueConstraint("athlete_id", "method_id", name="uq_athlete_method_familiarity"),
        CheckConstraint(
            "familiarity IN ('familiar','previously_exposed','unfamiliar','unknown')",
            name="valid_method_familiarity",
        ),
        CheckConstraint("successful_exposures >= 0", name="nonnegative_method_exposures"),
        {"schema": "athlete"},
    )

    athlete_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("athlete.profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge.methods.id", ondelete="CASCADE"),
        nullable=False,
    )
    familiarity: Mapped[str] = mapped_column(String(24), nullable=False)
    successful_exposures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_performed_on: Mapped[date | None] = mapped_column(Date)


class Assessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessments"
    __table_args__ = ({"schema": "athlete"},)

    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_code: Mapped[str] = mapped_column(String(60), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(24), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
