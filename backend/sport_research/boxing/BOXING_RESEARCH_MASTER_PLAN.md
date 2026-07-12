# Boxing Research Master Plan

## Objective

Build an app-facing boxing knowledge base that helps SFTC understand boxing as a complete combat sport: rules, ring geography, stance, guard, punches, defense, footwork, tactics, sparring load, competition preparation, S&C, injury risk, weight-class demands, and level-based skill teaching.

The database should help the AI generate training that improves boxing performance without reducing boxing to generic HIIT, random bag work, or bodybuilding.

## Research Domains

1. Rules, ring model, scoring, weight classes, and competition structure
2. Technical fundamentals: stance, guard, footwork, punches, combinations, defense
3. Tactical IQ: range, rhythm, pressure, counterpunching, feints, southpaw/orthodox, corner strategy
4. Boxing S&C, injury risk, sparring load, weight making, return-to-training, and macro planning
5. Level-based teaching progressions and assessments

## App-Facing Collections To Create

- `sport_profiles`
- `sport_roles`
- `sport_training_rules`
- `planning_rules`
- `sport_teaching_progressions`
- `sport_skill_assessments`
- `sport_level_transition_rules`

## Boxing-Specific Quality Rules

- Treat boxing as a skill sport first, not just conditioning.
- Separate technical boxing, tactical boxing, sparring, bag work, pad work, roadwork, strength work, and recovery.
- Respect concussion, hand/wrist, shoulder, neck, low-back, knee, and weight-cut risks.
- Beginners should learn stance, guard, balance, footwork, basic punches, defense, and safe contact progression before high-volume sparring.
- Intermediate athletes need combinations, exits, counters, range control, feints, conditioning specificity, and controlled sparring.
- Advanced athletes need opponent-specific tactics, fight-camp periodization, sparring load management, high-quality power/speed work, and tapering.
- Never prescribe hard sparring as default conditioning.
- Never pair heavy neck/shoulder fatigue with high-contact sparring without recovery logic.
- Weight making should be handled conservatively and never include unsafe dehydration instructions.

## Output Standard

Every final record should answer one backend question:

- What boxing quality is this?
- Who is it for?
- When should it be used?
- What should be avoided?
- How does it progress by level?
- What injuries or fatigue states change the prescription?
- How does it influence macro planning?

