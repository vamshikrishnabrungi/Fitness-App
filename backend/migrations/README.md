# Runlete database migrations

Alembic is the canonical migration runner:

```bash
alembic -c alembic.ini upgrade head
```

- `001_postgis_foundation.sql` installs PostGIS and compatibility geometry
  tables.
- `002_run_club_competition_platform.sql` installs the authoritative relational
  club, activity-attribution, OSM edge, territory, challenge, race, leaderboard,
  moderation, audit, notification, outbox, and idempotency model.

Docker Compose mounts these files only to bootstrap a brand-new local volume.
Always run Alembic against an existing or managed database.

Before cutover, reconcile legacy Mongo club documents in dry-run mode:

```bash
python3 -m backend.migrate_run_clubs_postgres \
  --report run-club-migration-report.json
```

Review every repaired owner, duplicate membership, generated legacy UUID, and
slug conflict. Then apply:

```bash
python3 -m backend.migrate_run_clubs_postgres \
  --report run-club-migration-report.json \
  --apply
```

The migration preserves valid UUIDs, creates exactly one owner membership per
club, reconciles `member_ids`, assigns one initial primary club per athlete, and
records primary history. Competition seasons and club territory intentionally
start at cutover; do not import ambiguous historical multi-club contribution.

Historical activity metrics are separately audited and recomputed from original
GPS samples:

```bash
python3 -m backend.migrate_legacy_runs
python3 -m backend.migrate_legacy_runs --apply
python3 -m backend.backfill_geospatial
```

OSM edges are never loaded through the old HTTP street-edge endpoint. Use
`backend.osm_graph_manager` as documented in `docs/RUNNING_PLATFORM.md`.
