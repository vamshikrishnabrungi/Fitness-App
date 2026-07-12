# Cricket Research Draft Summary

This file is generated from the structured cricket research drafts. It is a review index, not the final sport database.

Draft files: 6

## Total Counts

- key_concepts: 94
- technical_models: 84
- tactical_rules: 151
- physical_demands: 55
- injury_or_load_risks: 60
- training_implications: 68
- backend_records_to_create: 57

## batting_skill_tactics

- File: `drafts/batting_skill_tactics_draft.json`
- Summary: Cricket batting is a perception-action skill built around a stable but adaptable setup, early ball information, decisive footwork, controlled bat-path, and tactical risk management by format and innings phase. Technique should not be reduced to one ideal stance or backlift: elite and developing batters use different guards, stance alignments, trigger movements, and backlift shapes, but reliable models keep the head and eyes level, movement completed before ball release, weight available to go forward or back, and shot selection matched to line, length, pace, spin, field, score, and personal strengths. Against pace, the batter manages time pressure, late movement, bounce, and ball age; against spin, the batter manages length conversion, release-reading, use of crease, sweep options, and strike rotation. Physical support is most relevant when it preserves batting skill under fatigue: acceleration between wickets, repeated deceleration and turning, lower-body power, trunk control, rotational power, shoulder/wrist robustness, and mobility for low or extended positions.
- Source domains: www.lords.org (3), pmc.ncbi.nlm.nih.gov (3), pubmed.ncbi.nlm.nih.gov (3), play.cricket.com.au (2), www.cricketnamibia.com (2), doi.org (2), www.jssm.org (2), www.icc-cricket.com (1), play.nzc.nz (1), cricketnamibia.com (1), journals.plos.org (1), repository.lboro.ac.uk (1)
- key_concepts: 18
- technical_models: 20
- tactical_rules: 22
- physical_demands: 8
- injury_or_load_risks: 8
- training_implications: 10
- backend_records_to_create: 10

### Notable Items

**Key Concepts**
- batting_setup_stability
- stance_variants
- guard_and_alignment
- grip_as_control_interface
- backlift_variability
- trigger_movement
- ... 12 more

**Technical Models**
- batting_action_phase_model
- stable_setup_model
- stance_alignment_model
- grip_face_control_model
- backlift_path_model
- trigger_movement_model
- ... 14 more

**Tactical Rules**
- new_ball_red_ball_rule
- play_swing_late_rule
- leave_width_rule
- seam_variable_bounce_rule
- short_ball_selectivity_rule
- pace_trigger_rule
- ... 16 more

**Physical Demands**
- perception_reaction_speed
- acceleration_between_wickets
- deceleration_and_turning
- lower_body_power
- rotational_power_and_sequencing
- trunk_stiffness_and_control
- ... 2 more

**Injury Or Load Risks**
- hamstring_running_risk
- calf_achilles_risk
- adductor_groin_risk
- lumbar_hip_rotation_risk
- upper_limb_impact_risk
- head_neck_ball_impact_risk
- ... 2 more

**Training Implications**
- batters_need_role_specific_training
- representative_practice
- technical_blocking_then_variability
- pace_preparation
- spin_preparation
- scenario_based_tactical_iq
- ... 4 more

**Backend Records To Create**
- batting_shot_families
- batting_action_phase_model
- batting_order_roles
- batting_against_pace
- batting_against_spin
- batting_phase_models
- ... 4 more


## conditions_match_iq

- File: `drafts/conditions_match_iq_draft.json`
- Summary: Cricket conditions IQ is the ability to link pitch surface, weather, ball age, format, innings phase, and match state into practical batting, bowling, fielding, toss, and workload decisions. The strongest evidence comes from laws and playing conditions for what is permitted, turf preparation guidance for how moisture, grass, compaction, and wear affect the surface, and aerodynamics research for swing and reverse swing mechanisms. Tactical claims about green pitches, dry turners, dew, chasing, overcast skies, and humidity should be stored with evidence labels because some are robust coaching principles while others are venue-dependent or partly tradition. The backend should treat conditions as a live state that is revised after the toss, first spells, ball behavior, outfield speed, dew onset, rain risk, and innings phase rather than as a fixed pre-match label.
- Source domains: www.lords.org (7), www.icc-cricket.com (4), www.ecb.co.uk (1), resources.ecb.co.uk (1), www.nzc.nz (1), www.sportsturfwa.asn.au (1), www.cambridge.org (1), torroja.dmt.upm.es (1), www.sciencedirect.com (1), www.abc.net.au (1), ar5iv.labs.arxiv.org (1), www.sfu.ca (1), doi.org (1), www.cricket.com.au (1), www.espncricinfo.com (1)
- key_concepts: 27
- technical_models: 10
- tactical_rules: 78
- physical_demands: 10
- injury_or_load_risks: 12
- training_implications: 14
- backend_records_to_create: 10

### Notable Items

**Key Concepts**
- condition_reading_before_strategy
- green_pitch
- dry_pitch
- hard_bouncy_pitch
- slow_low_pitch
- turning_pitch
- ... 21 more

**Technical Models**
- pitch_surface_state_model
- pitch_lifecycle_model
- ball_aerodynamics_model
- ball_age_phase_model
- weather_confidence_model
- dew_effect_model
- ... 4 more

**Tactical Rules**
- conditions_rule_001
- conditions_rule_002
- conditions_rule_003
- conditions_rule_004
- conditions_rule_005
- conditions_rule_006
- ... 72 more

**Physical Demands**
- heat_tolerance
- wet_ball_grip_strength
- footing_and_deceleration
- fast_bowling_repeat_power
- spin_finger_and_wrist_capacity
- batting_reaction_and_balance
- ... 4 more

**Injury Or Load Risks**
- fast_bowling_heat_fatigue
- wet_runup_slip
- wet_turning_between_wickets
- throwing_with_wet_ball
- hard_pitch_short_ball_load
- spinner_finger_overload
- ... 6 more

**Training Implications**
- condition_scenario_nets
- live_read_checklist
- new_ball_batting_block
- slow_pitch_batting_block
- turning_pitch_methods
- wet_ball_bowling
- ... 8 more

**Backend Records To Create**
- pitch_type_profiles
- ball_age_and_condition_tracker
- cricket_weather_context
- conditional_toss_decision
- format_phase_condition_rules
- rain_interruption_decision_support
- ... 4 more


## cricket_snc_injury_macro_planning

- File: `drafts/cricket_snc_injury_macro_planning_draft.json`
- Summary: Cricket S&C planning should be role-led, phase-led, and workload-aware. The same athlete may accumulate sprinting, repeated accelerations, rotational hitting, bowling, throwing, crouching, diving, and long-duration field exposure in one week, so the backend should treat cricket as a combined skill-load and physical-load system rather than a generic gym plan. Fast bowlers need the strongest workload guardrails because lumbar bone stress injury risk is shaped by age, maturation, bowling volume, recent spikes, technique, trunk mechanics, and prior back symptoms. All players need a fielding and throwing durability layer; batters need repeat sprint and rotational power support; spinners need shoulder, trunk, forearm, wrist, and finger capacity; wicketkeepers need hip, ankle, adductor, quad, trunk, hand, and reaction capacity; all-rounders need conflict management because their total cricket load can exceed the load of specialist roles. Off-season should rebuild strength, tissue capacity, sprint mechanics, mobility, and broad athletic qualities while skill volume is lower. Pre-season should progressively reintroduce bowling, throwing, sprinting, and match-simulation density. In-season should maintain strength and power, preserve high-speed exposure, monitor bowling and throwing load, and trim gym stress around heavy match or bowling weeks. Return-to-bowling should be staged, symptom-led, and clinician-supervised after lumbar, shoulder, side strain, hamstring, adductor, wrist, or finger injury. Useful testing should combine objective outputs, movement capacity, role-specific skill load, and athlete-state trends instead of relying on single population benchmarks.
- Source domains: pubmed.ncbi.nlm.nih.gov (5), pmc.ncbi.nlm.nih.gov (4), bjsm.bmj.com (2), play.cricket.com.au (1), resources.ecb.co.uk (1), journals.sagepub.com (1), journals.lww.com (1), www.jassm.org (1), repository.lboro.ac.uk (1), strengthandconditioning.org (1), commons.nmu.edu (1), salford-repository.worktribe.com (1), pureportal.coventry.ac.uk (1), journals.plos.org (1), www.intechopen.com (1)
- key_concepts: 10
- technical_models: 8
- tactical_rules: 9
- physical_demands: 12
- injury_or_load_risks: 14
- training_implications: 14
- backend_records_to_create: 8

### Notable Items

**Key Concepts**
- Role-first planning
- Skill load is training load
- Bowling load spikes matter
- Youth progression is maturation-sensitive
- Throwing is separate from bowling
- Every role needs a fielding layer
- ... 4 more

**Technical Models**
- Role-phase-load model
- Season macrocycle model
- One-match-week microcycle model
- Fast bowling workload model
- Fast bowler lumbar bone stress risk model
- Throwing kinetic-chain model
- ... 2 more

**Tactical Rules**
- cricket_rule_fast_bowler_back_pain_stop
- cricket_rule_youth_ca_135_246
- cricket_rule_ecb_recreational_spell_rest
- cricket_rule_workload_spike_adjustment
- cricket_rule_match_week_taper
- cricket_rule_throwing_load_progression
- ... 3 more

**Physical Demands**
- cricket_demand_batter_foundation
- cricket_demand_power_batter_t20_finisher
- cricket_demand_fast_bowler
- cricket_demand_fast_bowler_youth
- cricket_demand_spinner
- cricket_demand_all_rounder
- ... 6 more

**Injury Or Load Risks**
- cricket_risk_fast_bowler_lumbar_bone_stress
- cricket_risk_fast_bowling_technique_load
- cricket_risk_workload_delayed_response
- cricket_risk_underprepared_bowler
- cricket_risk_throwing_shoulder_elbow
- cricket_risk_side_strain
- ... 8 more

**Training Implications**
- cricket_training_off_season
- cricket_training_pre_season_bowling_ramp
- cricket_training_in_season_maintenance
- cricket_training_post_match_recovery
- cricket_training_fast_bowler_strength
- cricket_training_batter_power_speed
- ... 8 more

**Backend Records To Create**
- {"record_family": "sport_position_profiles", "record_ids": ["cricket_role_batter_physical_profile", "cricket_role_fast_bowler_physical_profi
- {"record_family": "sport_workload_rules", "record_ids": ["cricket_workload_fast_bowling_youth_ca_limits", "cricket_workload_fast_bowling_ecb
- {"record_family": "sport_workload_rules", "record_ids": ["cricket_workload_throwing_progression", "cricket_workload_wicketkeeper_crouch_expo
- {"record_family": "sport_injury_risks", "record_ids": ["cricket_injury_lumbar_bone_stress_fast_bowler", "cricket_injury_side_strain", "crick
- {"record_family": "sport_season_models", "record_ids": ["cricket_season_off_pre_in_transition_model", "cricket_tournament_compressed_schedul
- {"record_family": "sport_match_week_rules", "record_ids": ["cricket_match_week_one_match_template", "cricket_match_week_two_match_template",
- ... 2 more


## fielding_throwing_wicketkeeping

- File: `drafts/fielding_throwing_wicketkeeping_draft.json`
- Summary: Cricket fielding is a mixed technical, tactical, and physical domain built around preventing runs, creating dismissals, and protecting the shoulder, elbow, knee, hip, and back across repeated high-intensity actions. The useful backend model should split the domain into catching, ground fielding, throwing, diving/sliding, relay play, and wicketkeeping. Fielders need a ready position, early ball reading, efficient approach angle, clean pickup, and throw selection under time pressure. Throwing performance depends on whole-body sequencing, momentum into release, shoulder and trunk capacity, technique stability, and a speed-accuracy tradeoff. Throwing workload should be monitored because high weekly throw counts and short recovery windows have been associated with injury risk in elite cricketers. Wicketkeeping is a distinct role: the player is involved nearly every delivery, repeatedly moves from squat or semi-squat positions, must adapt standing back versus standing up, and requires lateral footwork, glove path control, leg-side take skill, stumping mechanics, hip/ankle mobility, trunk endurance, quad/adductor capacity, reaction speed, and shoulder/forearm durability.
- Source domains: www.lords.org (6), pubmed.ncbi.nlm.nih.gov (4), www.researchgate.net (3), doi.org (2), pmc.ncbi.nlm.nih.gov (2), strengthandconditioning.org (1), www.tandfonline.com (1), ro.ecu.edu.au (1), play.nzc.nz (1)
- key_concepts: 14
- technical_models: 18
- tactical_rules: 10
- physical_demands: 8
- injury_or_load_risks: 8
- training_implications: 10
- backend_records_to_create: 5

### Notable Items

**Key Concepts**
- fielding_primary_objectives
- position_families
- ready_position
- catching_families
- approach_angle
- pickup_options
- ... 8 more

**Technical Models**
- catching_tracking_model
- close_catching_model
- slip_catching_model
- high_catch_model
- boundary_catch_model
- ground_fielding_approach_model
- ... 12 more

**Tactical Rules**
- law_catch_completion
- law_boundary_catch_awareness
- law_run_out_execution
- law_stumping_execution
- law_keeper_position_constraints
- close_fielding_attack_rule
- ... 4 more

**Physical Demands**
- mixed_intensity_profile
- acceleration_0_to_20m
- change_of_direction_deceleration
- upper_body_throw_power
- trunk_rotation_and_stiffness
- hip_ankle_adductor_capacity
- ... 2 more

**Injury Or Load Risks**
- high_throw_count_risk
- shoulder_deceleration_risk
- elbow_forearm_risk
- finger_hand_impact_risk
- sprint_deceleration_soft_tissue_risk
- dive_slide_collision_risk
- ... 2 more

**Training Implications**
- integrated_skill_snc
- fielding_assessment_battery
- throwing_progression
- target_accuracy_under_pressure
- shoulder_preparation
- outfielder_training
- ... 4 more

**Backend Records To Create**
- cricket_skill_fielding_ground_fielding
- cricket_skill_throwing_overarm_sidearm_underarm
- cricket_workload_throwing_volume_spike
- cricket_role_wicketkeeper
- cricket_injury_rule_fielding_shoulder_knee_hand


## pace_bowling_skill_workload

- File: `drafts/pace_bowling_skill_workload_draft.json`
- Summary: Pace bowling is a high-force, high-skill role that combines run-up rhythm, delivery-stride mechanics, wrist and seam control, tactical deception, and carefully managed workload. The useful backend model should treat pace bowling as repeated sprint-plus-throw exposures with large lower-limb, trunk, shoulder, and lumbar stress. Technical coaching should preserve individual action style while improving repeatable momentum transfer, alignment, release control, and deceleration. Tactical advice should adapt to ball age, pitch, batter handedness, scoring phase, field support, and legal constraints. Workload rules should be conservative for youth bowlers, avoid sudden spikes after layoffs, track match and training balls separately, and reduce heavy gym stress around high bowling load.
- Source domains: resources.ecb.co.uk (3), pubmed.ncbi.nlm.nih.gov (3), www.mdpi.com (2), pmc.ncbi.nlm.nih.gov (2), play.cricket.com.au (1), www.lords.org (1), www.icc-cricket.com (1), doi.org (1), www.cambridge.org (1), people.stfx.ca (1), bjsm.bmj.com (1), peterbrukner.com (1), journals.lww.com (1), repository.usfca.edu (1)
- key_concepts: 15
- technical_models: 18
- tactical_rules: 20
- physical_demands: 9
- injury_or_load_risks: 12
- training_implications: 12
- backend_records_to_create: 14

### Notable Items

**Key Concepts**
- pace_bowling_integrated_model
- delivery_chain_phases
- individual_action_tolerance
- momentum_transfer
- accuracy_as_capacity
- front_foot_contact_load
- ... 9 more

**Technical Models**
- run_up_rhythm_model
- run_up_speed_control
- gather_bound_direction
- back_foot_contact_alignment
- back_foot_contact_action_type
- front_foot_contact_bracing
- ... 12 more

**Tactical Rules**
- new_ball_attack_top_off
- outswing_to_same_side_batter
- inswing_stumps_pads_plan
- green_or_damp_pitch
- hard_bouncy_pitch
- slow_low_pitch
- ... 14 more

**Physical Demands**
- run_up_acceleration_capacity
- front_leg_braking_strength
- lower_body_power
- trunk_strength_and_control
- hip_thoracic_mobility
- shoulder_scapular_capacity
- ... 3 more

**Injury Or Load Risks**
- lumbar_bone_stress_youth
- workload_spike
- too_little_chronic_load
- consecutive_days_youth
- growth_spurt_load_mismatch
- mixed_action_counter_rotation
- ... 6 more

**Training Implications**
- track_total_bowling_load
- apply_ca_youth_guidelines
- apply_ecb_youth_limits
- preseason_build_up
- planned_bowling_breaks
- adult_workload_spike_guardrail
- ... 6 more

**Backend Records To Create**
- cricket_role_pace_bowler
- cricket_skill_pace_bowling_delivery_chain
- cricket_skill_pace_bowling_swing_seam_variations
- cricket_tactical_pace_new_ball_top_off
- cricket_tactical_pace_death_bowling_options
- cricket_condition_pace_pitch_ball_age
- ... 8 more


## spin_bowling_skill_tactics

- File: `drafts/spin_bowling_skill_tactics_draft.json`
- Summary: Spin bowling is a deception skill built around repeatable release, control of spin axis and revolutions, pace and flight changes, use of crease, field-setting pressure, and reading batter intent. The backend should not treat all spinners as one role: finger spin, wrist spin, left-arm orthodox, and left-arm wrist spin have different release mechanics, accuracy profiles, variation menus, physical demands, and injury risks. Spin plans should connect technical development with tactical context: pitch wear, rough, ball age, batter handedness, match format, scoring pressure, and field protection. S&C support should emphasize shoulder and hip rotational capacity, trunk control, forearm/wrist/finger capacity, repeated low-to-moderate intensity bowling volume, and safe workload progression rather than fast-bowler sprint/run-up loading.
- Source domains: pmc.ncbi.nlm.nih.gov (4), www.lords.org (3), pubmed.ncbi.nlm.nih.gov (2), drpaulfelton.com (2), www.icc-cricket.com (1)
- key_concepts: 10
- technical_models: 10
- tactical_rules: 12
- physical_demands: 8
- injury_or_load_risks: 6
- training_implications: 8
- backend_records_to_create: 10

### Notable Items

**Key Concepts**
- spin_family_classification
- stock_ball_priority
- spin_axis_controls_deception
- flight_is_not_slow_bowling
- pace_variation_must_preserve_action
- crease_use_changes_angles
- ... 4 more

**Technical Models**
- spin_bowling_phase_model
- finger_spin_release_model
- wrist_spin_release_model
- stock_ball_control_model
- drift_dip_turn_model
- pace_flight_loop_model
- ... 4 more

**Tactical Rules**
- right_hand_off_spin_default
- off_spin_to_left_hander_angle
- leg_spin_attacking_line
- left_arm_orthodox_right_hander
- rough_attack_rule
- flat_pitch_control_rule
- ... 6 more

**Physical Demands**
- shoulder_external_rotation_tolerance
- hip_shoulder_separation
- trunk_rotation_control
- forearm_wrist_finger_capacity
- single_leg_balance_and_landing_control
- aerobic_repeatability
- ... 2 more

**Injury Or Load Risks**
- spinner_shoulder_overload
- wrist_finger_irritation
- low_back_rotation_load
- elbow_legality_or_pain_flag
- variation_spike_risk
- fielding_throwing_double_load

**Training Implications**
- spinner_program_differs_from_pace_bowler
- stock_ball_before_variations
- match_format_affects_training
- surface_context_changes_drills
- shoulder_monitoring_for_spinners
- gym_power_needs_transfer_constraint
- ... 2 more

**Backend Records To Create**
- spin_bowling_families
- cricket_role_spinner
- spin_bowling_phase_model
- spin_release_axis_model
- spin_matchup_rules_by_handedness
- spin_pitch_condition_rules
- ... 4 more
