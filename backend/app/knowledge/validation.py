from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Iterable

from backend.app.training.rules import RuleEvaluationError, validate_rule_definition

from .models import (
    MethodConstraint,
    MethodEffect,
    MethodRelation,
    MethodVersion,
    PrescriptionRuleVersion,
    RecipeBlock,
    RecipeSlot,
    RecipeVersion,
)


class KnowledgeValidationError(ValueError):
    pass


ALLOWED_TRAINING_ROLES = {"preparation", "primary", "accessory", "capacity", "recovery"}
ALLOWED_LEVELS = {"beginner", "recreational", "intermediate", "club", "regional", "advanced", "national", "international"}
ALLOWED_RELATION_TYPES = {"progression", "substitution", "alternative"}
ALLOWED_LOAD_CLASSES = {"easy", "moderate", "hard", "recovery"}
ALLOWED_RECIPE_TYPES = {
    "preparation", "strength", "power", "speed", "conditioning", "endurance",
    "interval", "tissue_capacity", "mixed", "recovery",
}
ALLOWED_RECIPE_BLOCK_TYPES = {"warm_up", "primary", "accessory", "conditioning", "cooldown"}
ALLOWED_DOSE_UNITS = {
    "sets", "repetitions", "load_kg", "percentage_1rm", "effort_rpe", "rir",
    "tempo_seconds", "recovery_seconds", "duration_seconds", "duration_minutes",
    "distance_m", "distance_km", "contacts", "height_cm", "intensity_percent",
    "approach_intensity_percent", "cut_angle_degrees", "bout_duration_seconds",
    "stimulus_type", "choice_count", "range_of_motion", "intensity_system", "pace",
    "heart_rate_zone", "power_watts", "set_recovery_seconds", "joint_position",
    "pool_length_m", "stroke_code", "send_off_seconds", "sled_load",
    "velocity_decrement_percent", "build_distance_m", "fly_distance_m", "wicket_spacing_m",
}
ALLOWED_SELECTION_CONSTRAINTS = {
    "movement_patterns", "method_types", "environments", "equipment", "surfaces",
    "minimum_level", "maximum_technical_cost", "maximum_impact_cost",
    "maximum_fatigue_cost", "supervision_allowed", "applicable_modes",
}


def validate_method(
    method: MethodVersion,
    effects: Iterable[MethodEffect],
    constraints: Iterable[MethodConstraint] = (),
) -> None:
    rows = list(effects)
    primary = [item for item in rows if item.is_primary]
    secondary = [item for item in rows if not item.is_primary]
    if len(primary) != 1:
        raise KnowledgeValidationError("a method version must have exactly one primary effect")
    if len(secondary) > 3:
        raise KnowledgeValidationError("a method version may have at most three secondary effects")
    if any(item.training_role not in ALLOWED_TRAINING_ROLES for item in rows):
        raise KnowledgeValidationError("a method effect uses an unsupported training role")
    if any(item.evidence_claim_id is None for item in rows):
        raise KnowledgeValidationError("every method effect requires evidence provenance")
    if method.level_minimum not in ALLOWED_LEVELS:
        raise KnowledgeValidationError("method level is not part of the controlled taxonomy")
    if not method.instructions or not method.cues or not method.common_errors or not method.safety_boundaries:
        raise KnowledgeValidationError("method is missing original athlete-facing instructions or safety content")
    if not method.wording_original:
        raise KnowledgeValidationError("method wording has not been confirmed as original Runlete content")
    if not method.accepted_dose_units:
        raise KnowledgeValidationError("method has no accepted dose units")
    if len(set(method.accepted_dose_units)) != len(method.accepted_dose_units):
        raise KnowledgeValidationError("method dose units must be unique")
    if method.generator_eligible and method.status not in {"catalogue_validated", "evidence_verified", "released"}:
        raise KnowledgeValidationError("only catalogue-validated or reviewed method versions may become generator eligible")
    for row in constraints:
        if row.action not in {"exclude", "modify", "stop", "refer", "require_supervision"}:
            raise KnowledgeValidationError(f"unsupported method constraint action: {row.action}")


def validate_progression_dag(relations: Iterable[MethodRelation]) -> None:
    rows = list(relations)
    if any(row.relation_type not in ALLOWED_RELATION_TYPES for row in rows):
        raise KnowledgeValidationError("method relation type is not supported")
    edges = [(row.from_method_id, row.to_method_id) for row in rows if row.relation_type == "progression"]
    adjacency: dict = defaultdict(list)
    indegree: Counter = Counter()
    nodes = set()
    for source, target in edges:
        if source == target:
            raise KnowledgeValidationError("a progression cannot point to itself")
        adjacency[source].append(target)
        indegree[target] += 1
        nodes.update((source, target))
    queue = deque(node for node in nodes if indegree[node] == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in adjacency[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(nodes):
        raise KnowledgeValidationError("progression graph contains a cycle")


def _validate_bound(name: str, value: object) -> None:
    if isinstance(value, list):
        if not value:
            raise KnowledgeValidationError(f"{name} allowed-values list cannot be empty")
        return
    if not isinstance(value, dict):
        raise KnowledgeValidationError(f"{name} dose specification must be bounded")
    minimum = value.get("minimum", value.get("min"))
    maximum = value.get("maximum", value.get("max"))
    allowed = value.get("allowed_values")
    if allowed is not None:
        if not isinstance(allowed, list) or not allowed:
            raise KnowledgeValidationError(f"{name} allowed_values must be a non-empty list")
        return
    if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
        raise KnowledgeValidationError(f"{name} requires numeric minimum and maximum bounds")
    if minimum > maximum:
        raise KnowledgeValidationError(f"{name} minimum exceeds maximum")
    step = value.get("step")
    if step is not None and (not isinstance(step, (int, float)) or step <= 0):
        raise KnowledgeValidationError(f"{name} step must be positive")


def validate_recipe(
    recipe: RecipeVersion,
    blocks: Iterable[RecipeBlock],
    slots_by_block: dict,
) -> None:
    rows = sorted(blocks, key=lambda row: row.sequence)
    if recipe.load_class not in ALLOWED_LOAD_CLASSES:
        raise KnowledgeValidationError("recipe uses an unsupported load class")
    if recipe.recipe_type not in ALLOWED_RECIPE_TYPES:
        raise KnowledgeValidationError("recipe uses an unsupported type")
    if not recipe.purpose.strip():
        raise KnowledgeValidationError("recipe purpose is required")
    if not rows:
        raise KnowledgeValidationError("recipe contains no blocks")
    if [row.sequence for row in rows] != list(range(1, len(rows) + 1)):
        raise KnowledgeValidationError("recipe block sequence must be contiguous and start at one")
    seen_slot_codes: set[str] = set()
    for block in rows:
        if block.block_type not in ALLOWED_RECIPE_BLOCK_TYPES:
            raise KnowledgeValidationError(f"unsupported recipe block type: {block.block_type}")
        if block.duration_minimum <= 0 or block.duration_minimum > block.duration_maximum:
            raise KnowledgeValidationError("recipe block duration bounds are invalid")
        slots: list[RecipeSlot] = sorted(slots_by_block.get(block.id, []), key=lambda row: row.sequence)
        if not slots:
            raise KnowledgeValidationError("every recipe block requires at least one slot")
        if [row.sequence for row in slots] != list(range(1, len(slots) + 1)):
            raise KnowledgeValidationError("recipe slot sequence must be contiguous and start at one")
        for slot in slots:
            if slot.slot_code in seen_slot_codes:
                raise KnowledgeValidationError(f"duplicate recipe slot code: {slot.slot_code}")
            seen_slot_codes.add(slot.slot_code)
            if slot.training_role not in ALLOWED_TRAINING_ROLES:
                raise KnowledgeValidationError("recipe slot uses an unsupported training role")
            unknown_constraints = set(slot.selection_constraints_json) - ALLOWED_SELECTION_CONSTRAINTS
            if unknown_constraints:
                raise KnowledgeValidationError(f"recipe slot uses unsupported selection constraints: {sorted(unknown_constraints)}")
            minimum_level = slot.selection_constraints_json.get("minimum_level")
            if minimum_level is not None and minimum_level not in ALLOWED_LEVELS:
                raise KnowledgeValidationError("recipe slot minimum level is not controlled")
            for key in ("maximum_technical_cost", "maximum_impact_cost", "maximum_fatigue_cost"):
                value = slot.selection_constraints_json.get(key)
                if value is not None and (not isinstance(value, int) or not 1 <= value <= 5):
                    raise KnowledgeValidationError(f"{key} must be an integer from one to five")
            if not slot.dose_schema_json:
                raise KnowledgeValidationError("recipe slot has no bounded dose schema")
            for unit, specification in slot.dose_schema_json.items():
                if unit not in ALLOWED_DOSE_UNITS:
                    raise KnowledgeValidationError(f"recipe slot uses unsupported dose unit: {unit}")
                _validate_bound(unit, specification)


def validate_prescription_rule(rule: PrescriptionRuleVersion) -> None:
    try:
        validate_rule_definition(rule.conditions_json, rule.actions_json)
    except RuleEvaluationError as exc:
        raise KnowledgeValidationError(str(exc)) from exc
    if not rule.explanation.strip():
        raise KnowledgeValidationError("prescription rule requires an explanation")
