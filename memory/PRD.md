# SFTC Fitness App — PRD

## Problem statement
Replace the rule-only backend with a real AI-driven coaching engine (Claude
Sonnet 4.5 via Emergent Universal Key) and finish the run-club + territory
features. Keep the existing API contracts so the Expo frontend keeps working.

## Architecture (Jan 2026)

```
/app/backend/
├── server.py                     # thin app, includes legacy + new routers
├── helpers.py                    # legacy helpers (kept for compatibility)
├── models.py                     # pydantic models
├── db_setup.py                   # indexes/collections
├── core/
│   ├── config.py                 # env vars, AI model ids, tuning constants
│   ├── db.py                     # shared Mongo client
│   ├── security.py               # JWT + get_current_user
│   └── run_helpers.py            # run aggregation, club totals/leaderboards
├── ai/
│   ├── client.py                 # LlmChat factory + robust JSON parser
│   └── workout_ai.py             # Claude-driven program generation + fallback
├── territory/
│   ├── h3_grid.py                # H3 cell conversion, polygons, bbox query
│   ├── anticheat.py              # GPS speed/teleport/duration validation
│   └── claim.py                  # ownership + takeover + GeoJSON export
└── routers/
    ├── workouts.py               # /workouts/*, /onboarding/complete
    ├── runs.py                   # /terra/runs, /terra/stats, /runs/stats
    ├── clubs.py                  # /terra/clubs/* (incl. detail / leave / members / territory)
    └── territory.py              # /territory/{me,cells,leaderboard,peaks/me}
```

## What's been implemented (2026-05-29)

### AI workout generation (Claude Sonnet 4.5)
- `POST /api/onboarding/complete` and `POST /api/workouts/generate-weekly` now
  call Claude Sonnet 4.5 through `emergentintegrations` + Emergent LLM key.
- The full athlete profile feeds the prompt: primary/secondary goals, sport
  + role, competition level + season phase, experience, equipment, training
  location, days/week, session length, preferred days, pain areas, injuries,
  age, height/weight, fitness assessment (pushups/pullups/squats/plank/run pace).
- Plans materialise into a `training_programs` doc, `program_blocks`, and one
  `workouts` doc per session (4 weeks × 4-6 sessions).
- If the LLM is unavailable / parse fails, deterministic rules-engine
  fallback runs automatically.

### Run clubs (full CRUD + territory)
- Existing endpoints kept: create, my, city, join, members leaderboard, city
  leaderboard.
- **New:** detail (`GET /terra/clubs/{id}`), members list
  (`GET /terra/clubs/{id}/members`), leave (`POST .../leave`), delete (owner),
  shared territory GeoJSON (`GET .../territory`).

### Territory (Uber H3, resolution 9 ≈ 174 m hexes)
- Every GPS path is converted to an ordered set of H3 cells (with gap-filling
  via `h3.grid_path_cells`).
- Cells become rows in `territory_cells` with `owner_id`, `owner_name`,
  `takeovers`, `claim_history`. Same-cell visits by another user trigger a
  takeover.
- `POST /terra/runs` now returns `{cells, cells_claimed, cells_taken_over,
  cells_retained, territory_geojson, claim: {...}, anti_cheat: {...}}`.
- New endpoints:
  - `GET /api/territory/me` — my owned cells (GeoJSON)
  - `GET /api/territory/cells?south=&west=&north=&east=` — city-map battlefield view
  - `GET /api/territory/leaderboard?city=` — top holders
  - `GET /api/territory/peaks/me` — runs with significant elevation gain (trekking)

### Anti-cheat
- Min 5 GPS points, ≥60 s duration, ≥0.2 km distance.
- Reject avg speed > 8 m/s for runs (5 m/s for treks).
- Reject any single GPS segment with implied speed > 30 m/s (teleport).
- Invalid runs are persisted but claim NO cells.

## Test credentials
See `/app/memory/test_credentials.md`.

## Backlog / Not yet built
- P1: Replace meal/coach/journal AI calls with the same Claude-via-Emergent
  client (currently still on OpenAI fallback inside server.py).
- P1: Frontend integration — add a map view (react-native-maps or
  mapbox/maplibre-react-native) and render `/territory/cells` + per-run
  `territory_geojson`.
- P2: Real club shared-territory ownership (currently we union member cells
  for display; cell ownership is still per-user).
- P2: Trekking-specific endpoint with peak naming and elevation profile.
- P2: Club invite codes / private join flow exposed to UI.
- P3: Move the remaining legacy handlers (meals, sleep, health, journal,
  coach) into modules.
