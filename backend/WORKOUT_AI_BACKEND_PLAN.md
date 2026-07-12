# Workout AI Backend Plan

## Core Mental Model

AI decides:
- what to train
- when to train it
- why it matters
- how hard it should be
- how it should progress
- how the next block should adjust

Database provides:
- exercise definitions
- coaching cues
- common errors
- regressions and progressions
- contraindications
- sport demands
- movement pattern rules
- progression rules
- readiness and pain rules
- source references

Athlete state provides:
- what the user has completed
- how the user responded
- current pain, fatigue, readiness, and performance trends
- what should be adjusted next

Retrieval keeps input flat.
Structure-only generation keeps output flat.
Rolling athlete state keeps long-term planning flat.

## Current Problem

The backend currently asks the AI to do too much in one output.

It asks for:
- full workout structure
- exercise reasoning
- coaching cues
- substitutions
- pain modifications
- sport transfer
- progression logic
- detailed exercise descriptions

This creates three token pressures:

1. Output explosion  
   The model writes too much detail for every exercise and every session.

2. Input bloat  
   The model receives too much knowledge context instead of only the relevant slice.

3. Long-term growth  
   If every future generation includes all previous workouts, the prompt grows forever.

The fix is not only a smaller prompt. The backend needs a better planning architecture.

## Target Architecture

### Layer 1: Macro Plan

Generated once after onboarding.

Purpose:
- define the long-term training direction
- give every future block context
- prevent random weekly workouts
- keep planning coherent across months

Example shape:

```json
{
  "duration_weeks": 24,
  "athlete_profile_snapshot_id": "profile_snapshot_001",
  "blocks": [
    {
      "block": 1,
      "weeks": "1-4",
      "theme": "Foundation",
      "goal": "movement quality, base volume, pain-safe loading"
    },
    {
      "block": 2,
      "weeks": "5-8",
      "theme": "Build",
      "goal": "load progression and sport-transfer strength"
    },
    {
      "block": 3,
      "weeks": "9-12",
      "theme": "Accumulation",
      "goal": "increase training density and work capacity"
    },
    {
      "block": 4,
      "weeks": "13-16",
      "theme": "Intensification",
      "goal": "reduce volume, increase intensity and power emphasis"
    },
    {
      "block": 5,
      "weeks": "17-20",
      "theme": "Sport Peak",
      "goal": "sport-specific performance and fatigue control"
    },
    {
      "block": 6,
      "weeks": "21-24",
      "theme": "Maintenance",
      "goal": "maintain strength, preserve readiness, reduce excessive load"
    }
  ]
}
```

Important:
- The AI may customize the macro plan.
- The backend must provide the planning framework.
- The backend must validate the macro plan against user goal, experience, schedule, pain, sport, and equipment.

### Layer 2: Four-Week Block Generation

Generated at the start of each block.

Purpose:
- create the next 4 weeks
- use the macro plan for direction
- use athlete state for adjustment
- use retrieved database context for allowed exercises and rules

The AI should output structure only:
- week number
- session day
- session title
- session purpose
- training quality
- sport transfer summary
- exercise IDs
- sets
- reps or duration
- rest
- intensity or RPE
- progression instruction

The AI should not output long exercise definitions or long coaching cue blocks.
Those come from the database.

### Layer 3: Exercise Detail Hydration

After AI generates the block, the backend hydrates the workout from the database.

For each exercise ID, the backend attaches:
- definition
- coaching cues
- common errors
- substitutions
- regressions
- progressions
- contraindications
- source references

This keeps AI output small while preserving high-quality coaching detail in the app.

### Layer 4: Athlete State

Updated after each workout and summarized after each block.

Purpose:
- avoid sending full workout history every time
- preserve important training trends
- adjust future plans logically

Example shape:

```json
{
  "user_id": "user_001",
  "current_level": "beginner",
  "current_block": 1,
  "current_week": 3,
  "completion_rate_28d": 0.86,
  "average_rpe_14d": 7.1,
  "pain_trends": [
    {
      "area": "knee",
      "trend": "stable",
      "severity": "mild",
      "notes": "No worsening during lower-body sessions"
    }
  ],
  "strength_trends": [
    {
      "exercise_id": "ex_goblet_squat",
      "trend": "improving",
      "last_completed": "3x10 at RPE 7"
    }
  ],
  "readiness": {
    "sleep_avg_hours_7d": 6.5,
    "stress_level": "moderate",
    "fatigue_flag": false
  },
  "coach_summary": "User is completing sessions well. Keep impact conservative but progress lower-body strength."
}
```

## Data We Need

### 1. Full Exercise Library

This includes:
- gym exercises
- bodyweight exercises
- mobility drills
- warm-up drills
- plyometrics
- sprint drills
- conditioning methods
- Olympic lifting movements and variations
- athletic accessories
- rehab-friendly regressions

The library should not be one flat dump.

Recommended collections:
- `raw_knowledge_sources`
- `exercise_library`
- `primary_exercise_library`
- `exercise_variation_library`
- `exercise_progression_graph`
- `exercise_detail_library`

Primary exercises are default app exercises.
Variations are specialist options unlocked only when appropriate.

### 2. Sport Knowledge Base

This is higher priority than adding more exercise records.

Required collections:
- `sport_profiles`
- `sport_training_rules`
- `sport_position_profiles`
- `sport_season_models`
- `sport_injury_risks`

Each sport profile should include:
- sport demands
- common movement qualities
- energy system needs
- common injury risks
- position or role differences
- training priorities by level
- in-season vs off-season rules

Example for volleyball:
- jumping power
- repeated jump capacity
- landing control
- shoulder durability
- trunk stiffness
- lateral movement
- ankle, knee, and hip control

Example for cricket:
- acceleration
- deceleration
- rotational power
- throwing shoulder durability
- hamstring and calf capacity
- adductor durability
- batting, bowling, and fielding role differences

### 3. Movement Pattern and Physical Quality System

Required collections:
- `movement_patterns`
- `physical_qualities`
- `training_adaptations`

Examples:
- squat
- hinge
- lunge
- push
- pull
- carry
- rotate
- anti-rotate
- jump
- land
- sprint
- decelerate
- change direction

Physical qualities:
- max strength
- hypertrophy
- acceleration
- max velocity
- power
- elastic strength
- aerobic base
- repeat sprint ability
- mobility
- tissue capacity
- trunk stiffness

This lets the AI choose training qualities first, then exercises second.

### 4. Progression and Readiness Rules

Required collections:
- `progression_rules`
- `readiness_rules`
- `pain_adjustment_rules`
- `deload_rules`
- `level_progression_rules`

These rules prevent random progression.

Examples:
- increase load only if target RPE was met
- add reps before load for beginners
- do not increase running impact and plyometric volume in the same week
- reduce impact if knee pain worsens
- deload after high fatigue, low completion, or rising pain

### 5. Transformation and Case Study References

This is useful, but it should not be motivational prose.

Store as structured references:
- `case_study_templates`
- `outcome_archetypes`
- `training_pathway_examples`

Example fields:
- starting profile
- goal
- constraints
- training path
- milestone pattern
- common adjustments
- expected time range
- applicable user tags

Use cases:
- beginner fat loss pathway
- beginner to intermediate strength pathway
- cricket power development pathway
- runner durability pathway
- volleyball jump and landing pathway

Priority:
1. Sport profiles
2. Progression rules
3. Exercise library
4. Case study templates

## Compact Record Format

### Primary Exercise Record

```json
{
  "id": "ex_front_squat",
  "name": "Front Squat",
  "category": "strength",
  "patterns": ["squat", "trunk_stiffness"],
  "qualities": ["lower_body_strength", "postural_strength"],
  "equipment": ["barbell", "rack", "plates"],
  "level_range": ["intermediate", "advanced"],
  "technical_complexity": "moderate",
  "mobility_requirement": "moderate",
  "impact_level": "low",
  "load_scalability": "high",
  "coaching_requirement": "moderate",
  "use_when": [
    "lower-body strength block",
    "athlete needs trunk stiffness and upright squat strength"
  ],
  "avoid_when": [
    "wrist pain",
    "poor front rack mobility",
    "acute knee pain"
  ],
  "progressions": ["ex_pause_front_squat"],
  "regressions": ["ex_goblet_squat"],
  "summary": "Anterior-loaded squat used to build lower-body strength and trunk stiffness.",
  "coaching_cues": [
    "Keep elbows high.",
    "Brace before descending.",
    "Drive up without collapsing through the torso."
  ],
  "common_errors": [
    "Elbows dropping.",
    "Knees collapsing inward.",
    "Losing brace at the bottom."
  ],
  "source_refs": ["source_id"]
}
```

### Variation Record

```json
{
  "id": "ex_block_snatch",
  "name": "Block Snatch",
  "base_exercise": "ex_snatch",
  "tier": "specialist_variation",
  "category": "power",
  "difficulty": "advanced",
  "equipment": ["barbell", "blocks", "plates"],
  "patterns": ["olympic_lift", "triple_extension", "overhead_stability"],
  "qualities": ["explosive_power", "snatch_technique"],
  "use_when": [
    "advanced lifter",
    "Olympic lifting technique session",
    "snatch acceleration from fixed start height"
  ],
  "avoid_when": [
    "beginner",
    "shoulder pain",
    "low back pain",
    "limited overhead mobility",
    "no blocks",
    "no Olympic lifting coaching"
  ],
  "summary": "The block snatch is performed like the snatch, except the bar starts from blocks instead of the floor.",
  "coaching_cues": [
    "Start from a still bar on blocks.",
    "Keep pressure balanced toward mid-foot/heel before separation.",
    "Accelerate aggressively through extension."
  ],
  "common_errors": [
    "Rushing the start position.",
    "Letting the bar drift away.",
    "Using the block height to avoid fixing pull mechanics."
  ],
  "source_refs": ["ow_section_074_snatch_exercises"]
}
```

## Retrieval Contract

The AI should never receive the full database.

For each generation, retrieval should send:
- 15 to 30 allowed primary exercises
- 0 to 8 qualified variations
- relevant progression paths
- relevant sport demands
- relevant movement pattern rules
- relevant progression rules
- relevant pain and readiness rules
- current athlete state
- current macro plan block

Filtering should consider:
- user goal
- sports
- experience level
- training location
- equipment
- facilities
- injury and pain flags
- schedule
- session duration
- current block theme
- athlete state trends

## AI Output Contract

The AI should output structure only.

Example session:

```json
{
  "day": "Monday",
  "title": "Lower Strength + Landing Control",
  "category": "Strength",
  "duration_min": 75,
  "session_purpose": "Build lower-body strength and knee-friendly landing control for volleyball and cricket.",
  "sport_transfer": "Supports jumping, deceleration, and fielding positions.",
  "exercises": [
    {
      "section": "warmup",
      "exercise_id": "ex_ankle_rocker_mobilization",
      "sets": 2,
      "reps": "8 each side",
      "intensity": "easy"
    },
    {
      "section": "main",
      "exercise_id": "ex_goblet_squat",
      "sets": 4,
      "reps": "8",
      "rest": "90 sec",
      "intensity": "RPE 7"
    },
    {
      "section": "main",
      "exercise_id": "ex_lateral_step_down",
      "sets": 3,
      "reps": "8 each side",
      "rest": "60 sec",
      "intensity": "controlled"
    }
  ],
  "progression_rule": "If all sets stay pain-free and RPE is below 8, add 1 rep per set next week before increasing load."
}
```

Backend then hydrates:
- definitions
- cues
- common errors
- substitutions
- regressions
- source references

## Level Progression

User level should not be a fixed identity.
It should be a recommendation state.

Levels:
- beginner
- intermediate
- advanced

Approach:
- Auto with review
- backend computes recommendation
- app shows explanation
- level changes only when evidence supports it

Beginner to intermediate eligibility:
- minimum 4 training weeks or 8 completed workouts
- at least 85 percent planned workout completion
- no worsening pain trend
- average session RPE inside target range
- stable completion of core movement patterns
- current exercises completed without repeated regressions

Intermediate to advanced eligibility:
- minimum 8 additional weeks or 16 completed workouts
- consistent progression in load, reps, density, or benchmarks
- good recovery consistency
- low unresolved pain flags
- equipment and context support advanced work

Hold or regress:
- pain worsening
- completion below 65 percent
- repeated failed sessions
- high fatigue or low readiness
- long break from training

Level affects retrieval:
- beginner: primary exercises and regressions only
- intermediate: primary exercises and simple progressions
- advanced: primary exercises and qualified specialist variations

## Backend Workflow

### Onboarding

1. Save user profile.
2. Build profile snapshot.
3. Retrieve planning frameworks and sport profiles.
4. Generate macro plan.
5. Validate macro plan.
6. Save macro plan.
7. Initialize athlete state.
8. Generate first 4-week block.
9. Validate block.
10. Save workouts.

### Block Generation

1. Load profile snapshot.
2. Load macro plan.
3. Load current athlete state.
4. Retrieve relevant exercise and sport knowledge.
5. Generate 4-week structure-only plan.
6. Validate plan.
7. Hydrate exercise details from database.
8. Save generated workouts.

### After Each Workout

1. Save completion.
2. Save exercise history.
3. Save RPE, pain, readiness, notes.
4. Update athlete state.

### After Each Block

1. Summarize block.
2. Update athlete state.
3. Run level progression check.
4. Generate next 4-week block using macro plan and athlete state.

## Validation Rules

Validate before saving:
- correct number of weeks
- correct sessions per week
- preferred days used when available
- session duration respected
- exercise IDs exist in retrieved allowed set
- no blocked exercise is used
- no advanced variation is used for beginner
- pain rules are respected
- sport transfer exists for sport users
- progression is reasonable
- weekly load does not jump aggressively
- cooldown and warm-up use real exercise IDs

If validation fails:
1. send specific validation errors back to AI once
2. regenerate
3. if it still fails, return a clear backend error

No rule/template fallback workouts.

## Implementation Order

### Phase 1: Planning Foundation

Create or finalize:
- `macro_plans`
- `athlete_states`
- `sport_profiles`
- `movement_patterns`
- `physical_qualities`
- `progression_rules`
- `readiness_rules`
- `pain_adjustment_rules`

Seed minimal planning knowledge for:
- general fitness
- strength
- fat loss
- muscle gain
- running
- cricket
- volleyball
- hybrid sport users

### Phase 2: Structure-Only Program Generator

Create a new generation path:
- macro plan generation
- 4-week block generation
- compact structure-only schema
- AI outputs exercise IDs, sets, reps, intensity, and progression
- backend hydrates details

Keep existing generator until the new path is proven.

### Phase 3: Retrieval Upgrade

Retrieval should return:
- allowed primary exercises
- allowed variations
- blocked exercises
- progression paths
- sport demands
- planning rules
- readiness rules
- athlete state summary

Do not pass raw source records to the AI.

### Phase 4: Validation and Persistence

Add validators for:
- exercise eligibility
- level eligibility
- injury conflicts
- sport transfer
- weekly load progression
- session count
- preferred days

Persist:
- all 4 weeks, not only week 1
- generated program skeleton
- hydrated workout records
- exercise references
- athlete state updates

### Phase 5: Exercise Library Expansion

Only after the architecture is stable:
- build full gym library
- build bodyweight library
- build mobility library
- build sprint and conditioning library
- continue book-by-book source ingestion
- classify primary exercises vs variations

### Phase 6: Cleanup

After the new database and generation path are proven:
- remove obsolete manual seed pathways from production startup
- archive one-off extraction scripts
- keep rebuildable ingestion and catalog scripts
- keep raw sources for traceability
- keep production runtime clean

## Expected End State

The backend should be able to:
- onboard a user
- generate a macro plan
- generate a 4-week training block
- use database-backed exercise details
- adjust future blocks based on athlete state
- avoid dumping the full database into prompts
- avoid generating huge verbose outputs
- keep plans logical for months
- keep workouts sport-specific, progressive, and safe
