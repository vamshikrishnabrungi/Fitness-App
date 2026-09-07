"""index OTP IP throttling window

Revision ID: 20260823_10
Revises: 20260823_09
"""

from alembic import op


revision = "20260823_10"
down_revision = "20260823_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_identity_otp_challenges_ip_created",
        "otp_challenges",
        ["requested_ip_hash", "created_at"],
        schema="identity",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_identity_otp_challenges_ip_created",
        table_name="otp_challenges",
        schema="identity",
    )
