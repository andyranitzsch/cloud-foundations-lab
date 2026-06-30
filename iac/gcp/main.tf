# Lab 09 — IaC contra el emulador GCP (cmarin78/gcp-emulator).
#
# Workflow: tofu init → tofu plan → tofu apply → tofu destroy
#
# Lo que declaramos:
#   1. Un bucket de Cloud Storage para que la app lea/escriba.
#   2. Versioning ON.
#
# Comparable a iac/aws/main.tf — misma intención, diferente API.

terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Provider Google apuntado al emulador local.
# Para GCP real: borrar los `*_custom_endpoint` y poner credenciales reales
# (ADC via gcloud o GOOGLE_APPLICATION_CREDENTIALS).
provider "google" {
  project = var.project_id
  region  = var.region

  # Endpoints custom hacia cmarin78/gcp-emulator (puerto 8443).
  # El emulador respeta los paths estándar de GCP REST.
  storage_custom_endpoint = "${var.gcp_emulator_endpoint}/storage/v1/"

  # Credenciales falsas — el emulador las ignora.
  # En GCP real esto se autoconfigura.
  credentials = jsonencode({
    type        = "service_account"
    client_id   = "00000000000000000000"
    private_key = "fake-key-for-emulator-only"
    token_uri   = "${var.gcp_emulator_endpoint}/o/oauth2/token"
  })
}

# El bucket — equivalente conceptual de aws_s3_bucket.
resource "google_storage_bucket" "app" {
  name          = var.bucket_name
  location      = "US"
  force_destroy = true # permite tofu destroy con objetos adentro

  versioning {
    enabled = true
  }

  labels = {
    lab        = "09"
    project    = var.project_id
    managed_by = "opentofu"
  }
}

# Objeto seed.
resource "google_storage_bucket_object" "hello" {
  name    = "hello.txt"
  bucket  = google_storage_bucket.app.name
  content = "hello from IaC — bucket ${google_storage_bucket.app.name}\n"
}
