# Sport Database Status Report

Generated: 2026-06-27T10:16:43+00:00

This report checks the current app-facing sport teaching database and retrieval layer. It does not call an AI model.

## Source Packs

| source_book_id | title | source_sections | knowledge_sources |
| --- | --- | --- | --- |
| calisthenics_playbook_push_pull_squat_2024 | Calisthenics Playbook for Push Pull Squat | 147 | 1 |
| advanced_calisthenics_web_research_v1 | Advanced Calisthenics Web Research Pack | 68 | 1 |
| plyometrics_complete_extraction_v1 | Plyometrics Complete Local Extraction | 118 | 1 |
| mobility_flexibility_web_research_v1 | Mobility and Flexibility Web Research Pack | 56 | 1 |
| general_gym_exercise_research_v1 | General Gym Exercise Research Library | 317 | 1 |
| cricket_level_teaching_database_v1 | SFTC Cricket Level-Based Teaching Database | 8 | 1 |
| volleyball_teaching_database_v1 | SFTC Volleyball Teaching And Planning Database | 8 | 1 |
| football_teaching_database_v1 | SFTC Football/Soccer Teaching And Planning Database | 10 | 1 |
| basketball_teaching_database_v1 | SFTC Basketball Teaching And Planning Database | 5 | 1 |
| badminton_teaching_database_v1 | SFTC Badminton Teaching Database | 15 | 1 |
| boxing_teaching_database_v1 | SFTC Boxing Teaching Database | 11 | 1 |
| cycling_teaching_database_v1 | SFTC Cycling Teaching Database | 14 | 1 |
| kickboxing_teaching_database_v1 | SFTC Kickboxing Teaching Database | 6 | 1 |
| mma_teaching_database_v1 | SFTC MMA Teaching Database | 5 | 1 |
| running_teaching_database_v1 | SFTC Running Endurance Teaching Database | 11 | 1 |
| swimming_teaching_database_v1 | SFTC Swimming Teaching Database | 16 | 1 |
| tennis_teaching_database_v1 | SFTC Tennis Teaching Database | 16 | 1 |
| wrestling_teaching_database_v1 | SFTC Wrestling Teaching Database | 5 | 1 |

## Sport Collection Counts

| sport | profiles | roles | training_rules | planning_rules | teaching_progressions | skill_assessments | transition_rules |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cricket | 1 | 0 | 0 | 2 | 24 | 6 | 6 |
| volleyball | 1 | 7 | 148 | 18 | 27 | 9 | 6 |
| soccer | 1 | 9 | 195 | 27 | 30 | 10 | 6 |
| basketball | 1 | 7 | 75 | 28 | 33 | 11 | 6 |
| boxing | 1 | 6 | 383 | 48 | 27 | 8 | 3 |
| kickboxing | 1 | 15 | 26 | 18 | 10 | 17 | 14 |
| mma | 1 | 11 | 32 | 22 | 24 | 22 | 17 |
| wrestling | 1 | 10 | 22 | 14 | 21 | 20 | 13 |
| running_endurance | 1 | 0 | 11 | 11 | 33 | 11 | 3 |
| badminton | 1 | 5 | 288 | 161 | 117 | 15 | 3 |
| tennis | 1 | 7 | 577 | 321 | 130 | 16 | 3 |
| swimming | 1 | 10 | 490 | 261 | 124 | 16 | 3 |
| cycling | 1 | 12 | 483 | 299 | 204 | 16 | 3 |

## Retrieval Smoke Tests

### cricket_beginner_batter

- sport teaching counts: `{'teaching_progressions': 5, 'skill_assessments': 2, 'level_transition_rules': 1}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 5, 'sport_skill_assessments': 2, 'sport_level_transition_rules': 1}`
- top progressions: `['cricket_teach_fielding_beginner', 'cricket_teach_batting_beginner', 'cricket_teach_match_iq_beginner', 'cricket_teach_cricket_snc_beginner', 'cricket_teach_throwing_beginner']`
- top assessments: `['cricket_assess_match_iq_level', 'cricket_assess_batting_level']`
- top transition rules: `['cricket_level_beginner_to_intermediate_general']`
- compact primary exercises: `['mob_drill_bird_dog', 'mob_drill_band_pull_apart', 'ex_dumbbell_bench_press', 'ex_pallof_press_iso_hold', 'mob_drill_dead_bug']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 1}`

### volleyball_intermediate_outside_hitter

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 3}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 3}`
- top progressions: `['volleyball_teach_transition_intermediate', 'volleyball_teach_serving_intermediate', 'volleyball_teach_passing_serve_receive_intermediate', 'volleyball_teach_defense_digging_intermediate', 'volleyball_teach_blocking_intermediate']`
- top assessments: `['volleyball_assess_serving', 'volleyball_assess_defense_digging', 'volleyball_assess_blocking']`
- top transition rules: `['volleyball_global_intermediate_to_advanced', 'volleyball_role_specialization_timing', 'volleyball_regression_and_return_rule']`
- compact primary exercises: `['mob_drill_bird_dog', 'mob_drill_dead_bug', 'ex_trap_bar_deadlift', 'ex_safety_bar_squat', 'ex_dumbbell_shoulder_press']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### football_intermediate_winger

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 3}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 3}`
- top progressions: `['soccer_teach_shooting_finishing_intermediate', 'soccer_teach_first_touch_receiving_intermediate', 'soccer_teach_dribbling_1v1_intermediate', 'soccer_teach_crossing_chance_creation_intermediate', 'soccer_teach_defending_pressing_intermediate']`
- top assessments: `['soccer_assess_shooting_finishing', 'soccer_assess_passing', 'soccer_assess_first_touch_receiving']`
- top transition rules: `['soccer_global_intermediate_to_advanced', 'soccer_regression_and_return_rule', 'soccer_position_specificity_timing']`
- compact primary exercises: `['ex_standing_single_leg_leg_curl', 'ex_single_leg_calf_raise', 'ex_lateral_lunge', 'ex_forward_lunge', 'ex_trap_bar_deadlift']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### basketball_beginner_point_guard

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 1}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 1}`
- top progressions: `['basketball_teach_ball_handling_beginner', 'basketball_teach_transition_beginner', 'basketball_teach_pick_and_roll_beginner', 'basketball_teach_shooting_beginner', 'basketball_teach_passing_beginner']`
- top assessments: `['basketball_assess_transition', 'basketball_assess_shooting', 'basketball_assess_pick_and_roll']`
- top transition rules: `['basketball_beginner_to_intermediate']`
- compact primary exercises: `['ex_split_squat', 'mob_drill_dead_bug', 'mob_drill_bird_dog', 'ex_reverse_lunge', 'ex_one_arm_dumbbell_row']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 1}`

### boxing_beginner_out_boxer

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 1}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 1}`
- top progressions: `['boxing_teach_stance_guard_beginner', 'boxing_teach_punch_mechanics_beginner', 'boxing_teach_boxing_strength_conditioning_beginner', 'boxing_teach_tactical_iq_beginner', 'boxing_teach_style_archetypes_beginner']`
- top assessments: `['boxing_assess_tactical_iq', 'boxing_assess_style_archetypes', 'boxing_assess_stance_guard']`
- top transition rules: `['boxing_beginner_to_intermediate']`
- compact primary exercises: `['mob_drill_bird_dog', 'mob_drill_dead_bug', 'ex_landmine_squat', 'ex_dumbbell_floor_press', 'ex_suspension_trainer_row']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 1}`

### kickboxing_beginner_k1

- sport teaching counts: `{'teaching_progressions': 3, 'skill_assessments': 3, 'level_transition_rules': 3}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 3, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 3}`
- top progressions: `['kickboxing_progression_contact_readiness', 'kickboxing_progression_beginner_foundation', 'kickboxing_progression_basic_punch_to_kick_chain']`
- top assessments: `['kickboxing_assess_stance_guard_recovery', 'kickboxing_assessment_strike_recovery', 'kickboxing_assessment_k1_clinch_knee_filter']`
- top transition rules: `['kickboxing_transition_beginner_to_intermediate_striking', 'kickboxing_transition_beginner_to_intermediate', 'kickboxing_transition_beginner_to_intermediate_movement']`
- compact primary exercises: `['mob_drill_bird_dog', 'mob_drill_dead_bug', 'ex_box_squat', 'ex_landmine_squat', 'ex_standing_calf_raise']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 3, 'skill_assessments': 2, 'level_transition_rules': 2}`

### mma_beginner_generalist

- sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 3, 'level_transition_rules': 2}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 4, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 2}`
- top progressions: `['mma_teach_snc_beginner', 'mma_teach_global_beginner', 'mma_teach_wrestling_beginner', 'mma_teach_ground_control_beginner']`
- top assessments: `['mma_assess_wrestling_cage', 'mma_assess_top_position_effectiveness', 'mma_assess_stance_guard_balance']`
- top transition rules: `['mma_grappling_beginner_to_intermediate', 'mma_beginner_to_intermediate']`
- compact primary exercises: `['mob_drill_dead_bug', 'ex_landmine_squat', 'ex_dumbbell_floor_press', 'ex_side_lying_dumbbell_external_rotation', 'ex_leg_press']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### wrestling_beginner_freestyle

- sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 3, 'level_transition_rules': 3}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 0, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 4, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 3}`
- top progressions: `['wrestling_teach_top_control_beginner', 'wrestling_teach_snc_beginner', 'wrestling_teach_global_beginner', 'wrestling_teach_bottom_escape_beginner']`
- top assessments: `['wrestling_assess_top_bottom_control', 'wrestling_assess_snc_load_readiness', 'wrestling_assess_domain_readiness']`
- top transition rules: `['wrestling_top_bottom_beginner_to_intermediate', 'wrestling_beginner_to_intermediate', 'wrestling_transition_beginner_to_intermediate']`
- compact primary exercises: `['mob_drill_dead_bug', 'mob_drill_bird_dog', 'ex_kettlebell_deadlift', 'ex_box_squat', 'ex_landmine_squat']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### running_beginner_5k

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 2}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 2}`
- top progressions: `['running_teach_running_strength_conditioning_beginner', 'running_teach_run_walk_foundation_beginner', 'running_teach_return_to_run_beginner', 'running_teach_race_specificity_beginner', 'running_teach_long_run_beginner']`
- top assessments: `['running_assess_running_strength_conditioning', 'running_assess_run_walk_foundation', 'running_assess_return_to_run']`
- top transition rules: `['running_hold_or_regress', 'running_beginner_to_intermediate']`
- compact primary exercises: `['mob_drill_dead_bug', 'mob_drill_bird_dog', 'mob_drill_band_pull_apart', 'mob_drill_glute_bridge', 'ex_standing_calf_raise']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### badminton_intermediate_doubles

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 2}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 2}`
- top progressions: `['badminton_teach_clear_drop_smash_intermediate', 'badminton_deep_teach_stroke_mechanics_deep_intermediate_stroke_implication_track_stroke_volume', 'badminton_deep_teach_stroke_mechanics_deep_intermediate_stroke_implication_include_prehab_support', 'badminton_deep_teach_stroke_mechanics_deep_intermediate_badminton_model_smash', 'badminton_deep_teach_stroke_mechanics_deep_intermediate_badminton_model_racket_preparation']`
- top assessments: `['badminton_assess_drive_lift_block_net', 'badminton_assess_doubles_tactics', 'badminton_assess_clear_drop_smash']`
- top transition rules: `['badminton_intermediate_to_advanced', 'badminton_hold_or_regress']`
- compact primary exercises: `['ex_single_leg_leg_press', 'ex_forward_lunge', 'ex_dumbbell_floor_press', 'ex_safety_bar_squat', 'ex_half_kneeling_landmine_press']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### tennis_intermediate_all_court

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 2}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 2}`
- top progressions: `['tennis_teach_volley_net_play_intermediate', 'tennis_teach_forehand_backhand_intermediate', 'tennis_deep_teach_stroke_mechanics_deep_intermediate_ti_volley_transition_sequence', 'tennis_deep_teach_stroke_mechanics_deep_intermediate_ti_serve_volume_gate', 'tennis_deep_teach_stroke_mechanics_deep_intermediate_ti_overhead_tracking_first']`
- top assessments: `['tennis_assess_volley_net_play', 'tennis_assess_singles_tactics', 'tennis_assess_forehand_backhand']`
- top transition rules: `['tennis_intermediate_to_advanced', 'tennis_hold_or_regress']`
- compact primary exercises: `['ex_single_leg_leg_press', 'ex_landmine_squat', 'ex_dumbbell_floor_press', 'ex_safety_bar_squat', 'ex_half_kneeling_landmine_press']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### swimming_beginner_fitness

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 2}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 6, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 2}`
- top progressions: `['swimming_teach_water_confidence_safety_beginner', 'swimming_teach_swimming_strength_conditioning_beginner', 'swimming_teach_starts_turns_underwaters_beginner', 'swimming_teach_open_water_triathlon_beginner', 'swimming_teach_injury_load_management_beginner']`
- top assessments: `['swimming_assess_water_confidence_safety', 'swimming_deep_assess_beginner_safety_learn_to_swim', 'swimming_deep_assess_level_teaching_progression_and_assessment']`
- top transition rules: `['swimming_hold_or_regress', 'swimming_beginner_to_intermediate']`
- compact primary exercises: `['mob_drill_dead_bug', 'mob_drill_glute_bridge', 'ex_suspension_trainer_row', 'ex_leg_press', 'ex_dumbbell_floor_press']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### cycling_beginner_fitness

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 2}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 7, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 2}`
- top progressions: `['cycling_teach_level_progression_beginner', 'cycling_teach_endurance_power_programming_beginner', 'cycling_teach_beginner_confidence_safety_beginner', 'cycling_teach_injury_snc_bike_fit_load_beginner', 'cycling_teach_track_bmx_power_beginner']`
- top assessments: `['cycling_deep_assess_beginner_fitness_commuter_cycling', 'cycling_assess_level_progression', 'cycling_assess_endurance_power_programming']`
- top transition rules: `['cycling_beginner_to_intermediate', 'cycling_hold_or_regress']`
- compact primary exercises: `['mob_drill_dead_bug', 'mob_drill_bird_dog', 'mob_drill_band_pull_apart', 'ex_bear_hug_carry', 'ex_kettlebell_deadlift']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

### hybrid_cricket_basketball_intermediate

- sport teaching counts: `{'teaching_progressions': 6, 'skill_assessments': 3, 'level_transition_rules': 2}`
- generation counts: `{'allowed_primary_exercises': 15, 'allowed_variations': 0, 'progression_paths': 6, 'recent_training_history': 0, 'exercise_candidates': 15, 'programming_rules': 6, 'technical_models': 14, 'technical_errors': 10, 'mobility_drills': 10, 'recovery_rules': 8, 'nutrition_principles': 8, 'sport_teaching_progressions': 6, 'sport_skill_assessments': 3, 'sport_level_transition_rules': 2}`
- top progressions: `['cricket_teach_cricket_snc_intermediate', 'basketball_teach_transition_intermediate', 'basketball_teach_shooting_intermediate', 'basketball_teach_rebounding_intermediate', 'basketball_teach_finishing_intermediate']`
- top assessments: `['basketball_assess_rebounding', 'basketball_assess_finishing', 'cricket_assess_match_iq_level']`
- top transition rules: `['basketball_intermediate_to_advanced', 'cricket_level_intermediate_to_advanced_general']`
- compact primary exercises: `['mob_drill_bird_dog', 'mob_drill_dead_bug', 'ex_cable_hip_adduction', 'ex_trap_bar_deadlift', 'ex_sumo_deadlift']`
- compact variations: `[]`
- compact sport teaching counts: `{'teaching_progressions': 4, 'skill_assessments': 2, 'level_transition_rules': 2}`

## Macro Plan Smoke Test

- template: `template_return_to_training_8w` / `Return To Training 8 Weeks`
- duration weeks: `8`
- sports: `['basketball', 'cricket']`
- phases: `3`
- planning rules: `16`
- competition week rules: `3`
- assumptions: `['No competition calendar supplied, so competition-week rules remain available but inactive.', 'No target date supplied, so the macro plan uses the selected template length.']`

## Read

- All retrieval test profiles should return sport teaching progressions, assessments, and transition rules.
- Football is stored as `soccer` internally and retrieved through the football alias.
- The compact context intentionally shows only selected IDs/names. Full descriptions are hydrated from Mongo later.
