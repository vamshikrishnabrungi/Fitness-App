"""Allow running plans to use the five or more days selected in onboarding."""

from alembic import op

revision = "20260909_30"
down_revision = "20260909_29"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE knowledge.phase_dose_policies "
        "SET maximum_sessions_per_week = GREATEST(maximum_sessions_per_week, 5)"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE knowledge.phase_dose_policies SET maximum_sessions_per_week = CASE "
        "WHEN phase_code IN ('general_preparation', 'specific_preparation') THEN 2 ELSE 1 END"
    )
