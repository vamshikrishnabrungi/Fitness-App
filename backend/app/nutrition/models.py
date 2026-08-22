from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FoodImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "food_images"
    __table_args__ = (UniqueConstraint("bucket", "object_name", name="uq_food_image_object"), {"schema": "nutrition"})
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    bucket: Mapped[str] = mapped_column(String(120), nullable=False)
    object_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    content_type: Mapped[str] = mapped_column(String(80), nullable=False)
    retain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FoodAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "food_analyses"
    __table_args__ = (UniqueConstraint("image_id", "source_object_hash", "prompt_version", name="uq_food_analysis_input"), {"schema": "nutrition"})
    image_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("nutrition.food_images.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_object_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(80))
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Meal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meals"
    __table_args__ = ({"schema": "nutrition"},)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("nutrition.food_analyses.id"))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    calories_kcal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    protein_g: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    carbohydrate_g: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    fat_g: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    fibre_g: Mapped[float | None] = mapped_column(Numeric(10, 2))
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    items_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
