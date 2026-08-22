from pathlib import Path

from backend.app.core.database import Base
import backend.app.models  # noqa: F401


BASELINE = Path("backend/alembic/versions/20260810_01_clean_postgres_knowledge_baseline.py")


def test_baseline_is_frozen_and_accounts_for_every_authoritative_table():
    source = BASELINE.read_text()
    assert "metadata.create_all" not in source
    assert "backend.app.models" not in source
    for table in Base.metadata.sorted_tables:
        assert f"op.create_table('{table.name}'" in source


def test_baseline_has_explicit_postgis_and_stream_foreign_keys():
    source = BASELINE.read_text()
    assert "CREATE EXTENSION IF NOT EXISTS postgis" in source
    assert "fk_activities_raw_stream_object" in source
    assert "fk_activities_cleaned_stream_object" in source
    assert "fk_activities_matched_stream_object" in source
