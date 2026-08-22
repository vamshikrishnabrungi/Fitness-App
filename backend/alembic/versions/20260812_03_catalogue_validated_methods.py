"""allow catalogue-validated generator methods"""
from alembic import op

revision="20260812_03"
down_revision="20260812_02"
branch_labels=None
depends_on=None

def upgrade()->None:
    # Use explicit SQL here. The project's naming convention otherwise applies
    # the ``ck_<table>_`` prefix a second time when referring to an existing
    # constraint created by the baseline migration.
    op.execute("ALTER TABLE knowledge.method_versions DROP CONSTRAINT IF EXISTS ck_method_versions_method_version_status")
    op.execute("ALTER TABLE knowledge.method_versions ADD CONSTRAINT ck_method_versions_method_version_status CHECK (status IN ('draft','catalogue_validated','evidence_verified','released','retired'))")

def downgrade()->None:
    op.execute("UPDATE knowledge.method_versions SET status='draft', generator_eligible=false WHERE status='catalogue_validated'")
    op.execute("ALTER TABLE knowledge.method_versions DROP CONSTRAINT IF EXISTS ck_method_versions_method_version_status")
    op.execute("ALTER TABLE knowledge.method_versions ADD CONSTRAINT ck_method_versions_method_version_status CHECK (status IN ('draft','evidence_verified','released','retired'))")
