"""add emoji to clubs

Revision ID: 20260823_08
Revises: 20260823_07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_08"
down_revision: str | None = "20260823_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clubs",
        sa.Column("emoji", sa.String(length=16), nullable=False, server_default="🏃"),
        schema="competition",
    )


def downgrade() -> None:
    op.drop_column("clubs", "emoji", schema="competition")
