# Runlete — PRD / Working Memory

## Product
Subscription athlete platform: Expo mobile app + modular FastAPI backend on
PostgreSQL/PostGIS, Redis, GCP (Pub/Sub, Cloud Storage, KMS), Valhalla map-matching,
plus a separate Admin Studio. Run clubs = the "competition" domain.

## Authoritative architecture (Jan 2026)
- Runtime backend: `backend/app/` (SQLAlchemy async, Alembic). NOT the default Mongo stack.
- Legacy `backend/*.py` (club_api/club_store/club_domain, Mongo-era) = archive/audit only,
  not in the runtime image.
- Run clubs live in `backend/app/competition/`:
  router.py, public_router.py, invitation_router.py, territory_router.py, service.py,
  policies.py, leaderboards.py, progress.py, event_projection.py, projection.py, models.py.
- Consistency model: synchronous Postgres writes + `operations.outbox_events`; async read
  models (feed, notifications, leaderboards, achievements, territory) built by the projection
  worker (`/internal/pubsub/{topic}` → `event_projection.project_domain_event`) fed by Pub/Sub.

## Environment brought up in this pod (2026-08-23)
- PostgreSQL 15 + PostGIS, Redis 7, and the API (port 8001) all run under supervisor.
- `/etc/supervisor/conf.d/runlete_services.conf` keeps Postgres + Redis alive.
- `/app/backend/server.py` shim lets the read-only supervisor `backend` program serve
  `backend.app.main:app`.
- `backend/.env` created with local Postgres/Redis config.
- Alembic migrated to head; full `competition` schema present.

## Session log
### 2026-08-23 — Run club analysis (backend only)
- Fixed 11 pre-existing repo lint errors (undefined `json`, trailing semicolons,
  duplicate dict keys) blocking pre-completion checks.
- Stood up the real Postgres/Redis/FastAPI stack locally and verified the full club
  lifecycle end-to-end (create/discover/join/members/challenge/invite/primary/feed).
- Delivered full analysis + recommendations in `/app/RUNCLUB_ANALYSIS.md`.

### 2026-08-23 (cont.) — Territory-first work (backend)
- Product decisions locked: street-based territory (not circles); NO minimum claim
  distance; leaderboard scopes wanted = solo/global, city, city-vs-city, country-vs-country,
  city club ranking; run city/country derived from GPS location; keep territory rules as-is;
  live-map Strava accuracy stays out of scope (frontend + Mapbox).
- Removed the hard 2.5 km territory min-distance gate in `activities/pipeline.py`
  `_replace_matches` (coverage/confidence/anti-cheat gates retained).
- **Fixed a real production bug (F7)** in `competition/projection.py`
  `project_activity_territory`: `SELECT ... FOR UPDATE` over a LEFT OUTER JOIN to
  `matched_edge_traversals` → Postgres "FOR UPDATE cannot be applied to the nullable side
  of an outer join". Changed to `.with_for_update(of=TerritoryScore)`. This bug broke
  territory projection for ANY qualifying run on real Postgres.
- Built `backend/dev_territory_harness.py`: seeds synthetic OSM region + street edges +
  matched traversals and drives the real engine. Verified claim → defend → takeover →
  decay → expire at both athlete and club level with correct decay math.

## Key findings (see RUNCLUB_ANALYSIS.md for detail)
- F1 (P0): async projection worker not running locally → club feed/notifications/
  leaderboards/achievements empty until outbox is drained. Domain logic is correct
  (proven via `backend/dev_drain_outbox.py`). Only the local trigger is missing.
- F2 (P1): duplicate legacy vs authoritative club code → drift risk.
- F3 (P1): leaderboards/territory need the activity pipeline (GCS + Valhalla); no
  lightweight demo-seed path.
- F4/F5 (P2): thin club discovery (no pagination/geo); no global leaderboard or /seasons
  in authoritative API.
- F6 (P3): `territory_router._features` N+1 + inline import.

## Backlog / next tasks
- P0: supervised local outbox drainer / Pub/Sub-emulator push subscription.
- P1: quarantine or remove legacy club modules; competition demo-seed script.
- P1: club discovery pagination + region/geo filter.
- P2: global leaderboard + /seasons endpoints; territory GeoJSON perf.

## Dev helpers
- `backend/dev_seed_clubs.py` — seed athletes + print JWTs.
- `backend/dev_drain_outbox.py` — drain club/competition outbox → read models.
- Credentials/usage: `/app/memory/test_credentials.md`.
