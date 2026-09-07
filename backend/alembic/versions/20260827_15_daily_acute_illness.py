"""Capture an explicit acute-illness generation stop.

Revision ID: 20260827_15
Revises: 20260827_14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_15"
down_revision = "20260827_14"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "daily_check_ins",
        sa.Column("acute_illness", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="health",
    )


def downgrade() -> None:
    op.drop_column("daily_check_ins", "acute_illness", schema="health")
