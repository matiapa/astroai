terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# Service Account for Cloud Run (needed for GCS access)
# =============================================================================
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name}"
}

# Grant the service account access to the GCS bucket
resource "google_storage_bucket_iam_member" "bucket_access" {
  bucket = var.gcs_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# =============================================================================
# Cloud Run Service (v2) with GCS FUSE Volume Mount
# =============================================================================
resource "google_cloud_run_v2_service" "default" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false  # Allow Terraform to recreate the service

  template {
    service_account = google_service_account.cloud_run_sa.email
    
    # Enable GCS FUSE
    annotations = {
      "run.googleapis.com/execution-environment" = "gen2"
    }

    # Define the GCS volume
    volumes {
      name = "gcs-volume"
      gcs {
        bucket    = var.gcs_bucket_name
        read_only = false
      }
    }

    containers {
      image = var.image_name

      # Port configuration
      ports {
        container_port = 8080
      }

      # Mount the GCS bucket
      volume_mounts {
        name       = "gcs-volume"
        mount_path = "/mnt/data"
      }

      # Resource limits
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }

      # Startup probe with extended timeout for Python apps
      startup_probe {
        http_get {
          path = "/"
          port = 8080
        }
        initial_delay_seconds = 10
        timeout_seconds       = 5
        period_seconds        = 10
        failure_threshold     = 30  # Allow up to 5 minutes for startup
      }

      # =============================================================================
      # Environment Variables
      # =============================================================================
      
      # API Configuration
      env {
        name  = "API_HOST"
        value = "0.0.0.0"
      }
      env {
        name  = "API_PORT"
        value = "8080"
      }

      # Storage Configuration (mounted GCS bucket)
      env {
        name  = "STORAGE_DIR"
        value = "/mnt/data"
      }

      # Google API Configuration
      env {
        name  = "GOOGLE_API_KEY"
        value = var.google_api_key
      }
      env {
        name  = "GOOGLE_CSE_ID"
        value = var.google_cse_id
      }

      # Astrometry Configuration
      env {
        name  = "ASTROMETRY_API_KEY"
        value = var.astrometry_api_key
      }
      env {
        name  = "ASTROMETRY_API_URL"
        value = var.astrometry_api_url
      }

      # Plate Solving Configuration
      env {
        name  = "PLATE_SOLVING_TIMEOUT"
        value = var.plate_solving_timeout
      }
      env {
        name  = "PLATE_SOLVING_USE_CACHE"
        value = var.plate_solving_use_cache
      }

      # Detection Configuration
      env {
        name  = "OBJECT_DETECTOR"
        value = var.object_detector
      }
      env {
        name  = "MAX_QUERY_OBJECTS"
        value = var.max_query_objects
      }
      env {
        name  = "SIMBAD_SEARCH_RADIUS"
        value = var.simbad_search_radius
      }

      # Misc Configuration
      env {
        name  = "VERBOSE"
        value = var.verbose
      }

      # Public URL
      env {
        name  = "PUBLIC_API_URL"
        value = var.public_api_url
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_storage_bucket_iam_member.bucket_access
  ]
}

# =============================================================================
# IAM - Allow public access
# =============================================================================
resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
