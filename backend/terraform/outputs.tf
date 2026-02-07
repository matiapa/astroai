output "service_url" {
  value       = google_cloud_run_v2_service.default.uri
  description = "The URL of the deployed Cloud Run service"
}

output "service_name" {
  value       = google_cloud_run_v2_service.default.name
  description = "The name of the Cloud Run service"
}

output "gcs_bucket_mounted" {
  value       = var.gcs_bucket_name
  description = "The GCS bucket mounted at /mnt/data"
}

output "service_account" {
  value       = google_service_account.cloud_run_sa.email
  description = "The service account used by Cloud Run"
}
