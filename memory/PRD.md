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

### 2026-08-23 (cont. 2) — Real map stack (OSM ingestion) end-to-end
- Reality: this pod has NO Docker/Valhalla; Valhalla (C++ tile builder) cannot be stood
  up here. OSM ingestion (osmium/shapely/PostGIS) IS pure-python and runs here.
- **Fixed a real schema bug (F8):** `StreetEdge.osm_way_id/from_node_id/to_node_id` were
  `INTEGER` (int32); real OSM node IDs are 64-bit and overflow. Widened to `BigInteger` in
  `maps/models.py` + new migration `20260823_07_street_edge_bigint.py` (applied).
- Ingested REAL OpenStreetMap Monaco (`/tmp/monaco.osm.pbf`, 674 KB) via the production
  pipeline → **5,794 street_edges**, graph activated (`backend/dev_ingest_osm.py`).
- Built `backend/dev_run_on_real_streets.py`: a dev PostGIS proximity map-matcher (stands in
  for Valhalla) that snaps a real GPS trace to ingested edges, then drives the REAL
  `project_activity_territory`. A simulated run along "Boulevard du Jardin Exotique"
  map-matched 310 real edges, **claimed 262**.
- Verified through the real API: `GET /territory/mine` returns 262 real streets as GeoJSON;
  `POST /territory/tile-session` + `GET /territory/tiles/{z}/{x}/{y}.mvt` returns an 8 KB
  Mapbox Vector Tile (content-type application/vnd.mapbox-vector-tile). Backend is fully
  ready to feed a Mapbox/MapLibre map.
- Live run map (Mapbox in Expo) remains a FRONTEND follow-up; requires MAPBOX_PUBLIC_TOKEN.

### 2026-08-23 (cont. 3) — Elevation pipeline upgrade (barometer/DEM + sustained-climb)
- Reviewed an external "flip distance authority" analysis: its headline claim was WRONG
  about this repo (device-smoothed GPS is already authoritative; map-matching is
  territory-only; tolerance logic already prevents "numbers changed"). The one valid,
  not-yet-done item was elevation — built it.
- New `activities/elevation.py`: `sustained_elevation_gain` (forward-fill -> centred
  moving-average smoothing -> hysteresis threshold, default 3 m) + source resolver
  `resolve_elevation` with priority device_barometer -> dem_lookup -> gps_altitude ->
  unavailable. `DemProvider` protocol with `NullDemProvider` and Open-Elevation/OpenTopoData
  compatible `HttpDemProvider` (env `DEM_PROVIDER_URL`, graceful failure).
- Wired into `activities/pipeline.py` (`_replace_metrics` now sets real `elevation_gain_m`
  + `elevation_source`); replaced the naive per-sample >=1 m GPS summation in
  `process_samples`; added `barometric_altitude` to `Sample` and all decoders
  (imports.py, worker_router.py, cleaned-store `_sample_dict`); added `dem_provider_url`
  to config.
- Verified (`backend/dev_elevation_check.py`): flat road + GPS noise -> old naive reported
  80 m fake climb, new sustained = 0 m; real ~50 m hill -> 44 m (conservative); barometer
  and DEM sources chosen correctly; GPS fallback works. Backend healthy.

### 2026-08-23 (cont. 4) — Run club FRONTEND verified + emoji wiring completed
- Frontend is Expo Router (RN + TS) with a mature Nike-style theme; run-club screens
  already fully built: clubs list/discovery/search, create, detail with 7 tabs
  (overview/leaderboard/territory/challenges/races/activity/members), join/primary/
  challenge+race join, invitation accept, admin, moderation, notifications, plus
  Mapbox territory/live-run/route map components.
- Verified the full frontend<->backend CONTRACT against the live API: every screen's
  reads match the responses (items-wrapping, challenge `metric`+`progress`+`is_joined`,
  members `athlete.name`, activity `event_type/occurred_at/payload`, leaderboard rows
  include `is_me` injected by the router, `/challenges|races/{id}/join` work).
- Fixed the one genuine gap: club `emoji` was picked in the create UI but never sent or
  stored. Wired end-to-end: Club model column + migration `20260823_08`, ClubCreate/
  ClubUpdate/ClubView, service view, create.tsx payload; regenerated `src/api/generated.ts`
  from live OpenAPI. Verified round-trip (create with 🔥 -> persisted -> returned).
- Frontend typecheck: only 1 error project-wide and it is PRE-EXISTING/unrelated
  (`/(tabs)/sport` route in home tab). Run-club screens + emoji change are type-clean.
- Set `frontend/.env` with placeholders: EXPO_PUBLIC_BACKEND_URL (empty -> relative
  /api/v1 via ingress on web) and EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN (placeholder).
- NOT built (both layers): the NEW leaderboard scopes (solo/global, city, city-vs-city,
  country-vs-country, city club ranking) — needs backend region-hierarchy endpoints first.

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
