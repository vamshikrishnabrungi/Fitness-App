# Cloud Run release manifests

Terraform owns the Cloud Run service configuration. The deployment workflow exports each
existing service with `gcloud run services describe --format=export`, replaces only the
container image with a Cloud Deploy image placeholder, and writes the result to
`deploy/rendered/`. Cloud Deploy then promotes that complete manifest. This prevents an image
release from dropping Terraform-managed environment variables, secrets, networking, probes,
scaling, or service identities.

Files under `deploy/rendered/` are ephemeral CI artifacts and must not be committed.

Use [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) before dispatch, during smoke
verification and for rollback ownership.
