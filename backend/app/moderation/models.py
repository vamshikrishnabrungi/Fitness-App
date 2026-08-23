from datetime import datetime
from typing import Any
from uuid import UUID
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CompetitionFlag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "competition_flags"
    __table_args__ = (UniqueConstraint("subject_type", "subject_id", "flag_code", "computation_version", name="uq_competition_flag"), {"schema": "competition"})
    subject_type: Mapped[str] = mapped_column(String(24), nullable=False)
    subject_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    flag_code: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    computation_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)


class ModerationDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "moderation_decisions"
    __table_args__ = ({"schema": "competition"},)
    flag_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.competition_flags.id", ondelete="CASCADE"), nullable=False)
    moderator_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModerationAppeal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "moderation_appeals"
    __table_args__ = (UniqueConstraint("decision_id", "athlete_id", name="uq_moderation_appeal"), {"schema": "competition"})
    decision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.moderation_decisions.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)

