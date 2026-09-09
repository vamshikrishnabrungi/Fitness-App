"""Store race times with hundredth-second precision and remove ultra event data."""

from alembic import op
import sqlalchemy as sa

revision = "20260909_29"
down_revision = "20260908_28"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("profiles", "recent_race_time_seconds", schema="athlete", existing_type=sa.Integer(), type_=sa.Numeric(10, 2), existing_nullable=True)
    op.alter_column("goals", "target_time_seconds", schema="athlete", existing_type=sa.Integer(), type_=sa.Numeric(10, 2), existing_nullable=True)
    op.execute("UPDATE athlete.profiles SET recent_race_event = NULL, recent_race_time_seconds = NULL WHERE recent_race_event = 'ultra'")
    op.execute("UPDATE athlete.goals SET status = 'cancelled' WHERE target_event = 'ultra'")
    op.execute("UPDATE athlete.sports SET event_code = NULL WHERE event_code = 'ultra'")


def downgrade() -> None:
    op.alter_column("goals", "target_time_seconds", schema="athlete", existing_type=sa.Numeric(10, 2), type_=sa.Integer(), existing_nullable=True)
    op.alter_column("profiles", "recent_race_time_seconds", schema="athlete", existing_type=sa.Numeric(10, 2), type_=sa.Integer(), existing_nullable=True)
