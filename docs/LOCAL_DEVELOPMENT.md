# Local Runlete development

The API, worker, Pub/Sub subscriber, Redis and Valhalla run on this Mac. Cloud SQL,
Cloud Storage, KMS and Pub/Sub remain hosted in the configured GCP project.
No Cloud Run service is required for this setup.

## Valhalla

Docker runs through Colima. Start the existing runtime and container:

```bash
colima start
docker start runlete-valhalla
curl --fail http://127.0.0.1:8002/status
```

The map is a Hyderabad road/path extract bounded by longitude 78.25–78.65 and
latitude 17.20–17.65. Coverage outside that area is not provided. It is an OSM
snapshot downloaded on 2026-09-07, not an automatically updated map. Data is stored
in `/Users/vamshikrishna/runlete-valhalla` outside the repository. Administrative
and timezone databases are disabled for this local walking/running setup.

`backend/.env` contains `VALHALLA_URL=http://127.0.0.1:8002`.

## Application processes

From the repository root, run each command in its own terminal. Stop an existing
process before restarting another copy on the same port.

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001 2>&1 | tee -a /tmp/runlete-backend.log
```

```bash
.venv/bin/python -m uvicorn backend.app.worker_main:app --host 127.0.0.1 --port 8003 2>&1 | tee -a /tmp/runlete-worker.log
```

```bash
.venv/bin/python -m backend.tools.local_worker 2>&1 | tee -a /tmp/runlete-events.log
```

The subscriber forwards events from the nine `runlete-development-*-local` pull
subscriptions to the loopback worker. It acknowledges successful jobs and retries
failures, and runs outbox publication recovery every minute. It intentionally
refuses to start outside the development environment. It does not run production
scheduler jobs such as account deletion or notification receipt sweeps.

```bash
cd frontend
EXPO_PUBLIC_BACKEND_URL=http://127.0.0.1:8001 npx expo start --dev-client --host localhost --port 8081
```

Redis should respond to `redis-cli ping`. Cloud credentials are loaded through the
app-specific `GOOGLE_APPLICATION_CREDENTIALS` path in `backend/.env`.

## Logs

```bash
docker logs -f runlete-valhalla
tail -f /tmp/runlete-backend.log /tmp/runlete-worker.log /tmp/runlete-events.log
```

Valhalla routing does not itself populate the PostGIS street-edge/territory
catalogue. A real recorded-run test is still required to validate the complete
activity/territory pipeline against the database's active graph data.
