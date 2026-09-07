# Runlete — final product and architecture specification

**Status:** authoritative  
**Updated:** 2026-09-04  
**Supersedes:** the historical Runlete analysis, working-memory PRD, run-club
analysis, running-platform note, and activity-metrics ADR.

## 1. Product definition

Runlete is an all-surface running and athlete-development platform delivered as
an Expo React Native application, a modular FastAPI service, and a separate
operational Admin Studio. It supports road, trail, park and track activities,
with manual or sensor-derived treadmill activities treated as a distinct flow.

The running product combines reliable live activity metrics with an edge-based
territory game. A valid run does not depend on a mapped road. Territory is an
optional competitive result produced only where a verified network edge exists.

Current product domains include identity and privacy, activity recording and
imports, analytics, routes and segments, safety, health, nutrition, clubs,
territory, challenges, races, leaderboards, notifications and moderation.
User-authored social posts, comments, kudos, follows, chat and messaging are not
part of the current product.

The mobile navigation has four primary tabs: Home, Train, Run and Profile.
There is no Sport tab and no public sport-knowledge API. Existing sport-content
rows remain preserved in PostgreSQL and may still be maintained through the
role-gated Admin Studio; packaged JSON is not a runtime or bootstrap source.

Training content is administered separately. The released PostgreSQL catalogue
and sport templates define the safe candidate set and prescription bounds. When
onboarding completes, the workout model selects from that bounded set; domain
validation remains authoritative for exercise eligibility, dosage, scheduling,
and athlete safety. The legacy deterministic reference compiler is retained
only for release tooling and compatibility tests, never for API plan creation.

## 2. Non-negotiable activity decision

For native GPS activities, the distance shown live on the device is the final
distance. The mobile recorder calculates it from a lightly smoothed GPS stream.
The backend replays the same versioned rules as confirmation and records the
difference, but it does not replace the number already shown to the athlete.

Imported activities without a device distance may use server-derived metrics.
Treadmill distance must come from manual entry or a supported sensor, never GPS.

Valhalla/OSM map matching is asynchronous and has only two responsibilities:

1. Produce an optional cosmetic road-snapped route for eligible road sections.
2. Produce verified edge traversals for territory scoring.

Matched geometry must never overwrite distance, pace, calories or elevation.

## 3. Activity metric contract

The current contract is `activity-metrics-v1`:

1. Request a GPS fix every 1,000 milliseconds. Preserve original timestamps
   when the operating system batches delivery.
2. Preserve raw latitude, longitude, timestamp, accuracy, altitude and available
   barometric altitude as immutable evidence.
3. Reject invalid coordinates, duplicate or non-increasing timestamps, accuracy
   worse than 100 metres, and jumps faster than 15 metres per second.
4. Smooth accepted coordinates in timestamp order. Clamp accuracy to 1–100 m and
   use update factor `clamp(1 - accuracy / 140, 0.35, 0.85)`.
5. Sum haversine distance over every accepted smoothed segment. Do not discard a
   valid segment solely because it is shorter than two metres.
6. Derive moving time from the accepted stream and the registered pause policy.
7. Warn when server replay differs by more than `max(25 m, 2% of device
   distance)`. Preserve device distance as final.
8. Derive live/final pace and calories from the same final distance.

Any change requires a new metric version, matching mobile/backend fixtures, and
an explicit reprocessing policy.

## 4. Elevation and surfaces

Elevation is independent of map matching. Source priority is device barometer,
DEM lookup, GPS altitude, then unavailable. Profiles are smoothed and only
sustained climbs past the configured threshold—three metres by default—count
toward elevation gain. The selected source is stored with the activity.

- **Road:** smoothed GPS metrics; optional cosmetic snap; verified accessible
  edges may claim territory.
- **Trail or park:** smoothed GPS metrics; no forced snap; a real verified path
  edge may claim territory.
- **Track:** smoothed GPS metrics; normal road snapping disabled.
- **Treadmill:** manual/sensor distance only; no GPS territory.

## 5. Activity lifecycle

1. Mobile records and persists raw fixes, smoothed coordinates and live metrics,
   including recovery state for backgrounding or interruption.
2. Evidence uploads through idempotent resumable chunks and signed object URLs.
3. FastAPI validates the upload and stores authoritative activity metadata in
   PostgreSQL/PostGIS while immutable streams remain in Cloud Storage.
4. The worker replays metrics, resolves elevation, applies privacy and anti-cheat
   rules, and optionally invokes road/path matching.
5. Verified traversals feed territory; accepted activity location resolves the
   regional leaderboard identifier without exposing raw coordinates.
6. Transactional outbox events drive notifications, leaderboards, achievements,
   feeds and other read models through Pub/Sub workers.

Historical activities with no resolved region require versioned reprocessing
before they can appear in regional boards.

## 6. Territory and competition

Territory is control of verified street/path edges, not a circle, polygon traced
from raw GPS, or proof that every kilometre maps to a road. There is no arbitrary
minimum-run-distance requirement. Eligibility depends on verified coverage,
matching confidence, running access, privacy, anti-cheat state and activity
visibility.

Control uses confidence, coverage, score age, defence, takeover, decay and
expiry. Athlete and primary-club projections use the same accepted evidence.
Normal clients render signed Mapbox vector tiles; GeoJSON endpoints are bounded
inspection/fallback surfaces.

Competition includes club lifecycle and membership, invitations, challenges,
races, athlete and club leaderboards, city/country comparisons, notifications,
moderation and territory takeover alerts. Mutations are synchronous Postgres
writes; feeds and aggregate projections are eventually consistent read models.

## 7. Security, privacy and resilience

- Native access and refresh tokens use the platform keychain/keystore. Refresh
  is single-flight, tokens rotate, and logout revokes the server session.
- OTP issuance is limited per email, per source-IP hash and globally.
- Authenticated API mutations buffer no more than 2 MiB; larger evidence/media
  uses signed or resumable uploads.
- Raw evidence is immutable. Derived artifacts carry processing versions and can
  be reproduced without rewriting history.
- PostGIS is the durable authority. Redis contains only ephemeral limits, locks
  and caches.
- Privacy zones and activity visibility are applied before public competition
  projections. Regional facts store a resolved identifier, not public GPS.
- Every retryable worker and upload operation is idempotent. Dead-letter and
  replay paths are operational requirements.

## 8. Runtime architecture

- `frontend/`: Expo Router React Native/TypeScript application.
- `backend.app.main:app`: public `/api/v1` FastAPI application; no internal worker
  routes.
- `backend.app.worker_main:app`: private health and `/internal/*` worker surface.
- `backend/app/`: authoritative modular runtime.
- `backend/alembic/`: PostgreSQL 16/PostGIS migration chain.
- `admin/`: operational Admin Studio with role-gated, audited actions.
- `infra/terraform/`: GCP infrastructure.
- `tests/production/`: production-domain automated validation.

Production uses Cloud Run, private Cloud SQL PostgreSQL 16/PostGIS, Memorystore,
Pub/Sub, Cloud Storage, Secret Manager, Cloud KMS, Cloud Armor and regional
Valhalla pools. The worker is internal-only and invoked by its dedicated service
identity. Retired Mongo-era modules are not part of the repository or runtime
inputs and are not runtime authority or part of the production image.

All durable relational and geospatial state is held in Cloud SQL PostgreSQL.
Large binary objects and ingestion artifacts are held in private Cloud Storage,
not on container filesystems. Cloud Run instances have no supported local-data
fallback. Direct database URLs and local envelope encryption exist only in the
isolated automated-test environment.

## 9. Training knowledge boundary

PostgreSQL stores versioned methods, effects, relations, evidence claims,
templates, sport priorities and policies. Imports are previewed and committed
atomically through Admin Studio. Stable codes and immutable versions preserve
provenance.

An import fails when any progression, regression or substitution code cannot be
resolved. The complete imported dataset is reviewed and activated as one
version/hash behind the generator feature gate. Development can enable the
adapter with `TRAINING_GENERATION_ENABLED=true`; production still requires
the normal credential, load, and release checks.

### 9.1 AI training generation contract

The imported training reference system contains 238 stable exercise identities,
112 four-week category/level references, 448 weekly prescriptions, 864
sport/scope/phase/goal priority rows, 117 category-level availability decisions,
11 sport modality policies, eight explicit non-automatic mode fallbacks and 24
scenario overlays. Its exact launch sports are badminton, basketball, boxing,
cricket, cycling, football, MMA, running, swimming, tennis and volleyball.

The athlete input contract must resolve a canonical level, phase and goal; the
exact sport event/role/format scope; availability and duration; equipment and
environment; external load; and unresolved pain state before retrieval.

The generation adapter retrieves the exact priority row and released level
templates, applies sport/scope/mode/equipment/environment gates, and sends the
resulting template blocks, bounded prescriptions, and eligible exercise
catalogue to the constrained workout model. The model selects the methods and
returns one selection for every slot; it cannot invent exercises, identifiers,
dose fields, or extra sessions. Warm-up and cooldown slots are included in the
same packet.

Competition uses one familiar physical-preparation exposure weekly and tapers
volume while retaining the familiar Week-1 intensity and recovery. Readiness 2
reduces category count and volume. Readiness 1, acute illness and unresolved
pain stop ordinary generation. Exact dated hard sport loads require a clear day
of spacing; a weekly summary without exact timing is rejected.

The backend rejects invalid frequency, unsupported dose units, missing
equipment, unresolved pain, unsafe hard-day spacing, session-duration overflow
and missing compatible-category coverage before persistence. Every item stores
its source template/version, method/version, explicit dose, scoped recovery,
safety boundaries, progression gate and regression action. The generation run
stores provider/model metadata, the accepted structured response, input hash,
validation result and complete decision trace.

### 9.2 Current training release status

Local implementation and release verification are complete. The runtime loads
released content only, constrains every model response to that content, and
fails rather than guessing when the model or catalogue cannot produce a safe
plan.

Development generation is enabled in the local environment after the released
training dataset is present. Production activation still requires credential
rotation, environment release checks, and an explicit feature-flag change. This
system is physical preparation, not diagnosis, rehabilitation, medical
clearance, or a claim of independent clinical review.

## 10. Delivery phases and current state

- **Phase 0 — field validation:** code path and synthetic parity tests exist;
  real-device road, trail and track comparison remains a release gate.
- **Phase 1 — recorder:** one-second collection, smoothing, authoritative live
  metrics, recovery persistence and background recording are implemented.
- **Phase 2 — upload/history:** resumable upload, server confirmation and
  local/offline history synchronization are implemented.
- **Phase 3 — elevation:** barometer/DEM/GPS resolution with sustained-climb
  smoothing is implemented; device/DEM field validation remains required.
- **Phase 4 — maps:** Mapbox rendering and asynchronous matching surfaces exist;
  production tokens and regional Valhalla graphs are deployment inputs.
- **Phase 5 — competition:** edge claims, clubs, leaderboards, alerts and
  anti-cheat foundations exist; launch regions require graph/privacy/load canaries.
- **Phase 6 — training:** released-only normalized retrieval, typed prescription
  binding, constrained AI selection, fail-closed validation, generation-run
  observability, semantic hashing and concurrency-safe versioned persistence
  are implemented. Activation remains gated on credential rotation, environment
  release checks and explicit feature-flag authorization.

## 11. Release gates

Before production activation:

1. Run identical known GPS fixtures through mobile and backend implementations.
2. Complete real-device road, trail and track runs and compare live/final values
   with a known course or watch.
3. Validate background recording, interruption recovery, offline upload and
   token rotation on supported iOS and Android versions.
4. Apply every Alembic migration to a clean PostgreSQL 16/PostGIS database.
5. Confirm each territory region's PostGIS edges and Valhalla graph share the
   same source version; pass matching, privacy and anti-cheat canaries.
6. Exercise Pub/Sub retry/dead-letter replay, backup restore and Cloud SQL PITR.
7. Validate Mapbox, APNs/FCM, email delivery, legal text and alert routing.
8. Enable training only after the immutable dataset validator, AI selection
   validation suite, generated-example adversarial evaluation, credential
   rotation, and explicit authorization pass.

Synthetic tests do not replace field validation.

## 12. Authoritative supporting guides

This file owns product and architecture decisions. The following remain
authoritative only for their operational subject:

- [`README.md`](../README.md): repository setup and validation commands.
- [`DEPLOY.md`](../DEPLOY.md): production deployment sequence and external inputs.
- [`infra/terraform/README.md`](../infra/terraform/README.md): infrastructure variables and operations.
- [`tests/load/README.md`](../tests/load/README.md): competition load gate.
- [`admin/README.md`](../admin/README.md) and [`frontend/README.md`](../frontend/README.md): client-specific operation.
