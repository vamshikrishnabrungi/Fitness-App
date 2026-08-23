from __future__ import annotations

import csv
import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "Backend data files" / "exercises" / "curated_exercises.csv"
TEMPLATES = ROOT / "Backend data files" / "exercise templates"
MATRIX = ROOT / "Backend data files" / "sport models" / "sport_role_phase_goal_priority_matrix.csv"
TEMPLATE_IMPORT = ROOT / "Backend data files" / "import templates" / "runlete-workout-template-import.csv"


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_normalized_catalogue_contract():
    rows = _rows(CATALOGUE)
    assert len(rows) == 238
    assert len({row["code"] for row in rows}) == 238
    assert sum(row["generator_eligible"] == "yes" for row in rows) == 237
    assert sum(row["generator_eligible"] == "no" for row in rows) == 1
    assert sum(row["approval_status"] == "approved" for row in rows) == 238
    assert sum(row["approval_status"] == "pending_review" for row in rows) == 0
    codes = {row["code"] for row in rows}
    for row in rows:
        assert len([q for q in row["secondary_qualities"].split(";") if q]) <= 3
        for field in ("progressions", "regressions", "substitutions"):
            assert set(filter(None, row[field].split(";"))) <= codes


def test_all_four_week_template_methods_resolve_to_catalogue():
    catalogue = {row["code"]: row for row in _rows(CATALOGUE)}
    schema = json.loads((TEMPLATES / "exercise_template.schema.json").read_text())
    referenced: set[str] = set()
    categories: set[str] = set()
    template_count = 0
    for path in sorted(TEMPLATES.glob("phase_*_exercise_templates.json")):
        payload = json.loads(path.read_text())
        template_count += len(payload["templates"])
        for template in payload["templates"]:
            jsonschema.validate(template, schema)
            categories.add(template["category_code"])
            assert len(template["weeks"]) == 4
            codes = [item["method_code"] for item in template["method_options"]]
            assert len(codes) == len(set(codes))
            referenced.update(codes)
            for item in template["method_options"]:
                assert {"method_code", "block_role", "applicable_modes", "implementation_note"} == set(item)
                assert item["applicable_modes"]
                assert {"beginner": 0, "intermediate": 1, "advanced": 2}[catalogue[item["method_code"]]["minimum_level"]] <= {
                    "beginner": 0, "intermediate": 1, "advanced": 2
                }[template["athlete_level"]]
    assert template_count == 112
    assert len(categories) == 39
    assert referenced <= set(catalogue)
    assert all(catalogue[code]["generator_eligible"] == "yes" for code in referenced)


def test_template_availability_and_modality_policy_are_explicit():
    availability = json.loads((TEMPLATES / "category_level_availability.json").read_text())["records"]
    assert len(availability) == 117
    assert sum(row["available"] for row in availability) == 112
    assert sum(not row["available"] for row in availability) == 5
    available = {(row["category_code"], row["athlete_level"]) for row in availability if row["available"]}
    for row in availability:
        if not row["available"]:
            assert (row["prerequisite_category"], row["athlete_level"]) in available

    policy = json.loads((TEMPLATES / "sport_mode_policy.json").read_text())
    assert len(policy["policies"]) == 11
    assert {row["sport_code"] for row in policy["policies"]} == {
        "running", "football", "cricket", "basketball", "volleyball",
        "badminton", "tennis", "cycling", "swimming", "boxing", "mma",
    }
    for path in sorted(TEMPLATES.glob("phase_*_exercise_templates.json")):
        for template in json.loads(path.read_text())["templates"]:
            if template["selection_policy"]["strategy"] == "single_modality":
                assert template["selection_policy"]["mode_required"] is True
                assert template["selection_policy"]["cross_training_requires_opt_in"] is True
                assert all(item["applicable_modes"] != ["all"] for item in template["method_options"])


def test_template_integrity_report_passes_without_hidden_errors():
    report = json.loads((TEMPLATES / "template_integrity_report.json").read_text())
    assert report["status"] == "passed"
    for field in (
        "level_violations", "ineligible_method_references", "dose_compatibility_violations",
        "modality_violations", "objective_violations", "duplicate_method_lists",
    ):
        assert report["report"][field] == []


def test_workout_template_import_example_is_parseable_and_controlled():
    rows = _rows(TEMPLATE_IMPORT)
    assert rows and {row["template_code"] for row in rows} == {"running_strength_foundation"}
    controlled_qualities = {row["primary_quality"] for row in _rows(CATALOGUE)} | {
        quality for row in _rows(CATALOGUE) for quality in row["secondary_qualities"].split(";") if quality
    }
    for row in rows:
        assert None not in row
        assert row["required_quality"] in controlled_qualities
        assert row["training_role"] in {"preparation", "primary", "accessory", "capacity", "recovery"}
        constraints = json.loads(row["selection_constraints_json"])
        dose = json.loads(row["dose_schema_json"])
        assert isinstance(constraints, dict)
        assert dose
        for specification in dose.values():
            assert specification["minimum"] <= specification["maximum"]


def test_sport_priority_matrix_complete_and_resolved():
    matrix = _rows(MATRIX)
    coverage = json.loads((TEMPLATES / "category_coverage.json").read_text())
    categories = {row["category_code"] for row in coverage["categories"]}
    assert len(matrix) == 864
    assert {row["sport_code"] for row in matrix} == {
        "running", "football", "cricket", "basketball", "volleyball",
        "badminton", "tennis", "cycling", "swimming", "boxing", "mma",
    }
    assert {row["phase_code"] for row in matrix} == {
        "general_preparation", "specific_preparation", "competition", "transition"
    }
    for row in matrix:
        assert row["primary_template_category"] in categories
        assert set(filter(None, row["session_block_order"].split(";"))) <= categories
        for index in range(1, 9):
            category = row[f"rank_{index}_category"]
            weight = row[f"rank_{index}_weight"]
            assert (not category and not weight) or category in categories
            if category:
                assert 0 < float(weight) <= 1
