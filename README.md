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

## Environment

Backend `.env` values:

- `MONGO_URL`
- `DB_NAME`
- `JWT_SECRET`
- `OPENAI_API_KEY` or `EMERGENT_LLM_KEY`

Frontend `.env` values:

- `EXPO_PUBLIC_BACKEND_URL`

## Run

Backend:

```bash
cd backend
uvicorn server:app --reload --port 8001
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

The app is still in prototype form. A few screens depend on compatibility shims in the backend, and the largest remaining gap is the set of journal, Terra, and advanced coach flows.
