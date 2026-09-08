"""Prune released training knowledge to the running product.

Revision ID: 20260908_28
Revises: 20260908_27
"""
from alembic import op

revision = "20260908_28"
down_revision = "20260908_27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove explicitly sport-owned content first; dependent rows cascade.
    op.execute("DELETE FROM knowledge.sport_knowledge_releases WHERE sport_code <> 'running'")
    op.execute("DELETE FROM knowledge.sport_knowledge_articles WHERE sport_code <> 'running'")
    op.execute("DELETE FROM knowledge.sport_knowledge_sources s WHERE NOT EXISTS (SELECT 1 FROM knowledge.sport_knowledge_article_sources x WHERE x.source_id=s.id)")
    op.execute("DELETE FROM knowledge.sport_template_priorities WHERE sport_code <> 'running'")
    op.execute("DELETE FROM knowledge.sport_mode_policies WHERE sport_code <> 'running'")
    op.execute("DELETE FROM knowledge.sport_quality_priorities WHERE sport_code <> 'running'")
    op.execute("DELETE FROM knowledge.demand_facts d WHERE NOT EXISTS (SELECT 1 FROM knowledge.demand_fact_versions v WHERE v.demand_fact_id=d.id AND v.sport_code='running')")
    op.execute("DELETE FROM knowledge.program_archetypes WHERE sport_code <> 'running'")
    op.execute("DELETE FROM knowledge.week_templates WHERE sport_code <> 'running'")
    op.execute("DELETE FROM knowledge.sport_taxa WHERE sport_code <> 'running'")

    # Keep only reference categories selected by a running priority.
    op.execute("""
      DELETE FROM knowledge.training_reference_templates t
      WHERE NOT EXISTS (
        SELECT 1 FROM knowledge.training_reference_template_versions v
        WHERE v.template_id=t.id AND v.content_version=t.latest_version
          AND v.category_code IN (
            SELECT primary_template_category FROM knowledge.sport_template_priorities WHERE sport_code='running'
            UNION
            SELECT i.category_code FROM knowledge.sport_template_priority_items i
            JOIN knowledge.sport_template_priorities p ON p.id=i.priority_id
            WHERE p.sport_code='running'
          )
      )
    """)
    op.execute("UPDATE knowledge.training_reference_methods SET sport_codes=ARRAY['running']::varchar[] WHERE 'running'=ANY(sport_codes)")
    op.execute("UPDATE knowledge.training_reference_methods SET sport_codes=ARRAY[]::varchar[] WHERE NOT ('running'=ANY(sport_codes))")

    # Remove catalog exercises that neither appear in a retained reference
    # template nor develop a physical quality selected by running priorities.
    op.execute("""
      DELETE FROM knowledge.methods m
      WHERE NOT EXISTS (SELECT 1 FROM knowledge.training_reference_methods r WHERE r.method_id=m.id)
        AND NOT EXISTS (
          SELECT 1 FROM knowledge.method_effects e WHERE e.method_id=m.id
            AND e.quality_code IN (
              SELECT primary_template_category FROM knowledge.sport_template_priorities WHERE sport_code='running'
              UNION
              SELECT i.category_code FROM knowledge.sport_template_priority_items i
              JOIN knowledge.sport_template_priorities p ON p.id=i.priority_id
              WHERE p.sport_code='running'
            )
        )
    """)
    op.execute("DELETE FROM knowledge.content_reviews")


def downgrade() -> None:
    # Curated source imports remain as provenance, but deleted released content
    # must be restored by re-importing and publishing its original packages.
    pass
