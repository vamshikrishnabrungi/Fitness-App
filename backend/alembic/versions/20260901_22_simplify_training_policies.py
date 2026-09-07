"""remove duplicated availability, fallback and scenario policy tables

Revision ID: 20260901_22
Revises: 20260831_21
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_22"
down_revision = "20260831_21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("scenario_overlays", schema="knowledge")
    op.drop_table("training_mode_fallbacks", schema="knowledge")
    op.drop_table("category_level_availability", schema="knowledge")


def _identity_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def downgrade() -> None:
    op.create_table(
        "category_level_availability", *_identity_columns(),
        sa.Column("category_code", sa.String(80), nullable=False),
        sa.Column("athlete_level", sa.String(24), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("template_code", sa.String(100)),
        sa.Column("prerequisite_category", sa.String(80)),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_code", "athlete_level", name="uq_category_level_availability"),
        schema="knowledge",
    )
    op.create_table(
        "training_mode_fallbacks", *_identity_columns(),
        sa.Column("category_code", sa.String(80), nullable=False),
        sa.Column("athlete_level", sa.String(24), nullable=False),
        sa.Column("requested_mode", sa.String(40), nullable=False),
        sa.Column("fallback_category", sa.String(80), nullable=False),
        sa.Column("automatic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_code", "athlete_level", "requested_mode", name="uq_training_mode_fallback"),
        schema="knowledge",
    )
    op.create_table(
        "scenario_overlays", *_identity_columns(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("applies_to", sa.String(180), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_scenario_overlay_code"),
        schema="knowledge",
    )
