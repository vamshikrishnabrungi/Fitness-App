from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_LIMITS: Dict[str, int] = {
    "primary_exercises": 30,
    "variations": 8,
    "progression_paths": 16,
    "exercise_history": 20,
    "exercises": 38,
    "programming_rules": 18,
    "technical_models": 14,
    "technical_errors": 10,
    "mobility_drills": 10,
    "recovery_rules": 8,
    "nutrition_principles": 8,
    "sport_teaching_progressions": 8,
    "sport_skill_assessments": 5,
    "sport_level_transition_rules": 5,
    "training_protocols": 6,
    "semantic_exercises": 12,
    "source_refs": 30,
}

COMPACT_AI_LIMITS: Dict[str, int] = {
    "primary_exercises": 12,
    "variations": 2,
    "progression_paths": 5,
    "exercise_history": 8,
    "programming_rules": 4,
    "technical_models": 0,
    "technical_errors": 0,
    "mobility_drills": 3,
    "recovery_rules": 2,
    "nutrition_principles": 1,
    "sport_teaching_progressions": 4,
    "sport_skill_assessments": 2,
    "sport_level_transition_rules": 2,
    "training_protocols": 5,
    "source_refs": 8,
}

SPORT_QUALITY_TAGS: Dict[str, List[str]] = {
    "running": [
        "aerobic",
        "lower_leg",
        "calf",
        "soleus",
        "ankle",
        "hip",
        "trunk",
        "hamstring",
        "single_leg",
        "jump_training",
    ],
    "running_endurance": [
        "aerobic",
        "lower_leg",
        "calf",
        "soleus",
        "ankle",
        "hip",
        "trunk",
        "hamstring",
        "single_leg",
        "threshold",
        "VO2",
        "long_run",
        "running_economy",
    ],
    "cricket": [
        "acceleration",
        "deceleration",
        "rotational",
        "anti_rotation",
        "shoulder",
        "scapular",
        "hamstring",
        "calf",
        "adductor",
        "lateral",
    ],
    "volleyball": [
        "jump",
        "landing",
        "deceleration",
        "knee",
        "ankle",
        "hip",
        "trunk",
        "shoulder",
        "overhead",
        "power",
    ],
    "football": [
        "acceleration",
        "sprint",
        "deceleration",
        "change_of_direction",
        "single_leg",
        "hamstring",
        "adductor",
        "calf",
        "aerobic",
    ],
    "soccer": [
        "acceleration",
        "sprint",
        "deceleration",
        "change_of_direction",
        "single_leg",
        "hamstring",
        "adductor",
        "calf",
        "aerobic",
    ],
    "basketball": [
        "acceleration",
        "deceleration",
        "jump",
        "landing",
        "ankle",
        "knee",
        "hip",
        "lateral",
        "trunk",
        "power",
    ],
    "badminton": [
        "split_step",
        "lunge",
        "deceleration",
        "change_of_direction",
        "ankle",
        "knee",
        "achilles",
        "shoulder",
        "scapular",
        "reaction_speed",
        "rotational",
        "overhead",
        "racket",
    ],
    "tennis": [
        "split_step",
        "lateral_movement",
        "deceleration",
        "change_of_direction",
        "rotational",
        "shoulder",
        "scapular",
        "elbow",
        "wrist",
        "racket",
        "serve",
        "return",
        "surface",
    ],
    "boxing": [
        "rotational",
        "trunk",
        "shoulder",
        "scapular",
        "hip",
        "footwork",
        "conditioning",
        "power",
    ],
    "mma": [
        "rotational",
        "trunk",
        "neck",
        "shoulder",
        "scapular",
        "hip",
        "grip",
        "wrestling",
        "grappling",
        "striking",
        "conditioning",
        "repeat_power",
        "contact_load",
    ],
    "kickboxing": [
        "striking",
        "rotational",
        "trunk",
        "shoulder",
        "scapular",
        "hip",
        "adductor",
        "knee",
        "ankle",
        "calf",
        "shin",
        "footwork",
        "kick",
        "punch",
        "repeat_power",
        "conditioning",
        "contact_load",
    ],
    "wrestling": [
        "wrestling",
        "grappling",
        "relative_strength",
        "repeat_power",
        "grip",
        "neck",
        "trunk",
        "hip",
        "adductor",
        "knee",
        "ankle",
        "hand_fighting",
        "takedown",
        "sprawl",
        "scramble",
    ],
    "olympic weightlifting": [
        "olympic_lift",
        "snatch",
        "clean",
        "jerk",
        "barbell",
        "power",
        "triple_extension",
    ],
    "weightlifting": [
        "olympic_lift",
        "snatch",
        "clean",
        "jerk",
        "barbell",
        "power",
        "triple_extension",
    ],
    "calisthenics": [
        "advanced_calisthenics",
        "bodyweight",
        "gymnastics_strength",
        "skill_progression",
        "straight_arm_strength",
        "straight_arm_pull",
        "ring_stability",
        "rings",
        "ring_dip",
        "ring_muscle_up",
        "muscle_up",
        "support",
        "lever",
        "planche",
        "front_lever",
        "back_lever",
        "human_flag",
        "compression",
        "vertical_pull",
        "vertical_push",
        "handstand",
        "handstand_push_up",
        "inversion",
    ],
    "plyometrics": [
        "plyometrics",
        "jump_training",
        "reactive_strength",
        "stretch_shortening_cycle",
        "landing_mechanics",
        "depth_jump",
        "bounding",
        "medicine_ball_throw",
        "elastic_reactivity",
        "short_ground_contact",
    ],
    "track and field": [
        "sprint_transfer",
        "bounding",
        "horizontal_power",
        "vertical_power",
        "reactive_strength",
        "plyometrics",
        "medicine_ball_throw",
    ],
    "tennis": [
        "lateral_movement",
        "change_of_direction",
        "rotational_power",
        "medicine_ball_throw",
        "plyometrics",
        "reactive_strength",
    ],
    "baseball": [
        "rotational_power",
        "medicine_ball_throw",
        "throw",
        "lateral_movement",
        "plyometrics",
    ],
    "softball": [
        "rotational_power",
        "medicine_ball_throw",
        "throw",
        "lateral_movement",
        "plyometrics",
    ],
    "rugby": [
        "reactive_strength",
        "jump_training",
        "medicine_ball_throw",
        "plyometrics",
        "change_of_direction",
    ],
    "swimming": [
        "medicine_ball_throw",
        "upper_body_power",
        "trunk_power",
        "plyometrics",
    ],
    "cycling": [
        "aerobic",
        "endurance",
        "threshold",
        "VO2",
        "sprint_power",
        "cadence",
        "bike_handling",
        "trunk",
        "hip",
        "knee",
        "low_back",
        "neck",
        "posture",
        "fueling",
    ],
    "gymnastics": [
        "plyometrics",
        "jump_training",
        "upper_body_plyometric",
        "landing_mechanics",
        "reactive_strength",
    ],
    "ice hockey": [
        "lateral_movement",
        "single_leg",
        "reactive_strength",
        "plyometrics",
    ],
    "mixed martial arts": [
        "medicine_ball_throw",
        "rotational_power",
        "reactive_strength",
        "plyometrics",
        "kicking_power",
    ],
    "mma": [
        "medicine_ball_throw",
        "rotational_power",
        "reactive_strength",
        "plyometrics",
        "kicking_power",
    ],
}

GOAL_TAGS: Dict[str, List[str]] = {
    "sport performance": ["power", "strength", "general_strength", "joint_stability", "trunk_stiffness", "speed", "technique", "jump_training", "accessory_work"],
    "build muscle": ["hypertrophy", "strength", "general_strength", "accessory_work"],
    "lose fat": ["conditioning", "general_strength", "muscular_endurance", "nutrition", "recovery"],
    "get stronger": ["strength", "general_strength", "max_strength", "loading", "program_design", "training_variables"],
    "endurance": ["aerobic", "conditioning", "recovery"],
    "mobility": ["mobility", "flexibility", "position"],
    "flexibility": ["flexibility", "mobility", "static_stretching", "range_of_motion", "cooldown"],
    "warmup": ["dynamic_warmup", "pre_workout", "activation", "mobility"],
    "warm-up": ["dynamic_warmup", "pre_workout", "activation", "mobility"],
    "cooldown": ["static_stretching", "post_workout", "recovery", "flexibility"],
    "cool-down": ["static_stretching", "post_workout", "recovery", "flexibility"],
    "activation": ["activation", "joint_stability", "pre_workout", "movement_prep"],
    "prehab": ["activation", "joint_stability", "injury_modification", "mobility"],
    "posture": ["posture", "desk_work", "thoracic_spine", "scapular_control", "neck"],
    "return from injury": ["safety", "return_to_training", "tissue_capacity", "joint_stability", "recovery", "mobility", "assessment"],
    "general fitness": ["strength", "general_strength", "conditioning", "mobility"],
    "advanced calisthenics": [
        "advanced_calisthenics",
        "bodyweight",
        "gymnastics_strength",
        "skill_progression",
        "straight_arm_strength",
        "ring_stability",
        "rings",
        "ring_dip",
        "ring_muscle_up",
        "muscle_up",
        "lever",
        "planche",
        "front_lever",
        "back_lever",
        "human_flag",
        "compression",
        "handstand",
        "handstand_push_up",
    ],
    "plyometrics": [
        "plyometrics",
        "jump_training",
        "reactive_strength",
        "landing_mechanics",
        "medicine_ball_throw",
        "bounding",
        "depth_jump",
    ],
    "jump higher": [
        "jump_training",
        "vertical_power",
        "reactive_strength",
        "landing_mechanics",
        "plyometrics",
    ],
    "power": [
        "power",
        "explosive_power",
        "reactive_strength",
        "medicine_ball_throw",
        "plyometrics",
    ],
    "speed": [
        "speed",
        "sprint_transfer",
        "bounding",
        "short_ground_contact",
        "plyometrics",
    ],
    "explosive power": [
        "explosive_power",
        "reactive_strength",
        "jump_training",
        "medicine_ball_throw",
        "plyometrics",
    ],
}

INJURY_TAGS: Dict[str, List[str]] = {
    "knee": ["knee", "landing", "jump", "squat", "deceleration", "quad", "hip", "ankle"],
    "shoulder": ["shoulder", "overhead", "press", "scapular", "rack"],
    "back": ["back", "spine", "trunk", "hinge", "bracing"],
    "lower back": ["back", "spine", "trunk", "hinge", "bracing"],
    "ankle": ["ankle", "calf", "jump", "landing"],
    "calf": ["calf", "soleus", "ankle", "jump", "running"],
    "achilles": ["achilles", "calf", "soleus", "ankle", "jump", "running"],
    "hip": ["hip", "glute", "squat", "hinge"],
    "hamstring": ["hamstring", "hinge", "sprint", "pull"],
    "adductor": ["adductor", "groin", "lateral"],
    "groin": ["adductor", "groin", "lateral"],
    "wrist": ["wrist", "front_rack", "overhead", "handstand_prep", "pushup_prep"],
    "neck": ["neck", "upper_trapezius", "posture", "desk_work"],
    "osteoporosis": ["osteoporosis", "bone_health", "older_adults", "balance", "fall_risk"],
}

MOBILITY_CONTEXT_TAGS = {
    "mobility",
    "flexibility",
    "dynamic_mobility",
    "static_stretching",
    "dynamic_warmup",
    "activation",
    "warmup",
    "pre_workout",
    "post_workout",
    "cooldown",
    "recovery",
    "range_of_motion",
    "joint_stability",
    "injury_modification",
    "return_to_training",
    "older_adults",
    "youth",
    "balance",
    "fall_risk",
    "posture",
    "desk_work",
    "mobility_flexibility_web_research_v1",
}

GENERAL_GYM_CONTEXT_TAGS = {
    "strength",
    "general_strength",
    "max_strength",
    "hypertrophy",
    "muscular_endurance",
    "conditioning",
    "power",
    "tissue_capacity",
    "joint_stability",
    "trunk_stiffness",
    "hip_control",
    "knee_control",
    "ankle_stability",
    "posterior_chain_strength",
    "single_leg_control",
    "return_to_training",
    "general_gym",
    "strength_and_conditioning",
    "general_gym_exercise_research_v1",
}

SPORT_BASE_DOMAINS: Dict[str, List[str]] = {
    "running": ["easy_aerobic_base", "long_run", "running_strength_conditioning", "return_to_run"],
    "running_endurance": ["easy_aerobic_base", "long_run", "running_strength_conditioning", "return_to_run"],
    "cricket": ["match_iq", "cricket_snc", "fielding", "throwing"],
    "volleyball": ["match_iq", "volleyball_snc", "serving", "passing_serve_receive", "defense_digging", "transition"],
    "soccer": ["match_iq", "football_snc", "ball_mastery", "first_touch_receiving", "passing", "defending_pressing"],
    "football": ["match_iq", "football_snc", "ball_mastery", "first_touch_receiving", "passing", "defending_pressing"],
    "basketball": ["match_iq", "basketball_snc", "ball_handling", "shooting", "passing", "defense_closeouts", "transition"],
    "boxing": ["tactical_iq", "boxing_strength_conditioning", "stance_guard", "footwork_ringcraft", "punch_mechanics", "defense_countering", "sparring_contact"],
    "mma": [
        "mma_rules_scoring",
        "mma_fight_iq",
        "mma_range_management",
        "mma_stance_guard",
        "mma_striking_entries",
        "mma_kicking",
        "mma_striking_defense",
        "mma_clinch_cage",
        "mma_wrestling",
        "mma_takedown_entries",
        "mma_takedown_defense",
        "mma_ground_control",
        "mma_submissions",
        "mma_escapes_scrambles",
        "mma_ground_and_pound",
        "mma_strength_conditioning",
        "mma_sparring_contact",
        "mma_fight_camp",
        "mma_injury_load_management",
        "mma_level_progression",
    ],
    "kickboxing": [
        "kickboxing_rules_scoring",
        "kickboxing_style_differences",
        "kickboxing_stance_guard",
        "kickboxing_footwork_ringcraft",
        "kickboxing_punch_mechanics",
        "kickboxing_kick_mechanics",
        "kickboxing_kick_defense_checks",
        "kickboxing_combinations_entries_exits",
        "kickboxing_defense_countering",
        "kickboxing_clinch_knees_rule_dependent",
        "kickboxing_sparring_contact",
        "kickboxing_strength_conditioning",
        "kickboxing_injury_load_management",
        "kickboxing_competition_week",
        "kickboxing_level_progression",
    ],
    "wrestling": [
        "wrestling_rules_scoring",
        "wrestling_style_differences",
        "wrestling_stance_motion",
        "wrestling_hand_fighting_ties",
        "wrestling_takedown_offense",
        "wrestling_takedown_defense",
        "wrestling_top_control_turns",
        "wrestling_bottom_escapes_reversals",
        "wrestling_par_terre",
        "wrestling_mat_returns",
        "wrestling_scrambles",
        "wrestling_edge_tactics",
        "wrestling_match_iq",
        "wrestling_strength_conditioning",
        "wrestling_injury_load_management",
        "wrestling_competition_week",
        "wrestling_level_progression",
    ],
    "badminton": [
        "rules_scoring_match_iq",
        "grip_racket_control",
        "serve_return",
        "footwork_recovery",
        "badminton_strength_conditioning",
        "injury_load_management",
        "stroke_mechanics_deep",
        "footwork_movement_court_coverage",
        "tactics_sport_iq",
        "badminton_injury_snc_load_return_to_court",
    ],
    "tennis": [
        "rules_scoring_match_iq",
        "serve_return",
        "forehand_backhand",
        "volley_net_play",
        "footwork_recovery",
        "singles_tactics",
        "doubles_tactics",
        "surface_adaptation",
        "tennis_strength_conditioning",
        "injury_load_management",
        "stroke_mechanics_deep",
        "movement_surface_deep",
        "tactics_match_iq_deep",
        "doubles_systems_deep",
        "injury_snc_load_deep",
        "level_teaching_progression_deep",
    ],
    "swimming": [
        "water_confidence_safety",
        "freestyle",
        "backstroke",
        "breaststroke",
        "butterfly",
        "starts_turns_underwaters",
        "event_programming",
        "open_water_triathlon",
        "swimming_strength_conditioning",
        "injury_load_management",
        "stroke_mechanics_deep",
        "starts_turns_streamlines_underwater_breakouts",
        "event_programming_periodization",
        "injury_snc_load_return_to_swim",
        "beginner_safety_learn_to_swim",
        "level_teaching_progression_and_assessment",
    ],
    "cycling": [
        "beginner_confidence_safety",
        "endurance_power_programming",
        "bike_handling_safety",
        "discipline_tactics",
        "road_criterium",
        "time_trial_triathlon",
        "mtb_gravel_cyclocross",
        "track_bmx_power",
        "injury_snc_bike_fit_load",
        "level_progression",
        "beginner_fitness_commuter_cycling",
        "level_teaching_progression",
    ],
}

SPORT_ALIASES: Dict[str, str] = {
    "football": "soccer",
    "soccer": "soccer",
    "running": "running_endurance",
    "runner": "running_endurance",
    "run": "running_endurance",
    "endurance": "running_endurance",
    "marathon": "running_endurance",
    "half_marathon": "running_endurance",
    "trail_running": "running_endurance",
    "mma": "mma",
    "mixed_martial_arts": "mma",
    "combat": "mma",
    "combat_sports": "mma",
    "kickboxing": "kickboxing",
    "kickboxer": "kickboxing",
    "k1": "kickboxing",
    "k_1": "kickboxing",
    "glory_style": "kickboxing",
    "low_kick": "kickboxing",
    "full_contact_kickboxing": "kickboxing",
    "point_fighting": "kickboxing",
    "light_contact": "kickboxing",
    "kick_light": "kickboxing",
    "fitness_kickboxing": "kickboxing",
    "muay_thai": "kickboxing",
    "wrestling": "wrestling",
    "wrestler": "wrestling",
    "folkstyle": "wrestling",
    "freestyle_wrestling": "wrestling",
    "greco": "wrestling",
    "greco_roman": "wrestling",
    "grappling": "mma",
    "boxer": "boxing",
    "badminton": "badminton",
    "shuttle": "badminton",
    "tennis": "tennis",
    "lawn_tennis": "tennis",
    "swimming": "swimming",
    "swim": "swimming",
    "swimmer": "swimming",
    "triathlon_swim": "swimming",
    "cycling": "cycling",
    "cycle": "cycling",
    "cyclist": "cycling",
    "bike": "cycling",
    "biking": "cycling",
    "road_cycling": "cycling",
    "road_bike": "cycling",
    "mountain_biking": "cycling",
    "mountain_bike": "cycling",
    "mtb": "cycling",
    "gravel": "cycling",
    "cyclocross": "cycling",
    "bmx": "cycling",
    "triathlon_cycling": "cycling",
}

CRICKET_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "batter": ["batting"],
    "batsman": ["batting"],
    "batting": ["batting"],
    "top_order": ["batting"],
    "middle_order": ["batting"],
    "finisher": ["batting"],
    "pace_bowler": ["pace_bowling"],
    "fast_bowler": ["pace_bowling"],
    "seamer": ["pace_bowling"],
    "swing_bowler": ["pace_bowling"],
    "death_bowler": ["pace_bowling"],
    "new_ball_bowler": ["pace_bowling"],
    "bowler": ["pace_bowling", "spin_bowling"],
    "spinner": ["spin_bowling"],
    "spin_bowler": ["spin_bowling"],
    "off_spinner": ["spin_bowling"],
    "leg_spinner": ["spin_bowling"],
    "finger_spinner": ["spin_bowling"],
    "wrist_spinner": ["spin_bowling"],
    "left_arm_orthodox": ["spin_bowling"],
    "wicketkeeper": ["wicketkeeping"],
    "wicket_keeper": ["wicketkeeping"],
    "keeper": ["wicketkeeping"],
    "fielder": ["fielding", "throwing"],
    "all_rounder": ["batting", "pace_bowling", "spin_bowling"],
    "allrounder": ["batting", "pace_bowling", "spin_bowling"],
}

CRICKET_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "batter": ["batsman", "batting"],
    "batsman": ["batter", "batting"],
    "fast_bowler": ["pace_bowler", "bowler"],
    "pace_bowler": ["fast_bowler", "bowler"],
    "seamer": ["pace_bowler", "fast_bowler", "bowler"],
    "swing_bowler": ["pace_bowler", "fast_bowler", "bowler"],
    "spinner": ["spin_bowler", "bowler"],
    "spin_bowler": ["spinner", "bowler"],
    "off_spinner": ["spinner", "spin_bowler", "finger_spinner", "bowler"],
    "leg_spinner": ["spinner", "spin_bowler", "wrist_spinner", "bowler"],
    "wicketkeeper": ["wicket_keeper", "keeper"],
    "wicket_keeper": ["wicketkeeper", "keeper"],
    "all_rounder": ["allrounder", "batter", "bowler"],
    "allrounder": ["all_rounder", "batter", "bowler"],
}

VOLLEYBALL_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "setter": ["setting", "serving", "blocking", "defense_digging", "transition"],
    "outside_hitter": ["attacking", "passing_serve_receive", "serving", "blocking", "defense_digging", "transition"],
    "outside": ["attacking", "passing_serve_receive", "serving", "blocking", "defense_digging", "transition"],
    "left_side": ["attacking", "passing_serve_receive", "serving", "blocking", "defense_digging", "transition"],
    "opposite": ["attacking", "serving", "blocking", "defense_digging", "transition"],
    "right_side": ["attacking", "serving", "blocking", "defense_digging", "transition"],
    "middle_blocker": ["blocking", "attacking", "serving", "transition"],
    "middle_hitter": ["blocking", "attacking", "serving", "transition"],
    "middle": ["blocking", "attacking", "serving", "transition"],
    "libero": ["passing_serve_receive", "defense_digging", "serving", "transition"],
    "defensive_specialist": ["passing_serve_receive", "defense_digging", "serving", "transition"],
    "ds": ["passing_serve_receive", "defense_digging", "serving", "transition"],
    "serving_specialist": ["serving", "defense_digging"],
    "pin_hitter": ["attacking", "passing_serve_receive", "blocking", "defense_digging", "transition"],
    "hitter": ["attacking", "serving", "blocking", "transition"],
    "blocker": ["blocking", "transition"],
    "passer": ["passing_serve_receive", "defense_digging", "transition"],
}

VOLLEYBALL_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "outside": ["outside_hitter", "left_side", "pin_hitter", "hitter", "passer"],
    "outside_hitter": ["outside", "left_side", "pin_hitter", "hitter", "passer"],
    "left_side": ["outside_hitter", "outside", "pin_hitter", "hitter", "passer"],
    "opposite": ["right_side", "pin_hitter", "hitter"],
    "right_side": ["opposite", "pin_hitter", "hitter"],
    "middle": ["middle_blocker", "middle_hitter", "blocker", "hitter"],
    "middle_blocker": ["middle", "middle_hitter", "blocker", "hitter"],
    "middle_hitter": ["middle", "middle_blocker", "blocker", "hitter"],
    "libero": ["defensive_specialist", "passer"],
    "defensive_specialist": ["libero", "passer"],
    "ds": ["defensive_specialist", "libero", "passer"],
    "serving_specialist": ["server"],
    "setter": ["playmaker"],
}

FOOTBALL_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "goalkeeper": ["goalkeeping", "passing", "first_touch_receiving", "football_snc", "match_iq"],
    "keeper": ["goalkeeping", "passing", "first_touch_receiving", "football_snc", "match_iq"],
    "gk": ["goalkeeping", "passing", "first_touch_receiving", "football_snc", "match_iq"],
    "center_back": ["defending_pressing", "passing", "first_touch_receiving", "team_tactics", "football_snc"],
    "centre_back": ["defending_pressing", "passing", "first_touch_receiving", "team_tactics", "football_snc"],
    "central_defender": ["defending_pressing", "passing", "first_touch_receiving", "team_tactics", "football_snc"],
    "fullback_wingback": ["defending_pressing", "crossing_chance_creation", "dribbling_1v1", "passing", "football_snc"],
    "fullback": ["defending_pressing", "crossing_chance_creation", "dribbling_1v1", "passing", "football_snc"],
    "wingback": ["defending_pressing", "crossing_chance_creation", "dribbling_1v1", "passing", "football_snc"],
    "defensive_midfielder": ["defending_pressing", "passing", "first_touch_receiving", "team_tactics", "football_snc"],
    "holding_midfielder": ["defending_pressing", "passing", "first_touch_receiving", "team_tactics", "football_snc"],
    "central_midfielder": ["passing", "first_touch_receiving", "dribbling_1v1", "team_tactics", "football_snc"],
    "box_to_box_midfielder": ["passing", "first_touch_receiving", "dribbling_1v1", "team_tactics", "football_snc"],
    "attacking_midfielder": ["passing", "first_touch_receiving", "dribbling_1v1", "shooting_finishing", "team_tactics"],
    "playmaker": ["passing", "first_touch_receiving", "dribbling_1v1", "shooting_finishing", "team_tactics"],
    "winger_wide_forward": ["dribbling_1v1", "crossing_chance_creation", "shooting_finishing", "passing", "football_snc"],
    "winger": ["dribbling_1v1", "crossing_chance_creation", "shooting_finishing", "passing", "football_snc"],
    "wide_forward": ["dribbling_1v1", "crossing_chance_creation", "shooting_finishing", "passing", "football_snc"],
    "striker_center_forward": ["shooting_finishing", "first_touch_receiving", "crossing_chance_creation", "team_tactics", "football_snc"],
    "striker": ["shooting_finishing", "first_touch_receiving", "crossing_chance_creation", "team_tactics", "football_snc"],
    "center_forward": ["shooting_finishing", "first_touch_receiving", "crossing_chance_creation", "team_tactics", "football_snc"],
    "centre_forward": ["shooting_finishing", "first_touch_receiving", "crossing_chance_creation", "team_tactics", "football_snc"],
    "forward": ["shooting_finishing", "first_touch_receiving", "crossing_chance_creation", "team_tactics", "football_snc"],
}

FOOTBALL_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "goalkeeper": ["keeper", "gk"],
    "keeper": ["goalkeeper", "gk"],
    "gk": ["goalkeeper", "keeper"],
    "center_back": ["centre_back", "central_defender", "defender"],
    "centre_back": ["center_back", "central_defender", "defender"],
    "fullback_wingback": ["fullback", "wingback", "wide_defender"],
    "fullback": ["fullback_wingback", "wingback", "wide_defender"],
    "wingback": ["fullback_wingback", "fullback", "wide_defender"],
    "defensive_midfielder": ["number_6", "holding_midfielder", "midfielder"],
    "holding_midfielder": ["defensive_midfielder", "number_6", "midfielder"],
    "central_midfielder": ["number_8", "box_to_box_midfielder", "midfielder"],
    "attacking_midfielder": ["number_10", "playmaker", "midfielder"],
    "winger_wide_forward": ["winger", "wide_forward", "wide_attacker"],
    "winger": ["winger_wide_forward", "wide_forward", "wide_attacker"],
    "wide_forward": ["winger_wide_forward", "winger", "wide_attacker"],
    "striker_center_forward": ["striker", "center_forward", "centre_forward", "forward"],
    "striker": ["striker_center_forward", "center_forward", "centre_forward", "forward"],
    "center_forward": ["striker_center_forward", "striker", "centre_forward", "forward"],
    "centre_forward": ["striker_center_forward", "striker", "center_forward", "forward"],
}

BASKETBALL_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "point_guard": ["ball_handling", "passing", "pick_and_roll", "off_ball_movement", "defense_closeouts", "match_iq", "basketball_snc"],
    "pg": ["ball_handling", "passing", "pick_and_roll", "off_ball_movement", "defense_closeouts", "match_iq", "basketball_snc"],
    "shooting_guard": ["shooting", "ball_handling", "finishing", "off_ball_movement", "defense_closeouts", "match_iq", "basketball_snc"],
    "sg": ["shooting", "ball_handling", "finishing", "off_ball_movement", "defense_closeouts", "match_iq", "basketball_snc"],
    "wing": ["shooting", "finishing", "off_ball_movement", "defense_closeouts", "rebounding", "transition", "basketball_snc"],
    "small_forward": ["shooting", "finishing", "off_ball_movement", "defense_closeouts", "rebounding", "transition", "basketball_snc"],
    "sf": ["shooting", "finishing", "off_ball_movement", "defense_closeouts", "rebounding", "transition", "basketball_snc"],
    "power_forward": ["finishing", "rebounding", "defense_closeouts", "pick_and_roll", "off_ball_movement", "basketball_snc"],
    "pf": ["finishing", "rebounding", "defense_closeouts", "pick_and_roll", "off_ball_movement", "basketball_snc"],
    "center": ["finishing", "rebounding", "defense_closeouts", "pick_and_roll", "basketball_snc"],
    "centre": ["finishing", "rebounding", "defense_closeouts", "pick_and_roll", "basketball_snc"],
    "big": ["finishing", "rebounding", "defense_closeouts", "pick_and_roll", "basketball_snc"],
    "combo_guard": ["ball_handling", "passing", "shooting", "finishing", "pick_and_roll", "defense_closeouts", "match_iq"],
    "stretch_big": ["shooting", "finishing", "rebounding", "pick_and_roll", "defense_closeouts", "basketball_snc"],
}

BASKETBALL_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "point_guard": ["pg", "guard", "guards", "lead_guard", "primary_ball_handler"],
    "pg": ["point_guard", "guard", "guards", "lead_guard", "primary_ball_handler"],
    "shooting_guard": ["sg", "guard", "guards", "off_guard", "wing", "wings"],
    "sg": ["shooting_guard", "guard", "guards", "off_guard", "wing", "wings"],
    "guard": ["guards", "point_guard", "shooting_guard", "combo_guard"],
    "guards": ["guard", "point_guard", "shooting_guard", "combo_guard"],
    "small_forward": ["sf", "wing", "wings", "forward"],
    "sf": ["small_forward", "wing", "wings", "forward"],
    "wing": ["wings", "small_forward", "shooting_guard", "sf", "sg", "forward"],
    "wings": ["wing", "small_forward", "shooting_guard", "sf", "sg", "forward"],
    "power_forward": ["pf", "forward", "big", "posts"],
    "pf": ["power_forward", "forward", "big", "posts"],
    "center": ["centre", "big", "post", "posts"],
    "centre": ["center", "big", "post", "posts"],
    "big": ["center", "centre", "power_forward", "post", "posts"],
    "post": ["posts", "center", "big"],
    "posts": ["post", "center", "big", "power_forward"],
    "combo_guard": ["point_guard", "shooting_guard", "guard", "guards"],
    "stretch_big": ["power_forward", "center", "big", "post", "posts"],
}

BOXING_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "out_boxer": ["style_archetypes", "footwork_ringcraft", "punch_mechanics", "defense_countering", "tactical_iq"],
    "outboxer": ["style_archetypes", "footwork_ringcraft", "punch_mechanics", "defense_countering", "tactical_iq"],
    "outside_fighter": ["style_archetypes", "footwork_ringcraft", "punch_mechanics", "defense_countering", "tactical_iq"],
    "pressure_fighter": ["style_archetypes", "footwork_ringcraft", "defense_countering", "sparring_contact", "boxing_strength_conditioning"],
    "swarmer": ["style_archetypes", "footwork_ringcraft", "defense_countering", "sparring_contact", "boxing_strength_conditioning"],
    "inside_fighter": ["style_archetypes", "defense_countering", "punch_mechanics", "sparring_contact", "boxing_strength_conditioning"],
    "counterpuncher": ["style_archetypes", "defense_countering", "tactical_iq", "punch_mechanics"],
    "counter_puncher": ["style_archetypes", "defense_countering", "tactical_iq", "punch_mechanics"],
    "boxer_puncher": ["style_archetypes", "punch_mechanics", "tactical_iq", "boxing_strength_conditioning"],
    "brawler_puncher": ["style_archetypes", "punch_mechanics", "sparring_contact", "boxing_strength_conditioning"],
    "brawler": ["style_archetypes", "punch_mechanics", "sparring_contact", "boxing_strength_conditioning"],
    "puncher": ["style_archetypes", "punch_mechanics", "boxing_strength_conditioning"],
    "southpaw": ["southpaw_orthodox", "footwork_ringcraft", "tactical_iq"],
    "orthodox": ["southpaw_orthodox", "footwork_ringcraft", "tactical_iq"],
}

BOXING_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "out_boxer": ["outboxer", "outside_fighter", "long_range"],
    "outboxer": ["out_boxer", "outside_fighter", "long_range"],
    "outside_fighter": ["out_boxer", "outboxer", "long_range"],
    "pressure_fighter": ["swarmer", "pressure", "inside_fighter"],
    "swarmer": ["pressure_fighter", "pressure", "inside_fighter"],
    "inside_fighter": ["pressure_fighter", "swarmer", "close_range"],
    "counterpuncher": ["counter_puncher", "counter"],
    "counter_puncher": ["counterpuncher", "counter"],
    "boxer_puncher": ["adaptive_style", "power_boxer"],
    "brawler_puncher": ["brawler", "puncher", "power_puncher"],
    "brawler": ["brawler_puncher", "puncher", "power_puncher"],
    "southpaw": ["left_handed", "opposite_stance"],
    "orthodox": ["right_handed", "opposite_stance"],
}

MMA_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner_mma": ["mma_level_progression", "mma_stance_guard", "mma_wrestling", "mma_ground_control", "mma_strength_conditioning"],
    "mma_generalist": ["mma_fight_iq", "mma_striking_entries", "mma_wrestling", "mma_ground_control", "mma_strength_conditioning"],
    "mixed_martial_artist": ["mma_fight_iq", "mma_striking_entries", "mma_wrestling", "mma_ground_control", "mma_strength_conditioning"],
    "striker": ["mma_stance_guard", "mma_striking_entries", "mma_kicking", "mma_striking_defense", "mma_range_management"],
    "kickboxer": ["mma_stance_guard", "mma_striking_entries", "mma_kicking", "mma_clinch_cage", "mma_range_management"],
    "muay_thai": ["mma_stance_guard", "mma_striking_entries", "mma_kicking", "mma_clinch_cage", "mma_range_management"],
    "wrestler": ["mma_wrestling", "mma_takedown_entries", "mma_takedown_defense", "mma_clinch_cage", "mma_ground_control"],
    "grappler": ["mma_ground_control", "mma_submissions", "mma_escapes_scrambles", "mma_takedown_defense", "mma_clinch_cage"],
    "bjj_grappler": ["mma_ground_control", "mma_submissions", "mma_escapes_scrambles", "mma_transitions"],
    "bjj": ["mma_ground_control", "mma_submissions", "mma_escapes_scrambles", "mma_transitions"],
    "pressure_fighter": ["mma_range_management", "mma_clinch_cage", "mma_wrestling", "mma_striking_entries", "mma_strength_conditioning"],
    "counter_fighter": ["mma_range_management", "mma_striking_defense", "mma_fight_iq", "mma_takedown_defense"],
    "southpaw": ["mma_stance_guard", "mma_range_management", "mma_striking_entries", "mma_fight_iq"],
    "orthodox": ["mma_stance_guard", "mma_range_management", "mma_striking_entries", "mma_fight_iq"],
}

MMA_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "beginner_mma": ["beginner", "new_mma_user"],
    "mma_generalist": ["mixed_martial_artist", "all_rounder", "all_around"],
    "mixed_martial_artist": ["mma_generalist", "all_rounder", "all_around"],
    "striker": ["standup_fighter", "boxing_based", "striking_based"],
    "kickboxer": ["muay_thai", "k1", "standup_fighter"],
    "muay_thai": ["kickboxer", "striker"],
    "wrestler": ["wrestling_based", "takedown_fighter"],
    "grappler": ["submission_grappler", "ground_fighter"],
    "bjj_grappler": ["bjj", "jiu_jitsu", "submission_grappler"],
    "bjj": ["bjj_grappler", "jiu_jitsu", "submission_grappler"],
    "pressure_fighter": ["pressure", "cage_pressure"],
    "counter_fighter": ["counter_striker", "counter"],
    "southpaw": ["left_handed", "opposite_stance"],
    "orthodox": ["right_handed"],
}

KICKBOXING_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner_kickboxer": ["kickboxing_level_progression", "kickboxing_stance_guard", "kickboxing_footwork_ringcraft", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_defense_countering"],
    "beginner": ["kickboxing_level_progression", "kickboxing_stance_guard", "kickboxing_footwork_ringcraft", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics"],
    "point_fighter": ["kickboxing_rules_scoring", "kickboxing_style_differences", "kickboxing_footwork_ringcraft", "kickboxing_combinations_entries_exits", "kickboxing_defense_countering"],
    "point_fighting": ["kickboxing_rules_scoring", "kickboxing_style_differences", "kickboxing_footwork_ringcraft", "kickboxing_combinations_entries_exits"],
    "light_contact_fighter": ["kickboxing_rules_scoring", "kickboxing_style_differences", "kickboxing_combinations_entries_exits", "kickboxing_defense_countering", "kickboxing_sparring_contact"],
    "light_contact": ["kickboxing_rules_scoring", "kickboxing_style_differences", "kickboxing_combinations_entries_exits", "kickboxing_sparring_contact"],
    "kick_light_fighter": ["kickboxing_rules_scoring", "kickboxing_kick_defense_checks", "kickboxing_kick_mechanics", "kickboxing_sparring_contact", "kickboxing_injury_load_management"],
    "kick_light": ["kickboxing_rules_scoring", "kickboxing_kick_defense_checks", "kickboxing_kick_mechanics", "kickboxing_sparring_contact"],
    "full_contact_kickboxer": ["kickboxing_rules_scoring", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_combinations_entries_exits", "kickboxing_strength_conditioning"],
    "full_contact": ["kickboxing_rules_scoring", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_combinations_entries_exits"],
    "low_kick_fighter": ["kickboxing_rules_scoring", "kickboxing_kick_mechanics", "kickboxing_kick_defense_checks", "kickboxing_injury_load_management", "kickboxing_strength_conditioning"],
    "low_kick": ["kickboxing_rules_scoring", "kickboxing_kick_mechanics", "kickboxing_kick_defense_checks", "kickboxing_injury_load_management"],
    "k1_fighter": ["kickboxing_rules_scoring", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_clinch_knees_rule_dependent", "kickboxing_competition_week"],
    "k1": ["kickboxing_rules_scoring", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_clinch_knees_rule_dependent"],
    "k_1": ["kickboxing_rules_scoring", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_clinch_knees_rule_dependent"],
    "pressure_fighter": ["kickboxing_footwork_ringcraft", "kickboxing_combinations_entries_exits", "kickboxing_defense_countering", "kickboxing_strength_conditioning"],
    "outfighter": ["kickboxing_footwork_ringcraft", "kickboxing_kick_mechanics", "kickboxing_defense_countering", "kickboxing_style_differences"],
    "outside_fighter": ["kickboxing_footwork_ringcraft", "kickboxing_kick_mechanics", "kickboxing_defense_countering"],
    "counter_fighter": ["kickboxing_defense_countering", "kickboxing_kick_defense_checks", "kickboxing_footwork_ringcraft", "kickboxing_style_differences"],
    "counter_striker": ["kickboxing_defense_countering", "kickboxing_kick_defense_checks", "kickboxing_footwork_ringcraft"],
    "kicker": ["kickboxing_kick_mechanics", "kickboxing_kick_defense_checks", "kickboxing_injury_load_management", "kickboxing_strength_conditioning"],
    "boxer_kickboxer": ["kickboxing_punch_mechanics", "kickboxing_combinations_entries_exits", "kickboxing_kick_defense_checks", "kickboxing_footwork_ringcraft"],
    "southpaw": ["kickboxing_stance_guard", "kickboxing_footwork_ringcraft", "kickboxing_defense_countering"],
    "orthodox": ["kickboxing_stance_guard", "kickboxing_footwork_ringcraft", "kickboxing_defense_countering"],
    "fitness_kickboxing": ["kickboxing_level_progression", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics", "kickboxing_injury_load_management"],
    "no_sparring": ["kickboxing_level_progression", "kickboxing_injury_load_management", "kickboxing_punch_mechanics", "kickboxing_kick_mechanics"],
}

KICKBOXING_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "beginner_kickboxer": ["beginner", "new_kickboxer"],
    "point_fighter": ["point_fighting", "tatami_fighter"],
    "point_fighting": ["point_fighter", "tatami_fighter"],
    "light_contact_fighter": ["light_contact"],
    "kick_light_fighter": ["kick_light"],
    "full_contact_kickboxer": ["full_contact"],
    "low_kick_fighter": ["low_kick"],
    "k1_fighter": ["k1", "k_1", "glory_style"],
    "k1": ["k1_fighter", "k_1", "glory_style"],
    "k_1": ["k1", "k1_fighter", "glory_style"],
    "pressure_fighter": ["pressure"],
    "outfighter": ["outside_fighter", "range_fighter"],
    "outside_fighter": ["outfighter", "range_fighter"],
    "counter_fighter": ["counter_striker", "counter"],
    "kicker": ["kick_specialist"],
    "boxer_kickboxer": ["boxing_based", "hands_heavy"],
    "southpaw": ["left_handed", "opposite_stance"],
    "orthodox": ["right_handed", "opposite_stance"],
    "fitness_kickboxing": ["fitness", "bag_work", "no_sparring"],
}

WRESTLING_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner_wrestler": ["wrestling_level_progression", "wrestling_stance_motion", "wrestling_takedown_defense", "wrestling_top_control_turns", "wrestling_bottom_escapes_reversals"],
    "folkstyle_wrestler": ["wrestling_rules_scoring", "wrestling_top_control_turns", "wrestling_bottom_escapes_reversals", "wrestling_mat_returns", "wrestling_match_iq"],
    "folkstyle": ["wrestling_rules_scoring", "wrestling_top_control_turns", "wrestling_bottom_escapes_reversals", "wrestling_mat_returns", "wrestling_match_iq"],
    "freestyle_wrestler": ["wrestling_rules_scoring", "wrestling_takedown_offense", "wrestling_par_terre", "wrestling_edge_tactics", "wrestling_match_iq"],
    "freestyle": ["wrestling_rules_scoring", "wrestling_takedown_offense", "wrestling_par_terre", "wrestling_edge_tactics", "wrestling_match_iq"],
    "greco_wrestler": ["wrestling_rules_scoring", "wrestling_hand_fighting_ties", "wrestling_par_terre", "wrestling_style_differences", "wrestling_strength_conditioning"],
    "greco": ["wrestling_rules_scoring", "wrestling_hand_fighting_ties", "wrestling_par_terre", "wrestling_style_differences", "wrestling_strength_conditioning"],
    "greco_roman": ["wrestling_rules_scoring", "wrestling_hand_fighting_ties", "wrestling_par_terre", "wrestling_style_differences", "wrestling_strength_conditioning"],
    "leg_attacker": ["wrestling_stance_motion", "wrestling_takedown_offense", "wrestling_takedown_defense", "wrestling_scrambles"],
    "upper_body_wrestler": ["wrestling_hand_fighting_ties", "wrestling_takedown_offense", "wrestling_par_terre", "wrestling_strength_conditioning"],
    "counter_wrestler": ["wrestling_takedown_defense", "wrestling_hand_fighting_ties", "wrestling_scrambles", "wrestling_match_iq"],
    "top_rider": ["wrestling_top_control_turns", "wrestling_mat_returns", "wrestling_strength_conditioning"],
    "bottom_escape_specialist": ["wrestling_bottom_escapes_reversals", "wrestling_scrambles", "wrestling_match_iq"],
    "scrambler": ["wrestling_scrambles", "wrestling_takedown_defense", "wrestling_bottom_escapes_reversals"],
}

WRESTLING_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "beginner_wrestler": ["beginner", "new_wrestler"],
    "folkstyle_wrestler": ["folkstyle", "scholastic", "collegiate"],
    "folkstyle": ["folkstyle_wrestler", "scholastic", "collegiate"],
    "freestyle_wrestler": ["freestyle"],
    "freestyle": ["freestyle_wrestler"],
    "greco_wrestler": ["greco", "greco_roman"],
    "greco": ["greco_wrestler", "greco_roman"],
    "greco_roman": ["greco_wrestler", "greco"],
    "leg_attacker": ["shot_wrestler", "single_leg", "double_leg"],
    "upper_body_wrestler": ["thrower", "greco_style"],
    "counter_wrestler": ["defensive_wrestler", "reattack"],
    "top_rider": ["rider", "top_wrestler"],
    "bottom_escape_specialist": ["bottom_wrestler", "escape_specialist"],
    "scrambler": ["scramble_wrestler", "funk"],
}

RUNNING_EVENT_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner": ["run_walk_foundation", "easy_aerobic_base", "return_to_run"],
    "return_to_running": ["return_to_run", "run_walk_foundation", "easy_aerobic_base"],
    "return_to_run": ["return_to_run", "run_walk_foundation", "easy_aerobic_base"],
    "5k": ["threshold_tempo", "intervals_vo2", "speed_strides_hills", "race_specificity"],
    "10k": ["threshold_tempo", "intervals_vo2", "long_run", "race_specificity"],
    "half_marathon": ["long_run", "threshold_tempo", "race_specificity", "easy_aerobic_base"],
    "marathon": ["long_run", "race_specificity", "easy_aerobic_base", "heat_environment"],
    "ultra": ["long_run", "trail_hill_terrain", "easy_aerobic_base", "heat_environment"],
    "trail": ["trail_hill_terrain", "long_run", "running_strength_conditioning", "heat_environment"],
    "trail_running": ["trail_hill_terrain", "long_run", "running_strength_conditioning", "heat_environment"],
    "speed": ["speed_strides_hills", "intervals_vo2", "running_strength_conditioning"],
    "run_fast": ["speed_strides_hills", "intervals_vo2", "running_strength_conditioning"],
}

BADMINTON_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "singles": ["singles_tactics", "footwork_recovery", "clear_drop_smash", "serve_return", "badminton_strength_conditioning", "stroke_mechanics_deep", "footwork_movement_court_coverage", "tactics_sport_iq"],
    "single": ["singles_tactics", "footwork_recovery", "clear_drop_smash", "serve_return", "badminton_strength_conditioning", "stroke_mechanics_deep", "footwork_movement_court_coverage", "tactics_sport_iq"],
    "doubles": ["doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash", "footwork_recovery", "stroke_mechanics_deep", "footwork_movement_court_coverage", "tactics_sport_iq"],
    "double": ["doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash", "footwork_recovery", "stroke_mechanics_deep", "footwork_movement_court_coverage", "tactics_sport_iq"],
    "mixed_doubles": ["mixed_doubles_tactics", "doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash", "stroke_mechanics_deep", "tactics_sport_iq"],
    "mixed": ["mixed_doubles_tactics", "doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash", "stroke_mechanics_deep", "tactics_sport_iq"],
    "xd": ["mixed_doubles_tactics", "doubles_tactics", "serve_return", "drive_lift_block_net", "clear_drop_smash", "stroke_mechanics_deep", "tactics_sport_iq"],
    "front_court": ["drive_lift_block_net", "serve_return", "doubles_tactics", "stroke_mechanics_deep", "tactics_sport_iq"],
    "net_player": ["drive_lift_block_net", "serve_return", "doubles_tactics", "stroke_mechanics_deep", "tactics_sport_iq"],
    "rear_court": ["clear_drop_smash", "doubles_tactics", "badminton_strength_conditioning", "stroke_mechanics_deep", "footwork_movement_court_coverage", "badminton_injury_snc_load_return_to_court"],
    "back_court": ["clear_drop_smash", "doubles_tactics", "badminton_strength_conditioning", "stroke_mechanics_deep", "footwork_movement_court_coverage", "badminton_injury_snc_load_return_to_court"],
}

BADMINTON_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "singles": ["single"],
    "single": ["singles"],
    "doubles": ["double", "front_court", "rear_court"],
    "double": ["doubles", "front_court", "rear_court"],
    "mixed_doubles": ["mixed", "xd", "front_court", "rear_court"],
    "mixed": ["mixed_doubles", "xd"],
    "xd": ["mixed_doubles", "mixed"],
    "front_court": ["net_player", "doubles"],
    "net_player": ["front_court", "doubles"],
    "rear_court": ["back_court", "doubles"],
    "back_court": ["rear_court", "doubles"],
}

TENNIS_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "aggressive_baseliner": ["forehand_backhand", "singles_tactics", "serve_return", "footwork_recovery", "tennis_strength_conditioning", "stroke_mechanics_deep", "tactics_match_iq_deep"],
    "baseline_attacker": ["forehand_backhand", "singles_tactics", "serve_return", "footwork_recovery", "stroke_mechanics_deep"],
    "power_baseliner": ["forehand_backhand", "singles_tactics", "serve_return", "tennis_strength_conditioning"],
    "counterpuncher": ["forehand_backhand", "singles_tactics", "footwork_recovery", "surface_adaptation", "injury_load_management", "movement_surface_deep", "tactics_match_iq_deep"],
    "defensive_retriever": ["forehand_backhand", "singles_tactics", "footwork_recovery", "surface_adaptation", "movement_surface_deep"],
    "retriever": ["forehand_backhand", "singles_tactics", "footwork_recovery", "surface_adaptation"],
    "all_court_player": ["forehand_backhand", "volley_net_play", "singles_tactics", "serve_return", "footwork_recovery", "stroke_mechanics_deep", "movement_surface_deep"],
    "serve_and_volley_player": ["serve_return", "volley_net_play", "doubles_tactics", "footwork_recovery", "tennis_strength_conditioning"],
    "big_server": ["serve_return", "tennis_strength_conditioning", "injury_load_management", "singles_tactics"],
    "doubles_net_player": ["doubles_tactics", "volley_net_play", "serve_return", "footwork_recovery", "doubles_systems_deep"],
    "doubles_baseline_player": ["doubles_tactics", "serve_return", "forehand_backhand", "footwork_recovery", "doubles_systems_deep"],
    "singles": ["singles_tactics", "serve_return", "forehand_backhand", "footwork_recovery", "surface_adaptation"],
    "single": ["singles_tactics", "serve_return", "forehand_backhand", "footwork_recovery", "surface_adaptation"],
    "doubles": ["doubles_tactics", "serve_return", "volley_net_play", "footwork_recovery", "doubles_systems_deep"],
    "double": ["doubles_tactics", "serve_return", "volley_net_play", "footwork_recovery", "doubles_systems_deep"],
    "one_handed_backhand": ["forehand_backhand", "surface_adaptation", "injury_load_management", "stroke_mechanics_deep"],
    "two_handed_backhand": ["forehand_backhand", "singles_tactics", "stroke_mechanics_deep"],
    "left_handed_player": ["serve_return", "singles_tactics", "doubles_tactics", "tactics_match_iq_deep"],
}

TENNIS_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "aggressive_baseliner": ["baseline_attacker", "power_baseliner", "baseliner"],
    "baseline_attacker": ["aggressive_baseliner", "power_baseliner", "baseliner"],
    "counterpuncher": ["defensive_baseliner", "defensive_retriever", "retriever"],
    "defensive_retriever": ["counterpuncher", "defensive_baseliner", "retriever"],
    "all_court_player": ["all_round_player", "net_transition_player"],
    "serve_and_volley_player": ["net_rusher", "attacking_net_player"],
    "big_server": ["serve_dominant_player", "first_strike_player"],
    "doubles_net_player": ["net_player", "poacher", "doubles"],
    "doubles_baseline_player": ["returner", "doubles"],
    "singles": ["single"],
    "single": ["singles"],
    "doubles": ["double", "doubles_net_player", "doubles_baseline_player"],
    "double": ["doubles", "doubles_net_player", "doubles_baseline_player"],
    "one_handed_backhand": ["single_handed_backhand", "backhand_player"],
    "two_handed_backhand": ["double_handed_backhand", "backhand_player"],
    "left_handed_player": ["lefty", "southpaw_tennis"],
}

SWIMMING_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "beginner_swimmer": ["water_confidence_safety", "freestyle", "injury_load_management", "beginner_safety_learn_to_swim"],
    "learn_to_swim": ["water_confidence_safety", "freestyle", "beginner_safety_learn_to_swim"],
    "non_swimmer": ["water_confidence_safety", "beginner_safety_learn_to_swim"],
    "fitness_swimmer": ["freestyle", "event_programming", "swimming_strength_conditioning", "injury_load_management"],
    "freestyle_sprinter": ["freestyle", "starts_turns_underwaters", "event_programming", "swimming_strength_conditioning", "stroke_mechanics_deep"],
    "sprint_freestyle": ["freestyle", "starts_turns_underwaters", "event_programming", "swimming_strength_conditioning"],
    "middle_distance_swimmer": ["freestyle", "event_programming", "starts_turns_underwaters", "injury_load_management"],
    "distance_swimmer": ["freestyle", "event_programming", "injury_load_management", "open_water_triathlon"],
    "backstroke_swimmer": ["backstroke", "starts_turns_underwaters", "injury_load_management", "stroke_mechanics_deep"],
    "breaststroke_swimmer": ["breaststroke", "event_programming", "injury_load_management", "stroke_mechanics_deep"],
    "butterfly_swimmer": ["butterfly", "starts_turns_underwaters", "injury_load_management", "stroke_mechanics_deep"],
    "im_swimmer": ["freestyle", "backstroke", "breaststroke", "butterfly", "starts_turns_underwaters", "event_programming"],
    "individual_medley": ["freestyle", "backstroke", "breaststroke", "butterfly", "starts_turns_underwaters", "event_programming"],
    "open_water_swimmer": ["open_water_triathlon", "freestyle", "event_programming", "injury_load_management"],
    "triathlon_swimmer": ["open_water_triathlon", "freestyle", "event_programming", "swimming_strength_conditioning"],
    "masters_swimmer": ["freestyle", "event_programming", "injury_load_management", "swimming_strength_conditioning"],
    "youth_development": ["water_confidence_safety", "freestyle", "starts_turns_underwaters", "event_programming"],
}

SWIMMING_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "beginner_swimmer": ["learn_to_swim", "water_confidence", "non_swimmer"],
    "learn_to_swim": ["beginner_swimmer", "water_confidence", "non_swimmer"],
    "fitness_swimmer": ["general_swimmer", "recreational_swimmer", "masters_swimmer"],
    "freestyle_sprinter": ["sprint_freestyle", "50m", "100m"],
    "sprint_freestyle": ["freestyle_sprinter", "50m", "100m"],
    "middle_distance_swimmer": ["200m", "400m", "middle_distance"],
    "distance_swimmer": ["800m", "1500m", "distance_freestyle"],
    "backstroke_swimmer": ["backstroke"],
    "breaststroke_swimmer": ["breaststroke"],
    "butterfly_swimmer": ["butterfly", "fly"],
    "im_swimmer": ["individual_medley", "medley"],
    "individual_medley": ["im_swimmer", "medley"],
    "open_water_swimmer": ["open_water", "distance_swimmer"],
    "triathlon_swimmer": ["triathlon", "open_water_swimmer"],
    "masters_swimmer": ["adult_swimmer", "fitness_swimmer"],
    "youth_development": ["youth_swimmer", "age_group_swimmer"],
}

CYCLING_ROLE_DOMAIN_TAGS: Dict[str, List[str]] = {
    "road_cyclist": ["road_criterium", "endurance_power_programming", "bike_handling_safety", "discipline_tactics"],
    "road_rider": ["road_criterium", "endurance_power_programming", "bike_handling_safety", "discipline_tactics"],
    "road_racer": ["road_criterium", "endurance_power_programming", "discipline_tactics"],
    "criterium_racer": ["road_criterium", "discipline_tactics", "bike_handling_safety", "track_bmx_power"],
    "crit_racer": ["road_criterium", "discipline_tactics", "bike_handling_safety"],
    "time_trialist": ["time_trial_triathlon", "endurance_power_programming", "injury_snc_bike_fit_load"],
    "time_trial": ["time_trial_triathlon", "endurance_power_programming", "injury_snc_bike_fit_load"],
    "tt": ["time_trial_triathlon", "endurance_power_programming", "injury_snc_bike_fit_load"],
    "track_sprinter": ["track_bmx_power", "discipline_tactics", "injury_snc_bike_fit_load"],
    "track_endurance": ["track_bmx_power", "endurance_power_programming", "discipline_tactics"],
    "mountain_biker": ["mtb_gravel_cyclocross", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "mtb": ["mtb_gravel_cyclocross", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "gravel_cyclist": ["mtb_gravel_cyclocross", "endurance_power_programming", "discipline_tactics"],
    "gravel": ["mtb_gravel_cyclocross", "endurance_power_programming", "discipline_tactics"],
    "cyclocross_rider": ["mtb_gravel_cyclocross", "track_bmx_power", "discipline_tactics"],
    "cyclocross": ["mtb_gravel_cyclocross", "track_bmx_power", "discipline_tactics"],
    "cx": ["mtb_gravel_cyclocross", "track_bmx_power", "discipline_tactics"],
    "bmx_racer": ["track_bmx_power", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "bmx": ["track_bmx_power", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "triathlon_cyclist": ["time_trial_triathlon", "endurance_power_programming", "injury_snc_bike_fit_load"],
    "triathlete": ["time_trial_triathlon", "endurance_power_programming", "injury_snc_bike_fit_load"],
    "commuter_cyclist": ["beginner_confidence_safety", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "commuter": ["beginner_confidence_safety", "bike_handling_safety", "injury_snc_bike_fit_load"],
    "fitness_cyclist": ["beginner_confidence_safety", "endurance_power_programming", "level_progression"],
    "beginner_cyclist": ["beginner_confidence_safety", "bike_handling_safety", "level_progression"],
}

CYCLING_ROLE_EQUIVALENTS: Dict[str, List[str]] = {
    "road_cyclist": ["road", "road_rider", "road_racer"],
    "road_rider": ["road_cyclist", "road"],
    "road_racer": ["road_cyclist", "road"],
    "criterium_racer": ["criterium", "crit_racer", "crit"],
    "crit_racer": ["criterium_racer", "criterium", "crit"],
    "time_trialist": ["time_trial", "tt", "tt_rider"],
    "time_trial": ["time_trialist", "tt"],
    "tt": ["time_trialist", "time_trial"],
    "track_sprinter": ["track_sprint", "sprinter", "track_cyclist"],
    "track_endurance": ["track_endurance_rider", "track_cyclist"],
    "mountain_biker": ["mtb", "mountain_bike", "xc", "trail_rider"],
    "mtb": ["mountain_biker", "mountain_bike", "xc"],
    "gravel_cyclist": ["gravel", "gravel_rider"],
    "cyclocross_rider": ["cyclocross", "cx"],
    "cyclocross": ["cyclocross_rider", "cx"],
    "bmx_racer": ["bmx", "bmx_racing"],
    "triathlon_cyclist": ["triathlon", "triathlete"],
    "commuter_cyclist": ["commuter", "commuting"],
    "fitness_cyclist": ["fitness", "recreational_cyclist", "beginner_cyclist"],
}

CRICKET_SPECIFIC_BOWLING_ROLES = {
    "fast_bowler",
    "pace_bowler",
    "seamer",
    "swing_bowler",
    "death_bowler",
    "new_ball_bowler",
    "spinner",
    "spin_bowler",
    "off_spinner",
    "leg_spinner",
    "finger_spinner",
    "wrist_spinner",
    "left_arm_orthodox",
}

LEVEL_ORDER = {
    "beginner": 1,
    "novice": 1,
    "intermediate": 2,
    "advanced": 3,
    "elite": 4,
}


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _tokens(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        items: List[str] = []
        for nested in value.values():
            items.extend(_tokens(nested))
        return items
    if isinstance(value, (list, tuple, set)):
        items = []
        for nested in value:
            items.extend(_tokens(nested))
        return items
    text = str(value).strip()
    if not text:
        return []
    compact = _norm(text)
    parts = [_norm(part) for part in re.split(r"[,;/|]+|\s+", text) if _norm(part)]
    return sorted(set([compact, *parts]))


def _clean_list(value: Any) -> List[Any]:
    if not value:
        return []
    items = value if isinstance(value, list) else [value]
    return [item for item in items if item not in (None, "", [], {})]


def _text_list(doc: Dict[str, Any], fields: Sequence[str]) -> List[str]:
    values: List[str] = []
    for field in fields:
        value = doc.get(field)
        if isinstance(value, list):
            values.extend(str(item) for item in value if item not in (None, ""))
        elif value not in (None, ""):
            values.append(str(value))
    return values


def _infer_profile_age(profile: Dict[str, Any]) -> Optional[int]:
    raw_age = profile.get("age")
    if raw_age not in (None, ""):
        try:
            age = int(raw_age)
            return age if 0 < age < 120 else None
        except (TypeError, ValueError):
            pass

    raw_year = profile.get("birth_year") or profile.get("year_of_birth")
    if raw_year not in (None, ""):
        try:
            birth_year = int(raw_year)
            return date.today().year - birth_year
        except (TypeError, ValueError):
            pass

    dob = str(profile.get("date_of_birth") or "").strip()
    match = re.search(r"(19|20)\d{2}", dob)
    if match:
        try:
            return date.today().year - int(match.group(0))
        except ValueError:
            return None
    return None


def _safe_source_refs(doc: Dict[str, Any], *, max_refs: int = 2) -> List[Dict[str, Any]]:
    refs = doc.get("source_refs") or []
    safe_refs: List[Dict[str, Any]] = []
    for ref in refs[:max_refs]:
        if not isinstance(ref, dict):
            continue
        safe_refs.append({
            "source_book_id": ref.get("source_book_id"),
            "section_id": ref.get("section_id"),
            "section_title": ref.get("section_title"),
            "heading": ref.get("heading"),
        })
    return safe_refs


def _merge_unique_refs(records: Iterable[Dict[str, Any]], *, limit: int) -> List[Dict[str, Any]]:
    seen: set[Tuple[Optional[str], Optional[str], Optional[str]]] = set()
    refs: List[Dict[str, Any]] = []
    for record in records:
        for ref in record.get("source_refs") or []:
            if not isinstance(ref, dict):
                continue
            key = (ref.get("source_book_id"), ref.get("section_id"), ref.get("heading"))
            if key in seen:
                continue
            seen.add(key)
            refs.append({
                "source_book_id": ref.get("source_book_id"),
                "section_id": ref.get("section_id"),
                "section_title": ref.get("section_title"),
                "heading": ref.get("heading"),
            })
            if len(refs) >= limit:
                return refs
    return refs


def _profile_terms(profile: Dict[str, Any]) -> Dict[str, List[str]]:
    goals = _clean_list(profile.get("selected_goals") or profile.get("goals"))
    primary_goal = profile.get("primary_goal")
    if primary_goal and primary_goal not in goals:
        goals.insert(0, primary_goal)

    sports = [str(item) for item in _clean_list(profile.get("sports"))]
    for detail in profile.get("sport_details") or []:
        if isinstance(detail, dict) and detail.get("sport"):
            sports.append(str(detail["sport"]))

    injuries: List[Any] = list(_clean_list(profile.get("pain_areas")))
    for injury in profile.get("current_injuries") or []:
        if isinstance(injury, dict):
            injuries.extend([injury.get("area"), injury.get("note"), injury.get("status")])
            injuries.extend(_clean_list(injury.get("triggers")))
        else:
            injuries.append(injury)
    injuries.extend(_clean_list(profile.get("injury_history")))
    injuries.extend(_clean_list(profile.get("medical_notes")))

    age = _infer_profile_age(profile)
    age_context: List[str] = []
    if age is not None:
        if age < 18:
            age_context.extend(["youth", "beginner", "movement_learning"])
        if age >= 60:
            age_context.extend(["older_adults", "balance", "fall_risk", "gentle_range"])

    equipment = _clean_list(profile.get("equipment"))
    facilities = _clean_list(profile.get("facilities"))
    training_location = profile.get("training_location")
    if training_location:
        facilities.append(training_location)

    goal_tags = set(_tokens(goals))
    for goal in goals:
        goal_tags.update(GOAL_TAGS.get(str(goal).lower(), []))
    goal_tags.update(_tokens(age_context))

    sport_tags = set(_tokens(sports))
    for sport in sports:
        sport_tags.update(SPORT_QUALITY_TAGS.get(str(sport).lower(), []))

    injury_tags = set(_tokens(injuries))
    for injury in injuries:
        injury_tags.update(INJURY_TAGS.get(str(injury).lower(), []))

    equipment_tags = set(_tokens(equipment + facilities))
    if "gym" in equipment_tags or "full_gym" in equipment_tags:
        equipment_tags.update(["barbell", "dumbbell", "dumbbells", "rack", "bench", "cable", "machine"])
    if "bodyweight" in equipment_tags or "home" in equipment_tags or "indoors" in equipment_tags:
        equipment_tags.update(["bodyweight", "none", "no_equipment"])

    experience = _norm(profile.get("experience"))
    if not experience:
        experience = "intermediate"

    return {
        "goals": sorted(goal_tags),
        "sports": sorted(sport_tags),
        "injuries": sorted(injury_tags),
        "equipment": sorted(equipment_tags),
        "experience": [experience],
        "all": sorted(goal_tags | sport_tags | injury_tags | equipment_tags | {experience}),
    }


def _profile_sports(profile: Dict[str, Any]) -> List[str]:
    sports: List[str] = []
    for sport in _clean_list(profile.get("sports")):
        normalized = _norm(sport)
        sports.append(SPORT_ALIASES.get(normalized, normalized))
    for detail in profile.get("sport_details") or []:
        if isinstance(detail, dict) and detail.get("sport"):
            normalized = _norm(detail["sport"])
            sports.append(SPORT_ALIASES.get(normalized, normalized))
    return sorted(set(item for item in sports if item))


def _profile_role_tags(profile: Dict[str, Any]) -> List[str]:
    roles: List[str] = ["all_roles"]
    for detail in profile.get("sport_details") or []:
        if not isinstance(detail, dict):
            continue
        for key in ("role", "position", "position_or_style", "style"):
            if detail.get(key):
                roles.extend(_tokens(detail[key]))
        for key in ("current_skill_priority", "skill_priorities"):
            roles.extend(_tokens(detail.get(key)))
    roles.extend(_tokens(profile.get("sport_role")))
    roles.extend(_tokens(profile.get("cricket_role")))
    for role in list(roles):
        roles.extend(CRICKET_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(VOLLEYBALL_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(FOOTBALL_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(BASKETBALL_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(BOXING_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(MMA_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(KICKBOXING_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(WRESTLING_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(BADMINTON_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(TENNIS_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(SWIMMING_ROLE_EQUIVALENTS.get(role, []))
        roles.extend(CYCLING_ROLE_EQUIVALENTS.get(role, []))
    return sorted(set(item for item in roles if item))


def _sport_domains_for_profile(profile: Dict[str, Any]) -> List[str]:
    sports = _profile_sports(profile)
    roles = _profile_role_tags(profile)
    domains: List[str] = []
    for sport in sports:
        domains.extend(SPORT_BASE_DOMAINS.get(sport, []))
        if sport == "cricket":
            has_specific_bowling_role = bool(set(roles).intersection(CRICKET_SPECIFIC_BOWLING_ROLES))
            for role in roles:
                if role == "bowler" and has_specific_bowling_role:
                    continue
                domains.extend(CRICKET_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "volleyball":
            for role in roles:
                domains.extend(VOLLEYBALL_ROLE_DOMAIN_TAGS.get(role, []))
        if sport in {"soccer", "football"}:
            for role in roles:
                domains.extend(FOOTBALL_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "basketball":
            for role in roles:
                domains.extend(BASKETBALL_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "boxing":
            for role in roles:
                domains.extend(BOXING_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "mma":
            for role in roles:
                domains.extend(MMA_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "kickboxing":
            for role in roles:
                domains.extend(KICKBOXING_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "wrestling":
            for role in roles:
                domains.extend(WRESTLING_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "badminton":
            for role in roles:
                domains.extend(BADMINTON_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "tennis":
            for role in roles:
                domains.extend(TENNIS_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "swimming":
            for role in roles:
                domains.extend(SWIMMING_ROLE_DOMAIN_TAGS.get(role, []))
        if sport == "cycling":
            for role in roles:
                domains.extend(CYCLING_ROLE_DOMAIN_TAGS.get(role, []))
        if sport in {"running", "running_endurance"}:
            running_base = ["run_walk_foundation", "easy_aerobic_base", "return_to_run", "running_strength_conditioning"]
            level = _profile_terms(profile)["experience"][0]
            has_impact_risk = bool(_profile_terms(profile)["injuries"])
            domains.extend(running_base)
            if level == "beginner" or has_impact_risk:
                domains.extend(["long_run", "race_specificity"])
            else:
                for role in roles:
                    domains.extend(RUNNING_EVENT_DOMAIN_TAGS.get(role, []))
                for token in _tokens(profile.get("primary_goal")) + _tokens(profile.get("selected_goals")) + _tokens(profile.get("goals")):
                    domains.extend(RUNNING_EVENT_DOMAIN_TAGS.get(token, []))
    return sorted(set(item for item in domains if item))


def _difficulty_score(doc: Dict[str, Any], experience: str) -> int:
    difficulty = _norm(doc.get("difficulty"))
    if not difficulty:
        return 0
    user_level = LEVEL_ORDER.get(experience, 2)
    doc_level = LEVEL_ORDER.get(difficulty, 2)
    if doc_level == user_level:
        return 3
    if doc_level < user_level:
        return 1
    if doc_level == user_level + 1:
        return -2
    return -5


def _score_doc(
    doc: Dict[str, Any],
    profile_terms: Dict[str, List[str]],
    *,
    positive_fields: Sequence[str],
    injury_fields: Sequence[str] = (),
    equipment_fields: Sequence[str] = (),
    experience_sensitive: bool = False,
) -> Tuple[int, List[str]]:
    doc_terms = set(_tokens(_text_list(doc, positive_fields)))
    score = 0
    reasons: List[str] = []

    for label, weight in [("sports", 5), ("goals", 4), ("equipment", 2)]:
        matches = doc_terms.intersection(profile_terms[label])
        if matches:
            score += weight * min(3, len(matches))
            reasons.append(f"{label}:{','.join(sorted(matches)[:4])}")

    if equipment_fields:
        equipment_terms = set(_tokens(_text_list(doc, equipment_fields)))
        profile_equipment = set(profile_terms["equipment"])
        if equipment_terms:
            if equipment_terms.intersection(profile_equipment):
                score += 4
                reasons.append("equipment_match")
            elif "barbell" in equipment_terms and not profile_equipment.intersection({"barbell", "gym", "full_gym"}):
                score -= 14
                reasons.append("equipment_mismatch")

    if injury_fields:
        injury_terms = set(_tokens(_text_list(doc, injury_fields)))
        conflicts = injury_terms.intersection(profile_terms["injuries"])
        if conflicts:
            score -= 14
            reasons.append(f"injury_conflict:{','.join(sorted(conflicts)[:3])}")

    if experience_sensitive:
        adjustment = _difficulty_score(doc, profile_terms["experience"][0])
        score += adjustment
        if adjustment:
            reasons.append(f"difficulty_adjustment:{adjustment}")

    if doc.get("expert_validation_status") == "pending":
        score -= 1

    return score, reasons


def _compact_exercise(doc: Dict[str, Any], score: int, reasons: List[str]) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "name": doc.get("name"),
        "aliases": doc.get("aliases") or [],
        "definition": doc.get("definition"),
        "category": doc.get("category") or doc.get("exercise_type"),
        "exercise_family": doc.get("exercise_family"),
        "movement_patterns": doc.get("movement_patterns") or [],
        "primary_muscles": doc.get("primary_muscles") or [],
        "secondary_muscles": doc.get("secondary_muscles") or [],
        "equipment_required": doc.get("equipment_required") or doc.get("equipment") or [],
        "difficulty": doc.get("difficulty"),
        "training_qualities": doc.get("training_qualities") or [],
        "sport_tags": doc.get("sport_tags") or [],
        "injury_flags": doc.get("injury_flags") or [],
        "contraindications": doc.get("contraindications") or [],
        "regressions": doc.get("regressions") or [],
        "progressions": doc.get("progressions") or [],
        "substitutions": doc.get("substitutions") or [],
        "coaching_cues": doc.get("coaching_cues") or [],
        "source_refs": _safe_source_refs(doc),
        "rank_score": score,
        "rank_reasons": reasons,
    }


def _compact_catalog_exercise(doc: Dict[str, Any], score: int, reasons: List[str]) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "source_exercise_id": doc.get("source_exercise_id"),
        "name": doc.get("name"),
        "aliases": doc.get("aliases") or [],
        "base_exercise": doc.get("base_exercise"),
        "tier": doc.get("tier"),
        "variation_type": doc.get("variation_type"),
        "category": doc.get("category"),
        "difficulty": doc.get("difficulty"),
        "default_user_level": doc.get("default_user_level"),
        "technical_complexity": doc.get("technical_complexity"),
        "mobility_requirement": doc.get("mobility_requirement"),
        "stability_requirement": doc.get("stability_requirement"),
        "impact_level": doc.get("impact_level"),
        "load_scalability": doc.get("load_scalability"),
        "coaching_requirement": doc.get("coaching_requirement"),
        "beginner_usable_as_drill": doc.get("beginner_usable_as_drill"),
        "equipment": doc.get("equipment") or [],
        "patterns": doc.get("patterns") or [],
        "qualities": doc.get("qualities") or [],
        "primary_muscles": doc.get("primary_muscles") or [],
        "secondary_muscles": doc.get("secondary_muscles") or [],
        "summary": doc.get("summary"),
        "coaching_cues": doc.get("coaching_cues") or [],
        "common_errors": doc.get("common_errors") or [],
        "use_when": doc.get("use_when") or [],
        "avoid_when": doc.get("avoid_when") or [],
        "progressions": doc.get("progressions") or [],
        "regressions": doc.get("regressions") or [],
        "source_refs": _safe_source_refs(doc),
        "rank_score": score,
        "rank_reasons": reasons,
    }


def _compact_knowledge_doc(doc: Dict[str, Any], score: int, reasons: List[str]) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "sport": doc.get("sport"),
        "domain": doc.get("domain"),
        "title": doc.get("title") or doc.get("name") or doc.get("error_name"),
        "knowledge_type": doc.get("knowledge_type"),
        "category": doc.get("category") or doc.get("rule_type") or doc.get("lift") or doc.get("phase"),
        "summary": doc.get("summary") or doc.get("technical_summary") or doc.get("rule_text") or doc.get("rule") or doc.get("app_usage") or doc.get("usage"),
        "recommended_action": doc.get("recommended_action") or [],
        "blocked_action": doc.get("blocked_action") or [],
        "applies_to": doc.get("applies_to") or [],
        "topics": doc.get("topics") or doc.get("applies_to") or doc.get("addresses") or [],
        "usage_context": doc.get("usage_context") or doc.get("app_usage"),
        "coaching_cues": doc.get("coaching_cues") or [],
        "corrections": doc.get("corrections") or [],
        "progression_steps": doc.get("progression_steps") or [],
        "contraindications": doc.get("contraindications") or [],
        "source_refs": _safe_source_refs(doc),
        "rank_score": score,
        "rank_reasons": reasons,
    }


def _first_strings(value: Any, limit: int = 2, max_chars: int = 140) -> List[str]:
    if not value:
        return []
    items = value if isinstance(value, list) else [value]
    result: List[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        result.append(text[:max_chars])
        if len(result) >= limit:
            break
    return result


def _short_text(value: Any, max_chars: int = 220) -> Optional[str]:
    text = str(value or "").strip()
    return text[:max_chars] if text else None


def _ai_exercise_record(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "name": doc.get("name"),
        "category": doc.get("category"),
        "level": doc.get("default_user_level") or doc.get("difficulty"),
        "equipment": _first_strings(doc.get("equipment") or doc.get("equipment_required"), 3, 32),
        "patterns": _first_strings(doc.get("patterns") or doc.get("movement_patterns"), 3, 32),
        "qualities": _first_strings(doc.get("qualities") or doc.get("training_qualities"), 3, 32),
        "summary": _short_text(doc.get("summary") or doc.get("definition"), 120),
        "use_when": _first_strings(doc.get("use_when"), 1, 90),
        "avoid_when": _first_strings(doc.get("avoid_when") or doc.get("contraindications"), 2, 60),
        "cues": _first_strings(doc.get("coaching_cues"), 1, 90),
    }


def _ai_rule_record(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "sport": doc.get("sport"),
        "domain": doc.get("domain"),
        "title": doc.get("title") or doc.get("id"),
        "category": doc.get("category"),
        "summary": _short_text(doc.get("summary") or doc.get("rule") or doc.get("rule_text") or doc.get("condition"), 140),
        "use": _short_text(doc.get("usage_context") or doc.get("applies_to") or doc.get("retrieval_tags"), 120),
        "applies_to": _first_strings(doc.get("applies_to"), 12, 40),
        "do": _first_strings(doc.get("recommended_action"), 2, 80),
        "avoid": _first_strings(doc.get("blocked_action") or doc.get("contraindications"), 2, 60),
        "cues": _first_strings(doc.get("coaching_cues"), 1, 80),
    }


def _compact_sport_teaching_doc(doc: Dict[str, Any], score: int, reasons: List[str]) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "sport": doc.get("sport"),
        "domain": doc.get("domain"),
        "level": doc.get("level"),
        "role_tags": doc.get("role_tags") or [],
        "learning_goal": doc.get("learning_goal"),
        "teaching_priorities": _first_strings(doc.get("teaching_priorities"), 4, 70),
        "technical_focus": _first_strings(doc.get("technical_focus"), 3, 70),
        "tactical_focus": _first_strings(doc.get("tactical_focus"), 3, 70),
        "physical_support": _first_strings(doc.get("physical_support"), 3, 65),
        "practice_design": _first_strings(doc.get("practice_design"), 2, 70),
        "typical_drills": _first_strings(doc.get("typical_drills"), 3, 65),
        "avoid_until_ready": _first_strings(doc.get("avoid_until_ready"), 3, 70),
        "progression_signals": _first_strings(doc.get("progression_signals"), 3, 80),
        "rank_score": score,
        "rank_reasons": reasons,
    }


def _compact_sport_assessment_doc(doc: Dict[str, Any], profile: Dict[str, Any], score: int, reasons: List[str]) -> Dict[str, Any]:
    level = _profile_terms(profile)["experience"][0]
    level_rank = LEVEL_ORDER.get(level, 2)
    selected_bands = []
    for band in doc.get("level_bands") or []:
        band_level = _norm(band.get("level"))
        band_rank = LEVEL_ORDER.get(band_level, 2)
        if band_level == level or band_rank == level_rank + 1:
            selected_bands.append({
                "level": band.get("level"),
                "indicators": _first_strings(band.get("indicators"), 2, 75),
                "ready_for_next_when": _first_strings(band.get("ready_for_next_when"), 2, 75),
            })
    return {
        "id": doc.get("id"),
        "sport": doc.get("sport"),
        "domain": doc.get("domain"),
        "summary": _short_text(doc.get("summary"), 120),
        "current_and_next_level_bands": selected_bands,
        "hold_if": _first_strings(doc.get("hold_if"), 3, 75),
        "rank_score": score,
        "rank_reasons": reasons,
    }


def _compact_sport_transition_rule_doc(doc: Dict[str, Any], score: int, reasons: List[str]) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "sport": doc.get("sport"),
        "from_level": doc.get("from_level"),
        "to_level": doc.get("to_level"),
        "applies_to": doc.get("applies_to") or [],
        "minimum_evidence": _first_strings(doc.get("minimum_evidence"), 3, 75),
        "promote_when": _first_strings(doc.get("promote_when"), 3, 75),
        "hold_when": _first_strings(doc.get("hold_when"), 3, 75),
        "rank_score": score,
        "rank_reasons": reasons,
    }


def compact_context_for_ai(context: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce retrieval output to only the tokens the model needs for generation."""
    primary = [_ai_exercise_record(doc) for doc in (context.get("allowed_primary_exercises") or [])[:COMPACT_AI_LIMITS["primary_exercises"]]]
    variations = [_ai_exercise_record(doc) for doc in (context.get("allowed_variations") or [])[:COMPACT_AI_LIMITS["variations"]]]
    programming = [_ai_rule_record(doc) for doc in (context.get("programming_rules") or [])[:COMPACT_AI_LIMITS["programming_rules"]]]
    support = context.get("supporting_context") or {}
    mobility = [_ai_rule_record(doc) for doc in (support.get("mobility_drills") or [])[:COMPACT_AI_LIMITS["mobility_drills"]]]
    recovery = [_ai_rule_record(doc) for doc in (support.get("recovery_rules") or [])[:COMPACT_AI_LIMITS["recovery_rules"]]]
    nutrition = [_ai_rule_record(doc) for doc in (support.get("nutrition_principles") or [])[:COMPACT_AI_LIMITS["nutrition_principles"]]]
    sport_teaching = context.get("sport_teaching_context") or {}
    progressions = [
        {
            "from": doc.get("from_exercise_name"),
            "to": doc.get("to_exercise_name"),
            "direction": doc.get("direction"),
            "min_level": doc.get("min_user_level"),
        }
        for doc in (context.get("progression_paths") or [])[:COMPACT_AI_LIMITS["progression_paths"]]
    ]
    history = [
        {
            "date": doc.get("date"),
            "exercise": doc.get("exercise_name"),
            "sets": doc.get("sets"),
            "reps": doc.get("reps"),
            "rpe": doc.get("rpe"),
            "pain": doc.get("pain_score"),
        }
        for doc in (context.get("recent_training_history") or [])[:COMPACT_AI_LIMITS["exercise_history"]]
    ]
    return {
        "policy": {
            "use_primary_by_default": True,
            "use_variations_only_if_qualified": True,
            "do_not_use_full_source_text": True,
        },
        "allowed_primary_exercises": primary,
        "allowed_variations": variations,
        "progression_paths": progressions,
        "programming_rules": programming,
        "mobility_recovery_nutrition": {
            "mobility": mobility,
            "recovery": recovery,
            "nutrition": nutrition,
        },
        "sport_teaching_context": {
            "teaching_progressions": (sport_teaching.get("teaching_progressions") or [])[:COMPACT_AI_LIMITS["sport_teaching_progressions"]],
            "skill_assessments": (sport_teaching.get("skill_assessments") or [])[:COMPACT_AI_LIMITS["sport_skill_assessments"]],
            "level_transition_rules": (sport_teaching.get("level_transition_rules") or [])[:COMPACT_AI_LIMITS["sport_level_transition_rules"]],
        },
        "recent_training_history": history,
        "training_protocols": (context.get("training_protocols") or [])[:COMPACT_AI_LIMITS["training_protocols"]],
        "known_exercise_names": (context.get("known_exercise_names") or [])[:50],
        "counts": context.get("counts") or {},
    }


def _sort_ranked(items: List[Tuple[int, List[str], Dict[str, Any]]], limit: int) -> List[Tuple[int, List[str], Dict[str, Any]]]:
    return sorted(items, key=lambda row: (row[0], str(row[2].get("title") or row[2].get("name") or "")), reverse=True)[:limit]


async def retrieve_exercise_candidates(
    db: Any,
    profile: Dict[str, Any],
    *,
    limit: int = DEFAULT_LIMITS["exercises"],
) -> List[Dict[str, Any]]:
    """Return compact exercise candidates ranked for a user profile."""
    terms = _profile_terms(profile)
    query_terms = sorted(set(terms["sports"] + terms["goals"] + terms["equipment"] + terms["injuries"]))
    query: Dict[str, Any] = {}
    if query_terms:
        query = {
            "$or": [
                {"sport_tags": {"$in": query_terms}},
                {"training_qualities": {"$in": query_terms}},
                {"movement_patterns": {"$in": query_terms}},
                {"equipment": {"$in": query_terms}},
                {"equipment_required": {"$in": query_terms}},
                {"exercise_family": {"$in": query_terms}},
                {"category": {"$in": query_terms}},
            ]
        }

    docs = await db.exercise_library.find(query).to_list(max(limit * 8, 120))
    if len(docs) < min(20, limit):
        docs = await db.exercise_library.find({}).to_list(max(limit * 8, 160))

    ranked: List[Tuple[int, List[str], Dict[str, Any]]] = []
    for doc in docs:
        score, reasons = _score_doc(
            doc,
            terms,
            positive_fields=(
                "name",
                "definition",
                "category",
                "exercise_type",
                "exercise_family",
                "movement_patterns",
                "primary_muscles",
                "secondary_muscles",
                "training_qualities",
                "sport_tags",
                "source_fields_available",
            ),
            injury_fields=("contraindications", "injury_flags"),
            equipment_fields=("equipment", "equipment_required"),
            experience_sensitive=True,
        )
        if "equipment_mismatch" in reasons and score < 0:
            continue
        if any(reason.startswith("injury_conflict") for reason in reasons) and score < 4:
            continue
        if score > -8:
            ranked.append((score, reasons, doc))

    return [_compact_exercise(doc, score, reasons) for score, reasons, doc in _sort_ranked(ranked, limit)]


async def retrieve_primary_exercise_candidates(
    db: Any,
    profile: Dict[str, Any],
    *,
    limit: int = DEFAULT_LIMITS["primary_exercises"],
) -> List[Dict[str, Any]]:
    """Return compact app-facing primary exercises ranked for a user profile."""
    terms = _profile_terms(profile)
    query_terms = sorted(set(terms["sports"] + terms["goals"] + terms["equipment"] + terms["injuries"]))
    query: Dict[str, Any] = {}
    if query_terms:
        query = {
            "$or": [
                {"qualities": {"$in": query_terms}},
                {"patterns": {"$in": query_terms}},
                {"equipment": {"$in": query_terms}},
                {"base_exercise": {"$in": query_terms}},
                {"category": {"$in": query_terms}},
                {"primary_muscles": {"$in": query_terms}},
                {"sport_tags": {"$in": query_terms}},
                {"source_book_id": {"$in": query_terms}},
                {"source_book_ids": {"$in": query_terms}},
            ]
        }

    docs = await db.primary_exercise_library.find(query).to_list(max(limit * 6, 120))
    if len(docs) < min(12, limit):
        docs = await db.primary_exercise_library.find({}).to_list(max(limit * 6, 120))

    profile_domain = set(terms["sports"] + terms["goals"] + terms["injuries"])
    if profile_domain.intersection(MOBILITY_CONTEXT_TAGS):
        mobility_docs = await db.primary_exercise_library.find({
            "$or": [
                {"source_book_id": "mobility_flexibility_web_research_v1"},
                {"source_book_ids": "mobility_flexibility_web_research_v1"},
            ]
        }).to_list(80)
        seen_doc_ids = {str(doc.get("_id")) for doc in docs}
        for mobility_doc in mobility_docs:
            doc_id = str(mobility_doc.get("_id"))
            if doc_id not in seen_doc_ids:
                docs.append(mobility_doc)
                seen_doc_ids.add(doc_id)

    equipment_domain = set(terms["equipment"])
    if profile_domain.intersection(GENERAL_GYM_CONTEXT_TAGS) or equipment_domain.intersection({"barbell", "dumbbell", "dumbbells", "kettlebell", "cable", "machine", "bench", "rack", "squat_rack", "gym", "full_gym", "home", "bodyweight"}):
        general_gym_docs = await db.primary_exercise_library.find({
            "$or": [
                {"source_book_id": "general_gym_exercise_research_v1"},
                {"source_book_ids": "general_gym_exercise_research_v1"},
            ]
        }).to_list(260)
        seen_doc_ids = {str(doc.get("_id")) for doc in docs}
        for gym_doc in general_gym_docs:
            doc_id = str(gym_doc.get("_id"))
            if doc_id not in seen_doc_ids:
                docs.append(gym_doc)
                seen_doc_ids.add(doc_id)

    ranked: List[Tuple[int, List[str], Dict[str, Any]]] = []
    for doc in docs:
        score, reasons = _score_doc(
            doc,
            terms,
            positive_fields=(
                "name",
                "summary",
                "category",
                "base_exercise",
                "patterns",
                "qualities",
                "primary_muscles",
                "secondary_muscles",
                "use_when",
                "sport_tags",
                "source_book_id",
                "source_book_ids",
            ),
            injury_fields=("avoid_when",),
            equipment_fields=("equipment",),
            experience_sensitive=True,
        )
        if "equipment_mismatch" in reasons and score < 0:
            continue
        if any(reason.startswith("injury_conflict") for reason in reasons) and score < 5:
            continue
        doc_context = set(_tokens(_text_list(
            doc,
            (
                "name",
                "summary",
                "category",
                "base_exercise",
                "patterns",
                "qualities",
                "primary_muscles",
                "sport_tags",
                "use_when",
                "avoid_when",
                "source_book_id",
                "source_book_ids",
            ),
        )))
        if profile_domain.intersection(MOBILITY_CONTEXT_TAGS) and doc_context.intersection(MOBILITY_CONTEXT_TAGS):
            score += 22 if "mobility_flexibility_web_research_v1" in doc_context else 8
            reasons.append("mobility_primary_match")
        if "general_gym_exercise_research_v1" in doc_context:
            equipment_domain = set(terms["equipment"])
            if profile_domain.intersection(GENERAL_GYM_CONTEXT_TAGS) or equipment_domain.intersection({"barbell", "dumbbell", "dumbbells", "kettlebell", "cable", "machine", "bench", "rack", "squat_rack", "gym", "full_gym"}):
                score += 22
                reasons.append("general_gym_primary_match")
            if profile_domain.intersection({"mobility", "flexibility"}) and not profile_domain.intersection(GENERAL_GYM_CONTEXT_TAGS):
                score -= 10
                reasons.append("pure_mobility_profile_penalty")
        injury_matches = doc_context.intersection(terms["injuries"])
        if "mobility_flexibility_web_research_v1" in doc_context and injury_matches:
            score += 10
            reasons.append(f"mobility_primary_injury_match:{','.join(sorted(injury_matches)[:3])}")
        if "general_gym_exercise_research_v1" in doc_context and injury_matches:
            score += 8
            reasons.append(f"general_gym_injury_match:{','.join(sorted(injury_matches)[:3])}")
        if terms["injuries"] and doc_context.intersection({"plyometrics", "jump_training", "reactive_strength", "depth_jump", "bounding", "high_impact"}):
            score -= 18
            reasons.append("injury_high_impact_penalty")
        ranked.append((score, reasons, doc))

    return [_compact_catalog_exercise(doc, score, reasons) for score, reasons, doc in _sort_ranked(ranked, limit)]


def _variation_allowed_by_level(profile: Dict[str, Any]) -> bool:
    terms = _profile_terms(profile)
    experience = terms["experience"][0]
    if LEVEL_ORDER.get(experience, 2) >= LEVEL_ORDER["advanced"]:
        return True
    all_terms = set(terms["all"])
    return bool(all_terms.intersection({"olympic", "weightlifting", "snatch", "clean", "jerk"}))


async def retrieve_variation_candidates(
    db: Any,
    profile: Dict[str, Any],
    *,
    limit: int = DEFAULT_LIMITS["variations"],
) -> List[Dict[str, Any]]:
    """Return qualified specialist variations only when level/context gates allow them."""
    if limit <= 0 or not _variation_allowed_by_level(profile):
        return []

    terms = _profile_terms(profile)
    query_terms = sorted(set(terms["sports"] + terms["goals"] + terms["equipment"] + terms["injuries"]))
    query: Dict[str, Any] = {}
    if query_terms:
        query = {
            "$or": [
                {"qualities": {"$in": query_terms}},
                {"patterns": {"$in": query_terms}},
                {"equipment": {"$in": query_terms}},
                {"base_exercise": {"$in": query_terms}},
                {"category": {"$in": query_terms}},
                {"variation_type": {"$in": query_terms}},
                {"sport_tags": {"$in": query_terms}},
                {"source_book_id": {"$in": query_terms}},
                {"source_book_ids": {"$in": query_terms}},
            ]
        }

    docs = await db.exercise_variation_library.find(query).to_list(max(limit * 20, 300))
    if len(docs) < min(4, limit):
        docs = await db.exercise_variation_library.find({}).to_list(max(limit * 20, 300))

    ranked: List[Tuple[int, List[str], Dict[str, Any]]] = []
    for doc in docs:
        score, reasons = _score_doc(
            doc,
            terms,
            positive_fields=(
                "name",
                "summary",
                "category",
                "base_exercise",
                "variation_type",
                "patterns",
                "qualities",
                "use_when",
                "sport_tags",
                "source_book_id",
                "source_book_ids",
            ),
            injury_fields=("avoid_when",),
            equipment_fields=("equipment",),
            experience_sensitive=True,
        )
        if "equipment_mismatch" in reasons:
            continue
        if any(reason.startswith("injury_conflict") for reason in reasons):
            continue
        if score > -4:
            ranked.append((score, reasons, doc))

    return [_compact_catalog_exercise(doc, score, reasons) for score, reasons, doc in _sort_ranked(ranked, limit)]


async def retrieve_progression_paths(
    db: Any,
    selected_exercises: Sequence[Dict[str, Any]],
    *,
    limit: int = DEFAULT_LIMITS["progression_paths"],
) -> List[Dict[str, Any]]:
    ids = [exercise.get("id") for exercise in selected_exercises if exercise.get("id")]
    if not ids or limit <= 0:
        return []
    docs = await db.exercise_progression_graph.find({
        "$or": [
            {"from_exercise_id": {"$in": ids}},
            {"to_exercise_id": {"$in": ids}},
        ]
    }).limit(limit).to_list(limit)
    return [
        {
            "id": doc.get("id"),
            "base_exercise": doc.get("base_exercise"),
            "from_exercise_id": doc.get("from_exercise_id"),
            "from_exercise_name": doc.get("from_exercise_name"),
            "to_exercise_id": doc.get("to_exercise_id"),
            "to_exercise_name": doc.get("to_exercise_name"),
            "direction": doc.get("direction"),
            "min_user_level": doc.get("min_user_level"),
        }
        for doc in docs
    ]


def _compact_protocol(doc: Dict[str, Any], reasons: List[str]) -> Dict[str, Any]:
    """Compact a decision-layer protocol for the generation prompt."""
    stages = [
        {
            "stage": s.get("stage"),
            "when": s.get("when"),
            "prescription": _short_text(s.get("prescription"), 260),
            "purpose": s.get("purpose"),
        }
        for s in (doc.get("stages") or [])
    ][:4]
    return {
        "name": doc.get("name"),
        "category": doc.get("category"),
        "applies_because": reasons,
        "summary": _short_text(doc.get("summary"), 220),
        "stages": stages,
        "key_rules": _first_strings(doc.get("key_rules"), 4, 180),
        "monitoring": _first_strings(doc.get("monitoring"), 3, 120),
        "avoid": _first_strings(doc.get("avoid"), 3, 120),
        "recommended_exercises": [str(x) for x in (doc.get("recommended_exercises") or [])][:6],
        "evidence_level": doc.get("evidence_level"),
        "source_refs": _safe_source_refs(doc, max_refs=2),
    }


async def retrieve_training_protocols(
    db: Any,
    profile: Dict[str, Any],
    *,
    limit: int = DEFAULT_LIMITS["training_protocols"],
) -> List[Dict[str, Any]]:
    """Decision-layer retrieval: surface the few expert protocols (rehab/loading/testing/progression)
    relevant to this athlete. Condition-specific protocols rank above broadly-relevant general ones."""
    docs = await db.training_protocols.find({}).to_list(500)
    if not docs:
        return []
    terms = _profile_terms(profile)
    injury_tokens = set(terms["injuries"])
    goal_tokens = set(terms["goals"])
    sport_tokens = set(terms["sports"])
    phase = _norm(profile.get("season_phase"))

    ranked: List[Tuple[int, List[str], Dict[str, Any]]] = []
    for doc in docs:
        match = doc.get("match") or {}
        score = 0
        reasons: List[str] = []
        if set(_tokens(match.get("injury_areas") or [])) & injury_tokens:
            score += 6
            reasons.append("injury")
        if set(_tokens(match.get("goals") or [])) & goal_tokens:
            score += 3
            reasons.append("goal")
        if set(_tokens(match.get("sports") or [])) & sport_tokens:
            score += 3
            reasons.append("sport")
        if phase and phase in {_norm(p) for p in (match.get("phases") or [])}:
            score += 2
            reasons.append("phase")
        if doc.get("scope") == "general":
            score += 1
            reasons.append("general")
        if score <= 0:
            continue
        evidence = {"high": 2, "moderate": 1}.get(str(doc.get("evidence_level") or "").lower(), 0)
        ranked.append((score * 10 + evidence, reasons, doc))

    ranked.sort(key=lambda item: (item[0], item[2].get("id", "")), reverse=True)
    return [_compact_protocol(doc, reasons) for _, reasons, doc in ranked[:limit]]


async def retrieve_recent_exercise_history(
    db: Any,
    profile: Dict[str, Any],
    *,
    limit: int = DEFAULT_LIMITS["exercise_history"],
) -> List[Dict[str, Any]]:
    user_id = profile.get("user_id")
    if not user_id:
        return []
    docs = await db.user_exercise_history.find({"user_id": user_id}).sort("date", -1).limit(limit).to_list(limit)
    return [
        {
            "date": doc.get("date"),
            "exercise_id": doc.get("exercise_id"),
            "exercise_name": doc.get("exercise_name"),
            "workout_id": doc.get("workout_id"),
            "completed": doc.get("completed"),
            "sets": doc.get("sets"),
            "reps": doc.get("reps"),
            "load": doc.get("load"),
            "rpe": doc.get("rpe"),
            "pain_score": doc.get("pain_score"),
            "source": doc.get("source"),
        }
        for doc in docs
    ]


async def _retrieve_collection_context(
    db: Any,
    collection_name: str,
    profile: Dict[str, Any],
    *,
    limit: int,
    query_fields: Sequence[str],
    positive_fields: Sequence[str],
) -> List[Dict[str, Any]]:
    terms = _profile_terms(profile)
    query_terms = sorted(set(terms["sports"] + terms["goals"] + terms["injuries"] + terms["equipment"] + terms["experience"]))
    query: Dict[str, Any] = {}
    if query_terms:
        query = {"$or": [{field: {"$in": query_terms}} for field in query_fields]}

    # Exclude non-movement/principle entries (flagged is_movement=False) from drill selection.
    exclude = {"is_movement": {"$ne": False}} if collection_name == "mobility_drills" else {}

    fetch_limit = max(limit * 20, 220) if collection_name == "programming_rules" else max(limit * 5, 50)
    docs = await db[collection_name].find({**exclude, **query}).to_list(fetch_limit)
    if len(docs) < min(5, limit):
        docs = await db[collection_name].find(exclude).to_list(fetch_limit)

    ranked: List[Tuple[int, List[str], Dict[str, Any]]] = []
    for doc in docs:
        score, reasons = _score_doc(
            doc,
            terms,
            positive_fields=positive_fields,
            injury_fields=("contraindications", "injury_flags"),
        )
        if collection_name == "programming_rules":
            profile_equipment = set(terms["equipment"])
            doc_context = set(_tokens(_text_list(doc, ("applies_to", "topics", "source_book_id"))))
            if profile_equipment.intersection({"bodyweight", "home", "no_equipment", "none"}) and doc_context.intersection({"bodyweight", "calisthenics"}):
                score += 10
                reasons.append("bodyweight_rule_match")
            profile_domain = set(terms["sports"] + terms["goals"])
            if profile_domain.intersection({"advanced_calisthenics", "gymnastics_strength", "skill_progression"}) and doc_context.intersection({"advanced_calisthenics", "gymnastics_strength", "skill_progression", "rings", "planche", "front_lever"}):
                score += 12
                reasons.append("advanced_calisthenics_rule_match")
            if profile_domain.intersection({"plyometrics", "jump_training", "reactive_strength", "landing_mechanics", "medicine_ball_throw", "bounding", "speed", "power"}) and doc_context.intersection({"plyometrics", "jump_training", "reactive_strength", "landing_mechanics", "depth_jump", "bounding", "medicine_ball_throw", "plyometrics_complete_extraction_v1"}):
                score += 24 if "plyometrics_complete_extraction_v1" in doc_context else 12
                reasons.append("plyometrics_rule_match")
            if profile_domain.intersection(MOBILITY_CONTEXT_TAGS) and doc_context.intersection(MOBILITY_CONTEXT_TAGS):
                score += 32 if "mobility_flexibility_web_research_v1" in doc_context else 9
                reasons.append("mobility_rule_match")
            if "youth" in doc_context and "youth" not in profile_domain:
                score -= 35
                reasons.append("age_context_mismatch:youth")
            if "older_adults" in doc_context and not profile_domain.intersection({"older_adults", "fall_risk", "osteoporosis"}):
                score -= 28
                reasons.append("age_context_mismatch:older_adults")
        if collection_name in {"planning_rules", "sport_training_rules"}:
            profile_sports = set(_profile_sports(profile))
            profile_domains = set(_sport_domains_for_profile(profile))
            profile_roles = set(_profile_role_tags(profile))
            doc_sport = _norm(doc.get("sport"))
            doc_domain = _norm(doc.get("domain"))
            doc_roles = set(_tokens(doc.get("applies_to") or doc.get("role_tags")))
            doc_context = set(_tokens(_text_list(doc, ("topics", "retrieval_tags", "category", "domain", "title", "summary", "rule", "rule_text"))))
            if doc_sport in profile_sports:
                score += 30
                reasons.append("sport_specific_rule")
            if doc_domain and doc_domain in profile_domains:
                score += 16
                reasons.append(f"sport_domain_rule:{doc_domain}")
            if doc_roles.intersection(profile_roles):
                score += 10
                reasons.append("sport_role_rule")
            if doc_context.intersection(terms["injuries"]):
                score += 12
                reasons.append("sport_injury_rule")
            if doc.get("source_pack_id") and "badminton" in str(doc.get("source_pack_id")) and "badminton" in profile_sports:
                score += 8
                reasons.append("badminton_pack_rule")
        if collection_name in {"mobility_drills", "recovery_rules"}:
            doc_context = set(_tokens(_text_list(
                doc,
                (
                    "name",
                    "title",
                    "summary",
                    "addresses",
                    "body_regions",
                    "topics",
                    "category",
                    "phase",
                    "source_book_id",
                    "source_book_ids",
                ),
            )))
            profile_domain = set(terms["sports"] + terms["goals"] + terms["injuries"])
            injury_matches = doc_context.intersection(terms["injuries"])
            if injury_matches:
                score += 10
                reasons.append(f"mobility_injury_match:{','.join(sorted(injury_matches)[:3])}")
            if profile_domain.intersection(MOBILITY_CONTEXT_TAGS) and doc_context.intersection(MOBILITY_CONTEXT_TAGS):
                score += 14 if "mobility_flexibility_web_research_v1" in doc_context else 7
                reasons.append("mobility_context_match")
            if "youth" in doc_context and "youth" not in profile_domain:
                score -= 35
                reasons.append("age_context_mismatch:youth")
            if "older_adults" in doc_context and not profile_domain.intersection({"older_adults", "fall_risk", "osteoporosis"}):
                score -= 28
                reasons.append("age_context_mismatch:older_adults")
        ranked.append((score, reasons, doc))

    return [_compact_knowledge_doc(doc, score, reasons) for score, reasons, doc in _sort_ranked(ranked, limit)]


async def retrieve_programming_context(
    db: Any,
    profile: Dict[str, Any],
    *,
    limit: int = DEFAULT_LIMITS["programming_rules"],
) -> List[Dict[str, Any]]:
    """Return compact programming rules relevant to profile goals, sport, level, and constraints."""
    profile_sports = set(_profile_sports(profile))
    general_rules = await _retrieve_collection_context(
        db,
        "programming_rules",
        profile,
        limit=limit,
        query_fields=("topics", "applies_to", "rule_type"),
        positive_fields=("title", "summary", "rule_text", "topics", "applies_to", "rule_type", "app_usage"),
    )
    sport_planning_rules: List[Dict[str, Any]] = []
    sport_training_rules: List[Dict[str, Any]] = []
    if profile_sports:
        for collection_name, positive_fields, target in (
            (
                "planning_rules",
                ("title", "summary", "rule", "rule_text", "topics", "applies_to", "category", "recommended_action", "blocked_action"),
                sport_planning_rules,
            ),
            (
                "sport_training_rules",
                ("title", "summary", "rule", "condition", "domain", "retrieval_tags", "applies_to", "category", "recommended_action", "blocked_action"),
                sport_training_rules,
            ),
        ):
            if collection_name == "planning_rules":
                query = {
                    "$or": [
                        {"sport": {"$in": sorted(profile_sports)}},
                        {"applies_to": {"$in": sorted(profile_sports)}},
                    ]
                }
            else:
                query = {"sport": {"$in": sorted(profile_sports)}}
            docs = await db[collection_name].find(query).to_list(max(limit * 6, 80))
            ranked: List[Tuple[int, List[str], Dict[str, Any]]] = []
            terms = _profile_terms(profile)
            profile_domains = set(_sport_domains_for_profile(profile))
            profile_roles = set(_profile_role_tags(profile))
            for doc in docs:
                score, reasons = _score_doc(
                    doc,
                    terms,
                    positive_fields=positive_fields,
                    injury_fields=("contraindications", "injury_flags"),
                )
                doc_domain = _norm(doc.get("domain"))
                doc_roles = set(_tokens(doc.get("applies_to") or doc.get("role_tags")))
                score += 30
                reasons.append("sport_specific_rule")
                if doc_domain and doc_domain in profile_domains:
                    score += 16
                    reasons.append(f"sport_domain_rule:{doc_domain}")
                if doc_roles.intersection(profile_roles):
                    score += 10
                    reasons.append("sport_role_rule")
                if set(_tokens(_text_list(doc, ("rule", "summary", "condition", "retrieval_tags")))).intersection(terms["injuries"]):
                    score += 12
                    reasons.append("sport_injury_rule")
                ranked.append((score, reasons, doc))
            target.extend([_compact_knowledge_doc(doc, score, reasons) for score, reasons, doc in _sort_ranked(ranked, limit)])

    merged: Dict[str, Dict[str, Any]] = {}
    for doc in [*general_rules, *sport_planning_rules, *sport_training_rules]:
        doc_id = str(doc.get("id") or f"{doc.get('title')}:{doc.get('category')}")
        existing = merged.get(doc_id)
        if not existing or int(doc.get("rank_score") or 0) > int(existing.get("rank_score") or 0):
            merged[doc_id] = doc
    return sorted(
        merged.values(),
        key=lambda doc: (int(doc.get("rank_score") or 0), str(doc.get("title") or "")),
        reverse=True,
    )[:limit]


async def retrieve_technical_context(
    db: Any,
    profile: Dict[str, Any],
    *,
    model_limit: int = DEFAULT_LIMITS["technical_models"],
    error_limit: int = DEFAULT_LIMITS["technical_errors"],
) -> Dict[str, List[Dict[str, Any]]]:
    """Return technique models and common error context relevant to profile demands."""
    models = await _retrieve_collection_context(
        db,
        "technical_models",
        profile,
        limit=model_limit,
        query_fields=("topics", "lift", "phase"),
        positive_fields=("title", "summary", "technical_summary", "topics", "lift", "phase", "app_usage"),
    )
    errors = await _retrieve_collection_context(
        db,
        "technical_errors",
        profile,
        limit=error_limit,
        query_fields=("topics", "lift", "correction_signal_tags"),
        positive_fields=("error_name", "summary", "topics", "lift", "correction_signal_tags", "corrections"),
    )
    return {"technical_models": models, "technical_errors": errors}


async def retrieve_supporting_context(
    db: Any,
    profile: Dict[str, Any],
    *,
    mobility_limit: int = DEFAULT_LIMITS["mobility_drills"],
    recovery_limit: int = DEFAULT_LIMITS["recovery_rules"],
    nutrition_limit: int = DEFAULT_LIMITS["nutrition_principles"],
) -> Dict[str, List[Dict[str, Any]]]:
    """Return mobility, recovery, and nutrition knowledge relevant to profile constraints."""
    mobility = await _retrieve_collection_context(
        db,
        "mobility_drills",
        profile,
        limit=mobility_limit,
        query_fields=("addresses", "body_regions", "topics", "category"),
        positive_fields=("name", "summary", "addresses", "body_regions", "topics", "category"),
    )
    recovery = await _retrieve_collection_context(
        db,
        "recovery_rules",
        profile,
        limit=recovery_limit,
        query_fields=("topics", "category"),
        positive_fields=("title", "summary", "rule_text", "topics", "category"),
    )
    nutrition = await _retrieve_collection_context(
        db,
        "nutrition_principles",
        profile,
        limit=nutrition_limit,
        query_fields=("topics", "category"),
        positive_fields=("title", "summary", "rule_text", "topics", "category"),
    )
    return {
        "mobility_drills": mobility,
        "recovery_rules": recovery,
        "nutrition_principles": nutrition,
    }


def _sport_context_score(doc: Dict[str, Any], profile: Dict[str, Any]) -> Tuple[int, List[str]]:
    terms = _profile_terms(profile)
    sports = set(_profile_sports(profile))
    role_tags = set(_profile_role_tags(profile))
    domains = set(_sport_domains_for_profile(profile))
    level = terms["experience"][0]

    score = 0
    reasons: List[str] = []
    doc_sport = _norm(doc.get("sport"))
    doc_domain = _norm(doc.get("domain"))
    doc_level = _norm(doc.get("level") or doc.get("from_level"))
    doc_roles = set(_tokens(doc.get("role_tags") or doc.get("applies_to")))

    if doc_sport in sports:
        score += 12
        reasons.append("sport_match")
    if doc_domain in domains:
        score += 10
        reasons.append(f"domain_match:{doc_domain}")
    elif doc_domain in SPORT_BASE_DOMAINS.get(doc_sport, []):
        score += 4
        reasons.append(f"base_domain:{doc_domain}")
    if doc_roles.intersection(role_tags):
        score += 8
        reasons.append(f"role_match:{','.join(sorted(doc_roles.intersection(role_tags))[:3])}")
        specific_role_matches = doc_roles.intersection(role_tags) - {"all_roles"}
        if specific_role_matches:
            score += 6
            reasons.append(f"specific_role_match:{','.join(sorted(specific_role_matches)[:3])}")
    if "all_roles" in doc_roles:
        score += 3
        reasons.append("all_roles")
    elif doc_roles and not doc_roles.intersection(role_tags):
        score -= 24
        reasons.append("role_mismatch")

    if doc.get("level"):
        if doc_level == level:
            score += 10
            reasons.append("level_match")
        else:
            doc_rank = LEVEL_ORDER.get(doc_level, 2)
            user_rank = LEVEL_ORDER.get(level, 2)
            if doc_rank < user_rank:
                score += 2
                reasons.append("lower_level_reference")
            elif doc_rank == user_rank + 1:
                score -= 4
                reasons.append("next_level_reference")
            else:
                score -= 12
                reasons.append("level_mismatch")

    from_level = _norm(doc.get("from_level"))
    to_level = _norm(doc.get("to_level"))
    if from_level:
        if from_level in {level, "any"}:
            score += 8
            reasons.append("transition_level_match")
        elif to_level in {"hold_or_regress", "hold_or_conservative_progression"}:
            score += 4
            reasons.append("safety_override")
        else:
            score -= 4
            reasons.append("transition_level_mismatch")

    doc_terms = set(_tokens([
        doc.get("learning_goal"),
        doc.get("summary"),
        doc.get("teaching_priorities"),
        doc.get("technical_focus"),
        doc.get("tactical_focus"),
        doc.get("physical_support"),
        doc.get("hold_if"),
        doc.get("minimum_evidence"),
        doc.get("promote_when"),
        doc.get("hold_when"),
    ]))
    injury_matches = doc_terms.intersection(terms["injuries"])
    if injury_matches:
        score += 5
        reasons.append(f"injury_relevance:{','.join(sorted(injury_matches)[:3])}")

    return score, reasons


def _transition_rule_relevant(doc: Dict[str, Any], profile: Dict[str, Any]) -> bool:
    level = _profile_terms(profile)["experience"][0]
    role_tags = set(_profile_role_tags(profile))
    applies_to = set(_tokens(doc.get("applies_to")))
    from_level = _norm(doc.get("from_level"))
    to_level = _norm(doc.get("to_level"))
    age = _infer_profile_age(profile)
    is_youth_user = (age is not None and age < 18) or bool(role_tags.intersection({"youth", "youth_player", "youth_fast_bowler"}))

    youth_only_tags = {"youth", "youth_player", "youth_fast_bowler"}
    if applies_to and applies_to.issubset(youth_only_tags) and not is_youth_user:
        return False

    if from_level == level:
        if applies_to and "all_roles" not in applies_to and not applies_to.intersection(role_tags):
            return False
        return True

    if from_level == "any" and to_level in {"hold_or_regress", "hold_or_conservative_progression"}:
        return bool(applies_to.intersection(role_tags))

    return False


async def retrieve_sport_teaching_context(
    db: Any,
    profile: Dict[str, Any],
    *,
    progression_limit: int = DEFAULT_LIMITS["sport_teaching_progressions"],
    assessment_limit: int = DEFAULT_LIMITS["sport_skill_assessments"],
    transition_limit: int = DEFAULT_LIMITS["sport_level_transition_rules"],
) -> Dict[str, List[Dict[str, Any]]]:
    sports = _profile_sports(profile)
    if not sports:
        return {
            "teaching_progressions": [],
            "skill_assessments": [],
            "level_transition_rules": [],
        }

    domains = _sport_domains_for_profile(profile)
    roles = _profile_role_tags(profile)
    level = _profile_terms(profile)["experience"][0]

    progression_query: Dict[str, Any] = {"sport": {"$in": sports}}
    if domains:
        progression_query["domain"] = {"$in": domains}
    if level:
        progression_query["level"] = level
    progressions = await db.sport_teaching_progressions.find(progression_query).to_list(max(progression_limit * 4, 40))
    if len(progressions) < min(3, progression_limit):
        fallback_query: Dict[str, Any] = {"sport": {"$in": sports}}
        if domains:
            fallback_query["domain"] = {"$in": domains}
        progressions = await db.sport_teaching_progressions.find(fallback_query).to_list(max(progression_limit * 5, 60))

    assessments_query: Dict[str, Any] = {"sport": {"$in": sports}}
    if domains:
        assessments_query["domain"] = {"$in": domains}
    assessments = await db.sport_skill_assessments.find(assessments_query).to_list(max(assessment_limit * 4, 30))

    transition_query: Dict[str, Any] = {
        "sport": {"$in": sports},
        "$or": [
            {"from_level": level},
            {"from_level": "any"},
            {"to_level": {"$in": ["hold_or_regress", "hold_or_conservative_progression"]}},
            {"applies_to": {"$in": roles}},
        ],
    }
    transitions = await db.sport_level_transition_rules.find(transition_query).to_list(max(transition_limit * 4, 30))
    transitions = [doc for doc in transitions if _transition_rule_relevant(doc, profile)]

    ranked_progressions = [
        (*_sport_context_score(doc, profile), doc)
        for doc in progressions
    ]
    ranked_assessments = [
        (*_sport_context_score(doc, profile), doc)
        for doc in assessments
    ]
    ranked_transitions = [
        (*_sport_context_score(doc, profile), doc)
        for doc in transitions
    ]

    ranked_progressions = sorted(ranked_progressions, key=lambda row: (row[0], str(row[2].get("id") or "")), reverse=True)[:progression_limit]
    ranked_assessments = sorted(ranked_assessments, key=lambda row: (row[0], str(row[2].get("id") or "")), reverse=True)[:assessment_limit]
    ranked_transitions = sorted(ranked_transitions, key=lambda row: (row[0], str(row[2].get("id") or "")), reverse=True)[:transition_limit]

    return {
        "teaching_progressions": [
            _compact_sport_teaching_doc(doc, score, reasons)
            for score, reasons, doc in ranked_progressions
            if score > 0
        ],
        "skill_assessments": [
            _compact_sport_assessment_doc(doc, profile, score, reasons)
            for score, reasons, doc in ranked_assessments
            if score > 0
        ],
        "level_transition_rules": [
            _compact_sport_transition_rule_doc(doc, score, reasons)
            for score, reasons, doc in ranked_transitions
            if score > 0
        ],
    }


def _merge_dedup_interleave(primary: List[Dict[str, Any]], semantic: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Interleave keyword-matched and semantically-matched candidates, deduped by id, so that
    semantic recall-rescues (exercises keyword search missed) survive downstream compaction."""
    seen: set = set()
    out: List[Dict[str, Any]] = []
    i = j = 0
    while i < len(primary) or j < len(semantic):
        if i < len(primary):
            doc = primary[i]
            i += 1
            key = doc.get("id") or doc.get("name")
            if key and key not in seen:
                seen.add(key)
                out.append(doc)
        if j < len(semantic):
            doc = semantic[j]
            j += 1
            key = doc.get("id") or doc.get("name")
            if key and key not in seen:
                seen.add(key)
                out.append(doc)
    return out


_LOWER_LIMB_INJURY_TOKENS = {
    "knee", "patellar", "patella", "acl", "mcl", "ankle", "achilles", "calf", "shin",
    "hip", "groin", "adductor", "hamstring", "foot", "tendon", "tendinopathy",
}


def _semantic_hard_filter(doc: Dict[str, Any], injury_tokens: set, has_lower_limb_injury: bool) -> bool:
    """Stage-1 safety gate: exclude contraindicated / high-impact-while-injured exercises so semantic
    recall stays relevant AND safe. Deliberately conservative to protect recall."""
    avoid = set(_tokens(
        (doc.get("avoid_when") or []) + (doc.get("contraindications") or []) + (doc.get("injury_flags") or [])
    ))
    if avoid & injury_tokens:
        return False
    if has_lower_limb_injury and _norm(doc.get("impact_level")) in {"high", "very_high", "maximal"}:
        return False
    return True


async def retrieve_semantic_exercise_candidates(
    db: Any,
    profile: Dict[str, Any],
    *,
    limit: int = DEFAULT_LIMITS["semantic_exercises"],
    protocols: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Stage-2 semantic retrieval: embed the athlete's need and rank embedded exercises by cosine
    similarity. Rescues relevant exercises that keyword/tag matching misses. Returns [] (no-op) when
    embeddings are disabled/unavailable or no exercises have been embedded yet."""
    try:
        from backend.embeddings import embed_query, cosine, embeddings_enabled
    except Exception:
        return []
    if not embeddings_enabled():
        return []

    terms = _profile_terms(profile)
    protocol_exercises: List[str] = []
    for proto in protocols or []:
        protocol_exercises.extend(proto.get("recommended_exercises") or [])

    query_parts = [
        str(profile.get("primary_goal") or ""),
        " ".join(terms["goals"][:12]),
        " ".join(terms["sports"][:8]),
        ("injuries: " + " ".join(terms["injuries"][:8])) if terms["injuries"] else "",
        ("recommended: " + " ".join(protocol_exercises[:10])) if protocol_exercises else "",
        ("experience: " + terms["experience"][0]) if terms["experience"] else "",
    ]
    query = " | ".join(part for part in query_parts if part)
    query_vec = embed_query(query)
    if not query_vec:
        return []

    injury_tokens = set(terms["injuries"])
    has_lower_limb_injury = bool(injury_tokens & _LOWER_LIMB_INJURY_TOKENS)

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for col in ("primary_exercise_library", "exercise_variation_library"):
        docs = await db[col].find({"embedding": {"$exists": True}}).to_list(2000)
        for doc in docs:
            vec = doc.get("embedding")
            if not vec:
                continue
            if not _semantic_hard_filter(doc, injury_tokens, has_lower_limb_injury):
                continue  # Stage-1 safety filter before semantic ranking
            sim = cosine(query_vec, vec)
            scored.append((sim, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    out: List[Dict[str, Any]] = []
    for sim, doc in scored[:limit]:
        clean = {k: v for k, v in doc.items() if k not in ("embedding", "_id")}
        clean["_semantic_score"] = round(float(sim), 3)
        out.append(clean)
    return out


async def build_generation_knowledge_context(
    db: Any,
    profile: Dict[str, Any],
    *,
    limits: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Build compact Mongo-backed context for AI workout generation.

    The return value is intentionally prompt-sized: it contains ranked, normalized snippets and source
    references, not full book text.
    """
    resolved_limits = {**DEFAULT_LIMITS, **(limits or {})}
    profile_terms = _profile_terms(profile)

    primary_exercises = await retrieve_primary_exercise_candidates(
        db,
        profile,
        limit=resolved_limits["primary_exercises"],
    )
    variations = await retrieve_variation_candidates(
        db,
        profile,
        limit=resolved_limits["variations"],
    )
    selected_exercises = [*primary_exercises, *variations]
    progression_paths = await retrieve_progression_paths(
        db,
        selected_exercises,
        limit=resolved_limits["progression_paths"],
    )
    recent_history = await retrieve_recent_exercise_history(
        db,
        profile,
        limit=resolved_limits["exercise_history"],
    )
    programming_rules = await retrieve_programming_context(db, profile, limit=resolved_limits["programming_rules"])
    technical = await retrieve_technical_context(
        db,
        profile,
        model_limit=resolved_limits["technical_models"],
        error_limit=resolved_limits["technical_errors"],
    )
    support = await retrieve_supporting_context(
        db,
        profile,
        mobility_limit=resolved_limits["mobility_drills"],
        recovery_limit=resolved_limits["recovery_rules"],
        nutrition_limit=resolved_limits["nutrition_principles"],
    )
    sport_teaching = await retrieve_sport_teaching_context(
        db,
        profile,
        progression_limit=resolved_limits["sport_teaching_progressions"],
        assessment_limit=resolved_limits["sport_skill_assessments"],
        transition_limit=resolved_limits["sport_level_transition_rules"],
    )
    training_protocols = await retrieve_training_protocols(
        db,
        profile,
        limit=resolved_limits["training_protocols"],
    )

    # Stage 2: semantic recall-rescue — merge embedding-ranked candidates into the primary pool
    # so exercises keyword matching missed still reach the model (no-op if embeddings unavailable).
    semantic_candidates = await retrieve_semantic_exercise_candidates(
        db,
        profile,
        limit=resolved_limits["semantic_exercises"],
        protocols=training_protocols,
    )
    if semantic_candidates:
        primary_exercises = _merge_dedup_interleave(primary_exercises, semantic_candidates)
        selected_exercises = [*primary_exercises, *variations]

    all_records: List[Dict[str, Any]] = [
        *selected_exercises,
        *programming_rules,
        *technical["technical_models"],
        *technical["technical_errors"],
        *support["mobility_drills"],
        *support["recovery_rules"],
        *support["nutrition_principles"],
    ]

    return {
        "source_scope": "app_exercise_catalog_plus_olympic_source_context",
        "profile_match_terms": profile_terms,
        "retrieval_policy": {
            "compact": True,
            "no_full_source_text": True,
            "ranking": "primary catalog first; specialist variations only when level/equipment/injury gates pass",
            "limits": resolved_limits,
        },
        "allowed_primary_exercises": primary_exercises,
        "allowed_variations": variations,
        "blocked_exercises": [],
        "progression_paths": progression_paths,
        "recent_training_history": recent_history,
        "exercise_candidates": selected_exercises,
        "programming_rules": programming_rules,
        "technical_context": technical,
        "supporting_context": support,
        "sport_teaching_context": sport_teaching,
        "training_protocols": training_protocols,
        "source_refs": _merge_unique_refs(all_records, limit=resolved_limits["source_refs"]),
        "counts": {
            "allowed_primary_exercises": len(primary_exercises),
            "allowed_variations": len(variations),
            "progression_paths": len(progression_paths),
            "recent_training_history": len(recent_history),
            "exercise_candidates": len(selected_exercises),
            "programming_rules": len(programming_rules),
            "technical_models": len(technical["technical_models"]),
            "technical_errors": len(technical["technical_errors"]),
            "mobility_drills": len(support["mobility_drills"]),
            "recovery_rules": len(support["recovery_rules"]),
            "nutrition_principles": len(support["nutrition_principles"]),
            "sport_teaching_progressions": len(sport_teaching["teaching_progressions"]),
            "sport_skill_assessments": len(sport_teaching["skill_assessments"]),
            "sport_level_transition_rules": len(sport_teaching["level_transition_rules"]),
            "training_protocols": len(training_protocols),
            "semantic_exercises": len(semantic_candidates),
        },
        "known_exercise_names": sorted({
            str(exercise.get("name")).strip().lower()
            for exercise in selected_exercises
            if str(exercise.get("name") or "").strip()
        }),
        "exercise_ref_by_name": {
            str(exercise.get("name")).strip().lower(): {
                "id": exercise.get("id"),
                "name": exercise.get("name"),
                "tier": exercise.get("tier"),
                "source_exercise_id": exercise.get("source_exercise_id"),
                "source_refs": exercise.get("source_refs") or [],
                "summary": _short_text(exercise.get("summary") or exercise.get("definition"), 220),
                "coaching_cues": _first_strings(exercise.get("coaching_cues"), 3, 120),
                "common_errors": _first_strings(exercise.get("common_errors"), 3, 120),
                "substitutions": _first_strings(exercise.get("substitutions"), 3, 100),
                "regressions": _first_strings(exercise.get("regressions"), 3, 100),
                "progressions": _first_strings(exercise.get("progressions"), 3, 100),
                "use_when": _first_strings(exercise.get("use_when") or exercise.get("usage_context"), 3, 120),
                "avoid_when": _first_strings(
                    exercise.get("avoid_when") or exercise.get("contraindications") or exercise.get("injury_flags"),
                    3,
                    100,
                ),
            }
            for exercise in selected_exercises
            if exercise.get("id") and str(exercise.get("name") or "").strip()
        },
        "exercise_ref_by_id": {
            str(exercise.get("id")): {
                "id": exercise.get("id"),
                "name": exercise.get("name"),
                "tier": exercise.get("tier"),
                "source_exercise_id": exercise.get("source_exercise_id"),
                "source_refs": exercise.get("source_refs") or [],
                "summary": _short_text(exercise.get("summary") or exercise.get("definition"), 220),
                "coaching_cues": _first_strings(exercise.get("coaching_cues"), 3, 120),
                "common_errors": _first_strings(exercise.get("common_errors"), 3, 120),
                "substitutions": _first_strings(exercise.get("substitutions"), 3, 100),
                "regressions": _first_strings(exercise.get("regressions"), 3, 100),
                "progressions": _first_strings(exercise.get("progressions"), 3, 100),
                "use_when": _first_strings(exercise.get("use_when") or exercise.get("usage_context"), 3, 120),
                "avoid_when": _first_strings(
                    exercise.get("avoid_when") or exercise.get("contraindications") or exercise.get("injury_flags"),
                    3,
                    100,
                ),
            }
            for exercise in selected_exercises
            if exercise.get("id")
        },
    }


async def build_workout_knowledge_context(db: Any, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper used by workout generation."""
    return await build_generation_knowledge_context(db, profile)


async def find_exercise_references(
    db: Any,
    exercise_names: Sequence[str],
    *,
    limit: int = 1,
) -> Dict[str, List[Dict[str, Any]]]:
    """Resolve generated exercise names to library records for later workout/source linking."""
    results: Dict[str, List[Dict[str, Any]]] = {}
    for name in exercise_names:
        clean_name = str(name or "").strip()
        if not clean_name:
            continue
        docs: List[Dict[str, Any]] = []
        for collection_name in ["primary_exercise_library", "exercise_variation_library", "exercise_library"]:
            exact = await db[collection_name].find({"name": {"$regex": f"^{re.escape(clean_name)}$", "$options": "i"}}).to_list(limit)
            docs = exact
            if not docs:
                docs = await db[collection_name].find({
                    "$or": [
                        {"name": {"$regex": re.escape(clean_name), "$options": "i"}},
                        {"aliases": {"$regex": re.escape(clean_name), "$options": "i"}},
                    ]
                }).to_list(limit)
            if docs:
                break
        results[clean_name] = [
            {
                "id": doc.get("id"),
                "name": doc.get("name"),
                "exercise_family": doc.get("exercise_family") or doc.get("base_exercise"),
                "tier": doc.get("tier"),
                "movement_patterns": doc.get("movement_patterns") or doc.get("patterns") or [],
                "equipment_required": doc.get("equipment_required") or doc.get("equipment") or [],
                "source_refs": _safe_source_refs(doc),
            }
            for doc in docs
        ]
    return results
