# Runlete GCP infrastructure

This OpenTofu root provisions one staging or production project in `europe-west1`: private VPC, regional Cloud SQL PostgreSQL 16, Redis Standard HA, Cloud Run API/worker/Admin services, Pub/Sub with dead letters, signed-upload Cloud Storage buckets, KMS, Secret Manager, Valhalla managed instance groups, Artifact Registry, monitoring and GitHub workload identity.

Use a separate GCP project and state bucket for each environment. The bootstrap project/state bucket and the first deployer identity are intentionally outside this root. Never place secret values in `.tfvars`; Terraform creates database/JWT/OTP secrets, while Mapbox, Resend and optional Sentry secret versions are populated out-of-band.

```sh
tofu init -backend-config="bucket=RUNLETE_TF_STATE_BUCKET" -backend-config="prefix=production"
tofu plan -var-file=production.tfvars
tofu apply -var-file=production.tfvars
```

Before apply, enable billing, delegate DNS, publish immutable API/Admin images, configure the IAP OAuth brand/client, and create secret versions for Mapbox, Resend and Sentry. Production deletion protection is enabled for Cloud SQL and Cloud Run.
