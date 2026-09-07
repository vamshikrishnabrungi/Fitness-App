"""Add venue-aware availability, method familiarity, and session venues.

Revision ID: 20260827_18
Revises: 20260827_17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260827_18"
down_revision = "20260827_17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    empty_array = sa.text("'{}'::varchar[]")
    op.add_column(
        "availability_windows",
        sa.Column(
            "environments",
            postgresql.ARRAY(sa.String(30)),
            nullable=False,
            server_default=empty_array,
        ),
        schema="athlete",
    )
    op.create_table(
        "method_familiarity",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("athlete_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("method_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("familiarity", sa.String(24), nullable=False),
        sa.Column("successful_exposures", sa.Integer(), nullable=False),
        sa.Column("last_performed_on", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "familiarity IN ('familiar','previously_exposed','unfamiliar','unknown')",
            name="valid_method_familiarity",
        ),
        sa.CheckConstraint("successful_exposures >= 0", name="nonnegative_method_exposures"),
        sa.ForeignKeyConstraint(
            ["athlete_id"], ["athlete.profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["method_id"], ["knowledge.methods.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("athlete_id", "method_id", name="uq_athlete_method_familiarity"),
        schema="athlete",
    )
    op.create_index(
        "ix_method_familiarity_athlete_id",
        "method_familiarity",
        ["athlete_id"],
        schema="athlete",
    )
    op.add_column(
        "sessions",
        sa.Column("venue_code", sa.String(30), nullable=True),
        schema="training",
    )


def downgrade() -> None:
    op.drop_column("sessions", "venue_code", schema="training")
    op.drop_index(
        "ix_method_familiarity_athlete_id",
        table_name="method_familiarity",
        schema="athlete",
    )
    op.drop_table("method_familiarity", schema="athlete")
    op.drop_column("availability_windows", "environments", schema="athlete")
