resource "google_compute_security_policy" "edge" {
  name = "${local.name}-edge"

  rule {
    action   = "throttle"
    priority = 1000
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 1200
        interval_sec = 60
      }
    }
  }

  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow after WAF and throttle"
  }
}

resource "google_compute_region_network_endpoint_group" "api" {
  name                  = "${local.name}-api-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.api.name
  }
}

resource "google_compute_region_network_endpoint_group" "admin" {
  name                  = "${local.name}-admin-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.admin.name
  }
}

resource "google_compute_backend_service" "api" {
  name                  = "${local.name}-api"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  security_policy       = google_compute_security_policy.edge.id
  backend {
    group = google_compute_region_network_endpoint_group.api.id
  }
}

resource "google_compute_backend_service" "admin" {
  name                  = "${local.name}-admin"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  security_policy       = google_compute_security_policy.edge.id
  backend {
    group = google_compute_region_network_endpoint_group.admin.id
  }
  iap {
    enabled              = true
    oauth2_client_id     = var.iap_oauth_client_id
    oauth2_client_secret = var.iap_oauth_client_secret
  }
}

# Admin API traffic uses the same canonical FastAPI service, but its dedicated
# backend is IAP-protected. Mobile API traffic remains on the non-IAP backend and
# is still protected by Runlete access tokens and domain authorization.
resource "google_compute_backend_service" "admin_api" {
  name                  = "${local.name}-admin-api"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  security_policy       = google_compute_security_policy.edge.id
  backend {
    group = google_compute_region_network_endpoint_group.api.id
  }
  iap {
    enabled              = true
    oauth2_client_id     = var.iap_oauth_client_id
    oauth2_client_secret = var.iap_oauth_client_secret
  }
}

locals {
  iap_bindings = merge(
    { for member in var.iap_access_members : "ui:${member}" => { member = member, backend = google_compute_backend_service.admin.name } },
    { for member in var.iap_access_members : "api:${member}" => { member = member, backend = google_compute_backend_service.admin_api.name } },
  )
}

resource "google_iap_web_backend_service_iam_member" "admin_access" {
  for_each            = local.iap_bindings
  project             = var.project_id
  web_backend_service = each.value.backend
  role                = "roles/iap.httpsResourceAccessor"
  member              = each.value.member
}

resource "google_compute_url_map" "https" {
  name            = "${local.name}-https"
  default_service = google_compute_backend_service.api.id

  host_rule {
    hosts        = [var.domain]
    path_matcher = "api"
  }
  host_rule {
    hosts        = [var.admin_domain]
    path_matcher = "admin"
  }
  path_matcher {
    name            = "api"
    default_service = google_compute_backend_service.api.id
  }
  path_matcher {
    name            = "admin"
    default_service = google_compute_backend_service.admin.id
    path_rule {
      paths   = ["/api", "/api/*"]
      service = google_compute_backend_service.admin_api.id
    }
  }
}

resource "google_compute_managed_ssl_certificate" "domains" {
  name = "${local.name}-tls"
  managed {
    domains = [var.domain, var.admin_domain]
  }
}

resource "google_compute_target_https_proxy" "https" {
  name             = "${local.name}-https"
  url_map          = google_compute_url_map.https.id
  ssl_certificates = [google_compute_managed_ssl_certificate.domains.id]
}

resource "google_compute_global_address" "edge" {
  name = "${local.name}-edge"
}

resource "google_compute_global_forwarding_rule" "https" {
  name                  = "${local.name}-https"
  ip_address            = google_compute_global_address.edge.address
  port_range            = "443"
  target                = google_compute_target_https_proxy.https.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

resource "google_compute_url_map" "http_redirect" {
  name = "${local.name}-http-redirect"
  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "http" {
  name    = "${local.name}-http"
  url_map = google_compute_url_map.http_redirect.id
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "${local.name}-http"
  ip_address            = google_compute_global_address.edge.address
  port_range            = "80"
  target                = google_compute_target_http_proxy.http.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}
