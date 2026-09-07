"""Add versioned sport and scope restrictions to reference methods.

Revision ID: 20260827_13
Revises: 20260825_12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260827_13"
down_revision = "20260825_12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    empty_array = sa.text("'{}'::varchar[]")
    op.add_column(
        "training_reference_methods",
        sa.Column("sport_codes", postgresql.ARRAY(sa.String(40)), nullable=False, server_default=empty_array),
        schema="knowledge",
    )
    op.add_column(
        "training_reference_methods",
        sa.Column("scope_codes", postgresql.ARRAY(sa.String(80)), nullable=False, server_default=empty_array),
        schema="knowledge",
    )


def downgrade() -> None:
    op.drop_column("training_reference_methods", "scope_codes", schema="knowledge")
    op.drop_column("training_reference_methods", "sport_codes", schema="knowledge")
