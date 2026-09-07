"""Persist explicit athlete consent for cross-training modalities."""

from alembic import op
import sqlalchemy as sa

revision = "20260827_20"
down_revision = "20260827_19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("cross_training_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="athlete",
    )


def downgrade() -> None:
    op.drop_column("profiles", "cross_training_consent", schema="athlete")
