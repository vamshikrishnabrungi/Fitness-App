resource "google_monitoring_notification_channel" "operations_email" {
  display_name = "Runlete operations email"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
  force_delete = false
}

resource "google_monitoring_uptime_check_config" "api" {
  display_name = "${local.name} public API"
  timeout      = "10s"
  period       = "60s"

  monitored_resource {
    type = "uptime_url"
    labels = {
      host       = var.domain
      project_id = var.project_id
    }
  }

  http_check {
    path         = "/healthz"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  content_matchers {
    content = "ok"
    matcher = "CONTAINS_STRING"
  }
}

resource "google_monitoring_alert_policy" "api_uptime" {
  display_name = "${local.name} API unavailable"
  combiner     = "OR"
  severity     = "CRITICAL"
  notification_channels = [
    google_monitoring_notification_channel.operations_email.name,
  ]

  conditions {
    display_name = "Uptime checks failing"
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.check_id=\"${google_monitoring_uptime_check_config.api.uptime_check_id}\""
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      duration        = "180s"
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_TRUE"
      }
      trigger {
        count = 1
      }
    }
  }
}

resource "google_monitoring_alert_policy" "pubsub_queue_age" {
  display_name = "${local.name} worker queue age"
  combiner     = "OR"
  severity     = "WARNING"
  notification_channels = [
    google_monitoring_notification_channel.operations_email.name,
  ]

  conditions {
    display_name = "Oldest unacked message exceeds five minutes"
    condition_threshold {
      filter          = "resource.type=\"pubsub_subscription\" AND metric.type=\"pubsub.googleapis.com/subscription/oldest_unacked_message_age\" AND resource.label.project_id=\"${var.project_id}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 300
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
      trigger {
        count = 1
      }
    }
  }
}

resource "google_billing_budget" "monthly" {
  count           = var.billing_account == "" ? 0 : 1
  billing_account = var.billing_account
  display_name    = "${local.name} monthly budget"

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget_usd)
    }
  }

  budget_filter {
    projects = ["projects/${data.google_project.current.number}"]
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.75
  }
  threshold_rules {
    threshold_percent = 0.9
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  all_updates_rule {
    monitoring_notification_channels = [google_monitoring_notification_channel.operations_email.name]
    disable_default_iam_recipients   = false
  }
}
