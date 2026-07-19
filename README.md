# SFTC Fitness App

Monorepo with an Expo frontend and a FastAPI backend.

## Layout

- `frontend/`: Expo Router app
- `backend/`: FastAPI API and MongoDB persistence
- `tests/`: Python smoke tests and helper checks

## Prerequisites

- Node.js 20+
- Python 3.11+
- MongoDB running locally or reachable through `MONGO_URL`

## Setup

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-runtime.txt
```

Frontend:

```bash
cd frontend
npm install
```

## Seed data (run once on a fresh database)

`ensure_database_schema` creates the (empty) collections automatically at startup, but the
decision-layer protocols, macro-plan templates, and semantic embeddings must be loaded once.
From the repo root, with the backend venv active:

```bash
python -m backend.seed_all
```

This is idempotent (safe to re-run) and:

1. creates all collections + indexes,
2. seeds `training_protocols` (evidence-based rehab/loading/testing protocols),
3. seeds the research-backed `macro_plan_templates`,
4. builds exercise embeddings for semantic retrieval — this needs `fastembed`
   (already in `requirements-runtime.txt`; the first run downloads a ~130MB model).
   Semantic retrieval degrades gracefully to keyword matching if `fastembed` is absent
   or `EXERCISE_EMBEDDINGS_ENABLED=false`.

The exercise/sport knowledge itself was produced separately by a one-shot
`backend/ingest_*.py` pipeline (19 scripts) that read source books into MongoDB.
Those scripts have already run and are not part of the app, so they were removed
from the tree to keep `backend/` navigable. They remain in git history — recover
with:

    git show a103d69:backend/ingest_<name>.py > backend/ingest_<name>.py
    git show a103d69 --stat -- backend/ingest_    # list all 19

Note they resolve paths via `Path(__file__).resolve().parents[1]`, so they expect
to sit in `backend/`, and they need the (gitignored) source books to re-run.

## Environment

Backend `backend/.env` values:

- `MONGO_URL`, `DB_NAME`
- `JWT_SECRET`
- `ANTHROPIC_API_KEY` — workout/coach generation
- `OPENROUTER_API_KEY` — meal analysis
- `WORKOUT_AI_MODEL` (default `claude-haiku-4-5-20251001`), `MEAL_AI_MODEL`

Optional workout-engine knobs (sensible defaults if unset):

- `WORKOUT_AI_MAX_TOKENS`, `WORKOUT_AI_MAX_ATTEMPTS`, `WORKOUT_AI_CONTINUATION_ATTEMPTS`
- `WORKOUT_AI_VALIDATION_MODE` (`tiered` | `strict` | `off`), `WORKOUT_AI_MAX_SESSION_MIN`
- `MACRO_AI_TUNING` (default on), `MACRO_AI_MODEL`
- `EXERCISE_EMBEDDINGS_ENABLED` (default on), `EMBEDDING_MODEL`

Frontend `frontend/.env` values:

- `EXPO_PUBLIC_BACKEND_URL` — must point at the machine's LAN IP (e.g.
  `http://192.168.x.x:8001`) for a phone to reach the backend; `localhost` only works on the
  host machine's web build.

## Run

Backend (bind to `0.0.0.0` so phones on the LAN can reach it):

```bash
cd backend
uvicorn backend.server:app --reload --host 0.0.0.0 --port 8001
```

Frontend:

```bash
cd frontend
npm run start
```

## Checks

Frontend:

```bash
cd frontend
npm run typecheck
npm run lint
npm run check
```

Backend:

```bash
cd backend
python3 -m py_compile server.py
pytest
```

## Notes

The app is still in prototype form. The largest remaining gaps are the journal, Terra, and
advanced coach flows. The workout-generation engine is documented inline; briefly: rules pick a
macro template (AI tunes it) → two-stage retrieval feeds exercises + protocols + the athlete's
tested baselines → the AI writes each week's structure → a tiered validator repairs/scores it →
weekly feedback (RPE/pain/completion/strength trends) drives the next block.
