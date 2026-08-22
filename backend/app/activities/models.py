from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Activity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint("athlete_id", "source", "source_identity", name="uq_activity_athlete_source_identity"),
        CheckConstraint("status IN ('recording','paused','finishing','uploaded','processing','provisional','complete','rejected')", name="activity_status"),
        {"schema": "activity"},
    )
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    source_identity: Mapped[str] = mapped_column(String(200), nullable=False)
    sport_type: Mapped[str] = mapped_column(String(30), default="running", nullable=False)
    surface: Mapped[str] = mapped_column(String(20), default="road", nullable=False)
    distance_source: Mapped[str] = mapped_column(String(30), default="device_smoothed_gps", nullable=False)
    device_distance_m: Mapped[float | None] = mapped_column(Numeric(12, 2))
    server_confirmation_delta_m: Mapped[float | None] = mapped_column(Numeric(12, 2))
    elevation_source: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="recording", nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(16), default="private", nullable=False)
    title: Mapped[str | None] = mapped_column(String(160))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    elapsed_seconds: Mapped[int | None] = mapped_column(Integer)
    moving_seconds: Mapped[int | None] = mapped_column(Integer)
    paused_seconds: Mapped[int | None] = mapped_column(Integer)
    distance_m: Mapped[float | None] = mapped_column(Numeric(12, 2))
    elevation_gain_m: Mapped[float | None] = mapped_column(Numeric(10, 2))
    average_pace_s_per_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    calories_kcal: Mapped[float | None] = mapped_column(Numeric(10, 2))
    average_hr: Mapped[int | None] = mapped_column(Integer)
    average_cadence: Mapped[float | None] = mapped_column(Numeric(8, 2))
    raw_stream_object_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("activity.stream_objects.id", use_alter=True, name="fk_activities_raw_stream_object"),
    )
    cleaned_stream_object_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("activity.stream_objects.id", use_alter=True, name="fk_activities_cleaned_stream_object"),
    )
    matched_stream_object_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("activity.stream_objects.id", use_alter=True, name="fk_activities_matched_stream_object"),
    )
    route_geometry: Mapped[Any | None] = mapped_column(Geometry("LINESTRING", srid=4326, spatial_index=True))
    public_route_geometry: Mapped[Any | None] = mapped_column(Geometry("LINESTRING", srid=4326, spatial_index=True))
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    computation_version: Mapped[str | None] = mapped_column(String(40))
    rejection_code: Mapped[str | None] = mapped_column(String(60))
    processing_error_code: Mapped[str | None] = mapped_column(String(80))
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ActivityStreamObject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stream_objects"
    __table_args__ = (UniqueConstraint("bucket", "object_name", name="uq_stream_object"), {"schema": "activity"})
    activity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), index=True)
    variant: Mapped[str] = mapped_column(String(24), nullable=False)
    bucket: Mapped[str] = mapped_column(String(120), nullable=False)
    object_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class UploadChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "upload_chunks"
    __table_args__ = (UniqueConstraint("activity_id", "chunk_number", name="uq_activity_chunk"), {"schema": "activity"})
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False)
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False)
    object_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)


class ActivityQuality(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quality"
    __table_args__ = (UniqueConstraint("activity_id", "computation_version", name="uq_activity_quality_version"), {"schema": "activity"})
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False)
    computation_version: Mapped[str] = mapped_column(String(40), nullable=False)
    gps_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    duplicate_status: Mapped[str] = mapped_column(String(24), nullable=False)
    speed_status: Mapped[str] = mapped_column(String(24), nullable=False)
    vehicle_status: Mapped[str] = mapped_column(String(24), nullable=False)
    matcher_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    competition_eligible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    territory_eligible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(ARRAY(String(100)), default=list, nullable=False)


class ActivitySplit(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "splits"
    __table_args__ = (UniqueConstraint("activity_id", "split_type", "sequence", name="uq_activity_split"), {"schema": "activity"})
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False)
    split_type: Mapped[str] = mapped_column(String(20), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_m: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    elapsed_seconds: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    elevation_delta_m: Mapped[float | None] = mapped_column(Numeric(8, 2))
    average_hr: Mapped[int | None] = mapped_column(Integer)


class BestEffort(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "best_efforts"
    __table_args__ = (UniqueConstraint("activity_id", "distance_code", name="uq_activity_best_effort"), {"schema": "activity"})
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    distance_code: Mapped[str] = mapped_column(String(30), nullable=False)
    distance_m: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    elapsed_seconds: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    start_offset_seconds: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    quality_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_personal_record: Mapped[bool] = mapped_column(Boolean, nullable=False)


class ActivityClubAttribution(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "club_attributions"
    __table_args__ = (UniqueConstraint("activity_id", name="uq_activity_club_attribution"), {"schema": "activity"})
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    club_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("competition.clubs.id"), nullable=True)
    attributed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ActivityEdit(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "edits"
    __table_args__ = ({"schema": "activity"},)
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False)
    edit_type: Mapped[str] = mapped_column(String(30), nullable=False)
    before_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    after_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ActivityFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("activity_id", name="uq_activity_feedback"), {"schema": "activity"})
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    feeling: Mapped[str] = mapped_column(String(30), nullable=False)
    session_rpe: Mapped[float | None] = mapped_column(Numeric(3, 1))
    notes: Mapped[str | None] = mapped_column(Text)


class IntegrationConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "integration_connections"
    __table_args__ = (
        UniqueConstraint("athlete_id", "provider", name="uq_integration_athlete_provider"),
        {"schema": "activity"},
    )
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    external_athlete_id: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    cursor: Mapped[str | None] = mapped_column(String(500))
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ImportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        UniqueConstraint("athlete_id", "deduplication_key", name="uq_import_athlete_deduplication"),
        {"schema": "activity"},
    )
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    bucket: Mapped[str] = mapped_column(String(120), nullable=False)
    object_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    deduplication_key: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    diagnostics_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    activity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="SET NULL"))
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
