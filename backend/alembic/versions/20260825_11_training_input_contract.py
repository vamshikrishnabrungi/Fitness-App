"""Persist the canonical training phase selected during onboarding.

Revision ID: 20260825_11
Revises: 20260823_10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260825_11"
down_revision = "20260823_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("season_phase", sa.String(length=32), nullable=False, server_default="general_preparation"),
        schema="athlete",
    )


def downgrade() -> None:
    op.drop_column("profiles", "season_phase", schema="athlete")
