"""Allow canonical training category codes in session items.

Revision ID: 20260827_17
Revises: 20260827_16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_17"
down_revision = "20260827_16"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "session_items",
        "block_type",
        existing_type=sa.String(length=30),
        type_=sa.String(length=80),
        existing_nullable=False,
        schema="training",
    )


def downgrade() -> None:
    op.alter_column(
        "session_items",
        "block_type",
        existing_type=sa.String(length=80),
        type_=sa.String(length=30),
        existing_nullable=False,
        schema="training",
    )
