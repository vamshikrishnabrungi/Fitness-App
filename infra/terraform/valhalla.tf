resource "google_compute_firewall" "valhalla" {
  name          = "${local.name}-valhalla-internal"
  network       = google_compute_network.main.name
  direction     = "INGRESS"
  source_ranges = [google_compute_subnetwork.main.ip_cidr_range]
  target_tags   = ["runlete-valhalla"]
  allow {
    protocol = "tcp"
    ports    = ["8002"]
  }
}

resource "google_compute_firewall" "valhalla_health_checks" {
  name          = "${local.name}-valhalla-health-checks"
  network       = google_compute_network.main.name
  direction     = "INGRESS"
  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
  target_tags   = ["runlete-valhalla"]
  allow {
    protocol = "tcp"
    ports    = ["8002"]
  }
}

resource "google_compute_health_check" "valhalla" {
  name                = "${local.name}-valhalla"
  timeout_sec         = 5
  check_interval_sec  = 30
  healthy_threshold   = 2
  unhealthy_threshold = 3
  http_health_check {
    port         = 8002
    request_path = "/status"
  }
}

resource "google_compute_instance_template" "valhalla" {
  for_each     = var.valhalla_regions
  name_prefix  = "${local.name}-valhalla-${each.value}-"
  machine_type = var.valhalla_machine_type
  tags         = ["runlete-valhalla"]

  disk {
    source_image = "projects/cos-cloud/global/images/family/cos-stable"
    auto_delete  = true
    boot         = true
    disk_size_gb = 50
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id
  }

  metadata = {
    startup-script = templatefile("${path.module}/valhalla-startup.sh.tftpl", {
      graph_bucket = google_storage_bucket.buckets["valhalla-graphs"].name
      graph_object = lookup(var.valhalla_graph_objects, each.value, "graphs/${each.value}/current.tar.gz")
    })
  }

  service_account {
    email  = google_service_account.worker.email
    scopes = ["cloud-platform"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_region_instance_group_manager" "valhalla" {
  for_each           = var.valhalla_regions
  name               = "${local.name}-valhalla-${each.value}"
  region             = var.region
  base_instance_name = "valhalla-${each.value}"
  target_size        = var.valhalla_enabled ? 1 : 0

  version {
    instance_template = google_compute_instance_template.valhalla[each.value].id
  }

  named_port {
    name = "http"
    port = 8002
  }

  auto_healing_policies {
    health_check      = google_compute_health_check.valhalla.id
    initial_delay_sec = 900
  }
}

resource "google_compute_region_backend_service" "valhalla" {
  for_each              = var.valhalla_regions
  name                  = "${local.name}-valhalla-${each.value}"
  region                = var.region
  protocol              = "TCP"
  load_balancing_scheme = "INTERNAL"
  health_checks         = [google_compute_health_check.valhalla.id]

  backend {
    group = google_compute_region_instance_group_manager.valhalla[each.value].instance_group
  }
}

resource "google_compute_forwarding_rule" "valhalla" {
  for_each              = var.valhalla_regions
  name                  = "${local.name}-valhalla-${each.value}"
  region                = var.region
  load_balancing_scheme = "INTERNAL"
  ip_protocol           = "TCP"
  ports                 = ["8002"]
  network               = google_compute_network.main.id
  subnetwork            = google_compute_subnetwork.main.id
  backend_service       = google_compute_region_backend_service.valhalla[each.value].id
}
