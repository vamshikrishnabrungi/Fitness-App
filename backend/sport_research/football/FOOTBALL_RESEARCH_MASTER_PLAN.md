# Football Research Master Plan

## Purpose

Build a football/soccer knowledge system strong enough to support SFTC workout generation, sport teaching, position-specific athletic planning, tactical IQ, and progression decisions.

The backend should understand football like a high-level coaching and performance staff:

- how rules and match structure shape player actions
- how positions and tactical systems change physical demands
- how technical skills are taught from beginner to advanced
- how team tactics, phases of play, pressing, transitions, and rest defense work
- how conditioning supports football without damaging match quality
- how injuries and fatigue alter training decisions
- how match day, congested fixture periods, travel, and return-to-play affect the plan

The output should become structured backend data, not a generic article.

## Sport Key

- Research folder: `football`
- Backend sport key: `soccer`
- User-facing label: `Football`

## Scope

### Initial Scope

- association football / soccer
- 11v11 football first
- youth, school, club, amateur, college, semi-pro, and advanced competitive levels
- beginner through advanced athlete development

### Later Scope

- futsal
- beach soccer
- goalkeeper specialist expansion
- elite opposition scouting packs

## Core Football Domains

### 1. Rules, Match Structure, And Game Model

Research needs:

- official Laws of the Game
- pitch zones and thirds
- match duration, substitutions, extra time, penalties
- offside, fouls, cards, set pieces, restarts
- formations and player numbering
- phases of play: in possession, out of possession, transitions, set pieces
- how rule constraints shape tactical choices and physical demands

Backend outputs:

- `football_rule_model`
- `football_match_phase_model`
- `football_restart_model`
- `football_formation_model`
- `football_game_model_progression`

### 2. Positions, Roles, And Player Profiles

Positions/roles to model:

- goalkeeper
- center back
- fullback / wingback
- defensive midfielder
- central midfielder
- attacking midfielder
- winger / wide forward
- striker / center forward
- second striker / false nine

For each role, research:

- attacking responsibilities
- defensive responsibilities
- transition responsibilities
- set-piece responsibilities
- physical qualities
- common injury/load risks
- beginner/intermediate/advanced role development

Backend outputs:

- `football_role_profile`
- `football_role_skill_priority`
- `football_role_physical_demand`
- `football_role_injury_risk`
- `football_role_training_implication`

### 3. Ball Mastery, First Touch, Passing, And Receiving

Research needs:

- ball manipulation
- first touch orientation
- receiving across body
- receiving under pressure
- short passing
- long passing
- wall pass / third-player combination
- scanning before receiving
- body shape
- passing weight and timing
- common technical errors and corrections

Backend outputs:

- `football_ball_mastery_model`
- `football_first_touch_model`
- `football_passing_model`
- `football_receiving_model`
- `football_scanning_rule`

### 4. Dribbling, 1v1, Carrying, And Turning

Research needs:

- close control
- changes of direction
- body feints
- shielding
- turning under pressure
- running with the ball
- 1v1 attacking
- 1v1 defending
- when to dribble vs pass
- beginner/intermediate/advanced skill progression

Backend outputs:

- `football_dribbling_model`
- `football_1v1_model`
- `football_carrying_model`
- `football_turning_model`
- `football_dribble_decision_rule`

### 5. Shooting, Finishing, Crossing, And Chance Creation

Research needs:

- shooting mechanics
- finishing from different angles
- first-time finishing
- crossing technique
- cutbacks
- heading
- striker movement
- winger delivery
- shot selection and expected value
- common errors and corrections

Backend outputs:

- `football_shooting_model`
- `football_finishing_progression`
- `football_crossing_model`
- `football_chance_creation_rule`
- `football_attacking_third_model`

### 6. Defending, Pressing, Tackling, And Duel Play

Research needs:

- defensive stance and body shape
- jockeying
- tackling technique
- intercepting
- delaying
- pressing triggers
- cover and balance
- compactness
- back-line coordination
- defensive duels
- avoiding reckless challenge behavior

Backend outputs:

- `football_defending_model`
- `football_pressing_rule`
- `football_tackling_model`
- `football_duel_model`
- `football_defensive_tactical_rule`

### 7. Team Tactics, Formations, Phases, And Match IQ

Research needs:

- common formations: 4-3-3, 4-2-3-1, 4-4-2, 3-5-2, 3-4-3
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

Backend outputs:

- `football_formation_profile`
- `football_phase_tactical_rule`
- `football_pressing_system`
- `football_build_up_model`
- `football_match_iq_progression`
- `football_performance_indicator`

### 8. Goalkeeping

Research needs:

- ready position
- shot stopping
- handling
- diving
- footwork
- crosses
- 1v1 situations
- distribution
- sweeper-keeper actions
- communication and defensive organization
- goalkeeper-specific S&C and injury risks

Backend outputs:

- `football_goalkeeper_model`
- `football_goalkeeper_progression`
- `football_goalkeeper_physical_demand`
- `football_goalkeeper_tactical_rule`
- `football_goalkeeper_assessment`

### 9. S&C, Injury Risk, And Macro Planning

Research needs:

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

Backend outputs:

- `football_physical_demand`
- `football_injury_risk_rule`
- `football_macro_planning_rule`
- `football_return_to_play_rule`
- `football_readiness_adjustment_rule`

### 10. Level-Based Teaching Database

Research needs:

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

Backend outputs:

- `sport_teaching_progressions`
- `sport_skill_assessments`
- `sport_level_transition_rules`

## Initial Source Shortlist

Use credible sources only. Prioritize:

- IFAB Laws of the Game
- FIFA Training Centre
- FIFA technical and tactical reports
- FIFA 11+ injury prevention material
- UEFA technical/coaching material
- official federation coaching resources
- peer-reviewed football match-demand, training-load, and injury-prevention studies
- reputable S&C and sports medicine literature

Starter source targets:

| Domain | Sources |
|---|---|
| Laws/rules | IFAB Laws of the Game, FIFA rules resources |
| Game model/tactics | FIFA Training Centre, UEFA technical reports, FIFA technical reports |
| Skill teaching | FIFA Training Centre coaching content, federation coaching manuals |
| Injury prevention | FIFA 11+, peer-reviewed injury prevention studies |
| Match demands | peer-reviewed physical-demand studies and position-specific reviews |
| Load management | peer-reviewed training-load and injury-risk studies |
| S&C/macro planning | football S&C reviews, hamstring/groin/ACL return-to-play literature |

## Quality Bar

The football database is good only if it helps the backend:

- create a logical football macro plan
- generate role-specific 4-week blocks
- adjust around match days and congested fixtures
- choose relevant S&C based on position, level, and injury state
- teach technical skills by level
- explain sport transfer in workouts
- avoid random conditioning
- avoid treating football as generic running plus leg day
