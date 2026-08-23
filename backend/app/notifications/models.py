from datetime import datetime
from typing import Any
from uuid import UUID
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base, UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("source_event_id", "recipient_user_id", "notification_type", name="uq_notification_source_recipient"),
        UniqueConstraint("deduplication_key", name="uq_notification_deduplication"),
        {"schema": "operations"},
    )
    recipient_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(60), nullable=False)
    deduplication_key: Mapped[str] = mapped_column(String(240), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(String(500), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PushToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "push_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_push_token_hash"), {"schema": "operations"})
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    encrypted_token: Mapped[str] = mapped_column(String(2000), nullable=False)
    wrapped_dek: Mapped[str] = mapped_column(String(2000), nullable=False)
    kms_key_version: Mapped[str] = mapped_column(String(300), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NotificationDelivery(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint("notification_id", "push_token_id", name="uq_notification_push_delivery"),
        {"schema": "operations"},
    )
    notification_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("operations.notifications.id", ondelete="CASCADE"), nullable=False
    )
    push_token_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("operations.push_tokens.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(300))
    last_error: Mapped[str | None] = mapped_column(Text)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    receipt_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
