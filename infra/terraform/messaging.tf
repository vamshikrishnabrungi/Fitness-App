resource "google_pubsub_topic" "topics" {
  for_each = local.topics
  name     = "${local.name}-${each.value}"
  labels   = local.labels
}

resource "google_pubsub_topic" "dead_letter" {
  for_each = local.topics
  name     = "${local.name}-${each.value}-dead-letter"
  labels   = local.labels
}

resource "google_pubsub_topic_iam_member" "dead_letter_publisher" {
  for_each = local.topics
  topic    = google_pubsub_topic.dead_letter[each.value].name
  role     = "roles/pubsub.publisher"
  member   = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription_iam_member" "source_subscriber" {
  for_each     = local.topics
  subscription = google_pubsub_subscription.push[each.value].name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription" "dead_letter_inspection" {
  for_each                   = local.topics
  name                       = "${local.name}-${each.value}-dead-letter-inspection"
  topic                      = google_pubsub_topic.dead_letter[each.value].id
  message_retention_duration = "1209600s"
  retain_acked_messages      = true
}

resource "google_pubsub_subscription" "push" {
  for_each                   = local.topics
  name                       = "${local.name}-${each.value}-worker"
  topic                      = google_pubsub_topic.topics[each.value].id
  ack_deadline_seconds       = 600
  message_retention_duration = "604800s"

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter[each.value].id
    max_delivery_attempts = 10
  }

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.worker.uri}/internal/pubsub/${each.value}"
    oidc_token {
      service_account_email = google_service_account.pubsub.email
      audience              = google_cloud_run_v2_service.worker.uri
    }
  }
}

resource "google_cloud_scheduler_job" "outbox" {
  name      = "${local.name}-outbox-recovery"
  region    = var.region
  schedule  = "* * * * *"
  time_zone = "UTC"

  http_target {
    uri         = "${google_cloud_run_v2_service.worker.uri}/internal/maintenance/outbox"
    http_method = "POST"
    oidc_token {
      service_account_email = google_service_account.pubsub.email
      audience              = google_cloud_run_v2_service.worker.uri
    }
  }
}

resource "google_cloud_scheduler_job" "account_deletions" {
  name      = "${local.name}-account-deletions"
  region    = var.region
  schedule  = "17 * * * *"
  time_zone = "UTC"

  http_target {
    uri         = "${google_cloud_run_v2_service.worker.uri}/internal/maintenance/account-deletions"
    http_method = "POST"
    oidc_token {
      service_account_email = google_service_account.pubsub.email
      audience              = google_cloud_run_v2_service.worker.uri
    }
  }
}

resource "google_cloud_scheduler_job" "push_receipts" {
  name      = "${local.name}-push-receipts"
  region    = var.region
  schedule  = "*/2 * * * *"
  time_zone = "UTC"

  http_target {
    uri         = "${google_cloud_run_v2_service.worker.uri}/internal/maintenance/push-receipts"
    http_method = "POST"
    oidc_token {
      service_account_email = google_service_account.pubsub.email
      audience              = google_cloud_run_v2_service.worker.uri
    }
  }
}

resource "google_cloud_scheduler_job" "idempotency_retention" {
  name      = "${local.name}-idempotency-retention"
  region    = var.region
  schedule  = "23 * * * *"
  time_zone = "UTC"

  http_target {
    uri         = "${google_cloud_run_v2_service.worker.uri}/internal/maintenance/idempotency-retention"
    http_method = "POST"
    oidc_token {
      service_account_email = google_service_account.pubsub.email
      audience              = google_cloud_run_v2_service.worker.uri
    }
  }
}
