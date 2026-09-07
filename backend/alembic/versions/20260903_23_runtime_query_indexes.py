"""Add indexes for latency-critical runtime queries.

Revision ID: 20260903_23
Revises: 20260901_22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260903_23"
down_revision = "20260901_22"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_identity_otp_email_created",
        "otp_challenges",
        ["normalized_email", "created_at"],
        schema="identity",
    )
    op.create_index(
        "ix_operations_outbox_unpublished_created",
        "outbox_events",
        ["created_at"],
        schema="operations",
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.create_index("ix_operations_idempotency_expires_at", "idempotency_records", ["expires_at"], schema="operations")
    op.create_index("ix_activity_activities_athlete_started", "activities", ["athlete_id", "started_at"], schema="activity")
    op.create_index("ix_activity_activities_status_started", "activities", ["status", "started_at"], schema="activity")


def downgrade() -> None:
    op.drop_index("ix_activity_activities_status_started", table_name="activities", schema="activity")
    op.drop_index("ix_activity_activities_athlete_started", table_name="activities", schema="activity")
    op.drop_index("ix_operations_idempotency_expires_at", table_name="idempotency_records", schema="operations")
    op.drop_index("ix_operations_outbox_unpublished_created", table_name="outbox_events", schema="operations")
    op.drop_index("ix_identity_otp_email_created", table_name="otp_challenges", schema="identity")
