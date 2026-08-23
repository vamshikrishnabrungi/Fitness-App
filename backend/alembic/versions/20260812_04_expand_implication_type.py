"""Expand evidence implication vocabulary storage.

Revision ID: 20260812_04
Revises: 20260812_03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260812_04"
down_revision: str | None = "20260812_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "evidence_claim_versions",
        "implication_type",
        schema="knowledge",
        existing_type=sa.String(length=20),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
    op.alter_column(
        "demand_fact_versions",
        "implication_type",
        schema="knowledge",
        existing_type=sa.String(length=20),
        type_=sa.String(length=32),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "demand_fact_versions",
        "implication_type",
        schema="knowledge",
        existing_type=sa.String(length=32),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
    op.alter_column(
        "evidence_claim_versions",
        "implication_type",
        schema="knowledge",
        existing_type=sa.String(length=32),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
