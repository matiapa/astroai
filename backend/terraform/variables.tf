# =============================================================================
# Required Variables
# =============================================================================

variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "image_name" {
  description = "The container image to deploy (e.g., REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG)"
  type        = string
}

variable "gcs_bucket_name" {
  description = "The name of the GCS bucket to mount at /mnt/data"
  type        = string
}

# =============================================================================
# API Keys (Sensitive)
# =============================================================================

variable "google_api_key" {
  description = "Google API Key for Gemini and other Google services"
  type        = string
  sensitive   = true
}

variable "google_cse_id" {
  description = "Google Custom Search Engine ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "astrometry_api_key" {
  description = "API Key for Astrometry.net service"
  type        = string
  sensitive   = true
}

# =============================================================================
# Optional Variables with Defaults
# =============================================================================

variable "region" {
  description = "The Google Cloud region to deploy to"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "astroia-backend"
}

# =============================================================================
# Resource Limits
# =============================================================================

variable "cpu_limit" {
  description = "CPU limit for the Cloud Run container"
  type        = string
  default     = "2"
}

variable "memory_limit" {
  description = "Memory limit for the Cloud Run container"
  type        = string
  default     = "2Gi"
}

# =============================================================================
# Application Configuration
# =============================================================================

variable "astrometry_api_url" {
  description = "URL for the Astrometry plate solving service"
  type        = string
  default     = "http://ec2-3-145-73-178.us-east-2.compute.amazonaws.com/solve"
}

variable "plate_solving_timeout" {
  description = "Timeout in seconds for plate solving"
  type        = string
  default     = "120"
}

variable "plate_solving_use_cache" {
  description = "Whether to use caching for plate solving results"
  type        = string
  default     = "false"
}

variable "object_detector" {
  description = "Object detection algorithm to use"
  type        = string
  default     = "contrast_detector"
}

variable "max_query_objects" {
  description = "Maximum number of objects to query from SIMBAD"
  type        = string
  default     = "10"
}

variable "simbad_search_radius" {
  description = "Search radius in degrees for SIMBAD queries"
  type        = string
  default     = "10"
}

variable "verbose" {
  description = "Enable verbose logging"
  type        = string
  default     = "true"
}
