# Football Multi-Agent Research Briefs

Use these briefs to run parallel research agents. Each agent should produce one structured draft JSON file and cite credible sources.

The target is elite football coaching-staff understanding: technical skill, positional role demands, team tactics, physical preparation, injury control, match-week planning, and tactical IQ.

Backend sport key: `soccer`.

## Shared Output Schema

Each agent returns:

```json
{
  "metadata": {
    "domain": "",
    "sport": "soccer",
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

## Agent 1: Rules, Match Structure, And Game Model

Output file:

`drafts/rules_match_structure_game_model_draft.json`

Research:

- official Laws of the Game
- pitch zones and thirds
- match duration, substitutions, extra time, penalties
- offside, fouls, cards, set pieces, restarts
- formations and player numbering
- phases of play: in possession, out of possession, transition to attack, transition to defense, set pieces
- how rules change tactical decisions and player workload

Questions:

- What are the rule constraints that matter for coaching and backend planning?
- How should beginners understand pitch zones, restarts, and offside?
- How do formations and phases of play shape physical demands?
- What match structures matter for macro-plan and match-week planning?

Backend records:

- `football_rule_model`
- `football_match_phase_model`
- `football_restart_model`
- `football_formation_model`
- `football_game_model_progression`

## Agent 2: Positions, Roles, And Player Profiles

Output file:

`drafts/positions_roles_demands_draft.json`

Research:

- goalkeeper
- center back
- fullback / wingback
- defensive midfielder
- central midfielder
- attacking midfielder
- winger / wide forward
- striker / center forward
- second striker / false nine
- role-specific tactical responsibilities
- role-specific physical demands
- role-specific injury risks
- beginner/intermediate/advanced role development

Questions:

- What does each position do in possession, out of possession, transitions, and set pieces?
- What physical qualities matter most by role?
- What are common role-specific injury and overload risks?
- What should a beginner in each role learn first?
- What separates intermediate from advanced in each role?

Backend records:

- `football_role_profile`
- `football_role_skill_priority`
- `football_role_physical_demand`
- `football_role_injury_risk`
- `football_role_training_implication`

## Agent 3: Ball Mastery, First Touch, Passing, And Receiving

Output file:

`drafts/ball_mastery_first_touch_passing_draft.json`

Research:

- ball mastery
- first touch orientation
- receiving across body
- receiving under pressure
- scanning before receiving
- short passing
- long passing
- wall pass
- third-player combination
- passing weight and timing
- common errors and corrections

Questions:

- How should ball mastery progress from beginner to advanced?
- How does scanning affect receiving and passing decisions?
- What are common first-touch and passing errors?
- How do physical qualities support receiving and passing?

Backend records:

- `football_ball_mastery_model`
- `football_first_touch_model`
- `football_passing_model`
- `football_receiving_model`
- `football_scanning_rule`

## Agent 4: Dribbling, 1v1, Carrying, And Turning

Output file:

`drafts/dribbling_1v1_carrying_turning_draft.json`

Research:

- close control
- running with the ball
- carrying into space
- changes of direction
- body feints
- shielding
- turning under pressure
- 1v1 attacking
- 1v1 defending
- when to dribble vs pass
- beginner/intermediate/advanced progression

Questions:

- How should dribbling be taught by level?
- What is the difference between dribbling, carrying, and 1v1 attacking?
- What cues matter for protecting the ball and beating a defender?
- How does defending 1v1 progress safely?

Backend records:

- `football_dribbling_model`
- `football_1v1_model`
- `football_carrying_model`
- `football_turning_model`
- `football_dribble_decision_rule`

## Agent 5: Shooting, Finishing, Crossing, And Chance Creation

Output file:

`drafts/shooting_finishing_crossing_chance_creation_draft.json`

Research:

- shooting mechanics
- finishing from different angles
- first-time finishing
- volleys and headers
- crossing technique
- cutbacks
- striker movement
- winger delivery
- shot selection
- expected-goal style decision-making
- beginner/intermediate/advanced progression

Questions:

- How should shooting and finishing progress by level?
- How should shot selection be taught?
- What attacking actions are role-specific?
- What physical qualities support shooting, crossing, and repeated attacking actions?

Backend records:

- `football_shooting_model`
- `football_finishing_progression`
- `football_crossing_model`
- `football_chance_creation_rule`
- `football_attacking_third_model`

## Agent 6: Defending, Pressing, Tackling, And Duel Play

Output file:

`drafts/defending_pressing_tackling_duels_draft.json`

Research:

- defensive stance and body shape
- jockeying
- delaying
- tackling technique
- intercepting
- pressing triggers
- cover and balance
- compactness
- back-line coordination
- defensive duels
- safe challenge behavior

Questions:

- How should defending be taught by level?
- What pressing cues and triggers matter?
- What makes a duel safe or risky?
- How do defensive roles change by position and formation?

Backend records:

- `football_defending_model`
- `football_pressing_rule`
- `football_tackling_model`
- `football_duel_model`
- `football_defensive_tactical_rule`

## Agent 7: Team Tactics, Formations, Phases, And Match IQ

Output file:

`drafts/team_tactics_formations_match_iq_draft.json`

Research:

- formations: 4-3-3, 4-2-3-1, 4-4-2, 3-5-2, 3-4-3
- build-up play
- possession play
- counterattack
- pressing systems
- mid-block and low-block defending
- rest defense
- counterpressing
- overloads and underloads
- set-piece tactics
- game-state decisions
- opponent scouting
- performance indicators

Questions:

- What tactical concepts should beginners understand first?
- What tactical ideas separate intermediate from advanced?
- How do formations alter physical and technical demands?
- What stats and performance indicators matter by level?

Backend records:

- `football_formation_profile`
- `football_phase_tactical_rule`
- `football_pressing_system`
- `football_build_up_model`
- `football_match_iq_progression`
- `football_performance_indicator`

## Agent 8: Goalkeeping

Output file:

`drafts/goalkeeping_draft.json`

Research:

- ready position
- handling
- shot stopping
- diving
- footwork
- crosses
- 1v1 situations
- distribution
- sweeper-keeper actions
- communication
- defensive organization
- goalkeeper-specific S&C and injury risks

Questions:

- How should goalkeeping progress from beginner to advanced?
- What technical models matter most?
- What tactical responsibilities matter beyond shot stopping?
- What physical preparation differs from outfield players?

Backend records:

- `football_goalkeeper_model`
- `football_goalkeeper_progression`
- `football_goalkeeper_physical_demand`
- `football_goalkeeper_tactical_rule`
- `football_goalkeeper_assessment`

## Agent 9: Football S&C, Injury Risk, And Macro Planning

Output file:

`drafts/football_snc_injury_macro_planning_draft.json`

Research:

- acceleration and sprinting
- max velocity exposure
- deceleration
- change of direction
- repeated sprint ability
- aerobic base and high-intensity running
- unilateral strength
- hamstring resilience
- adductor/groin durability
- calf/Achilles capacity
- ankle/knee/hip control
- trunk stiffness
- match-day-minus planning
- congested fixtures
- return-to-run and return-to-play
- youth growth/maturation considerations

Questions:

- What physical qualities matter most for each role?
- How should high-speed running exposure shape gym programming?
- What should be avoided before matches?
- How do congested fixtures change training?
- How should hamstring, groin, knee, ankle, and Achilles pain alter workouts?

Backend records:

- `football_physical_demand`
- `football_injury_risk_rule`
- `football_macro_planning_rule`
- `football_return_to_play_rule`
- `football_readiness_adjustment_rule`

## Agent 10: Level-Based Teaching Database

Output file:

`drafts/football_level_teaching_draft.json`

Research:

- beginner/intermediate/advanced progression for every domain
- skill prerequisites
- typical drills
- avoid-until-ready gates
- assessment signals
- position-specific progression
- tactical learning progression

Domains:

- ball mastery
- first touch / receiving
- passing
- dribbling / 1v1
- shooting / finishing
- crossing / chance creation
- defending / pressing
- match IQ / tactics
- goalkeeping
- football S&C

Backend records:

- `sport_teaching_progressions`
- `sport_skill_assessments`
- `sport_level_transition_rules`

## Execution Plan

Run agents in two waves.

### Wave 1: Game Understanding

Run together:

1. Rules, Match Structure, And Game Model
2. Positions, Roles, And Player Profiles
3. Ball Mastery, First Touch, Passing, And Receiving
4. Dribbling, 1v1, Carrying, And Turning
5. Shooting, Finishing, Crossing, And Chance Creation
6. Defending, Pressing, Tackling, And Duel Play
7. Team Tactics, Formations, Phases, And Match IQ
8. Goalkeeping

Output:

- complete football technical/tactical map
- role and formation definitions
- draft backend records to create

### Wave 2: Performance And App Integration

Run after Wave 1:

1. Football S&C, Injury Risk, And Macro Planning
2. Level-Based Teaching Database

Output:

- role-aware S&C and injury rules
- football progression gates
- app-facing beginner/intermediate/advanced teaching records
- retrieval tags for workout generation

## Review Checklist

Before ingestion, confirm:

- no long copied source text
- sources are credible
- 11v11 football is separated from futsal
- beginner/intermediate/advanced is explicit
- roles are explicit
- tactical rules are tied to match situations
- S&C accounts for sprinting, deceleration, match schedule, and football-specific injuries
- injury rules include hamstring, adductor/groin, ankle, knee, ACL, calf/Achilles, and concussion awareness
- records are useful for AI workout generation and not just sport trivia
