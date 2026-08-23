"""widen street_edge OSM identifiers to bigint

OSM node IDs (and increasingly way IDs) exceed the 32-bit integer range, so
street-edge ingestion of any real region overflows INTEGER columns. Widen the
OSM identifier columns to BIGINT.

Revision ID: 20260823_07
Revises: 20260819_06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_07"
down_revision: str | None = "20260819_06"
branch_labels = None
depends_on = None

_COLUMNS = ("osm_way_id", "from_node_id", "to_node_id")


def upgrade() -> None:
    for column in _COLUMNS:
        op.alter_column("street_edges", column, type_=sa.BigInteger(),
                        existing_type=sa.Integer(), existing_nullable=False, schema="activity")


def downgrade() -> None:
    for column in _COLUMNS:
        op.alter_column("street_edges", column, type_=sa.Integer(),
                        existing_type=sa.BigInteger(), existing_nullable=False, schema="activity")
