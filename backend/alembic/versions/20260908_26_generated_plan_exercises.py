"""Allow plan-scoped AI generated exercises.

Revision ID: 20260908_26
Revises: 20260908_25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260908_26"
down_revision = "20260908_25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("session_items", "method_id", nullable=True, schema="training")
    op.alter_column("session_items", "method_version", nullable=True, schema="training")
    op.add_column("session_items", sa.Column("generated_exercise_json", postgresql.JSONB(none_as_null=True), nullable=True), schema="training")
    op.create_check_constraint(
        "ck_session_item_exercise_source",
        "session_items",
        "((method_id IS NOT NULL AND method_version IS NOT NULL AND generated_exercise_json IS NULL) OR "
        "(method_id IS NULL AND method_version IS NULL AND generated_exercise_json IS NOT NULL))",
        schema="training",
    )


def downgrade() -> None:
    op.drop_constraint("ck_session_item_exercise_source", "session_items", schema="training", type_="check")
    op.drop_column("session_items", "generated_exercise_json", schema="training")
    op.alter_column("session_items", "method_version", nullable=False, schema="training")
    op.alter_column("session_items", "method_id", nullable=False, schema="training")
