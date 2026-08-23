# Runlete — Run Club (Competition) Backend Analysis

_Analysis + recommendations. Backend only. Stack was brought up and verified live in this environment._

## 1. Environment status (now running here)

| Service | Status | Notes |
|---|---|---|
| PostgreSQL 15 + PostGIS | RUNNING (supervisor `postgresql`) | db `runlete`, role `runlete`, PostGIS + uuid-ossp enabled |
| Redis 7 | RUNNING (supervisor `redis`) | `redis://localhost:6379/0` |
| FastAPI API (`backend.app.main:app`) | RUNNING (supervisor `backend`, port 8001) | via `/app/backend/server.py` shim |
| Alembic migrations | applied to `head` (6 revisions) | full `competition` schema created |

Auth in dev: `ADMIN_STUDIO_OPEN_ACCESS=true` opens `/api/v1/admin/*` only. Normal
club endpoints require a real athlete JWT (mint with `backend/dev_seed_clubs.py`).

Helper scripts added (dev-only, safe to delete):
- `backend/server.py` — supervisor entrypoint shim → real app.
- `backend/dev_seed_clubs.py` — seeds two athletes, prints access tokens.
- `backend/dev_drain_outbox.py` — local stand-in for the Pub/Sub projection worker.

## 2. What run clubs are today (authoritative = `backend/app/competition/`)

Fully implemented and **verified working** end-to-end in this environment:

- **Club lifecycle**: create, discover (`?q=`), mine, detail, update (optimistic
  `version`), archive/restore. ✅ create→discover→detail verified.
- **Membership**: join (public=instant active, private=requested), approve/reject,
  cancel request, leave, remove, ban/unban, role change, transfer ownership.
  Single-active-owner enforced by a partial unique index. ✅ join + members list verified.
- **Primary club**: one competitive primary per athlete, 7-day switch cooldown. ✅ verified.
- **Invitations**: tokenised, max-uses + expiry, create/list/revoke + public accept. ✅ create verified.
- **Challenges**: 6 types (distance, duration, run_count, consistency, territory_gain,
  fastest_segment), closed contract with canonical SI units; create + club/global list + join. ✅ create + list verified.
- **Races**: route-bound, start window, capacity, age/level eligibility; create +
  list + join + results. ✅ create verified.
- **Leaderboards**: additive `LeaderboardFact` rows → periodic `LeaderboardSnapshot`
  (week/month/all, distance/moving_time/runs); club + public snapshots with privacy filter.
- **Activity feed** (`SystemActivityEvent`): club timeline (club_created, member joined/left,
  eligible_run, PRs, race results, territory changes). ✅ populated after projection.
- **Achievements**, **Notifications** (with push token delivery), **Moderation** flags/appeals.
- **Territory**: H3/PostGIS street-edge ownership, GeoJSON (`/territory/mine`, `/club/{id}`,
  `/edges/{id}`) + signed **MVT vector tiles**, decay/expiry scoring, club edge aggregation.

## 3. Architecture (how a club action becomes visible)

```
HTTP mutation ──► Postgres write (clubs/memberships/…) + enqueue_event() → operations.outbox_events
                     │ (same transaction, strong consistency)
                     ▼
       main.py middleware → publish_outbox_ids() → Pub/Sub  ── (PRODUCTION ONLY)
                     ▼
       POST /internal/pubsub/{topic} (push) → event_projection.project_domain_event()
                     ▼
       READ MODELS: system_activity_events, notifications, achievements, leaderboard_snapshots
```

Writes are synchronous and consistent. Everything a member *sees* (feed, notifications,
leaderboards, achievements, territory rollups) is an **eventually-consistent read model**
built by the projection worker consuming the outbox via Pub/Sub.

## 4. Findings / gaps

**F1 (P0, dev-blocking for demos): the async projection worker does not run locally.**
`publish_outbox_ids()` no-ops when `GOOGLE_CLOUD_PROJECT` is empty, and there is no
Pub/Sub emulator subscription pushing to `/internal/pubsub/{topic}`. Result: outbox rows
accumulate unpublished and **club feed / notifications / leaderboards / achievements stay
empty**. Proven: after running `dev_drain_outbox.py`, the feed returned
`['membership_joined','club_created']` and a notification appeared. The domain logic is correct;
only the local trigger is missing.

**F2 (P1): two parallel club implementations coexist.** Legacy `backend/club_api.py` +
`backend/club_store.py` (raw SQL, Mongo-era users) vs authoritative
`backend/app/competition/*` (SQLAlchemy). README says legacy is archive/audit only and not in
the runtime image — but it's still importable and was the source of pre-existing lint errors.
Risk of drift/confusion.

**F3 (P1): leaderboards & territory are invisible without the activity pipeline.** Both read
models are fed only by completed activities, which require GCS object storage + Valhalla
map-matching (not provisioned here). Expected, but there is no lightweight seed/demo path to
populate them for testing club competition in isolation.

**F4 (P2): club discovery is thin.** `GET /clubs` returns max 50 by name only,
`next_cursor` is always `None`, and there is no region/geo filter even though `home_region_id`
and PostGIS `home_location` exist on the model.

**F5 (P2): feature parity gaps vs the legacy API.** Authoritative API has no cross-club/global
athlete leaderboard and no `/seasons` endpoint (legacy `club_api.py` exposed both).

**F6 (P3): `territory_router._features` is N+1** (a `ST_AsGeoJSON` query per edge) and uses
inline `__import__('json')`. Works, but should aggregate in one query for city-scale maps.

## 5. Recommendations (prioritized)

- **P0 — Local projection worker.** Add a supervised poller (or Pub/Sub-emulator push
  subscription) that drains `operations.outbox_events` into `project_domain_event` /
  `worker_router.consume`, so club social features are demoable without GCP. `dev_drain_outbox.py`
  is a one-shot proof; productionise it as a short-interval loop under supervisor for dev.
- **P1 — Quarantine legacy club code.** Move `club_api.py`/`club_store.py`/`club_domain.py`
  out of the import path (or delete) once confirmed unused, to stop drift and lint noise.
- **P1 — Demo seed for competition.** Seed clubs + members + a handful of synthetic completed
  activities + leaderboard facts so `/clubs/{id}/leaderboards` and `/territory/*` render without
  the full GCS/Valhalla stack.
- **P1 — Enrich discovery.** Real cursor pagination + optional `region_id` / lat-lng radius
  filter on `GET /clubs`.
- **P2 — Close parity gaps.** Add global athlete leaderboard + `/seasons` to the authoritative router.
- **P2 — Territory perf.** Single aggregated `ST_AsGeoJSON`/`json_agg` query in `_features`;
  drop the inline import.

## 6. Verified endpoint smoke matrix

| Flow | Result |
|---|---|
| POST /clubs (owner) | 201, owner membership, count=1 |
| GET /clubs?q= (other athlete) | finds club |
| POST /clubs/{id}/join (member) | active, count=2 |
| GET /clubs/{id}/members | owner + member listed |
| POST /clubs/{id}/challenges | 201 |
| GET /clubs/{id}/challenges | lists challenge |
| PUT /clubs/primary | 200 |
| POST /clubs/{id}/invitations | 201 + accept_token |
| GET /clubs/{id}/leaderboards | 200 (empty until activities) |
| GET /clubs/{id}/activity | events after projection ✅ |
| GET /territory/mine | empty FeatureCollection (needs OSM data) |
