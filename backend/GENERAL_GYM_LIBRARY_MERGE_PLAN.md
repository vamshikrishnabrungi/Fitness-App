# General Gym Exercise Library Merge Plan

## Objective

Create the missing general gym strength-and-conditioning database without corrupting the existing Olympic lifting, calisthenics, plyometrics, and mobility knowledge.

The goal is not just to collect exercise names. The goal is to create a usable training catalog that lets the AI choose:

- what exercise fits the athlete
- what variation is appropriate
- what to avoid for injury or readiness
- how to regress or progress over blocks
- which substitutions work when equipment is missing

## Current Build Strategy

Use parallel research, then a single controlled merge.

Parallel workers create drafts only:

- `backend/data/exercise_research_drafts/lower_body_gym_draft.json`
- `backend/data/exercise_research_drafts/upper_body_gym_draft.json`
- `backend/data/exercise_research_drafts/core_carries_athletic_accessories_draft.json`

The main merge process owns:

- deduplication
- naming normalization
- tier classification
- progression graph creation
- source sanity checks
- Mongo ingestion
- retrieval testing

## Canonical Schema

Drafts must follow:

`backend/data/exercise_schema/general_gym_exercise_taxonomy_v1.json`

Validation command:

```bash
backend/.venv/bin/python backend/validate_exercise_research_drafts.py
```

## Merge Rules

1. Keep broadly useful gym exercises as `primary_exercise_library`.
2. Keep stance, grip, equipment, tempo, range, machine, and difficulty variants as `exercise_variation_library` when they change programming use.
3. Do not preserve duplicate records that only rename the same movement.
4. Keep machine alternatives because they matter for beginners, substitutions, hypertrophy, and injury-sensitive users.
5. Keep regressions and progressions even when they are simple.
6. Store long source knowledge nowhere in the prompt path. Keep short summaries, cues, errors, and source refs.
7. Use progression graph edges so future blocks can upgrade training without asking AI to invent progressions.

## Production Collections

Final records should load into:

- `primary_exercise_library`
- `exercise_variation_library`
- `exercise_progression_graph`
- `exercise_library`

## Expected Final Coverage

### Lower Body

- squat pattern
- hinge pattern
- single-leg squat/lunge
- step-up
- hip thrust/bridge
- hamstring curl/Nordic
- knee extension
- calf/soleus
- adductor/groin
- glute medius/lateral hip
- lower-body machines

### Upper Body

- horizontal push
- vertical push
- horizontal pull
- vertical pull
- shoulder/scapular control
- rotator cuff
- chest/back accessories
- arm accessories
- upper-body machines/cables

### Core / Carries / Athletic Accessories

- anti-extension
- anti-rotation
- anti-lateral flexion
- rotation control
- loaded carries
- chops/lifts
- crawls
- sled work
- neck/upper-back capacity
- grip capacity

## Retrieval Expectations

After ingestion:

- beginner gym user should receive machines, dumbbells, goblet squats, supported rows, basic carries, simple core
- intermediate athlete should receive barbell/dumbbell primaries, unilateral work, trunk stiffness, accessories
- user with knee pain should receive knee-friendly hinge, hip, ankle, hamstring, calf, and controlled squat/lunge options
- user with shoulder pain should avoid aggressive overhead work and receive scapular/rotator-cuff alternatives
- user without gym equipment should receive bodyweight/band substitutions

## Test Profiles

Use these after ingestion:

1. Beginner fat loss, 3 days/week, home/bodyweight, knee discomfort.
2. Intermediate cricket + volleyball athlete, 4 days/week, full gym, shoulder history.
3. Intermediate strength goal, 5 days/week, full gym, no injuries.
4. Beginner older adult, 3 days/week, machines/dumbbells, back stiffness.
5. Runner, 2 strength days/week, dumbbells/bands, Achilles sensitivity.

## Done Criteria

- Draft validation passes.
- Duplicates are normalized.
- Mongo ingestion succeeds.
- Retrieval gives relevant exercise candidates for the five test profiles.
- AI prompt receives compact exercise IDs and rules, not full encyclopedia entries.
- Existing Olympic/calisthenics/plyometrics/mobility records still retrieve correctly.

