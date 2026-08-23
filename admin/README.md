# Runlete Admin Studio

The Admin Studio is the controlled authoring and operations interface for Runlete's PostgreSQL knowledge platform. It never edits published content in place and never acts as a runtime workout library.

## Local development

```bash
npm install
npm run dev
```

Set `VITE_API_URL` when the API is not served from the same origin. The local Studio opens directly without a login when the backend runs with `ENVIRONMENT=development` and `ADMIN_STUDIO_OPEN_ACCESS=true`.

Open access is deliberately rejected when `ENVIRONMENT=production`. A production deployment must add an authenticated service boundary before the Studio is exposed publicly.

## Roles

- `content_editor`: authors drafts, imports source material, records reviews, validates simulations, and prepares release manifests.
- `content_publisher`: reads knowledge and activates, retires, or rolls back validated immutable releases.
- `moderator`: handles competition flags and appeals.
- `platform_admin`: has all administrative capabilities, including roles, OSM graphs, feature flags, audit history, and failed-job replay.

The API enforces these boundaries. UI navigation is also role-aware.

## Workspaces

- Taxonomy, methods, media, evidence, sport demands, quality priorities, and prescription rules.
- Session recipe, program-phase, and weekly-template builders.
- Human review ledger, representative-athlete simulation, coverage/conflict reports, workbook reconciliation, and release management.
- Feature flags, minimum-client rules, audit history, OSM/Valhalla graph registration, processing health, retries, moderation, and role assignment.

## Verification

```bash
npm run build
```

Repository acceptance additionally runs the PostgreSQL migration check, production backend tests, OpenAPI generation, and mobile TypeScript contract checking.
