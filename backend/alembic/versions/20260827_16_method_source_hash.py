"""Pin method versions to their canonical source import.

Revision ID: 20260827_16
Revises: 20260827_15
"""

from alembic import op
import sqlalchemy as sa


revision = "20260827_16"
down_revision = "20260827_15"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "method_versions",
        sa.Column("source_hash", sa.String(length=64), nullable=True),
        schema="knowledge",
    )


def downgrade() -> None:
    op.drop_column("method_versions", "source_hash", schema="knowledge")
