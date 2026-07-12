# MMA Agent Research Briefs

## Shared Instructions

Create backend-ready research drafts for SFTC. Do not copy long source prose. Convert credible source material into structured coaching knowledge, teaching progressions, assessment gates, safety rules, and retrieval tags.

Use sources from:

- official MMA rules and federations
- wrestling, grappling, BJJ, and kickboxing rule/education bodies
- reputable coaching education
- peer-reviewed MMA/combat sport physiology, injury, and training-load literature

Each draft should include:

- `research_goal`
- `source_refs`
- `technical_principles`
- `level_guidance`
- `drills_or_practice_design`
- `common_errors`
- `safety_constraints`
- `backend_records`

`backend_records` should contain:

- `sport_training_rules`
- `planning_rules`
- `teaching_progressions`
- `skill_assessments`
- `level_transition_rules`

Use record ids prefixed with `mma_`.

## Agent 1: Rules, Scoring, Fight IQ

Scope:

- unified rules
- amateur vs professional constraints
- scoring priorities
- effective striking/grappling
- effective aggression and cage control as backup criteria
- fight phases
- round strategy
- tactical decision-making
- competition-week rules

Output:

- `backend/sport_research/mma/drafts/rules_scoring_fight_iq_draft.json`

## Agent 2: MMA Striking And Kickboxing

Scope:

- stance and guard for MMA
- boxing entries with takedown risk
- kicking and checking
- knees and elbows by level/rule set
- striking defense
- countering
- footwork and cage positioning
- southpaw/orthodox matchups
- safe sparring progressions

Output:

- `backend/sport_research/mma/drafts/striking_kickboxing_mma_draft.json`

## Agent 3: Wrestling, Clinch, Cage

Scope:

- wrestling stance and motion
- penetration step, level change, single leg, double leg, body lock
- sprawl and takedown defense
- underhooks, overhooks, wrist control, head position
- cage wrestling, wall walks, mat returns, pummeling
- clinch striking rules and safety
- beginner-to-advanced control progressions

Output:

- `backend/sport_research/mma/drafts/wrestling_grappling_cage_draft.json`

## Agent 4: Ground Grappling And Submissions

Scope:

- guard, half guard, side control, mount, back control
- guard passing, sweeps, escapes, stand-ups
- submission hierarchy and avoid-until-ready gates
- ground-and-pound mechanics and safety
- positional sparring progressions
- scramble decision-making

Output:

- `backend/sport_research/mma/drafts/ground_control_submissions_draft.json`

## Agent 5: S&C, Fight Camp, Injury And Load

Scope:

- MMA physical qualities
- aerobic base, anaerobic repeat power, strength, power, neck/trunk/shoulder durability
- fight-camp phases
- sparring/contact load
- return-to-contact and return-to-grappling
- injury and symptom safety rules
- weight-cut and dehydration risks

Output:

- `backend/sport_research/mma/drafts/mma_snc_fight_camp_draft.json`

## Agent 6: Level Teaching And Assessment

Scope:

- beginner/intermediate/advanced domains
- skill assessments
- promotion/hold/regress criteria
- domain-specific readiness
- unlock gates for sparring, submissions, cage wrestling, hard grappling, and fight camp

Output:

- `backend/sport_research/mma/drafts/mma_level_teaching_draft.json`
