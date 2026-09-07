"""Add versioned deterministic phase-dose policies.

Revision ID: 20260827_19
Revises: 20260827_18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260827_19"
down_revision = "20260827_18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "phase_dose_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("phase_code", sa.String(60), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("progression_mode", sa.String(32), nullable=False),
        sa.Column("maximum_categories", sa.Integer(), nullable=False),
        sa.Column("maximum_sessions_per_week", sa.Integer(), nullable=False),
        sa.Column("weekly_volume_multipliers", postgresql.JSONB(), nullable=False),
        sa.Column("novelty_policy", sa.String(40), nullable=False),
        sa.Column("policy_basis", sa.Text(), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "progression_mode IN ('development','maintain_week_1','competition_taper')",
            name="valid_phase_progression_mode",
        ),
        sa.CheckConstraint("maximum_categories BETWEEN 1 AND 8", name="valid_phase_category_limit"),
        sa.CheckConstraint("maximum_sessions_per_week BETWEEN 1 AND 7", name="valid_phase_session_limit"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phase_code", name="uq_phase_dose_policy"),
        schema="knowledge",
    )


def downgrade() -> None:
    op.drop_table("phase_dose_policies", schema="knowledge")
