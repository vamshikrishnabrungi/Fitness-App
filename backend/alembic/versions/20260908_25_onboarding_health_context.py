"""Persist onboarding health context used for plan generation.

Revision ID: 20260908_25
Revises: 20260904_24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260908_25"
down_revision = "20260904_24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column(
            "health_context_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        schema="athlete",
    )


def downgrade() -> None:
    op.drop_column("profiles", "health_context_json", schema="athlete")
