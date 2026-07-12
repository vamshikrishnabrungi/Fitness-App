# Volleyball Multi-Agent Research Briefs

Use these briefs to run parallel research agents. Each agent should produce one structured draft JSON file and cite credible sources.

The target is Olympic-staff-level understanding: sport skill, role demands, tactical systems, physical preparation, injury control, and match IQ.

## Shared Output Schema

Each agent returns:

```json
{
  "metadata": {
    "domain": "",
    "sport": "volleyball",
    "version": "draft_v1",
    "research_goal": ""
  },
  "source_refs": [
    {
      "title": "",
      "url": "",
      "source_type": "",
      "organization_or_author": "",
      "notes": ""
    }
  ],
  "key_concepts": [],
  "technical_models": [],
  "tactical_rules": [],
  "physical_demands": [],
  "injury_or_load_risks": [],
  "training_implications": [],
  "backend_records_to_create": []
}
```

## Agent 1: Rules, Rotations, And Systems

Output file:

`drafts/rules_rotations_systems_draft.json`

Research:

- official rules
- rotations
- overlap rules
- front row/back row restrictions
- libero rules
- substitution rules
- 4-2, 6-2, 5-1 systems
- how system choice changes player workload
- how rotations change side-out and transition options

Questions:

- What can each role legally do in each rotation?
- How do front-row/back-row constraints affect attack and block responsibilities?
- How does libero use change serve receive and defense?
- What system should beginners learn first?
- What systems are suitable for intermediate and advanced teams?

Backend records:

- `volleyball_rule_model`
- `volleyball_rotation_model`
- `volleyball_system_profile`
- `volleyball_position_constraint`
- `volleyball_system_progression`

## Agent 2: Positions, Roles, And Athlete Profiles

Output file:

`drafts/positions_roles_demands_draft.json`

Research:

- setter
- outside hitter
- opposite hitter
- middle blocker
- libero
- defensive specialist
- serving specialist
- role-specific physical demands
- role-specific technical priorities
- role-specific tactical responsibilities

Questions:

- What does each position do in serve receive, offense, block, defense, and transition?
- What physical qualities matter most by role?
- What are common role-specific injury risks?
- What should a beginner in each role learn first?
- What separates intermediate from advanced in each role?

Backend records:

- `volleyball_role_profile`
- `volleyball_role_skill_priority`
- `volleyball_role_physical_demand`
- `volleyball_role_injury_risk`
- `volleyball_role_training_implication`

## Agent 3: Serving, Serve Receive, And Passing

Output file:

`drafts/serving_receive_passing_draft.json`

Research:

- underhand serve
- float serve
- jump float
- jump topspin
- serving zones
- seam targeting
- risk/reward serving
- passing platform
- serve receive formations
- seam communication
- passing quality metrics
- libero and outside hitter receive responsibilities

Questions:

- How should serving progress from beginner to advanced?
- How does serve type change receive mechanics?
- How do teams decide serving targets?
- What are common passing errors and corrections?
- What physical support helps passing and serve receive?

Backend records:

- `volleyball_serving_progression`
- `volleyball_serving_tactical_rule`
- `volleyball_passing_model`
- `volleyball_receive_system`
- `volleyball_seam_rule`

## Agent 4: Setting, Offense, And Attacking

Output file:

`drafts/setting_offense_attacking_draft.json`

Research:

- setter footwork
- hand setting mechanics
- set location and tempo
- out-of-system setting
- attack approach mechanics
- arm swing
- contact point
- attack choices
- quicks, slides, pipe, high ball, back-row attack
- offensive systems and combinations

Questions:

- How should setting be taught by level?
- How should attacking be taught by level?
- What is the setter decision tree?
- What attacking options are safe/appropriate for beginners vs advanced players?
- How do offensive systems create matchup advantages?

Backend records:

- `volleyball_setting_model`
- `volleyball_set_tempo_model`
- `volleyball_attacking_model`
- `volleyball_attack_option`
- `volleyball_offensive_tactical_rule`

## Agent 5: Blocking, Defense, Digging, And Transition

Output file:

`drafts/blocking_defense_transition_draft.json`

Research:

- blocking ready position
- shuffle/crossover/swing block footwork
- read block vs commit block
- block hand positioning
- middle blocker responsibilities
- perimeter defense
- rotational defense
- read defense
- digging hard-driven balls
- tips/roll shots
- transition from dig to attack
- coverage responsibilities

Questions:

- How does blocking progress from beginner to advanced?
- How do block and floor defense connect?
- What does each role read before and during the attack?
- What should be avoided when the player lacks landing control?
- How should transition attack be trained safely?

Backend records:

- `volleyball_blocking_model`
- `volleyball_defense_system`
- `volleyball_digging_model`
- `volleyball_transition_model`
- `volleyball_block_defense_tactical_rule`

## Agent 6: Match IQ, Scouting, And Team Tactics

Output file:

`drafts/match_iq_scouting_tactics_draft.json`

Research:

- side-out phase
- transition phase
- serving runs
- rotation-by-rotation analysis
- setter tendencies
- hitter tendencies
- serving target plans
- block matchups
- defensive adjustments
- substitution/time-out decision logic
- common volleyball performance indicators

Questions:

- What stats matter most by level?
- What should beginner players understand tactically?
- What does an advanced team scout?
- How should tactical plans change by rotation?
- What are useful in-match adjustment rules?

Backend records:

- `volleyball_match_phase_model`
- `volleyball_scouting_rule`
- `volleyball_rotation_tactical_rule`
- `volleyball_performance_indicator`
- `volleyball_match_iq_progression`

## Agent 7: Volleyball S&C, Injury Risk, And Macro Planning

Output file:

`drafts/volleyball_snc_injury_macro_planning_draft.json`

Research:

- jump and landing volume
- repeated jump ability
- knee and ankle injury risks
- patellar tendinopathy risk
- ACL risk
- shoulder overuse from serving/hitting
- low back and finger injury risks
- off-season, pre-season, in-season, tournament week
- strength, power, speed, landing, mobility, recovery
- return-to-jump
- return-to-serve/hit

Questions:

- What physical qualities matter most for each role?
- How should court jump volume shape gym programming?
- What should be avoided before matches?
- How do tournament weeks change training?
- How should shoulder and knee pain change workouts?

Backend records:

- `volleyball_physical_demand`
- `volleyball_injury_risk_rule`
- `volleyball_macro_planning_rule`
- `volleyball_return_to_play_rule`
- `volleyball_readiness_adjustment_rule`

## Agent 8: Level-Based Teaching Database

Output file:

`drafts/volleyball_level_teaching_draft.json`

Research:

- beginner/intermediate/advanced progression for every domain
- skill prerequisites
- typical drills
- avoid-until-ready gates
- assessment signals
- role-specific progression

Domains:

- serving
- passing / serve receive
- setting
- attacking
- blocking
- defense / digging
- transition
- match IQ
- volleyball S&C

Backend records:

- `sport_teaching_progressions`
- `sport_skill_assessments`
- `sport_level_transition_rules`

## Parallel Execution Plan

Run agents in two waves.

### Wave 1: Game Understanding

Run these together:

1. Rules, Rotations, And Systems
2. Positions, Roles, And Athlete Profiles
3. Serving, Serve Receive, And Passing
4. Setting, Offense, And Attacking
5. Blocking, Defense, Digging, And Transition
6. Match IQ, Scouting, And Team Tactics

Output:

- full volleyball technical/tactical map
- all role and system definitions
- draft backend records to create

### Wave 2: Performance And App Integration

Run after Wave 1:

1. Volleyball S&C, Injury Risk, And Macro Planning
2. Level-Based Teaching Database

Output:

- role-aware S&C rules
- volleyball progression gates
- app-facing beginner/intermediate/advanced teaching records
- retrieval tags for workout generation

## Review Checklist

Before ingestion, confirm:

- no long copied source text
- all source refs are credible
- indoor volleyball and beach volleyball are separated
- beginner vs intermediate vs advanced is explicit
- roles are explicit
- tactical rules are tied to match situations
- S&C rules account for jump/serve/hit volume
- injury rules include knee, ankle, shoulder, back, finger, and patellar tendon risks
- records are useful for AI workout generation and not just sport trivia

