output "api_service_uri" {
  value = google_cloud_run_v2_service.api.uri
}

output "admin_service_uri" {
  value = google_cloud_run_v2_service.admin.uri
}

output "database_connection_name" {
  value = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  value     = google_redis_instance.cache.host
  sensitive = true
}

output "storage_buckets" {
  value = { for key, bucket in google_storage_bucket.buckets : key => bucket.name }
}

output "workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "deployment_service_accounts" {
  value = {
    api    = google_service_account.api.email
    worker = google_service_account.worker.email
    admin  = google_service_account.admin.email
    deploy = google_service_account.deploy.email
  }
}

output "artifact_repository" {
  value = google_artifact_registry_repository.containers.name
}

output "load_balancer_ip" {
  value = google_compute_global_address.edge.address
}

output "valhalla_internal_addresses" {
  value = { for key, rule in google_compute_forwarding_rule.valhalla : key => rule.ip_address }
}
