from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "pylometrics"
FULL_EXTRACTION_PATH = SOURCE_DIR / "Plyometrics_Full_Extraction.md"
EXERCISES_JSON_PATH = SOURCE_DIR / "exercises.json"
EXERCISES_CSV_PATH = SOURCE_DIR / "exercises.csv"
EXERCISES_MD_PATH = SOURCE_DIR / "exercises.md"

SOURCE_PACK_ID = "plyometrics_complete_extraction_v1"
INGESTION_METHOD = "local_plyometrics_extraction_normalized_v1"


CHAPTERS: List[Dict[str, Any]] = [
    {
        "chapter": 1,
        "title": "Muscular Actions, Sport Performance, and Plyometric Training",
        "topics": ["eccentric_strength", "isometric_strength", "concentric_strength", "sport_power"],
        "summary": "Plyometric performance depends on coordinated eccentric loading, brief coupling, and explosive concentric action. Strength, balance, and trunk control support the expression of force in sport.",
    },
    {
        "chapter": 2,
        "title": "Anatomy and Physiology of Plyometrics",
        "topics": ["stretch_shortening_cycle", "muscle_groups", "center_of_gravity", "force_transfer"],
        "summary": "Lower-body force, trunk stiffness, upper-body contribution, center-of-gravity control, and efficient stretch-shortening cycle mechanics determine the quality of plyometric movement.",
    },
    {
        "chapter": 3,
        "title": "How Plyometrics Works",
        "topics": ["resistance_training", "depth_jumps", "vertical_jump_mechanics", "readiness"],
        "summary": "Plyometrics works best when the athlete has enough strength and movement skill to tolerate rapid loading and produce force quickly without losing landing quality.",
    },
    {
        "chapter": 4,
        "title": "Plyometric Training and Young Athletes",
        "topics": ["youth_training", "movement_education", "progression", "volume_recovery"],
        "summary": "Youth plyometrics should begin as low-intensity movement education, develop fundamental patterns, and progress only after technical control and recovery are adequate.",
    },
    {
        "chapter": 5,
        "title": "Plyometric and Neuromuscular Training for Female Athletes",
        "topics": ["acl_risk", "trunk_control", "landing_mechanics", "neuromuscular_training"],
        "summary": "Female athletes may need targeted trunk, hip, knee, and landing-control training to reduce valgus collapse, quadriceps dominance, and ACL risk factors.",
    },
    {
        "chapter": 6,
        "title": "Plyometric Training for Injury Rehabilitation",
        "topics": ["rehabilitation", "return_to_sport", "pain_response", "progression"],
        "summary": "Rehab plyometrics should progress frequency, intensity, volume, and recovery only when pain, swelling, tissue response, and technique remain controlled.",
    },
    {
        "chapter": 7,
        "title": "Strength and Power Assessment for Plyometric Training",
        "topics": ["assessment", "tuck_jump_assessment", "functional_tests", "screening"],
        "summary": "Assessment should identify strength, power, landing, asymmetry, and high-risk movement faults before selecting plyometric intensity and volume.",
    },
    {
        "chapter": 8,
        "title": "Introduction of a Plyometric Training Program",
        "topics": ["program_design", "equipment", "warmup", "volume", "frequency", "recovery", "landing"],
        "summary": "Program design should match age, training background, cycle timing, equipment, intensity, foot-contact volume, recovery needs, and landing mechanics.",
    },
    {
        "chapter": 9,
        "title": "Essential Plyometric Exercises",
        "topics": ["exercise_library", "jumps", "depth_jumps", "box_drills", "bounding", "medicine_ball"],
        "summary": "Exercises are organized by jump family, intensity, equipment, sport transfer, start position, execution, and sample program use.",
    },
    {
        "chapter": 10,
        "title": "Plyometric Training in a Comprehensive Conditioning Program",
        "topics": ["integrative_training", "complex_training", "resistance_training", "interval_training"],
        "summary": "Plyometrics can be integrated with strength, sprint, interval, and circuit training, but complex pairings are best for experienced athletes with adequate strength and recovery.",
    },
    {
        "chapter": 11,
        "title": "Sport-Specific Plyometric Training Programs",
        "topics": ["needs_analysis", "sport_specific_planning", "season_timing", "sample_programs"],
        "summary": "Sport-specific plyometric plans start with athlete context, needs analysis, tests, time frame, and exercise selection aligned to sport demands.",
    },
]


PROGRAMMING_RULES: List[Dict[str, Any]] = [
    {
        "id": "plyo_rule_begin_with_low_intensity",
        "title": "Begin Plyometrics With Low-Intensity Skill Work",
        "category": "progression",
        "applies_to": ["beginner", "youth", "return_to_training", "plyometrics"],
        "summary": "Beginners should start with low-intensity jumps, skips, landing practice, and simple footwork before progressing to higher-force drills.",
        "rule_text": "Use low-intensity preparatory drills until the athlete can land softly, control body position, and repeat clean efforts without fatigue-driven technique loss.",
        "recommended_focus": ["movement_quality", "landing_mechanics", "low_impact_jump_training"],
        "contraindications": ["poor_landing_control", "unresolved_pain"],
    },
    {
        "id": "plyo_rule_landing_quality_gate",
        "title": "Landing Quality Gates Plyometric Intensity",
        "category": "safety",
        "applies_to": ["plyometrics", "jump_training", "return_to_sport"],
        "summary": "Do not progress jump intensity when the athlete lands stiff-legged, collapses inward at the knee, cannot absorb force, or shows major side-to-side asymmetry.",
        "rule_text": "Require soft forefoot-to-whole-foot landing, hip/knee/ankle flexion, knee tracking, balanced foot pressure, and control in two-leg and single-leg landings.",
        "recommended_focus": ["drop_and_freeze", "jump_to_box", "single_leg_control", "eccentric_strength"],
        "contraindications": ["knee_valgus", "quadriceps_dominance", "ligament_dominance"],
    },
    {
        "id": "plyo_rule_foot_contact_volume_by_phase",
        "title": "Use Foot Contacts To Control Jump Volume",
        "category": "volume",
        "applies_to": ["plyometrics", "program_design", "season_phase"],
        "summary": "Lower-body jump volume should be counted as foot contacts and adjusted by athlete level and season phase.",
        "rule_text": "Off-season: beginners 60-100 contacts, intermediate 100-150, advanced 150-250. Pre-season: beginners 100-250, intermediate 150-300, advanced 150-450. In-season volume depends on sport and competition load; championship phases favor recovery.",
        "parameters": {
            "off_season": {"beginner": "60-100", "intermediate": "100-150", "advanced": "150-250"},
            "pre_season": {"beginner": "100-250", "intermediate": "150-300", "advanced": "150-450"},
            "in_season": "sport_dependent",
            "championship": "recovery_only",
        },
        "recommended_focus": ["volume_tracking", "season_planning"],
        "contraindications": ["untracked_jump_load", "fatigue"],
    },
    {
        "id": "plyo_rule_48_72_hour_lower_body_recovery",
        "title": "Allow 48 To 72 Hours Between Hard Lower-Body Plyometric Sessions",
        "category": "recovery",
        "applies_to": ["lower_body_plyometrics", "jump_training", "bounding", "depth_jumps"],
        "summary": "High-quality lower-body plyometric work generally needs two to three days of recovery before another hard stimulus.",
        "rule_text": "Separate intense lower-body jump, hop, depth-jump, and bounding sessions by 48-72 hours unless the work is low-intensity warm-up movement.",
        "recommended_focus": ["recovery", "quality_efforts", "load_spacing"],
        "contraindications": ["daily_high_intensity_plyometrics", "soreness", "pain"],
    },
    {
        "id": "plyo_rule_power_rest_ratio",
        "title": "Use Long Rest For Power Plyometrics",
        "category": "recovery",
        "applies_to": ["power", "reactive_strength", "high_intensity_plyometrics"],
        "summary": "Power-focused plyometrics require enough rest to preserve speed, height, distance, and landing quality.",
        "rule_text": "Use roughly 1:5 to 1:10 work-to-rest for power work. Short sets may need 45-60 seconds or more depending on intensity and athlete readiness.",
        "recommended_focus": ["quality", "maximal_effort", "fresh_reps"],
        "contraindications": ["conditioning_fatigue", "rushed_rest"],
    },
    {
        "id": "plyo_rule_plyos_before_fatigue",
        "title": "Place Plyometrics Before Fatiguing Training",
        "category": "session_order",
        "applies_to": ["plyometrics", "strength_training", "sport_practice"],
        "summary": "High-quality plyometrics should happen while the athlete is fresh, not after heavy fatigue or hard skill practice.",
        "rule_text": "Place plyometric skill, speed, and power drills early in the session after warm-up. Avoid high-volume or high-intensity plyometrics after hard sport practice.",
        "recommended_focus": ["warmup", "skill_quality", "speed_power"],
        "contraindications": ["post_practice_fatigue", "end_of_session_max_jumps"],
    },
    {
        "id": "plyo_rule_warmup_specificity",
        "title": "Use Specific Movement Warm-Ups Before Plyometrics",
        "category": "warmup",
        "applies_to": ["plyometrics", "speed", "jump_training"],
        "summary": "Warm-ups should raise temperature and rehearse movement patterns without becoming high-intensity conditioning.",
        "rule_text": "Use marching, jogging, ankling, skipping, disassociation, and low-intensity movement drills over short distances with walk-back recovery.",
        "recommended_focus": ["marching_drills", "skipping", "ankling", "movement_rehearsal"],
        "contraindications": ["fatiguing_warmup", "cold_start_depth_jumps"],
    },
    {
        "id": "plyo_rule_cycle_length",
        "title": "Use Four To Six Week Plyometric Learning Blocks",
        "category": "periodization",
        "applies_to": ["beginner", "intermediate", "macro_plan", "block_planning"],
        "summary": "Four to six weeks is a practical minimum to teach and reassess plyometric mechanics before intensifying.",
        "rule_text": "Build initial plyometric blocks around skill development and reassessment. If time allows, use 12-18 week off-season/pre-season progressions.",
        "recommended_focus": ["foundation_block", "reassessment", "gradual_progression"],
        "contraindications": ["rapid_jump_intensity_progression"],
    },
    {
        "id": "plyo_rule_strength_base_for_high_intensity",
        "title": "Require Strength Base For High-Intensity Plyometrics",
        "category": "readiness",
        "applies_to": ["depth_jumps", "single_leg_hops", "complex_training", "weighted_jumps"],
        "summary": "Higher-intensity plyometrics require adequate strength and landing control because impact forces rise quickly.",
        "rule_text": "Keep intensity low to moderate until the athlete demonstrates functional strength, stable landing mechanics, and repeatable jump quality.",
        "recommended_focus": ["resistance_training", "eccentric_strength", "jump_and_freeze"],
        "contraindications": ["weak_landing", "poor_strength_base", "large_heavy_beginner"],
    },
    {
        "id": "plyo_rule_weighted_jumps_advanced_only",
        "title": "Weighted Jumps Are Advanced Only",
        "category": "safety",
        "applies_to": ["weighted_jumps", "advanced", "elite"],
        "summary": "Added load in jumps should be reserved for advanced athletes after a long preparation period.",
        "rule_text": "Do not prescribe weighted vests, belts, bands, or heavy loaded jumps to beginners. Use added load cautiously and sparingly with experienced athletes.",
        "recommended_focus": ["bodyweight_first", "technical_quality", "low_frequency"],
        "contraindications": ["beginner", "joint_pain", "poor_landing_mechanics"],
    },
    {
        "id": "plyo_rule_rehab_progress_by_response",
        "title": "In Rehab, Progress Only With Good Tissue Response",
        "category": "rehabilitation",
        "applies_to": ["return_to_sport", "injury_rehab", "pain"],
        "summary": "Rehab plyometrics should progress only when pain, swelling, movement quality, and next-day response remain acceptable.",
        "rule_text": "If joint pain, swelling, or poor mechanics appears, reduce volume or intensity to the last tolerated level and rebuild gradually.",
        "recommended_focus": ["low_intensity_high_control", "pain_monitoring", "volume_before_intensity"],
        "contraindications": ["worsening_pain", "swelling", "poor_control"],
    },
    {
        "id": "plyo_rule_complex_training_advanced",
        "title": "Complex Training Requires Experience",
        "category": "complex_training",
        "applies_to": ["advanced", "strength_power", "short_term_power_sports"],
        "summary": "Pairing heavy resistance work with plyometrics can be useful for advanced power athletes but should not be used as a beginner teaching method.",
        "rule_text": "Use complex training only after a basic strength phase. Pair one or two major lifts with compatible low-volume plyometrics and avoid fatigue.",
        "recommended_focus": ["squat_to_hurdle_hop", "bench_to_power_drop", "low_plyo_volume"],
        "contraindications": ["beginner", "poor_lift_technique", "fatigue"],
    },
    {
        "id": "plyo_rule_in_season_maintenance",
        "title": "Reduce Plyometric Load In-Season Unless The Sport Schedule Allows It",
        "category": "season_phase",
        "applies_to": ["in_season", "competition_week", "jump_sports", "court_sports"],
        "summary": "In-season plyometrics should maintain power without adding excessive soreness or impact load around matches.",
        "rule_text": "Use lower volume, moderate intensity, and recovery-focused work during heavy competition periods. Keep hard plyometrics far from match day.",
        "recommended_focus": ["power_maintenance", "landing_quality", "low_volume"],
        "contraindications": ["three_game_week", "travel_fatigue", "high_soreness"],
    },
]


TRAINING_PRINCIPLES: List[Dict[str, Any]] = [
    {
        "id": "plyo_principle_stretch_shortening_cycle",
        "title": "Stretch-Shortening Cycle Drives Plyometric Transfer",
        "domain": "plyometrics",
        "topics": ["eccentric", "coupling", "concentric", "reactive_strength"],
        "summary": "True plyometric work uses rapid eccentric loading, a short transition, and explosive concentric action to improve reactive power.",
    },
    {
        "id": "plyo_principle_quality_over_quantity",
        "title": "Plyometric Quality Matters More Than More Reps",
        "domain": "plyometrics",
        "topics": ["quality", "fatigue", "safety"],
        "summary": "Adding extra jumps after a workout feels easy can reduce quality and increase injury risk; future sessions should be adjusted instead.",
    },
    {
        "id": "plyo_principle_specificity",
        "title": "Plyometric Selection Should Match Sport Demands",
        "domain": "sport_specific_training",
        "topics": ["needs_analysis", "movement_direction", "energy_systems"],
        "summary": "Exercise choice should reflect sport direction, jump/throw demands, positions, energy-system needs, competition timing, and athlete limitations.",
    },
    {
        "id": "plyo_principle_integrative_training",
        "title": "Plyometrics Works Best Inside A Complete Training System",
        "domain": "program_design",
        "topics": ["strength_training", "sprint_training", "conditioning"],
        "summary": "Plyometrics should complement strength, sprint, interval, mobility, recovery, and sport practice rather than replace them.",
    },
    {
        "id": "plyo_principle_landing_prevents_injury_and_enables_power",
        "title": "Landing Mechanics Protect The Athlete And Set Up Takeoff",
        "domain": "movement_quality",
        "topics": ["landing", "knee", "hip", "ankle"],
        "summary": "Soft, aligned, controlled landings reduce joint stress and create a better position for the next explosive effort.",
    },
    {
        "id": "plyo_principle_upper_body_plyometrics",
        "title": "Medicine Ball And Push-Up Plyometrics Train Upper-Body Power",
        "domain": "upper_body_power",
        "topics": ["medicine_ball", "throwing", "shoulder", "trunk"],
        "summary": "Upper-body plyometrics can develop rapid force for throwing, striking, swimming, contact sports, and trunk-to-arm transfer.",
    },
]


READINESS_RULES: List[Dict[str, Any]] = [
    {
        "id": "plyo_ready_jump_and_freeze",
        "title": "Jump And Freeze Landing Control",
        "category": "landing_assessment",
        "summary": "Use two-leg and single-leg jump-and-freeze tasks to check whether the athlete can absorb force without valgus collapse, stiffness, or loss of balance.",
        "pass_criteria": ["soft_landing", "knee_tracks_over_foot", "balanced_trunk", "no_pain", "no_major_asymmetry"],
        "fail_action": "Use low-intensity landing drills, strength work, and balance before high-intensity plyometrics.",
    },
    {
        "id": "plyo_ready_functional_strength",
        "title": "Functional Strength Before High Impact",
        "category": "strength_assessment",
        "summary": "High-intensity plyometrics should wait until the athlete demonstrates sufficient lower-body strength and eccentric control.",
        "pass_criteria": ["stable_squat", "stable_lunge", "controlled_single_leg_task", "no_joint_response"],
        "fail_action": "Keep plyometric work low to moderate and prioritize strength development.",
    },
    {
        "id": "plyo_ready_5_5_5_squat",
        "title": "Five Reps In Five Seconds Squat Check",
        "category": "power_readiness",
        "summary": "A 60 percent bodyweight squat load performed for five reps in five seconds can indicate whether plyometric intensity should remain low-moderate or progress.",
        "pass_criteria": ["five_reps", "five_seconds", "clean_depth", "stable_knees", "no_pain"],
        "fail_action": "Emphasize resistance training and lower-intensity plyometrics.",
    },
    {
        "id": "plyo_ready_no_adverse_response",
        "title": "No Pain Or Swelling Response",
        "category": "rehab_readiness",
        "summary": "Progress only if the athlete has no worsening pain, swelling, or next-day joint response after the current plyometric dose.",
        "pass_criteria": ["no_worsening_pain", "no_swelling", "normal_movement_next_day"],
        "fail_action": "Return to prior tolerated volume or intensity.",
    },
]


BENCHMARK_TESTS: List[Dict[str, Any]] = [
    {
        "id": "plyo_test_tuck_jump_assessment",
        "name": "Tuck Jump Assessment",
        "category": "movement_screen",
        "measures": ["landing_mechanics", "fatigue_response", "knee_valgus", "trunk_control"],
        "usage": "Screen repeated-jump mechanics and identify neuromuscular deficits before or during plyometric training.",
    },
    {
        "id": "plyo_test_depth_jump",
        "name": "Depth Jump Test",
        "category": "reactive_power",
        "measures": ["reactive_strength", "landing_absorption", "vertical_power"],
        "usage": "Assess readiness and response to depth-jump style reactive loading.",
    },
    {
        "id": "plyo_test_cutting",
        "name": "Cutting Test",
        "category": "change_of_direction",
        "measures": ["deceleration", "lateral_control", "knee_position"],
        "usage": "Assess return-to-sport cutting control and sport-specific change-of-direction mechanics.",
    },
    {
        "id": "plyo_test_modified_agility_t",
        "name": "Modified Agility T-Test",
        "category": "agility",
        "measures": ["acceleration", "lateral_movement", "backpedal", "change_of_direction"],
        "usage": "Track agility progress and compare sport-readiness across training blocks.",
    },
    {
        "id": "plyo_test_single_leg_hop_distance",
        "name": "Single-Leg Hop Distance Tests",
        "category": "single_leg_power",
        "measures": ["single_leg_power", "asymmetry", "landing_control"],
        "usage": "Compare left-right power and control in return-to-sport or advanced plyometric progression.",
    },
    {
        "id": "plyo_test_hexagon_drill",
        "name": "Hexagon Drill",
        "category": "footwork",
        "measures": ["quick_feet", "multidirectional_control", "reactivity"],
        "usage": "Assess low-intensity multidirectional footwork and agility readiness.",
    },
    {
        "id": "plyo_test_jump_and_reach",
        "name": "Jump-And-Reach Test",
        "category": "vertical_power",
        "measures": ["vertical_jump", "arm_swing", "takeoff_power"],
        "usage": "Track vertical jump progress in court, jumping, and swimming examples.",
    },
    {
        "id": "plyo_test_standing_triple_jump",
        "name": "Standing Triple Jump",
        "category": "horizontal_power",
        "measures": ["horizontal_power", "elastic_sequence", "landing_control"],
        "usage": "Assess advanced horizontal power and track/jump transfer.",
    },
    {
        "id": "plyo_test_flying_30",
        "name": "Flying 30-Meter Sprint",
        "category": "speed",
        "measures": ["max_velocity", "sprint_transfer"],
        "usage": "Use with track and field or speed-development blocks to monitor sprint performance.",
    },
]


INJURY_MODIFICATIONS: List[Dict[str, Any]] = [
    {
        "id": "plyo_injury_knee_acl_risk",
        "title": "Knee Or ACL Risk Plyometric Modification",
        "injury_area": "knee",
        "summary": "Avoid high-volume, high-impact, single-leg, and depth-jump work when knee control, pain, or swelling is not stable.",
        "recommended_regressions": ["drop_and_freeze", "jump_to_box", "low_box_step_off", "lateral_jump_and_hold"],
        "blocked_patterns": ["high_depth_jump", "fatigued_jump_circuit", "single_leg_high_impact"],
    },
    {
        "id": "plyo_injury_ankle_achilles",
        "title": "Ankle Or Achilles Plyometric Modification",
        "injury_area": "ankle_achilles",
        "summary": "Reduce repeated elastic contacts and progress ankle hops, bounding, and depth jumps only after pain-free calf capacity and landing control.",
        "recommended_regressions": ["two_foot_ankle_hop_low_volume", "marching_drill", "jump_to_box"],
        "blocked_patterns": ["long_bounding", "high_hurdle_hops", "single_leg_hops"],
    },
    {
        "id": "plyo_injury_shoulder",
        "title": "Shoulder Plyometric Modification",
        "injury_area": "shoulder",
        "summary": "Use low-load medicine ball drills and avoid aggressive catching, power drops, handstand depth jumps, and high-speed overhead throws when shoulder symptoms exist.",
        "recommended_regressions": ["chest_pass_light", "trunk_rotation_light", "front_toss_light"],
        "blocked_patterns": ["power_drop", "handstand_depth_jump", "max_overhead_throw"],
    },
    {
        "id": "plyo_injury_return_to_sport",
        "title": "Return-To-Sport Plyometric Progression",
        "injury_area": "return_to_sport",
        "summary": "Progress from low-intensity high-control contacts to higher-intensity lower-volume contacts only after stable tissue response.",
        "recommended_regressions": ["low_intensity_hops", "landing_hold", "submaximal_bounds"],
        "blocked_patterns": ["competition_like_high_intensity_before_control"],
    },
    {
        "id": "plyo_injury_large_heavy_beginner",
        "title": "Large Or Heavy Beginner Impact Management",
        "injury_area": "load_management",
        "summary": "Large or heavy beginners should use double-leg, low-intensity plyometrics for longer before progressing to single-leg, depth, or complex drills.",
        "recommended_regressions": ["double_leg_low_contacts", "box_jump_up_not_down", "skipping_drills"],
        "blocked_patterns": ["single_leg_depth_jump", "weighted_jump", "high_box_drop"],
    },
]


SPORT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "plyo_template_football_offseason",
        "title": "Football Off-Season Plyometric Template",
        "sport": "football",
        "duration_weeks": 12,
        "summary": "Build work capacity, movement skill, lower-body power, and position-appropriate footwork across three four-week cycles.",
        "phase_focus": ["foundation", "progression", "performance"],
        "recommended_categories": ["jumps_in_place", "standing_jumps", "multiple_hops_and_jumps", "box_drills", "medicine_ball_exercises"],
    },
    {
        "id": "plyo_template_basketball_preseason",
        "title": "Basketball Pre-Season Plyometric Template",
        "sport": "basketball",
        "duration_weeks": 4,
        "summary": "Emphasize vertical jump, landing control, rim/reach drills, lateral movement, and recovery before the competitive season.",
        "phase_focus": ["preparation", "progression", "performance"],
        "recommended_categories": ["jumps_in_place", "standing_jumps", "multiple_hops_and_jumps", "depth_jumps", "medicine_ball_exercises"],
    },
    {
        "id": "plyo_template_soccer_summer",
        "title": "Soccer Twelve-Week Plyometric Template",
        "sport": "soccer",
        "duration_weeks": 12,
        "summary": "Develop trunk strength, lower-body power, speed, agility, and body control with a gradual shift from foundation to sport-specific work.",
        "phase_focus": ["general_strength", "power_development", "sport_specific_speed"],
        "recommended_categories": ["bounding", "multiple_hops_and_jumps", "standing_jumps", "box_drills"],
    },
    {
        "id": "plyo_template_volleyball_jump_landing",
        "title": "Volleyball Jump And Landing Template",
        "sport": "volleyball",
        "duration_weeks": 12,
        "summary": "Improve jump height, landing mechanics, core strength, and knee-friendly control for repeated jumping demands.",
        "phase_focus": ["landing_retraining", "vertical_power", "power_maintenance"],
        "recommended_categories": ["jumps_in_place", "standing_jumps", "depth_jumps", "box_drills", "medicine_ball_exercises"],
    },
    {
        "id": "plyo_template_baseball_spring_prep",
        "title": "Baseball Spring Preparation Plyometric Template",
        "sport": "baseball",
        "duration_weeks": 6,
        "summary": "Use short preparation windows to emphasize trunk rotation, throwing power, lower-body force transfer, and complex training where qualified.",
        "phase_focus": ["complex_training", "rotational_power", "throwing_preparation"],
        "recommended_categories": ["medicine_ball_exercises", "standing_jumps", "box_drills", "bounding"],
    },
    {
        "id": "plyo_template_tennis_youth_development",
        "title": "Tennis Youth Development Plyometric Template",
        "sport": "tennis",
        "duration_weeks": 6,
        "summary": "For younger athletes, prioritize movement skill, low-intensity footwork, trunk rotation, and progressive strength before higher-load power work.",
        "phase_focus": ["core_strength", "footwork", "rotation", "progression"],
        "recommended_categories": ["jumps_in_place", "multiple_hops_and_jumps", "box_drills", "medicine_ball_exercises"],
    },
    {
        "id": "plyo_template_mma_weekly_power",
        "title": "MMA Weekly Ballistic Power Template",
        "sport": "mixed_martial_arts",
        "duration_weeks": 4,
        "summary": "Use one high-quality weekly plyometric exposure for mature athletes to develop kicking, rotational, and whole-body ballistic power.",
        "phase_focus": ["max_recovery", "ballistic_power", "knee_history_management"],
        "recommended_categories": ["multiple_hops_and_jumps", "depth_jumps", "medicine_ball_exercises"],
    },
    {
        "id": "plyo_template_swimming_upper_power",
        "title": "Swimming Upper-Body Power Template",
        "sport": "swimming",
        "duration_weeks": 8,
        "summary": "Use medicine ball and upper-body power work to improve shoulder/trunk force transfer while respecting high swim-training volume.",
        "phase_focus": ["shoulder_strength", "upper_body_power", "pool_schedule_integration"],
        "recommended_categories": ["medicine_ball_exercises", "standing_jumps"],
    },
    {
        "id": "plyo_template_long_jump_linear_power",
        "title": "Long Jump Linear Power Template",
        "sport": "track_and_field_jumps",
        "duration_weeks": 4,
        "summary": "Prioritize linear jump power, bounding, sprint transfer, and high-quality recovery for advanced track jumpers.",
        "phase_focus": ["linear_power", "horizontal_elasticity", "sprint_transfer"],
        "recommended_categories": ["standing_jumps", "multiple_hops_and_jumps", "bounding"],
    },
]


CATEGORY_PROFILES: Dict[str, Dict[str, Any]] = {
    "jumps_in_place": {
        "patterns": ["vertical_jump", "repeated_jump", "ankle_stiffness"],
        "qualities": ["reactive_strength", "elastic_stiffness", "coordination"],
        "primary": ["quadriceps", "glutes", "calves"],
        "secondary": ["hamstrings", "trunk"],
    },
    "standing_jumps": {
        "patterns": ["horizontal_power", "vertical_power", "takeoff"],
        "qualities": ["explosive_power", "acceleration", "jump_power"],
        "primary": ["quadriceps", "glutes", "hamstrings", "calves"],
        "secondary": ["trunk", "shoulders"],
    },
    "multiple_hops_and_jumps": {
        "patterns": ["repeated_jump", "elastic_reactivity", "short_ground_contact"],
        "qualities": ["reactive_strength", "speed_power", "elastic_endurance"],
        "primary": ["calves", "quadriceps", "glutes", "hamstrings"],
        "secondary": ["trunk", "hip_stabilizers"],
    },
    "depth_jumps": {
        "patterns": ["landing", "depth_jump", "reactive_takeoff"],
        "qualities": ["reactive_strength", "eccentric_strength", "landing_mechanics"],
        "primary": ["quadriceps", "glutes", "calves", "hamstrings"],
        "secondary": ["trunk", "hip_stabilizers"],
    },
    "box_drills": {
        "patterns": ["box_jump", "step_up_power", "lateral_footwork"],
        "qualities": ["coordination", "jump_power", "change_of_direction"],
        "primary": ["quadriceps", "glutes", "calves"],
        "secondary": ["hamstrings", "trunk", "hip_stabilizers"],
    },
    "bounding": {
        "patterns": ["bounding", "sprint_mechanics", "horizontal_elasticity"],
        "qualities": ["stride_power", "acceleration", "elastic_strength"],
        "primary": ["glutes", "hamstrings", "calves", "quadriceps"],
        "secondary": ["hip_flexors", "trunk"],
    },
    "medicine_ball_exercises": {
        "patterns": ["medicine_ball_throw", "upper_body_power", "trunk_power"],
        "qualities": ["explosive_power", "rotational_power", "force_transfer"],
        "primary": ["trunk", "shoulders", "chest"],
        "secondary": ["lats", "triceps", "glutes", "hips"],
    },
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _file_info(path: Path) -> Dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "line_count": len(data.decode("utf-8", errors="ignore").splitlines()),
    }


def _slug(value: str) -> str:
    value = value.replace("ñ", "n").replace("Ñ", "N")
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _title(value: str) -> str:
    normalized = re.sub(r"\s+", " ", str(value or "").strip())
    if not normalized:
        return ""
    small = {"and", "or", "with", "to", "the", "of", "in"}
    words = []
    for idx, word in enumerate(normalized.lower().split(" ")):
        if idx > 0 and word in small:
            words.append(word)
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words).replace("Mma", "MMA").replace("Acl", "ACL")


def _clean_text(value: Any, *, max_chars: int = 700) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"Figure\s+\d+\.\d+[a-z]?", "", text)
    text = text.replace("Remem- TIP", "Remember").replace("de- tion", "direction")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _source_hash(*parts: Any) -> str:
    text = "\n".join(str(part or "") for part in parts)
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _normalize_category(value: str) -> str:
    return _slug(value).replace("multiple_hops_and_jumps", "multiple_hops_and_jumps")


def _normalize_intensity(level: str, name: str, category: str) -> str:
    text = f"{level} {name} {category}".lower()
    if "high" in text and "moderate to high" not in text:
        return "high"
    if "moderate to high" in text or ("moderate" in text and "high" in text):
        return "moderate_high"
    if "low to moderate" in text:
        return "low_moderate"
    if "moderate" in text:
        return "moderate"
    return "low"


def _difficulty(intensity: str, category: str, name: str) -> str:
    name_l = name.lower()
    if intensity in {"high", "moderate_high"}:
        return "advanced"
    if "single-leg" in name_l or "depth jump" in name_l or category == "depth_jumps":
        return "intermediate" if intensity in {"low", "low_moderate"} else "advanced"
    if intensity in {"moderate", "low_moderate"}:
        return "intermediate"
    return "beginner"


def _impact_level(intensity: str, category: str, name: str) -> str:
    name_l = name.lower()
    if intensity == "high" or "depth jump" in name_l or "single-leg" in name_l:
        return "high"
    if intensity in {"moderate_high", "moderate"} or category in {"multiple_hops_and_jumps", "bounding"}:
        return "moderate"
    return "low"


def _technical_complexity(intensity: str, category: str, name: str) -> str:
    name_l = name.lower()
    if any(term in name_l for term in ["360", "single-leg depth", "handstand", "power drop", "catch and pass"]):
        return "high"
    if category in {"depth_jumps", "bounding", "medicine_ball_exercises"} and intensity in {"moderate_high", "high"}:
        return "high"
    if intensity in {"moderate", "moderate_high"}:
        return "moderate"
    return "low"


def _parse_list(value: Any) -> List[str]:
    text = str(value or "").replace("/", ",")
    text = re.sub(r"\([^)]*\)", "", text)
    parts = [part.strip() for part in re.split(r",|;|\band\b", text) if part.strip()]
    return sorted(set(_slug(part) for part in parts if _slug(part)))


def _equipment_tags(value: Any, category: str) -> List[str]:
    text = str(value or "").lower()
    tags = set()
    if not text or "none" in text or "no equipment" in text:
        tags.add("bodyweight")
    if "cone" in text:
        tags.add("cones")
    if "hurdle" in text or "barrier" in text:
        tags.add("hurdles_or_barriers")
    if "box" in text:
        tags.add("plyo_box")
    if "medicine ball" in text:
        tags.add("medicine_ball")
    if "partner" in text:
        tags.add("partner")
    if "basketball" in text or "goal" in text or "rim" in text:
        tags.add("basketball_goal")
    if "tape" in text or "pattern" in text or "hexagon" in text:
        tags.add("floor_markings")
    if "mat" in text or "sandpit" in text or category in {"depth_jumps", "standing_jumps"}:
        tags.add("soft_landing_surface")
    if "stadium" in text or "steps" in text:
        tags.add("steps")
    if "external resistance" in text or "barbell" in text:
        tags.add("external_load")
    return sorted(tags or {"bodyweight"})


def _category_for_ai(category: str) -> str:
    return {
        "jumps_in_place": "plyometric_jumps_in_place",
        "standing_jumps": "plyometric_standing_jumps",
        "multiple_hops_and_jumps": "plyometric_multiple_hops_jumps",
        "depth_jumps": "plyometric_depth_jumps",
        "box_drills": "plyometric_box_drills",
        "bounding": "plyometric_bounding",
        "medicine_ball_exercises": "plyometric_medicine_ball",
    }.get(category, category)


def _name_specific_patterns(name: str) -> List[str]:
    name_l = name.lower()
    patterns: List[str] = []
    if "lateral" in name_l or "side" in name_l or "zigzag" in name_l:
        patterns.extend(["lateral_movement", "frontal_plane"])
    if "180" in name_l or "360" in name_l or "twist" in name_l or "rotation" in name_l:
        patterns.extend(["rotation", "air_turn"])
    if "sprint" in name_l or "bounding" in name_l or "skipping" in name_l:
        patterns.append("sprint_transfer")
    if "single-leg" in name_l or "single leg" in name_l:
        patterns.append("single_leg")
    if "hurdle" in name_l or "barrier" in name_l or "cone" in name_l:
        patterns.append("barrier_clearance")
    if "chest pass" in name_l or "throw" in name_l or "toss" in name_l or "slam" in name_l:
        patterns.append("throw")
    if "woodchopper" in name_l or "side throw" in name_l or "russian" in name_l or "rotation" in name_l:
        patterns.append("rotational_power")
    if "push-up" in name_l or "push up" in name_l or "power drop" in name_l:
        patterns.append("upper_body_plyometric")
    return patterns


def _coaching_cues(name: str, category: str, intensity: str) -> List[str]:
    cues = [
        "Start with clean posture and stop the set when jump height, distance, rhythm, or landing quality drops.",
        "Land quietly with the foot, knee, hip, and trunk aligned before the next effort.",
    ]
    if category in {"multiple_hops_and_jumps", "bounding", "depth_jumps"}:
        cues.append("Keep ground contact brief without sacrificing control.")
    if category == "medicine_ball_exercises":
        cues.append("Brace the trunk and move the ball explosively without leaking force through the spine.")
    if "single-leg" in name.lower():
        cues.append("Own the single-leg landing before adding speed, height, distance, or fatigue.")
    if intensity in {"high", "moderate_high"}:
        cues.append("Use full recovery and low volume; every repetition should look powerful and controlled.")
    return cues


def _common_errors(name: str, category: str, intensity: str) -> List[str]:
    errors = [
        "Continuing after landings become loud, stiff, or unstable.",
        "Letting the knees collapse inward or losing trunk position.",
    ]
    if category in {"depth_jumps", "multiple_hops_and_jumps", "bounding"}:
        errors.append("Chasing speed while contact time, posture, or landing alignment gets worse.")
    if category == "medicine_ball_exercises":
        errors.append("Using the arms only instead of transferring force through hips and trunk.")
    if intensity in {"high", "moderate_high"}:
        errors.append("Using advanced intensity before the athlete has earned it through strength and landing control.")
    return errors


def _avoid_when(intensity: str, category: str, equipment: List[str], name: str) -> List[str]:
    avoid = ["painful landings", "poor landing control", "fatigue that changes mechanics"]
    if category in {"depth_jumps", "multiple_hops_and_jumps", "bounding", "box_drills"}:
        avoid.extend(["active knee pain", "active ankle or Achilles pain", "hard or unsafe landing surface"])
    if intensity in {"high", "moderate_high"}:
        avoid.extend(["beginner without plyometric base", "recent lower-body injury without clearance"])
    if "single-leg" in name.lower():
        avoid.append("single-leg instability or major side-to-side asymmetry")
    if "medicine_ball" in equipment:
        avoid.append("no suitable medicine ball or safe throwing area")
    if "plyo_box" in equipment:
        avoid.append("unsafe box height or unstable box")
    return sorted(set(avoid))


def _use_when(sports: List[str], category: str, intensity: str) -> List[str]:
    use = ["plyometric block", "sport power development"]
    if sports:
        use.append("sport transfer: " + ", ".join(sports[:5]))
    if category == "medicine_ball_exercises":
        use.append("upper-body or rotational power emphasis")
    if category in {"jumps_in_place", "standing_jumps"}:
        use.append("jump mechanics and takeoff development")
    if category in {"multiple_hops_and_jumps", "bounding"}:
        use.append("elastic reactivity, sprint transfer, or repeated-effort power")
    if category == "depth_jumps":
        use.append("reactive strength after landing mechanics are established")
    if intensity in {"high", "moderate_high"}:
        use.append("qualified intermediate or advanced athlete")
    return use


def _summary(row: Dict[str, Any], category: str, intensity: str, sports: List[str]) -> str:
    name = _title(row["name"])
    category_name = category.replace("_", " ")
    sport_text = f" with transfer to {', '.join(sports[:4])}" if sports else ""
    return f"{name} is a {intensity.replace('_', ' ')} intensity {category_name} drill for reactive power, landing control, and athletic force production{sport_text}."


def _sample_prescription(row: Dict[str, Any], difficulty: str, intensity: str, category: str) -> Dict[str, Any]:
    if category == "bounding":
        base = {"sets": "2-4", "distance": "10-30 m", "rest": "walk-back to 90 sec"}
    elif category == "medicine_ball_exercises":
        base = {"sets": "2-4", "reps": "4-8", "rest": "45-90 sec"}
    elif intensity == "high":
        base = {"sets": "2-4", "reps": "3-5", "rest": "60-120 sec"}
    elif intensity in {"moderate_high", "moderate"}:
        base = {"sets": "2-4", "reps": "4-8", "rest": "45-90 sec"}
    else:
        base = {"sets": "2-3", "reps": "6-10 or 10-20 sec", "rest": "30-60 sec"}
    base["intent"] = "quality first; stop when mechanics decline"
    base["difficulty"] = difficulty
    return base


def _load_exercise_rows() -> List[Dict[str, Any]]:
    rows = json.loads(_read_text(EXERCISES_JSON_PATH))
    if not isinstance(rows, list):
        raise ValueError("pylometrics/exercises.json must contain a list")
    csv_rows = list(csv.DictReader(EXERCISES_CSV_PATH.open(newline="", encoding="utf-8", errors="ignore")))
    if len(rows) != len(csv_rows):
        raise ValueError(f"Exercise JSON/CSV count mismatch: {len(rows)} vs {len(csv_rows)}")
    return rows


def _exercise_section_lines() -> Dict[str, int]:
    lines = _read_text(EXERCISES_MD_PATH).splitlines()
    result: Dict[str, int] = {}
    for index, line in enumerate(lines, start=1):
        if line.startswith("### "):
            result[_slug(line[4:])] = index
    return result


def _chapter_line_ranges() -> Dict[int, Tuple[int, int]]:
    lines = _read_text(FULL_EXTRACTION_PATH).splitlines()
    starts: List[Tuple[int, int]] = []
    pattern = re.compile(r"^# Chapter (\d+) ·")
    for index, line in enumerate(lines, start=1):
        match = pattern.match(line)
        if match:
            starts.append((int(match.group(1)), index))
    ranges: Dict[int, Tuple[int, int]] = {}
    for idx, (chapter, start) in enumerate(starts):
        end = starts[idx + 1][1] - 1 if idx + 1 < len(starts) else len(lines)
        ranges[chapter] = (start, end)
    return ranges


def _source_refs(section_id: str, heading: str, *, chapter: int = 9) -> List[Dict[str, Any]]:
    return [
        {
            "source_book_id": SOURCE_PACK_ID,
            "section_id": section_id,
            "section_title": heading,
            "heading": heading,
            "source_type": "local_extraction",
            "source_file": "pylometrics/Plyometrics_Full_Extraction.md",
            "chapter": chapter,
        }
    ]


def _exercise_records(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    section_lines = _exercise_section_lines()
    for row in rows:
        name = _title(row["name"])
        category = _normalize_category(row.get("category") or "")
        profile = CATEGORY_PROFILES.get(category, CATEGORY_PROFILES["jumps_in_place"])
        intensity = _normalize_intensity(row.get("LEVEL") or "", name, category)
        difficulty = _difficulty(intensity, category, name)
        impact = _impact_level(intensity, category, name)
        complexity = _technical_complexity(intensity, category, name)
        equipment = _equipment_tags(row.get("EQUIPMENT"), category)
        sports = _parse_list(row.get("SPORTS"))
        patterns = sorted(set(profile["patterns"] + _name_specific_patterns(name)))
        qualities = sorted(set(profile["qualities"] + ["plyometric_power", "stretch_shortening_cycle"]))
        exercise_id = f"plyo_ex_{_slug(name)}"
        section_id = f"plyo_section_ex_{_slug(name)}"
        raw_start = _clean_text(row.get("START"), max_chars=900)
        raw_action = _clean_text(row.get("ACTION"), max_chars=1100)
        raw_program = _clean_text(row.get("SAMPLE PROGRAM"), max_chars=1200)
        records.append(
            {
                "id": exercise_id,
                "name": name,
                "aliases": [],
                "category": _category_for_ai(category),
                "source_category": category,
                "difficulty": difficulty,
                "default_user_level": difficulty,
                "intensity": intensity,
                "technical_complexity": complexity,
                "mobility_requirement": "moderate",
                "stability_requirement": "high" if "single_leg" in patterns or category == "depth_jumps" else "moderate",
                "impact_level": impact,
                "load_scalability": "moderate" if category != "medicine_ball_exercises" else "high",
                "coaching_requirement": "high" if complexity == "high" or impact == "high" else "moderate",
                "equipment": equipment,
                "patterns": patterns,
                "qualities": qualities,
                "sport_tags": sorted(set(["plyometrics", "jump_training", "reactive_strength", *sports, *patterns, *qualities])),
                "primary_muscles": profile["primary"],
                "secondary_muscles": profile["secondary"],
                "summary": _summary(row, category, intensity, sports),
                "coaching_cues": _coaching_cues(name, category, intensity),
                "common_errors": _common_errors(name, category, intensity),
                "use_when": _use_when(sports, category, intensity),
                "avoid_when": _avoid_when(intensity, category, equipment, name),
                "progressions": [],
                "regressions": [],
                "sample_prescription": _sample_prescription(row, difficulty, intensity, category),
                "source_extract": {
                    "level": _clean_text(row.get("LEVEL"), max_chars=300),
                    "recommended_sports": _clean_text(row.get("SPORTS"), max_chars=300),
                    "equipment": _clean_text(row.get("EQUIPMENT"), max_chars=300),
                    "start": raw_start,
                    "action": raw_action,
                    "sample_program": raw_program,
                },
                "source_line_start": section_lines.get(_slug(name)),
                "source_text_hash": _source_hash(row.get("START"), row.get("ACTION"), row.get("SAMPLE PROGRAM")),
                "source_refs": _source_refs(section_id, name, chapter=9),
            }
        )
    return records


def _is_variation(record: Dict[str, Any]) -> bool:
    if record["impact_level"] == "high" or record["technical_complexity"] == "high":
        return True
    if record["source_category"] == "depth_jumps" and record["name"] not in {"Drop And Freeze", "Jump To Box", "Step-Close Jump And Reach"}:
        return True
    return False


def _catalog_doc(record: Dict[str, Any], library: str) -> Dict[str, Any]:
    doc = {
        "id": record["id"],
        "name": record["name"],
        "aliases": record["aliases"],
        "base_exercise": record["source_category"],
        "category": record["category"],
        "difficulty": record["difficulty"],
        "default_user_level": record["default_user_level"],
        "technical_complexity": record["technical_complexity"],
        "mobility_requirement": record["mobility_requirement"],
        "stability_requirement": record["stability_requirement"],
        "impact_level": record["impact_level"],
        "load_scalability": record["load_scalability"],
        "coaching_requirement": record["coaching_requirement"],
        "beginner_usable_as_drill": record["difficulty"] == "beginner",
        "equipment": record["equipment"],
        "patterns": record["patterns"],
        "qualities": record["qualities"],
        "sport_tags": record["sport_tags"],
        "primary_muscles": record["primary_muscles"],
        "secondary_muscles": record["secondary_muscles"],
        "summary": record["summary"],
        "coaching_cues": record["coaching_cues"],
        "common_errors": record["common_errors"],
        "use_when": record["use_when"],
        "avoid_when": record["avoid_when"],
        "progressions": record["progressions"],
        "regressions": record["regressions"],
        "sample_prescription": record["sample_prescription"],
        "source_book_id": SOURCE_PACK_ID,
        "source_book_ids": [SOURCE_PACK_ID],
        "source_refs": record["source_refs"],
        "expert_validation_status": "pending",
        "ingestion_method": INGESTION_METHOD,
        "version": "v1.0.0",
    }
    if library == "variation":
        doc["tier"] = "specialist_variation"
        doc["variation_type"] = "high_intensity_or_specialist_plyometric"
    return doc


def _raw_doc(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": f"{record['id']}_raw",
        "name": record["name"],
        "aliases": record["aliases"],
        "definition": record["summary"],
        "exercise_family": record["source_category"],
        "exercise_type": record["category"],
        "category": record["category"],
        "difficulty": record["difficulty"],
        "intensity": record["intensity"],
        "equipment_required": record["equipment"],
        "movement_patterns": record["patterns"],
        "training_qualities": record["qualities"],
        "primary_muscles": record["primary_muscles"],
        "secondary_muscles": record["secondary_muscles"],
        "coaching_cues": record["coaching_cues"],
        "common_errors": record["common_errors"],
        "contraindications": record["avoid_when"],
        "injury_flags": record["avoid_when"],
        "progressions": record["progressions"],
        "regressions": record["regressions"],
        "sport_tags": record["sport_tags"],
        "summary": record["summary"],
        "source_extract": record["source_extract"],
        "source_text_hash": record["source_text_hash"],
        "source_book_id": SOURCE_PACK_ID,
        "source_book_ids": [SOURCE_PACK_ID],
        "source_refs": record["source_refs"],
        "expert_validation_status": "pending",
        "ingestion_method": INGESTION_METHOD,
        "version": "v1.0.0",
    }


def _source_docs(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs: List[Dict[str, Any]] = []
    chapter_ranges = _chapter_line_ranges()
    for chapter in CHAPTERS:
        line_start, line_end = chapter_ranges.get(chapter["chapter"], (None, None))
        docs.append(
            {
                "id": f"plyo_chapter_{chapter['chapter']:02d}",
                "source_book_id": SOURCE_PACK_ID,
                "section_order": chapter["chapter"] * 1000,
                "section_title": f"Chapter {chapter['chapter']} - {chapter['title']}",
                "domain": "plyometrics",
                "topics": chapter["topics"],
                "summary": chapter["summary"],
                "source_file": "pylometrics/Plyometrics_Full_Extraction.md",
                "line_start": line_start,
                "line_end": line_end,
                "created_at": now,
                "updated_at": now,
            }
        )
    for index, record in enumerate(records, start=1):
        docs.append(
            {
                "id": f"plyo_section_ex_{_slug(record['name'])}",
                "source_book_id": SOURCE_PACK_ID,
                "section_order": 9000 + index,
                "section_title": record["name"],
                "domain": "plyometrics",
                "topics": sorted(set([record["source_category"], record["intensity"], *record["patterns"], *record["qualities"]])),
                "summary": record["summary"],
                "source_file": "pylometrics/exercises.md",
                "line_start": record.get("source_line_start"),
                "source_text_hash": record["source_text_hash"],
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _principle_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs = []
    for item in TRAINING_PRINCIPLES:
        docs.append(
            {
                **item,
                "knowledge_type": "training_principle",
                "source_book_id": SOURCE_PACK_ID,
                "source_refs": _source_refs("plyo_chapter_01", item["title"], chapter=1),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _rule_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs = []
    chapter_by_category = {
        "progression": 8,
        "safety": 8,
        "volume": 8,
        "recovery": 8,
        "session_order": 8,
        "warmup": 8,
        "periodization": 8,
        "readiness": 7,
        "rehabilitation": 6,
        "complex_training": 10,
        "season_phase": 11,
    }
    for item in PROGRAMMING_RULES:
        chapter = chapter_by_category.get(item["category"], 8)
        docs.append(
            {
                **item,
                "knowledge_type": "programming_rule",
                "topics": item.get("applies_to") or [],
                "usage_context": item.get("rule_text"),
                "source_book_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(f"plyo_chapter_{chapter:02d}", item["title"], chapter=chapter),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _readiness_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **item,
            "knowledge_type": "readiness_rule",
            "topics": [item["category"], "plyometrics", "assessment"],
            "factors": item.get("pass_criteria") or [],
            "source_book_id": SOURCE_PACK_ID,
            "source_refs": _source_refs("plyo_chapter_07", item["title"], chapter=7),
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        }
        for item in READINESS_RULES
    ]


def _benchmark_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **item,
            "test_name": item["name"],
            "knowledge_type": "benchmark_test",
            "topics": [item["category"], *item.get("measures", [])],
            "qualities": item.get("measures", []),
            "sport_tags": ["plyometrics", "jump_training", item["category"], *item.get("measures", [])],
            "source_book_id": SOURCE_PACK_ID,
            "source_refs": _source_refs("plyo_chapter_07", item["name"], chapter=7),
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        }
        for item in BENCHMARK_TESTS
    ]


def _injury_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    chapter_by_area = {
        "knee": 5,
        "ankle_achilles": 6,
        "shoulder": 10,
        "return_to_sport": 6,
        "load_management": 8,
    }
    docs = []
    for item in INJURY_MODIFICATIONS:
        chapter = chapter_by_area.get(item["injury_area"], 6)
        docs.append(
            {
                **item,
                "knowledge_type": "injury_modification",
                "topics": [item["injury_area"], "plyometrics", "regression"],
                "body_area": item["injury_area"],
                "avoid_patterns": item.get("blocked_patterns") or [],
                "source_book_id": SOURCE_PACK_ID,
                "source_refs": _source_refs(f"plyo_chapter_{chapter:02d}", item["title"], chapter=chapter),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _sport_rule_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs = []
    for item in SPORT_TEMPLATES:
        docs.append(
            {
                **item,
                "knowledge_type": "sport_training_rule",
                "category": "sport_specific_plyometric_template",
                "condition": f"{item['sport']} user needs plyometric power, landing, speed, or medicine-ball transfer work",
                "applies_to": [item["sport"], "plyometrics", *item["recommended_categories"]],
                "topics": [item["sport"], "sport_specific", "plyometrics", *item["phase_focus"]],
                "source_book_id": SOURCE_PACK_ID,
                "source_refs": _source_refs("plyo_chapter_11", item["title"], chapter=11),
                "ingestion_method": INGESTION_METHOD,
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs


def _template_docs() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **item,
            "category": "plyometric_sport_template",
            "level": "intermediate",
            "equipment_required": ["bodyweight", "soft_landing_surface"],
            "sport_tags": [item["sport"], "plyometrics", "jump_training"],
            "source_book_id": SOURCE_PACK_ID,
            "source_refs": _source_refs("plyo_chapter_11", item["title"], chapter=11),
            "ingestion_method": INGESTION_METHOD,
            "created_at": now,
            "updated_at": now,
        }
        for item in SPORT_TEMPLATES
    ]


def _progression_edges(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    records_by_category: Dict[str, List[Dict[str, Any]]] = {}
    intensity_order = {"low": 1, "low_moderate": 2, "moderate": 3, "moderate_high": 4, "high": 5}
    for record in records:
        records_by_category.setdefault(record["source_category"], []).append(record)

    docs: List[Dict[str, Any]] = []
    for category, category_records in records_by_category.items():
        ordered = sorted(category_records, key=lambda r: (intensity_order.get(r["intensity"], 3), r["technical_complexity"], r["name"]))
        for current, nxt in zip(ordered, ordered[1:]):
            docs.append(
                {
                    "id": f"plyo_prog_{_slug(current['name'])}_to_{_slug(nxt['name'])}",
                    "base_exercise": category,
                    "from_exercise_id": current["id"],
                    "from_exercise_name": current["name"],
                    "to_exercise_id": nxt["id"],
                    "to_exercise_name": nxt["name"],
                    "direction": "progression",
                    "min_user_level": nxt["difficulty"],
                    "progression_condition": "Progress only when the athlete completes the current drill with clean landings, consistent rhythm, no pain, and no next-day adverse response.",
                    "source_book_id": SOURCE_PACK_ID,
                    "source_refs": _source_refs("plyo_chapter_08", "Plyometric Progression System", chapter=8),
                    "created_at": now,
                    "updated_at": now,
                }
            )
    return docs


def _merge_list(existing: Any, incoming: Any) -> List[Any]:
    result: List[Any] = []
    for value in [existing, incoming]:
        items = value if isinstance(value, list) else [value]
        for item in items:
            if item in (None, "", [], {}):
                continue
            if item not in result:
                result.append(item)
    return result


def _merge_doc(existing: Dict[str, Any], incoming: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    merged = dict(existing)
    list_fields = {
        "aliases",
        "equipment",
        "equipment_required",
        "patterns",
        "movement_patterns",
        "qualities",
        "training_qualities",
        "sport_tags",
        "primary_muscles",
        "secondary_muscles",
        "coaching_cues",
        "common_errors",
        "use_when",
        "avoid_when",
        "contraindications",
        "injury_flags",
        "progressions",
        "regressions",
        "source_refs",
        "source_book_ids",
    }
    for key, value in incoming.items():
        if key == "_id":
            continue
        if key in list_fields:
            merged[key] = _merge_list(merged.get(key), value)
        elif key in {"created_at"} and merged.get(key):
            continue
        elif value not in (None, "", [], {}):
            merged[key] = value
    merged["source_book_ids"] = _merge_list(merged.get("source_book_ids"), SOURCE_PACK_ID)
    merged["updated_at"] = now
    return merged


async def _upsert_many(db: Any, collection_name: str, docs: Iterable[Dict[str, Any]]) -> int:
    now = datetime.utcnow()
    collection = db[collection_name]
    count = 0
    for doc in docs:
        doc = {**doc, "updated_at": now}
        doc.setdefault("created_at", now)
        if collection_name == "source_sections" and doc.get("source_book_id") == SOURCE_PACK_ID:
            await collection.replace_one({"id": doc["id"]}, doc, upsert=True)
            count += 1
            continue
        existing = await collection.find_one({"id": doc["id"]})
        if not existing and doc.get("name"):
            existing = await collection.find_one({"name": doc["name"]})
        if existing:
            merged = _merge_doc(existing, doc, now)
            await collection.replace_one({"id": existing["id"]}, merged)
        else:
            await collection.replace_one({"id": doc["id"]}, doc, upsert=True)
        count += 1
    return count


async def ingest() -> Dict[str, int]:
    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "test_database")]
    await ensure_database_schema(db)

    rows = _load_exercise_rows()
    records = _exercise_records(rows)
    primary = [record for record in records if not _is_variation(record)]
    variations = [record for record in records if _is_variation(record)]
    files = [_file_info(path) for path in [FULL_EXTRACTION_PATH, EXERCISES_JSON_PATH, EXERCISES_CSV_PATH, EXERCISES_MD_PATH]]
    now = datetime.utcnow()
    source_doc = {
        "id": SOURCE_PACK_ID,
        "title": "Plyometrics Complete Local Extraction",
        "source_type": "local_book_extraction",
        "domains": ["plyometrics", "jump_training", "reactive_strength", "medicine_ball_power"],
        "summary": "Normalized plyometric exercise, programming, assessment, safety, rehab, and sport-specific planning knowledge extracted from local source files.",
        "source_count": len(files),
        "exercise_count": len(records),
        "ingestion_method": INGESTION_METHOD,
        "files": files,
        "created_at": now,
        "updated_at": now,
    }

    counts: Dict[str, int] = {}
    for collection in ("source_registry", "knowledge_sources"):
        await db[collection].replace_one({"id": SOURCE_PACK_ID}, source_doc, upsert=True)
        counts[collection] = 1

    extraction_run = {
        "id": f"{SOURCE_PACK_ID}_latest",
        "source_book_id": SOURCE_PACK_ID,
        "status": "completed",
        "ingestion_method": INGESTION_METHOD,
        "files": files,
        "exercise_count": len(records),
        "primary_count": len(primary),
        "variation_count": len(variations),
        "created_at": now,
        "updated_at": now,
    }
    await db.knowledge_extraction_runs.replace_one({"id": extraction_run["id"]}, extraction_run, upsert=True)
    counts["knowledge_extraction_runs"] = 1

    counts["source_sections"] = await _upsert_many(db, "source_sections", _source_docs(records))
    counts["primary_exercise_library"] = await _upsert_many(db, "primary_exercise_library", [_catalog_doc(record, "primary") for record in primary])
    counts["exercise_variation_library"] = await _upsert_many(db, "exercise_variation_library", [_catalog_doc(record, "variation") for record in variations])
    counts["exercise_library"] = await _upsert_many(db, "exercise_library", [_raw_doc(record) for record in records])
    counts["exercise_progression_graph"] = await _upsert_many(db, "exercise_progression_graph", _progression_edges(records))
    counts["training_principles"] = await _upsert_many(db, "training_principles", _principle_docs())
    counts["programming_rules"] = await _upsert_many(db, "programming_rules", _rule_docs())
    counts["readiness_rules"] = await _upsert_many(db, "readiness_rules", _readiness_docs())
    counts["benchmark_tests"] = await _upsert_many(db, "benchmark_tests", _benchmark_docs())
    counts["injury_modifications"] = await _upsert_many(db, "injury_modifications", _injury_docs())
    counts["sport_training_rules"] = await _upsert_many(db, "sport_training_rules", _sport_rule_docs())
    counts["workout_templates"] = await _upsert_many(db, "workout_templates", _template_docs())
    client.close()
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest normalized plyometrics source data into MongoDB.")
    return parser.parse_args()


def main() -> None:
    parse_args()
    counts = asyncio.run(ingest())
    for collection, count in counts.items():
        print(f"{collection}: {count}")


if __name__ == "__main__":
    main()
