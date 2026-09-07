variable "project_id" {
  type = string
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production"
  }
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "api_image" {
  type        = string
  description = "Immutable Artifact Registry API image URI."
}

variable "admin_image" {
  type        = string
  description = "Immutable Artifact Registry Admin image URI."
}

variable "domain" {
  type = string
}

variable "admin_domain" {
  type = string
}

variable "iap_oauth_client_id" {
  type      = string
  sensitive = true
}

variable "iap_oauth_client_secret" {
  type      = string
  sensitive = true
}

variable "iap_jwt_audience" {
  type        = string
  description = "Expected aud claim for X-Goog-IAP-JWT-Assertion on the Admin API backend."
}

variable "iap_access_members" {
  description = "IAM principals allowed through Admin Studio IAP, e.g. user:owner@example.com or group:admins@example.com."
  type        = set(string)
  default     = []
}

variable "github_repository" {
  type        = string
  description = "GitHub owner/repository allowed to deploy."
}

variable "alert_email" {
  type = string
}

variable "billing_account" {
  type        = string
  default     = ""
  description = "Billing account ID used for production budget alerts. Empty disables budget creation."
}

variable "monthly_budget_usd" {
  type        = number
  default     = 2500
  description = "Monthly cost envelope used for budget threshold notifications."
}

variable "database_tier" {
  type    = string
  default = "db-custom-2-7680"
}

variable "redis_memory_gb" {
  type    = number
  default = 5
}

variable "api_max_instances" {
  type    = number
  default = 20
}

variable "worker_max_instances" {
  type    = number
  default = 30
}

variable "training_generation_enabled" {
  type        = bool
  default     = false
  description = "Explicit release gate for deterministic training generation. Keep false until a reviewed catalogue release is active."
}

variable "valhalla_machine_type" {
  type    = string
  default = "e2-standard-4"
}

variable "valhalla_regions" {
  type    = set(string)
  default = ["us", "uk", "india"]
}

variable "valhalla_graph_objects" {
  type        = map(string)
  default     = {}
  description = "Map of logical region to object path in the Valhalla graph bucket."
}

variable "valhalla_enabled" {
  type    = bool
  default = false
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = null
}

variable "resend_api_key" {
  type      = string
  sensitive = true
  default   = null
}

variable "mapbox_public_token" {
  type      = string
  sensitive = true
  default   = null
}

variable "sentry_dsn" {
  type      = string
  sensitive = true
  default   = null
}

variable "expo_access_token" {
  type      = string
  sensitive = true
  default   = null
}
