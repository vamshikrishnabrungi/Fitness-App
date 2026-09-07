# Runlete staging and production release checklist

Use this checklist for every GCP release. The deployment workflow is manual and
environment-protected; completing the code checks does not authorize a deploy.

## One-time environment bootstrap

- [ ] Separate GCP project, billing account and GCS OpenTofu state bucket exist.
- [ ] DNS control is available for the API and Admin Studio domains.
- [ ] OpenTofu foundation has been applied with production-grade IAP membership.
- [ ] GitHub Environment contains `GCP_PROJECT_ID`,
  `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOY_SERVICE_ACCOUNT` and
  `API_BASE_URL`; the production environment also contains `EXPO_TOKEN`.
- [ ] `iap_jwt_audience` matches the Admin API backend-service audience and
  every Admin Studio operator has both IAP access and an assigned database role.
- [ ] Mapbox, Resend, APNs/FCM, Expo/EAS and optional Sentry credentials are
  present in their intended secret stores.
- [ ] Launch-region OSM input and matching graph share the same source version.
- [ ] Cloud SQL backup, PITR, deletion protection and alert delivery are verified.

## Before dispatch

- [ ] Release commit is reviewed and present on `main` for production.
- [ ] Repository CI is green and generated OpenAPI/client files are current.
- [ ] `training_generation_enabled` remains `false` unless an approved immutable
  catalogue release has passed every automated evidence and release gate.
- [ ] `tofu plan` has been reviewed for the selected environment and contains no
  unexpected replacement, IAM broadening, deletion or secret change.
- [ ] API and Admin image repository names match `runlete-<environment>`.
- [ ] Database backup/PITR timestamp and rollback owner are recorded.
- [ ] Release operator, incident channel and operational alert destination are active.

## Automated workflow sequence

1. Validate clean database migrations, audit dependencies and run backend production tests.
2. Typecheck, lint and export the Expo client.
3. Lint and build Admin Studio.
4. Format and validate OpenTofu.
5. Authenticate through GitHub OIDC—never a long-lived service-account key.
6. Build immutable API/Admin images in Cloud Build.
7. Update and execute the migration Cloud Run job before traffic promotion.
8. Export Terraform-owned Cloud Run definitions; deploy worker, API and Admin
   sequentially, waiting for each rollout and checking API readiness.
9. Dispatch the separate mobile production workflow only after the backend
   release is stable; EAS builds signed binaries and submits them to both stores.

## Post-release verification

- [ ] Migration job completed once with no retry.
- [ ] API `/healthz` and public TLS/Cloud Armor path are healthy.
- [ ] Worker `/healthz`, Pub/Sub push authentication and queue age are healthy.
- [ ] Admin Studio is reachable only through IAP and an approved principal.
- [ ] OTP request/verify, refresh rotation and logout pass a staging smoke test.
- [ ] Signed/resumable activity upload and asynchronous processing complete.
- [ ] A known GPS fixture preserves device distance and produces expected metrics.
- [ ] Territory tile session and one launch-region tile render successfully.
- [ ] Notifications, dead-letter inspection and operational alerts are observable.
- [ ] Error rate, latency, instance count, database connections and Redis health are
  watched during the release window.

## Rollback

Application rollback uses the last known-good Cloud Deploy/Cloud Run revision.
Do not automatically downgrade the database. If a migration is not backward
compatible, stop promotion and follow its reviewed forward-fix or restore plan.
Never delete Cloud SQL, buckets, KMS keys, graph artifacts or Terraform state as
part of application rollback.

Record the failed revision, migration head, image digests, rollback revision,
operator and incident timeline before closing the release.
