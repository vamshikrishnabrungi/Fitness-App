#!/usr/bin/env python3
"""Build Runlete's research-derived four-week exercise-reference templates.

The builder does not alter application or database data. It compiles the nine
research phases into reviewable JSON artifacts and validates every method
reference against the normalized curated catalogue. The extension registry is
retained as historical lineage for any method not yet present in the CSV.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Backend data files" / "exercise templates"
CATALOGUE = ROOT / "Backend data files" / "exercises" / "curated_exercises.csv"


def method(code: str, role: str, note: str = "", modes: list[str] | None = None) -> dict:
    return {
        "method_code": code,
        "block_role": role,
        "applicable_modes": modes or ["all"],
        "implementation_note": note,
    }


EXTENSIONS = {
    # Preparation, landing, speed, direction change and agility drills.
    "easy_mode_specific_raise": ("Easy mode-specific raise", "preparation_drill"),
    "snap_down": ("Snap-down", "landing_drill"),
    "bilateral_jump_to_stick": ("Bilateral jump and stick", "landing_drill"),
    "drop_landing_to_stick": ("Drop landing to stick", "landing_drill"),
    "single_leg_land_and_stick": ("Single-leg land and stick", "landing_drill"),
    "wall_march": ("Wall march", "speed_drill"),
    "wall_switch": ("Wall switch", "speed_drill"),
    "a_march": ("A-march", "speed_drill"),
    "a_skip": ("A-skip", "speed_drill"),
    "falling_start_acceleration": ("Falling-start acceleration", "speed_drill"),
    "two_point_start_acceleration": ("Two-point-start acceleration", "speed_drill"),
    "three_point_start_acceleration": ("Three-point-start acceleration", "speed_drill"),
    "light_sled_acceleration": ("Light resisted sled acceleration", "speed_drill"),
    "hill_acceleration": ("Hill acceleration", "speed_drill"),
    "progressive_build_up_run": ("Progressive build-up run", "speed_drill"),
    "flying_sprint": ("Flying sprint", "speed_drill"),
    "wicket_run": ("Supervised wicket run", "speed_drill"),
    "short_speed_endurance_run": ("Short speed-endurance run", "conditioning_modality"),
    "long_sprint_endurance_run": ("Long sprint-endurance run", "conditioning_modality"),
    "planned_linear_stop": ("Planned linear stop", "deceleration_drill"),
    "progressive_speed_deceleration": ("Progressive-speed deceleration", "deceleration_drill"),
    "lateral_stop": ("Lateral stop", "deceleration_drill"),
    "planned_45_degree_cut": ("Planned 45-degree cut", "change_of_direction_drill"),
    "planned_90_degree_cut": ("Planned 90-degree cut", "change_of_direction_drill"),
    "planned_180_degree_turn": ("Planned 180-degree turn", "change_of_direction_drill"),
    "planned_multidirectional_sequence": ("Planned multidirectional sequence", "change_of_direction_drill"),
    "single_cue_reactive_cut": ("Single-cue reactive cut", "reactive_agility_drill"),
    "multi_choice_reactive_cut": ("Multi-choice reactive cut", "reactive_agility_drill"),
    "partner_mirror_drill": ("Partner mirror drill", "reactive_agility_drill"),
    "partner_chase_drill": ("Partner chase drill", "reactive_agility_drill"),
    # Strength/isometric gaps identified by Phase 01 and Phase 08.
    "split_squat_yielding_hold": ("Split-squat yielding hold", "isometric"),
    "standing_calf_raise_hold": ("Standing calf-raise hold", "isometric"),
    "bent_knee_soleus_hold": ("Bent-knee soleus hold", "isometric"),
    "hamstring_bridge_hold": ("Hamstring bridge hold", "isometric"),
    "hip_flexor_isometric_hold": ("Hip-flexor isometric hold", "isometric"),
    "shoulder_external_rotation_hold": ("Shoulder external-rotation hold", "isometric"),
    "overcoming_mid_thigh_pull": ("Overcoming mid-thigh pull", "isometric"),
    "overcoming_split_squat_push": ("Overcoming split-squat push", "isometric"),
    # Aerobic, anaerobic and recovery modalities are not exercises.
    "run_walk_intervals": ("Run-walk intervals", "conditioning_modality"),
    "easy_continuous_run": ("Easy continuous run", "conditioning_modality"),
    "long_aerobic_run": ("Long aerobic run", "conditioning_modality"),
    "steady_tempo_run": ("Steady/tempo run", "conditioning_modality"),
    "threshold_run_intervals": ("Threshold running intervals", "conditioning_modality"),
    "long_aerobic_power_intervals": ("Long aerobic-power intervals", "conditioning_modality"),
    "short_aerobic_power_intervals": ("Short aerobic-power intervals", "conditioning_modality"),
    "shuttle_aerobic_power_intervals": ("Shuttle aerobic-power intervals", "conditioning_modality"),
    "maximal_short_sprint_repeats": ("Maximal short sprint repeats", "conditioning_modality"),
    "anaerobic_capacity_intervals": ("Anaerobic-capacity intervals", "conditioning_modality"),
    "linear_repeated_sprints": ("Linear repeated-sprint protocol", "conditioning_modality"),
    "cod_repeated_sprints": ("COD repeated-sprint protocol", "conditioning_modality"),
    "repeated_high_intensity_cluster": ("Repeated high-intensity cluster", "conditioning_modality"),
    "easy_continuous_cycle": ("Easy continuous cycling", "conditioning_modality"),
    "cycling_threshold_intervals": ("Cycling threshold intervals", "conditioning_modality"),
    "cycling_aerobic_power_intervals": ("Cycling aerobic-power intervals", "conditioning_modality"),
    "cycling_sprint_repeats": ("Cycling sprint repeats", "conditioning_modality"),
    "easy_aerobic_swim": ("Easy aerobic swim", "conditioning_modality"),
    "swimming_threshold_intervals": ("Swimming threshold intervals", "conditioning_modality"),
    "swimming_aerobic_power_intervals": ("Swimming aerobic-power intervals", "conditioning_modality"),
    "swimming_sprint_repeats": ("Swimming sprint repeats", "conditioning_modality"),
    "swimming_anaerobic_capacity_set": ("Swimming anaerobic-capacity set", "conditioning_modality"),
    "easy_rower_session": ("Easy rowing-ergometer session", "conditioning_modality"),
    "very_easy_active_cooldown": ("Very easy active cooldown", "recovery_modality"),
    "low_impact_recovery_session": ("Low-impact recovery session", "recovery_modality"),
    "optional_foam_rolling": ("Optional symptom-free foam rolling", "recovery_modality"),
    "passive_rest": ("Passive rest/no modality", "recovery_modality"),
}


# Four weekly prescriptions are deliberately explicit. Week 4 consolidates or
# deloads; it is not an automatic fourth consecutive overload.
DOSES = {
    "strength": {
        "beginner": [(3, "8", "RIR 3", "90-150s"), (3, "8", "RIR 2-3", "90-180s"), (4, "6", "RIR 2-3", "120-180s"), (2, "6", "RIR 3-4", "120s")],
        "intermediate": [(4, "6", "RIR 3", "150-240s"), (4, "5", "RIR 2-3", "180-240s"), (5, "4", "RIR 2", "180-300s"), (3, "4", "RIR 3", "180-240s")],
        "advanced": [(4, "5", "RIR 2-3", "180-300s"), (5, "4", "RIR 2", "180-300s"), (5, "3", "RIR 1-2", "240-300s"), (3, "3", "RIR 3", "180-300s")],
    },
    "isometric_yield": {
        "beginner": [(3, "15s", "RPE 6", "60s"), (3, "20s", "RPE 6-7", "60-90s"), (4, "20s", "RPE 7", "90s"), (2, "20s", "RPE 6", "60s")],
        "intermediate": [(3, "20s", "RPE 7", "90s"), (4, "20s", "RPE 7-8", "90s"), (4, "25s", "RPE 8", "90-120s"), (2, "20s", "RPE 7", "90s")],
        "advanced": [(4, "20s", "RPE 8", "90-120s"), (4, "25s", "RPE 8", "120s"), (5, "20s", "RPE 8-9", "120-180s"), (3, "15s", "RPE 7", "90s")],
    },
    "isometric_overcome": {
        "beginner": [(3, "3s", "RPE 7", "120s"), (3, "4s", "RPE 7", "120s"), (4, "4s", "RPE 7-8", "150s"), (2, "3s", "RPE 6-7", "120s")],
        "intermediate": [(4, "4s", "high intent", "150-180s"), (5, "4s", "high intent", "180s"), (5, "5s", "maximal safe intent", "180-240s"), (3, "4s", "high intent", "150s")],
        "advanced": [(5, "3s", "maximal safe intent", "180-240s"), (5, "4s", "maximal safe intent", "180-240s"), (6, "4s", "maximal safe intent", "240s"), (3, "3s", "high intent", "180s")],
    },
    "eccentric": {
        "beginner": [(2, "6", "3s eccentric/RIR 4", "120s"), (3, "6", "3s eccentric/RIR 3", "120s"), (3, "7", "3s eccentric/RIR 3", "150s"), (2, "6", "controlled/RIR 4", "120s")],
        "intermediate": [(3, "6", "3s eccentric/RIR 3", "150s"), (4, "5", "3-4s eccentric/RIR 2-3", "180s"), (4, "6", "controlled high effort", "180-240s"), (2, "5", "RIR 4", "150s")],
        "advanced": [(3, "5", "high controlled effort", "180-240s"), (4, "4", "high controlled effort", "240s"), (4, "5", "high nonfailure effort", "240s"), (2, "4", "submaximal", "180s")],
    },
    "power": {
        "beginner": [(3, "3", "fast, submaximal", "120s"), (3, "4", "fast", "120-150s"), (4, "3", "high quality", "150s"), (2, "3", "high quality", "120s")],
        "intermediate": [(4, "3", "high intent", "150s"), (4, "4", "high intent", "150-180s"), (5, "3", "high intent", "180s"), (3, "3", "high quality", "150s")],
        "advanced": [(4, "3", "maximal safe intent", "180s"), (5, "3", "maximal safe intent", "180-240s"), (5, "2", "maximal safe intent", "240s"), (3, "2", "high quality", "180s")],
    },
    "landing": {
        "beginner": [(3, "3 contacts", "low", "60s"), (3, "4 contacts", "low", "60-90s"), (4, "3 contacts", "low-moderate", "90s"), (2, "3 contacts", "low", "60s")],
        "intermediate": [(3, "4 contacts", "moderate", "90s"), (4, "4 contacts", "moderate", "90-120s"), (4, "5 contacts", "moderate", "120s"), (2, "4 contacts", "low-moderate", "90s")],
        "advanced": [(4, "4 contacts", "moderate-high", "120s"), (4, "5 contacts", "high quality", "120-180s"), (5, "4 contacts", "high quality", "180s"), (3, "3 contacts", "moderate", "120s")],
    },
    "speed": {
        "beginner": [(4, "10m", "90-95% intent", "120s"), (5, "10m", "90-95%", "120s"), (4, "15m", "95%", "150s"), (3, "10-15m", "90-95%", "120s")],
        "intermediate": [(4, "15m", "95%", "150s"), (5, "15m", "95-98%", "150-180s"), (4, "20m", "95-100%", "180s"), (3, "15-20m", "95%", "150s")],
        "advanced": [(4, "20m", "95-100%", "180-240s"), (5, "20m", "95-100%", "180-240s"), (4, "30m", "95-100%", "240s"), (3, "20m", "95-100%", "180s")],
    },
    "direction": {
        "beginner": [(3, "3/side", "50-60% entry", "60-90s"), (3, "4/side", "60%", "90s"), (4, "3/side", "60-70%", "90-120s"), (2, "3/side", "50-60%", "60-90s")],
        "intermediate": [(3, "4/side", "70%", "90-120s"), (4, "4/side", "70-80%", "120s"), (4, "5/side", "80-90%", "120-180s"), (2, "4/side", "70%", "90-120s")],
        "advanced": [(4, "4/side", "80-90%", "120-180s"), (4, "5/side", "90%", "150-180s"), (5, "4/side", "90-100%", "180s"), (3, "3/side", "80-90%", "120-180s")],
    },
    "aerobic": {
        "beginner": [(1, "20min", "RPE 2-3/talk test", "continuous"), (1, "24min", "RPE 2-3", "continuous"), (1, "28min", "RPE 2-3", "continuous"), (1, "20min", "RPE 2", "continuous")],
        "intermediate": [(1, "30min", "easy zone", "continuous"), (1, "36min", "easy zone", "continuous"), (1, "42min", "easy zone", "continuous"), (1, "30min", "easy zone", "continuous")],
        "advanced": [(1, "45min", "easy zone", "continuous"), (1, "55min", "easy zone", "continuous"), (1, "65min", "easy zone", "continuous"), (1, "45min", "easy zone", "continuous")],
    },
    "threshold": {
        "beginner": [(3, "3min", "RPE 6", "2min easy"), (3, "4min", "RPE 6", "2min easy"), (4, "4min", "RPE 6-7", "2min easy"), (2, "4min", "RPE 6", "2min easy")],
        "intermediate": [(3, "6min", "threshold estimate", "2min easy"), (4, "6min", "threshold", "2min easy"), (3, "8min", "threshold", "2-3min easy"), (2, "6min", "threshold", "2min easy")],
        "advanced": [(4, "8min", "threshold", "2min easy"), (3, "10min", "threshold", "2min easy"), (4, "10min", "threshold", "2-3min easy"), (2, "8min", "threshold", "2min easy")],
    },
    "hi_aerobic": {
        "beginner": [(4, "1min", "RPE 7-8", "2min easy"), (5, "1min", "RPE 7-8", "2min easy"), (5, "90s", "RPE 8", "2min easy"), (3, "1min", "RPE 7", "2min easy")],
        "intermediate": [(4, "3min", "RPE 8", "3min easy"), (5, "3min", "RPE 8", "3min easy"), (4, "4min", "RPE 8-9", "3min easy"), (3, "3min", "RPE 8", "3min easy")],
        "advanced": [(5, "4min", "high aerobic", "3min easy"), (6, "4min", "high aerobic", "3min easy"), (5, "5min", "high aerobic", "3-4min easy"), (3, "4min", "high aerobic", "3min easy")],
    },
    "anaerobic_power": {
        "beginner": [(4, "6s", "near maximal", "90s"), (5, "6s", "near maximal", "120s"), (6, "6s", "maximal quality", "120s"), (3, "6s", "near maximal", "90s")],
        "intermediate": [(6, "6s", "maximal", "120s"), (7, "6s", "maximal", "120-150s"), (8, "6s", "maximal", "150s"), (4, "6s", "maximal", "120s")],
        "advanced": [(6, "8s", "maximal", "150s"), (8, "8s", "maximal", "150-180s"), (10, "6s", "maximal", "180s"), (5, "6s", "maximal", "150s")],
    },
    "anaerobic_capacity": {
        "beginner": [(4, "15s", "hard controlled", "75s"), (5, "15s", "hard", "75s"), (5, "20s", "hard", "100s"), (3, "15s", "hard controlled", "75s")],
        "intermediate": [(5, "20s", "very hard", "100s"), (6, "20s", "very hard", "100s"), (6, "30s", "very hard", "150s"), (4, "20s", "hard", "100s")],
        "advanced": [(6, "30s", "very hard", "150s"), (7, "30s", "very hard", "150-180s"), (8, "30s", "very hard", "180s"), (4, "30s", "hard", "150s")],
    },
    "repeat_effort": {
        "beginner": [(2, "4x10m", "90-95%", "20s reps/3min sets"), (2, "5x10m", "90-95%", "20s/3min"), (3, "4x10m", "95%", "20s/3min"), (2, "4x10m", "90%", "25s/3min")],
        "intermediate": [(2, "5x20m", "95%", "20s/4min"), (3, "5x20m", "95%", "20s/4min"), (3, "6x20m", "95-100%", "20s/4min"), (2, "5x20m", "95%", "25s/4min")],
        "advanced": [(3, "6x20m", "maximal repeat quality", "20s/4min"), (3, "7x20m", "maximal repeat quality", "20s/4min"), (4, "6x20m", "maximal repeat quality", "20s/4min"), (2, "6x20m", "95%", "25s/4min")],
    },
    "capacity": {
        "beginner": [(2, "12", "RIR 4", "60s"), (3, "12", "RIR 3", "60s"), (3, "15", "RIR 3", "60-90s"), (2, "10", "RIR 4", "60s")],
        "intermediate": [(3, "12", "RIR 3", "60-90s"), (3, "15", "RIR 2-3", "60-90s"), (4, "12", "RIR 2", "90s"), (2, "12", "RIR 4", "60s")],
        "advanced": [(3, "15", "RIR 2-3", "90s"), (4, "15", "RIR 2", "90s"), (4, "20", "RIR 2", "90-120s"), (2, "12", "RIR 3", "90s")],
    },
    "mobility": {
        "beginner": [(2, "6/side", "controlled range", "30s"), (2, "8/side", "controlled range", "30s"), (3, "8/side", "controlled range", "30s"), (1, "8/side", "easy range", "30s")],
        "intermediate": [(2, "8/side", "controlled range", "30s"), (3, "8/side", "controlled range", "30s"), (3, "10/side", "active end range", "30-45s"), (2, "8/side", "easy range", "30s")],
        "advanced": [(3, "8/side", "active end range", "30s"), (3, "10/side", "active end range", "30-45s"), (4, "8/side", "loaded/control", "45-60s"), (2, "8/side", "easy range", "30s")],
    },
    "recovery": {
        "beginner": [(1, "10min", "RPE 1-2", "none"), (1, "15min", "RPE 1-2", "none"), (1, "20min", "RPE 1-2", "none"), (1, "10min", "RPE 1", "none")],
        "intermediate": [(1, "15min", "RPE 1-2", "none"), (1, "20min", "RPE 1-2", "none"), (1, "25min", "RPE 1-3", "none"), (1, "15min", "RPE 1-2", "none")],
        "advanced": [(1, "20min", "RPE 1-2", "none"), (1, "25min", "RPE 1-2", "none"), (1, "30min", "RPE 1-3", "none"), (1, "15min", "RPE 1-2", "none")],
    },
}


# phase, category, display name, dose profile, source templates, and the actual
# method progression for beginner/intermediate/advanced.
CATEGORY_ROWS = [
    (1,"maximum_strength","Maximum strength","strength",["P1-MAX-FOUNDATION","P1-MAX-DEVELOPMENT","P1-MAX-MAINTENANCE"],
     [["bodyweight_squat","goblet_squat","kettlebell_deadlift","push_up","inverted_row"],["goblet_squat","trap_bar_deadlift","dumbbell_split_squat","dumbbell_bench_press","lat_pulldown"],["barbell_back_squat","trap_bar_deadlift","bulgarian_split_squat","barbell_bench_press","pull_up"]]),
    (1,"yielding_isometric_force","Yielding isometric force","isometric_yield",["P1-ISO-YIELD-CAPACITY"],
     [["spanish_squat_hold","pallof_press_iso_hold","adductor_squeeze"],["split_squat_yielding_hold","bent_knee_soleus_hold","short_lever_copenhagen_plank"],["split_squat_yielding_hold","standing_calf_raise_hold","hamstring_bridge_hold"]]),
    (1,"overcoming_isometric_force","Overcoming isometric force","isometric_overcome",["P1-ISO-OVERCOMING-MAX","P1-ISO-RAPID-INTENT"],
     [["split_squat_yielding_hold"],["overcoming_split_squat_push","overcoming_mid_thigh_pull"],["overcoming_mid_thigh_pull","overcoming_split_squat_push"]]),
    (1,"eccentric_capacity","Eccentric capacity","eccentric",["P1-ECC-INTRO","P1-ECC-DEVELOPMENT","P1-ECC-MAINTENANCE"],
     [["negative_push_up"],["barbell_romanian_deadlift","assisted_nordic_hamstring_curl"],["barbell_romanian_deadlift","nordic_hamstring_curl","single_leg_romanian_deadlift"]]),
    (2,"explosive_strength","Explosive strength","power",["P2-T01","P2-T02"],
     [["standing_jump_and_reach","underhand_throw"],["kettlebell_swing"],["push_press","kettlebell_swing"]]),
    (2,"vertical_power","Vertical power","power",["P2-T03"],
     [["standing_jump_and_reach"],["squat_jump","box_jump"],["box_jump","squat_jump"]]),
    (2,"horizontal_power","Horizontal power","power",["P2-T04"],
     [["standing_long_jump","underhand_throw"],["standing_long_jump","power_skipping"],["standing_long_jump","power_skipping"]]),
    (2,"lateral_power","Lateral power","power",["P2-T05"],
     [["side_to_side_ankle_hop"],["lateral_cone_hop"],["single_leg_lateral_jump","diagonal_cone_hop"]]),
    (2,"rotational_power","Rotational power","power",["P2-T06"],
     [["side_throw","pallof_press"],["side_throw","landmine_rotation"],["side_throw","landmine_rotation"]]),
    (2,"upper_body_power","Upper-body power","power",["P2-T07"],
     [["underhand_throw","medicine_ball_slam"],["chest_pass","overhead_throw"],["chest_pass","push_press"]]),
    (3,"landing_capacity","Landing capacity","landing",["P3-T01","P3-T02","P3-T03","P3-T04"],
     [["snap_down","bilateral_jump_to_stick"],["drop_landing_to_stick","bilateral_jump_to_stick"],["single_leg_land_and_stick","drop_landing_to_stick"]]),
    (3,"extensive_plyometrics","Extensive plyometrics","landing",["P3-T05","P3-T06"],
     [["two_foot_ankle_hops","side_to_side_ankle_hop"],["front_cone_hop","zigzag_pogo_hop"],["hurdle_barrier_hop","power_skipping"]]),
    (3,"reactive_elastic_strength","Reactive/elastic strength","landing",["P3-T07","P3-T10"],
     [["two_foot_ankle_hops"],["front_cone_hop","lateral_cone_hop"],["hurdle_barrier_hop","drop_landing_to_stick"]]),
    (3,"horizontal_bounding","Horizontal bounding","landing",["P3-T08"],
     [["standing_long_jump"],["power_skipping","standing_long_jump"],["power_skipping","standing_long_jump"]]),
    (3,"lateral_elastic_strength","Lateral elastic strength","landing",["P3-T09"],
     [["side_to_side_ankle_hop"],["lateral_cone_hop","zigzag_pogo_hop"],["single_foot_side_to_side_ankle_hop","single_leg_lateral_jump"]]),
    (4,"acceleration","Acceleration","speed",["P4-T01","P4-T02","P4-T03","P4-T04","P4-T05"],
     [["wall_march","falling_start_acceleration"],["wall_switch","two_point_start_acceleration","light_sled_acceleration"],["a_skip","three_point_start_acceleration","light_sled_acceleration"]]),
    (4,"maximum_velocity","Maximum velocity","speed",["P4-T06","P4-T07"],
     [["progressive_build_up_run"],["a_skip","progressive_build_up_run","flying_sprint"],["wicket_run","flying_sprint"]]),
    (4,"speed_endurance","Speed endurance","anaerobic_capacity",["P4-T09","P4-T10"],
     [["short_speed_endurance_run"],["short_speed_endurance_run"],["long_sprint_endurance_run"]]),
    (5,"deceleration","Deceleration","direction",["P5-T01","P5-T02","P5-T03","P5-T04"],
     [["snap_down","planned_linear_stop"],["progressive_speed_deceleration","lateral_stop"],["progressive_speed_deceleration","lateral_stop"]]),
    (5,"planned_change_of_direction","Planned change of direction","direction",["P5-T05","P5-T06","P5-T07","P5-T08"],
     [["planned_45_degree_cut"],["planned_45_degree_cut","planned_90_degree_cut"],["planned_90_degree_cut","planned_180_degree_turn","planned_multidirectional_sequence"]]),
    (5,"reactive_agility","Reactive agility","direction",["P5-T09","P5-T10","P5-T11"],
     [["single_cue_reactive_cut"],["single_cue_reactive_cut","partner_mirror_drill"],["multi_choice_reactive_cut","partner_chase_drill"]]),
    (6,"aerobic_capacity","Aerobic capacity","aerobic",["P6-T01","P6-T02","P6-T03","P6-T04"],
     [["run_walk_intervals","easy_continuous_cycle"],["easy_continuous_run","easy_continuous_cycle"],["long_aerobic_run","easy_continuous_cycle"]]),
    (6,"threshold_capacity","Threshold capacity","threshold",["P6-T06","P6-T07","P6-T08","P6-T12","P6-T13"],
     [["steady_tempo_run"],["threshold_run_intervals","cycling_threshold_intervals"],["threshold_run_intervals","swimming_threshold_intervals"]]),
    (6,"high_intensity_aerobic_power","High-intensity aerobic power","hi_aerobic",["P6-T09","P6-T10","P6-T11"],
     [["short_aerobic_power_intervals"],["long_aerobic_power_intervals","shuttle_aerobic_power_intervals"],["long_aerobic_power_intervals","cycling_aerobic_power_intervals"]]),
    (7,"anaerobic_power","Anaerobic power","anaerobic_power",["P7-T01","P7-T02","P7-T03"],
     [["cycling_sprint_repeats"],["maximal_short_sprint_repeats","cycling_sprint_repeats"],["maximal_short_sprint_repeats","swimming_sprint_repeats"]]),
    (7,"anaerobic_capacity","Anaerobic capacity","anaerobic_capacity",["P7-T04","P7-T05","P7-T06","P7-T07","P7-T08"],
     [["anaerobic_capacity_intervals"],["anaerobic_capacity_intervals","swimming_anaerobic_capacity_set"],["long_sprint_endurance_run","anaerobic_capacity_intervals"]]),
    (7,"repeated_sprint_ability","Repeated-sprint ability","repeat_effort",["P7-T09","P7-T10","P7-T11","P7-T12"],
     [["linear_repeated_sprints"],["linear_repeated_sprints","cod_repeated_sprints"],["cod_repeated_sprints","linear_repeated_sprints"]]),
    (7,"repeated_high_intensity_ability","Repeated high-intensity ability","repeat_effort",["P7-T13","P7-T14","P7-T15"],
     [["repeated_high_intensity_cluster"],["repeated_high_intensity_cluster","sled_push"],["repeated_high_intensity_cluster","cod_repeated_sprints"]]),
    (8,"local_muscular_endurance","Local muscular endurance","capacity",["P8-T01","P8-T02","P8-T03","P8-T04"],
     [["banded_lateral_walk","standing_calf_raise","front_plank"],["walking_lunge","push_up","seated_cable_row"],["walking_lunge","pull_up","push_up"]]),
    (8,"calf_soleus_capacity","Calf–soleus capacity","capacity",["P8-T05","P8-T06","P8-T07","P8-T08"],
     [["standing_calf_raise","seated_calf_raise","tibialis_raise"],["single_leg_calf_raise","seated_calf_raise","bent_knee_soleus_hold"],["single_leg_calf_raise","standing_calf_raise_hold","bent_knee_soleus_hold"]]),
    (8,"hamstring_capacity","Hamstring capacity","capacity",["P8-T09","P8-T10","P8-T11"],
     [["glute_bridge","hamstring_bridge_hold"],["barbell_romanian_deadlift","assisted_nordic_hamstring_curl","hamstring_bridge_hold"],["single_leg_romanian_deadlift","nordic_hamstring_curl","hamstring_bridge_hold"]]),
    (8,"adductor_capacity","Adductor capacity","capacity",["P8-T12","P8-T13"],
     [["adductor_squeeze"],["short_lever_copenhagen_adduction","short_lever_copenhagen_plank"],["copenhagen_adduction","copenhagen_plank"]]),
    (8,"shoulder_capacity","Shoulder capacity","capacity",["P8-T14","P8-T15"],
     [["band_external_rotation_at_side","wall_slide","band_pull_apart"],["side_lying_dumbbell_external_rotation","incline_y_raise","serratus_cable_punch"],["cable_90_90_external_rotation","overhead_carry","scapular_pull_up"]]),
    (8,"trunk_force_transfer","Trunk force transfer","capacity",["P8-T16","P8-T17"],
     [["dead_bug","pallof_press","farmer_s_carry"],["cable_lift","pallof_press_iso_hold","suitcase_carry"],["plank_drag_through","single_arm_front_rack_carry","landmine_rotation"]]),
    (8,"neck_capacity","Neck capacity","isometric_yield",["P8-T18"],
     [["four_direction_cervical_isometrics"],["four_direction_cervical_isometrics"],["four_direction_cervical_isometrics"]]),
    (8,"grip_capacity","Grip capacity","capacity",["P8-T17"],
     [["controlled_hang","farmer_s_carry"],["farmer_s_carry","controlled_hang"],["farmer_s_carry","controlled_hang"]]),
    (9,"performance_preparation","Performance preparation","mobility",["P9-T01","P9-T02","P9-T03","P9-T04","P9-T05","P9-T06","P9-T07","P9-T08","P9-T09","P9-T10"],
     [["easy_mode_specific_raise","world_s_greatest_stretch","front_back_leg_swing"],["easy_mode_specific_raise","inchworm_walkout","lateral_leg_swing"],["easy_mode_specific_raise","world_s_greatest_stretch","progressive_build_up_run"]]),
    (9,"mobility_range_capacity","Mobility/range capacity","mobility",["P9-T11","P9-T12","P9-T13"],
     [["knee_to_wall_ankle_rocks","90_90_hip_switch","open_book_thoracic_rotation"],["deep_squat_pry","cossack_squat","wall_slide_with_lift_off"],["cossack_squat","hip_airplane","wall_slide_with_lift_off"]]),
    (9,"recovery_management","Recovery management","recovery",["P9-T14","P9-T15","P9-T16","P9-T17","P9-T18"],
     [["passive_rest","very_easy_active_cooldown"],["passive_rest","low_impact_recovery_session","optional_foam_rolling"],["passive_rest","low_impact_recovery_session","optional_foam_rolling"]]),
]


LEVELS = ["beginner", "intermediate", "advanced"]
LEVEL_INDEX = {x: i for i, x in enumerate(LEVELS)}

# These combinations do not have a catalogue method that honestly represents
# the requested quality at that athlete level. They are unavailable rather
# than being filled with a biomechanically different exercise.
UNSUPPORTED_CATEGORY_LEVELS = {
    ("overcoming_isometric_force", "beginner"): {
        "prerequisite_category": "yielding_isometric_force",
        "reason": "Overcoming-isometric methods in the catalogue require intermediate supervision and setup competence.",
    },
    ("lateral_power", "beginner"): {
        "prerequisite_category": "lateral_elastic_strength",
        "reason": "No approved beginner method has lateral power as its primary effect.",
    },
    ("lateral_power", "intermediate"): {
        "prerequisite_category": "lateral_elastic_strength",
        "reason": "The approved primary lateral-power method is advanced; intermediate options train lateral elastic capacity instead.",
    },
    ("rotational_power", "beginner"): {
        "prerequisite_category": "trunk_force_transfer",
        "reason": "No approved beginner method has rotational power as its primary effect.",
    },
    ("speed_endurance", "beginner"): {
        "prerequisite_category": "acceleration",
        "reason": "Approved speed-endurance methods require at least intermediate high-speed exposure.",
    },
}

# Conditioning templates select one mode before the model sees candidates.
# Cross-training modes are supplied only when the athlete explicitly permits
# them; they are never treated as the athlete's primary sport mode by default.
MODALITY_OPTIONS = {
    "aerobic_capacity": {
        "beginner": {"running": ["run_walk_intervals"], "cycling": ["easy_continuous_cycle"], "swimming": ["easy_aerobic_swim"], "rowing": ["easy_rower_session"]},
        "intermediate": {"running": ["easy_continuous_run"], "cycling": ["easy_continuous_cycle"], "swimming": ["easy_aerobic_swim"], "rowing": ["easy_rower_session"]},
        "advanced": {"running": ["long_aerobic_run"], "cycling": ["easy_continuous_cycle"], "swimming": ["easy_aerobic_swim"], "rowing": ["easy_rower_session"]},
    },
    "threshold_capacity": {
        "beginner": {"running": ["steady_tempo_run"]},
        "intermediate": {"running": ["threshold_run_intervals"], "cycling": ["cycling_threshold_intervals"], "swimming": ["swimming_threshold_intervals"]},
        "advanced": {"running": ["threshold_run_intervals"], "cycling": ["cycling_threshold_intervals"], "swimming": ["swimming_threshold_intervals"]},
    },
    "high_intensity_aerobic_power": {
        "beginner": {"running": ["short_aerobic_power_intervals"], "field_court": ["short_aerobic_power_intervals"]},
        "intermediate": {"running": ["long_aerobic_power_intervals"], "field_court": ["shuttle_aerobic_power_intervals"], "cycling": ["cycling_aerobic_power_intervals"], "swimming": ["swimming_aerobic_power_intervals"]},
        "advanced": {"running": ["long_aerobic_power_intervals"], "field_court": ["shuttle_aerobic_power_intervals"], "cycling": ["cycling_aerobic_power_intervals"], "swimming": ["swimming_aerobic_power_intervals"]},
    },
    "anaerobic_power": {
        "beginner": {"cycling": ["cycling_sprint_repeats"]},
        "intermediate": {"running": ["maximal_short_sprint_repeats"], "field_court": ["maximal_short_sprint_repeats"], "cycling": ["cycling_sprint_repeats"], "swimming": ["swimming_sprint_repeats"]},
        "advanced": {"running": ["maximal_short_sprint_repeats"], "field_court": ["maximal_short_sprint_repeats"], "cycling": ["cycling_sprint_repeats"], "swimming": ["swimming_sprint_repeats"]},
    },
    "anaerobic_capacity": {
        "beginner": {"running": ["anaerobic_capacity_intervals"], "field_court": ["anaerobic_capacity_intervals"], "cycling": ["anaerobic_capacity_intervals"]},
        "intermediate": {"running": ["anaerobic_capacity_intervals"], "field_court": ["anaerobic_capacity_intervals"], "cycling": ["anaerobic_capacity_intervals"], "swimming": ["swimming_anaerobic_capacity_set"]},
        "advanced": {"running": ["long_sprint_endurance_run", "anaerobic_capacity_intervals"], "field_court": ["anaerobic_capacity_intervals"], "cycling": ["anaerobic_capacity_intervals"], "swimming": ["swimming_anaerobic_capacity_set"]},
    },
    "speed_endurance": {
        "intermediate": {"running": ["short_speed_endurance_run"]},
        "advanced": {"running": ["long_sprint_endurance_run"]},
    },
    "repeated_sprint_ability": {
        "beginner": {"field_court": ["linear_repeated_sprints"]},
        "intermediate": {"field_court": ["linear_repeated_sprints", "cod_repeated_sprints"]},
        "advanced": {"field_court": ["cod_repeated_sprints", "linear_repeated_sprints"]},
    },
    "repeated_high_intensity_ability": {
        "beginner": {"field_court": ["repeated_high_intensity_cluster"]},
        "intermediate": {"field_court": ["repeated_high_intensity_cluster", "sled_push"]},
        "advanced": {"field_court": ["repeated_high_intensity_cluster", "cod_repeated_sprints"]},
    },
}

MODALITY_EXPECTED_MODES = {
    "aerobic_capacity": {"running", "cycling", "swimming"},
    "threshold_capacity": {"running", "cycling", "swimming"},
    "high_intensity_aerobic_power": {"running", "cycling", "swimming", "field_court"},
    "anaerobic_power": {"running", "cycling", "swimming", "field_court"},
    "anaerobic_capacity": {"running", "cycling", "swimming", "field_court"},
    "speed_endurance": {"running"},
    "repeated_sprint_ability": {"field_court"},
    "repeated_high_intensity_ability": {"field_court"},
}

SPORT_MODE_POLICY = {
    "running": "running", "cycling": "cycling", "swimming": "swimming",
    "football": "field_court", "cricket": "field_court", "basketball": "field_court",
    "volleyball": "field_court", "badminton": "field_court", "tennis": "field_court",
    "boxing": "field_court", "mma": "field_court",
}

PROFILE_OVERRIDES = {("adductor_capacity", "beginner"): "isometric_yield"}

PROFILE_REQUIRED_UNITS = {
    "strength": {"repetitions"}, "isometric_yield": {"duration_seconds"},
    "isometric_overcome": {"duration_seconds"}, "eccentric": {"repetitions"},
    "power": {"repetitions"}, "landing": {"contacts", "repetitions"},
    "speed": {"distance_m"}, "direction": {"repetitions", "distance_m"},
    "aerobic": {"duration_seconds", "duration_minutes", "distance_m", "distance_km"},
    "threshold": {"duration_seconds", "duration_minutes", "distance_m"},
    "hi_aerobic": {"duration_seconds", "duration_minutes", "distance_m"},
    "anaerobic_power": {"duration_seconds", "distance_m"},
    "anaerobic_capacity": {"duration_seconds", "distance_m"},
    "repeat_effort": {"distance_m", "duration_seconds", "repetitions"},
    "capacity": {"repetitions", "duration_seconds", "distance_m"},
    "mobility": {"repetitions", "duration_seconds"},
    "recovery": {"duration_seconds", "duration_minutes"},
}

CATEGORY_OBJECTIVE_QUALITY = {
    "yielding_isometric_force": "isometric_force_capacity",
    "overcoming_isometric_force": "isometric_force_capacity",
    "extensive_plyometrics": "reactive_elastic_strength",
    "horizontal_bounding": "horizontal_power",
    "lateral_elastic_strength": "reactive_elastic_strength",
    "planned_change_of_direction": "change_of_direction",
    "performance_preparation": "mobility_preparation",
    "recovery_management": "recovery_capacity",
}

# A missing level or mode is represented honestly. Retrieval follows the named
# prerequisite reference or fails closed; it never silently promotes a novice
# into an advanced method or swaps running, cycling and swimming modalities.
MODE_FALLBACKS = {
    ("threshold_capacity", "beginner", "cycling"): "aerobic_capacity",
    ("threshold_capacity", "beginner", "swimming"): "aerobic_capacity",
    ("high_intensity_aerobic_power", "beginner", "cycling"): "aerobic_capacity",
    ("high_intensity_aerobic_power", "beginner", "swimming"): "aerobic_capacity",
    ("anaerobic_power", "beginner", "running"): "acceleration",
    ("anaerobic_power", "beginner", "field_court"): "acceleration",
    ("anaerobic_power", "beginner", "swimming"): "aerobic_capacity",
    ("anaerobic_capacity", "beginner", "swimming"): "aerobic_capacity",
}


SCENARIO_OVERLAYS = [
    {"code":"general_preparation","applies_to":"all categories","instruction":"Use the full four-week progression. Prioritize technique, tolerance and broad capacity before sport-specific complexity."},
    {"code":"specific_preparation_preseason","applies_to":"all categories","instruction":"Keep the primary method and intensity progression, reduce unrelated accessory work, and make direction/modality resemble the sport demand."},
    {"code":"in_season","applies_to":"all categories","instruction":"Use one familiar exposure weekly where needed; retain meaningful intensity, remove one-third to one-half of development volume, and avoid novelty."},
    {"code":"competition_taper","applies_to":"all categories","instruction":"Use familiar methods only. Retain brief quality exposure in Weeks 1–2, reduce volume materially in Week 3, and use a short primer or omit in Week 4 according to competition proximity."},
    {"code":"congested_competition","applies_to":"all categories","instruction":"Do not run the development progression. Use zero or one low-volume familiar microdose; competition and practice load take priority."},
    {"code":"re_entry_after_clearance","applies_to":"all categories","instruction":"Begin with the beginner Week 1 method and dose regardless of historical level; progress only after two symptom-free, technically acceptable exposures. This is not rehabilitation."},
    {"code":"limited_equipment_home","applies_to":"strength/power/capacity/mobility","instruction":"Use listed bodyweight, band, dumbbell or isometric substitutions that preserve the target quality. Do not replace speed, power or strength with a random fatigue circuit."},
    {"code":"field_court_only","applies_to":"speed/landing/COD/agility/conditioning","instruction":"Use bodyweight, medicine-ball, running and partner methods. Surface, space, footwear and supervision gates remain mandatory."},
    {"code":"road_track_only","applies_to":"speed and running conditioning","instruction":"Use distance- and pace-based options. Maximum velocity requires a safe flat surface; road traffic or poor footing invalidates the session."},
    {"code":"pool_only","applies_to":"aerobic/threshold/anaerobic/recovery","instruction":"Use the corresponding swim modality and preserve the same energy-system objective; specify stroke, distance, rest and pool length."},
    {"code":"minor_16_17","applies_to":"all categories","instruction":"Use conservative level selection, prioritize technique and supervision, and exclude unsupervised specialist overload, assisted sprinting and hazardous setups."},
    {"code":"high_fatigue_or_low_readiness","applies_to":"all categories","instruction":"Confirm the report and screen pain/illness. Reduce sets or replace high-impact/high-speed work with a low-cost familiar method; do not compensate later in the week."},
    {"code":"pain_or_illness","applies_to":"all categories","instruction":"Stop ordinary generation for the affected region or systemic illness. Modify, omit or refer under health policy; never generate rehabilitation or train through pain."},
    {"code":"missed_session","applies_to":"all categories","instruction":"Do not stack the missed session beside another hard exposure. Resume the progression only if spacing and total-load gates pass; otherwise skip it."},
    {"code":"secondary_sport_load","applies_to":"all categories","instruction":"Count secondary-sport practice and competition as external load. Remove duplicative high-intensity or high-impact work before adding another session."},
    {"code":"heat_humidity_altitude","applies_to":"speed/conditioning/preparation/recovery","instruction":"Use environment-adjusted intensity and longer recovery, monitor symptoms, and avoid interpreting slower output as loss of fitness. Heat-illness signs stop the session."},
    {"code":"one_training_day_per_week","applies_to":"all categories","instruction":"Prioritize the highest sport/goal qualities, combine only compatible blocks, and omit low-priority accessories. Do not compress multiple full reference sessions into one exhaustive workout."},
    {"code":"two_training_days_per_week","applies_to":"all categories","instruction":"Distribute the highest-priority qualities across two sessions. Pair speed or power before strength where compatible and keep the second session distinct enough to manage fatigue."},
    {"code":"three_or_more_training_days_per_week","applies_to":"all categories","instruction":"Separate high-cost qualities when possible, alternate demanding and lower-cost days, and count sport practices before allocating additional sessions."},
    {"code":"no_valid_performance_baseline","applies_to":"strength/speed/conditioning","instruction":"Use RPE, RIR, talk test and technical quality fallbacks. Do not fabricate percentages, pace zones, velocity targets or maximal test results."},
    {"code":"travel_or_time_zone_change","applies_to":"all categories","instruction":"Protect sleep opportunity and reduce novel or high-cost work near travel. Use familiar low-volume preparation and adjust the week rather than forcing the original calendar."},
    {"code":"menstrual_symptoms_or_individual_cycle_response","applies_to":"all categories","instruction":"Do not change training from cycle phase alone. Respond to the athlete's confirmed symptoms, readiness and preferences using ordinary modification rules."},
    {"code":"weight_sensitive_sport_context","applies_to":"strength and conditioning","instruction":"Prioritize relative-strength and performance outcomes, limit unnecessary hypertrophy volume, monitor body mass only with consent, and do not prescribe rapid weight loss."},
    {"code":"no_safe_or_valid_template","applies_to":"all categories","instruction":"Return an explicit unable-to-generate result. Do not fill missing content with invented exercises, improvised rehabilitation or unsupported prescriptions."},
]


def week_prescription(profile: str, level: str, week: int) -> dict:
    sets, amount, intensity, recovery = DOSES[profile][level][week - 1]
    return {"sets_or_series": sets, "repetitions_distance_or_duration": amount, "intensity": intensity, "recovery": recovery}


PREPARATION_CODES = {
    "easy_mode_specific_raise", "wall_march", "wall_switch", "a_march",
    "a_skip", "progressive_build_up_run", "snap_down",
}


def sequence_methods(codes: list[str], modes_by_code: dict[str, list[str]] | None = None) -> list[dict]:
    """Create one compact, stable method-option list for the four weeks."""
    first_training_method = next((c for c in codes if c not in PREPARATION_CODES), codes[0])
    result = []
    for code in codes:
        if code in PREPARATION_CODES and code != first_training_method:
            role = "preparation"
        elif code == first_training_method:
            role = "primary_reference"
        else:
            role = "supporting_reference"
        result.append(method(code, role, modes=(modes_by_code or {}).get(code)))
    return result


def modality_methods(mode_options: dict[str, list[str]]) -> list[dict]:
    """Compact modality candidates while retaining one primary per mode."""
    order: list[str] = []
    modes_by_code: dict[str, list[str]] = {}
    primary_codes: set[str] = set()
    for mode_code, codes in mode_options.items():
        if not codes:
            continue
        primary_codes.add(codes[0])
        for code in codes:
            if code not in order:
                order.append(code)
            modes_by_code.setdefault(code, []).append(mode_code)
    return [
        method(code, "primary_reference" if code in primary_codes else "supporting_reference", modes=modes_by_code[code])
        for code in order
    ]


def build_template(phase: int, category: str, name: str, profile: str, source_templates: list[str], level: str, codes: list[str]) -> dict:
    mode_options = MODALITY_OPTIONS.get(category, {}).get(level, {})
    modes_by_code: dict[str, list[str]] = {}
    if mode_options:
        codes = []
        for mode_code, mode_codes in mode_options.items():
            for code in mode_codes:
                if code not in codes:
                    codes.append(code)
                modes_by_code.setdefault(code, []).append(mode_code)
    method_options = modality_methods(mode_options) if mode_options else sequence_methods(codes, modes_by_code)
    dose_profile = PROFILE_OVERRIDES.get((category, level), profile)
    weeks = []
    for w in range(1, 5):
        weeks.append({
            "week": w,
            "intent": ["entry and establish baseline", "accumulate successful exposure", "highest development exposure", "consolidate and reduce fatigue"][w-1],
            "sessions_per_week": 1 if profile in {"threshold","hi_aerobic","anaerobic_power","anaerobic_capacity","repeat_effort","recovery"} else (2 if level != "advanced" else "1-2"),
            "prescription_per_primary_method": week_prescription(dose_profile, level, w),
            "progression_condition": "Complete the planned exposure with acceptable technique/output, no pain or illness, and no material interference with the next key sport session.",
            "regression_condition": "If quality, readiness, symptoms or schedule gate fails, repeat the prior successful week or use the category regression; do not progress automatically.",
        })
    return {
        "template_code": f"P{phase}-{category.upper().replace('_','-')}-{level.upper()}-4W",
        "content_version": 1,
        "status": "research_derived_candidate",
        "phase": phase,
        "category_code": category,
        "name": f"{name} — {level.title()} four-week reference",
        "athlete_level": level,
        "duration_weeks": 4,
        "purpose": f"Give the workout-generation model an exercise-based progression reference for {name.lower()}, not a mandatory athlete program.",
        "source_template_ids": source_templates,
        "applicable_scenarios": ["general_preparation", "specific_preparation_preseason", "in_season", "competition_taper", "congested_competition", "re_entry_after_clearance"],
        "method_options": method_options,
        "selection_policy": {
            "strategy": "single_modality" if mode_options else "quality_methods",
            "required_primary_count": 1,
            "supporting_methods_are_candidates": True,
            "mode_required": bool(mode_options),
            "cross_training_requires_opt_in": bool(mode_options),
            "unresolved_behavior": "fail_closed",
        },
        "selection_rules": {
            "use": "Select methods matching the athlete's sport demand, environment, equipment and level; preserve the category objective and weekly progression shape.",
            "avoid": "Do not include every listed method, invent a method, progress multiple loading variables at once, or use fatigue as proof of effectiveness.",
            "session_order": "Complete relevant preparation first; perform speed, power and high-skill work before fatiguing strength or conditioning; place low-priority capacity work later.",
            "dose_application": "The weekly prescription applies to the primary_reference method. Preparation and supporting references use their own released method-dose compatibility; they must not inherit the primary dose blindly.",
        },
        "weeks": weeks,
        "exercise_progression_policy": "Keep the reference methods stable across four weeks and progress dose or execution quality first. A method change requires the stated progression gate, a compatible substitution, and no new equipment or level conflict.",
        "week_4_policy": "Consolidation/deload by default. It may become an assessment or competition week only when the sport package and athlete schedule explicitly require it.",
        "mandatory_stops": ["pain", "acute illness", "unsafe environment or equipment", "technique or output deterioration beyond the released limit", "unresolved schedule conflict"],
        "ai_use": "Reference for one-call four-week generation. AI may adapt within released method eligibility and dose bounds; it must not copy blindly or exceed constraints.",
    }


def compile_prompt_reference(template: dict, method_names: dict[str, str]) -> str:
    names = ", ".join(method_names[m["method_code"]] for m in template["method_options"])
    weekly = []
    for week in template["weeks"]:
        dose = week["prescription_per_primary_method"]
        weekly.append(
            f"Week {week['week']} ({week['intent']}): primary reference dose "
            f"{dose['sets_or_series']} sets/series × {dose['repetitions_distance_or_duration']} at "
            f"{dose['intensity']}, with {dose['recovery']} recovery"
        )
    return (
        f"{template['name']}. Approved method candidates: {names}. Use this as a flexible exercise-based planning reference: "
        + ". ".join(weekly)
        + ". Progress only after acceptable technique/output, readiness and schedule checks; otherwise repeat or regress. "
          "Week 4 consolidates rather than automatically overloading. Apply dose only to the primary reference method; supporting methods retain their own approved dose."
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with CATALOGUE.open(encoding="utf-8-sig", newline="") as fh:
        catalogue_rows = list(csv.DictReader(fh))
    catalogue = {row["code"]: row for row in catalogue_rows}
    extensions = {
        code: {
            "method_code": code,
            "name": name,
            "method_type": method_type,
            "catalogue_status": "required_catalogue_extension",
            "generator_eligible": False,
            "reason": "Required by a reviewed Phase 1–9 template but absent from the normalized catalogue.",
        }
        for code, (name, method_type) in EXTENSIONS.items()
        if code not in catalogue
    }
    method_names = {code: row["exercise_name"] for code, row in catalogue.items()}
    method_names.update({code: item["name"] for code, item in extensions.items()})

    by_phase: dict[int, list[dict]] = {n: [] for n in range(1, 10)}
    categories = []
    availability = []
    referenced = set()
    for phase, category, name, profile, sources, methods_by_level in CATEGORY_ROWS:
        supported_levels = [level for level in LEVELS if (category, level) not in UNSUPPORTED_CATEGORY_LEVELS]
        categories.append({"phase": phase, "category_code": category, "name": name, "levels": supported_levels, "source_template_ids": sources})
        for level in LEVELS:
            unsupported = UNSUPPORTED_CATEGORY_LEVELS.get((category, level))
            if unsupported:
                availability.append({
                    "category_code": category, "athlete_level": level, "available": False,
                    "template_code": None, **unsupported,
                })
                continue
            codes = methods_by_level[LEVEL_INDEX[level]]
            template = build_template(phase, category, name, profile, sources, level, codes)
            referenced.update(item["method_code"] for item in template["method_options"])
            template["prompt_reference_text"] = compile_prompt_reference(template, method_names)
            by_phase[phase].append(template)
            availability.append({
                "category_code": category, "athlete_level": level, "available": True,
                "template_code": template["template_code"], "prerequisite_category": None,
                "reason": "A level-compatible four-week reference is available.",
            })

    unresolved = sorted(referenced - set(catalogue) - set(extensions))
    if unresolved:
        raise SystemExit(f"Unresolved method codes: {unresolved}")

    level_violations = []
    ineligible_references = []
    dose_violations = []
    modality_violations = []
    objective_violations = []
    duplicates = []
    for templates in by_phase.values():
        for template in templates:
            options = template["method_options"]
            option_codes = [item["method_code"] for item in options]
            if len(option_codes) != len(set(option_codes)):
                duplicates.append(template["template_code"])
            required_units = PROFILE_REQUIRED_UNITS[PROFILE_OVERRIDES.get(
                (template["category_code"], template["athlete_level"]),
                next(row[3] for row in CATEGORY_ROWS if row[1] == template["category_code"]),
            )]
            for item in options:
                row = catalogue[item["method_code"]]
                if LEVEL_INDEX[row["minimum_level"]] > LEVEL_INDEX[template["athlete_level"]]:
                    level_violations.append({"template_code": template["template_code"], "method_code": item["method_code"], "minimum_level": row["minimum_level"]})
                if row["generator_eligible"] != "yes" or row["approval_status"] != "approved":
                    ineligible_references.append({"template_code": template["template_code"], "method_code": item["method_code"]})
                if item["block_role"] == "primary_reference" and not (set(row["dose_units"].split(";")) & required_units):
                    dose_violations.append({"template_code": template["template_code"], "method_code": item["method_code"], "accepted_units": row["dose_units"], "required_any": sorted(required_units)})
            objective = CATEGORY_OBJECTIVE_QUALITY.get(template["category_code"], template["category_code"])
            if not any(
                item["block_role"] == "primary_reference"
                and objective in {catalogue[item["method_code"]]["primary_quality"], *catalogue[item["method_code"]]["secondary_qualities"].split(";")}
                for item in options
            ):
                objective_violations.append({"template_code": template["template_code"], "required_quality": objective})
            if template["selection_policy"]["strategy"] == "single_modality":
                modes = sorted({mode for item in options for mode in item["applicable_modes"]})
                for mode_code in modes:
                    if not any(item["block_role"] == "primary_reference" and mode_code in item["applicable_modes"] for item in options):
                        modality_violations.append({"template_code": template["template_code"], "mode": mode_code, "reason": "no primary candidate"})
                for missing_mode in MODALITY_EXPECTED_MODES[template["category_code"]] - set(modes):
                    if (template["category_code"], template["athlete_level"], missing_mode) not in MODE_FALLBACKS:
                        modality_violations.append({"template_code": template["template_code"], "mode": missing_mode, "reason": "no candidate or explicit fallback"})

    validation_errors = level_violations + ineligible_references + dose_violations + modality_violations + objective_violations + duplicates
    if validation_errors:
        raise SystemExit("Template integrity validation failed:\n" + json.dumps({
            "level_violations": level_violations,
            "ineligible_references": ineligible_references,
            "dose_violations": dose_violations,
            "modality_violations": modality_violations,
            "objective_violations": objective_violations,
            "duplicate_method_lists": duplicates,
        }, indent=2))

    package = {
        "schema_version": "1.0.0",
        "package_code": "runlete_exercise_reference_templates_4w_v1",
        "status": "research_derived_candidate_not_published",
        "duration_weeks": 4,
        "levels": LEVELS,
        "category_count": len(CATEGORY_ROWS),
        "template_count": sum(len(x) for x in by_phase.values()),
        "phases": [{"phase": n, "file": f"phase_{n:02d}_exercise_templates.json", "template_count": len(by_phase[n])} for n in range(1,10)],
        "scenario_overlays_file": "scenario_overlays.json",
        "availability_file": "category_level_availability.json",
        "sport_mode_policy_file": "sport_mode_policy.json",
        "integrity_report_file": "template_integrity_report.json",
        "catalogue_extension_file": "required_catalogue_extensions.json",
        "template_schema_file": "exercise_template.schema.json",
        "design_boundary": "These are exercise-based references for AI planning, not fixed prescriptions and not a production content release.",
    }
    (OUT / "manifest.json").write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n")
    (OUT / "scenario_overlays.json").write_text(json.dumps({"schema_version":"1.0.0","overlays":SCENARIO_OVERLAYS}, indent=2, ensure_ascii=False) + "\n")
    (OUT / "required_catalogue_extensions.json").write_text(json.dumps({"schema_version":"1.0.0","methods":list(extensions.values())}, indent=2, ensure_ascii=False) + "\n")
    (OUT / "category_coverage.json").write_text(json.dumps({"schema_version":"1.0.0","categories":categories}, indent=2, ensure_ascii=False) + "\n")
    (OUT / "category_level_availability.json").write_text(json.dumps({"schema_version":"1.0.0","records":availability}, indent=2, ensure_ascii=False) + "\n")
    sport_policies = [
        {"sport_code": sport_code, "primary_mode": mode, "cross_training_requires_opt_in": True}
        for sport_code, mode in SPORT_MODE_POLICY.items()
    ]
    mode_fallbacks = [
        {"category_code": category, "athlete_level": level, "requested_mode": mode, "fallback_category": fallback, "automatic": False}
        for (category, level, mode), fallback in MODE_FALLBACKS.items()
    ]
    (OUT / "sport_mode_policy.json").write_text(json.dumps({"schema_version":"1.0.0","policies":sport_policies,"missing_mode_fallbacks":mode_fallbacks}, indent=2, ensure_ascii=False) + "\n")

    # Reconcile every Phase 01–09 source template family. Families not cited by
    # one category template remain accounted for as scenario/dose variants;
    # they are retained in source research and must be considered during the
    # later PostgreSQL import rather than silently discarded.
    direct_ids = {source for templates in by_phase.values() for template in templates for source in template["source_template_ids"]}
    reconciliation = []
    for matrix in sorted(ROOT.glob("Research materials/quality development/phase_*/phase_*_template_matrix.csv")):
        with matrix.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                source_id = (row.get("template_id") or row.get("template_code") or "").strip()
                phase_match = matrix.parent.name.split("_")[1]
                reconciliation.append({
                    "source_template_id": source_id,
                    "source_phase": int(phase_match),
                    "source_file": str(matrix.relative_to(ROOT)),
                    "source_name_or_objective": row.get("name") or row.get("objective") or "",
                    "disposition": "direct_four_week_reference_input" if source_id in direct_ids else "retained_scenario_or_specialist_variant",
                    "reason": "Cited directly by one or more category templates." if source_id in direct_ids else "A maintenance, congestion, taper, specialist or modality variant represented through scenario overlays or retained for later method-specific release work.",
                })
    (OUT / "source_template_reconciliation.json").write_text(json.dumps({"schema_version":"1.0.0","records":reconciliation}, indent=2, ensure_ascii=False) + "\n")
    for n, templates in by_phase.items():
        (OUT / f"phase_{n:02d}_exercise_templates.json").write_text(json.dumps({"schema_version":"1.0.0","phase":n,"templates":templates}, indent=2, ensure_ascii=False) + "\n")
    retrieval = []
    for n, templates in by_phase.items():
        for template in templates:
            retrieval.append({
                "category_code": template["category_code"],
                "athlete_level": template["athlete_level"],
                "template_code": template["template_code"],
                "file": f"phase_{n:02d}_exercise_templates.json",
                "phase": n,
                "source_template_ids": template["source_template_ids"],
            })
    (OUT / "retrieval_index.json").write_text(json.dumps({"schema_version":"1.0.0","records":retrieval}, indent=2, ensure_ascii=False) + "\n")

    report = {
        "catalogue_rows": len(catalogue),
        "existing_catalogue_methods_referenced": len(referenced & set(catalogue)),
        "required_extension_methods_referenced": len(referenced & set(extensions)),
        "unresolved_method_references": unresolved,
        "categories": len(CATEGORY_ROWS),
        "templates": sum(len(x) for x in by_phase.values()),
        "four_week_records": sum(len(x) * 4 for x in by_phase.values()),
        "levels_per_category": 3,
        "scenario_overlays": len(SCENARIO_OVERLAYS),
        "unsupported_category_levels": len(UNSUPPORTED_CATEGORY_LEVELS),
        "modality_guarded_templates": sum(t["selection_policy"]["strategy"] == "single_modality" for templates in by_phase.values() for t in templates),
        "level_violations": level_violations,
        "ineligible_method_references": ineligible_references,
        "dose_compatibility_violations": dose_violations,
        "modality_violations": modality_violations,
        "objective_violations": objective_violations,
        "duplicate_method_lists": duplicates,
    }
    (OUT / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    (OUT / "template_integrity_report.json").write_text(json.dumps({
        "schema_version": "1.0.0", "status": "passed", "report": report,
        "unsupported_references": [dict(category_code=category, athlete_level=level, **details) for (category, level), details in UNSUPPORTED_CATEGORY_LEVELS.items()],
    }, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
