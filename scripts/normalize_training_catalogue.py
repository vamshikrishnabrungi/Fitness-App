#!/usr/bin/env python3
"""Build Runlete's normalized, catalogue-approved training-method CSV.

The current CSV is the source catalogue. This compiler preserves stable codes,
uses the Phase 1 audit for the 173 legacy records, completes the 58 reviewed
extensions, adds the seven unresolved methods, and emits canonical code-based
relations plus a reconciliation report.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "Backend data files" / "exercises" / "curated_exercises.csv"
AUDIT = ROOT / "Research materials" / "audits" / "catalogue" / "phase1_exercise_catalogue_audit.csv"
REPORT_JSON = ROOT / "Research materials" / "audits" / "catalogue" / "normalized_catalogue_validation.json"
REPORT_MD = ROOT / "Research materials" / "audits" / "catalogue" / "NORMALIZED_CATALOGUE_VALIDATION.md"

QUALITY_CODES = {
    "maximum_strength", "explosive_strength", "isometric_force_capacity",
    "eccentric_capacity", "local_muscular_endurance", "acceleration",
    "maximum_velocity", "speed_endurance", "deceleration",
    "change_of_direction", "reactive_agility", "landing_capacity",
    "vertical_power", "horizontal_power", "lateral_power",
    "rotational_power", "upper_body_power", "reactive_elastic_strength",
    "aerobic_capacity", "threshold_capacity", "high_intensity_aerobic_power",
    "anaerobic_power", "anaerobic_capacity", "repeated_sprint_ability",
    "repeated_high_intensity_ability", "calf_soleus_capacity",
    "hamstring_capacity", "adductor_capacity", "shoulder_capacity",
    "trunk_force_transfer", "neck_capacity", "grip_capacity",
    "balance_postural_control", "movement_coordination",
    "mobility_range_capacity", "mobility_preparation", "recovery_capacity",
    "economy_efficiency",
}

METHOD_TYPES = {
    "exercise", "isometric", "plyometric", "speed_drill",
    "deceleration_drill", "change_of_direction_drill",
    "reactive_agility_drill", "preparation_drill", "mobility",
    "conditioning_modality", "assessment",
}
TRAINING_ROLES = {"preparation", "primary", "accessory", "capacity", "recovery"}
LEVEL = {"beginner": 0, "intermediate": 1, "advanced": 2}

DOSE_BY_TYPE = {
    "exercise": "sets;repetitions;load_kg;percentage_1rm;effort_rpe;rir;tempo_seconds;recovery_seconds",
    "isometric": "sets;duration_seconds;effort_rpe;joint_position;recovery_seconds",
    "plyometric": "sets;repetitions;contacts;distance_m;height_cm;intensity_percent;effort_rpe;recovery_seconds",
    "speed_drill": "sets;repetitions;distance_m;duration_seconds;intensity_percent;recovery_seconds",
    "deceleration_drill": "sets;repetitions;distance_m;approach_intensity_percent;recovery_seconds",
    "change_of_direction_drill": "sets;repetitions;distance_m;approach_intensity_percent;cut_angle_degrees;recovery_seconds",
    "reactive_agility_drill": "sets;repetitions;bout_duration_seconds;approach_intensity_percent;stimulus_type;choice_count;recovery_seconds",
    "preparation_drill": "sets;repetitions;duration_seconds;distance_m;effort_rpe;recovery_seconds",
    "mobility": "sets;repetitions;duration_seconds;range_of_motion;effort_rpe;recovery_seconds",
    "conditioning_modality": "sets;repetitions;duration_seconds;duration_minutes;distance_m;distance_km;intensity_system;pace;heart_rate_zone;power_watts;recovery_seconds;set_recovery_seconds",
    "assessment": "attempts;duration_seconds;distance_m;load_kg;measurement_unit;recovery_seconds",
}

DOSE_UNIT_OVERRIDES = {
    **{code: "sets;distance_m;duration_seconds;load_kg;effort_rpe;recovery_seconds" for code in {
        "farmer_s_carry", "suitcase_carry", "single_arm_front_rack_carry",
        "overhead_carry", "double_kettlebell_front_rack_carry", "bear_hug_carry",
    }},
    **{code: "sets;distance_m;duration_seconds;effort_rpe;recovery_seconds" for code in {
        "bear_crawl", "lateral_bear_crawl", "crab_walk",
    }},
    **{code: "sets;distance_m;load_kg;effort_rpe;recovery_seconds" for code in {
        "sled_push", "forward_sled_drag", "backward_sled_drag",
    }},
    "controlled_hang": "sets;duration_seconds;effort_rpe;recovery_seconds",
    "passive_rest": "duration_minutes",
}


def slug(value: str) -> str:
    value = value.lower().replace("&", "and").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def split(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def unique(values: list[str], limit: int | None = None) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result[:limit] if limit else result


MISSING_METHODS = [
    {
        "source_id": "EXT-059", "exercise_name": "A-March", "code": "a_march",
        "aliases": "marching sprint drill", "type": "speed_drill",
        "movement_pattern": "upright_sprint_preparation", "primary_quality": "movement_coordination",
        "secondary_qualities": "maximum_velocity;mobility_preparation", "training_role": "preparation",
        "primary_muscles": "hip_flexors;calves;glutes", "secondary_muscles": "trunk",
        "equipment": "", "environments": "field;track;court;gym", "minimum_level": "beginner",
        "technical_cost": "2", "impact_cost": "1", "fatigue_cost": "1", "supervision_required": "no",
        "instructions": "March forward with a tall posture, lifting one thigh while the opposite foot remains active under the body. Place each foot beneath the hips and keep a steady rhythm.",
        "coaching_cues": "Stay tall. Step down beneath you. Keep the rhythm controlled.",
        "common_mistakes": "Reaching the foot forward; leaning back; forcing excessive knee height; rushing before posture is stable.",
        "safety_stop_conditions": "Stop for pain, dizziness, loss of balance, unsafe footing or inability to maintain controlled posture.",
        "progressions": "a_skip", "regressions": "wall_march", "substitutions": "wall_march;power_skipping",
    },
    {
        "source_id": "EXT-060", "exercise_name": "Hill Acceleration", "code": "hill_acceleration",
        "aliases": "uphill acceleration", "type": "speed_drill", "movement_pattern": "incline_linear_acceleration",
        "primary_quality": "acceleration", "secondary_qualities": "horizontal_power;explosive_strength",
        "training_role": "primary", "primary_muscles": "glutes;quadriceps;hamstrings;calves", "secondary_muscles": "trunk",
        "equipment": "safe_moderate_hill", "environments": "field;road;trail", "minimum_level": "intermediate",
        "technical_cost": "3", "impact_cost": "2", "fatigue_cost": "4", "supervision_required": "yes",
        "instructions": "Accelerate up a safe, consistent moderate incline for the prescribed distance. Use full recovery and stop the repetition before posture or step rhythm deteriorates.",
        "coaching_cues": "Push the ground back. Rise gradually. Keep steps forceful and rhythmic.",
        "common_mistakes": "Using a hill that is too steep; turning the sprint into a slow grind; short recovery; running on traffic-exposed or uneven ground.",
        "safety_stop_conditions": "Stop for pain, dizziness, unusual breathlessness, unsafe traffic or surface, slipping, or clear loss of sprint mechanics.",
        "progressions": "light_sled_acceleration", "regressions": "falling_start_acceleration", "substitutions": "light_sled_acceleration;two_point_start_acceleration",
    },
    {
        "source_id": "EXT-061", "exercise_name": "Easy Aerobic Swim", "code": "easy_aerobic_swim",
        "aliases": "easy continuous swim", "type": "conditioning_modality", "movement_pattern": "continuous_swimming",
        "primary_quality": "aerobic_capacity", "secondary_qualities": "economy_efficiency;recovery_capacity",
        "training_role": "primary", "primary_muscles": "cardiorespiratory_system;whole_body", "secondary_muscles": "shoulders;trunk",
        "equipment": "pool;pace_clock", "environments": "pool", "minimum_level": "beginner",
        "technical_cost": "2", "impact_cost": "1", "fatigue_cost": "2", "supervision_required": "yes",
        "instructions": "Only prescribe this method to an athlete with demonstrated independent water competency in a supervised pool. Swim continuously or in short easy repeats using a familiar stroke, comfortable breathing and an intensity that permits controlled technique throughout.",
        "coaching_cues": "Easy rhythm. Relaxed breathing. Finish with the same stroke quality you started with.",
        "common_mistakes": "Turning the session into threshold work; using an unfamiliar stroke; ignoring pool length or water-safety rules; continuing with shoulder pain.",
        "safety_stop_conditions": "Do not prescribe without demonstrated independent water competency and appropriate pool supervision. Stop for distress in water, chest pain, dizziness, shoulder pain, unusual breathlessness or loss of safe stroke control.",
        "progressions": "swimming_threshold_intervals", "regressions": "low_impact_recovery_session", "substitutions": "easy_continuous_cycle;easy_continuous_run",
    },
    {
        "source_id": "EXT-062", "exercise_name": "Swimming Aerobic-Power Intervals", "code": "swimming_aerobic_power_intervals",
        "aliases": "swim aerobic power intervals", "type": "conditioning_modality", "movement_pattern": "high_intensity_swimming_intervals",
        "primary_quality": "high_intensity_aerobic_power", "secondary_qualities": "aerobic_capacity;economy_efficiency",
        "training_role": "primary", "primary_muscles": "cardiorespiratory_system;whole_body", "secondary_muscles": "shoulders;trunk",
        "equipment": "pool;pace_clock", "environments": "pool", "minimum_level": "intermediate",
        "technical_cost": "3", "impact_cost": "1", "fatigue_cost": "4", "supervision_required": "yes",
        "instructions": "Only prescribe this method to an athlete with demonstrated independent water competency and established repeat-swimming ability in a supervised pool. Swim repeated work bouts in the prescribed high-aerobic domain with a specified stroke, distance, pool length, send-off and easy recovery.",
        "coaching_cues": "Hard and repeatable. Hold stroke length. Respect the send-off.",
        "common_mistakes": "Racing the first repeat; unspecified rest or pool length; continuing after substantial pace or stroke deterioration.",
        "safety_stop_conditions": "Do not prescribe without demonstrated independent water competency and appropriate pool supervision. Stop for distress in water, chest pain, dizziness, shoulder pain, unusual breathlessness or inability to maintain the prescribed stroke and pace range.",
        "progressions": "swimming_anaerobic_capacity_set", "regressions": "swimming_threshold_intervals", "substitutions": "cycling_aerobic_power_intervals;long_aerobic_power_intervals",
    },
    {
        "source_id": "EXT-063", "exercise_name": "Easy Rowing-Ergometer Session", "code": "easy_rower_session",
        "aliases": "easy erg row", "type": "conditioning_modality", "movement_pattern": "continuous_rowing_ergometer",
        "primary_quality": "aerobic_capacity", "secondary_qualities": "recovery_capacity;local_muscular_endurance",
        "training_role": "primary", "primary_muscles": "cardiorespiratory_system;whole_body", "secondary_muscles": "trunk;posterior_chain",
        "equipment": "rowing_ergometer", "environments": "gym;home", "minimum_level": "beginner",
        "technical_cost": "2", "impact_cost": "1", "fatigue_cost": "2", "supervision_required": "no",
        "instructions": "Row continuously at conversational effort using a familiar stroke rate and damper setting that allow smooth, repeatable technique.",
        "coaching_cues": "Easy pressure. Smooth sequence. Keep breathing comfortable.",
        "common_mistakes": "High damper and low-rate grinding; racing the monitor; excessive spinal rounding; using an unfamiliar setup unsupervised.",
        "safety_stop_conditions": "Stop for pain, dizziness, chest pain, unusual breathlessness or inability to maintain controlled rowing mechanics.",
        "progressions": "", "regressions": "low_impact_recovery_session", "substitutions": "easy_continuous_cycle;easy_aerobic_swim",
    },
    {
        "source_id": "EXT-064", "exercise_name": "Hip-Flexor Isometric Hold", "code": "hip_flexor_isometric_hold",
        "aliases": "standing hip flexion hold", "type": "isometric", "movement_pattern": "hip_flexion_isometric",
        "primary_quality": "isometric_force_capacity", "secondary_qualities": "movement_coordination;trunk_force_transfer",
        "training_role": "capacity", "primary_muscles": "hip_flexors", "secondary_muscles": "trunk;stance_leg_glutes",
        "equipment": "wall_optional;resistance_band_optional", "environments": "home;gym;field;track", "minimum_level": "beginner",
        "technical_cost": "2", "impact_cost": "1", "fatigue_cost": "2", "supervision_required": "no",
        "instructions": "Lift one thigh to the prescribed position and hold without leaning back or losing pelvic control. Use support or light resistance only when specified.",
        "coaching_cues": "Stay tall. Hold the thigh without leaning. Keep the stance foot active.",
        "common_mistakes": "Leaning back; rotating the pelvis; holding the breath; choosing resistance that changes the position.",
        "safety_stop_conditions": "Stop for hip or back pain, cramping that does not settle, numbness, dizziness or loss of balance.",
        "progressions": "", "regressions": "", "substitutions": "",
    },
    {
        "source_id": "EXT-065", "exercise_name": "Shoulder External-Rotation Isometric Hold", "code": "shoulder_external_rotation_hold",
        "aliases": "external rotation hold", "type": "isometric", "movement_pattern": "shoulder_external_rotation_isometric",
        "primary_quality": "shoulder_capacity", "secondary_qualities": "isometric_force_capacity",
        "training_role": "capacity", "primary_muscles": "rotator_cuff", "secondary_muscles": "scapular_stabilizers",
        "equipment": "resistance_band_or_immovable_support", "environments": "home;gym;field", "minimum_level": "beginner",
        "technical_cost": "2", "impact_cost": "1", "fatigue_cost": "2", "supervision_required": "no",
        "instructions": "Hold the upper arm in the prescribed supported position and produce controlled external-rotation force without moving the shoulder or trunk.",
        "coaching_cues": "Keep the shoulder quiet. Hold steady pressure. Do not twist the trunk.",
        "common_mistakes": "Using excessive effort; moving the elbow; shrugging; rotating the torso; working through shoulder pain.",
        "safety_stop_conditions": "Stop for shoulder pain, instability, numbness, tingling, unexpected weakness or loss of controlled position.",
        "progressions": "cable_90_90_external_rotation", "regressions": "band_external_rotation_at_side", "substitutions": "side_lying_dumbbell_external_rotation;band_external_rotation_at_side",
    },
]


TYPE_OVERRIDES = {
    "snap_down": "deceleration_drill",
    "bilateral_jump_to_stick": "plyometric",
    "drop_landing_to_stick": "plyometric",
    "single_leg_land_and_stick": "plyometric",
    "easy_mode_specific_raise": "preparation_drill",
    "wall_march": "speed_drill", "wall_switch": "speed_drill", "a_skip": "speed_drill",
    "falling_start_acceleration": "speed_drill", "two_point_start_acceleration": "speed_drill",
    "three_point_start_acceleration": "speed_drill", "light_sled_acceleration": "speed_drill",
    "progressive_build_up_run": "speed_drill", "flying_sprint": "speed_drill", "wicket_run": "speed_drill",
    "planned_linear_stop": "deceleration_drill", "progressive_speed_deceleration": "deceleration_drill",
    "lateral_stop": "deceleration_drill", "planned_45_degree_cut": "change_of_direction_drill",
    "planned_90_degree_cut": "change_of_direction_drill", "planned_180_degree_turn": "change_of_direction_drill",
    "planned_multidirectional_sequence": "change_of_direction_drill",
    "single_cue_reactive_cut": "reactive_agility_drill", "multi_choice_reactive_cut": "reactive_agility_drill",
    "partner_mirror_drill": "reactive_agility_drill", "partner_chase_drill": "reactive_agility_drill",
    "split_squat_yielding_hold": "isometric", "standing_calf_raise_hold": "isometric",
    "bent_knee_soleus_hold": "isometric", "hamstring_bridge_hold": "isometric",
    "overcoming_mid_thigh_pull": "isometric", "overcoming_split_squat_push": "isometric",
    "optional_foam_rolling": "mobility",
}

QUALITY_OVERRIDES = {
    "four_direction_cervical_isometrics": "neck_capacity",
    "controlled_hang": "grip_capacity",
    "farmer_s_carry": "grip_capacity",
    "supported_single_leg_balance": "balance_postural_control",
    "hip_airplane": "balance_postural_control",
    "optional_foam_rolling": "mobility_range_capacity",
    "knee_to_wall_ankle_rocks": "mobility_range_capacity",
    "deep_squat_pry": "mobility_range_capacity",
    "cossack_squat": "mobility_range_capacity",
}

SECONDARY_OVERRIDES = {
    "four_direction_cervical_isometrics": ["isometric_force_capacity"],
    "controlled_hang": ["shoulder_capacity", "local_muscular_endurance"],
    "farmer_s_carry": ["trunk_force_transfer", "local_muscular_endurance"],
    "supported_single_leg_balance": ["movement_coordination", "mobility_preparation"],
    "hip_airplane": ["trunk_force_transfer", "hamstring_capacity"],
    "barbell_romanian_deadlift": ["eccentric_capacity", "hamstring_capacity", "maximum_strength"],
    "dumbbell_romanian_deadlift": ["eccentric_capacity", "hamstring_capacity", "maximum_strength"],
    "single_leg_romanian_deadlift": ["eccentric_capacity", "hamstring_capacity", "trunk_force_transfer"],
    "knee_to_wall_ankle_rocks": ["mobility_preparation"],
    "deep_squat_pry": ["mobility_preparation"],
    "cossack_squat": ["mobility_preparation", "adductor_capacity"],
}


def normalize_type(row: dict[str, str], audit: dict[str, str] | None) -> str:
    if row["code"] in TYPE_OVERRIDES:
        return TYPE_OVERRIDES[row["code"]]
    proposed = audit["proposed_type"] if audit else row["type"]
    if proposed in METHOD_TYPES:
        return proposed
    return {"strength": "exercise", "conditioning": "exercise", "athletic_drill": "preparation_drill"}.get(proposed, "exercise")


def normalized_dose(row: dict[str, str]) -> str:
    if row["code"] in DOSE_UNIT_OVERRIDES:
        return DOSE_UNIT_OVERRIDES[row["code"]]
    base = split(DOSE_BY_TYPE[row["type"]])
    code = row["code"]
    if code == "light_sled_acceleration":
        base += ["sled_load", "velocity_decrement_percent"]
    if code == "flying_sprint":
        base += ["build_distance_m", "fly_distance_m"]
    if code == "wicket_run":
        base += ["wicket_spacing_m"]
    if row["type"] == "conditioning_modality" and "swim" in code:
        base += ["pool_length_m", "stroke_code", "send_off_seconds"]
    return ";".join(unique(base))


def difficulty(row: dict[str, str]) -> tuple[int, int, int, int]:
    return (
        LEVEL.get(row["minimum_level"], 1),
        int(row["technical_cost"]), int(row["impact_cost"]), int(row["fatigue_cost"]),
    )


def main() -> None:
    with CATALOGUE.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
        fieldnames = list(rows[0])
    with AUDIT.open(encoding="utf-8-sig", newline="") as fh:
        audit_by_code = {row["stable_code"]: row for row in csv.DictReader(fh)}

    existing = {row["code"]: row for row in rows}
    for candidate in MISSING_METHODS:
        if candidate["code"] in existing:
            existing[candidate["code"]].update(candidate)
        else:
            row = {name: "" for name in fieldnames}
            row.update(candidate)
            row.update({
                "catalogue_scope": "shared_training_domain_extension",
                "generator_eligible": "yes", "approval_status": "approved",
                "approved_by": "Runlete founder",
                "approval_scope": "Catalogue content and bounded generator selection; not medical diagnosis, rehabilitation or specialist certification",
            })
            rows.append(row)

    for row in rows:
        audit = audit_by_code.get(row["code"])
        row["type"] = normalize_type(row, audit)
        if audit:
            row["primary_quality"] = audit["proposed_primary_quality"]
            row["secondary_qualities"] = audit["proposed_secondary_qualities"]
            row["training_role"] = audit["proposed_training_role"]
        row["primary_quality"] = QUALITY_OVERRIDES.get(row["code"], row["primary_quality"])
        if row["code"] in SECONDARY_OVERRIDES:
            row["secondary_qualities"] = ";".join(SECONDARY_OVERRIDES[row["code"]])
        secondary = [q for q in split(row["secondary_qualities"]) if q in QUALITY_CODES and q != row["primary_quality"]]
        row["secondary_qualities"] = ";".join(unique(secondary, 3))
        if row["training_role"] not in TRAINING_ROLES:
            row["training_role"] = "capacity" if row["primary_quality"].endswith("_capacity") else "primary"
        row["dose_units"] = normalized_dose(row)
        if not row["equipment"].strip():
            row["equipment"] = "bodyweight"
        new_gap_candidate = row["source_id"].startswith("EXT-") and int(row["source_id"].split("-")[1]) > 65
        row["generator_eligible"] = "no" if "specialist" in row["catalogue_scope"] or new_gap_candidate else "yes"
        row["approval_status"] = "pending_review" if new_gap_candidate else "approved"
        row["approved_by"] = "" if new_gap_candidate else "Runlete founder"
        row["approval_scope"] = (
            "Complete normalized candidate; requires founder review before bounded generator selection"
            if new_gap_candidate else
            "Catalogue content and bounded generator selection; not medical diagnosis, rehabilitation or specialist certification"
        )

    by_code = {row["code"]: row for row in rows}
    by_name: dict[str, str] = {}
    for row in rows:
        for value in [row["code"], row["exercise_name"], *split(row["aliases"])]:
            by_name[slug(value)] = row["code"]

    alias_targets = {
        "supported_squat": "bodyweight_squat", "slower_squat_to_stick": "bodyweight_squat",
        "shorter_walk_or_gentle_cycle": "easy_continuous_cycle", "walking": "easy_continuous_run",
        "easy_cycling": "easy_continuous_cycle", "easy_swimming": "easy_aerobic_swim",
        "easy_walk": "easy_continuous_run", "easy_swim": "easy_aerobic_swim", "easy_cycle": "easy_continuous_cycle",
        "aerobic_swim": "easy_aerobic_swim", "threshold_running_or_swimming_intervals": "threshold_run_intervals",
        "rowing_or_swimming_aerobic_power_intervals": "swimming_aerobic_power_intervals",
        "maximal_short_run_or_swim_repeats": "maximal_short_sprint_repeats",
        "bike_anaerobic_capacity_intervals": "anaerobic_capacity_intervals",
        "gentle_mobility": "world_s_greatest_stretch", "shorter_cooldown_or_none": "passive_rest",
        "shorter_session_or_passive_rest": "passive_rest", "less_pressure_time_or_omit": "passive_rest",
        "additional_rest_or_professional_review_when_indicated": "passive_rest",
        "very_easy_cooldown_or_low_impact_recovery_only_for_a_defined_purpose": "very_easy_active_cooldown",
        "static_wall_hold": "wall_march", "marching_drill": "a_march", "rolling_or_split_stance_start": "falling_start_acceleration",
        "split_stance_or_rolling_start": "falling_start_acceleration", "lighter_sled": "two_point_start_acceleration",
        "directional_jump_to_stick": "bilateral_jump_to_stick", "lower_jump": "snap_down",
        "supported_step_down": "snap_down", "single_leg_lateral_jump_to_stick": "single_leg_lateral_jump",
        "longer_duration": "easy_continuous_run", "shorter_duration_or_lower_resistance": "low_impact_recovery_session",
        "shorter_duration": "low_impact_recovery_session", "fewer_intervals": "steady_tempo_run",
        "fewer_reps": "maximal_short_sprint_repeats", "submaximal_short_repeats": "easy_aerobic_swim",
    }
    by_name.update(alias_targets)

    dropped: list[dict[str, str]] = []
    moved_to_substitution: defaultdict[str, list[str]] = defaultdict(list)

    def resolve(source: dict[str, str], raw: str, relation: str) -> str | None:
        target = by_name.get(slug(raw))
        if not target or target == source["code"]:
            dropped.append({"source_code": source["code"], "relation": relation, "raw_target": raw, "reason": "not_a_canonical_catalogue_method"})
            return None
        target_row = by_code[target]
        if relation == "progressions" and difficulty(target_row) <= difficulty(source):
            moved_to_substitution[source["code"]].append(target)
            return None
        if relation == "regressions" and difficulty(target_row) >= difficulty(source):
            moved_to_substitution[source["code"]].append(target)
            return None
        if relation == "substitutions" and not (
            target_row["primary_quality"] == source["primary_quality"]
            or target_row["movement_pattern"] == source["movement_pattern"]
        ):
            dropped.append({"source_code": source["code"], "relation": relation, "raw_target": raw, "reason": "does_not_preserve_primary_objective_or_pattern"})
            return None
        return target

    for row in rows:
        for relation in ("progressions", "regressions", "substitutions"):
            resolved = [resolve(row, raw, relation) for raw in split(row[relation])]
            row[relation] = ";".join(unique([code for code in resolved if code]))

    no_automatic_substitution = {"hip_flexor_isometric_hold"}
    for row in rows:
        substitutions = split(row["substitutions"]) + moved_to_substitution[row["code"]]
        if not substitutions and row["code"] not in no_automatic_substitution:
            candidates = [
                other for other in rows
                if other["code"] != row["code"]
                and other["primary_quality"] == row["primary_quality"]
                and other["type"] == row["type"]
                and other["catalogue_scope"] != "specialist"
            ]
            candidates.sort(key=lambda other: (abs(LEVEL.get(other["minimum_level"], 1) - LEVEL.get(row["minimum_level"], 1)), other["technical_cost"], other["code"]))
            substitutions.extend(other["code"] for other in candidates[:2])
        row["substitutions"] = ";".join(unique([code for code in substitutions if code in by_code and code != row["code"]], 3))

    errors: list[str] = []
    codes = [row["code"] for row in rows]
    if len(codes) != len(set(codes)):
        errors.append("duplicate stable codes")
    for row in rows:
        if row["type"] not in METHOD_TYPES:
            errors.append(f"{row['code']}: invalid method type {row['type']}")
        if row["primary_quality"] not in QUALITY_CODES:
            errors.append(f"{row['code']}: invalid primary quality {row['primary_quality']}")
        if row["training_role"] not in TRAINING_ROLES:
            errors.append(f"{row['code']}: invalid role {row['training_role']}")
        if len(split(row["secondary_qualities"])) > 3:
            errors.append(f"{row['code']}: more than three secondary qualities")
        for relation in ("progressions", "regressions", "substitutions"):
            for target in split(row[relation]):
                if target not in by_code:
                    errors.append(f"{row['code']}: unresolved {relation} target {target}")

    rows.sort(key=lambda row: (int(row["source_id"].split("-")[-1]), row["code"]))
    with CATALOGUE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "schema_version": "1.0.0",
        "catalogue_rows": len(rows),
        "legacy_rows_reconciled": sum(row["source_id"].startswith("REV-") for row in rows),
        "previous_extensions_approved": sum(row["source_id"].startswith("EXT-") and int(row["source_id"].split("-")[1]) <= 58 for row in rows),
        "missing_methods_added": [method["code"] for method in MISSING_METHODS],
        "generator_eligible": Counter(row["generator_eligible"] for row in rows),
        "method_types": Counter(row["type"] for row in rows),
        "primary_qualities": Counter(row["primary_quality"] for row in rows),
        "relations": {relation: sum(len(split(row[relation])) for row in rows) for relation in ("progressions", "regressions", "substitutions")},
        "dropped_noncanonical_relation_phrases": len(dropped),
        "validation_errors": errors,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=dict) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "# Normalized catalogue validation\n\n"
        f"- Catalogue rows: **{len(rows)}** (173 legacy + 58 approved extensions + 7 resolved methods).\n"
        f"- Generator-eligible catalogue methods: **{report['generator_eligible'].get('yes', 0)}**.\n"
        f"- Canonical progression links: **{report['relations']['progressions']}**.\n"
        f"- Canonical regression links: **{report['relations']['regressions']}**.\n"
        f"- Canonical substitution links: **{report['relations']['substitutions']}**.\n"
        f"- Non-method prose/unresolved relation fragments removed: **{len(dropped)}**.\n"
        f"- Validation errors: **{len(errors)}**.\n\n"
        "Catalogue approval permits bounded selection only. Sport-release eligibility remains governed by the immutable release manifest and generation feature flag.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, default=dict))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
