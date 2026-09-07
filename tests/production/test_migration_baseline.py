from pathlib import Path
import re

from backend.app.core.database import Base
import backend.app.models  # noqa: F401


BASELINE = Path("backend/alembic/versions/20260810_01_clean_postgres_knowledge_baseline.py")
VERSIONS = Path("backend/alembic/versions")


def test_migrations_are_explicit_and_account_for_every_authoritative_table():
    source = BASELINE.read_text()
    assert "metadata.create_all" not in source
    assert "backend.app.models" not in source
    migration_source = "\n".join(path.read_text() for path in sorted(VERSIONS.glob("*.py")))
    for table in Base.metadata.sorted_tables:
        assert re.search(rf"op\.create_table\(\s*(['\"])({re.escape(table.name)})\1", migration_source)


def test_baseline_has_explicit_postgis_and_stream_foreign_keys():
    source = BASELINE.read_text()
    assert "CREATE EXTENSION IF NOT EXISTS postgis" in source
    assert "fk_activities_raw_stream_object" in source
    assert "fk_activities_cleaned_stream_object" in source
    assert "fk_activities_matched_stream_object" in source


def test_p1_migrations_add_activity_region_and_otp_ip_index():
    activity_region = (VERSIONS / "20260823_09_activity_region.py").read_text()
    otp_index = (VERSIONS / "20260823_10_otp_rate_limit_index.py").read_text()
    assert 'sa.Column("region_id"' in activity_region
    assert "fk_activities_region_id_geographic_regions" in activity_region
    assert "ix_identity_otp_challenges_ip_created" in otp_index
