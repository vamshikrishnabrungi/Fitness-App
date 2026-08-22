locals {
  common_runtime_env = {
    ENVIRONMENT                 = var.environment
    GOOGLE_CLOUD_PROJECT        = var.project_id
    GOOGLE_CLOUD_REGION         = var.region
    CLOUD_SQL_INSTANCE          = google_sql_database_instance.postgres.connection_name
    DATABASE_USER               = google_sql_user.app.name
    DATABASE_NAME               = google_sql_database.runlete.name
    REDIS_URL                   = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
    RAW_ACTIVITY_BUCKET         = google_storage_bucket.buckets["raw-activity"].name
    IMPORT_BUCKET               = google_storage_bucket.buckets["imports"].name
    NUTRITION_IMAGE_BUCKET      = google_storage_bucket.buckets["food-images"].name
    EXPORT_BUCKET               = google_storage_bucket.buckets["exports"].name
    VALHALLA_GRAPH_BUCKET       = google_storage_bucket.buckets["valhalla-graphs"].name
    KMS_KEY_NAME                = google_kms_crypto_key.health.id
    OPENAI_WORKOUT_MODEL        = "gpt-4o"
    OPENAI_FOOD_MODEL           = "gpt-4o"
    VALHALLA_URLS_JSON          = jsonencode({ for key, rule in google_compute_forwarding_rule.valhalla : key => "http://${rule.ip_address}:8002" })
    TRAINING_GENERATION_ENABLED = "true"
    ALLOWED_ORIGINS             = "https://${var.admin_domain},https://${var.domain}"
  }
  common_secret_env = {
    DATABASE_PASSWORD = "database-password"
    JWT_SECRET        = "jwt-secret"
    OTP_PEPPER        = "otp-pepper"
  }
  optional_secret_env = {
    OPENAI_API_KEY      = "openai-api-key"
    RESEND_API_KEY      = "resend-api-key"
    MAPBOX_PUBLIC_TOKEN = "mapbox-token"
    SENTRY_DSN          = "sentry-dsn"
    EXPO_ACCESS_TOKEN   = "expo-access-token"
  }
}

resource "google_cloud_run_v2_service" "api" {
  name                = "${local.name}-api"
  location            = var.region
  deletion_protection = var.environment == "production"
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account                  = google_service_account.api.email
    timeout                          = "300s"
    max_instance_request_concurrency = 40

    scaling {
      min_instance_count = var.environment == "production" ? 2 : 0
      max_instance_count = var.api_max_instances
    }

    vpc_access {
      network_interfaces {
        network    = google_compute_network.main.name
        subnetwork = google_compute_subnetwork.main.name
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.api_image
      ports {
        container_port = 8080
      }
      resources {
        limits   = { cpu = "2", memory = "2Gi" }
        cpu_idle = true
      }

      dynamic "env" {
        for_each = local.common_runtime_env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = merge(local.common_secret_env, local.optional_secret_env)
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.runtime[env.value].secret_id
              version = "latest"
            }
          }
        }
      }

      startup_probe {
        http_get {
          path = "/healthz"
        }
        initial_delay_seconds = 2
        timeout_seconds       = 2
        period_seconds        = 5
        failure_threshold     = 12
      }

      liveness_probe {
        http_get {
          path = "/healthz"
        }
        timeout_seconds   = 2
        period_seconds    = 30
        failure_threshold = 3
      }
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_service" "worker" {
  name                = "${local.name}-worker"
  location            = var.region
  deletion_protection = var.environment == "production"
  ingress             = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.worker.email
    timeout         = "900s"

    scaling {
      min_instance_count = 0
      max_instance_count = var.worker_max_instances
    }

    vpc_access {
      network_interfaces {
        network    = google_compute_network.main.name
        subnetwork = google_compute_subnetwork.main.name
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image   = var.api_image
      command = ["uvicorn"]
      args    = ["backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
      ports {
        container_port = 8080
      }
      resources {
        limits   = { cpu = "2", memory = "4Gi" }
        cpu_idle = true
      }

      dynamic "env" {
        for_each = local.common_runtime_env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = merge(local.common_secret_env, local.optional_secret_env)
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.runtime[env.value].secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service" "admin" {
  name                = "${local.name}-admin"
  location            = var.region
  deletion_protection = var.environment == "production"
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.admin.email
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
    containers {
      image = var.admin_image
      ports {
        container_port = 8080
      }
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
    }
  }
}

resource "google_cloud_run_v2_job" "migrate" {
  name                = "${local.name}-migrate"
  location            = var.region
  deletion_protection = var.environment == "production"

  template {
    task_count = 1
    template {
      service_account = google_service_account.api.email
      timeout         = "900s"
      max_retries     = 0

      vpc_access {
        network_interfaces {
          network    = google_compute_network.main.name
          subnetwork = google_compute_subnetwork.main.name
        }
        egress = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = var.api_image
        command = ["alembic"]
        args    = ["-c", "alembic.ini", "upgrade", "head"]

        resources {
          limits = { cpu = "1", memory = "1Gi" }
        }

        dynamic "env" {
          for_each = local.common_runtime_env
          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = merge(local.common_secret_env, local.optional_secret_env)
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = google_secret_manager_secret.runtime[env.value].secret_id
                version = "latest"
              }
            }
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image]
  }
}

resource "google_cloud_run_v2_service_iam_member" "lb_api" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "lb_admin" {
  name     = google_cloud_run_v2_service.admin.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "pubsub_worker" {
  name     = google_cloud_run_v2_service.worker.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub.email}"
}
