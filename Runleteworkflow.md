# Runlete — complete system workflow & audit

A full read-through of the codebase: what exists, how it is wired, how data
moves, what is live, and what is dead. Written from source, not from memory.

Audit date: 2026-07-26 · Branch: `feat/adaptive-workout-engine`

---

## 0. Executive summary

Runlete is an **athlete's app** with two live pillars and one dormant one:

| Pillar | State | Notes |
|---|---|---|
| **Run club + territory game** | ✅ live, in production | Run tracking, GPS territory claiming, clubs, leaderboards, activity feed |
| **Workout generation (AI)** | ⏸ built but **paused** | Full multi-stage engine, disabled via `WORKOUT_GENERATION_ENABLED=false` |
| **Sport skills library** | 🚧 planned | Knowledge base exists (3.8k docs); UI reads an empty collection |

Deployment: backend on **Render** (`runlete-api.onrender.com`), database on
**MongoDB Atlas** (Mumbai), email via **Resend**, app is a **React Native /
Expo** release build on iOS.

Scale: **76 API endpoints**, **70 Mongo collections**, ~3.6k lines in
`server.py`, ~44 app screens.

---

## 1. Architecture

```
┌────────────────────────┐        HTTPS/JSON          ┌──────────────────────┐
│  Expo / React Native   │  ───────────────────────▶  │  FastAPI (uvicorn)   │
│  iOS release build     │  ◀───────────────────────  │  Render, single web  │
│  - expo-router screens │      Bearer JWT auth       │  service, free tier  │
│  - zustand stores      │                            └───────┬──────────────┘
│  - AsyncStorage cache  │                                    │ Motor (async)
└────────────────────────┘                                    ▼
                                                    ┌──────────────────────┐
   external: Apple Maps (react-native-maps),        │  MongoDB Atlas M0    │
   expo-location GPS                                │  Mumbai · 70 colls   │
                                                    └──────────────────────┘
                       AI: Anthropic / OpenRouter (workout generation)
                       Email: Resend HTTPS API (OTP)
```

### Backend module map

| File | Lines | Responsibility |
|---|---|---|
| `server.py` | 3,609 | All 76 endpoints, orchestration, auth, program assembly |
| `knowledge_retrieval.py` | 2,982 | Retrieval layer — turns the knowledge base into AI context |
| `ai_workout_service.py` | 1,096 | Prompt construction, AI calls, output validation |
| `macro_plan_service.py` | 715 | Long-term periodized plan (the "season" above weeks) |
| `models.py` | 561 | Pydantic request/response/domain models |
| `db_setup.py` | 536 | 70 collection definitions + all indexes, runs on startup |
| `helpers.py` | 269 | Pure formatters (run/terra normalizers, doc cleaning) |
| `level_progression.py` | 139 | Objective level assessment (beginner→advanced) |
| `sport_library.py` | 200 | Sport section blueprints + KB adapters (new, unwired) |
| `embeddings.py` | 70 | Optional fastembed semantic search (off in prod) |

Support scripts (not part of the running app): `seed_*.py`, `build_*`,
`audit_*`, `generate_*`, `fix_exercise_data.py`, plus per-sport
`validate_*`/`summarize_*` under `sport_research/`.

---

## 2. Request lifecycle & auth

1. App calls `api.get/post/put/delete` (`src/utils/api.ts`).
2. Base URL resolution: in `__DEV__` the **Metro host is auto-detected**
   (survives DHCP changes); otherwise `EXPO_PUBLIC_BACKEND_URL` baked at build
   time. All paths are prefixed `/api`.
3. `Authorization: Bearer <JWT>` attached from AsyncStorage when present.
4. FastAPI `api_router` (prefix `/api`) → `get_current_user` dependency decodes
   the JWT (HS256, `JWT_SECRET`, 30-day expiry), loads the user doc from
   `users`, and injects it into the handler.
5. Errors raise `ApiError` client-side carrying the **HTTP status** (or `null`
   for network failure) — this is what lets the app distinguish "token
   rejected" from "server unreachable".

Middleware: CORS (`ALLOWED_ORIGINS`), SlowAPI rate limits on auth and
generation routes, optional Sentry (inert without `SENTRY_DSN`).

### Auth flows
- **Register**: `POST /auth/request-otp` → 6-digit code (10-min TTL, `otps`
  collection with a TTL index) emailed via Resend → `POST /auth/register`
  (email, password, name, otp, profile) → bcrypt hash → JWT.
- **Login**: password (`/auth/login`) or OTP (`/auth/login-otp`).
- **Session restore**: `loadAuth()` reads the token, calls `/auth/me`, and
  **only clears the session on 401/403** — a network failure keeps the token
  and falls back to the cached user profile.
- `/auth/reset-password` exists and works but has **no UI**.

---

## 3. Onboarding → the profile that drives everything

Screens (in order): `sports` → `profile` → `goals` → `experience` →
`equipment` → `schedule` → `health` → `assessment` → `generating`.

State accumulates in `onboardingStore` (zustand) and is submitted once by
`POST /onboarding/complete`, which:
1. Upserts `athlete_profiles` (`raw_profile` holds the full submitted object).
2. If `generate_program` **and** generation is enabled → schedules
   `_generate_full_week_background` as a FastAPI background task and returns
   immediately with `program_generating: true`.
3. The `generating` screen polls `GET /programs/active` until the program
   materializes.

Profile fields that matter downstream: `sports`, `goal`, `experience`,
`equipment`, `training_days_per_week`, `preferred_training_days`,
`session_duration_min`, `start_date`, `pain_areas`, `current_injuries`,
`stress_level`, `season_phase`, `city`/`country`.

The 17 supported sports (`app/onboarding/sports.tsx`) map to knowledge-base
keys in `sport_library.ONBOARDING_TO_KB` (e.g. Football → `soccer`, Running →
`running_endurance`).

---

## 4. Workout generation — the deepest subsystem

> **Currently paused.** `WORKOUT_GENERATION_ENABLED=false` makes every
> generation entry point return 503 (or no-op in background paths). The engine
> below is fully built and was working; it is off purely to stop AI spend.

### 4.1 The pipeline

```
profile ──▶ macro plan ──▶ knowledge retrieval ──▶ compaction ──▶ AI call
                                                                    │
                     ┌──────────────────────────────────────────────┘
                     ▼
             schema parse (Pydantic)
                     ▼
             validate_program_quality  ──fail──▶ retry with error feedback
                     ▼
             week trim + persist (program / blocks / workouts)
                     ▼
             grounding + deterministic quality rubric  ──▶ stored on program
```

### 4.2 Step by step (`_create_ai_training_program`)

1. **Base date** — `_program_base_date()` anchors the plan to the user's chosen
   `start_date`; session 1 lands exactly on it, later sessions follow the AI's
   day pattern via `_next_scheduled_date_for_day`.
2. **Macro plan** — `ensure_user_macro_plan()` creates/loads a periodized
   long-term plan from `macro_plan_templates` filtered by sport, goal, level
   and season phase. This is the *direction*; weeks are generated inside it.
3. **Knowledge retrieval** — `build_workout_knowledge_context(db, profile)`
   queries the knowledge base (see §5) for: allowed primary exercises, allowed
   variations, progression paths, recent exercise history, programming rules,
   technical models/errors, mobility/recovery/nutrition, training protocols,
   and sport teaching context.
4. **Compaction** — `compact_context_for_ai()` shrinks that to token-budget
   size, then `athlete_state` and `benchmarks` summaries are attached.
5. **AI call** — `generate_ai_training_program()`:
   - Provider: **Anthropic** if `ANTHROPIC_API_KEY` is set, else **OpenRouter**.
     Model from `WORKOUT_AI_MODEL`. 180s/120s timeouts.
   - The user payload carries: profile brief, knowledge context, session
     blueprints, required JSON schema, schedule rules (day count must match),
     generation scope (`WORKOUT_AI_MAX_WEEKS`, default **1**), and a
     `quality_gate` object of hard requirements.
   - Grounding rule: the model must pick exercises **by `id`** from the allowed
     pool and copy it into `exercise_id`.
6. **Parse & validate** — output must be pure JSON → `ProgramGenerationOutput`
   → `_limit_program_weeks` → `validate_program_quality()`.
7. **Retry** — on validation failure the loop re-calls the model with
   `previous_generation_failed_because` + a compactness instruction, up to
   `WORKOUT_AI_MAX_ATTEMPTS` (default 2).
8. **Persist** — insert `training_programs`, one `program_blocks` doc per
   block, and one `workouts` doc per week-1 session.
9. **Score** — `_program_grounding()` (what % of exercises resolved to library
   ids) and `_score_program_rubric()` (deterministic 0–100 S&C rubric, no extra
   AI call) are stored on the program.

### 4.3 The validator (`validate_program_quality`)

Tiered by default (`WORKOUT_AI_VALIDATION_MODE`): **hard** issues block and
trigger retry, **soft** issues are recorded, **safety** issues always block.

Checks include: generic titles ("full body circuit"), vague exercise names
("cardio", "core work"), lazy fillers (burpees, jumping jacks, random AMRAPs),
missing per-exercise purpose/prescription/rest, missing `sport_transfer` or
`why_this_session`, session duration realism (`_session_duration_cap`),
sport-specificity of transfer language, pain/injury contradictions, and
(optionally) strict library-name matching.

### 4.4 Regeneration / continuation

Two paths, same engine:

- **Automatic**: `POST /workouts/{id}/complete` → background task
  `_maybe_generate_next_block()`. It generates week N+1 only when **every**
  workout of week N is completed, the next week doesn't exist, and the macro
  plan horizon isn't reached. Concurrency-safe via an **atomic claim**
  (`generating_week` field) that prevents double-generation.
- **Manual**: `POST /workouts/generate-next` → `_extend_ai_training_program()`.

Continuation passes a `previous_block_summary` and a `continuation` directive
so the model progresses (progressive overload, accessory rotation, adaptation
to reported RPE/soreness/pain) rather than re-generating from scratch. Every
Nth week (`WORKOUT_AI_DELOAD_EVERY`) is flagged as a **deload** with an
explicit volume-reduction directive.

`POST /workouts/generate-weekly` regenerates week 1 synchronously.

### 4.5 Feedback → adaptation loop

```
complete workout ──▶ user_exercise_history (per-exercise: load, reps, RPE, pain)
                ──▶ update_athlete_state()   (28d completion, 14d RPE/pain,
                                              strength trends, progression signal)
                ──▶ _create_level_assessment_for_user()  (level recommendation)
                ──▶ background: _maybe_generate_next_block()
```

`athlete_states` is then summarized into the *next* generation's context, so
the AI progresses load when RPE is low and completion high, and deloads when
the progression signal says `hold_or_deload`.

### 4.6 Cost & safety guards

| Guard | Mechanism |
|---|---|
| Global kill switch | `WORKOUT_GENERATION_ENABLED` |
| Per-user daily cap | `WORKOUT_AI_DAILY_QUOTA` (default 25/rolling-24h) via `ai_generation_log` (TTL 2 days) |
| Rate limits | SlowAPI: 2/min weekly, 4/min next-block |
| Weeks per call | `WORKOUT_AI_MAX_WEEKS` (default 1) |
| Retry ceiling | `WORKOUT_AI_MAX_ATTEMPTS` (default 2) |

---

## 5. The knowledge base

~3,800 curated documents ingested from sports-science sources, sitting in
Mongo and consumed by retrieval. **Important: this data currently lives only in
the local `test_database`; the Atlas production DB does not have it**, so
retrieval-dependent features degrade in production.

| Collection | Docs (local) | Used for |
|---|---|---|
| `sport_training_rules` | 2,734 | Programming rules per sport |
| `sport_teaching_progressions` | 804 | Skill progressions/drills (13 sports) |
| `sport_skill_assessments` | 177 | Level checkpoints ("ready when…") |
| `sport_roles` | 99 | Position/role context |
| `sport_profiles` | 14 | Sport demand profiles |
| `exercise_library` / `primary_exercise_library` / `exercise_variation_library` | ~1,200 | Exercise pool for generation |
| `exercise_progression_graph` | 606 | Regression/progression edges |
| `training_protocols` | — | Expert rehab/loading protocols (override generic programming) |
| `macro_plan_templates`, `planning_rules`, `competition_week_rules` | — | Periodization |

Coverage by sport (teaching progressions): cycling 204, tennis 130, swimming
124, badminton 117, basketball 33, running 33, soccer 30, volleyball 27, boxing
27, cricket 24, mma 24, wrestling 21, kickboxing 10. **No content**: golf,
hockey, horse riding, hyrox, rugby, table tennis.

Retrieval (`knowledge_retrieval.py`) is keyword/attribute-based by default;
`embeddings.py` adds optional semantic ranking via fastembed
(`EXERCISE_EMBEDDINGS_ENABLED`, **off in production** to keep the free instance
light).

Source JSON for all of this lives in `backend/sport_research/**` and
`backend/data/**`. The one-shot `ingest_*.py` scripts that loaded it were
removed from the tree (recoverable from git history — see README).

---

## 6. Run club & territory game — the live pillar

### 6.1 Recording a run

`app/run/track.tsx`:
1. `expo-location` `watchPositionAsync` (BestForNavigation, 2s / 5m).
2. Points >2m apart append to `gpsPath`; distance accumulates by haversine.
3. A live `MapView` follows the user and draws the route as a coral polyline.
4. Loop detection: start/end within 100m after ≥8 points.
5. **Territory preview**: `distance >= 2.5` → claimed km, else 0.
6. Finish → `POST /terra/runs` with the full GPS path.
   If the user hasn't moved (<2 points or <0.05 km) the app **refuses to save**
   rather than sending a fabricated path.

### 6.2 Server-side run handling (`create_terra_run`)

- Normalizes the path (`_terra_normalize_path` on `model_dump()`ed points).
- Duration from start/end times (or path timestamps).
- **Distance = sum of haversine segments. Never fabricated** — a stationary run
  is 0.0 km.
- `is_loop` if ≥4 points and start≈end.
- **Territory = the run's own distance, claimed only at ≥2.5 km**
  (`TERRITORY_MIN_KM`), else 0. No bounding-box area, no corridor matching.
- Persists to `terra_runs` (incl. `gps_path`, `claimed_territory`), emits a
  `run_completed` activity event, returns
  `territory: {claimed, road_km, threshold_km}` which drives the
  "ROAD CLAIMED!" celebration.

### 6.3 Territory display

`GET /territory/mine` returns every run ≥2.5 km as `{id, path[[lat,lng]],
distance_km, date}` plus `claimed_km` and `road_count`. `TerritoryMap.tsx`
draws those paths as coral polylines over Apple Maps.

> Known limitation: territory is **per-run with no dedup** — running the same
> road twice counts twice. Chosen deliberately ("permanent, simplest").

### 6.4 Clubs, leaderboards, activity

- **Clubs**: create/join (`run_clubs`, `run_club_memberships`), public clubs
  join instantly, private ones create a `pending` membership for admin
  approval. Members are stored **both** as a `member_ids` array on the club and
  as membership rows — see §9 for the integrity risk this creates.
- **Leaderboards**: club-in-city, city-vs-city, country-vs-country, and
  club-member; all aggregate `terra_runs` by period (week/month/all).
- **Activity feed** (`club_activity_events`, TTL 30 days): auto-emitted on
  `run_completed`, `member_joined`, `club_created`, `territory_captured`.
- **Stats**: `/terra/stats` (totals + 7-day history), `/profile/stats`
  (streak, totals), `/runs/stats`.

---

## 7. Other live features

- **Nutrition** (`app/nutrition`): photo → `POST /meals/analyze` → AI vision
  (OpenRouter, `MEAL_AI_MODEL`) returns items + macros → `meals`,
  `nutrition_targets`; daily summary drives the Home nutrition card.
- **Health**: injuries (log/resolve, `injury_logs`), benchmarks
  (`user_benchmarks` — 1RMs, CMJ, hop LSI, feed straight into generation),
  biology (`health_metrics`), strain (`/health/strain`, computed from workout
  durations over 7 days). The `/health` **screen exists but nothing navigates
  to it**.
- **Calendar**: per-day meals / workouts / moods.
- **Analytics**: workout + food tabs (sleep tab removed).
- **Education**: recovery / strain / biology articles.
- **Sport tab**: currently reads `GET /lessons`, and the `lessons` collection
  is **empty** — so the tab renders nothing. This is what the sport-library
  rebuild replaces.

---

## 8. Data model — what is actually stored

70 collections. The ones that carry real user data:

**Identity & profile**: `users` (email, bcrypt hash, `profile`, `is_admin`),
`otps` (TTL), `athlete_profiles` (`raw_profile` = full onboarding payload).

**Training**: `training_programs` (status, goal, sports, `current_week`,
`macro_plan_id`, `profile_snapshot`, `generation` metadata, quality report),
`program_blocks`, `workouts` (the unit the app renders — title, category,
duration, `exercises`, `scheduled_date`, `week_number`, `session_number`,
`completed`, `adaptation`, `session_plan`, `user_feedback`),
`workout_sessions`, `exercise_results`, `user_exercise_history` (per-set
truth: load, reps, RPE, pain), `user_level_assessments`, `user_benchmarks`,
`macro_plans`, `athlete_states`.

**Running/social**: `terra_runs` (distance, duration, `gps_path`,
`territory_captured`, `claimed_territory`, `is_loop`, date), `run_clubs`,
`run_club_memberships`, `terra_reflections`, `club_activity_events` (TTL 30d),
`terra_training_plans`.

**Health/nutrition**: `meals`, `nutrition_targets`, `health_metrics`,
`injuries`, `injury_logs`, `quick_logs` (**now read-only — nothing writes to
it**, see §9), `moods`.

**Ops**: `ai_generation_log` (TTL 2d, quota), `job_status`,
`sport_library_progress` (new).

The remaining ~30 are the read-only knowledge base (§5).

All collections and indexes are created idempotently by
`ensure_database_schema()` on **every startup** — a fresh database needs no
seeding for the app to run.

---

## 9. Findings — issues, dead code, risks

### Fixed during this audit
- Removed dead frontend: `HomeCard/` suite (8 files, 671 lines, zero imports),
  `OnboardingUI.tsx` (434 lines, superseded by `CoachOnboarding`),
  `analytics/recovery-detail.tsx`, `src/data/mockHomeData.ts`.
- Removed 111 lines of orphaned sleep/feed helpers from `helpers.py`.
- Removed stale root files: `sftcinfo.md` (described the deleted SFTC/coach/
  sleep product), `creation1.json` (unreferenced).
- Gitignored `.DS_Store` / `.pytest_cache`.

### Open — correctness / integrity
1. **Club membership has two sources of truth** — `run_clubs.member_ids`
   (array, updated read-modify-write) *and* `run_club_memberships` rows, with
   **no transaction**. Concurrent joins can lose a member and drift
   `member_count`. Fix: atomic `$addToSet`/`$pull`, treat the memberships
   collection as authoritative.
2. **`quick_logs` is written by nothing** but still read in 4 places
   (readiness/sleep-quality inputs, AI context). Those inputs now silently
   evaluate as empty. Decide: delete the read paths, or add a writer.
3. **Knowledge base is not in Atlas.** Production retrieval returns empty
   context, so if generation is re-enabled in prod it will be far weaker than
   locally. Needs a migration/seed step before unpausing.
4. **Territory double-counts** repeated roads (deliberate, but worth revisiting
   when leaderboards matter).

### Open — dead / unreachable
- **18 endpoints have no frontend caller**: `/athlete/profile`,
  `/athlete/level-assessment`, `/auth/reset-password`, `/health/metrics`,
  `/library/summary`, `/macro-plan/*`, `/program/summary`, `/terra/vault`,
  `/terra/leaderboard/{global,friends}`, `/terra/clubs/{id}/{feed,members}`,
  `/workouts/{generate-weekly,generate-next,generate-status,recommended}`,
  `/sport-library*`. Several are intentional (generation is paused; sport
  library is mid-build); `/terra/vault`, `/terra/leaderboard/friends` and
  `/program/summary` look like genuine leftovers.
- **`/health` screen is unreachable** — 530 lines, functional, but nothing
  navigates to it.
- **`app/sport/lesson.tsx`** targets the empty `lessons` collection; it will be
  replaced by the sport-library rebuild.
- **`job_status` collection + `/workouts/generate-status/{job_id}`** are
  vestiges of an ARQ worker that no longer exists (generation is inline now).

### Open — operational
- Render free tier **sleeps after 15 min**; first request costs ~50s. Warm
  latency measured at ~300 ms from India (US region) — a Mumbai host would be
  ~40 ms.
- Frontend has **no automated tests**; backend has 47 (contract-level).
- `frontend/app/(tabs)/run.tsx` is 1,383 lines carrying four tabs, three modals
  and ~15 fetches — the clearest refactor candidate.

---

## 10. Configuration reference

| Variable | Purpose |
|---|---|
| `MONGO_URL`, `DB_NAME` | Database (Atlas in prod) |
| `JWT_SECRET` | Token signing — changing it logs everyone out |
| `ALLOWED_ORIGINS` | CORS allowlist |
| `WORKOUT_GENERATION_ENABLED` | Global generation kill switch (**currently false**) |
| `WORKOUT_AI_MODEL`, `_MAX_TOKENS`, `_MAX_WEEKS`, `_MAX_ATTEMPTS`, `_DAILY_QUOTA`, `_DELOAD_EVERY`, `_STRICT_LIBRARY_MATCHES`, `_CONTINUATION_ATTEMPTS` | Generation tuning |
| `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY` | AI providers (Anthropic preferred) |
| `MEAL_AI_MODEL` | Meal photo analysis |
| `EXERCISE_EMBEDDINGS_ENABLED` | Semantic retrieval (off in prod) |
| `RESEND_API_KEY`, `RESEND_FROM` | OTP email (preferred transport) |
| `SMTP_*`, `INFO_EMAIL_*` | SMTP fallback for OTP |
| `SENTRY_DSN` | Optional error monitoring |
| `EXPO_PUBLIC_BACKEND_URL` | Baked into release builds only |

Deployment specifics live in `DEPLOY.md`; `render.yaml` is the Render blueprint.
