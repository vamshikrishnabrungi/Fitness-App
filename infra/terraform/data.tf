resource "google_sql_database_instance" "postgres" {
  name                = "${local.name}-postgres"
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = true

  settings {
    tier              = var.database_tier
    availability_type = "REGIONAL"
    disk_type         = "PD_SSD"
    disk_size         = 100
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 14
      }
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.main.id
      enable_private_path_for_google_cloud_services = true
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = false
    }

    maintenance_window {
      day          = 7
      hour         = 2
      update_track = "stable"
    }

    user_labels = local.labels
  }

  depends_on = [google_service_networking_connection.private_services]
}

resource "google_sql_database" "runlete" {
  name     = "runlete"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = "runlete_app"
  instance = google_sql_database_instance.postgres.name
  password = random_password.database.result
}

resource "google_secret_manager_secret_version" "database" {
  secret      = google_secret_manager_secret.runtime["database-password"].id
  secret_data = random_password.database.result
}

resource "google_redis_instance" "cache" {
  name               = "${local.name}-redis"
  region             = var.region
  tier               = "STANDARD_HA"
  memory_size_gb     = var.redis_memory_gb
  redis_version      = "REDIS_7_2"
  authorized_network = google_compute_network.main.id
  labels             = local.labels
}

resource "google_storage_bucket" "buckets" {
  for_each                    = local.buckets
  name                        = "${var.project_id}-${var.environment}-${each.value}"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning {
    enabled = contains(["raw-activity", "imports", "osm-inputs", "valhalla-graphs"], each.value)
  }

  dynamic "cors" {
    for_each = contains(["raw-activity", "imports", "exercise-media", "food-images"], each.value) ? [1] : []
    content {
      origin          = ["https://${var.domain}", "https://${var.admin_domain}"]
      method          = ["GET", "HEAD", "PUT"]
      response_header = ["Content-Type", "ETag", "x-goog-generation"]
      max_age_seconds = 3600
    }
  }

  dynamic "lifecycle_rule" {
    for_each = each.value == "food-images" ? [1] : []
    content {
      condition {
        age = 30
      }
      action {
        type = "Delete"
      }
    }
  }

  dynamic "lifecycle_rule" {
    for_each = each.value == "exports" ? [1] : []
    content {
      condition {
        age = 30
      }
      action {
        type = "Delete"
      }
    }
  }

  labels = local.labels
}
