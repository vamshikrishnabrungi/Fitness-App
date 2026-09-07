"""Make deterministic plan retries idempotent.

Revision ID: 20260827_14
Revises: 20260827_13
"""

from alembic import op


revision = "20260827_14"
down_revision = "20260827_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_training_plan_deterministic_input",
        "plans",
        ["athlete_id", "input_hash", "dataset_hash", "planner_version"],
        schema="training",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_training_plan_deterministic_input",
        "plans",
        type_="unique",
        schema="training",
    )
