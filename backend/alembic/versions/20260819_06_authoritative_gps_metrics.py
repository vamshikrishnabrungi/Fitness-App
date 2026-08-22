"""Record authoritative device-smoothed GPS metrics and activity surface."""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260819_06"
down_revision: str | None = "20260815_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("activities", sa.Column("surface", sa.String(length=20), server_default="road", nullable=False), schema="activity")
    op.add_column("activities", sa.Column("distance_source", sa.String(length=30), server_default="device_smoothed_gps", nullable=False), schema="activity")
    op.add_column("activities", sa.Column("device_distance_m", sa.Numeric(12, 2), nullable=True), schema="activity")
    op.add_column("activities", sa.Column("server_confirmation_delta_m", sa.Numeric(12, 2), nullable=True), schema="activity")
    op.add_column("activities", sa.Column("elevation_source", sa.String(length=20), nullable=True), schema="activity")


def downgrade() -> None:
    for name in ("elevation_source", "server_confirmation_delta_m", "device_distance_m", "distance_source", "surface"):
        op.drop_column("activities", name, schema="activity")
