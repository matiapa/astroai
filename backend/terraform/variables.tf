variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

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

variable "image_name" {
  description = "The container image to deploy (e.g., gcr.io/project/image:tag)"
  type        = string
}
