locals {
  name = "runlete-${var.environment}"
  labels = {
    application = "runlete"
    environment = var.environment
    managed_by  = "terraform"
  }
  services = toset([
    "artifactregistry.googleapis.com",
    "batch.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudbuild.googleapis.com",
    "clouddeploy.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudscheduler.googleapis.com",
    "compute.googleapis.com",
    "iamcredentials.googleapis.com",
    "iap.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
    "redis.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
  ])
  topics  = toset(["activity", "territory", "training", "nutrition", "health", "club", "competition", "notifications", "maintenance"])
  buckets = toset(["raw-activity", "imports", "food-images", "exports", "exercise-media", "osm-inputs", "valhalla-graphs"])
  external_secret_values = {
    openai-api-key    = var.openai_api_key
    resend-api-key    = var.resend_api_key
    mapbox-token      = var.mapbox_public_token
    sentry-dsn        = var.sentry_dsn
    expo-access-token = var.expo_access_token
  }
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "services" {
  for_each           = local.services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "main" {
  name                    = local.name
  auto_create_subnetworks = false
  depends_on              = [google_project_service.services]
}

resource "google_compute_subnetwork" "main" {
  name                     = "${local.name}-${var.region}"
  region                   = var.region
  network                  = google_compute_network.main.id
  ip_cidr_range            = "10.42.0.0/20"
  private_ip_google_access = true
}

resource "google_compute_router" "main" {
  name    = local.name
  region  = var.region
  network = google_compute_network.main.id
}

resource "google_compute_router_nat" "main" {
  name                               = local.name
  router                             = google_compute_router.main.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  subnetwork {
    name                    = google_compute_subnetwork.main.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
}

resource "google_compute_global_address" "private_services" {
  name          = "${local.name}-private-services"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_services" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services.name]
}

resource "google_service_account" "api" {
  account_id   = "${local.name}-api"
  display_name = "Runlete API"
}

resource "google_service_account" "worker" {
  account_id   = "${local.name}-worker"
  display_name = "Runlete workers"
}

resource "google_service_account" "admin" {
  account_id   = "${local.name}-admin"
  display_name = "Runlete Admin Studio"
}

resource "google_service_account" "pubsub" {
  account_id   = "${local.name}-pubsub"
  display_name = "Pub/Sub and Scheduler invoker"
}

resource "google_project_iam_member" "api_roles" {
  for_each = toset([
    "roles/cloudkms.cryptoKeyEncrypterDecrypter",
    "roles/cloudsql.client",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/pubsub.publisher",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectUser",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_roles" {
  for_each = toset([
    "roles/cloudkms.cryptoKeyEncrypterDecrypter",
    "roles/cloudsql.client",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "pubsub_token_creator" {
  project    = var.project_id
  role       = "roles/iam.serviceAccountTokenCreator"
  member     = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  depends_on = [google_project_service.services]
}

resource "google_service_account_iam_member" "api_sign_blob" {
  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.api.email}"
}

resource "google_kms_key_ring" "main" {
  name     = local.name
  location = var.region
}

resource "google_kms_crypto_key" "health" {
  name            = "health-envelope"
  key_ring        = google_kms_key_ring.main.id
  rotation_period = "7776000s"
  lifecycle {
    prevent_destroy = true
  }
}

resource "random_password" "database" {
  length  = 32
  special = false
}

resource "random_password" "jwt" {
  length  = 64
  special = false
}

resource "random_password" "otp" {
  length  = 64
  special = false
}

resource "google_secret_manager_secret" "runtime" {
  for_each  = toset(["database-password", "jwt-secret", "otp-pepper", "openai-api-key", "resend-api-key", "mapbox-token", "sentry-dsn", "expo-access-token"])
  secret_id = "${local.name}-${each.value}"
  replication {
    auto {}
  }
  labels = local.labels
}

resource "google_secret_manager_secret_version" "jwt" {
  secret      = google_secret_manager_secret.runtime["jwt-secret"].id
  secret_data = random_password.jwt.result
}

resource "google_secret_manager_secret_version" "otp" {
  secret      = google_secret_manager_secret.runtime["otp-pepper"].id
  secret_data = random_password.otp.result
}

resource "google_secret_manager_secret_version" "external" {
  for_each    = local.external_secret_values
  secret      = google_secret_manager_secret.runtime[each.key].id
  secret_data = each.value == null ? "" : each.value
}
