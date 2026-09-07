"""Allow deterministic reference-data plans without legacy recipes.

Revision ID: 20260825_12
Revises: 20260825_11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260825_12"
down_revision = "20260825_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("plans", "content_release_id", nullable=True, schema="training")
    op.add_column("plans", sa.Column("dataset_hash", sa.String(length=64)), schema="training")
    op.alter_column("sessions", "recipe_id", nullable=True, schema="training")
    op.alter_column("sessions", "recipe_version", nullable=True, schema="training")
    op.alter_column("session_items", "slot_id", nullable=True, schema="training")


def downgrade() -> None:
    op.alter_column("session_items", "slot_id", nullable=False, schema="training")
    op.alter_column("sessions", "recipe_version", nullable=False, schema="training")
    op.alter_column("sessions", "recipe_id", nullable=False, schema="training")
    op.drop_column("plans", "dataset_hash", schema="training")
    op.alter_column("plans", "content_release_id", nullable=False, schema="training")
