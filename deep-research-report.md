# SFTC Sports Performance Knowledge Architecture

## Master schema and system architecture

SFTC should be built as a linked evidence graph, not a flat workout library. The highest-confidence universal domains that recur across modern resistance-training guidance, athlete-load consensus, sports nutrition guidance, REDs guidance, and long-term athletic development are: athlete context, sport demands, exercise metadata, training-variable logic, readiness/recovery rules, skills, tests, injury flags, and source traceability. That is the minimum architecture required for an AI coach to answer, with auditability, *what the athlete needs, why, how to train it, and how to adjust it safely*. citeturn8view6turn0search0turn0search1turn0search2turn22search2turn14search0

The canonical storage model should separate **content objects** from **decision rules** and **source records**. Engineers should treat every recommendation as a composition of: a profile object, one or more constraint objects, one or more rule objects, and one or more sources. That keeps generation explainable, allows coach overrides, and makes validation workflows possible. The foundational source stack should heavily weight pronouncements and consensus from entity["organization","American College of Sports Medicine","exercise medicine society"], entity["organization","National Strength and Conditioning Association","strength coaching association"], entity["organization","International Olympic Committee","olympic governing body"], entity["organization","FIFA","football governing body"], entity["organization","International Cricket Council","cricket governing body"], entity["organization","World Athletics","athletics governing body"], entity["organization","International Tennis Federation","tennis governing body"], entity["organization","Badminton World Federation","badminton governing body"], entity["organization","World Aquatics","aquatics governing body"], entity["organization","UEFA","european football governing body"], and entity["organization","National Athletic Trainers' Association","athletic trainers association"]. citeturn15search2turn24view2turn2search5turn8view5turn8view7turn26view0turn19search10

### Canonical output files

| File | Primary object | Required use in SFTC |
|---|---|---|
| `/sports/sport_profiles.jsonl` | One sport profile per sport/discipline | Plan generation, coach dashboard, user insights |
| `/sports/sport_demands.csv` | Flattened demand attributes | Filtering, similarity search, analytics |
| `/sports/sport_training_rules.jsonl` | Sport-specific AI decisions | Workout adaptation, calendar logic |
| `/exercises/exercise_library.jsonl` | Exercise objects | Session generation, substitutions, coach edits |
| `/exercises/movement_patterns.jsonl` | Movement pattern ontology | Skill/exercise mapping, injury-safe alternatives |
| `/training/physical_qualities.jsonl` | Quality taxonomy and programming defaults | Progression engine, testing engine |
| `/training/programming_rules.jsonl` | Sets/reps/RPE/order/deload rules | Session builder and mesocycle planner |
| `/running/running_workouts.jsonl` | Running workout types | GPS plan builder |
| `/running/running_plan_rules.jsonl` | Running-generation logic | Mileage progression, heat/hydration adjustments |
| `/nutrition/nutrition_guidelines.jsonl` | Macro/micro/hydration guidance | Meal guidance and body-composition logic |
| `/recovery/readiness_rules.jsonl` | Readiness and recovery rules | Load adjustments and recovery-only recommendations |
| `/skills/sport_skills.jsonl` | Learn-your-sport modules | Skill learning, video search prompts |
| `/testing/performance_tests.jsonl` | Standardized tests | Benchmarking and retesting schedules |
| `/injury/injury_risk_database.jsonl` | Risk factors and contraindications | Safety routing and regressions |
| `/sources/source_registry.csv` | Source truth table | Audit, explainability, evidence refresh |

### Common record envelope

The most practical production pattern is a **shared envelope** plus domain-specific payloads.

```json
{
  "id": "string",
  "name": "string",
  "category": "string",
  "description": "string",
  "structured_fields": {},
  "tags": [],
  "sport_tags": [],
  "goal_tags": [],
  "contraindications": [],
  "evidence_level": "strong_evidence | moderate_evidence | coaching_consensus | weak_evidence | needs_expert_validation",
  "source_refs": ["SR-001", "SR-002"],
  "sftc_app_usage_profile_id": "UP-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1",
  "last_reviewed_date": "2026-05-13",
  "expert_validation_status": "pending | validated | rejected",
  "version": "v1.0.0"
}
```

### Reusable support profiles

```json
{
  "usage_profiles": [
    {
      "usage_profile_id": "UP-SPORT-DEFAULT",
      "used_for_plan_generation": true,
      "used_for_workout_generation": true,
      "used_for_recovery_adjustment": true,
      "used_for_nutrition_recommendation": true,
      "used_for_skill_learning": true,
      "used_for_coach_dashboard": true,
      "used_for_user_insights": true,
      "used_for_progress_tracking": true
    },
    {
      "usage_profile_id": "UP-EXERCISE-DEFAULT",
      "used_for_plan_generation": true,
      "used_for_workout_generation": true,
      "used_for_recovery_adjustment": true,
      "used_for_nutrition_recommendation": false,
      "used_for_skill_learning": false,
      "used_for_coach_dashboard": true,
      "used_for_user_insights": true,
      "used_for_progress_tracking": true
    }
  ],
  "personalization_profiles": [
    {
      "personalization_profile_id": "PP-ATHLETE-CORE-v1",
      "inputs": [
        "sport",
        "goal",
        "experience_level",
        "age_range",
        "sex_if_relevant",
        "body_weight_if_relevant",
        "training_days",
        "equipment",
        "injury_history",
        "readiness_score",
        "sleep",
        "soreness",
        "recent_training_load"
      ]
    }
  ]
}
```

### Starter programming rules matrix

The strongest universal resistance-training defaults should be stored at the **quality-family** level and inherited downward, with sport-specific overrides layered on top. ACSM’s 2026 umbrella review and 2009 position stand remain the best universal starting points for set/rep/rest defaults. citeturn7view18turn0search0turn8view6

| Quality family | Typical loading emphasis | Starter prescription storage fields |
|---|---|---|
| Max strength | High load, low reps, long rest | `rep_range`, `intensity_pct_1rm`, `rest_seconds`, `velocity_loss_cap` |
| Hypertrophy | Moderate load, moderate reps, moderate rest | `weekly_sets_per_muscle_group`, `rir_target`, `exercise_variation_rotation` |
| Power | Low-moderate load or ballistic intent, low reps, long rest | `ballistic_flag`, `intent=maximal_velocity`, `ground_contact_limits` |
| Muscular endurance | Lower load, higher reps or timed sets | `density_target`, `rest_ratio`, `fatigue_tolerance_flag` |
| Speed / acceleration | Max intent, very low reps, full recovery | `distance_band`, `rep_count`, `min_rest_ratio`, `readiness_gate` |
| Aerobic base | Low intensity, repeatable volume | `zone_target`, `session_duration_range`, `weekly_frequency`, `easy_hard_distribution` |

### Readiness and recovery adjustment defaults

SFTC should treat sleep, subjective state, load history, and injury flags as **decision inputs**, not passive dashboard data. Sleep restriction reduces performance and recovery quality; HRV can be useful for context but should not be run as a solitary “go/no-go” switch; the IOC load consensus supports monitoring training, competition, and wellbeing together; and menstrual tracking should prioritize symptoms and individual response rather than rigid cycle-synced prescriptions because the performance literature is mixed. citeturn12search11turn12search2turn0search1turn1search2turn1search10turn24view7

| Readiness factor | Meaning | Default SFTC adjustment |
|---|---|---|
| Sleep duration/quality | Recovery, cognitive function, mood, reaction time | Reduce intensity first; if very poor plus high soreness, reduce volume too |
| HRV and resting HR | Autonomic strain / adaptation context | Use as secondary modifier; never alone |
| Soreness by region | Tissue-specific tolerance | Avoid heavy loading of sore region; substitute alternate patterns |
| Mood / stress | Global allostatic load | Downgrade high-CNS work if stress is high |
| Previous workout intensity | Residual fatigue | Avoid stacking maximal lower body, sprint, or contact stress |
| Acute load spike | Short-term load shock | Warn user; prefer slower ramping |
| Injury flag | Mechanical risk / pain aggravation | Remove aggravating pattern, route to regression, recommend medical evaluation when indicated |
| Menstrual symptoms if user opts in | Individual symptom burden | Modify using symptoms, not generic phase assumptions |
| Travel / heat / hydration | Environmental stress | Reduce pace targets, lengthen rest, increase hydration prompts |

## Universal ontologies and taxonomies

The ontology needs to be broad enough for general fitness, but precise enough for sport transfer. That means movement patterns, physical qualities, and exercise metadata must all be queryable independently and also cross-linked. This approach is consistent with LTAD, youth resistance-training guidance, and modern resistance-training synthesis that emphasize physical literacy, foundational strength, and targeted manipulation of variables rather than one-size-fits-all exercise lists. citeturn14search0turn24view2turn14search9turn8view6

### Full sport taxonomy

| Category | Sports / goal domains |
|---|---|
| Combat sports | Boxing, MMA, wrestling, Brazilian jiu-jitsu, Muay Thai, kickboxing, judo, karate, taekwondo |
| Team field/court sports | Football/soccer, basketball, cricket, hockey, rugby, American football, volleyball, handball |
| Racket sports | Tennis, badminton, squash, table tennis |
| Endurance sports | Running, cycling, swimming, triathlon, rowing |
| Strength/power sports | Powerlifting, Olympic weightlifting, strongman, throws, sprinting, jumping |
| Skill/aesthetic/bodyweight sports | Calisthenics, gymnastics, parkour, climbing, dance |
| General fitness goals | Fat loss, muscle gain, strength, athletic physique, mobility, conditioning, longevity, return to fitness, beginner fitness |

### Movement pattern taxonomy

| Pattern | Core tags for storage | Typical sport transfer |
|---|---|---|
| Squat | bilateral, knee-dominant, vertical-force | jumping, deceleration, positional strength |
| Hinge | bilateral/unilateral, hip-dominant | sprinting, striking, lifting, posterior-chain robustness |
| Lunge | split stance, unilateral, frontal/sagittal | COD, badminton, fencing-like positions, field sports |
| Push | horizontal/vertical | combat sports, court sports, general fitness |
| Pull | horizontal/vertical | climbing, grappling, posture, shoulder balance |
| Carry | bilateral/unilateral, gait-loaded | trunk stiffness, grip, combat/contact robustness |
| Rotation | transverse force production | boxing, cricket, tennis, golf-like transfer |
| Anti-rotation | trunk control | change of direction, combat stabilization |
| Sprint | acceleration or max-velocity | team sports, sprinting, field coverage |
| Jump | bilateral/unilateral, vertical/horizontal | basketball, volleyball, badminton, jumping events |
| Throw | overhead/chest/rotational | cricket, basketball, handball, throws |
| Brace | trunk stiffness / pressure management | heavy lifting, collision tolerance |
| Crawl | quadrupedal locomotion | rehab, conditioning, shoulder integration |
| Change of direction | cut, shuffle, crossover | all field and racket sports |
| Deceleration | braking, force absorption | soccer, basketball, tennis, badminton |
| Landing | bilateral/unilateral | jumping sports, injury reduction |
| Striking | punch, kick, implement strike | boxing, kick sports, cricket batting |
| Grappling | clinch, pull, resist, twist | wrestling, BJJ, judo |
| Locomotion | run, jog, swim, cycle, skip | endurance and conditioning engines |

### Physical quality taxonomy

| Group | Qualities |
|---|---|
| Force production | Max strength, hypertrophy, explosive power, rate of force development, grip strength, core stiffness, rotational power |
| Speed and reactivity | Speed, acceleration, max velocity, reaction time |
| Multi-directional movement | Agility, change of direction, balance, coordination |
| Energy systems | Anaerobic power, anaerobic capacity, aerobic base, VO2 max, lactate threshold, muscular endurance |
| Range and control | Mobility, flexibility, stability |
| Context modifiers | Tissue tolerance, fatigue resistance, readiness sensitivity |

### Exercise taxonomy

Every exercise should be indexed across **at least** these dimensions:

| Dimension | Allowed values |
|---|---|
| Modality | bodyweight, free_weight, machine, cable, band, sled, med_ball, plyometric, sprint_drill, mobility, isometric, carry, olympic_derivative, rehab_prehab |
| Pattern | one or more movement patterns from the ontology |
| Force vector | vertical, horizontal, diagonal, rotational |
| Contraction emphasis | concentric, eccentric, isometric, stretch_shortening_cycle |
| Bilaterality | bilateral, unilateral, offset, contralateral |
| Plane bias | sagittal, frontal, transverse, multiplanar |
| Difficulty | beginner, intermediate, advanced |
| Fatigue cost | low, medium, high |
| Joint stress | low, medium, high |
| Placement | warm_up, activation, main_strength, main_power, accessory, conditioning, cooldown |
| Equipment dependency | none, minimal, moderate, specialized |
| Safety routing | standard, technical_supervision_needed, not_for_acute_pain, not_for_novices |

## Source hierarchy and evidence governance

The source hierarchy should be explicit in the database and surfaced to both the coach dashboard and any explanation UI. The governing logic should follow a GRADE-like certainty approach layered on top of an Oxford-style evidence hierarchy, with ACSM-style evidence-based pronouncements at the top of the exercise/training stack. citeturn24view4turn24view3turn15search2

Official evidence portals worth wiring into refresh jobs include urlACSMhttps://acsm.org, urlNSCAhttps://www.nsca.com, urlIOC consensus statementshttps://olympics.com/ioc/documents/athletes/medical-and-scientific-consensus-statements, urlFIFA medical resourceshttps://inside.fifa.com/health-and-medical/injury-prevention, urlICC medical resourceshttps://www.icc-cricket.com/about/cricket/medical, urlWorld Athletics coaching resourceshttps://worldathletics.org, urlITF coaching resourceshttps://www.itftennis.com/en/growing-the-game/coaching/, urlBWFhttps://bwfbadminton.com, and urlWorld Aquaticshttps://www.worldaquatics.com.

### Evidence grading system for SFTC

| SFTC evidence level | Practical definition | Default product behavior |
|---|---|---|
| Strong evidence | Umbrella review, position stand, consensus statement, or consistent systematic review/meta-analysis | May drive default prescriptions |
| Moderate evidence | Consistent cohort/controlled evidence or high-quality narrative review with convergence | May drive prescriptions with conservative caps |
| Coaching consensus | Governing-body manual, technical text, expert consensus without direct intervention proof | Use for cueing and progression; show lower confidence |
| Weak evidence | Small or heterogeneous observational work | Do not auto-prescribe aggressively |
| Needs expert validation | Sparse, conflicting, or highly context-specific evidence | Store, but hide from autonomous recommendation engine until reviewed |

### Seed rows for `/sources/source_registry.csv`

These rows are sufficient to support the architecture, examples, and starter records below.

| ID | Title | Type / year | Rel. | Limitations | Citation |
|---|---|---:|---:|---|---|
| SR-001 | Resistance Training Prescription for Muscle Function, Hypertrophy, and Physical Performance in Healthy Adults | ACSM umbrella review / 2026 | 5 | Healthy adults; not sport-specific rehab | citeturn6search6turn8view6 |
| SR-002 | Progression Models in Resistance Training for Healthy Adults | ACSM position stand / 2009 | 5 | Older but foundational | citeturn0search0 |
| SR-003 | How much is too much? Part 1: IOC consensus on load in sport and risk of injury | IOC consensus / 2016 | 5 | Not a precise threshold model | citeturn0search1 |
| SR-005 | Nutrition and Athletic Performance | Joint position statement / 2016 | 5 | Broad athlete guidance | citeturn0search2 |
| SR-006 | Exercise and Fluid Replacement | ACSM position stand / 2007 | 5 | Foundational but older | citeturn0search3 |
| SR-007 | Sleep and the athlete: narrative review and 2021 expert consensus recommendations | Expert consensus / 2021 | 4 | Narrative synthesis | citeturn12search11 |
| SR-008 | IOC consensus statement on REDs | IOC consensus / 2023 | 5 | Does not replace clinician evaluation | citeturn22search2 |
| SR-009 | UEFA consensus statement on menstrual cycle tracking in women’s football | UEFA consensus / 2025 | 4 | Football-focused implementation guidance | citeturn1search2 |
| SR-010 | Menstrual cycle effects on exercise performance | Systematic review/meta-analysis / 2020 | 4 | Mixed results; high individual variability | citeturn1search10 |
| SR-029 | Training intensity distribution among well-trained and elite endurance athletes | Systematic review / 2015 | 4 | Elite-centric | citeturn6search0 |
| SR-030 | Periodization, methods, intensity distribution, and volume in highly trained and elite distance runners | Systematic review / 2022 | 4 | Highly trained/elite scope | citeturn6search4 |
| SR-031 | Excessive progression in weekly running distance and injury risk | Prospective study / 2014 | 4 | Novice runners only | citeturn18search10 |
| SR-032 | START-TO-RUN distance and running-related injury among obese novice runners | Trial / 2018 | 4 | Obese novice runners only | citeturn18search20 |
| SR-033 | Identifying high-risk running sessions in recreational runners | Prospective cohort / 2025 | 4 | Newer line of research, needs replication | citeturn18search15 |
| SR-034 | Consensus recommendations on training and competing in the heat | Consensus statement / 2015 | 5 | Heat-specific context | citeturn23search2 |
| SR-036 | Exercise-Associated Hyponatremia: 2017 Update | Consensus update / 2017 | 4 | Event-medical focus | citeturn23search12 |
| SR-037 | Heart Rate Variability Applications in Strength and Conditioning | Review / 2024 | 4 | HRV is context-dependent | citeturn12search2 |
| SR-038 | Acute:Chronic Workload Ratio: Conceptual Issues and Fundamental Pitfalls | Methodological commentary / 2020 | 4 | Critique, not a replacement model | citeturn17search3turn24view7 |
| SR-039 | ACWR and injury risk in sport | Systematic review / 2020 | 4 | Heterogeneous methods, not causal proof | citeturn17search8 |
| SR-041 | Warm-up intervention programs to prevent sports injuries | Systematic review/meta-analysis / 2022 | 4 | Programs vary across sports | citeturn12search5 |
| SR-042 | IOC consensus statement on youth athletic development | IOC consensus / 2015 | 5 | Youth-focused broad framework | citeturn14search0 |
| SR-045 | GRADE Working Group overview | Methodology resource / current | 5 | Framework, not sport-specific evidence | citeturn15search0turn24view4 |
| SR-046 | Oxford Centre for Evidence-Based Medicine levels of evidence | Methodology resource / 2009 | 5 | Generic hierarchy | citeturn15search1turn24view3 |
| SR-055 | Yo-Yo IR1 reliability and validity in young soccer players | Validation study / 2014 | 4 | Youth soccer sample | citeturn21search1 |
| SR-065 | Physical Activity Guidelines | Official ACSM resource / current | 4 | General health guidance | citeturn6search13 |

| ID | Title | Type / year | Rel. | Limitations | Citation |
|---|---|---:|---:|---|---|
| SR-011 | Amateur boxing: physical and physiological attributes | Review / 2015 | 4 | Amateur boxing focus | citeturn2search0 |
| SR-012 | Epidemiology of injuries in amateur boxing | Systematic review/meta-analysis / 2022 | 4 | Amateur-only and heterogeneous reporting | citeturn2search8 |
| SR-013 | FIFA 11+ injury prevention program for soccer players | Systematic review / 2017 | 4 | Compliance-dependent | citeturn2search1 |
| SR-015 | Incidence and prevalence of elite male cricket injuries using updated consensus definitions | Epidemiology study / 2016 | 4 | Elite male scope | citeturn3search5 |
| SR-016 | Physical profiling of international cricket players | Cross-sectional study / 2020 | 4 | Descriptive profile, not interventional | citeturn3search6 |
| SR-018 | Measuring Physical Demands in Basketball | Systematic review / 2021 | 4 | Monitoring-method focus | citeturn2search3 |
| SR-019 | Sports Injuries in Basketball Players | Systematic review / 2024 | 4 | Injury definitions vary | citeturn2search11 |
| SR-020 | Physiologic Profile of Basketball Athletes | Review / 2017 | 4 | Applied review, not a consensus statement | citeturn24view0 |
| SR-021 | Systematic review on badminton injuries | Systematic review / 2025 | 4 | Variable bias in included studies | citeturn4search0 |
| SR-022 | Physiological characteristics of badminton match play | Match analysis study / 2007 | 4 | Older methods; level dependent | citeturn9search3 |
| SR-024 | Tennis injuries: occurrence, aetiology, and prevention | Review / 2006 | 4 | Older literature base | citeturn4search1 |
| SR-025 | Intensity of tennis match play | Review / 2006 | 4 | Older synthesis | citeturn9search6 |
| SR-027 | Swim-Training Volume and Shoulder Pain Across the Life Span of the Competitive Swimmer | Systematic review / 2020 | 4 | Cutoffs still uncertain | citeturn7view15 |
| SR-047 | Injury Profile Among Street Workout Practitioners | Case-control / 2021 | 3 | Self-report and selection bias | citeturn11search6 |
| SR-049 | Progressive calisthenic push-up training and muscle strength/thickness | Intervention study / 2018 | 3 | Push-up-specific small sample | citeturn11search0 |
| SR-063 | Instruction-Beginners Reference Material | Boxing Canada coaching manual / 2024 | 3 | Coaching consensus, beginner manual | citeturn26view4turn27view0turn27view1turn27view2 |
| SR-064 | Freestyle Breathing: Swim Farther With Less Effort | U.S. Masters Swimming guide / current | 3 | Coaching guide, not a trial | citeturn26view2 |
| SR-066 | Physical Demands of Different Positions in FA Premier League Soccer | Match-analysis study / 2007 | 4 | Older single-league dataset | citeturn28view0 |

## Data collection roadmap and first ten deep-collect sports

The correct rollout is **ontology first, then high-demand sports, then edge cases**. That sequencing minimizes rework in the planner and gives the AI a universal substrate before sport-specific specialization.

| Phase | Core deliverables | Exit criteria |
|---|---|---|
| Universal foundation | Schema, movement library, exercise library, programming defaults, readiness rules | Session builder can create safe general plans |
| Sport starter packs | 10 priority sports below | One validated profile and starter decision rules per sport |
| Running module | Workout objects, GPS metrics, progression and heat rules | Plans can adjust to pace, terrain, heat, and readiness |
| Nutrition module | Macro/hydration/REDs-safe logic | Meal guidance can explain tradeoffs and safety flags |
| Skills and testing | Skill modules and performance tests | “Learn your sport” and benchmarking loops function end-to-end |
| QA and validation | Expert review, contraindication audit, source refresh jobs | Autonomous recommendations pass safety review |

### First ten sports to collect deeply

These should be the first full-depth collections because, taken together, they cover combat, endurance, field/court, racket, aquatic, bodyweight, and mainstream general-fitness use cases.

| Priority | Sport | Why it belongs in wave one |
|---|---|---|
| High | Boxing | High skill + conditioning + readiness-sensitivity |
| High | Running | GPS, route history, zone logic, mass-market conditioning |
| High | Football/soccer | Large user base, multi-demand intermittent sport |
| High | Cricket | Distinct role demands and injury patterns |
| High | Basketball | Jump-sprint-COD archetype with clear injury needs |
| High | Badminton | High-speed racket footwork and repeat-lunge profile |
| High | Tennis | Serve + lateral movement + shoulder/elbow integration |
| High | Swimming | Technique-heavy endurance with volume-linked shoulder risk |
| High | Calisthenics | Relative-strength and skill progression engine |
| High | Strength training / general fitness | Essential cross-sport base and general-user coverage |

## JSON examples

### Sport profile example

This boxing example operationalizes the evidence that boxing is an intermittent striking sport with high demands on power, speed, coordination, and repeat-effort fitness, while injury considerations include soft-tissue trauma, hand/wrist issues, and contact-related head flags. citeturn2search0turn2search8turn27view1turn27view2

```json
{
  "id": "sport_boxing_v1",
  "sport_name": "Boxing",
  "sport_category": "Combat Sports",
  "overview": "Intermittent striking sport requiring technical efficiency, repeated high-intensity efforts, footwork, rotational force transfer, and tactical decision-making under fatigue.",
  "primary_goals_of_training": [
    "improve striking skill",
    "improve repeat-effort conditioning",
    "develop lower- and upper-body power",
    "maintain position and balance under contact"
  ],
  "athlete_types": ["fitness_boxer", "novice_amateur", "amateur_competitor"],
  "positions_or_roles": ["orthodox", "southpaw", "out_boxer", "pressure_boxer", "counterpuncher"],
  "competition_structure": "round-based intermittent combat",
  "season_structure": {
    "off_season": "general strength, aerobic base, technical rebuilding",
    "pre_season": "increase boxing-specific conditioning and sparring density",
    "in_season": "maintain strength/power and peak specific readiness",
    "transition_phase": "recover from contact load and rebuild weak links"
  },
  "physical_demands": {
    "strength": "moderate_high",
    "power": "high",
    "speed": "high",
    "agility": "high",
    "aerobic_capacity": "moderate_high",
    "anaerobic_capacity": "high",
    "mobility": "high",
    "coordination": "high",
    "balance": "high",
    "reaction_time": "high",
    "muscular_endurance": "high"
  },
  "energy_system_demands": {
    "phosphagen": "high during single exchanges and explosive entries",
    "glycolytic": "high during flurries and late-round bursts",
    "oxidative": "important between exchanges, rounds, and across sessions"
  },
  "movement_demands": [
    "stance_and_guard",
    "rotation",
    "anti_rotation",
    "lateral_footwork",
    "acceleration_deceleration",
    "punching",
    "slip_roll_pivot"
  ],
  "common_injuries": [
    "contusions",
    "lacerations_or_abrasions",
    "hand_or_wrist_pain",
    "shoulder_irritation",
    "head_impact_flags"
  ],
  "recommended_strength_exercises": [
    "split_squat",
    "hinge_variation",
    "pull_variation",
    "anti_rotation_press",
    "loaded_carry"
  ],
  "recommended_power_exercises": [
    "medicine_ball_rotational_throw",
    "jump_squat",
    "plyometric_pushup"
  ],
  "recommended_conditioning_methods": [
    "bag_intervals",
    "shuttle_intervals",
    "rope_skipping",
    "easy_aerobic_runs_or_cycles"
  ],
  "warm_up_protocols": [
    "rope_skip",
    "dynamic_hip_tspine_ankle_mobility",
    "shadowboxing",
    "reaction_drills"
  ],
  "nutrition_considerations": [
    "protect carbohydrate availability around hard sessions",
    "avoid aggressive unsupervised rapid dehydration"
  ],
  "recovery_considerations": [
    "flag any concussion-like symptoms immediately",
    "reduce impact volume when sleep and soreness are poor"
  ],
  "sources": ["SR-011", "SR-012", "SR-063"],
  "evidence_level": "moderate_evidence_plus_coaching_consensus",
  "last_reviewed_date": "2026-05-13",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Exercise example

This exercise example uses ACSM progression logic and the universal movement taxonomy. Goblet squat is a useful starter object because it is equipment-light, technically teachable, and easy to regress/progress. citeturn8view6turn0search0turn14search0

```json
{
  "id": "ex_goblet_squat_v1",
  "name": "Goblet Squat",
  "alternative_names": ["DB Goblet Squat", "KB Goblet Squat"],
  "category": "free_weight",
  "movement_pattern": ["squat", "brace"],
  "primary_muscles": ["quadriceps", "gluteus_maximus"],
  "secondary_muscles": ["adductors", "erector_spinae", "abdominals"],
  "joint_actions": ["hip_flexion_extension", "knee_flexion_extension", "ankle_dorsiflexion_plantarflexion"],
  "equipment_required": ["dumbbell_or_kettlebell"],
  "difficulty_level": "beginner_to_intermediate",
  "sport_relevance": ["general_fitness", "running", "basketball", "soccer", "combat_sports"],
  "goal_relevance": ["strength", "hypertrophy", "movement_quality"],
  "technique_description": "Hold load at chest, brace trunk, descend with balanced foot pressure, and stand with controlled knee and hip extension.",
  "coaching_cues": [
    "ribs stacked over pelvis",
    "full foot on floor",
    "knees track over toes",
    "elbows point down"
  ],
  "common_mistakes": [
    "heels lifting",
    "lumbar collapse",
    "valgus knee drift",
    "depth lost by poor bracing"
  ],
  "safety_notes": [
    "reduce depth if pain occurs",
    "elevate heels or use box regression if ankle mobility limits pattern"
  ],
  "regressions": ["box_squat", "counterbalance_squat", "assisted_squat"],
  "progressions": ["double_kettlebell_front_squat", "barbell_front_squat", "tempo_goblet_squat"],
  "suitable_rep_ranges": ["5-8", "8-12", "12-15"],
  "suitable_intensity_ranges": ["RPE_6_8", "moderate_external_load"],
  "suitable_rest_periods": ["60-150_seconds"],
  "training_quality_targeted": ["strength", "hypertrophy", "movement_quality"],
  "fatigue_cost": "medium",
  "joint_stress": "low_to_medium",
  "best_placement_in_workout": "main_strength_or_accessory",
  "not_recommended_for_whom": ["users_with_painful_acute_knee_or_hip_flare_without_clinical_clearance"],
  "source_refs": ["SR-001", "SR-002"],
  "evidence_level": "strong_evidence",
  "last_reviewed_date": "2026-05-13",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-EXERCISE-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Readiness rule example

This rule reflects the strongest current synthesis: integrate sleep, autonomic status, load, and symptoms; do not make HRV or ACWR a single-metric gate. citeturn12search11turn12search2turn0search1turn24view7turn17search8

```json
{
  "id": "rr_low_sleep_high_soreness_v1",
  "name": "Low sleep plus high soreness readiness downgrade",
  "category": "recovery_readiness_rule",
  "condition": {
    "sleep_duration_hours": "<6",
    "subjective_soreness": ">=7/10",
    "previous_session_intensity": "high",
    "hrv_status": "suppressed_if_available"
  },
  "decision": "downgrade_intensity_and_reduce_local_load",
  "reason": "Performance and recovery are likely impaired; tissue tolerance is reduced and the probability of poor-quality high-intensity work rises.",
  "training_adjustment": {
    "replace": ["max_strength", "max_velocity_sprints", "high_impact_plyometrics"],
    "with": ["technical_practice", "zone1_zone2_aerobic", "mobility", "low_load_strength"],
    "volume_change": "-20_to_-40_percent",
    "intensity_change": "-1_to_-2_rpe"
  },
  "risk_level": "moderate",
  "source_basis": ["SR-003", "SR-007", "SR-037", "SR-038", "SR-039"],
  "warning_logic": "If pain, illness symptoms, or concussion flags are present, escalate to medical referral prompt.",
  "last_reviewed_date": "2026-05-13",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Running workout example

Threshold work belongs in the database as a distinct object because it develops sustained high aerobic power without the recovery cost of all-out interval work. citeturn6search0turn6search4turn23search2turn19search10

```json
{
  "id": "run_threshold_intervals_v1",
  "name": "Threshold Intervals",
  "category": "running_workout",
  "purpose": "Improve lactate-threshold speed and durable race pace",
  "intensity": "comfortably_hard_submaximal",
  "duration_or_distance_range": "20_to_40_minutes_total_work",
  "suitable_user_level": ["intermediate", "advanced", "beginner_with_coach_progression"],
  "warm_up": ["10_to_15_min_easy", "dynamic_drills", "2_to_4_strides"],
  "main_set_examples": [
    "4 x 5_min_threshold with 60_to_90s_easy_jog",
    "3 x 8_min_threshold with 2_min_easy_jog"
  ],
  "cooldown": ["10_min_easy", "light_mobility"],
  "recovery_cost": "medium",
  "progression_logic": [
    "increase total threshold minutes before increasing pace",
    "maintain easy-day separation"
  ],
  "contraindications": [
    "acute calf_or_achilles_pain",
    "very_low_readiness",
    "novice runner without base phase"
  ],
  "source_refs": ["SR-029", "SR-030", "SR-034", "SR-053"],
  "evidence_level": "moderate_evidence",
  "last_reviewed_date": "2026-05-13",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Sport skill example

This boxing-jab example is rooted in governing-body coaching material, so it should be stored as **coaching consensus**, not overrepresented as experimental evidence. citeturn27view1turn27view2turn26view4

```json
{
  "id": "skill_boxing_jab_v1",
  "skill_name": "Boxing Jab",
  "sport": "Boxing",
  "level": "beginner",
  "description": "Lead-hand straight punch used for range finding, scoring, timing disruption, and setup of combinations.",
  "why_it_matters": "The jab is the foundational offensive and defensive connector in boxing.",
  "prerequisites": ["stance", "guard", "basic_balance", "hand_return_to_guard"],
  "step_by_step_learning_progression": [
    "learn stance and guard",
    "extend lead hand on straight line",
    "rotate shoulder to protect chin",
    "retract hand directly to guard",
    "add foot timing and range control"
  ],
  "drills": [
    "mirror_jab",
    "jab_to_target_from_stance",
    "jab_plus_recovery_step",
    "jab_on_coach_call"
  ],
  "common_mistakes": [
    "reaching and losing balance",
    "dropping rear hand",
    "slow retraction",
    "locking knees"
  ],
  "coaching_cues": [
    "hit and come home",
    "shoulder protects chin",
    "stay tall and balanced",
    "rear hand guards face"
  ],
  "self_assessment_checklist": [
    "did hand return to guard quickly",
    "did head stay protected",
    "did feet stay under control"
  ],
  "video_reference_keywords": [
    "boxing jab fundamentals",
    "boxing stance and jab",
    "lead hand straight punch"
  ],
  "safety_notes": [
    "do not hyperextend elbow",
    "use wraps and gloves when progressing impact work"
  ],
  "sources": ["SR-063"],
  "evidence_level": "coaching_consensus",
  "last_reviewed_date": "2026-05-13",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Performance test example

The Yo-Yo IR1 is a high-value soccer/team-sport field test because it has published reliability and validity data and translates well to intermittent-endurance tracking. citeturn21search1

```json
{
  "id": "test_yoyo_ir1_v1",
  "name": "Yo-Yo Intermittent Recovery Test Level 1",
  "category": "performance_test",
  "purpose": "Assess intermittent endurance and recovery capacity relevant to team sports",
  "equipment": ["20m_markers", "audio_file", "flat_running_surface"],
  "protocol": [
    "perform repeated 2 x 20m shuttle runs at increasing speed",
    "take active recovery during designated intervals",
    "terminate when pace can no longer be maintained on two occasions"
  ],
  "scoring": {
    "primary_score": "total_distance_m",
    "secondary_scores": ["peak_heart_rate_if_available", "rpe_post_test"]
  },
  "reliability": "good_in_target_populations",
  "sport_relevance": ["soccer", "basketball", "handball", "field_hockey"],
  "benchmark_storage_note": "store norms by age, sex, level, and sport",
  "safety_notes": [
    "avoid during acute lower-limb injury",
    "do not test when significant illness or severe fatigue is present"
  ],
  "sources": ["SR-055"],
  "evidence_level": "moderate_evidence",
  "last_reviewed_date": "2026-05-13",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

## Starter records for the first ten sports

These are **database-ready v0.1 starter records**, not final exhaustive sport packs. They are strong enough to power early planning, session generation, and coach dashboards, but most still require sport-specific expert validation and benchmark enrichment. Where evidence is thinner, the record is marked as coaching consensus rather than overstated. citeturn8view6turn0search1turn14search0

### Boxing

Boxing places a premium on repeated explosive efforts, footwork, rotational force transfer, balance, and decision-making under fatigue. Reviews describe strong demands on speed, power, and coordination, while amateur boxing injury surveillance repeatedly identifies contusions, abrasions/lacerations, and upper-extremity or head-related concerns. citeturn2search0turn2search8turn27view1turn27view2

```json
{
  "id": "sport_boxing_starter_v01",
  "sport_name": "Boxing",
  "sport_category": "Combat Sports",
  "athlete_types": ["fitness_boxer", "novice_amateur", "amateur_competitor"],
  "roles": ["orthodox", "southpaw", "out_boxer", "pressure_boxer", "counterpuncher"],
  "demand_profile": {
    "strength": "moderate_high",
    "power": "high",
    "speed": "high",
    "agility": "high",
    "aerobic_capacity": "moderate_high",
    "anaerobic_capacity": "high",
    "mobility": "thoracic_hip_ankle_shoulder"
  },
  "energy_systems": {
    "phosphagen": "high",
    "glycolytic": "high",
    "oxidative": "moderate_high"
  },
  "movement_demands": ["stance_and_guard", "rotation", "anti_rotation", "lateral_footwork", "deceleration", "punching"],
  "common_injuries": ["contusions", "lacerations_abrasions", "hand_wrist_pain", "shoulder_irritation", "head_impact_flags"],
  "kpis": ["technical_accuracy_under_fatigue", "punch_velocity_proxy", "round_density", "body_mass_management"],
  "tests": ["CMJ", "medicine_ball_rotational_throw", "beep_or_yoyo_variant", "grip_strength"],
  "weekly_training_logic": {
    "2_days_per_week": ["1_skill_plus_strength", "1_skill_plus_conditioning"],
    "3_days_per_week": ["2_skill_sessions", "1_strength_power_session"],
    "4_days_per_week": ["2_skill", "1_strength_power", "1_conditioning"]
  },
  "exercise_buckets": ["split_squat", "hinge", "horizontal_pull", "push", "medicine_ball_rotation", "neck_bracing", "carry"],
  "ai_rules": [
    {
      "condition": "low_readiness_or_headache_on_contact_day",
      "decision": "replace_sparring_with_shadowboxing_and_technical_drills",
      "reason": "contact quality and safety are compromised"
    },
    {
      "condition": "physique_plus_sport_goal",
      "decision": "use_moderate_hypertrophy_volume_away_from_hard_bag_or_sparring_days",
      "reason": "excess soreness can impair skill and conditioning"
    }
  ],
  "source_refs": ["SR-011", "SR-012", "SR-063"],
  "evidence_level": "moderate_evidence_plus_coaching_consensus",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Running

The running engine should bias heavily toward aerobic consistency, conservative load progression, and explicit risk control for sudden volume spikes. Endurance reviews support predominantly low-intensity distribution in trained endurance populations, and novice-runner studies show that large short-term increases in running distance are risky while beginner starting doses should be conservative. Heat and hydration guidance should be first-class plan modifiers, not optional notes. citeturn6search0turn6search4turn18search10turn18search20turn18search15turn23search2turn23search12

```json
{
  "id": "sport_running_starter_v01",
  "sport_name": "Running",
  "sport_category": "Endurance Sports",
  "athlete_types": ["beginner_runner", "recreational_runner", "race_runner", "sport_conditioning_runner"],
  "roles": ["5k", "10k", "half_marathon", "marathon", "conditioning_runner"],
  "demand_profile": {
    "strength": "supportive_not_primary",
    "power": "depends_on_goal",
    "speed": "goal_dependent",
    "aerobic_capacity": "high",
    "anaerobic_capacity": "moderate_goal_dependent",
    "mobility": "ankle_hip_tspine_supportive"
  },
  "energy_systems": {
    "phosphagen": "important_for_sprints_and_hills",
    "glycolytic": "important_for_threshold_vo2_and_racing",
    "oxidative": "dominant_for_base_and_distance_events"
  },
  "movement_demands": ["locomotion", "landing", "deceleration", "single_leg_support", "elastic_recoil"],
  "common_injuries": ["achilles_or_calf_irritation", "patellofemoral_pain", "shin_pain", "hamstring_or_hip_overuse"],
  "kpis": ["distance", "pace", "heart_rate", "training_load", "personal_records", "route_difficulty"],
  "tests": ["5k_time_trial", "threshold_estimate", "resting_hr_trend", "optional_vo2_proxy"],
  "weekly_training_logic": {
    "distribution": "most_volume_easy",
    "progression_bias": "conservative",
    "spike_management": "avoid_large_single_run_jumps",
    "deload_logic": "insert_when_fatigue_flags_or_after_build_blocks"
  },
  "exercise_buckets": ["single_leg_strength", "calf_strength", "hamstring_strength", "core_stiffness", "foot_ankle_capacity"],
  "ai_rules": [
    {
      "condition": "beginner_with_low_base",
      "decision": "start_with_walk_run_or_short_easy_runs_and_gradual_progression",
      "reason": "novice runners tolerate smaller starting doses better"
    },
    {
      "condition": "heat_or_humidity_high",
      "decision": "slow_pace_targets_increase_recovery_and_hydration_prompts",
      "reason": "heat stress changes physiological cost"
    },
    {
      "condition": "single_run_planned_far_above_recent_longest_run",
      "decision": "cap_session_and_warn_user",
      "reason": "single-session spikes are injury-associated"
    }
  ],
  "source_refs": ["SR-029", "SR-030", "SR-031", "SR-032", "SR-033", "SR-034", "SR-036"],
  "evidence_level": "moderate_to_strong_evidence",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Football and soccer

Soccer is intermittent, multi-directional, and position-specific. Match-analysis work shows repeat changes of direction, turns, accelerations, and position-dependent demands, while soccer injury reviews consistently place the lower limb at the center of injury burden and FIFA 11+ evidence supports structured warm-up prevention work. Workload data matter, but ACWR should not be treated as a causal injury oracle. citeturn28view0turn10search1turn2search1turn10search2turn24view7turn17search8

```json
{
  "id": "sport_soccer_starter_v01",
  "sport_name": "Football/Soccer",
  "sport_category": "Team Field/Court Sports",
  "athlete_types": ["youth_player", "recreational_player", "academy_player", "competitive_player"],
  "roles": ["goalkeeper", "defender", "midfielder", "winger", "striker"],
  "demand_profile": {
    "strength": "moderate_high",
    "power": "high",
    "speed": "high",
    "agility": "high",
    "aerobic_capacity": "high",
    "anaerobic_capacity": "high"
  },
  "energy_systems": {
    "phosphagen": "burst_actions",
    "glycolytic": "repeat_high_intensity_actions",
    "oxidative": "match_recovery_and_total_work"
  },
  "movement_demands": ["sprint", "change_of_direction", "deceleration", "landing", "kicking", "jumping", "backpedal"],
  "common_injuries": ["ankle_sprain", "hamstring_strain", "knee_injury", "groin_pain"],
  "kpis": ["sprint_exposure", "repeat_sprint_capacity", "jumping_heading_capacity", "match_load", "availability"],
  "tests": ["10m_20m_sprint", "CMJ", "YoYo_IR1", "505_or_5_10_5", "groin_and_hamstring_screen"],
  "weekly_training_logic": {
    "goalkeeper": ["power", "landing", "upper_body_and_core", "reactivity"],
    "midfielder": ["intermittent_endurance", "repeat_running", "deceleration"],
    "winger_striker": ["acceleration", "max_velocity", "finishing_freshness"]
  },
  "exercise_buckets": ["split_squat", "hinge", "hamstring_eccentric", "calf", "landing_mechanics", "plyometrics", "rotation_anti_rotation"],
  "ai_rules": [
    {
      "condition": "match_within_48h",
      "decision": "remove_high_soreness_lower_body_hypertrophy",
      "reason": "sprinting and COD quality take priority"
    },
    {
      "condition": "history_of_lower_limb_injury",
      "decision": "prioritize_fifa11plus_style_warmup_and_tissue_capacity_work",
      "reason": "prevention evidence is strongest here"
    }
  ],
  "source_refs": ["SR-013", "SR-038", "SR-039", "SR-055", "SR-066"],
  "evidence_level": "moderate_to_strong_evidence",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Cricket

Cricket requires role-specific logic more than many sports. Fast bowlers, batters, wicketkeepers, and fielders do not have the same stress profile; published injury data consistently show fast bowlers carry the heaviest physical and injury burden, especially hamstring and lumbar issues, while profiling studies show meaningful positional differences. citeturn3search5turn3search6

```json
{
  "id": "sport_cricket_starter_v01",
  "sport_name": "Cricket",
  "sport_category": "Team Field/Court Sports",
  "athlete_types": ["recreational_player", "club_player", "competitive_player"],
  "roles": ["batter", "fast_bowler", "spin_bowler", "wicketkeeper", "fielder"],
  "demand_profile": {
    "strength": "role_dependent",
    "power": "high_for_bowling_throwing_hitting",
    "speed": "moderate_high",
    "agility": "moderate_high",
    "aerobic_capacity": "moderate",
    "anaerobic_capacity": "moderate_high"
  },
  "energy_systems": {
    "phosphagen": "high_for_sprints_throws_bowling_actions",
    "glycolytic": "moderate_intervals_of_play",
    "oxidative": "supports_long_match_duration"
  },
  "movement_demands": ["rotation", "anti_rotation", "sprint", "throw", "jump_land", "deceleration"],
  "common_injuries": ["hamstring_strain", "lumbar_stress_in_fast_bowlers", "shoulder_overuse", "impact_hand_finger_injuries"],
  "kpis": ["bowling_load", "throwing_load", "sprint_ability", "rotational_power", "availability"],
  "tests": ["medicine_ball_rotational_throw", "10m_20m_sprint", "CMJ", "grip_strength"],
  "weekly_training_logic": {
    "fast_bowler": ["bowling_load_tracking", "posterior_chain", "lumbo_pelvic_strength", "landing_control"],
    "batter": ["rotational_power", "repeat_sprint", "trunk_control"],
    "wicketkeeper": ["squat_tolerance", "lateral_reactivity", "grip"]
  },
  "exercise_buckets": ["hinge", "split_squat", "rotation_anti_rotation", "med_ball", "hamstring", "calf"],
  "ai_rules": [
    {
      "condition": "fast_bowler_plus_lumbar_history_plus_load_spike",
      "decision": "reduce_bowling_volume_and_shift_to_strength_technique",
      "reason": "bowling load and lumbar risk are major concerns"
    }
  ],
  "source_refs": ["SR-015", "SR-016"],
  "evidence_level": "moderate_evidence",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Basketball

Basketball combines repeated jumps, cuts, accelerations, decelerations, and short-duration high-intensity skill execution. Review work emphasizes strength, power, agility, and sufficient endurance, while injury reviews repeatedly identify ankle and knee injuries as common. citeturn24view0turn2search11turn2search3

```json
{
  "id": "sport_basketball_starter_v01",
  "sport_name": "Basketball",
  "sport_category": "Team Field/Court Sports",
  "athlete_types": ["recreational_player", "school_player", "competitive_player"],
  "roles": ["guard", "wing", "forward", "center"],
  "demand_profile": {
    "strength": "moderate_high",
    "power": "high",
    "speed": "high",
    "agility": "high",
    "aerobic_capacity": "moderate",
    "anaerobic_capacity": "high"
  },
  "movement_demands": ["jump", "landing", "sprint", "change_of_direction", "deceleration", "throw_pass", "reach"],
  "common_injuries": ["ankle_sprain", "knee_injury", "patellar_tendon_load", "adductor_or_hamstring_irritation"],
  "kpis": ["jump_height", "repeat_jump_quality", "short_sprint", "COD", "availability"],
  "tests": ["CMJ", "broad_jump", "10m_sprint", "505_or_5_10_5", "grip_strength_optional"],
  "exercise_buckets": ["squat", "hinge", "single_leg", "landing", "plyometric", "calf", "core"],
  "ai_rules": [
    {
      "condition": "game_within_24_36h",
      "decision": "avoid_soreness_heavy_lower_body_volume",
      "reason": "jump_and_cut_quality_are_priority"
    },
    {
      "condition": "ankle_or_knee_history",
      "decision": "bias_toward_landing_deceleration_and_foot_ankle_capacity",
      "reason": "common injury areas need robustness"
    }
  ],
  "source_refs": ["SR-018", "SR-019", "SR-020"],
  "evidence_level": "moderate_evidence",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Badminton

Badminton is one of the purest high-speed racket movement profiles: short rallies, explosive lunges, rapid directional changes, repeated jumps, and strong recovery demands between efforts. Match-play studies report high relative cardiovascular strain, and injury reviews indicate a strong lower-limb and overuse signal. citeturn9search3turn4search0

```json
{
  "id": "sport_badminton_starter_v01",
  "sport_name": "Badminton",
  "sport_category": "Racket Sports",
  "athlete_types": ["recreational_player", "club_player", "competitive_player"],
  "roles": ["singles", "doubles", "mixed_doubles"],
  "demand_profile": {
    "strength": "moderate",
    "power": "high",
    "speed": "high",
    "agility": "very_high",
    "aerobic_capacity": "moderate_high",
    "anaerobic_capacity": "high"
  },
  "movement_demands": ["lunge", "jump", "landing", "change_of_direction", "overhead_strike", "rotation"],
  "common_injuries": ["ankle_foot_injury", "knee_overuse", "achilles_or_calf_irritation", "shoulder_irritation"],
  "kpis": ["court_coverage_speed", "repeat_lunge_quality", "jump_smash_power_proxy", "availability"],
  "tests": ["CMJ", "505", "single_leg_hop_optional", "aerobic_or_intermittent_endurance_test"],
  "exercise_buckets": ["split_squat", "lateral_lunge", "calf", "landing", "overhead_strength_support", "core"],
  "ai_rules": [
    {
      "condition": "high_lower_limb_soreness",
      "decision": "reduce_jump_smash_and_full_court_lunge_volume",
      "reason": "tendon_and_braking_load_are_high"
    }
  ],
  "source_refs": ["SR-021", "SR-022"],
  "evidence_level": "moderate_evidence",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Tennis

Tennis requires repeated acceleration, braking, lateral movement, serve/overhead mechanics, and point-by-point recovery. The injury literature is dominated by upper-extremity overuse and lower-extremity acute demands, and the match-intensity literature supports training for both explosive actions and durable intermittent work. citeturn4search1turn9search6turn26view0

```json
{
  "id": "sport_tennis_starter_v01",
  "sport_name": "Tennis",
  "sport_category": "Racket Sports",
  "athlete_types": ["recreational_player", "adult_beginner", "junior_competitor", "competitive_player"],
  "roles": ["singles", "doubles", "baseliner", "all_court", "serve_volley"],
  "demand_profile": {
    "strength": "moderate",
    "power": "high",
    "speed": "high",
    "agility": "high",
    "aerobic_capacity": "moderate",
    "anaerobic_capacity": "moderate_high"
  },
  "movement_demands": ["lateral_shuffle", "crossover", "deceleration", "serve", "forehand_backhand_rotation", "overhead"],
  "common_injuries": ["shoulder_overuse", "elbow_irritation", "wrist_irritation", "ankle_or_knee_injury"],
  "kpis": ["serve_velocity_proxy", "court_coverage", "repeat_acceleration", "shoulder_status"],
  "tests": ["10m_sprint", "lateral_COD_test", "medicine_ball_rotational_throw", "CMJ_optional"],
  "exercise_buckets": ["split_squat", "rotational_power", "scapular_strength", "calf", "landing", "anti_rotation"],
  "ai_rules": [
    {
      "condition": "shoulder_or_elbow_irritation",
      "decision": "reduce_serve_volume_and_bias_to_lower_body_plus_technical_drill",
      "reason": "overhead load can accumulate quickly"
    }
  ],
  "source_refs": ["SR-024", "SR-025"],
  "evidence_level": "moderate_evidence",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Swimming

Swimming is technique-dominant and highly volume-sensitive. The strongest injury signal in the reviewed evidence is shoulder pain linked with large swimming volumes, especially in adolescence, which makes progressive volume and shoulder-load monitoring central to the app’s swimming logic. citeturn7view15turn26view2

```json
{
  "id": "sport_swimming_starter_v01",
  "sport_name": "Swimming",
  "sport_category": "Endurance Sports",
  "athlete_types": ["learn_to_swim_athlete", "fitness_swimmer", "competitive_pool_swimmer"],
  "roles": ["freestyle", "backstroke", "breaststroke", "butterfly", "distance", "sprint"],
  "demand_profile": {
    "strength": "moderate",
    "power": "event_dependent",
    "speed": "event_dependent",
    "aerobic_capacity": "high_for_distance",
    "anaerobic_capacity": "high_for_sprint",
    "mobility": "shoulder_tspine_ankle_hip"
  },
  "movement_demands": ["locomotion", "pull", "kick", "rotation", "streamline", "start_turn_push"],
  "common_injuries": ["shoulder_pain", "rotator_cuff_irritation", "impingement_like_symptoms", "load_spike_overuse"],
  "kpis": ["pace_per_100", "stroke_count", "breathing_control", "turn_quality", "shoulder_status"],
  "tests": ["time_trial_by_event", "pull_strength_support_tests", "shoulder_screen"],
  "exercise_buckets": ["pull", "scapular_control", "tspine_mobility", "hip_extension", "core_stiffness"],
  "ai_rules": [
    {
      "condition": "adolescent_swimmer_plus_shoulder_pain_plus_recent_volume_rise",
      "decision": "reduce_swim_volume_and_shift_part_of_load_to_technique_and_dryland",
      "reason": "volume-linked shoulder pain risk is meaningful"
    }
  ],
  "source_refs": ["SR-027", "SR-064"],
  "evidence_level": "moderate_evidence_plus_coaching_consensus",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Calisthenics

Calisthenics is primarily a **relative-strength + skill-progression** sport. The current literature supports body-mass-based progression as a meaningful strength stimulus, but injury data also suggest shoulder and back regions can be problematic in street-workout populations, so tissue-capacity and progression rules must be conservative, especially for novices. citeturn11search0turn11search6

```json
{
  "id": "sport_calisthenics_starter_v01",
  "sport_name": "Calisthenics",
  "sport_category": "Skill/Aesthetic/Bodyweight Sports",
  "athlete_types": ["beginner_bodyweight_user", "intermediate_skill_seeker", "advanced_skill_athlete"],
  "roles": ["foundation_strength", "pullup_path", "dip_path", "handstand_path", "muscleup_path"],
  "demand_profile": {
    "max_strength": "high_relative_to_body_mass",
    "hypertrophy": "supportive",
    "power": "moderate_to_high",
    "mobility": "high",
    "stability": "high",
    "coordination": "high"
  },
  "movement_demands": ["pull", "push", "brace", "carry_optional", "hand_support", "hollow_arch_control"],
  "common_injuries": ["shoulder_overuse", "upper_back_or_mid_back_pain", "wrist_irritation", "elbow_tendon_irritation"],
  "kpis": ["strict_pullup_capacity", "dip_capacity", "support_hold", "skill_progression_level"],
  "tests": ["max_strict_pullups", "pushup_capacity", "hang_time", "Lsit_or_hollow_hold"],
  "exercise_buckets": ["scapular_pull", "pushup", "row", "dip_progression", "hollow_body", "wrist_prep"],
  "ai_rules": [
    {
      "condition": "novice_plus_goal_is_advanced_skill",
      "decision": "build_foundation_strength_and_tendon_tolerance_before_high_skill",
      "reason": "relative_strength_and_tissue_capacity_are_prerequisites"
    },
    {
      "condition": "shoulder_or_wrist_irritation",
      "decision": "regress_to_supported_variations_and_reduce_skill_volume",
      "reason": "skill work is joint-demanding"
    }
  ],
  "source_refs": ["SR-001", "SR-047", "SR-049"],
  "evidence_level": "moderate_evidence",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

### Strength training and general fitness

This domain should serve both standalone users and athletes using gym work as base preparation. ACSM’s recent synthesis strongly supports progressive resistance training for muscle function, hypertrophy, and physical performance, while general adult guidance still supports at least two weekly strengthening exposures as a baseline. Nutrition and REDs logic matter whenever body-composition goals become aggressive. citeturn7view18turn8view6turn6search13turn0search2turn22search2

```json
{
  "id": "sport_general_fitness_starter_v01",
  "sport_name": "Strength Training / General Fitness",
  "sport_category": "General Fitness Goals",
  "athlete_types": ["beginner", "return_to_fitness", "fat_loss_user", "muscle_gain_user", "strength_user"],
  "roles": ["fat_loss", "muscle_gain", "strength", "athletic_physique", "longevity"],
  "demand_profile": {
    "strength": "primary",
    "hypertrophy": "goal_dependent",
    "power": "optional_goal_dependent",
    "aerobic_capacity": "supportive",
    "mobility": "supportive",
    "stability": "supportive"
  },
  "movement_demands": ["squat", "hinge", "lunge", "push", "pull", "carry", "brace", "rotation_optional"],
  "common_injuries": ["technique_related_flareups", "load_spike_pain", "deconditioned_tissue_soreness"],
  "kpis": ["training_consistency", "strength_progress", "body_composition_proxy", "waist_or_mass_trend", "readiness"],
  "tests": ["estimated_1RM", "pushup_test", "pullup_test_optional", "plank_hold", "CMJ_optional"],
  "exercise_buckets": ["compound_lifts", "machine_support", "single_leg", "core", "carry", "zone2_cardio"],
  "ai_rules": [
    {
      "condition": "beginner",
      "decision": "start_with_2_to_3_full_body_sessions_and_simple_progressions",
      "reason": "consistency_and_movement_quality_beat_complexity"
    },
    {
      "condition": "fat_loss_plus_high_training_fatigue",
      "decision": "protect_strength_and_protein_intake_and_avoid_excessive_volume",
      "reason": "aggressive deficits can impair recovery_and_performance"
    }
  ],
  "source_refs": ["SR-001", "SR-002", "SR-005", "SR-008", "SR-065"],
  "evidence_level": "strong_evidence",
  "expert_validation_status": "pending",
  "sftc_app_usage_profile_id": "UP-SPORT-DEFAULT",
  "personalization_profile_id": "PP-ATHLETE-CORE-v1"
}
```

## Open questions and limitations

This report establishes the architecture and provides high-confidence starter records, but several pieces still need deeper collection before SFTC should claim “expert-grade” coverage across all sports. The largest gaps are: sport-, age-, sex-, and level-specific benchmark norms; female-player-specific evidence in some sports; richer role-based conditioning logic for cricket, tennis, and swimming sub-disciplines; and broader validation of skill-teaching content that still comes primarily from governing-body coaching manuals rather than intervention trials. citeturn22search2turn1search2turn1search10turn7view15turn26view4

ACWR should be stored as a contextual workload descriptor, not the app’s primary injury-risk engine, because the methodological literature does not support causal overconfidence. Menstrual-cycle handling should remain symptom-led and optional. Weight-cutting, concussion flags, REDs risk, exertional heat illness, and exercise-associated hyponatremia should always trigger conservative routing and, where appropriate, medical referral prompts rather than autonomous hard prescriptions. citeturn24view7turn17search8turn1search2turn1search10turn22search2turn23search2turn23search12