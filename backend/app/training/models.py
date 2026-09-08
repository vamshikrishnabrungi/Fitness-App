from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TrainingPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plans"
    __table_args__ = (
        UniqueConstraint("athlete_id", "plan_number", name="uq_athlete_plan_number"),
        UniqueConstraint(
            "athlete_id", "input_hash", "dataset_hash", "planner_version",
            name="uq_training_plan_deterministic_input",
        ),
        {"schema": "training"},
    )
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", nullable=False)
    goal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.goals.id"), nullable=False)
    # Legacy recipe plans pin a content release. Reference-data plans instead
    # pin one deterministic dataset hash; both formats can be read during the
    # migration away from the old package/release generator.
    content_release_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.content_releases.id"))
    dataset_hash: Mapped[str | None] = mapped_column(String(64))
    planner_version: Mapped[str] = mapped_column(String(40), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    input_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    decision_trace_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    validation_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    materialized_through: Mapped[date | None] = mapped_column(Date)
    selection_horizon_weeks: Mapped[int] = mapped_column(Integer, default=2, nullable=False)


class TrainingGenerationRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generation_runs"
    __table_args__ = (
        UniqueConstraint("plan_id", "horizon_starts_on", name="uq_training_generation_plan_horizon"),
        CheckConstraint("status IN ('accepted','rejected','failed')", name="generation_status"),
        CheckConstraint("attempt_count BETWEEN 1 AND 2", name="generation_attempt_count"),
        CheckConstraint("latency_ms >= 0", name="generation_latency"),
        {"schema": "training"},
    )
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    content_release_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.content_releases.id"), nullable=False)
    plan_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("training.plans.id", ondelete="SET NULL"))
    horizon_starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model_id: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(60), nullable=False)
    response_schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    planner_version: Mapped[str] = mapped_column(String(40), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    accepted_output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    validation_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class TrainingPhase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "phases"
    __table_args__ = (UniqueConstraint("plan_id", "sequence", name="uq_plan_phase_sequence"), {"schema": "training"})
    plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("training.plans.id", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    phase_code: Mapped[str] = mapped_column(String(50), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    priority_vector_json: Mapped[dict[str, float]] = mapped_column(JSONB, nullable=False)


class TrainingWeek(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "weeks"
    __table_args__ = (UniqueConstraint("plan_id", "week_number", name="uq_plan_week_number"), {"schema": "training"})
    plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("training.plans.id", ondelete="CASCADE"), nullable=False)
    phase_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("training.phases.id", ondelete="CASCADE"), nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    planned_load: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    deload: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    structure_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    materialization_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)


class TrainingSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint("week_id", "sequence", name="uq_week_session_sequence"),
        ForeignKeyConstraint(["recipe_id", "recipe_version"], ["knowledge.recipe_versions.recipe_id", "knowledge.recipe_versions.recipe_version"], ondelete="RESTRICT"),
        {"schema": "training"},
    )
    week_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("training.weeks.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    recipe_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    recipe_version: Mapped[int | None] = mapped_column(Integer)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    session_type: Mapped[str] = mapped_column(String(40), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    load_class: Mapped[str] = mapped_column(String(16), nullable=False)
    venue_code: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class SessionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "session_items"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_session_item_sequence"),
        CheckConstraint(
            "((method_id IS NOT NULL AND method_version IS NOT NULL AND generated_exercise_json IS NULL) OR "
            "(method_id IS NULL AND method_version IS NULL AND generated_exercise_json IS NOT NULL))",
            name="ck_session_item_exercise_source",
        ),
        ForeignKeyConstraint(["method_id", "method_version"], ["knowledge.method_versions.method_id", "knowledge.method_versions.content_version"], ondelete="RESTRICT"),
        {"schema": "training"},
    )
    session_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("training.sessions.id", ondelete="CASCADE"), nullable=False)
    method_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    method_version: Mapped[int | None] = mapped_column(Integer)
    # SQL NULL identifies catalog-backed rows. JSONB's default would encode
    # Python None as JSON `null`, which does not satisfy the source constraint.
    generated_exercise_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
    slot_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.recipe_slots.id"))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    block_type: Mapped[str] = mapped_column(String(80), nullable=False)
    prescription_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    substitution_methods_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    decision_trace_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)


class SessionCompletion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "session_completions"
    __table_args__ = (UniqueConstraint("session_id", name="uq_session_completion"), {"schema": "training"})
    session_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("training.sessions.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    session_rpe: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    completion_ratio: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    pain_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    calculated_load: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class AdaptationDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "adaptations"
    __table_args__ = ({"schema": "training"},)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    source_session_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("training.sessions.id"))
    decision_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(60), nullable=False)
    rule_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("knowledge.prescription_rules.id"))
    before_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    after_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
