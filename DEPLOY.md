# Runlete deployment

Runlete production targets GCP. Render, AWS and MongoDB are not deployment
targets for the new runtime.

## Topology

`infra/terraform` provisions:

- Global external Application Load Balancer, managed TLS and Cloud Armor.
- Cloud Run API, worker and Admin Studio services.
- Regional-HA private Cloud SQL PostgreSQL 16/PostGIS with PITR.
- Memorystore Redis Standard Tier.
- Pub/Sub push subscriptions, retry and dead-letter topics.
- Regional private Cloud Storage buckets with signed direct uploads.
- Secret Manager, Cloud KMS, Artifact Registry and service accounts.
- Regional Compute Engine Valhalla pools and graph artifact storage.
- Cloud Scheduler recovery/retention jobs and Cloud Monitoring.

The default write region is `europe-west1`; staging and production use separate
GCP projects.

## Deployment order

1. Supply a staging GCP project, billing/IAM access and DNS names.
2. Copy the environment example under `infra/terraform`, set project/domain and
   image variables, then run `tofu plan` and review it.
3. Apply staging foundation/data resources.
4. Build and publish the backend and Admin containers through Cloud Build.
5. Run `alembic upgrade head` against the exact staging Cloud SQL database.
6. Register and build launch-region OSM/Valhalla artifacts from the same PBF
   versions; run graph, GPS and privacy canaries before activation.
7. Configure Mapbox, APNs/FCM, Resend and optional Sentry secrets.
8. Build signed EAS development/release clients and validate background GPS,
   health permissions, interrupted imports and push delivery on real devices.
9. Run load, backup restore, PITR and dead-letter replay exercises.
10. Repeat the reviewed plan/apply process for production and use canary Cloud
    Run revisions before shifting traffic.

The GitHub deployment workflow reruns database migrations, backend tests,
dependency audits, frontend type/lint/export, Admin lint/build and OpenTofu
validation before it authenticates to GCP. Production dispatches are accepted
only from `main` and must also pass the configured GitHub Environment approvals.
The GCP workflow then deploys worker, API and Admin in order and waits for every
rollout. Mobile store delivery is a separate manual, production-protected EAS
workflow so a backend release cannot accidentally publish a client binary.

The operator checklist is [`deploy/RELEASE_CHECKLIST.md`](deploy/RELEASE_CHECKLIST.md).

## Required external inputs

- GCP staging/production project IDs and deployment IAM.
- Domain/DNS control.
- Mapbox public mobile token and native SDK download token.
- Apple APNs and Android Firebase/FCM configuration.
- Resend key and verified sending domain.
- Expo/EAS and store signing access.
- Optional Sentry DSN/release token.
- Legal privacy/terms text and operational alert destination.

The OpenAI API key is stored in Secret Manager. OSM and Valhalla require no API key.

## Safety gates

Never enable a territory region until its PostGIS claim edges and Valhalla graph
share a source version and pass matching/privacy tests. Never put secrets in the
repository or mobile bundle except Mapbox’s permitted public token. Do not
connect any MongoDB service: no MongoDB client, migration path or compatibility
runtime is shipped.

More detail: [Runlete final specification](docs/RUNLETE_FINAL.md) and
[infrastructure README](infra/terraform/README.md).
