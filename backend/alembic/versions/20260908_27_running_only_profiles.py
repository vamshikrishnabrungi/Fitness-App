"""Add runner-specific profile and goal fields.

Revision ID: 20260908_27
Revises: 20260908_26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260908_27"
down_revision = "20260908_26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("distance_unit", sa.String(2), nullable=False, server_default="km"), schema="athlete")
    op.add_column("profiles", sa.Column("running_experience", sa.String(20), nullable=False, server_default="beginner"), schema="athlete")
    op.add_column("profiles", sa.Column("runs_per_week", sa.Integer(), nullable=False, server_default="0"), schema="athlete")
    op.add_column("profiles", sa.Column("weekly_distance_m", sa.Numeric(10, 2), nullable=False, server_default="0"), schema="athlete")
    op.add_column("profiles", sa.Column("longest_recent_run_m", sa.Numeric(10, 2), nullable=False, server_default="0"), schema="athlete")
    op.add_column("profiles", sa.Column("recent_race_event", sa.String(40)), schema="athlete")
    op.add_column("profiles", sa.Column("recent_race_time_seconds", sa.Integer()), schema="athlete")
    op.add_column("profiles", sa.Column("training_interruption", sa.String(24), nullable=False, server_default="none"), schema="athlete")
    op.add_column("profiles", sa.Column("terrains", postgresql.ARRAY(sa.String(30)), nullable=False, server_default="{}"), schema="athlete")
    op.add_column("goals", sa.Column("target_event", sa.String(40)), schema="athlete")
    op.add_column("goals", sa.Column("target_distance_m", sa.Numeric(12, 2)), schema="athlete")
    op.add_column("goals", sa.Column("target_time_seconds", sa.Integer()), schema="athlete")


def downgrade() -> None:
    for column in ("target_time_seconds", "target_distance_m", "target_event"):
        op.drop_column("goals", column, schema="athlete")
    for column in ("terrains", "training_interruption", "recent_race_time_seconds", "recent_race_event", "longest_recent_run_m", "weekly_distance_m", "runs_per_week", "running_experience", "distance_unit"):
        op.drop_column("profiles", column, schema="athlete")
