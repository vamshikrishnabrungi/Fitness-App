from __future__ import annotations

from backend.exercise_library_audit import (
    CANONICAL_COLLECTION,
    GRAPH_COLLECTION,
    SOURCE_COLLECTIONS,
    SUPPLEMENTAL_COLLECTIONS,
    build_coverage,
    build_inventory,
    find_possible_equivalents,
    graph_audit,
    normalize_name,
    suspicious_instruction_reasons,
)


def _exercise(identifier: str, name: str, **overrides):
    doc = {
        "id": identifier,
        "name": name,
        "exercise_family": "squat",
        "category": "strength",
        "difficulty": "beginner",
        "equipment_required": ["bodyweight"],
        "movement_patterns": ["squat"],
        "training_qualities": ["general_strength"],
        "primary_muscles": ["quadriceps", "glutes"],
        "secondary_muscles": ["trunk"],
        "summary": "Research note.",
        "coaching_cues": ["Research cue."],
        "common_errors": ["Research error."],
        "contraindications": ["Pain during the movement."],
        "progressions": ["Goblet Squat"],
        "regressions": ["Box Squat"],
        "substitutions": ["Goblet Squat"],
        "source_refs": [{"source_book_id": "fixture"}],
        "expert_validation_status": "pending",
    }
    doc.update(overrides)
    return doc


def _collections(*canonical, mobility=None, primary=None, variation=None, graph=None):
    return {
        CANONICAL_COLLECTION: list(canonical),
        SOURCE_COLLECTIONS[0]: list(primary or []),
        SOURCE_COLLECTIONS[1]: list(variation or []),
        SUPPLEMENTAL_COLLECTIONS[0]: list(mobility or []),
        GRAPH_COLLECTION: list(graph or []),
    }


def test_normalize_name_collapses_punctuation_and_case():
    assert normalize_name("  Pull-Up  ") == "pull up"
    assert normalize_name("Strength & Conditioning") == "strength and conditioning"


def test_inventory_reconciles_duplicate_names_and_never_marks_ready():
    preferred = _exercise("gym_raw_pull_up", "Pull-Up", exercise_family="pull_up", movement_patterns=["vertical_pull"])
    duplicate = _exercise(
        "old_pull_up",
        "Pull-up",
        exercise_family="general_strength",
        source_book_id="old_book",
        source_book_ids=["old_book"],
    )
    source = {
        "id": "pex_pull_up",
        "source_exercise_id": "gym_raw_pull_up",
        "name": "Pull-Up",
    }
    inventory, reconciliation = build_inventory(
        _collections(preferred, duplicate, primary=[source]),
        movement_forms={"pull up": "Hang with control, pull the elbows down, and lower smoothly."},
        thumbnail_slugs={"pull-up"},
    )

    assert len(inventory) == 1
    row = inventory[0]
    assert row["source_id"] == "gym_raw_pull_up"
    assert row["migration_eligible"] is False
    assert "expert_approval_pending" in row["migration_blockers"]
    assert len(row["duplicate_records"]) == 1
    assert row["duplicate_records"][0]["disposition"] == "merge_duplicate"
    assert reconciliation["unmatched_source_record_count"] == 0


def test_non_movement_principles_are_rejected():
    principle = {
        "id": "mob_principle",
        "name": "Creating a Mobility Program",
        "category": "mobility_principles",
        "is_movement": False,
        "summary": "Knowledge document.",
        "coaching_cues": ["Not a movement."],
        "source_refs": [{"source_book_id": "fixture"}],
    }
    inventory, reconciliation = build_inventory(_collections(mobility=[principle]))
    assert inventory[0]["record_type"] == "training_principle_non_movement"
    assert inventory[0]["disposition"] == "reject"
    assert reconciliation["non_movement_candidates"] == 1


def test_instruction_mismatch_flags_wrong_press_template():
    record = {"name": "Barbell Overhead Press"}
    reasons = suspicious_instruction_reasons(
        record,
        "Lie on the bench, lower the load to the chest, then press until elbows are straight.",
    )
    assert "movement_form_template_mismatch:lie on the bench" in reasons
    assert "movement_form_template_mismatch:lower the load to the chest" in reasons


def test_probable_equivalents_are_flagged_without_automatic_merge():
    first = _exercise("back_squat", "Back Squat", equipment_required=["barbell", "plates"])
    second = _exercise("barbell_back_squat", "Barbell Back Squat", equipment_required=["barbell", "plates"])
    inventory, reconciliation = build_inventory(_collections(first, second))
    groups = find_possible_equivalents(inventory)
    assert len(inventory) == 2
    assert len(groups) == 1
    assert groups[0]["recommendation"] == "manual_biomechanical_equivalence_review"
    assert reconciliation["possible_equivalent_group_count"] == 1


def test_coverage_reports_speed_and_conditioning_gaps():
    inventory, _ = build_inventory(
        _collections(_exercise("squat", "Bodyweight Squat")),
        movement_forms={"bodyweight squat": "Squat with control."},
    )
    coverage = build_coverage(inventory)
    by_key = {row["capability"]: row for row in coverage["capabilities"]}
    assert by_key["acceleration"]["status"] == "gap"
    assert by_key["max_velocity"]["status"] == "gap"
    assert by_key["aerobic_conditioning"]["kind"] == "protocol"
    assert by_key["aerobic_conditioning"]["status"] == "gap"


def test_graph_audit_accepts_known_name_when_legacy_id_is_unknown_and_detects_cycle():
    edges = [
        {
            "id": "edge_1",
            "from_exercise_id": "legacy_a",
            "from_exercise_name": "Squat A",
            "to_exercise_id": "legacy_b",
            "to_exercise_name": "Squat B",
            "direction": "progression",
        },
        {
            "id": "edge_2",
            "from_exercise_id": "legacy_b",
            "from_exercise_name": "Squat B",
            "to_exercise_id": "legacy_a",
            "to_exercise_name": "Squat A",
            "direction": "progression",
        },
    ]
    result = graph_audit(edges, known_ids=set(), known_names={"squat a", "squat b"})
    assert result["unknown_reference_count"] == 0
    assert result["progression_cycle_count"] == 1
