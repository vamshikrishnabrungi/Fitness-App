# Boxing Multi-Agent Research Briefs

Use these briefs to run parallel research agents. Each agent should produce one structured draft JSON file and cite credible sources.

Target: Olympic/professional-level boxing coaching-staff understanding, converted into backend-useful records.

Backend sport key: `boxing`.

## Shared Output Schema

Each agent returns:

```json
{
  "metadata": {
    "domain": "",
    "sport": "boxing",
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

## Agent 1: Rules, Ring Model, And Competition Structure

Output file:

`drafts/rules_ring_scoring_competition_draft.json`

Research:

- official amateur/Olympic/pro boxing rule differences
- ring size, rounds, time, rest, scoring, fouls, knockdowns, standing counts
- weight classes and implications for training
- judging criteria and 10-point must logic
- competition week and weigh-in constraints

Backend records:

- `boxing_rule_model`
- `boxing_ring_zone_model`
- `boxing_scoring_rule`
- `boxing_competition_phase_model`
- `boxing_weight_class_context`
- `boxing_match_week_rule`

## Agent 2: Technical Fundamentals

Output file:

`drafts/technical_fundamentals_draft.json`

Research:

- stance, guard, balance, posture, chin/shoulder position
- footwork, pivots, ring movement, exits
- jab, cross, hooks, uppercuts, body shots
- defensive actions: block, parry, slip, roll, pull, step-out, clinch basics
- beginner/intermediate/advanced technical progression

Backend records:

- `boxing_stance_model`
- `boxing_footwork_model`
- `boxing_punch_model`
- `boxing_defense_model`
- `boxing_combination_model`
- `boxing_technical_progression`

## Agent 3: Tactical IQ And Fight Strategy

Output file:

`drafts/tactical_iq_strategy_draft.json`

Research:

- range management, rhythm, timing, entries and exits
- pressure fighter, out-boxer, counterpuncher, boxer-puncher, inside fighter
- southpaw/orthodox interactions
- feints, traps, ring cutting, corner strategy
- tactical adjustments between rounds

Backend records:

- `boxing_tactical_archetype`
- `boxing_range_rule`
- `boxing_counterpunching_rule`
- `boxing_pressure_rule`
- `boxing_southpaw_orthodox_rule`
- `boxing_match_iq_progression`

## Agent 4: S&C, Injury, Sparring Load, And Macro Planning

Output file:

`drafts/boxing_snc_injury_macro_planning_draft.json`

Research:

- energy system demands, repeated high-intensity efforts, aerobic recovery
- punching power, rotational power, trunk stiffness, neck/shoulder durability
- footwork conditioning, grip/forearm, calf/ankle capacity
- sparring load management and contact progression
- common injuries: concussion, hand/wrist, shoulder, neck, cuts, low back, knee, ankle
- off-season, camp, competition week, deload/taper, return-to-training

Backend records:

- `boxing_physical_demand`
- `boxing_injury_risk_rule`
- `boxing_sparring_load_rule`
- `boxing_macro_planning_rule`
- `boxing_return_to_play_rule`
- `boxing_readiness_adjustment_rule`

## Agent 5: Level-Based Teaching

Output file:

`drafts/boxing_level_teaching_draft.json`

Research:

- beginner/intermediate/advanced progressions
- skill prerequisites
- assessments and promotion gates
- safe sparring/contact gates
- what to avoid until ready

Backend records:

- `sport_teaching_progressions`
- `sport_skill_assessments`
- `sport_level_transition_rules`

