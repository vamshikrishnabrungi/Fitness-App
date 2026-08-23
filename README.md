# Runlete

Runlete is a subscription athlete platform with an Expo mobile app, modular
FastAPI backend, PostgreSQL/PostGIS authority, GCP event processing and a
separate operational Admin Studio.

The current release includes identity/privacy, run recording and imports,
activity analytics, routes, segments, heatmaps, safety, nutrition, health,
clubs, territory, challenges, races, leaderboards, notifications and
moderation. User posts, comments, kudos, follows, chat and messaging are not
part of the product.

Training knowledge/content is being completed separately. Deterministic
training generation remains disabled by default.

## Repository

- `backend/app/` — authoritative modular FastAPI runtime.
- `backend/alembic/` — frozen PostgreSQL/PostGIS baseline.
- `frontend/` — Expo Router mobile/web client.
- `admin/` — operational Admin Studio.
- `infra/terraform/` — GCP OpenTofu infrastructure.
- `tests/production/` — production-domain test suite.
- `docs/RUNNING_PLATFORM.md` — running/competition architecture and rollout.

Files directly under legacy `backend/` that reference MongoDB or the old AI
planner are archive/audit inputs only. They are not copied into the production
image and are not runtime authority. They remain temporarily because training
content is being handled in a separate task.

## Local setup

Requirements: Python 3.12+, Node 20+, Docker and OpenTofu.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-runtime.txt pytest

docker compose up -d postgis redis pubsub storage
alembic upgrade head
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the mobile client:

```bash
cd frontend
npm install
npm run start
```

Start the Admin Studio:

```bash
cd admin
npm install
npm run dev
```

The optional local Valhalla service downloads a large regional OSM package:

```bash
docker compose --profile geo up -d valhalla
```

## Configuration

Backend variables are documented in `backend/.env.example`. Local defaults use
PostGIS, Redis, the Pub/Sub emulator and the Cloud Storage emulator. Production
uses Cloud SQL, Memorystore, Pub/Sub, Cloud Storage, Cloud KMS, Secret Manager,
the OpenAI Responses API and regional Valhalla pools.

Frontend variables are documented in `frontend/.env.example`. A mobile Mapbox
public token is required to render native maps. Raw GPS and territory never fall
back to client-calculated ownership when Mapbox is unavailable.

## Validation

```bash
python -m pytest -q tests/production

python - <<'PY'
import json
from backend.app.main import app
with open('openapi.json', 'w') as output:
    json.dump(app.openapi(), output, indent=2)
    output.write('\n')
PY

cd frontend
npm run generate:api
npm run typecheck
npm run lint
npx expo export --platform web

cd ../admin
npm run build

cd ../infra/terraform
tofu validate
```

See [deployment](DEPLOY.md) and
[running platform](docs/RUNNING_PLATFORM.md) for GCP activation, OSM/Valhalla
and external credential gates.
