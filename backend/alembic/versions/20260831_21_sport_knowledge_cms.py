"""Add athlete-facing sport knowledge CMS tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260831_21"
down_revision = "20260827_20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sport_knowledge_sources",
        sa.Column("source_key", sa.String(100), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("publication_year", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.String(50), nullable=False),
        sa.Column("editorial_note", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("publication_year BETWEEN 1900 AND 2200", name="ck_sport_knowledge_sources_sport_knowledge_source_year"),
        sa.PrimaryKeyConstraint("id", name="pk_sport_knowledge_sources"),
        sa.UniqueConstraint("source_key", name="uq_sport_knowledge_source_key"),
        sa.UniqueConstraint("canonical_url", name="uq_sport_knowledge_source_url"),
        schema="knowledge",
    )
    op.create_table(
        "sport_knowledge_articles",
        sa.Column("sport_code", sa.String(40), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("latest_version", sa.Integer(), nullable=False),
        sa.Column("published_version", sa.Integer(), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_sport_knowledge_articles"),
        sa.UniqueConstraint("sport_code", "slug", name="uq_sport_knowledge_article_slug"),
        schema="knowledge",
    )
    op.create_index("ix_knowledge_sport_knowledge_articles_sport_code", "sport_knowledge_articles", ["sport_code"], schema="knowledge")
    op.create_table(
        "sport_knowledge_article_versions",
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_version", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(50), nullable=False),
        sa.Column("audiences", postgresql.ARRAY(sa.String(40)), nullable=False),
        sa.Column("events", postgresql.ARRAY(sa.String(50)), nullable=False),
        sa.Column("sections", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("medical_disclaimer", sa.Text(), nullable=False),
        sa.Column("reviewed_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.CheckConstraint("status IN ('draft','in_review','published','retired')", name="ck_sport_knowledge_article_versions_sport_knowledge_article_version_status"),
        sa.ForeignKeyConstraint(["article_id"], ["knowledge.sport_knowledge_articles.id"], ondelete="CASCADE", name="fk_sport_article_version_article"),
        sa.PrimaryKeyConstraint("article_id", "content_version", name="pk_sport_knowledge_article_versions"),
        schema="knowledge",
    )
    op.create_table(
        "sport_knowledge_article_sources",
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("article_version", sa.Integer(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id", "article_version"], ["knowledge.sport_knowledge_article_versions.article_id", "knowledge.sport_knowledge_article_versions.content_version"], ondelete="CASCADE", name="fk_sport_article_source_version"),
        sa.ForeignKeyConstraint(["source_id"], ["knowledge.sport_knowledge_sources.id"], ondelete="RESTRICT", name="fk_sport_article_source_source"),
        sa.PrimaryKeyConstraint("article_id", "article_version", "source_id", name="pk_sport_knowledge_article_sources"),
        schema="knowledge",
    )
    op.create_table(
        "sport_knowledge_releases",
        sa.Column("sport_code", sa.String(40), nullable=False),
        sa.Column("release_version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("subtitle", sa.Text(), nullable=False),
        sa.Column("medical_disclaimer", sa.Text(), nullable=False),
        sa.Column("article_manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("status IN ('published','retired')", name="ck_sport_knowledge_releases_sport_knowledge_release_status"),
        sa.ForeignKeyConstraint(["published_by"], ["identity.users.id"], ondelete="SET NULL", name="fk_sport_knowledge_releases_published_by_users"),
        sa.PrimaryKeyConstraint("id", name="pk_sport_knowledge_releases"),
        sa.UniqueConstraint("sport_code", "release_version", name="uq_sport_knowledge_release_version"),
        schema="knowledge",
    )
    op.create_index("ix_knowledge_sport_knowledge_releases_sport_code", "sport_knowledge_releases", ["sport_code"], schema="knowledge")


def downgrade() -> None:
    op.drop_index("ix_knowledge_sport_knowledge_releases_sport_code", table_name="sport_knowledge_releases", schema="knowledge")
    op.drop_table("sport_knowledge_releases", schema="knowledge")
    op.drop_table("sport_knowledge_article_sources", schema="knowledge")
    op.drop_table("sport_knowledge_article_versions", schema="knowledge")
    op.drop_index("ix_knowledge_sport_knowledge_articles_sport_code", table_name="sport_knowledge_articles", schema="knowledge")
    op.drop_table("sport_knowledge_articles", schema="knowledge")
    op.drop_table("sport_knowledge_sources", schema="knowledge")
