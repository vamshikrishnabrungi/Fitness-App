resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = local.name
  description   = "Immutable Runlete application images"
  format        = "DOCKER"
  labels        = local.labels

  cleanup_policies {
    id     = "retain-recent-releases"
    action = "KEEP"
    most_recent_versions {
      keep_count = 30
    }
  }

  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "2592000s"
    }
  }
}

resource "google_service_account" "deploy" {
  account_id   = "${local.name}-deploy"
  display_name = "Runlete GitHub deployment"
}

resource "google_project_iam_member" "deploy_roles" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/cloudbuild.builds.editor",
    "roles/cloudbuild.builds.builder",
    "roles/clouddeploy.jobRunner",
    "roles/clouddeploy.releaser",
    "roles/logging.logWriter",
    "roles/run.admin",
    "roles/storage.admin",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_service_account_iam_member" "deploy_runtime_accounts" {
  for_each = {
    api    = google_service_account.api.name
    worker = google_service_account.worker.name
    admin  = google_service_account.admin.name
  }
  service_account_id = each.value
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "${local.name}-github"
  display_name              = "Runlete GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "Runlete GitHub repository"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }
  attribute_condition = "assertion.repository == '${var.github_repository}'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_deploy" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}

resource "google_service_account_iam_member" "cloud_deploy_executor" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-clouddeploy.iam.gserviceaccount.com"
}

resource "google_clouddeploy_target" "services" {
  for_each    = toset(["api", "worker", "admin"])
  name        = "${local.name}-${each.value}"
  location    = var.region
  description = "Runlete ${each.value} Cloud Run target"
  labels      = local.labels
  run {
    location = "projects/${var.project_id}/locations/${var.region}"
  }
  execution_configs {
    usages          = ["RENDER", "DEPLOY"]
    service_account = google_service_account.deploy.email
  }
}

resource "google_clouddeploy_delivery_pipeline" "services" {
  for_each    = google_clouddeploy_target.services
  name        = "${local.name}-${each.key}"
  location    = var.region
  description = "Runlete ${each.key} release pipeline"
  labels      = local.labels
  serial_pipeline {
    stages {
      target_id = each.value.name
      profiles  = [each.key]
    }
  }
}
