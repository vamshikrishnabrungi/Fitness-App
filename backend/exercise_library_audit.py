#!/usr/bin/env python3
"""Read-only production-readiness audit for Runlete's exercise knowledge.

The audit deliberately never writes to MongoDB. It reconciles the raw and
app-facing exercise collections, creates one inventory row per normalized
candidate, evaluates provisional utility and safety, measures athletic S&C
coverage, and writes decision artifacts to ``Research materials/audits/exercise library``.

Automated classifications are triage recommendations, not clinical or coaching
approval. No record is migration eligible until original Runlete copy/media and
the required expert reviews are complete.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "Research materials" / "audits" / "exercise library"
ENV_PATH = ROOT / "backend" / ".env"
MOVEMENT_FORMS_PATH = ROOT / "backend" / "EXERCISE_MOVEMENT_FORMS.md"
THUMBNAIL_DIR = ROOT / "frontend" / "assets" / "images" / "exercise-thumbnails"

CANONICAL_COLLECTION = "exercise_library"
SOURCE_COLLECTIONS = ("primary_exercise_library", "exercise_variation_library")
SUPPLEMENTAL_COLLECTIONS = ("mobility_drills",)
GRAPH_COLLECTION = "exercise_progression_graph"
AUDITED_COLLECTIONS = (CANONICAL_COLLECTION, *SOURCE_COLLECTIONS, *SUPPLEMENTAL_COLLECTIONS, GRAPH_COLLECTION)

MINIMAL_EQUIPMENT = {
    "bodyweight", "floor", "mat", "wall", "doorway", "cones", "floor_markings",
    "soft_landing_surface", "resistance_band", "mini_band", "strap_optional",
    "support_optional", "wall_support_optional", "pad_optional", "wall_or_bench",
}
FIELD_EQUIPMENT = MINIMAL_EQUIPMENT | {
    "medicine_ball", "plyo_box", "box", "hurdles_or_barriers", "partner", "sled",
    "open_space", "track", "field",
}
HOME_EQUIPMENT = MINIMAL_EQUIPMENT | {
    "dumbbell", "dumbbells", "kettlebell", "bench", "pull_up_bar", "stability_ball",
    "foam_pad",
}
GYM_ONLY_EQUIPMENT = {
    "barbell", "plates", "squat_rack", "cable_machine", "smith_machine", "machine",
    "leg_press", "hack_squat_machine", "dip_station", "captains_chair", "landmine",
    "trap_bar", "gymnastic_rings", "parallettes", "riser", "blocks",
}

NON_MOVEMENT_CATEGORIES = {"mobility_principles", "principle", "knowledge", "concept"}
SPECIALIST_TERMS = {
    "snatch", "clean", "jerk", "planche", "front lever", "back lever", "human flag",
    "muscle-up", "muscle up", "skin the cat", "german hang", "handstand push-up",
    "ring dip", "ring support", "v-sit", "l-sit", "dragon flag", "one-arm pull-up",
    "one-arm push-up", "archer pull-up", "archer push-up", "clapping push-up",
    "behind the neck", "rack support", "squat jerk",
}
HIGH_IMPACT_TERMS = {
    "depth jump", "drop jump", "hurdle hop", "barrier hop", "multiple box", "bounding",
    "single-leg hop", "single leg hop", "tuck jump", "reactive jump", "jump with",
}
AMBIGUOUS_OR_UNSUITABLE_NAMES = {
    "russian baby maker", "death stretch", "barksi clean", "barksi snatch",
    "munoz formation", "krumrie formation", "quarter-eagle chest pass",
}

CORE_FAMILIES = {
    "squat", "hinge", "deadlift", "romanian deadlift", "lunge", "split squat", "step-up",
    "step up", "bench press", "overhead press", "push-up", "push up", "row", "pull-up",
    "pull up", "chin-up", "chin up", "lat pulldown", "carry", "plank", "side plank",
    "pallof press", "bridge", "hip thrust", "calf raise", "hamstring curl", "sled push",
    "sled pull", "crawl", "shoulder external rotation",
}


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


@dataclass(frozen=True)
class CapabilityRule:
    label: str
    patterns: Tuple[str, ...] = ()
    qualities: Tuple[str, ...] = ()
    name_regex: Optional[re.Pattern[str]] = None
    minimum_candidates: int = 3
    kind: str = "exercise"


CAPABILITY_RULES: Mapping[str, CapabilityRule] = {
    "squat": CapabilityRule("Squat", ("squat",), name_regex=_rx(r"\bsquat\b")),
    "hinge": CapabilityRule("Hinge", ("hinge",), name_regex=_rx(r"deadlift|good morning|hip hinge|kettlebell swing")),
    "lunge": CapabilityRule("Lunge", ("lunge", "split_stance"), name_regex=_rx(r"\blunge\b|split squat")),
    "step_up_unilateral": CapabilityRule("Step-up and unilateral strength", ("step_up", "single_leg"), name_regex=_rx(r"step[- ]?up|single-leg|split squat")),
    "horizontal_push": CapabilityRule("Horizontal push", ("horizontal_push",), name_regex=_rx(r"bench press|push[- ]?up|chest press|floor press")),
    "vertical_push": CapabilityRule("Vertical push", ("vertical_push",), name_regex=_rx(r"overhead press|shoulder press|landmine press|pike push")),
    "horizontal_pull": CapabilityRule("Horizontal pull", ("horizontal_pull",), name_regex=_rx(r"\brow\b|face pull")),
    "vertical_pull": CapabilityRule("Vertical pull", ("vertical_pull",), name_regex=_rx(r"pull[- ]?up|chin[- ]?up|pulldown")),
    "carry": CapabilityRule("Loaded carries", ("carry",), name_regex=_rx(r"\bcarry\b")),
    "crawl": CapabilityRule("Crawling", ("crawl",), name_regex=_rx(r"crawl|crab walk")),
    "anti_extension": CapabilityRule("Anti-extension", ("anti_extension",), name_regex=_rx(r"plank|dead bug|rollout")),
    "anti_rotation": CapabilityRule("Anti-rotation", ("anti_rotation",), name_regex=_rx(r"pallof|drag-through|shoulder tap")),
    "controlled_rotation": CapabilityRule("Controlled rotation", ("rotation_control",), name_regex=_rx(r"wood chop|woodchop|landmine rotation|cable (chop|lift)")),
    "calf_soleus_tibialis": CapabilityRule("Calf, soleus and tibialis capacity", ("calf_raise", "soleus", "ankle_stability"), name_regex=_rx(r"calf raise|soleus|tibialis|short foot")),
    "hamstring": CapabilityRule("Hamstring capacity", ("knee_flexion",), name_regex=_rx(r"hamstring|nordic|leg curl|romanian deadlift|glute-ham")),
    "adductor_groin": CapabilityRule("Adductor and groin capacity", ("adductor",), name_regex=_rx(r"adductor|copenhagen")),
    "hip_capacity": CapabilityRule("Hip capacity and control", ("hip_extension", "hip_abduction"), name_regex=_rx(r"hip thrust|glute bridge|clamshell|hip abduction|hip airplane")),
    "shoulder_scapular": CapabilityRule("Shoulder and scapular capacity", ("scapular_control", "shoulder_external_rotation"), name_regex=_rx(r"external rotation|wall slide|trap raise|face pull|scapular")),
    "jump_landing": CapabilityRule("Jumping and landing", ("landing", "vertical_jump", "box_jump"), qualities=("landing_mechanics",), name_regex=_rx(r"jump|drop and freeze")),
    "hopping_bounding": CapabilityRule("Hopping and bounding", ("bounding", "repeated_jump", "horizontal_elasticity"), name_regex=_rx(r"hop|bound|skipping")),
    "medicine_ball_power": CapabilityRule("Medicine-ball power", ("medicine_ball_throw",), name_regex=_rx(r"medicine ball|chest pass|side throw|overhead throw|slam")),
    "acceleration": CapabilityRule("Acceleration mechanics", ("acceleration_drill",), qualities=("sprint_acceleration",), name_regex=_rx(r"wall acceleration drill|falling start|resisted sprint|sled sprint|three-point start")),
    "max_velocity": CapabilityRule("Maximum-velocity mechanics", ("max_velocity",), qualities=("max_velocity",), name_regex=_rx(r"a-skip|b-skip|wicket run|flying sprint|straight-leg bound")),
    "sprint_preparation": CapabilityRule("Sprint preparation", ("sprint_mechanics",), name_regex=_rx(r"power skipping|marching drill|ankling|pogo|dribble run")),
    "deceleration": CapabilityRule("Deceleration", ("deceleration",), qualities=("deceleration",), name_regex=_rx(r"deceleration|snap-down|stick landing|stop drill")),
    "planned_cod": CapabilityRule("Planned change of direction", ("change_of_direction",), qualities=("change_of_direction",), name_regex=_rx(r"5-10-5|pro agility|t-drill|cutting drill|change-of-direction sprint")),
    "reactive_agility": CapabilityRule("Reactive agility", ("reactive_agility",), qualities=("reactive_agility",), name_regex=_rx(r"mirror drill|reactive shuffle|coach-call|partner reaction")),
    "aerobic_conditioning": CapabilityRule("Aerobic conditioning modalities", ("aerobic_conditioning",), qualities=("aerobic_capacity",), name_regex=_rx(r"tempo run|easy run|bike|rower|continuous circuit"), kind="protocol"),
    "anaerobic_conditioning": CapabilityRule("Anaerobic conditioning modalities", ("anaerobic_conditioning",), qualities=("anaerobic_capacity",), name_regex=_rx(r"shuttle sprint|hill sprint|assault bike|hard interval"), kind="protocol"),
    "repeated_sprint_conditioning": CapabilityRule("Repeated-sprint conditioning", ("repeated_sprint",), qualities=("repeated_sprint_ability",), name_regex=_rx(r"repeated sprint|sprint shuttle"), kind="protocol"),
    "warmup_mobility_activation": CapabilityRule("Warm-up, mobility and activation", ("dynamic_mobility", "activation", "pre_workout"), qualities=("activation",), name_regex=_rx(r"warm-up|leg swing|arm circles|mobility|rockback")),
    "cooldown_recovery": CapabilityRule("Cooldown and recovery", ("post_workout_or_recovery", "recovery"), qualities=("recovery",), name_regex=_rx(r"cool-?down|recovery|static stretch|breathing")),
    "low_impact_return": CapabilityRule("Low-impact and return-to-training options", qualities=("return_to_training",), name_regex=_rx(r"assisted|supported|machine|isometric|bridge|balance")),
}


def normalize_name(value: Any) -> str:
    text = str(value or "").lower().replace("&", " and ")
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def slugify(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def clean_list(value: Any) -> List[str]:
    if value in (None, "", [], {}):
        return []
    items = value if isinstance(value, list) else [value]
    result: List[str] = []
    for item in items:
        if isinstance(item, Mapping):
            continue
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def first_value(doc: Mapping[str, Any], *fields: str) -> Any:
    for field in fields:
        value = doc.get(field)
        if value not in (None, "", [], {}):
            return value
    return None


def json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "__str__") and value.__class__.__name__ == "ObjectId":
        return str(value)
    return value


def read_env_defaults() -> Tuple[str, str]:
    mongo_url = "mongodb://localhost:27017"
    db_name = "test_database"
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            if key == "MONGO_URL":
                mongo_url = value
            elif key == "DB_NAME":
                db_name = value
    return mongo_url, db_name


def parse_movement_forms(path: Path = MOVEMENT_FORMS_PATH) -> Dict[str, str]:
    if not path.exists():
        return {}
    result: Dict[str, str] = {}
    for line in path.read_text(errors="ignore").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0].lower() in {"exercise", "---"} or set(cells[0]) == {"-"}:
            continue
        result[normalize_name(cells[0])] = cells[1]
    return result


def candidate_text(record: Mapping[str, Any]) -> str:
    values: List[str] = [
        str(record.get("name") or ""), str(record.get("family") or ""),
        str(record.get("category") or ""),
    ]
    for field in ("patterns", "qualities", "aliases"):
        values.extend(clean_list(record.get(field)))
    return " ".join(values).lower().replace("_", " ")


def capability_matches(record: Mapping[str, Any], rule: CapabilityRule) -> bool:
    patterns = {normalize_name(item).replace(" ", "_") for item in clean_list(record.get("patterns"))}
    qualities = {normalize_name(item).replace(" ", "_") for item in clean_list(record.get("qualities"))}
    name = str(record.get("name") or "")
    if set(rule.patterns) & patterns or set(rule.qualities) & qualities:
        return True
    return bool(rule.name_regex and rule.name_regex.search(name))


def infer_capabilities(record: Mapping[str, Any]) -> List[str]:
    return [key for key, rule in CAPABILITY_RULES.items() if capability_matches(record, rule)]


def infer_record_type(doc: Mapping[str, Any]) -> str:
    category = normalize_name(first_value(doc, "category", "exercise_type"))
    name = normalize_name(doc.get("name"))
    patterns = " ".join(clean_list(first_value(doc, "movement_patterns", "patterns"))).lower()
    if doc.get("is_movement") is False or category.replace(" ", "_") in NON_MOVEMENT_CATEGORIES:
        return "training_principle_non_movement"
    if re.search(r"\b(test|assessment|screen)\b", name):
        return "assessment"
    if any(token in category for token in ("mobility", "stretch", "warmup", "activation")):
        return "mobility_preparation_drill"
    if re.search(r"sprint|acceleration|deceleration|agility|change.of.direction|max.velocity", f"{name} {patterns}"):
        return "locomotion_speed_drill"
    if category == "conditioning" or re.search(r"interval|conditioning|shuttle", name):
        return "conditioning_modality"
    return "exercise_movement"


def is_specialist(record: Mapping[str, Any]) -> bool:
    text = candidate_text(record)
    source_id = str(record.get("source_id") or "").lower()
    return source_id.startswith("advcal_") or any(term in text for term in SPECIALIST_TERMS)


def infer_risk(record: Mapping[str, Any]) -> Dict[str, str]:
    text = candidate_text(record)
    equipment = {normalize_name(item).replace(" ", "_") for item in clean_list(record.get("equipment"))}
    advanced = normalize_name(record.get("difficulty")) == "advanced"
    specialist = is_specialist(record)
    high_impact = any(term in text for term in HIGH_IMPACT_TERMS) or "depth_jump" in text.replace(" ", "_")
    if specialist or high_impact:
        return {"risk_level": "high", "supervision": "required"}
    if advanced or "barbell" in equipment or "plyo_box" in equipment or "medicine_ball" in equipment:
        return {"risk_level": "moderate", "supervision": "recommended"}
    return {"risk_level": "low", "supervision": "normal"}


def infer_environments(record: Mapping[str, Any]) -> Dict[str, bool]:
    equipment = {normalize_name(item).replace(" ", "_") for item in clean_list(record.get("equipment"))}
    equipment = {item[:-1] if item == "dumbbells" else item for item in equipment}
    home = not bool(equipment & GYM_ONLY_EQUIPMENT) and all(item in HOME_EQUIPMENT or item == "dumbbell" for item in equipment)
    field = not bool(equipment & GYM_ONLY_EQUIPMENT) and all(item in FIELD_EQUIPMENT or item in {"dumbbell", "kettlebell"} for item in equipment)
    return {"home": home, "gym": True, "field": field}


def infer_team_scalability(record: Mapping[str, Any], risk: Mapping[str, str]) -> Dict[str, str]:
    equipment = {normalize_name(item).replace(" ", "_") for item in clean_list(record.get("equipment"))}
    if risk["supervision"] == "required" or equipment & {"machine", "cable_machine", "barbell", "squat_rack", "gymnastic_rings"}:
        return {"team_scalability": "low", "station_capacity": "individual_or_small_station", "setup_time": "high"}
    if equipment & {"dumbbell", "dumbbells", "kettlebell", "medicine_ball", "plyo_box", "sled", "partner"}:
        return {"team_scalability": "medium", "station_capacity": "small_group_station", "setup_time": "moderate"}
    return {"team_scalability": "high", "station_capacity": "large_group", "setup_time": "low"}


def infer_sport_demands(record: Mapping[str, Any], capabilities: Sequence[str]) -> List[str]:
    result: List[str] = []
    cap = set(capabilities)
    if cap & {"squat", "hinge", "lunge", "step_up_unilateral"}:
        result.append("lower_body_force_capacity")
    if cap & {"horizontal_push", "vertical_push", "horizontal_pull", "vertical_pull", "shoulder_scapular"}:
        result.append("upper_body_force_capacity")
    if cap & {"carry", "crawl", "anti_extension", "anti_rotation", "controlled_rotation"}:
        result.append("trunk_force_transfer")
    if cap & {"jump_landing", "hopping_bounding", "medicine_ball_power"}:
        result.append("explosive_power")
    if cap & {"acceleration", "max_velocity", "sprint_preparation"}:
        result.append("linear_speed")
    if cap & {"deceleration", "planned_cod", "reactive_agility"}:
        result.append("multidirectional_speed")
    if cap & {"calf_soleus_tibialis", "hamstring", "adductor_groin", "hip_capacity", "low_impact_return"}:
        result.append("tissue_capacity")
    if cap & {"aerobic_conditioning", "anaerobic_conditioning", "repeated_sprint_conditioning"}:
        result.append("energy_system_development")
    if cap & {"warmup_mobility_activation", "cooldown_recovery"}:
        result.append("preparation_and_recovery")
    return result or ["general_athletic_preparation"]


def suspicious_instruction_reasons(record: Mapping[str, Any], movement_form: str) -> List[str]:
    if not movement_form:
        return ["movement_form_missing"]
    name = normalize_name(record.get("name"))
    form = movement_form.lower()
    reasons: List[str] = []
    checks = [
        (_rx(r"chop|rotation|pallof|adductor squeeze"), ("jump or hop explosively", "pull the elbows back toward the ribs")),
        (_rx(r"row|pull-up|chin-up|pulldown"), ("lie on the bench", "press until elbows are straight")),
        (_rx(r"overhead press|shoulder press|landmine press"), ("lie on the bench", "lower the load to the chest")),
        (_rx(r"throw|toss|pass|slam"), ("pull the elbows back toward the ribs", "land quietly with the foot")),
        (_rx(r"nordic|hamstring curl"), ("bend hips and knees to descend", "drive back to standing")),
    ]
    for name_rule, forbidden in checks:
        if name_rule.search(name):
            for phrase in forbidden:
                if phrase in form:
                    reasons.append(f"movement_form_template_mismatch:{phrase}")
    if len(movement_form) > 900:
        reasons.append("movement_form_excessively_long")
    return reasons


def record_completeness(record: Mapping[str, Any]) -> Dict[str, Any]:
    requirements = {
        "name": bool(record.get("name")),
        "category": bool(record.get("category")),
        "difficulty": bool(record.get("difficulty")),
        "equipment": bool(record.get("equipment")),
        "patterns": bool(record.get("patterns")),
        "qualities": bool(record.get("qualities")),
        "primary_muscles": bool(record.get("primary_muscles")),
        "summary": bool(record.get("summary_present")),
        "coaching_cues": bool(record.get("coaching_cues_present")),
        "common_errors": bool(record.get("common_errors_present")),
        "progression_or_regression": bool(record.get("progressions") or record.get("regressions")),
        "substitutions": bool(record.get("substitutions")),
        "safety": bool(record.get("avoid_when")),
        "source_refs": bool(record.get("source_refs")),
    }
    missing = [field for field, present in requirements.items() if not present]
    return {
        "present": sum(requirements.values()),
        "required": len(requirements),
        "missing": missing,
        "complete": not missing,
    }


def provisional_disposition(record: Mapping[str, Any]) -> Tuple[str, List[str]]:
    name = normalize_name(record.get("name"))
    record_type = record.get("record_type")
    instruction_flags = record.get("instruction_flags") or []
    risk = record.get("risk") or {}
    reasons: List[str] = []
    if record_type == "training_principle_non_movement":
        return "reject", ["knowledge_document_not_an_exercise"]
    if name in AMBIGUOUS_OR_UNSUITABLE_NAMES:
        return "quarantine", ["ambiguous_or_unsuitable_user_facing_name", "manual_specialist_review_required"]
    if instruction_flags and any("template_mismatch" in flag for flag in instruction_flags):
        return "rewrite_required", ["movement_instruction_appears_incorrect", "retain_movement_only_after_original_copy_review"]
    if is_specialist(record):
        return "specialist", ["specialist_skill_or_technical_lift", "mandatory_specialist_review"]
    if risk.get("risk_level") == "high":
        return "specialist", ["high_impact_or_high_supervision_requirement"]
    capabilities = set(record.get("capabilities") or [])
    family = normalize_name(record.get("family"))
    category = normalize_name(record.get("category"))
    difficulty = normalize_name(record.get("difficulty"))
    if difficulty == "advanced" or any(token in category for token in ("plyometric", "hypertrophy", "mobility", "stretch", "skill")):
        return "contextual", ["useful_but_not_a_default_foundational_selection"]
    if family in CORE_FAMILIES or capabilities & {
        "squat", "hinge", "lunge", "horizontal_push", "vertical_push", "horizontal_pull",
        "vertical_pull", "carry", "anti_extension", "anti_rotation", "hamstring", "hip_capacity",
        "shoulder_scapular", "calf_soleus_tibialis",
    }:
        reasons.append("broad_athletic_strength_and_conditioning_utility")
        return "core", reasons
    reasons.append("useful_for_specific_quality_equipment_or_training_context")
    return "contextual", reasons


def canonical_record(doc: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "source_id": str(doc.get("id") or doc.get("_id") or ""),
        "name": str(doc.get("name") or "").strip(),
        "aliases": clean_list(doc.get("aliases")),
        "family": str(first_value(doc, "base_exercise", "exercise_family") or "").strip(),
        "category": str(first_value(doc, "category", "exercise_type") or "").strip(),
        "difficulty": str(first_value(doc, "default_user_level", "difficulty") or "").strip().lower(),
        "technical_complexity": str(doc.get("technical_complexity") or "").strip().lower(),
        "equipment": clean_list(first_value(doc, "equipment", "equipment_required")),
        "patterns": clean_list(first_value(doc, "patterns", "movement_patterns")),
        "qualities": clean_list(first_value(doc, "qualities", "training_qualities")),
        "primary_muscles": clean_list(doc.get("primary_muscles")),
        "secondary_muscles": clean_list(doc.get("secondary_muscles")),
        "progressions": clean_list(doc.get("progressions")),
        "regressions": clean_list(doc.get("regressions")),
        "substitutions": clean_list(doc.get("substitutions")),
        "avoid_when": clean_list(first_value(doc, "avoid_when", "contraindications", "injury_flags")),
        "summary_present": bool(first_value(doc, "summary", "definition")),
        "coaching_cues_present": bool(first_value(doc, "coaching_cues", "instructions")),
        "common_errors_present": bool(first_value(doc, "common_errors", "common_mistakes")),
        "source_refs": json_safe(doc.get("source_refs") or []),
        "expert_validation_status": str(doc.get("expert_validation_status") or "pending"),
        "is_movement": doc.get("is_movement"),
    }


def source_descriptor(collection: str, doc: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "collection": collection,
        "id": str(doc.get("id") or doc.get("_id") or ""),
        "source_exercise_id": str(doc.get("source_exercise_id") or ""),
        "name": str(doc.get("name") or "").strip(),
    }


def equivalence_key(record: Mapping[str, Any]) -> str:
    """Conservative name key for probable-equivalence review, never auto-merge."""
    name = f" {normalize_name(record.get('name'))} "
    replacements = {
        " banded ": " band ",
        " scapula ": " scapular ",
        " bent over ": " bent ",
        " pullup ": " pull up ",
        " pushup ": " push up ",
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    equipment = {normalize_name(item).replace(" ", "_") for item in clean_list(record.get("equipment"))}
    if "barbell" in equipment:
        name = name.replace(" barbell ", " ")
    return " ".join(name.split())


def find_possible_equivalents(inventory: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in inventory:
        if row.get("record_type") == "training_principle_non_movement":
            continue
        groups[equivalence_key(row)].append(row)

    alias_targets: Dict[Tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)
    by_name = {normalize_name(row.get("name")): row for row in inventory}
    for row in inventory:
        for alias in clean_list(row.get("aliases")):
            alias_key = normalize_name(alias)
            if alias_key in by_name and by_name[alias_key].get("audit_key") != row.get("audit_key"):
                pair = tuple(sorted((str(row.get("audit_key")), alias_key)))
                alias_targets[pair].extend([row, by_name[alias_key]])

    results: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, ...]] = set()
    for reason, grouped_rows in [
        ("normalized_mechanical_name_match", rows) for rows in groups.values() if len(rows) > 1
    ] + [
        ("alias_matches_another_canonical_name", rows) for rows in alias_targets.values() if len(rows) > 1
    ]:
        unique = {str(row.get("audit_key")): row for row in grouped_rows}
        keys = tuple(sorted(unique))
        if len(keys) < 2 or keys in seen:
            continue
        seen.add(keys)
        results.append({
            "reason": reason,
            "recommendation": "manual_biomechanical_equivalence_review",
            "records": [
                {
                    "audit_key": row.get("audit_key"),
                    "source_id": row.get("source_id"),
                    "name": row.get("name"),
                    "family": row.get("family"),
                    "equipment": row.get("equipment"),
                }
                for row in unique.values()
            ],
        })
    return sorted(results, key=lambda item: tuple(record["name"] for record in item["records"]))


def choose_preferred_doc(docs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    def score(doc: Mapping[str, Any]) -> Tuple[int, str]:
        source_ids = " ".join(clean_list(doc.get("source_book_ids")) + [str(doc.get("source_book_id") or "")])
        identifier = str(doc.get("id") or "")
        completeness = sum(bool(first_value(doc, field)) for field in (
            "category", "difficulty", "equipment_required", "movement_patterns", "training_qualities",
            "primary_muscles", "summary", "coaching_cues", "common_errors", "substitutions",
        ))
        general_bonus = 20 if "general_gym" in source_ids else 0
        normalized_catalog_bonus = 5 if identifier.startswith("gym_raw_") else 0
        concise_bonus = 3 if max([len(str(x)) for x in clean_list(doc.get("coaching_cues"))] or [0]) < 400 else 0
        return completeness + general_bonus + normalized_catalog_bonus + concise_bonus, identifier
    return max(docs, key=score)


def graph_audit(edges: Sequence[Mapping[str, Any]], known_ids: Set[str], known_names: Set[str]) -> Dict[str, Any]:
    unknown: List[Dict[str, str]] = []
    self_edges: List[str] = []
    progression_adjacency: Dict[str, Set[str]] = defaultdict(set)
    for edge in edges:
        edge_id = str(edge.get("id") or edge.get("_id") or "")
        source_id = str(edge.get("from_exercise_id") or "")
        source_name = str(first_value(edge, "from_exercise_name", "from") or "")
        target_id = str(edge.get("to_exercise_id") or "")
        target_name = str(first_value(edge, "to_exercise_name", "to") or "")
        source = source_id or source_name
        target = target_id or target_name
        source_known = source_id in known_ids or normalize_name(source_name) in known_names or normalize_name(source) in known_names
        target_known = target_id in known_ids or normalize_name(target_name) in known_names or normalize_name(target) in known_names
        if not (source_known and target_known):
            unknown.append({"edge_id": edge_id, "from": source, "to": target})
        if source and source == target:
            self_edges.append(edge_id)
        if str(edge.get("direction") or "progression") == "progression" and source and target:
            progression_adjacency[source].add(target)

    cycles: Set[Tuple[str, ...]] = set()
    active: List[str] = []
    active_set: Set[str] = set()
    visited: Set[str] = set()

    def visit(node: str) -> None:
        if node in active_set:
            start = active.index(node)
            cycle = active[start:] + [node]
            normalized = tuple(sorted(set(cycle)))
            if normalized:
                cycles.add(normalized)
            return
        if node in visited:
            return
        visited.add(node)
        active.append(node)
        active_set.add(node)
        for target in progression_adjacency.get(node, set()):
            visit(target)
        active.pop()
        active_set.remove(node)

    for node in list(progression_adjacency):
        visit(node)
    return {
        "edge_count": len(edges),
        "unknown_reference_count": len(unknown),
        "unknown_references": unknown,
        "self_edge_count": len(self_edges),
        "self_edges": self_edges,
        "progression_cycle_count": len(cycles),
        "progression_cycles": [list(cycle) for cycle in sorted(cycles)],
    }


def build_inventory(
    collections: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    movement_forms: Optional[Mapping[str, str]] = None,
    thumbnail_slugs: Optional[Set[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    movement_forms = movement_forms or {}
    thumbnail_slugs = thumbnail_slugs or set()
    grouped: Dict[str, List[Tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    source_reconciliation: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for collection in (CANONICAL_COLLECTION, *SUPPLEMENTAL_COLLECTIONS):
        for doc in collections.get(collection, []):
            key = normalize_name(doc.get("name"))
            if not key:
                key = f"missing-name:{collection}:{doc.get('id') or doc.get('_id')}"
            grouped[key].append((collection, doc))

    source_by_name: Dict[str, List[Tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    source_by_source_id: Dict[str, List[Tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    for collection in SOURCE_COLLECTIONS:
        for doc in collections.get(collection, []):
            source_by_name[normalize_name(doc.get("name"))].append((collection, doc))
            source_id = str(doc.get("source_exercise_id") or "")
            if source_id:
                source_by_source_id[source_id].append((collection, doc))

    inventory: List[Dict[str, Any]] = []
    represented_source_keys: Set[Tuple[str, str]] = set()
    duplicate_actions: List[Dict[str, Any]] = []

    for key in sorted(grouped):
        candidates = grouped[key]
        canonical_docs = [doc for collection, doc in candidates if collection == CANONICAL_COLLECTION]
        supplemental_docs = [doc for collection, doc in candidates if collection != CANONICAL_COLLECTION]
        preferred = choose_preferred_doc(canonical_docs or supplemental_docs)
        base = canonical_record(preferred)
        sources = [source_descriptor(collection, doc) for collection, doc in candidates]

        source_matches: List[Tuple[str, Mapping[str, Any]]] = list(source_by_name.get(key, []))
        preferred_id = str(preferred.get("id") or "")
        source_matches.extend(source_by_source_id.get(preferred_id, []))
        deduped_matches: Dict[Tuple[str, str], Tuple[str, Mapping[str, Any]]] = {}
        for collection, doc in source_matches:
            source_key = (collection, str(doc.get("id") or doc.get("_id") or ""))
            deduped_matches[source_key] = (collection, doc)
            represented_source_keys.add(source_key)
        for collection, doc in deduped_matches.values():
            descriptor = source_descriptor(collection, doc)
            if descriptor not in sources:
                sources.append(descriptor)

        duplicate_records = []
        for collection, doc in candidates:
            if doc is preferred:
                continue
            duplicate = source_descriptor(collection, doc)
            duplicate["disposition"] = "merge_duplicate"
            duplicate["merge_into_source_id"] = base["source_id"]
            duplicate_records.append(duplicate)
            duplicate_actions.append(duplicate)

        base.update({
            "audit_key": key,
            "canonical_proposed_name": base["name"],
            "source_records": sources,
            "duplicate_records": duplicate_records,
            "record_type": infer_record_type(preferred),
        })
        base["capabilities"] = infer_capabilities(base)
        base["environments"] = infer_environments(base)
        base["risk"] = infer_risk(base)
        base["team"] = infer_team_scalability(base, base["risk"])
        base["sport_demands"] = infer_sport_demands(base, base["capabilities"])
        base["instruction_flags"] = suspicious_instruction_reasons(base, movement_forms.get(key, ""))
        slug = slugify(base["name"])
        base["content_status"] = {
            "existing_prose": "research_notes_only",
            "original_runlete_copy_required": True,
            "movement_form_present": key in movement_forms,
            "movement_form_review_required": True,
        }
        base["media"] = {
            "thumbnail_present": slug in thumbnail_slugs,
            "technical_review": "pending" if slug in thumbnail_slugs else "missing",
            "ownership": "unverified" if slug in thumbnail_slugs else "missing",
            "migration_eligible": False,
        }
        base["completeness"] = record_completeness(base)
        disposition, reasons = provisional_disposition(base)
        base["disposition"] = disposition
        base["disposition_reasons"] = reasons
        base["expert_review"] = {
            "strength_conditioning": "pending",
            "physiotherapy": "required" if base["risk"]["risk_level"] == "high" or base["avoid_when"] else "not_yet_required",
            "specialist": "required" if disposition == "specialist" else "not_required",
            "reviewer_notes": "",
        }
        blockers = ["expert_approval_pending", "original_runlete_copy_required"]
        if not base["media"]["thumbnail_present"]:
            blockers.append("media_missing")
        else:
            blockers.extend(["media_technical_review_pending", "media_ownership_unverified"])
        if not base["completeness"]["complete"]:
            blockers.append("metadata_incomplete")
        if disposition in {"reject", "quarantine", "merge_duplicate", "rewrite_required", "specialist"}:
            blockers.append(f"disposition:{disposition}")
        base["migration_eligible"] = False
        base["migration_blockers"] = list(dict.fromkeys(blockers))
        inventory.append(base)

    unmatched_sources: List[Dict[str, Any]] = []
    for collection in SOURCE_COLLECTIONS:
        for doc in collections.get(collection, []):
            source_key = (collection, str(doc.get("id") or doc.get("_id") or ""))
            if source_key not in represented_source_keys:
                unmatched_sources.append(source_descriptor(collection, doc))

    for collection in AUDITED_COLLECTIONS:
        for doc in collections.get(collection, []):
            source_reconciliation[collection].append(source_descriptor(collection, doc))

    possible_equivalents = find_possible_equivalents(inventory)
    reconciliation = {
        "collection_counts": {collection: len(collections.get(collection, [])) for collection in AUDITED_COLLECTIONS},
        "candidate_rows": len(inventory),
        "movement_candidates": sum(row["record_type"] != "training_principle_non_movement" for row in inventory),
        "non_movement_candidates": sum(row["record_type"] == "training_principle_non_movement" for row in inventory),
        "duplicate_records": duplicate_actions,
        "possible_equivalent_group_count": len(possible_equivalents),
        "possible_equivalent_groups": possible_equivalents,
        "unmatched_source_record_count": len(unmatched_sources),
        "unmatched_source_records": unmatched_sources,
        "source_document_index": source_reconciliation,
    }
    return inventory, reconciliation


def build_coverage(inventory: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for key, rule in CAPABILITY_RULES.items():
        candidates = [row for row in inventory if key in (row.get("capabilities") or []) and row.get("disposition") != "reject"]
        approved = [row for row in candidates if row.get("migration_eligible")]
        beginner = [row for row in candidates if row.get("difficulty") == "beginner" or row.get("regressions")]
        normal = [row for row in candidates if row.get("difficulty") in {"beginner", "intermediate"} and row.get("disposition") in {"core", "contextual"}]
        progressions = [row for row in candidates if row.get("progressions") or row.get("difficulty") == "advanced"]
        minimal = [row for row in candidates if row.get("environments", {}).get("home") or row.get("environments", {}).get("field")]
        substitutions = [row for row in candidates if row.get("substitutions")]
        metadata_complete = [row for row in candidates if row.get("completeness", {}).get("complete")]
        candidate_standard = (
            len(candidates) >= rule.minimum_candidates
            and bool(beginner)
            and len(normal) >= 2
            and bool(progressions)
            and bool(minimal)
            and bool(substitutions)
            and bool(metadata_complete)
        )
        if not candidates or len(candidates) < rule.minimum_candidates:
            status = "gap"
        elif not candidate_standard:
            status = "partial"
        elif not approved:
            status = "candidate_coverage_blocked_pending_review"
        else:
            status = "approved"
        rows.append({
            "capability": key,
            "label": rule.label,
            "kind": rule.kind,
            "status": status,
            "candidate_count": len(candidates),
            "approved_count": len(approved),
            "beginner_or_regression_count": len(beginner),
            "normal_programming_count": len(normal),
            "progression_count": len(progressions),
            "minimal_equipment_count": len(minimal),
            "substitution_count": len(substitutions),
            "complete_metadata_count": len(metadata_complete),
            "examples": [row.get("name") for row in candidates[:8]],
        })
    return {
        "standards": {
            "minimum_candidates": 3,
            "requires_beginner_or_regression": True,
            "requires_two_normal_options": True,
            "requires_progression": True,
            "requires_minimal_equipment": True,
            "requires_substitution": True,
            "requires_complete_metadata": True,
            "approved_requires_expert_and_original_content": True,
        },
        "capabilities": rows,
        "status_counts": dict(Counter(row["status"] for row in rows)),
    }


def summarize_inventory(inventory: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    environments = Counter()
    risk = Counter()
    record_types = Counter()
    dispositions = Counter()
    difficulty = Counter()
    for row in inventory:
        dispositions[str(row.get("disposition"))] += 1
        record_types[str(row.get("record_type"))] += 1
        if row.get("record_type") != "training_principle_non_movement":
            risk[str((row.get("risk") or {}).get("risk_level"))] += 1
            difficulty[str(row.get("difficulty") or "missing")] += 1
            for environment, suitable in (row.get("environments") or {}).items():
                if suitable:
                    environments[environment] += 1
    return {
        "candidate_count": len(inventory),
        "movement_candidate_count": sum(row.get("record_type") != "training_principle_non_movement" for row in inventory),
        "production_ready_count": sum(bool(row.get("migration_eligible")) for row in inventory),
        "dispositions": dict(sorted(dispositions.items())),
        "record_types": dict(sorted(record_types.items())),
        "risk_levels": dict(sorted(risk.items())),
        "difficulty": dict(sorted(difficulty.items())),
        "environment_coverage": dict(sorted(environments.items())),
        "missing_media_count": sum(not (row.get("media") or {}).get("thumbnail_present") for row in inventory),
        "instruction_flag_count": sum(bool(row.get("instruction_flags")) for row in inventory),
        "metadata_incomplete_count": sum(not (row.get("completeness") or {}).get("complete") for row in inventory),
    }


def markdown_coverage(summary: Mapping[str, Any], coverage: Mapping[str, Any], graph: Mapping[str, Any]) -> str:
    lines = [
        "# Runlete Exercise Coverage and Gap Audit",
        "",
        "> Automated triage only. No exercise is production-approved until original content and expert review are complete.",
        "",
        "## Executive result",
        "",
        f"- Normalized audit candidates: **{summary['candidate_count']}**",
        f"- Movement candidates: **{summary['movement_candidate_count']}**",
        f"- Genuinely production-ready today: **{summary['production_ready_count']}**",
        f"- Missing thumbnails: **{summary['missing_media_count']}**",
        f"- Candidates with instruction/form flags: **{summary['instruction_flag_count']}**",
        f"- Candidates missing required metadata: **{summary['metadata_incomplete_count']}**",
        "",
        "The current library is a useful research inventory, but not a migration-ready product catalogue. Existing prose is source-derived research material, all records still need expert approval, and current media lacks recorded ownership/technical approval.",
        "",
        "## Dispositions",
        "",
        "| Disposition | Count | Meaning |",
        "|---|---:|---|",
    ]
    meanings = {
        "core": "Broadly useful candidate to retain and rewrite/review.",
        "contextual": "Useful for a specific training quality, environment or athlete.",
        "specialist": "Advanced skill/high-risk movement requiring specialist approval.",
        "rewrite_required": "Movement appears useful but current instruction/form is suspect.",
        "merge_duplicate": "Duplicate source record; merge into one canonical candidate.",
        "quarantine": "Ambiguous or unsafe until manually resolved.",
        "reject": "Non-movement or outside athletic S&C.",
    }
    for disposition, count in sorted(summary["dispositions"].items()):
        lines.append(f"| `{disposition}` | {count} | {meanings.get(disposition, '')} |")
    lines.extend([
        "",
        "## Athletic capability matrix",
        "",
        "| Capability | Type | Candidates | Beginner/regression | Normal options | Progression | Minimal equipment | Substitutions | Complete metadata | Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in coverage["capabilities"]:
        lines.append(
            f"| {row['label']} | {row['kind']} | {row['candidate_count']} | "
            f"{row['beginner_or_regression_count']} | {row['normal_programming_count']} | "
            f"{row['progression_count']} | {row['minimal_equipment_count']} | "
            f"{row['substitution_count']} | {row['complete_metadata_count']} | `{row['status']}` |"
        )
    lines.extend([
        "",
        "## Confirmed gaps and weak areas",
        "",
    ])
    gaps = [row for row in coverage["capabilities"] if row["status"] in {"gap", "partial"}]
    for row in gaps:
        lines.append(f"- **{row['label']}** — {row['candidate_count']} candidates; `{row['status']}`. Examples: {', '.join(row['examples']) or 'none'}. ")
    lines.extend([
        "",
        "Conditioning prescriptions, work-to-rest structures, team circuits and session progressions should be created as protocol/template records rather than padded into the exercise catalogue.",
        "",
        "## Progression graph",
        "",
        f"- Edges: {graph['edge_count']}",
        f"- Unknown references: {graph['unknown_reference_count']}",
        f"- Self edges: {graph['self_edge_count']}",
        f"- Progression-only cycle groups: {graph['progression_cycle_count']}",
        "",
        "Any reported cycle is a manual-review item; regression edges are excluded from cycle detection because reciprocal regression/progression pairs are intentional.",
        "",
        "## Environment and team readiness",
        "",
        f"- Home-suitable candidates: {summary['environment_coverage'].get('home', 0)}",
        f"- Gym-suitable candidates: {summary['environment_coverage'].get('gym', 0)}",
        f"- Field-suitable candidates: {summary['environment_coverage'].get('field', 0)}",
        "",
        "Environment suitability is equipment-based triage. Space, surface, noise, anchoring, ceiling height and athlete-to-coach ratio still require human review.",
        "",
    ])
    return "\n".join(lines)


def markdown_recommendation(
    summary: Mapping[str, Any],
    inventory: Sequence[Mapping[str, Any]],
    reconciliation: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> str:
    by_disposition: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in inventory:
        by_disposition[str(row.get("disposition"))].append(row)
    lines = [
        "# Runlete Exercise Migration Recommendation",
        "",
        "## Decision",
        "",
        "**Do not migrate the current exercise catalogue into the production generator yet.**",
        "",
        f"The audit found {summary['movement_candidate_count']} movement candidates, but zero are currently migration eligible because expert approval, original Runlete instructions, and owned/approved media are incomplete.",
        "",
        "## Recommended retention queues",
        "",
    ]
    for disposition in ("core", "contextual", "rewrite_required", "specialist", "quarantine", "reject"):
        items = by_disposition.get(disposition, [])
        lines.append(f"### {disposition.replace('_', ' ').title()} ({len(items)})")
        lines.append("")
        for row in items:
            flags = ", ".join(row.get("disposition_reasons") or [])
            lines.append(f"- `{row['source_id']}` — {row['name']} — {flags}")
        lines.append("")
    duplicates = reconciliation.get("duplicate_records") or []
    lines.extend([
        f"## Explicit duplicate merges ({len(duplicates)})",
        "",
    ])
    for item in duplicates:
        lines.append(f"- `{item.get('id')}` {item.get('name')} → `{item.get('merge_into_source_id')}`")
    possible_equivalents = reconciliation.get("possible_equivalent_groups") or []
    lines.extend([
        "",
        f"## Probable biomechanical equivalence reviews ({len(possible_equivalents)})",
        "",
        "These are review candidates only and are not automatically merged because equipment, stance, range or coaching purpose may differ.",
        "",
    ])
    for group in possible_equivalents:
        lines.append("- " + " ↔ ".join(f"`{item['source_id']}` {item['name']}" for item in group["records"]))
    lines.extend([
        "",
        "## Content commissioning priorities",
        "",
        "1. Rewrite and expert-review the core queue first, starting with foundational strength, trunk, lower-leg, hamstring, hip and shoulder capacity.",
        "2. Commission missing acceleration, max-velocity, deceleration, planned change-of-direction and reactive-agility drills.",
        "3. Build aerobic, anaerobic and repeated-sprint protocols outside the exercise table.",
        "4. Validate beginner regressions and equipment substitutions for home, gym and field use.",
        "5. Review specialist Olympic-lifting, high-impact plyometric and advanced-calisthenics modules separately; keep them disabled by default.",
        "6. Replace or technically approve every thumbnail using owned Runlete media.",
        "",
        "## Migration gate",
        "",
        "A record may enter the future production catalogue only when its canonical name/aliases are resolved, original copy is approved, safety and equipment metadata are complete, progression/substitution links resolve, required experts have signed off, and owned media has passed technical review.",
        "",
        "The next decision should choose the size of the first expert-review batch; no database migration is part of this audit.",
        "",
    ])
    return "\n".join(lines)


def write_outputs(
    output_dir: Path,
    *,
    db_name: str,
    inventory: Sequence[Mapping[str, Any]],
    reconciliation: Mapping[str, Any],
    coverage: Mapping[str, Any],
    graph: Mapping[str, Any],
) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_inventory(inventory)
    generated_at = datetime.now().astimezone().isoformat()
    inventory_payload = {
        "audit_version": "1.0.0",
        "generated_at": generated_at,
        "database": db_name,
        "read_only": True,
        "scope": "athletic strength and conditioning for ages 16+, all sports, home/gym/field",
        "summary": summary,
        "reconciliation": reconciliation,
        "graph_audit": graph,
        "records": inventory,
    }
    recommendation_payload = {
        "audit_version": "1.0.0",
        "generated_at": generated_at,
        "production_ready_count": summary["production_ready_count"],
        "decision": "do_not_migrate_current_catalogue_yet",
        "queues": {
            disposition: [row["audit_key"] for row in inventory if row.get("disposition") == disposition]
            for disposition in ("core", "contextual", "specialist", "rewrite_required", "quarantine", "reject")
        },
        "duplicate_merges": reconciliation.get("duplicate_records") or [],
        "possible_equivalent_groups": reconciliation.get("possible_equivalent_groups") or [],
        "coverage_gaps": [row for row in coverage["capabilities"] if row["status"] in {"gap", "partial"}],
    }
    paths = {
        "inventory": output_dir / "exercise_inventory.json",
        "coverage_json": output_dir / "coverage_matrix.json",
        "coverage_report": output_dir / "coverage_and_gaps.md",
        "recommendation_json": output_dir / "migration_recommendation.json",
        "recommendation_report": output_dir / "migration_recommendation.md",
    }
    paths["inventory"].write_text(json.dumps(json_safe(inventory_payload), indent=2, sort_keys=True) + "\n")
    paths["coverage_json"].write_text(json.dumps(json_safe(coverage), indent=2, sort_keys=True) + "\n")
    paths["coverage_report"].write_text(markdown_coverage(summary, coverage, graph) + "\n")
    paths["recommendation_json"].write_text(json.dumps(json_safe(recommendation_payload), indent=2, sort_keys=True) + "\n")
    paths["recommendation_report"].write_text(markdown_recommendation(summary, inventory, reconciliation, coverage) + "\n")
    return paths


def load_collections(db: Any) -> Dict[str, List[Dict[str, Any]]]:
    available = set(db.list_collection_names())
    missing = [name for name in AUDITED_COLLECTIONS if name not in available]
    if missing:
        raise RuntimeError(f"Required audit collections are missing: {', '.join(missing)}")
    projection = {"embedding": 0}
    return {name: list(db[name].find({}, projection)) for name in AUDITED_COLLECTIONS}


def run_audit(
    *, mongo_url: str, db_name: str, output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Any]:
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
    try:
        client.admin.command("ping")
        db = client[db_name]
        collections = load_collections(db)
    finally:
        client.close()

    movement_forms = parse_movement_forms()
    thumbnail_slugs = {path.stem for path in THUMBNAIL_DIR.glob("*.png")} if THUMBNAIL_DIR.exists() else set()
    inventory, reconciliation = build_inventory(
        collections, movement_forms=movement_forms, thumbnail_slugs=thumbnail_slugs,
    )
    known_ids = {
        str(doc.get("id"))
        for collection in (CANONICAL_COLLECTION, *SOURCE_COLLECTIONS, *SUPPLEMENTAL_COLLECTIONS)
        for doc in collections.get(collection, [])
        if doc.get("id")
    }
    known_names = {
        normalize_name(doc.get("name"))
        for collection in (CANONICAL_COLLECTION, *SOURCE_COLLECTIONS, *SUPPLEMENTAL_COLLECTIONS)
        for doc in collections.get(collection, [])
        if doc.get("name")
    }
    graph = graph_audit(collections[GRAPH_COLLECTION], known_ids, known_names)
    coverage = build_coverage(inventory)
    paths = write_outputs(
        output_dir,
        db_name=db_name,
        inventory=inventory,
        reconciliation=reconciliation,
        coverage=coverage,
        graph=graph,
    )
    return {
        "summary": summarize_inventory(inventory),
        "reconciliation": reconciliation,
        "coverage": coverage,
        "graph": graph,
        "paths": {key: str(value) for key, value in paths.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Runlete exercise catalogue production audit.")
    parser.add_argument(
        "--mongo-url",
        default=os.environ.get("EXERCISE_AUDIT_MONGO_URL", "mongodb://localhost:27017"),
        help="MongoDB URL to audit. Defaults to localhost and ignores the app's MONGO_URL for safety.",
    )
    parser.add_argument(
        "--db-name",
        default=os.environ.get("EXERCISE_AUDIT_DB_NAME", "test_database"),
        help="Database to audit. Defaults to test_database intentionally, not backend DB_NAME.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    result = run_audit(mongo_url=args.mongo_url, db_name=args.db_name, output_dir=args.output_dir)
    print(json.dumps({"summary": result["summary"], "paths": result["paths"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
