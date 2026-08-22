"""Add production storage for training reference datasets.

Revision ID: 20260815_05
Revises: 20260812_04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260815_05"
down_revision: str | None = "20260812_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _identity_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    ]


def upgrade() -> None:
    op.create_table("training_reference_templates", *_identity_columns(), sa.Column("code", sa.String(100), nullable=False), sa.Column("latest_version", sa.Integer(), nullable=False, server_default="1"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code", name="uq_training_reference_template_code"), schema="knowledge")
    op.create_table(
        "training_reference_template_versions",
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("content_version", sa.Integer(), nullable=False),
        sa.Column("research_phase", sa.Integer(), nullable=False), sa.Column("category_code", sa.String(80), nullable=False), sa.Column("name", sa.String(180), nullable=False),
        sa.Column("athlete_level", sa.String(24), nullable=False), sa.Column("duration_weeks", sa.Integer(), nullable=False), sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("source_template_ids", postgresql.ARRAY(sa.String(100)), nullable=False), sa.Column("applicable_scenarios", postgresql.ARRAY(sa.String(80)), nullable=False),
        sa.Column("selection_policy_json", postgresql.JSONB(), nullable=False), sa.Column("selection_rules_json", postgresql.JSONB(), nullable=False),
        sa.Column("exercise_progression_policy", sa.Text(), nullable=False), sa.Column("week_4_policy", sa.Text(), nullable=False), sa.Column("mandatory_stops", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("ai_use", sa.Text(), nullable=False), sa.Column("prompt_reference_text", sa.Text(), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("duration_weeks BETWEEN 1 AND 52", name="training_reference_duration"),
        sa.ForeignKeyConstraint(["template_id"], ["knowledge.training_reference_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("template_id", "content_version", name="pk_training_reference_template_versions"), schema="knowledge",
    )
    op.create_index(op.f("ix_knowledge_training_reference_template_versions_category_code"), "training_reference_template_versions", ["category_code"], schema="knowledge")
    op.create_index(op.f("ix_knowledge_training_reference_template_versions_athlete_level"), "training_reference_template_versions", ["athlete_level"], schema="knowledge")
    op.create_table(
        "training_reference_methods", sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False), sa.Column("sequence", sa.Integer(), nullable=False), sa.Column("method_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("method_version", sa.Integer(), nullable=False), sa.Column("block_role", sa.String(32), nullable=False), sa.Column("applicable_modes", postgresql.ARRAY(sa.String(40)), nullable=False),
        sa.Column("implementation_note", sa.Text(), nullable=False), sa.ForeignKeyConstraint(["template_id", "template_version"], ["knowledge.training_reference_template_versions.template_id", "knowledge.training_reference_template_versions.content_version"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["method_id", "method_version"], ["knowledge.method_versions.method_id", "knowledge.method_versions.content_version"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "template_version", "sequence", name="uq_training_reference_method_sequence"), sa.UniqueConstraint("template_id", "template_version", "method_id", name="uq_training_reference_method"), schema="knowledge",
    )
    op.create_table(
        "training_reference_weeks", sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False), sa.Column("week_number", sa.Integer(), nullable=False), sa.Column("intent", sa.String(180), nullable=False),
        sa.Column("sessions_per_week", sa.String(40), nullable=False), sa.Column("prescription_json", postgresql.JSONB(), nullable=False), sa.Column("progression_condition", sa.Text(), nullable=False),
        sa.Column("regression_condition", sa.Text(), nullable=False), sa.CheckConstraint("week_number BETWEEN 1 AND 52", name="training_reference_week_number"),
        sa.ForeignKeyConstraint(["template_id", "template_version"], ["knowledge.training_reference_template_versions.template_id", "knowledge.training_reference_template_versions.content_version"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("template_id", "template_version", "week_number", name="uq_training_reference_week"), schema="knowledge",
    )
    op.create_table("category_level_availability", *_identity_columns(), sa.Column("category_code", sa.String(80), nullable=False), sa.Column("athlete_level", sa.String(24), nullable=False), sa.Column("available", sa.Boolean(), nullable=False), sa.Column("template_code", sa.String(100)), sa.Column("prerequisite_category", sa.String(80)), sa.Column("reason", sa.Text(), nullable=False), sa.Column("source_hash", sa.String(64), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("category_code", "athlete_level", name="uq_category_level_availability"), schema="knowledge")
    op.create_table("sport_mode_policies", *_identity_columns(), sa.Column("sport_code", sa.String(40), nullable=False), sa.Column("primary_mode", sa.String(40), nullable=False), sa.Column("cross_training_requires_opt_in", sa.Boolean(), nullable=False), sa.Column("source_hash", sa.String(64), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("sport_code", name="uq_sport_mode_policy"), schema="knowledge")
    op.create_table("training_mode_fallbacks", *_identity_columns(), sa.Column("category_code", sa.String(80), nullable=False), sa.Column("athlete_level", sa.String(24), nullable=False), sa.Column("requested_mode", sa.String(40), nullable=False), sa.Column("fallback_category", sa.String(80), nullable=False), sa.Column("automatic", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("source_hash", sa.String(64), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("category_code", "athlete_level", "requested_mode", name="uq_training_mode_fallback"), schema="knowledge")
    op.create_table("scenario_overlays", *_identity_columns(), sa.Column("code", sa.String(80), nullable=False), sa.Column("applies_to", sa.String(180), nullable=False), sa.Column("instruction", sa.Text(), nullable=False), sa.Column("source_hash", sa.String(64), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code", name="uq_scenario_overlay_code"), schema="knowledge")
    op.create_table("sport_template_priorities", *_identity_columns(), sa.Column("sport_code", sa.String(40), nullable=False), sa.Column("scope_type", sa.String(30), nullable=False), sa.Column("scope_code", sa.String(80), nullable=False), sa.Column("phase_code", sa.String(60), nullable=False), sa.Column("goal_code", sa.String(80), nullable=False), sa.Column("primary_template_category", sa.String(80), nullable=False), sa.Column("session_block_order", postgresql.ARRAY(sa.String(80)), nullable=False), sa.Column("priority_basis", sa.Text(), nullable=False), sa.Column("source_hash", sa.String(64), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("sport_code", "scope_type", "scope_code", "phase_code", "goal_code", name="uq_sport_template_priority_scope"), schema="knowledge")
    op.create_index(op.f("ix_knowledge_sport_template_priorities_sport_code"), "sport_template_priorities", ["sport_code"], schema="knowledge")
    op.create_table("sport_template_priority_items", sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("priority_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("rank", sa.Integer(), nullable=False), sa.Column("category_code", sa.String(80), nullable=False), sa.Column("weight", sa.Numeric(4, 3), nullable=False), sa.CheckConstraint("rank BETWEEN 1 AND 8", name="sport_template_priority_rank"), sa.CheckConstraint("weight BETWEEN 0 AND 1", name="sport_template_priority_weight"), sa.ForeignKeyConstraint(["priority_id"], ["knowledge.sport_template_priorities.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("priority_id", "rank", name="uq_sport_template_priority_rank"), sa.UniqueConstraint("priority_id", "category_code", name="uq_sport_template_priority_category"), schema="knowledge")


def downgrade() -> None:
    for table in ("sport_template_priority_items", "sport_template_priorities", "scenario_overlays", "training_mode_fallbacks", "sport_mode_policies", "category_level_availability", "training_reference_weeks", "training_reference_methods", "training_reference_template_versions", "training_reference_templates"):
        op.drop_table(table, schema="knowledge")
