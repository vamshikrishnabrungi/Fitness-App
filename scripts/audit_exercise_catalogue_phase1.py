from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Backend data files" / "exercises" / "curated_exercises.csv"
OUTPUT = ROOT / "Research materials" / "audits" / "catalogue" / "phase1_exercise_catalogue_audit.csv"
RELATIONS = ROOT / "Research materials" / "audits" / "catalogue" / "phase1_unresolved_relations.csv"
COVERAGE = ROOT / "Research materials" / "audits" / "catalogue" / "phase1_method_coverage.csv"

CONTROLLED_QUALITIES = (
    "maximum_strength", "explosive_strength", "isometric_force_capacity", "eccentric_capacity",
    "local_muscular_endurance", "acceleration", "maximum_velocity", "speed_endurance",
    "deceleration", "change_of_direction", "reactive_agility", "landing_capacity",
    "vertical_power", "horizontal_power", "lateral_power", "rotational_power",
    "upper_body_power", "reactive_elastic_strength", "aerobic_capacity", "threshold_capacity",
    "high_intensity_aerobic_power", "anaerobic_power", "anaerobic_capacity",
    "repeated_sprint_ability", "repeated_high_intensity_ability", "calf_soleus_capacity",
    "hamstring_capacity", "adductor_capacity", "shoulder_capacity", "trunk_force_transfer",
    "mobility_preparation", "recovery_capacity",
)

QUALITY_MAP = {
    "max_strength": "maximum_strength", "strength": "maximum_strength", "general_strength": "maximum_strength",
    "lower_body_strength": "maximum_strength", "upper_body_strength": "maximum_strength",
    "upper_body_pulling_strength": "maximum_strength", "upper_back_strength": "maximum_strength",
    "unilateral_strength": "maximum_strength", "unilateral_posterior_chain_strength": "maximum_strength",
    "posterior_chain_strength": "hamstring_capacity", "unilateral_hip_extension_strength": "hamstring_capacity",
    "hip_extension_strength_endurance": "hamstring_capacity", "power": "explosive_strength",
    "whole_body_power": "explosive_strength", "explosive_power": "explosive_strength",
    "rate_of_force_development": "explosive_strength", "speed_power": "explosive_strength",
    "pulling_power": "upper_body_power", "jump_power": "vertical_power",
    "plyometric_power": "reactive_elastic_strength", "reactive_strength": "reactive_elastic_strength",
    "elastic_strength": "reactive_elastic_strength", "elastic_endurance": "reactive_elastic_strength",
    "stretch_shortening_cycle": "reactive_elastic_strength", "conditioning": "local_muscular_endurance",
    "muscular_endurance": "local_muscular_endurance", "hypertrophy": "maximum_strength",
    "quadriceps_strength_endurance": "local_muscular_endurance", "grip_capacity": "local_muscular_endurance",
    "grip_endurance": "local_muscular_endurance", "grip_strength": "maximum_strength",
    "adductor_strength": "adductor_capacity", "adductor_strength_endurance": "adductor_capacity",
    "groin_tissue_capacity": "adductor_capacity", "unilateral_calf_strength": "calf_soleus_capacity",
    "anterior_lower_leg_strength": "calf_soleus_capacity", "foot_intrinsic_strength": "calf_soleus_capacity",
    "shoulder_loading_tolerance": "shoulder_capacity", "shoulder_stability": "shoulder_capacity",
    "scapular_stability": "shoulder_capacity", "scapular_control": "shoulder_capacity",
    "scapular_upward_rotation_control": "shoulder_capacity", "serratus_strength": "shoulder_capacity",
    "lower_trapezius_and_scapular_strength_endurance": "shoulder_capacity",
    "upper_back_strength_endurance": "shoulder_capacity", "overhead_tolerance": "shoulder_capacity",
    "trunk_stiffness": "trunk_force_transfer", "trunk_control": "trunk_force_transfer",
    "trunk_and_hip_control": "trunk_force_transfer", "trunk_and_pelvic_control": "trunk_force_transfer",
    "trunk_and_shoulder_control": "trunk_force_transfer", "trunk_strength_endurance": "trunk_force_transfer",
    "lower_to_upper_force_transfer": "trunk_force_transfer", "lateral_force_transfer": "trunk_force_transfer",
    "hip_control": "trunk_force_transfer", "hip_and_pelvic_control": "trunk_force_transfer",
    "pelvic_control": "trunk_force_transfer", "isometric_control": "isometric_force_capacity",
    "eccentric_control": "eccentric_capacity", "landing_control": "landing_capacity",
    "single_leg_landing_control": "landing_capacity", "movement_preparation": "mobility_preparation",
    "whole_body_movement_preparation": "mobility_preparation", "warm_up": "mobility_preparation",
    "mobility": "mobility_preparation", "range_of_motion": "mobility_preparation",
    "active_control": "mobility_preparation", "balance": "mobility_preparation",
    "balance_support": "mobility_preparation", "coordination": "mobility_preparation",
    "motor_control": "mobility_preparation", "movement_awareness": "mobility_preparation",
    "movement_quality": "mobility_preparation", "joint_stability": "maximum_strength",
    "single_leg_control": "maximum_strength", "lateral_control": "mobility_preparation",
    "knee_control": "mobility_preparation", "knee_extension_control": "mobility_preparation",
    "hip_and_knee_control": "mobility_preparation", "knee_and_hip_control": "mobility_preparation",
    "foot_and_knee_control": "mobility_preparation", "ankle_control": "mobility_preparation",
    "ankle_stability": "mobility_preparation", "proprioception": "mobility_preparation",
    "ankle_mobility": "mobility_preparation", "calf_range_of_motion": "mobility_preparation",
    "dynamic_hamstring_mobility": "mobility_preparation", "dynamic_hip_mobility": "mobility_preparation",
    "dynamic_shoulder_mobility": "mobility_preparation", "hamstring_range_of_motion": "mobility_preparation",
    "hip_flexor_and_quadriceps_mobility": "mobility_preparation", "hip_flexor_range_of_motion": "mobility_preparation",
    "hip_mobility": "mobility_preparation", "pectoral_and_anterior_shoulder_range_of_motion": "mobility_preparation",
    "posterior_hip_range_of_motion": "mobility_preparation", "posterior_shoulder_range_of_motion": "mobility_preparation",
    "quadriceps_range_of_motion": "mobility_preparation", "shoulder_and_lat_range_of_motion": "mobility_preparation",
    "shoulder_mobility": "mobility_preparation", "soleus_and_ankle_range_of_motion": "mobility_preparation",
    "spine_mobility": "mobility_preparation", "thoracic_mobility": "mobility_preparation",
    "wrist_mobility": "mobility_preparation", "breathing": "recovery_capacity",
    "return_to_training": "recovery_capacity", "progressive_loading_tolerance": "recovery_capacity",
    "tissue_capacity": "local_muscular_endurance", "overhead_throwing": "upper_body_power",
    "pull_up_skill": "maximum_strength",
}

MOBILITY_CODES = {
    "adductor_mobility", "ankle_mobility", "calf_range_of_motion", "dynamic_hamstring_mobility",
    "dynamic_hip_mobility", "dynamic_shoulder_mobility", "hamstring_range_of_motion",
    "hip_flexor_and_quadriceps_mobility", "hip_flexor_range_of_motion", "hip_mobility",
    "pectoral_and_anterior_shoulder_range_of_motion", "posterior_hip_range_of_motion",
    "posterior_shoulder_range_of_motion", "quadriceps_range_of_motion", "shoulder_and_lat_range_of_motion",
    "shoulder_mobility", "soleus_and_ankle_range_of_motion", "spine_mobility", "thoracic_mobility",
    "wrist_mobility", "whole_body_movement_preparation", "movement_preparation", "balance",
}

TYPE_OVERRIDES = {
    "Bodyweight Squat": "exercise", "Walking Lunge": "exercise", "Cable Wood Chop": "exercise",
    "Half-Kneeling Cable Chop": "exercise", "Bear Hug Carry": "exercise", "Kettlebell Swing": "exercise",
    "Push Press": "exercise", "Chest Pass": "exercise", "Side Throw": "exercise",
    "Overhead Throw": "exercise", "Underhand Throw": "exercise", "Medicine Ball Slam": "exercise",
    "Sled Push": "exercise", "Backward Sled Drag": "exercise", "Forward Sled Drag": "exercise",
    "Bear Crawl": "exercise", "Lateral Bear Crawl": "exercise", "Crab Walk": "exercise",
}

PRIMARY_OVERRIDES = {
    "Bodyweight Squat": "maximum_strength", "Goblet Squat": "maximum_strength",
    "Box Squat": "maximum_strength", "Landmine Squat": "maximum_strength",
    "Kettlebell Deadlift": "maximum_strength", "Walking Lunge": "maximum_strength",
    "Dumbbell Hip Thrust": "maximum_strength", "Glute Bridge": "hamstring_capacity",
    "Nordic Hamstring Curl": "hamstring_capacity", "Assisted Nordic Hamstring Curl": "hamstring_capacity",
    "Slider Hamstring Curl": "hamstring_capacity", "Standing Calf Raise": "calf_soleus_capacity",
    "Seated Calf Raise": "calf_soleus_capacity", "Tibialis Raise": "calf_soleus_capacity",
    "Face Pull": "shoulder_capacity", "Band Pull-Apart": "shoulder_capacity",
    "Push-Up Plus (full push-up)": "shoulder_capacity", "Scapular Pull-Up": "shoulder_capacity",
    "Band External Rotation at Side": "shoulder_capacity", "Side-Lying Dumbbell External Rotation": "shoulder_capacity",
    "Prone Y-T-W Raise": "shoulder_capacity", "Cable Wood Chop": "trunk_force_transfer",
    "Half-Kneeling Cable Chop": "trunk_force_transfer", "Cable Lift": "trunk_force_transfer",
    "Half-Kneeling Cable Lift": "trunk_force_transfer", "Landmine Rotation": "trunk_force_transfer",
    "Farmer's Carry": "local_muscular_endurance", "Overhead Carry": "shoulder_capacity",
    "Adductor Squeeze": "adductor_capacity", "Short-Lever Copenhagen Plank": "adductor_capacity",
    "Copenhagen Plank": "adductor_capacity", "Short-Lever Copenhagen Adduction": "adductor_capacity",
    "Copenhagen Adduction": "adductor_capacity", "Spanish Squat Hold": "isometric_force_capacity",
    "Four-Direction Cervical Isometrics": "isometric_force_capacity", "Controlled Hang": "shoulder_capacity",
    "Kettlebell Swing": "explosive_strength", "Push Press": "upper_body_power",
    "Squat Jump": "vertical_power", "Standing Jump-and-reach": "vertical_power",
    "Standing Long Jump": "horizontal_power", "Two-foot Ankle Hops": "reactive_elastic_strength",
    "Side-to-side Ankle Hop": "reactive_elastic_strength", "Single-foot Side-to-side Ankle Hop": "reactive_elastic_strength",
    "Front Cone Hop": "reactive_elastic_strength", "Lateral Cone Hop": "reactive_elastic_strength",
    "Diagonal Cone Hop": "reactive_elastic_strength", "Hurdle (barrier) Hop": "reactive_elastic_strength",
    "Zigzag Pogo Hop": "reactive_elastic_strength", "Power Skipping": "reactive_elastic_strength",
    "Alternate Bounding with Single-arm Action": "horizontal_power", "Chest Pass": "upper_body_power",
    "Side Throw": "rotational_power", "Overhead Throw": "upper_body_power",
    "Underhand Throw": "upper_body_power", "Medicine Ball Slam": "upper_body_power",
    "Short Foot": "calf_soleus_capacity", "Sled Push": "explosive_strength",
    "Backward Sled Drag": "local_muscular_endurance", "Forward Sled Drag": "local_muscular_endurance",
    "Bear Crawl": "trunk_force_transfer", "Lateral Bear Crawl": "trunk_force_transfer",
    "Crab Walk": "shoulder_capacity",
}

CORE_PATTERNS = {
    "squat", "hinge", "split_squat", "lunge", "horizontal_push", "vertical_push", "horizontal_pull",
    "vertical_pull", "single_leg_hinge", "step_up", "hip_extension", "knee_flexion", "knee_extension",
    "calf_raise", "single_leg_plantar_flexion", "ankle_dorsiflexion", "anti_extension", "anti_rotation",
    "anti_lateral_flexion", "adductor", "shoulder_external_rotation", "scapular_control",
}


def split(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*;\s*", value or "") if part.strip()]


def normalize_quality(code: str) -> str:
    if code in CONTROLLED_QUALITIES:
        return code
    if code in MOBILITY_CODES:
        return "mobility_preparation"
    return QUALITY_MAP.get(code, "mobility_preparation")


def proposed_type(row: dict[str, str]) -> str:
    if row["exercise_name"] in TYPE_OVERRIDES:
        return TYPE_OVERRIDES[row["exercise_name"]]
    if row["type"] == "strength":
        return "exercise"
    return row["type"]


def proposed_role(row: dict[str, str], quality: str) -> str:
    if row["catalogue_scope"] == "specialist_only":
        return "primary"
    if proposed_type(row) in {"mobility"}:
        return "preparation"
    if quality in {"calf_soleus_capacity", "hamstring_capacity", "adductor_capacity", "shoulder_capacity", "local_muscular_endurance", "trunk_force_transfer", "isometric_force_capacity"}:
        return "capacity"
    return "primary" if row["movement_pattern"] in CORE_PATTERNS or proposed_type(row) == "plyometric" else "accessory"


def expected_units(method_type: str, name: str) -> list[str]:
    if method_type == "isometric":
        return ["sets", "duration_seconds", "effort_rpe", "recovery_seconds"]
    if method_type == "plyometric":
        return ["sets", "repetitions", "contacts", "distance_m", "effort_rpe", "recovery_seconds"]
    if method_type in {"speed_drill", "deceleration_drill", "change_of_direction_drill", "reactive_agility_drill"}:
        return ["sets", "repetitions", "distance_m", "effort_rpe", "recovery_seconds", "set_recovery_seconds"]
    if method_type == "conditioning_modality":
        return ["sets", "repetitions", "duration_seconds", "duration_minutes", "distance_m", "distance_km", "pace", "heart_rate_zone", "effort_rpe", "recovery_seconds", "recovery_minutes", "set_recovery_seconds"]
    if method_type == "mobility":
        return ["sets", "repetitions", "duration_seconds"]
    units = ["sets", "repetitions", "effort_rpe", "rir", "recovery_seconds"]
    if any(token in name.lower() for token in ("carry", "crawl", "sled")):
        units.append("distance_m")
    else:
        units.extend(["load_kg", "percentage_1rm"])
    return units


def relation_kind(value: str, names: set[str]) -> tuple[str, str]:
    key = value.casefold()
    if key in names:
        return "catalogue_link", names_by_key[key]
    if re.search(r"\b(heavier|lighter|longer|shorter|tempo|pause|paused|reduced range|higher rep|thinner band|stronger band|front-foot elevation|low-handle)\b", key):
        return "prescription_variation", ""
    return "unresolved_method_name", ""


with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))

names_by_key = {row["exercise_name"].casefold(): row["exercise_name"] for row in rows}
names = set(names_by_key)
relation_rows: list[dict[str, str]] = []
audit_rows: list[dict[str, str]] = []
coverage: dict[tuple[str, str], Counter] = defaultdict(Counter)

for row in rows:
    method_type = proposed_type(row)
    primary = PRIMARY_OVERRIDES.get(row["exercise_name"], normalize_quality(row["primary_quality"]))
    secondary = []
    for value in split(row["secondary_qualities"]):
        normalized = normalize_quality(value)
        if normalized != primary and normalized not in secondary:
            secondary.append(normalized)
    secondary = secondary[:3]
    role = proposed_role(row, primary)
    current_units = split(row["dose_units"])
    required_units = expected_units(method_type, row["exercise_name"])
    missing_units = [unit for unit in required_units if unit not in current_units]
    relation_summary = {}
    unresolved_count = 0
    variation_count = 0
    for field in ("progressions", "regressions", "substitutions"):
        values = split(row[field])
        exact = variations = unresolved = 0
        for value in values:
            kind, resolved_name = relation_kind(value, names)
            exact += kind == "catalogue_link"
            variations += kind == "prescription_variation"
            unresolved += kind == "unresolved_method_name"
            if kind != "catalogue_link":
                relation_rows.append({
                    "source_id": row["source_id"], "exercise_name": row["exercise_name"],
                    "relation_type": field[:-1], "raw_target": value, "classification": kind,
                    "recommended_action": "move to prescription/progression rule" if kind == "prescription_variation" else "resolve to a catalogue method, add a justified method, or remove",
                })
        relation_summary[field] = f"{len(values)} total; {exact} linked; {variations} prescription; {unresolved} unresolved"
        unresolved_count += unresolved
        variation_count += variations
    issues = []
    if method_type != row["type"]:
        issues.append("method_type")
    if primary != row["primary_quality"] or secondary != split(row["secondary_qualities"])[:3]:
        issues.append("effects")
    if row["training_role"] not in {"preparation", "primary", "accessory", "capacity", "recovery"}:
        issues.append("training_role")
    if missing_units:
        issues.append("dose_model")
    if row["instructions"].strip() == row["coaching_cues"].strip():
        issues.append("instructions_duplicate_cues")
    if not split(row["aliases"]):
        issues.append("aliases_missing")
    if unresolved_count:
        issues.append("unresolved_relations")
    if variation_count:
        issues.append("prescription_text_in_relations")
    if row["type"] in {"plyometric", "isometric"} and not row["supervision_required"]:
        issues.append("supervision_value_missing")
    if row["catalogue_scope"] == "specialist_only":
        value = "specialist"
    elif row["movement_pattern"] in CORE_PATTERNS or primary in {"acceleration", "maximum_velocity", "deceleration", "change_of_direction", "reactive_agility", "aerobic_capacity", "threshold_capacity", "high_intensity_aerobic_power", "repeated_sprint_ability"}:
        value = "core"
    else:
        value = "contextual"
    readiness = "rewrite_required"
    reasons = [
        "Instructions and cues are not separated",
        "Catalogue approval is not equivalent to sport-package release eligibility",
    ]
    if method_type != row["type"]:
        reasons.append(f"Type should change from {row['type']} to {method_type}")
    if primary != row["primary_quality"]:
        reasons.append(f"Primary quality should normalize to {primary}")
    if missing_units:
        reasons.append("Dose compatibility is incomplete")
    if unresolved_count:
        reasons.append(f"{unresolved_count} relation targets do not resolve")
    audit_rows.append({
        "source_id": row["source_id"], "exercise_name": row["exercise_name"], "stable_code": row["code"],
        "catalogue_value": value, "readiness_disposition": readiness,
        "current_type": row["type"], "proposed_type": method_type,
        "movement_pattern": row["movement_pattern"], "current_primary_quality": row["primary_quality"],
        "proposed_primary_quality": primary, "proposed_secondary_qualities": ";".join(secondary),
        "proposed_training_role": role, "minimum_level": row["minimum_level"],
        "technical_cost": row["technical_cost"], "impact_cost": row["impact_cost"],
        "fatigue_cost": row["fatigue_cost"], "supervision_required": row["supervision_required"],
        "environments": row["environments"], "equipment": row["equipment"],
        "current_dose_units": row["dose_units"], "required_dose_units": ";".join(required_units),
        "missing_dose_units": ";".join(missing_units), "instruction_status": "rewrite: currently duplicates coaching cues",
        "safety_status": "present; scientific/specialist verification remains required",
        "progression_status": relation_summary["progressions"], "regression_status": relation_summary["regressions"],
        "substitution_status": relation_summary["substitutions"], "issues": ";".join(issues),
        "reason": "; ".join(reasons), "generator_release_eligible": "no",
    })
    coverage[(primary, method_type)][row["minimum_level"]] += 1
    coverage[(primary, method_type)]["total"] += 1

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
    writer.writeheader(); writer.writerows(audit_rows)
with RELATIONS.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(relation_rows[0]))
    writer.writeheader(); writer.writerows(relation_rows)
with COVERAGE.open("w", encoding="utf-8", newline="") as handle:
    columns = ["physical_quality", "method_type", "total", "beginner", "intermediate", "advanced"]
    writer = csv.DictWriter(handle, fieldnames=columns); writer.writeheader()
    for (quality, method_type), values in sorted(coverage.items()):
        writer.writerow({column: values.get(column, 0) for column in columns} | {"physical_quality": quality, "method_type": method_type})

print(f"audited={len(audit_rows)} unresolved_relation_rows={len(relation_rows)}")
