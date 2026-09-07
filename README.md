# Runlete

Runlete is a subscription athlete platform with an Expo mobile app, modular
FastAPI backend, PostgreSQL/PostGIS authority, GCP event processing and a
separate operational Admin Studio.

The mobile app uses four primary tabs: Home, Train, Run and Profile. The current
release includes identity/privacy, run recording and imports,
activity analytics, routes, segments, heatmaps, safety, nutrition, health,
clubs, territory, challenges, races, leaderboards, notifications and
moderation. User posts, comments, kudos, follows, chat and messaging are not
part of the product.

Sport-knowledge records already stored in PostgreSQL are retained for possible
future use, but there is no mobile Sport tab or public sport-content route.
Training knowledge/content is being completed separately. Deterministic
training generation remains disabled by default.

## Repository

- `backend/app/` — authoritative modular FastAPI runtime.
- `backend/alembic/` — frozen PostgreSQL/PostGIS baseline.
- `frontend/` — Expo Router mobile/web client.
- `admin/` — operational Admin Studio.
- `infra/terraform/` — GCP OpenTofu infrastructure.
- `tests/production/` — production-domain test suite.
- `docs/RUNLETE_FINAL.md` — authoritative product and architecture specification.

## Local setup

Requirements: Python 3.12+, Node 20+, Google Cloud CLI and OpenTofu. Local
application processes connect to managed GCP services; there is no local
database, local object-store fallback, or storage-emulator runtime. Sensitive
payload encryption uses Cloud KMS outside automated tests.

```bash
gcloud auth application-default login
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-runtime.txt pytest

cp backend/.env.example backend/.env
# Fill CLOUD_SQL_INSTANCE, DATABASE_*, REDIS_URL, buckets and secrets.
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

## Configuration

Backend variables are documented in `backend/.env.example`. Development,
staging and production all use Cloud SQL through the authenticated connector,
managed Redis, Pub/Sub, Cloud Storage and regional Valhalla. A direct database
URL is accepted only as `TEST_DATABASE_URL` under `ENVIRONMENT=test`.

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

See [deployment](DEPLOY.md) and the
[final specification](docs/RUNLETE_FINAL.md) for GCP activation, OSM/Valhalla
and external credential gates.
