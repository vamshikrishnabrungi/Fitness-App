# Volleyball Research Master Plan

## Purpose

Build a volleyball knowledge system strong enough to support SFTC workout generation, sport teaching, role-specific athletic planning, tactical IQ, and progression decisions.

The target quality is not "generic volleyball fitness." The backend should understand volleyball like a high-level coaching staff:

- the rules and rotation constraints that shape player actions
- position-specific skill demands
- team systems and tactical choices
- serve/receive, transition, blocking, defense, and side-out logic
- beginner/intermediate/advanced teaching progressions
- injury risks from jumping, landing, overhead hitting, blocking, serving, and high training volume
- how gym work supports volleyball without interfering with court quality

The end product should become structured backend data, not a generic article.

## Scope

### Sport Variants

Initial scope:

- indoor six-player volleyball
- youth, school, college, club, and competitive adult levels
- beginner through advanced athlete development

Later scope:

- beach volleyball
- sitting volleyball
- elite opposition scouting packs

## Core Volleyball Domains

### 1. Rules, Rotations, And Systems

Research needs:

- FIVB rule structure
- rally scoring
- rotations and overlap rules
- front row vs back row restrictions
- libero rules and constraints
- substitution rules
- serve order and rotation order
- 4-2, 6-2, and 5-1 systems
- how rotations create offensive/defensive strengths and weaknesses
- how rules change tactical decisions

Backend outputs:

- `volleyball_rule_models`
- `volleyball_rotation_models`
- `volleyball_system_profiles`
- `volleyball_position_constraints`
- `volleyball_tactical_rules`

### 2. Positions And Role Demands

Positions to model:

- Setter
- Outside hitter / left-side hitter
- Opposite / right-side hitter
- Middle blocker / middle hitter
- Libero
- Defensive specialist
- Serving specialist

For each role, research:

- primary responsibilities
- technical priorities
- tactical decisions
- physical qualities
- common injury risks
- S&C priorities
- beginner vs intermediate vs advanced progression

Backend outputs:

- `volleyball_role_profiles`
- `volleyball_role_physical_demands`
- `volleyball_role_skill_priorities`
- `volleyball_role_injury_risks`
- `volleyball_role_training_implications`

### 3. Serving

Research needs:

- underhand serve for beginners
- standing float serve
- jump float serve
- topspin/jump serve
- serving zones
- serving seams
- targeting weak passers
- serving short/deep
- serving under pressure
- serve risk management
- serving as tactical weapon vs error control

Backend outputs:

- `volleyball_serving_models`
- `volleyball_serving_progressions`
- `volleyball_serving_tactical_rules`
- `volleyball_serving_assessments`

### 4. Serve Receive And Passing

Research needs:

- platform shape
- footwork before contact
- angle control
- midline vs outside-body passing
- seam responsibility
- 2-person and 3-person receive systems
- libero responsibility
- passing zones and quality grades
- handling float vs topspin serve
- communication rules

Backend outputs:

- `volleyball_passing_models`
- `volleyball_receive_systems`
- `volleyball_seam_rules`
- `volleyball_passing_assessments`

### 5. Setting And Offensive Organization

Research needs:

- hand setting mechanics
- footwork to ball
- tempo setting
- front set, back set, quick set, pipe, slide, high ball
- setter decision tree
- offensive tempo
- attacker availability
- blocker matchup recognition
- out-of-system setting
- 5-1 and 6-2 offensive logic

Backend outputs:

- `volleyball_setting_models`
- `volleyball_offense_system_profiles`
- `volleyball_set_tempo_models`
- `volleyball_setter_decision_rules`

### 6. Attacking

Research needs:

- approach mechanics
- penultimate step
- arm swing
- takeoff mechanics
- contact point
- attacking lines, cross-court, tips, roll shots, tooling block
- transition attacking
- out-of-system attacking
- hitter coverage
- role-specific attack choices

Backend outputs:

- `volleyball_attacking_models`
- `volleyball_attack_options`
- `volleyball_attacker_progressions`
- `volleyball_attack_tactical_rules`

### 7. Blocking

Research needs:

- ready position
- footwork patterns: shuffle, crossover, swing block
- hand positioning
- press over net
- solo vs double block
- read blocking vs commit blocking
- blocking seams
- middle blocker responsibilities
- opponent setter/hitter cues

Backend outputs:

- `volleyball_blocking_models`
- `volleyball_blocking_systems`
- `volleyball_blocking_tactical_rules`
- `volleyball_blocker_assessments`

### 8. Defense, Digging, And Transition

Research needs:

- base defense
- perimeter defense
- rotational defense
- read defense
- defensive posture
- digging hard-driven balls
- digging tips/roll shots
- pursuit and emergency plays
- transition from defense to attack
- libero and DS tactical responsibilities

Backend outputs:

- `volleyball_defense_systems`
- `volleyball_digging_models`
- `volleyball_transition_models`
- `volleyball_defensive_tactical_rules`

### 9. Team Tactics And Match IQ

Research needs:

- side-out vs transition phase
- first-ball side-out
- serving pressure vs error management
- matchup targeting
- rotation-by-rotation strengths/weaknesses
- setter tendencies
- hitter tendencies
- blocker matchups
- timeout/substitution use
- scoring runs and momentum
- statistical performance indicators

Backend outputs:

- `volleyball_match_phase_models`
- `volleyball_scouting_models`
- `volleyball_tactical_decision_rules`
- `volleyball_performance_indicators`

### 10. S&C, Injury Risk, And Macro Planning

Research needs:

- jump volume and landing load
- shoulder volume from serving and attacking
- knee, ankle, patellar tendon, ACL, shoulder, back, and finger risks
- lower-body strength and power
- eccentric landing capacity
- calf/soleus and ankle stiffness
- trunk stiffness
- overhead shoulder durability
- scapular control
- hip mobility and adductor capacity
- in-season vs off-season training
- tournament weeks and match-day-minus planning
- return-to-jump and return-to-serve/hit progressions

Backend outputs:

- `volleyball_physical_demands`
- `volleyball_injury_risk_rules`
- `volleyball_macro_planning_rules`
- `volleyball_return_to_play_rules`
- `volleyball_testing_benchmarks`

## Beginner / Intermediate / Advanced Teaching Logic

### Beginner

Goal:

- learn safe, repeatable basic skills and court understanding

Priorities:

- ready position
- movement to ball
- forearm passing
- simple serving
- basic setting shape
- safe approach and landing mechanics
- communication
- rotation basics

Avoid:

- excessive jump serving
- high-volume hitting
- complex offensive systems
- aggressive plyometrics without landing skill
- overloading shoulder before scapular control

### Intermediate

Goal:

- build role-specific reliability and tactical decisions

Priorities:

- serve receive quality
- attacking choices
- setting tempo
- block/defense relationship
- transition attack
- position-specific movement
- controlled power development
- repeated jump capacity

Avoid:

- adding every attack option at once
- high jump volume without recovery tracking
- heavy lower-body work before key matches
- neglecting shoulder durability

### Advanced

Goal:

- optimize role-specific performance under tactical and fatigue constraints

Priorities:

- scouting and matchup execution
- tempo and deception
- blocking reads
- serve targeting
- transition efficiency
- high-quality power work
- fatigue-managed jump/serve/attack volume
- tournament microcycle management

Avoid:

- novelty close to competition
- max jump/plyometric volume during high court load
- shoulder overload from combined hitting/serving/gym work

## Draft Files To Create

The volleyball research should produce these draft files:

1. `rules_rotations_systems_draft.json`
2. `positions_roles_demands_draft.json`
3. `serving_receive_passing_draft.json`
4. `setting_offense_attacking_draft.json`
5. `blocking_defense_transition_draft.json`
6. `match_iq_scouting_tactics_draft.json`
7. `volleyball_snc_injury_macro_planning_draft.json`
8. `volleyball_level_teaching_draft.json`

Each draft should contain:

- `source_refs`
- `key_concepts`
- `technical_models`
- `tactical_rules`
- `physical_demands`
- `injury_or_load_risks`
- `training_implications`
- `backend_records_to_create`

## Initial Credible Source Base

Use sources from these categories:

- FIVB official rules and coaching material
- national federation coaching education
- Olympic/team coaching interviews where credible
- peer-reviewed volleyball biomechanics, injury, and performance studies
- reputable S&C and sports medicine sources

Initial source targets:

- FIVB official volleyball rules
- FIVB coaches course material
- USA Volleyball coaching education and lesson plans
- FIVB technical/data reports
- peer-reviewed match-analysis and performance-indicator studies
- peer-reviewed or federation medical material on injury risk, jump load, landing, shoulder, patellar tendon, ACL, ankle sprain, and training load
- NCAA/collegiate or national-federation material where credible

### Source Shortlist

Use this as the first research pool. Agents can add sources, but should prioritize these.

| Area | Source | URL | Use |
| --- | --- | --- | --- |
| Rules | FIVB Official Volleyball Rules 2025-2028 | `https://www.fivb.com/wp-content/uploads/2025/01/FIVB-Volleyball_Rules2025_2028-EN-v05.pdf` | rotations, libero, player actions, front/back row rules, faults |
| Rules | FIVB Official Volleyball Rules page | `https://www.fivb.com/volleyball/the-game/official-volleyball-rules/` | current official rules landing page |
| Rules / Cases | FIVB Casebook 2025 | `https://volleyboll.se/download/18.298f7086197176bdb6335667/1748597507597/FIVB%20CaseBook%202025.pdf` | rule interpretation and examples |
| Coaching | FIVB Coaches Course Materials | `https://www.fivb.com/document-category/coaches-courses-materials/` | Level I/II manuals and official coaching material |
| Coaching | FIVB Coaches Manual Level II | `https://www.fivb.com/wp-content/uploads/2024/03/Coaches_Manual_Level_II_EN.pdf` | tactics, team preparation, strategy, match preparation |
| Coaching | FIVB Tools and Resources Centre | `https://www.fivb.com/inside-fivb/education/tools-and-resources-centre/` | manuals, terminology, education resources |
| Coaching | USA Volleyball Coach Academy | `https://usavolleyball.org/resources-for-coaches/coach-academy/` | coach education library |
| Coaching | USA Volleyball Lesson Plans | `https://usavolleyball.org/resources-for-coaches/lesson-plans/` | gamelike drills for hitting, setting, serving, passing, blocking |
| Serve Receive | USA Volleyball: You Win with Serve Reception, not Passing | `https://usavolleyball.org/resource/you-win-with-serve-reception-not-passing/` | reading serve before contact and representative practice |
| Rules | USA Volleyball Indoor Rules 2025-2027 | `https://usavolleyball.org/wp-content/uploads/2023/03/2025-2027-USAV-Indoor-Rules-Book_FINAL.pdf` | US indoor rule context based on FIVB |
| Injuries | Epidemiology of Common Injuries in the Volleyball Athlete | `https://pmc.ncbi.nlm.nih.gov/articles/PMC10234904/` | common volleyball injury patterns |
| Injuries | Strategies for the Prevention of Volleyball Related Injuries | `https://pmc.ncbi.nlm.nih.gov/articles/PMC2564299/` | ankle/knee/shoulder prevention ideas |
| Injuries | FIVB Medical: Principles of Prevention and Treatment of Common Volleyball Injuries | `https://www.fivb.com/wp-content/uploads/2024/03/FIVB_Medical_Injury_Prevention.pdf` | federation medical injury prevention |
| Injuries | Active & Safe Volleyball Evidence Summary | `https://activesafe.ca/wp-content/uploads/2018/04/Volleyball.pdf` | injury mechanisms and prevention evidence summary |
| Training Load | Beyond the Jump: Scoping Review of External Training Load | `https://pmc.ncbi.nlm.nih.gov/articles/PMC11569689/` | external load and jump monitoring |
| Training Load | Quantifying Internal and External Training Loads in Collegiate Male Volleyball | `https://link.springer.com/article/10.1186/s13102-024-00958-7` | load by mesocycle and position |
| Training Load / Injury | Training Load and Injuries in Volleyball | `https://pubmed.ncbi.nlm.nih.gov/39535079/` | workload and injury risk |
| Performance | FIVB Technical and Data Report VNL 2024 | `https://www.fivb.com/wp-content/uploads/2025/04/FIVB-Technical-and-Data-Report-07.05.2025.pdf` | elite team profiles and performance metrics |
| Performance | Game-Related Performance Factors in European Men's Volleyball | `https://pmc.ncbi.nlm.nih.gov/articles/PMC5260591/` | outcome predictors in high-level volleyball |
| Performance | Game-Related Volleyball Skills that Influence Victory | `https://pmc.ncbi.nlm.nih.gov/articles/PMC4120451/` | victory-discriminating skills |
| Serve | Variables that Predict Serve Efficacy in Elite Men's Volleyball | `https://pmc.ncbi.nlm.nih.gov/articles/PMC5873346/` | serve efficacy predictors |
| Match Analysis | Match Analysis in Volleyball: Systematic Review | `https://mjssm.me/clanci/MJSSM_March_2016_Silva.pdf` | match-analysis literature map |
| Attack | Tactical and Statistical Analysis of Spiking Efficiency | `https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1630870/full` | spike type, zone, and set phase |

## Data Quality Rules

- Do not copy full source text.
- Extract principles, models, rules, and progressions.
- Store source references for traceability.
- Separate skill teaching from S&C prescriptions.
- Separate team tactics from individual fitness.
- Flag confidence when a claim is coaching consensus rather than strong research.
- Keep indoor volleyball separate from beach volleyball unless explicitly useful.

## Backend End State

The backend should be able to answer:

- What does this player need based on role, level, and season phase?
- What volleyball skills should the athlete learn next?
- What physical qualities support that role?
- What should be avoided because of injury, fatigue, match schedule, or current level?
- How should volleyball practice and gym training interact?
- What changes from beginner to intermediate to advanced?
- How should training change during match week or tournament week?
