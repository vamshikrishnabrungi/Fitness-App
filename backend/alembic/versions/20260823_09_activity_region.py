"""derive leaderboard region from each activity

Revision ID: 20260823_09
Revises: 20260823_08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260823_09"
down_revision = "20260823_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activities",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="activity",
    )
    op.create_foreign_key(
        "fk_activities_region_id_geographic_regions",
        "activities",
        "geographic_regions",
        ["region_id"],
        ["id"],
        source_schema="activity",
        referent_schema="activity",
    )
    op.create_index("ix_activity_activities_region_id", "activities", ["region_id"], schema="activity")


def downgrade() -> None:
    op.drop_index("ix_activity_activities_region_id", table_name="activities", schema="activity")
    op.drop_constraint("fk_activities_region_id_geographic_regions", "activities", schema="activity", type_="foreignkey")
    op.drop_column("activities", "region_id", schema="activity")
