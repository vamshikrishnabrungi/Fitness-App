from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'sftc_database')
REPORT_PATH = ROOT_DIR.parent / 'deep-research-report.md'

DEFAULT_ENVELOPE = {
    'evidence_level': 'coaching_consensus',
    'source_refs': [],
    'sftc_app_usage_profile_id': 'UP-DEFAULT',
    'personalization_profile_id': 'PP-ATHLETE-CORE-v1',
    'last_reviewed_date': '2026-05-13',
    'expert_validation_status': 'pending',
    'version': 'v1.0.0',
}


SOURCE_REFERENCES = [
    {
        'id': 'who-physical-activity-2020',
        'title': 'WHO Guidelines on Physical Activity and Sedentary Behaviour',
        'url': 'https://www.ncbi.nlm.nih.gov/books/NBK566046/',
        'notes': 'Used for general aerobic and muscle-strengthening baseline recommendations.',
    },
    {
        'id': 'cdc-adult-activity-basics',
        'title': 'CDC Physical Activity Basics for Adults',
        'url': 'https://www.cdc.gov/physical-activity-basics/adding-adults/what-counts.html',
        'notes': 'Used for public-health strength and aerobic activity framing.',
    },
    {
        'id': 'acsm-progression-models-2009',
        'title': 'ACSM Progression Models in Resistance Training for Healthy Adults',
        'url': 'https://www.unboundmedicine.com/medline/citation/19204579/',
        'notes': 'Used for progressive overload principles and resistance training progression.',
    },
    {
        'id': 'cricket-bowling-demands-2021',
        'title': 'Quantification of the demands of cricket bowling and relationship to injury risk',
        'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8431903/',
        'notes': 'Used for fast bowling workload, lumbar stress, and cricket role demands.',
    },
    {
        'id': 'cricketers-shoulder-2020',
        'title': "The cricketer's shoulder and injury",
        'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7136799/',
        'notes': 'Used for cricket shoulder risk and shoulder care emphasis.',
    },
    {
        'id': 'volleyball-injury-epidemiology-2023',
        'title': 'Epidemiology of Common Injuries in the Volleyball Athlete',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/37014607/',
        'notes': 'Used for volleyball injury patterns: ankle, patellar tendon, shoulder, fingers/thumb.',
    },
    {
        'id': 'fifa-11-plus-review-2017',
        'title': 'The FIFA 11+ injury prevention program for soccer players: systematic review',
        'url': 'https://bmcsportsscimedrehabil.biomedcentral.com/articles/10.1186/s13102-017-0083-z',
        'notes': 'Used for soccer injury-prevention components: core, eccentric thigh, proprioception, dynamic stabilization, plyometrics.',
    },
]


MOVEMENT_PATTERNS = [
    {'id': 'pattern_squat', 'pattern': 'squat', 'core_tags': ['bilateral', 'knee_dominant', 'vertical_force'], 'sport_transfer': ['jumping', 'deceleration', 'positional_strength']},
    {'id': 'pattern_hinge', 'pattern': 'hinge', 'core_tags': ['hip_dominant', 'posterior_chain'], 'sport_transfer': ['sprinting', 'striking', 'lifting', 'posterior_chain_robustness']},
    {'id': 'pattern_lunge', 'pattern': 'lunge', 'core_tags': ['split_stance', 'unilateral'], 'sport_transfer': ['change_of_direction', 'racket_sports', 'field_sports']},
    {'id': 'pattern_push', 'pattern': 'push', 'core_tags': ['horizontal', 'vertical'], 'sport_transfer': ['combat_sports', 'court_sports', 'general_fitness']},
    {'id': 'pattern_pull', 'pattern': 'pull', 'core_tags': ['horizontal', 'vertical'], 'sport_transfer': ['climbing', 'grappling', 'posture', 'shoulder_balance']},
    {'id': 'pattern_carry', 'pattern': 'carry', 'core_tags': ['bilateral', 'unilateral', 'gait_loaded'], 'sport_transfer': ['trunk_stiffness', 'grip', 'contact_robustness']},
    {'id': 'pattern_rotation', 'pattern': 'rotation', 'core_tags': ['transverse_force'], 'sport_transfer': ['boxing', 'cricket', 'tennis', 'golf']},
    {'id': 'pattern_anti_rotation', 'pattern': 'anti_rotation', 'core_tags': ['trunk_control'], 'sport_transfer': ['change_of_direction', 'combat_stabilization']},
    {'id': 'pattern_sprint', 'pattern': 'sprint', 'core_tags': ['acceleration', 'max_velocity'], 'sport_transfer': ['team_sports', 'sprinting', 'field_coverage']},
    {'id': 'pattern_jump', 'pattern': 'jump', 'core_tags': ['bilateral', 'unilateral', 'vertical', 'horizontal'], 'sport_transfer': ['basketball', 'volleyball', 'badminton']},
    {'id': 'pattern_throw', 'pattern': 'throw', 'core_tags': ['overhead', 'chest', 'rotational'], 'sport_transfer': ['cricket', 'basketball', 'handball']},
    {'id': 'pattern_change_of_direction', 'pattern': 'change_of_direction', 'core_tags': ['cut', 'shuffle', 'crossover'], 'sport_transfer': ['field_sports', 'racket_sports']},
    {'id': 'pattern_deceleration', 'pattern': 'deceleration', 'core_tags': ['braking', 'force_absorption'], 'sport_transfer': ['soccer', 'basketball', 'tennis', 'badminton']},
    {'id': 'pattern_landing', 'pattern': 'landing', 'core_tags': ['bilateral', 'unilateral'], 'sport_transfer': ['jumping_sports', 'injury_reduction']},
    {'id': 'pattern_locomotion', 'pattern': 'locomotion', 'core_tags': ['run', 'jog', 'swim', 'cycle', 'skip'], 'sport_transfer': ['endurance', 'conditioning']},
]


PHYSICAL_QUALITIES = [
    {'id': 'quality_max_strength', 'quality': 'max_strength', 'group': 'force_production', 'programming_defaults': {'rep_range': '1-6', 'rest_seconds': '120-240'}},
    {'id': 'quality_hypertrophy', 'quality': 'hypertrophy', 'group': 'force_production', 'programming_defaults': {'rep_range': '6-15', 'rir_target': '1-4'}},
    {'id': 'quality_explosive_power', 'quality': 'explosive_power', 'group': 'force_production', 'programming_defaults': {'rep_range': '1-5', 'intent': 'maximal_velocity'}},
    {'id': 'quality_rotational_power', 'quality': 'rotational_power', 'group': 'force_production', 'programming_defaults': {'rep_range': '3-6 each side', 'rest_seconds': '60-120'}},
    {'id': 'quality_speed', 'quality': 'speed', 'group': 'speed_reactivity', 'programming_defaults': {'distance_band': '10-40m', 'rest': 'full_recovery'}},
    {'id': 'quality_acceleration', 'quality': 'acceleration', 'group': 'speed_reactivity', 'programming_defaults': {'distance_band': '5-30m', 'readiness_gate': True}},
    {'id': 'quality_change_of_direction', 'quality': 'change_of_direction', 'group': 'multi_directional_movement', 'programming_defaults': {'reps': 'low_quality_focused', 'fatigue_cap': 'moderate'}},
    {'id': 'quality_agility', 'quality': 'agility', 'group': 'multi_directional_movement', 'programming_defaults': {'include_reactive_component': True}},
    {'id': 'quality_aerobic_base', 'quality': 'aerobic_base', 'group': 'energy_systems', 'programming_defaults': {'zone_target': 'easy_conversational', 'weekly_frequency': '2-5'}},
    {'id': 'quality_anaerobic_capacity', 'quality': 'anaerobic_capacity', 'group': 'energy_systems', 'programming_defaults': {'work_rest_ratio': 'sport_dependent'}},
    {'id': 'quality_mobility', 'quality': 'mobility', 'group': 'range_control', 'programming_defaults': {'frequency': 'frequent_low_cost'}},
    {'id': 'quality_tissue_tolerance', 'quality': 'tissue_tolerance', 'group': 'context_modifiers', 'programming_defaults': {'progression': 'conservative'}},
]


READINESS_RULES = [
    {
        'id': 'rr_low_sleep_high_soreness_v1',
        'name': 'Low sleep plus high soreness readiness downgrade',
        'category': 'recovery_readiness_rule',
        'factors': ['sleep_duration', 'subjective_soreness'],
        'condition': {'sleep_duration_hours': '<6', 'subjective_soreness': '>=7/10'},
        'adjustment': {'training_intensity': 'reduce', 'training_volume': 'reduce', 'avoid_regions': 'sore_regions'},
        'source_refs': ['SR-003', 'SR-007', 'SR-037'],
        'evidence_level': 'moderate_evidence',
    },
    {
        'id': 'rr_active_pain_v1',
        'name': 'Active pain pattern removal',
        'category': 'injury_routing_rule',
        'factors': ['pain', 'injury_flags'],
        'condition': {'pain_scale': '>=4/10'},
        'adjustment': {'remove_aggravating_patterns': True, 'route_to_regression': True, 'recommend_medical_review_when_red_flags': True},
        'source_refs': ['SR-003', 'SR-041'],
        'evidence_level': 'moderate_evidence',
    },
    {
        'id': 'rr_high_stress_cns_v1',
        'name': 'High stress CNS downgrade',
        'category': 'recovery_readiness_rule',
        'factors': ['stress', 'mood'],
        'condition': {'stress': 'high'},
        'adjustment': {'downgrade_high_cns_work': True, 'prefer_technique_or_aerobic': True},
        'source_refs': ['SR-003', 'SR-007'],
        'evidence_level': 'coaching_consensus',
    },
]


NUTRITION_GUIDELINES = [
    {
        'id': 'nutrition_performance_carbs_v1',
        'category': 'fueling',
        'goal_tags': ['performance', 'sport_performance', 'endurance'],
        'guideline': 'Protect carbohydrate availability around hard sessions and competitions.',
        'safety_flags': ['avoid_aggressive_energy_deficit_during_high_load'],
        'source_refs': ['SR-005', 'SR-008'],
        'evidence_level': 'strong_evidence',
    },
    {
        'id': 'nutrition_protein_strength_v1',
        'category': 'protein',
        'goal_tags': ['muscle_gain', 'strength', 'fat_loss'],
        'guideline': 'Distribute protein across meals to support muscle repair and satiety.',
        'safety_flags': ['screen_for_low_energy_availability_when_intake_is_low'],
        'source_refs': ['SR-005', 'SR-008'],
        'evidence_level': 'strong_evidence',
    },
    {
        'id': 'nutrition_hydration_heat_v1',
        'category': 'hydration',
        'goal_tags': ['running', 'outdoor_sport', 'performance'],
        'guideline': 'Adjust fluid and electrolyte strategy for heat, sweat rate, duration, and body size.',
        'safety_flags': ['hyponatremia_risk_with_overdrinking', 'heat_illness_risk'],
        'source_refs': ['SR-006', 'SR-034', 'SR-036'],
        'evidence_level': 'strong_evidence',
    },
]


RUNNING_WORKOUTS = [
    {
        'id': 'run_easy_zone2_v1',
        'name': 'Easy Zone 2 Run',
        'workout_type': 'easy',
        'suitable_user_level': ['beginner', 'intermediate', 'advanced'],
        'purpose': 'Build aerobic base with low recovery cost.',
        'prescription': {'intensity': 'conversational', 'duration_min': '20-60'},
        'progression_logic': ['increase duration gradually', 'keep most weekly volume easy'],
        'source_refs': ['SR-029', 'SR-030', 'SR-031'],
        'evidence_level': 'moderate_evidence',
    },
    {
        'id': 'run_threshold_intervals_v1',
        'name': 'Threshold Intervals',
        'workout_type': 'threshold',
        'suitable_user_level': ['intermediate', 'advanced', 'beginner_with_coach_progression'],
        'purpose': 'Develop sustainable high aerobic power without all-out intensity.',
        'prescription': {'examples': ['3 x 8 min', '4 x 5 min'], 'rest': 'easy jog 2-3 min'},
        'progression_logic': ['increase total threshold time before pace', 'avoid after poor readiness'],
        'source_refs': ['SR-029', 'SR-030'],
        'evidence_level': 'moderate_evidence',
    },
]


RUNNING_PLAN_RULES = [
    {
        'id': 'run_conservative_progression_v1',
        'rule_type': 'progression',
        'applies_to': ['running'],
        'condition': 'no pain and weekly volume completed',
        'action': 'increase weekly distance conservatively, usually 5-10%',
        'source_refs': ['SR-031', 'SR-032'],
        'evidence_level': 'moderate_evidence',
    },
    {
        'id': 'run_heat_adjustment_v1',
        'rule_type': 'environment',
        'applies_to': ['running'],
        'condition': 'heat_or_humidity_high',
        'action': 'slow pace targets, lengthen rests, increase hydration prompts',
        'source_refs': ['SR-034', 'SR-036'],
        'evidence_level': 'strong_evidence',
    },
]


EQUIPMENT_LIBRARY = [
    {'id': 'bodyweight', 'name': 'Bodyweight', 'setting': 'anywhere', 'exercise_tags': ['push-up', 'squat', 'lunge', 'plank']},
    {'id': 'dumbbells', 'name': 'Dumbbells', 'setting': 'home_or_gym', 'exercise_tags': ['goblet squat', 'press', 'row', 'carry']},
    {'id': 'barbell', 'name': 'Barbell', 'setting': 'gym', 'exercise_tags': ['squat', 'deadlift', 'bench press', 'row']},
    {'id': 'kettlebell', 'name': 'Kettlebell', 'setting': 'home_or_gym', 'exercise_tags': ['swing', 'goblet squat', 'carry']},
    {'id': 'resistance_bands', 'name': 'Resistance Bands', 'setting': 'home_or_gym', 'exercise_tags': ['row', 'face pull', 'external rotation']},
    {'id': 'medicine_ball', 'name': 'Medicine Ball', 'setting': 'gym', 'exercise_tags': ['rotational throw', 'slam', 'chest pass']},
    {'id': 'pull_up_bar', 'name': 'Pull-up Bar', 'setting': 'home_or_gym', 'exercise_tags': ['pull-up', 'hang', 'knee raise']},
    {'id': 'bench', 'name': 'Bench', 'setting': 'home_or_gym', 'exercise_tags': ['bench press', 'step-up', 'split squat']},
    {'id': 'treadmill', 'name': 'Treadmill', 'setting': 'gym', 'exercise_tags': ['run', 'tempo', 'intervals']},
    {'id': 'bike', 'name': 'Bike', 'setting': 'home_or_gym', 'exercise_tags': ['zone 2', 'intervals', 'recovery']},
    {'id': 'rower', 'name': 'Rower', 'setting': 'gym', 'exercise_tags': ['conditioning', 'intervals']},
]


EXERCISE_LIBRARY = [
    {
        'id': 'goblet_squat',
        'name': 'Goblet Squat',
        'category': 'strength',
        'movement_patterns': ['squat'],
        'primary_muscles': ['quadriceps', 'glutes'],
        'secondary_muscles': ['core', 'adductors'],
        'equipment': ['dumbbells', 'kettlebell'],
        'difficulty': 'beginner',
        'coaching_cues': ['Brace before descending', 'Keep full foot on the floor', 'Drive knees in line with toes'],
        'common_mistakes': ['Heels lifting', 'Knees collapsing inward', 'Losing torso position'],
        'progressions': ['front squat', 'back squat'],
        'regressions': ['box squat', 'bodyweight squat'],
        'substitutions': ['split squat', 'leg press'],
        'sport_tags': ['cricket', 'volleyball', 'football', 'running', 'general'],
        'injury_flags': ['knee', 'hip'],
    },
    {
        'id': 'romanian_deadlift',
        'name': 'Romanian Deadlift',
        'category': 'strength',
        'movement_patterns': ['hinge'],
        'primary_muscles': ['hamstrings', 'glutes'],
        'secondary_muscles': ['erectors', 'lats', 'grip'],
        'equipment': ['barbell', 'dumbbells'],
        'difficulty': 'intermediate',
        'coaching_cues': ['Push hips back', 'Keep bar close', 'Stop before lumbar rounding'],
        'common_mistakes': ['Squatting the hinge', 'Rounding lower back', 'Overreaching range'],
        'progressions': ['single-leg romanian deadlift', 'trap bar deadlift'],
        'regressions': ['hip hinge drill', 'kettlebell deadlift'],
        'substitutions': ['hip thrust', 'hamstring curl'],
        'sport_tags': ['cricket', 'football', 'running', 'volleyball'],
        'injury_flags': ['low_back', 'hamstring'],
    },
    {
        'id': 'split_squat',
        'name': 'Split Squat',
        'category': 'strength',
        'movement_patterns': ['lunge', 'single_leg'],
        'primary_muscles': ['quadriceps', 'glutes'],
        'secondary_muscles': ['adductors', 'calves', 'core'],
        'equipment': ['bodyweight', 'dumbbells'],
        'difficulty': 'beginner',
        'coaching_cues': ['Tall posture', 'Control the descent', 'Push through front foot'],
        'common_mistakes': ['Front knee collapsing', 'Pushing off rear foot too much'],
        'progressions': ['rear-foot elevated split squat'],
        'regressions': ['assisted split squat', 'step-up'],
        'substitutions': ['reverse lunge', 'step-up'],
        'sport_tags': ['cricket', 'volleyball', 'football', 'running'],
        'injury_flags': ['knee', 'hip'],
    },
    {
        'id': 'push_up',
        'name': 'Push-up',
        'category': 'strength',
        'movement_patterns': ['horizontal_push'],
        'primary_muscles': ['chest', 'triceps'],
        'secondary_muscles': ['shoulders', 'core'],
        'equipment': ['bodyweight'],
        'difficulty': 'beginner',
        'coaching_cues': ['Body stays straight', 'Elbows 30-45 degrees', 'Reach the floor with control'],
        'common_mistakes': ['Hips sagging', 'Elbows flaring', 'Partial range only'],
        'progressions': ['weighted push-up', 'ring push-up'],
        'regressions': ['incline push-up', 'knee push-up'],
        'substitutions': ['dumbbell bench press'],
        'sport_tags': ['general', 'cricket', 'volleyball', 'football'],
        'injury_flags': ['shoulder', 'wrist'],
    },
    {
        'id': 'one_arm_dumbbell_row',
        'name': 'One-arm Dumbbell Row',
        'category': 'strength',
        'movement_patterns': ['horizontal_pull'],
        'primary_muscles': ['lats', 'upper_back'],
        'secondary_muscles': ['biceps', 'rear_delts', 'core'],
        'equipment': ['dumbbells', 'bench'],
        'difficulty': 'beginner',
        'coaching_cues': ['Pull elbow toward hip', 'Keep ribs down', 'Pause at top'],
        'common_mistakes': ['Shrugging', 'Twisting torso', 'Using momentum'],
        'progressions': ['chest-supported row', 'barbell row'],
        'regressions': ['band row'],
        'substitutions': ['cable row', 'inverted row'],
        'sport_tags': ['cricket', 'volleyball', 'general'],
        'injury_flags': ['shoulder', 'low_back'],
    },
    {
        'id': 'pallof_press',
        'name': 'Pallof Press',
        'category': 'core',
        'movement_patterns': ['anti_rotation'],
        'primary_muscles': ['obliques', 'deep_core'],
        'secondary_muscles': ['glutes', 'shoulders'],
        'equipment': ['resistance_bands', 'cable_machine'],
        'difficulty': 'beginner',
        'coaching_cues': ['Stay tall', 'Do not rotate', 'Exhale as arms extend'],
        'common_mistakes': ['Leaning away', 'Holding breath', 'Rushing reps'],
        'progressions': ['half-kneeling pallof press', 'pallof walkout'],
        'regressions': ['shorter lever pallof press'],
        'substitutions': ['dead bug', 'side plank'],
        'sport_tags': ['cricket', 'football', 'volleyball', 'running'],
        'injury_flags': ['low_back'],
    },
    {
        'id': 'dead_bug',
        'name': 'Dead Bug',
        'category': 'core',
        'movement_patterns': ['anti_extension'],
        'primary_muscles': ['deep_core'],
        'secondary_muscles': ['hip_flexors'],
        'equipment': ['bodyweight'],
        'difficulty': 'beginner',
        'coaching_cues': ['Lower back stays quiet', 'Move slowly', 'Exhale fully'],
        'common_mistakes': ['Arching lower back', 'Moving too fast'],
        'progressions': ['weighted dead bug', 'hollow hold'],
        'regressions': ['heel taps'],
        'substitutions': ['plank', 'bird dog'],
        'sport_tags': ['general', 'cricket', 'running'],
        'injury_flags': ['low_back'],
    },
    {
        'id': 'medicine_ball_rotational_throw',
        'name': 'Medicine Ball Rotational Throw',
        'category': 'power',
        'movement_patterns': ['rotation', 'throw'],
        'primary_muscles': ['obliques', 'hips'],
        'secondary_muscles': ['shoulders', 'upper_back'],
        'equipment': ['medicine_ball'],
        'difficulty': 'intermediate',
        'coaching_cues': ['Rotate through hips', 'Brace before throw', 'Move explosively'],
        'common_mistakes': ['Only using arms', 'Overarching lower back'],
        'progressions': ['step-behind rotational throw'],
        'regressions': ['half-kneeling rotational throw'],
        'substitutions': ['cable chop', 'band rotation'],
        'sport_tags': ['cricket', 'tennis', 'badminton', 'volleyball'],
        'injury_flags': ['shoulder', 'low_back'],
    },
    {
        'id': 'pogo_jump',
        'name': 'Pogo Jump',
        'category': 'plyometric',
        'movement_patterns': ['jump', 'ankle_stiffness'],
        'primary_muscles': ['calves', 'feet'],
        'secondary_muscles': ['quadriceps', 'glutes'],
        'equipment': ['bodyweight'],
        'difficulty': 'intermediate',
        'coaching_cues': ['Stay tall', 'Bounce through ankles', 'Quiet contacts'],
        'common_mistakes': ['Deep knee bend', 'Loud landings', 'Too much volume too soon'],
        'progressions': ['single-leg pogo', 'low hurdle hops'],
        'regressions': ['calf raise', 'jump rope'],
        'substitutions': ['jump rope', 'ankle hops'],
        'sport_tags': ['volleyball', 'running', 'football'],
        'injury_flags': ['ankle', 'achilles', 'knee'],
    },
    {
        'id': 'broad_jump',
        'name': 'Broad Jump',
        'category': 'power',
        'movement_patterns': ['jump', 'horizontal_power'],
        'primary_muscles': ['glutes', 'quadriceps', 'calves'],
        'secondary_muscles': ['hamstrings', 'core'],
        'equipment': ['bodyweight'],
        'difficulty': 'intermediate',
        'coaching_cues': ['Load hips', 'Swing arms', 'Land softly with control'],
        'common_mistakes': ['Landing stiff', 'Knees collapsing', 'Too many reps under fatigue'],
        'progressions': ['repeated broad jump'],
        'regressions': ['snap-down landing', 'box jump'],
        'substitutions': ['kettlebell swing', 'jump squat'],
        'sport_tags': ['volleyball', 'football', 'cricket'],
        'injury_flags': ['knee', 'ankle'],
    },
    {
        'id': 'acceleration_run',
        'name': 'Acceleration Run',
        'category': 'speed',
        'movement_patterns': ['sprint', 'acceleration'],
        'primary_muscles': ['glutes', 'hamstrings', 'calves'],
        'secondary_muscles': ['core', 'hip_flexors'],
        'equipment': ['bodyweight'],
        'difficulty': 'intermediate',
        'coaching_cues': ['Push the ground back', 'Low heel recovery early', 'Rest fully between reps'],
        'common_mistakes': ['Rushing rest', 'Overstriding', 'Running through pain'],
        'progressions': ['resisted sprint', 'flying sprint'],
        'regressions': ['march drill', 'wall drill'],
        'substitutions': ['bike sprint', 'sled push'],
        'sport_tags': ['cricket', 'football', 'running', 'volleyball'],
        'injury_flags': ['hamstring', 'calf', 'achilles'],
    },
    {
        'id': 'five_ten_five_shuttle',
        'name': '5-10-5 Shuttle',
        'category': 'agility',
        'movement_patterns': ['change_of_direction', 'deceleration'],
        'primary_muscles': ['quadriceps', 'glutes', 'adductors'],
        'secondary_muscles': ['calves', 'core'],
        'equipment': ['cones'],
        'difficulty': 'intermediate',
        'coaching_cues': ['Lower hips before cutting', 'Plant under body', 'Accelerate out'],
        'common_mistakes': ['Planting too wide', 'Upright braking', 'Excess volume'],
        'progressions': ['reactive shuttle'],
        'regressions': ['deceleration drill', 'lateral shuffle'],
        'substitutions': ['lateral bound stick', 'cone cuts'],
        'sport_tags': ['football', 'cricket', 'volleyball', 'badminton'],
        'injury_flags': ['knee', 'ankle', 'groin'],
    },
    {
        'id': 'face_pull',
        'name': 'Face Pull',
        'category': 'prehab',
        'movement_patterns': ['scapular_control', 'horizontal_pull'],
        'primary_muscles': ['rear_delts', 'mid_traps'],
        'secondary_muscles': ['rotator_cuff'],
        'equipment': ['resistance_bands', 'cable_machine'],
        'difficulty': 'beginner',
        'coaching_cues': ['Pull toward eyes', 'Rotate thumbs back', 'Do not shrug'],
        'common_mistakes': ['Lower-back arching', 'Too much load', 'Neck tension'],
        'progressions': ['cable face pull'],
        'regressions': ['band pull-apart'],
        'substitutions': ['band external rotation', 'prone Y raise'],
        'sport_tags': ['cricket', 'volleyball', 'badminton', 'general'],
        'injury_flags': ['shoulder', 'neck'],
    },
    {
        'id': 'band_external_rotation',
        'name': 'Band External Rotation',
        'category': 'prehab',
        'movement_patterns': ['shoulder_rotation'],
        'primary_muscles': ['rotator_cuff'],
        'secondary_muscles': ['rear_delts'],
        'equipment': ['resistance_bands'],
        'difficulty': 'beginner',
        'coaching_cues': ['Elbow stays near side', 'Rotate slowly', 'Keep shoulder blade set'],
        'common_mistakes': ['Twisting torso', 'Letting elbow drift', 'Using too much band tension'],
        'progressions': ['90-90 external rotation'],
        'regressions': ['isometric external rotation'],
        'substitutions': ['side-lying external rotation'],
        'sport_tags': ['cricket', 'volleyball', 'badminton', 'tennis'],
        'injury_flags': ['shoulder'],
    },
    {
        'id': 'copenhagen_plank',
        'name': 'Copenhagen Plank',
        'category': 'strength',
        'movement_patterns': ['adductor_strength', 'core'],
        'primary_muscles': ['adductors', 'obliques'],
        'secondary_muscles': ['glutes'],
        'equipment': ['bench'],
        'difficulty': 'advanced',
        'coaching_cues': ['Straight line from head to foot', 'Squeeze top leg down', 'Keep hips high'],
        'common_mistakes': ['Dropping hips', 'Too long a lever too soon'],
        'progressions': ['long-lever copenhagen plank'],
        'regressions': ['short-lever copenhagen plank'],
        'substitutions': ['side plank', 'adductor squeeze'],
        'sport_tags': ['football', 'cricket', 'running'],
        'injury_flags': ['groin', 'hip'],
    },
    {
        'id': 'farmers_carry',
        'name': "Farmer's Carry",
        'category': 'strength',
        'movement_patterns': ['carry', 'grip', 'anti_lateral_flexion'],
        'primary_muscles': ['traps', 'grip', 'core'],
        'secondary_muscles': ['glutes', 'calves'],
        'equipment': ['dumbbells', 'kettlebell'],
        'difficulty': 'beginner',
        'coaching_cues': ['Walk tall', 'Ribs down', 'Do not lean'],
        'common_mistakes': ['Shrugging excessively', 'Short choppy steps', 'Leaning to one side'],
        'progressions': ['suitcase carry', 'rack carry'],
        'regressions': ['lighter carry', 'march in place'],
        'substitutions': ['sled push', 'loaded march'],
        'sport_tags': ['general', 'cricket', 'football'],
        'injury_flags': ['low_back', 'shoulder'],
    },
    {
        'id': 'zone_2_run',
        'name': 'Zone 2 Run',
        'category': 'endurance',
        'movement_patterns': ['aerobic'],
        'primary_muscles': ['cardiorespiratory_system'],
        'secondary_muscles': ['calves', 'quadriceps', 'glutes'],
        'equipment': ['bodyweight', 'treadmill'],
        'difficulty': 'beginner',
        'coaching_cues': ['Conversational pace', 'Relax shoulders', 'Finish feeling repeatable'],
        'common_mistakes': ['Running too hard', 'Ignoring pain', 'Increasing volume too quickly'],
        'progressions': ['long run', 'tempo intervals'],
        'regressions': ['run-walk', 'bike zone 2'],
        'substitutions': ['bike', 'rower', 'brisk walk'],
        'sport_tags': ['running', 'football', 'cricket', 'general'],
        'injury_flags': ['knee', 'shin', 'achilles'],
    },
]


SPORT_PROFILES = [
    {
        'id': 'cricket',
        'sport': 'cricket',
        'physical_demands': ['acceleration', 'rotational_power', 'repeated_sprint_ability', 'throwing_capacity', 'fielding_agility'],
        'key_qualities': ['posterior_chain_strength', 'single_leg_strength', 'trunk_rotation_control', 'shoulder_durability', 'sprint_mechanics'],
        'training_priorities': ['rotational_power', 'hamstring_resilience', 'lumbopelvic_control', 'shoulder_prehab', 'acceleration'],
        'common_injuries': ['low_back', 'hamstring', 'shoulder', 'ankle', 'knee'],
        'conditioning_needs': ['repeated_efforts', 'speed_repeatability', 'aerobic_base'],
        'season_phases': ['off_season', 'pre_season', 'in_season'],
        'source_ids': ['cricket-bowling-demands-2021', 'cricketers-shoulder-2020'],
    },
    {
        'id': 'volleyball',
        'sport': 'volleyball',
        'physical_demands': ['repeated_jumping', 'landing', 'lateral_movement', 'overhead_hitting', 'reactive_agility'],
        'key_qualities': ['vertical_power', 'reactive_strength', 'ankle_stiffness', 'knee_control', 'shoulder_capacity'],
        'training_priorities': ['landing_mechanics', 'plyometric_progression', 'deceleration', 'shoulder_prehab', 'trunk_stability'],
        'common_injuries': ['ankle', 'patellar_tendon', 'shoulder', 'finger_thumb', 'concussion'],
        'conditioning_needs': ['alactic_repeats', 'jump_repeatability', 'short_recovery_bouts'],
        'season_phases': ['off_season', 'pre_season', 'in_season'],
        'source_ids': ['volleyball-injury-epidemiology-2023'],
    },
    {
        'id': 'football',
        'sport': 'football',
        'aliases': ['soccer'],
        'physical_demands': ['sprinting', 'deceleration', 'change_of_direction', 'aerobic_power', 'contact_tolerance'],
        'key_qualities': ['eccentric_hamstring_strength', 'adductor_strength', 'ankle_knee_control', 'repeat_sprint_ability'],
        'training_priorities': ['hamstring_resilience', 'adductor_strength', 'deceleration', 'core_stability', 'plyometrics'],
        'common_injuries': ['hamstring', 'groin', 'ankle', 'knee'],
        'conditioning_needs': ['aerobic_base', 'repeated_sprints', 'high_intensity_intervals'],
        'season_phases': ['off_season', 'pre_season', 'in_season'],
        'source_ids': ['fifa-11-plus-review-2017'],
    },
    {
        'id': 'running',
        'sport': 'running',
        'physical_demands': ['aerobic_endurance', 'tendon_capacity', 'single_leg_stiffness', 'pace_control'],
        'key_qualities': ['calf_capacity', 'hip_stability', 'posterior_chain_strength', 'aerobic_base'],
        'training_priorities': ['gradual_volume', 'strength_maintenance', 'calf_foot_capacity', 'easy_hard_distribution'],
        'common_injuries': ['shin', 'knee', 'achilles', 'plantar_fascia', 'hip'],
        'conditioning_needs': ['zone_2_base', 'threshold_work', 'race_specific_pace'],
        'season_phases': ['base', 'build', 'race', 'recovery'],
        'source_ids': ['who-physical-activity-2020', 'acsm-progression-models-2009'],
    },
    {
        'id': 'general_fitness',
        'sport': 'general_fitness',
        'physical_demands': ['strength', 'aerobic_capacity', 'mobility', 'body_composition'],
        'key_qualities': ['movement_quality', 'work_capacity', 'consistency'],
        'training_priorities': ['full_body_strength', 'aerobic_base', 'mobility', 'progressive_overload'],
        'common_injuries': ['low_back', 'knee', 'shoulder'],
        'conditioning_needs': ['moderate_aerobic_work', 'intervals_as_tolerated'],
        'season_phases': ['general'],
        'source_ids': ['who-physical-activity-2020', 'cdc-adult-activity-basics', 'acsm-progression-models-2009'],
    },
]


SPORT_ROLES = [
    {'id': 'cricket_fast_bowler', 'sport': 'cricket', 'role': 'fast_bowler', 'priorities': ['lumbar_load_management', 'hamstring_resilience', 'shoulder_capacity', 'run_up_speed'], 'risk_areas': ['low_back', 'hamstring', 'shoulder']},
    {'id': 'cricket_batter', 'sport': 'cricket', 'role': 'batter', 'priorities': ['rotational_power', 'acceleration', 'trunk_control'], 'risk_areas': ['low_back', 'shoulder', 'hamstring']},
    {'id': 'cricket_wicketkeeper', 'sport': 'cricket', 'role': 'wicketkeeper', 'priorities': ['hip_mobility', 'reactive_agility', 'knee_capacity'], 'risk_areas': ['knee', 'hip', 'low_back']},
    {'id': 'volleyball_setter', 'sport': 'volleyball', 'role': 'setter', 'priorities': ['landing_control', 'shoulder_durability', 'reactive_agility'], 'risk_areas': ['ankle', 'shoulder', 'finger_thumb']},
    {'id': 'volleyball_hitter', 'sport': 'volleyball', 'role': 'outside_hitter', 'priorities': ['vertical_power', 'shoulder_capacity', 'deceleration'], 'risk_areas': ['patellar_tendon', 'ankle', 'shoulder']},
    {'id': 'volleyball_libero', 'sport': 'volleyball', 'role': 'libero', 'priorities': ['lateral_quickness', 'deceleration', 'trunk_control'], 'risk_areas': ['ankle', 'knee', 'low_back']},
    {'id': 'football_midfielder', 'sport': 'football', 'role': 'midfielder', 'priorities': ['aerobic_power', 'change_of_direction', 'hamstring_resilience'], 'risk_areas': ['hamstring', 'groin', 'ankle']},
    {'id': 'running_5k_10k', 'sport': 'running', 'role': '5k_10k', 'priorities': ['aerobic_base', 'threshold_pace', 'calf_capacity'], 'risk_areas': ['shin', 'achilles', 'knee']},
]


INJURY_MODIFICATIONS = [
    {'id': 'knee_pain', 'body_area': 'knee', 'avoid_patterns': ['high_volume_jumping', 'deep_knee_flexion_under_fatigue'], 'safe_patterns': ['hinge', 'hip_dominant', 'controlled_step_up'], 'regressions': ['box squat', 'split squat partial range'], 'red_flags': ['swelling', 'locking', 'giving way']},
    {'id': 'shoulder_pain', 'body_area': 'shoulder', 'avoid_patterns': ['high_volume_overhead', 'painful_pressing'], 'safe_patterns': ['scapular_control', 'horizontal_pull', 'rotator_cuff_isometrics'], 'regressions': ['landmine press', 'incline push-up'], 'red_flags': ['night pain', 'loss of strength', 'instability']},
    {'id': 'low_back_pain', 'body_area': 'low_back', 'avoid_patterns': ['heavy_axial_loading', 'loaded_rotation', 'end_range_flexion_under_load'], 'safe_patterns': ['anti_rotation', 'split_stance', 'hip_hinge_regression'], 'regressions': ['dead bug', 'goblet squat', 'hip thrust'], 'red_flags': ['radiating pain', 'numbness', 'bowel bladder changes']},
    {'id': 'hamstring_pain', 'body_area': 'hamstring', 'avoid_patterns': ['max_sprinting', 'aggressive_stretching'], 'safe_patterns': ['isometric_hinge', 'glute_bridge', 'bike_conditioning'], 'regressions': ['short_lever bridge', 'tempo RDL light'], 'red_flags': ['bruising', 'pop sensation', 'walking pain']},
    {'id': 'ankle_pain', 'body_area': 'ankle', 'avoid_patterns': ['reactive_jumps', 'hard_cuts'], 'safe_patterns': ['balance', 'calf_isometrics', 'linear_strength'], 'regressions': ['calf raise', 'marching drill'], 'red_flags': ['unable to bear weight', 'major swelling']},
    {'id': 'groin_pain', 'body_area': 'groin', 'avoid_patterns': ['wide_cutting', 'aggressive_lateral_lunges'], 'safe_patterns': ['short_lever_adductor', 'linear_strength'], 'regressions': ['adductor squeeze', 'side plank'], 'red_flags': ['sharp pain with walking', 'rapid swelling']},
]


PROGRESSION_RULES = [
    {'id': 'strength_load_up', 'rule_type': 'progress', 'applies_to': ['strength'], 'condition': 'completion >= 90% and rpe <= 7 and pain <= 3', 'action': 'increase load 2.5-5% next exposure'},
    {'id': 'strength_hold', 'rule_type': 'hold', 'applies_to': ['strength'], 'condition': 'rpe 8-9 or completion 70-89%', 'action': 'repeat same prescription before progressing'},
    {'id': 'pain_regress', 'rule_type': 'regress', 'applies_to': ['all'], 'condition': 'pain >= 4', 'action': 'swap to pain-free regression and reduce volume 20-40%'},
    {'id': 'sleep_reduce', 'rule_type': 'modify', 'applies_to': ['strength', 'conditioning'], 'condition': 'sleep_hours < 6 or sleep_score < 60', 'action': 'reduce volume 20% and avoid max-intensity work'},
    {'id': 'missed_sessions', 'rule_type': 'reschedule', 'applies_to': ['program'], 'condition': 'missed_sessions >= 2 in 7 days', 'action': 'repeat current week or compress to priority sessions'},
    {'id': 'plyometric_volume', 'rule_type': 'progress', 'applies_to': ['plyometric'], 'condition': 'no tendon pain and landings controlled', 'action': 'increase contacts by 10-15% weekly'},
    {'id': 'running_volume', 'rule_type': 'progress', 'applies_to': ['running'], 'condition': 'no pain and weekly_km completed', 'action': 'increase weekly distance no more than 5-10%'},
    {'id': 'high_run_day', 'rule_type': 'modify', 'applies_to': ['strength'], 'condition': 'run_distance_km >= 5 and strength_pending', 'action': 'keep strength technique-focused and avoid heavy lower-body volume'},
]


BENCHMARK_TESTS = [
    {'id': 'push_up_max', 'test_name': 'Push-up Max Set', 'qualities': ['upper_body_strength_endurance'], 'sport_tags': ['general', 'cricket', 'volleyball'], 'unit': 'reps'},
    {'id': 'pull_up_max', 'test_name': 'Pull-up Max Set', 'qualities': ['relative_upper_body_strength'], 'sport_tags': ['general', 'cricket', 'volleyball'], 'unit': 'reps'},
    {'id': 'plank_hold', 'test_name': 'Plank Hold', 'qualities': ['trunk_endurance'], 'sport_tags': ['general', 'running', 'cricket'], 'unit': 'seconds'},
    {'id': 'broad_jump', 'test_name': 'Broad Jump', 'qualities': ['horizontal_power'], 'sport_tags': ['cricket', 'football', 'volleyball'], 'unit': 'cm'},
    {'id': 'vertical_jump', 'test_name': 'Vertical Jump', 'qualities': ['vertical_power'], 'sport_tags': ['volleyball', 'football', 'cricket'], 'unit': 'cm'},
    {'id': 'twenty_meter_sprint', 'test_name': '20m Sprint', 'qualities': ['acceleration'], 'sport_tags': ['cricket', 'football', 'volleyball'], 'unit': 'seconds'},
    {'id': 'five_ten_five', 'test_name': '5-10-5 Agility', 'qualities': ['change_of_direction'], 'sport_tags': ['football', 'cricket', 'badminton', 'volleyball'], 'unit': 'seconds'},
    {'id': 'one_km_time_trial', 'test_name': '1km Time Trial', 'qualities': ['aerobic_power', 'pace_control'], 'sport_tags': ['running', 'football', 'cricket'], 'unit': 'time'},
]


WORKOUT_TEMPLATES = [
    {
        'id': 'athletic_lower_strength',
        'title': 'Athletic Lower Strength',
        'category': 'strength',
        'level': 'beginner_intermediate',
        'duration_min': 45,
        'sport_tags': ['general', 'cricket', 'volleyball', 'football', 'running'],
        'equipment_required': ['dumbbells'],
        'exercise_slots': [
            {'slot': 'main_squat', 'exercise_ids': ['goblet_squat'], 'sets': 4, 'reps': '6-10', 'rest': '90 sec'},
            {'slot': 'hinge', 'exercise_ids': ['romanian_deadlift'], 'sets': 3, 'reps': '8-10', 'rest': '75 sec'},
            {'slot': 'single_leg', 'exercise_ids': ['split_squat'], 'sets': 3, 'reps': '8 each', 'rest': '60 sec'},
            {'slot': 'core', 'exercise_ids': ['dead_bug'], 'sets': 3, 'reps': '10 each', 'rest': '45 sec'},
        ],
    },
    {
        'id': 'cricket_power_rotation',
        'title': 'Cricket Power + Rotation',
        'category': 'power',
        'level': 'intermediate',
        'duration_min': 45,
        'sport_tags': ['cricket'],
        'equipment_required': ['medicine_ball', 'resistance_bands'],
        'exercise_slots': [
            {'slot': 'sprint', 'exercise_ids': ['acceleration_run'], 'sets': 6, 'reps': '20 m', 'rest': '75 sec'},
            {'slot': 'rotation_power', 'exercise_ids': ['medicine_ball_rotational_throw'], 'sets': 4, 'reps': '5 each', 'rest': '60 sec'},
            {'slot': 'anti_rotation', 'exercise_ids': ['pallof_press'], 'sets': 3, 'reps': '10 each', 'rest': '45 sec'},
            {'slot': 'shoulder_care', 'exercise_ids': ['band_external_rotation', 'face_pull'], 'sets': 2, 'reps': '15', 'rest': '30 sec'},
        ],
    },
    {
        'id': 'volleyball_jump_landing',
        'title': 'Volleyball Jump + Landing Prep',
        'category': 'plyometric',
        'level': 'intermediate',
        'duration_min': 40,
        'sport_tags': ['volleyball'],
        'equipment_required': ['bodyweight'],
        'exercise_slots': [
            {'slot': 'ankle_stiffness', 'exercise_ids': ['pogo_jump'], 'sets': 3, 'reps': '20 sec', 'rest': '45 sec'},
            {'slot': 'horizontal_power', 'exercise_ids': ['broad_jump'], 'sets': 4, 'reps': '3', 'rest': '75 sec'},
            {'slot': 'single_leg_strength', 'exercise_ids': ['split_squat'], 'sets': 3, 'reps': '8 each', 'rest': '60 sec'},
            {'slot': 'shoulder_care', 'exercise_ids': ['face_pull'], 'sets': 3, 'reps': '15', 'rest': '45 sec'},
        ],
    },
    {
        'id': 'runner_strength_maintenance',
        'title': 'Runner Strength Maintenance',
        'category': 'strength',
        'level': 'beginner_intermediate',
        'duration_min': 35,
        'sport_tags': ['running'],
        'equipment_required': ['bodyweight', 'dumbbells'],
        'exercise_slots': [
            {'slot': 'single_leg', 'exercise_ids': ['split_squat'], 'sets': 3, 'reps': '8 each', 'rest': '60 sec'},
            {'slot': 'hinge', 'exercise_ids': ['romanian_deadlift'], 'sets': 3, 'reps': '8', 'rest': '75 sec'},
            {'slot': 'ankle_capacity', 'exercise_ids': ['pogo_jump'], 'sets': 2, 'reps': '15 sec', 'rest': '45 sec'},
            {'slot': 'core', 'exercise_ids': ['pallof_press'], 'sets': 3, 'reps': '10 each', 'rest': '45 sec'},
        ],
    },
    {
        'id': 'full_body_fat_loss_circuit',
        'title': 'Full Body Fat Loss Circuit',
        'category': 'conditioning',
        'level': 'beginner',
        'duration_min': 35,
        'sport_tags': ['general'],
        'equipment_required': ['bodyweight', 'dumbbells'],
        'exercise_slots': [
            {'slot': 'lower', 'exercise_ids': ['goblet_squat'], 'sets': 3, 'reps': '12', 'rest': '30 sec'},
            {'slot': 'upper_push', 'exercise_ids': ['push_up'], 'sets': 3, 'reps': '8-12', 'rest': '30 sec'},
            {'slot': 'upper_pull', 'exercise_ids': ['one_arm_dumbbell_row'], 'sets': 3, 'reps': '10 each', 'rest': '30 sec'},
            {'slot': 'carry', 'exercise_ids': ['farmers_carry'], 'sets': 3, 'reps': '30 m', 'rest': '60 sec'},
        ],
    },
]


SPORT_SLUG_OVERRIDES = {
    'boxing': 'boxing',
    'running': 'running',
    'football/soccer': 'football',
    'football': 'football',
    'soccer': 'football',
    'cricket': 'cricket',
    'basketball': 'basketball',
    'badminton': 'badminton',
    'tennis': 'tennis',
    'swimming': 'swimming',
    'calisthenics': 'calisthenics',
    'strength training / general fitness': 'general_fitness',
}


def _slug(value: str) -> str:
    normalized = value.strip().lower().replace('&', 'and')
    normalized = re.sub(r'[^a-z0-9]+', '_', normalized).strip('_')
    return normalized or 'unknown'


def _with_envelope(doc: Dict[str, Any], *, usage_profile: str = 'UP-DEFAULT') -> Dict[str, Any]:
    source_refs = doc.get('source_refs') or doc.get('source_ids') or []
    return {
        **DEFAULT_ENVELOPE,
        **doc,
        'source_refs': source_refs,
        'sftc_app_usage_profile_id': doc.get('sftc_app_usage_profile_id') or usage_profile,
        'last_reviewed_date': doc.get('last_reviewed_date') or DEFAULT_ENVELOPE['last_reviewed_date'],
        'expert_validation_status': doc.get('expert_validation_status') or DEFAULT_ENVELOPE['expert_validation_status'],
        'version': doc.get('version') or DEFAULT_ENVELOPE['version'],
    }


def _read_report() -> str:
    if not REPORT_PATH.exists():
        return ''
    return REPORT_PATH.read_text(encoding='utf-8')


def _report_json_objects() -> List[Dict[str, Any]]:
    text = _read_report()
    objects: List[Dict[str, Any]] = []
    for raw_block in re.findall(r'```json\s*(\{.*?\})\s*```', text, flags=re.DOTALL):
        try:
            parsed = json.loads(raw_block)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed.get('id'):
            objects.append(parsed)
    return objects


def _report_source_registry() -> List[Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    for line in _read_report().splitlines():
        if not line.startswith('| SR-'):
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if len(cells) < 6:
            continue
        source_id, title, source_type_year, relevance, limitations, citation = cells[:6]
        try:
            evidence_rank = int(re.sub(r'[^0-9]', '', relevance) or '0')
        except ValueError:
            evidence_rank = 0
        records[source_id] = {
            'id': source_id,
            'title': title,
            'source_type_year': source_type_year,
            'evidence_rank': evidence_rank,
            'limitations': limitations,
            'citation_ref': citation,
            'source_origin': 'deep-research-report.md',
        }
    return list(records.values())


def _normalize_report_sport_record(record: Dict[str, Any]) -> Dict[str, Any]:
    display_name = str(record.get('sport_name') or record.get('name') or '').strip()
    sport_key = SPORT_SLUG_OVERRIDES.get(display_name.lower(), _slug(display_name))
    source_refs = record.get('source_refs') or []
    training_priorities = record.get('exercise_buckets') or []
    demand_profile = record.get('demand_profile') or {}
    key_qualities = [
        quality for quality, value in demand_profile.items()
        if str(value).lower() in {'high', 'very_high', 'moderate_high', 'primary'}
    ]
    return _with_envelope(
        {
            'id': sport_key,
            'sport': sport_key,
            'display_name': display_name,
            'sport_name': display_name,
            'sport_category': record.get('sport_category'),
            'athlete_types': record.get('athlete_types') or [],
            'roles': record.get('roles') or [],
            'physical_demands': record.get('movement_demands') or [],
            'demand_profile': demand_profile,
            'energy_systems': record.get('energy_systems') or {},
            'key_qualities': key_qualities,
            'training_priorities': training_priorities,
            'common_injuries': record.get('common_injuries') or [],
            'conditioning_needs': record.get('conditioning_needs') or [],
            'kpis': record.get('kpis') or [],
            'tests': record.get('tests') or [],
            'weekly_training_logic': record.get('weekly_training_logic') or {},
            'ai_rules': record.get('ai_rules') or [],
            'report_record_id': record.get('id'),
            'raw_report_record': record,
            'source_refs': source_refs,
            'evidence_level': record.get('evidence_level') or 'coaching_consensus',
        },
        usage_profile='UP-SPORT-DEFAULT',
    )


def _report_sport_profiles() -> List[Dict[str, Any]]:
    profiles = []
    for record in _report_json_objects():
        record_id = str(record.get('id') or '')
        if record_id.startswith('sport_') and record_id.endswith('_starter_v01'):
            profiles.append(_normalize_report_sport_record(record))
    return profiles


def _report_sport_roles() -> List[Dict[str, Any]]:
    roles: List[Dict[str, Any]] = []
    for profile in _report_sport_profiles():
        for role in profile.get('roles') or []:
            roles.append(_with_envelope(
                {
                    'id': f"{profile['sport']}_{_slug(str(role))}",
                    'sport': profile['sport'],
                    'role': role,
                    'priorities': profile.get('training_priorities') or [],
                    'risk_areas': profile.get('common_injuries') or [],
                    'source_refs': profile.get('source_refs') or [],
                    'evidence_level': profile.get('evidence_level'),
                    'source_origin': 'deep-research-report.md',
                },
                usage_profile='UP-SPORT-DEFAULT',
            ))
    return roles


def _report_sport_training_rules() -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    for profile in _report_sport_profiles():
        for index, rule in enumerate(profile.get('ai_rules') or [], start=1):
            rules.append(_with_envelope(
                {
                    'id': f"{profile['sport']}_rule_{index}",
                    'sport': profile['sport'],
                    'condition': rule.get('condition'),
                    'decision': rule.get('decision'),
                    'reason': rule.get('reason'),
                    'source_refs': profile.get('source_refs') or [],
                    'evidence_level': profile.get('evidence_level'),
                    'source_origin': 'deep-research-report.md',
                },
                usage_profile='UP-SPORT-DEFAULT',
            ))
    return rules


def _collection_seeds() -> Dict[str, List[Dict[str, Any]]]:
    report_profiles = _report_sport_profiles()
    report_profile_sports = {profile['sport'] for profile in report_profiles}
    base_profiles = [
        _with_envelope(profile, usage_profile='UP-SPORT-DEFAULT')
        for profile in SPORT_PROFILES
        if profile.get('sport') not in report_profile_sports
    ]
    report_role_ids = {role['id'] for role in _report_sport_roles()}
    base_roles = [
        _with_envelope(role, usage_profile='UP-SPORT-DEFAULT')
        for role in SPORT_ROLES
        if role.get('id') not in report_role_ids
    ]
    return {
        'equipment_library': [_with_envelope(doc) for doc in EQUIPMENT_LIBRARY],
        'exercise_library': [_with_envelope(doc, usage_profile='UP-EXERCISE-DEFAULT') for doc in EXERCISE_LIBRARY],
        'movement_patterns': [_with_envelope(doc) for doc in MOVEMENT_PATTERNS],
        'physical_qualities': [_with_envelope(doc) for doc in PHYSICAL_QUALITIES],
        'sport_profiles': [*base_profiles, *report_profiles],
        'sport_roles': [*base_roles, *_report_sport_roles()],
        'sport_training_rules': _report_sport_training_rules(),
        'injury_modifications': [_with_envelope(doc) for doc in INJURY_MODIFICATIONS],
        'progression_rules': [_with_envelope(doc) for doc in PROGRESSION_RULES],
        'readiness_rules': [_with_envelope(doc) for doc in READINESS_RULES],
        'benchmark_tests': [_with_envelope(doc) for doc in BENCHMARK_TESTS],
        'workout_templates': [_with_envelope(doc) for doc in WORKOUT_TEMPLATES],
        'knowledge_sources': [_with_envelope(doc) for doc in SOURCE_REFERENCES],
        'source_registry': [_with_envelope(doc) for doc in _report_source_registry()],
        'nutrition_guidelines': [_with_envelope(doc) for doc in NUTRITION_GUIDELINES],
        'running_workouts': [_with_envelope(doc) for doc in RUNNING_WORKOUTS],
        'running_plan_rules': [_with_envelope(doc) for doc in RUNNING_PLAN_RULES],
    }


async def _upsert_many(collection: Any, docs: Iterable[Dict[str, Any]], reset: bool) -> int:
    count = 0
    if reset:
        await collection.delete_many({})
    now = datetime.utcnow()
    for doc in docs:
        seeded = {**doc, 'updated_at': now}
        lookup = {'id': doc['id']}
        if collection.name == 'sport_profiles' and doc.get('sport'):
            lookup = {'sport': doc['sport']}
        elif collection.name == 'sport_roles' and doc.get('sport') and doc.get('role'):
            lookup = {'sport': doc['sport'], 'role': doc['role']}
        await collection.update_one(
            lookup,
            {
                '$set': seeded,
                '$setOnInsert': {'created_at': now},
            },
            upsert=True,
        )
        count += 1
    return count


async def seed_knowledge_base(reset: bool = False) -> Dict[str, int]:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await ensure_database_schema(db)

    summary: Dict[str, int] = {}
    for collection_name, docs in _collection_seeds().items():
        summary[collection_name] = await _upsert_many(db[collection_name], docs, reset)
    client.close()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description='Seed SFTC exercise and sports knowledge base.')
    parser.add_argument('--reset', action='store_true', help='Delete seeded knowledge collections before inserting.')
    args = parser.parse_args()
    summary = asyncio.run(seed_knowledge_base(reset=args.reset))
    for collection_name, count in summary.items():
        print(f'{collection_name}: {count}')


if __name__ == '__main__':
    main()
