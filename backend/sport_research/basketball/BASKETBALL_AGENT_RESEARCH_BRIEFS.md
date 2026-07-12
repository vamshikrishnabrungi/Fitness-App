# Basketball Multi-Agent Research Briefs

Use these briefs to run parallel research agents. Each agent should produce one structured draft JSON file and cite credible sources.

Target: Olympic/professional-level basketball coaching-staff understanding, converted into backend-useful records.

Backend sport key: `basketball`.

## Shared Output Schema

Each agent returns:

```json
{
  "metadata": {
    "domain": "",
    "sport": "basketball",
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

## Agent 1: Rules, Positions, And Game Model

Output file:

`drafts/rules_positions_game_model_draft.json`

Research:

- official rules and game structure
- court zones and spacing language
- game duration, shot clock, fouls, free throws, substitutions, violations
- game phases: half-court offense, half-court defense, transition offense, transition defense, special situations
- positions and role archetypes
- role-specific physical demands and injury risks

Backend records:

- `basketball_rule_model`
- `basketball_court_zone_model`
- `basketball_phase_model`
- `basketball_role_profile`
- `basketball_role_physical_demand`
- `basketball_role_injury_risk`
- `basketball_role_training_implication`

## Agent 2: Offensive Skills

Output file:

`drafts/offensive_skills_draft.json`

Research:

- ball handling and dribbling
- change of pace and direction
- passing and receiving
- shooting mechanics and shot types
- finishing and layup package
- footwork, pivots, triple threat
- spacing, cutting, screens, pick-and-roll
- beginner/intermediate/advanced offensive progression

Backend records:

- `basketball_ball_handling_model`
- `basketball_passing_model`
- `basketball_shooting_model`
- `basketball_finishing_model`
- `basketball_footwork_model`
- `basketball_pick_roll_rule`
- `basketball_spacing_rule`
- `basketball_offensive_skill_progression`

## Agent 3: Defense, Rebounding, And Team Tactics

Output file:

`drafts/defense_rebounding_team_tactics_draft.json`

Research:

- defensive stance and containment
- closeouts
- help defense and rotations
- screen navigation
- pick-and-roll coverages
- rebounding and box-outs
- transition defense
- switching, zone, shell principles
- communication and special situations

Backend records:

- `basketball_defensive_model`
- `basketball_closeout_model`
- `basketball_rebounding_model`
- `basketball_screen_navigation_model`
- `basketball_pick_roll_defense_rule`
- `basketball_team_tactical_rule`
- `basketball_match_iq_progression`

## Agent 4: S&C, Injury, And Macro Planning

Output file:

`drafts/basketball_snc_injury_macro_planning_draft.json`

Research:

- acceleration, deceleration, jumping, landing, lateral movement
- repeated sprint and court conditioning
- strength, power, trunk control, ankle/knee/hip capacity
- off-season, pre-season, in-season, competition-week planning
- youth vs adult load management
- ankle, knee, tendon, hip/groin, back, shoulder/wrist/finger risks
- return-to-play and readiness adjustments

Backend records:

- `basketball_physical_demand`
- `basketball_injury_risk_rule`
- `basketball_macro_planning_rule`
- `basketball_return_to_play_rule`
- `basketball_readiness_adjustment_rule`
- `basketball_match_week_rule`

## Agent 5: Level-Based Teaching

Output file:

`drafts/basketball_level_teaching_draft.json`

Research:

- beginner/intermediate/advanced progressions
- skill prerequisites
- typical drills
- avoid-until-ready gates
- assessments and promotion rules

Backend records:

- `sport_teaching_progressions`
- `sport_skill_assessments`
- `sport_level_transition_rules`

