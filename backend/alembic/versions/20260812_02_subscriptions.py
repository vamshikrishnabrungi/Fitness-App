"""add canonical subscription entitlements

Revision ID: 20260812_02
Revises: 20260810_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260812_02"
down_revision = "20260810_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("plan_code", sa.String(60), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("provider_subscription_id", sa.String(200), nullable=True),
        sa.Column("current_period_starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("status IN ('trialing','active','past_due','canceled','expired')", name="ck_subscriptions_subscription_status"),
        sa.ForeignKeyConstraint(["user_id"], ["identity.users.id"], ondelete="CASCADE", name="fk_subscriptions_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_subscriptions"),
        sa.UniqueConstraint("user_id", name="uq_subscription_user"),
        sa.UniqueConstraint("provider", "provider_subscription_id", name="uq_subscription_provider_identity"),
        schema="identity",
    )
    op.create_index("ix_identity_subscriptions_user_id", "subscriptions", ["user_id"], schema="identity")


def downgrade() -> None:
    op.drop_index("ix_identity_subscriptions_user_id", table_name="subscriptions", schema="identity")
    op.drop_table("subscriptions", schema="identity")
