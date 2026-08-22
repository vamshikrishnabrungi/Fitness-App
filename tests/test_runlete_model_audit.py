from __future__ import annotations

import json
from pathlib import Path

from backend.runlete_model_audit import (
    ALLOWED_DISPOSITIONS,
    DEFAULT_OUTPUT,
    REQUIRED_OUTPUTS,
    _claim_support_class,
    _content_scope,
    _substantive_text,
    normalize_sport,
    validate_outputs,
)


def test_sport_aliases_are_canonical():
    assert normalize_sport("Football") == "soccer"
    assert normalize_sport("soccer_football") == "soccer"
    assert normalize_sport("Running") == "running_endurance"
    assert normalize_sport("Mixed Martial Arts") == "mma"


def test_substantive_text_excludes_source_titles_from_coverage():
    record = {
        "rule": "Use conversational running for aerobic development.",
        "source_refs": [{"title": "Couch to 5K and 100m sprinting", "url": "https://example.test"}],
    }
    text = _substantive_text(record)
    assert "conversational running" in text
    assert "5k" not in text
    assert "100m" not in text


def test_scope_classifier_excludes_tactics_from_physical_generation():
    scope = _content_scope(
        "sport_teaching_progressions",
        "team_tactics",
        "passing formation game iq tactical decision",
    )
    assert scope == "technical_or_tactical"


def test_claim_support_never_implies_approval():
    record = {
        "rule": "Perform 3 sets of 5 repetitions.",
        "source_refs": [{"title": "A review", "url": "https://example.test"}],
    }
    assert _claim_support_class(record, _substantive_text(record)) == "evidence_linked_implication_candidate"


def test_generated_task_one_outputs_reconcile():
    result = validate_outputs(DEFAULT_OUTPUT)
    assert result["status"] == "pass"
    assert not result["missing_outputs"]
    assert result["inventory_count"] == result["manifest_inventory_count"]
    assert result["generator_gate_violations"] == 0
    assert result["migration_gate_violations"] == 0
    assert result["unaccounted_source_parse_errors"] == 0


def test_manifest_and_dispositions_preserve_closed_gates():
    manifest = json.loads((DEFAULT_OUTPUT / "audit_manifest.json").read_text(encoding="utf-8"))
    assert set(REQUIRED_OUTPUTS).issubset({path.name for path in DEFAULT_OUTPUT.iterdir()})
    assert manifest["records_with_disposition"] == manifest["inventory_record_count"]
    assert manifest["generator_eligible_count"] == 0
    assert manifest["migration_eligible_count"] == 0
    assert manifest["workbook"]["snapshot_status"] == "outdated_incomplete_snapshot"

    with (DEFAULT_OUTPUT / "record_dispositions.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            assert row["disposition"] in ALLOWED_DISPOSITIONS
            assert row["generator_eligible"] is False
            assert row["migration_eligible"] is False


def test_hyrox_is_explicitly_hidden_and_running_sprints_are_gaps():
    coverage = json.loads((DEFAULT_OUTPUT / "sport_coverage_matrix.json").read_text(encoding="utf-8"))
    assert coverage["sports"]["hyrox"]["release_status"] == "hidden_no_research_package"
    assert coverage["sports"]["hyrox"]["physical_preparation_record_count"] == 0

    running_report = (DEFAULT_OUTPUT / "running_gap_report.md").read_text(encoding="utf-8")
    for event in ("100m", "200m", "400m", "half_marathon"):
        assert f"| {event} | 0 | 0 | Gap |" in running_report
