# SFTC Local MongoDB Blueprint

This backend uses MongoDB locally through `MONGO_URL` and `DB_NAME`.

## Product Logic

SFTC is an athletic training app for:

- Athletes who need sport-specific strength and conditioning.
- Hybrid athletes who train for multiple sports, such as gym + cricket + volleyball.
- Non-athletes pursuing weight loss, muscle gain, general fitness, or mobility.
- Runners using GPS runs, run clubs, city leaderboards, and solo territory capture.
- Coaches managing clients, workouts, meals, and goals.

The backend should treat onboarding as the source of truth for program generation. AI can generate the plan, but the app must store the plan structure, progress, and user feedback independently of the AI response.

## Current Backend Slice

Implemented now:

- `GET /api/athlete/profile` returns or creates the structured athlete profile.
- `PUT /api/athlete/profile` stores the full profile and can generate a program.
- `POST /api/onboarding/complete` marks onboarding complete, stores the athlete profile, and can generate the first program.
- `POST /api/workouts/generate-weekly` accepts the current frontend onboarding payload, normalizes it, stores the profile, archives old active programs, creates a new active `training_program`, creates a `program_block`, and schedules the first week of workouts.
- `GET /api/coach/schemas` exposes the strict JSON contracts for program generation, daily activity snapshots, and future daily coach analysis.
- `GET /api/coach/daily-snapshot?date=YYYY-MM-DD` builds an on-demand snapshot across profile, active program, workouts, workout sessions, exercise results, runs, meals, sleep, quick logs, moods, injuries, health metrics, and coach assignments.
- `POST /api/coach/daily-snapshot?date=YYYY-MM-DD` builds and stores the snapshot in `daily_snapshots`.
- `GET /api/coach/daily-analysis?date=YYYY-MM-DD&refresh=false` returns the stored daily coach analysis or generates one from the daily snapshot.
- `POST /api/coach/daily-analysis?date=YYYY-MM-DD` regenerates and stores the daily coach analysis.
- `GET /api/library/*` exposes the seeded exercise, sport, role, template, injury, progression, readiness, nutrition, running, ontology, benchmark, equipment, and source libraries.

Program generation is currently a deterministic rules engine (`rules_engine_v1`) so local development works without an AI key. The next backend step is to replace or augment that rules engine with an AI generator while keeping the same stored program/workout shape.

The daily coach AI should consume `DailyActivitySnapshot`, not query MongoDB directly. Its output should conform to `DailyCoachAnalysis` before anything is saved or shown to the user.
If no AI key is configured, the backend uses a local rules fallback for readiness, training, nutrition, recovery, risk flags, and plan regeneration signals.

## Current Onboarding Inputs

Already collected:

- goals / selected goals
- experience level
- training location
- equipment
- sports
- body stats: gender, birth year, height, weight, target weight
- location: country, city
- sport context: competition level, season phase
- schedule: days per week, preferred days, session duration, training time, constraints
- injuries and pain areas
- recovery: average sleep, stress level
- nutrition: diet preference, nutrition goal
- basic fitness assessment: pushups, pullups, squats, plank, run pace

## Missing Onboarding Inputs

Needed before backend program generation is reliable:

- body fat if known
- timezone
- sport details: position/role/event
- training history: training age, current weekly volume, recent program, personal bests
- goal details: primary goal, target date, target weight/body composition, priority ranking
- injuries: injury history and detailed restrictions
- recovery: soreness and readiness baseline
- nutrition: allergies, restrictions, calorie/protein target preference
- run context: running experience, weekly km, race goals, preferred surfaces
- coach context: whether user has or wants a coach

## Core Collections

### users

Authentication and account-level identity.

Important fields:

- id
- email
- name
- hashed_password
- mode: user | coach
- profile
- created_at

### athlete_profiles

Long-term structured profile snapshot for program generation. The current app still stores most of this in `users.profile`; this collection is reserved for the cleaner backend phase.

Important fields:

- user_id
- demographics
- location
- sports
- training_context
- goals
- schedule
- injuries
- recovery_baseline
- nutrition_preferences
- onboarding_version

### training_programs

AI-generated or coach-generated high-level program.

Important fields:

- id
- user_id
- source: ai | coach | manual
- title
- goals
- sports
- status: active | paused | completed | archived
- start_date
- end_date
- current_week
- blocks

### workouts

Scheduled planned workouts.

Important fields:

- id
- user_id
- program_id
- scheduled_date
- category
- exercises
- target adaptations: strength, power, speed, endurance, mobility, recovery
- completed

### workout_sessions

Actual completed workout logs.

Important fields:

- id
- user_id
- workout_id
- date
- duration
- completion_percentage
- rpe
- energy_level
- soreness
- notes

### exercise_results

Per-exercise progress history.

Important fields:

- user_id
- session_id
- exercise_id/name
- sets
- reps
- load
- distance/time
- subjective difficulty

### exercise_library

Curated static exercise database for program generation and substitutions.

Important fields:

- id
- name
- category: strength | power | speed | endurance | mobility | prehab | core
- movement_patterns
- primary_muscles / secondary_muscles
- equipment
- difficulty
- coaching_cues
- progressions / regressions / substitutions
- sport_tags
- injury_flags

All knowledge-library records should use the shared evidence envelope from `deep-research-report.md`:

- evidence_level
- source_refs
- sftc_app_usage_profile_id
- personalization_profile_id
- last_reviewed_date
- expert_validation_status
- version

### movement_patterns / physical_qualities

Universal ontology layer used by the planner and AI.

Important fields:

- movement pattern or physical quality
- core tags
- sport transfer
- programming defaults
- evidence envelope fields

### sport_profiles / sport_roles

Sport-specific demands and role-specific program emphasis.

Important fields:

- sport
- physical_demands
- key_qualities
- training_priorities
- common_injuries
- conditioning_needs
- season_phases
- role priorities and risk areas
- report_record_id and raw_report_record when imported from `deep-research-report.md`

Current report-derived starter sports:

- Boxing
- Running
- Football/Soccer
- Cricket
- Basketball
- Badminton
- Tennis
- Swimming
- Calisthenics
- Strength Training / General Fitness

The earlier volleyball profile remains as a local starter record until a deeper report record is added.

### sport_training_rules

Sport-specific AI decision rules extracted from starter sport records.

Important fields:

- sport
- condition
- decision
- reason
- source_refs
- evidence_level

### workout_templates

Reusable workout structures assembled from exercise slots.

Important fields:

- title
- category
- level
- duration_min
- sport_tags
- equipment_required
- exercise_slots with sets/reps/rest

### injury_modifications / progression_rules / benchmark_tests / equipment_library

Support collections for safe personalization, progressive overload, athlete testing, and realistic equipment-aware programming.

### readiness_rules / nutrition_guidelines / running_workouts / running_plan_rules

Decision collections for daily coach analysis, fueling guidance, and run-plan generation.

Important fields:

- condition or target goal
- adjustment/action
- safety flags
- source_refs
- evidence_level

### source_registry / knowledge_sources

Traceability layer for evidence and source governance.

`source_registry` is parsed from `deep-research-report.md` and keeps evidence rank, limitations, and citation placeholders. `knowledge_sources` stores cleaner URL-backed sources already verified for the starter library.

### terra_runs

GPS run records.

Important fields:

- id
- user_id
- date
- start_time
- end_time
- distance_km
- duration_sec
- gps_path
- route_geojson
- city
- pace
- territory_km2
- is_loop

### run_clubs

Public/private run clubs.

Important fields:

- id
- name
- city
- description
- owner_id
- member_ids
- is_public

### run_club_memberships

Membership state for future private clubs and roles.

Important fields:

- club_id
- user_id
- role: owner | admin | member
- status: active | pending | removed
- joined_at

### meals / nutrition_targets

Food logs and nutrition targets.

### sleep_sessions / health_metrics / injuries

Recovery, health trends, and training constraints.

### coach_* collections

Coach-client relationships and assigned plans, workouts, meals, and goals.

### daily_snapshots / coach_daily_analyses

Daily AI input and output records.

Important fields:

- user_id
- date
- snapshot totals: workouts, runs, meals, sleep, territory, nutrition
- readiness inputs: energy, stress, mood, sleep quality, soreness, pain areas
- data quality: available and missing sections
- coach analysis: readiness, recommendations, risk flags, workout modifications

## Progress Storage

Progress should be stored as actual user events, not overwritten summaries:

- workouts completed -> `workout_sessions`
- exercise load/reps -> `exercise_results`
- runs -> `terra_runs`
- meals -> `meals`
- sleep -> `sleep_sessions`
- readiness/strain/recovery inputs -> `health_metrics`, `quick_logs`
- coach assignments -> `coach_*`

Dashboards and leaderboards should be calculated from those records.

## Local Setup

Run MongoDB locally:

```bash
mongod --dbpath ~/data/sftc-mongo
```

Backend startup calls `ensure_database_schema(db)` from `backend/db_setup.py`, creating collections and indexes automatically.

Seed the local knowledge base:

```bash
python -m backend.seed_knowledge_base
```

The seed script also reads `deep-research-report.md` when present and imports its source registry, starter sport records, sport roles, and sport-specific AI rules.

Use `--reset` only when you want to replace existing seeded library records:

```bash
python -m backend.seed_knowledge_base --reset
```
