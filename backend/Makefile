# =============================================================================
# AstroIA Backend - Build and Deployment Makefile
# =============================================================================

# Configuration - Override these via environment variables or command line
PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= us-central1
SERVICE_NAME ?= astroia-backend
REPOSITORY_NAME ?= astroia-repo
IMAGE_TAG ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
GCS_BUCKET_NAME ?= $(SERVICE_NAME)-storage

# Derived variables
REGISTRY_URL = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPOSITORY_NAME)
IMAGE_NAME = $(REGISTRY_URL)/$(SERVICE_NAME):$(IMAGE_TAG)
IMAGE_LATEST = $(REGISTRY_URL)/$(SERVICE_NAME):latest

# Terraform tfvars file (contains sensitive variables)
TFVARS_FILE = terraform/terraform.tfvars

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help check-env check-tfvars setup-registry setup-bucket build push deploy deploy-config clean tf-init tf-plan tf-apply tf-destroy logs

# =============================================================================
# Help
# =============================================================================
help:
	@echo ""
	@echo "$(CYAN)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║      AstroIA Backend - Build & Deployment Commands            ║$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(NC)"
	@echo "  make check-env        - Verify all required environment variables"
	@echo "  make check-tfvars     - Verify terraform.tfvars exists"
	@echo "  make setup-registry   - Create Artifact Registry repository (one-time)"
	@echo "  make setup-bucket     - Create GCS bucket for storage (one-time)"
	@echo ""
	@echo "$(GREEN)Build Commands:$(NC)"
	@echo "  make build            - Build Docker image locally"
	@echo "  make push             - Push Docker image to Artifact Registry"
	@echo ""
	@echo "$(GREEN)Deploy Commands:$(NC)"
	@echo "  make tf-init          - Initialize Terraform"
	@echo "  make tf-plan          - Preview Terraform changes"
	@echo "  make tf-apply         - Apply Terraform configuration"
	@echo "  make tf-destroy       - Destroy Terraform resources"
	@echo "  make deploy           - Build, push, and deploy (full pipeline)"
	@echo "  make deploy-config    - Deploy using latest image (skip build/push)"
	@echo ""
	@echo "$(GREEN)Utility Commands:$(NC)"
	@echo "  make logs             - Stream Cloud Run logs"
	@echo "  make clean            - Clean local Docker images"
	@echo ""
	@echo "$(YELLOW)Configuration (override with environment variables):$(NC)"
	@echo "  PROJECT_ID       = $(PROJECT_ID)"
	@echo "  REGION           = $(REGION)"
	@echo "  SERVICE_NAME     = $(SERVICE_NAME)"
	@echo "  REPOSITORY_NAME  = $(REPOSITORY_NAME)"
	@echo "  GCS_BUCKET_NAME  = $(GCS_BUCKET_NAME)"
	@echo "  IMAGE_TAG        = $(IMAGE_TAG)"
	@echo ""
	@echo "$(YELLOW)IMPORTANT: Create terraform/terraform.tfvars with your API keys!$(NC)"
	@echo "  Copy terraform/terraform.tfvars.example to terraform/terraform.tfvars"
	@echo ""

# =============================================================================
# Environment Checks
# =============================================================================
check-env:
	@echo "$(CYAN)Checking environment...$(NC)"
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "$(RED)Error: PROJECT_ID is not set$(NC)"; \
		echo "Run: gcloud config set project YOUR_PROJECT_ID"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ PROJECT_ID: $(PROJECT_ID)$(NC)"
	@echo "$(GREEN)✓ REGION: $(REGION)$(NC)"
	@echo "$(GREEN)✓ GCS_BUCKET_NAME: $(GCS_BUCKET_NAME)$(NC)"
	@echo "$(GREEN)✓ IMAGE_NAME: $(IMAGE_NAME)$(NC)"
	@gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1 || \
		(echo "$(RED)Error: Not authenticated with gcloud$(NC)" && exit 1)
	@echo "$(GREEN)✓ gcloud authenticated$(NC)"
	@docker info > /dev/null 2>&1 || \
		(echo "$(RED)Error: Docker is not running$(NC)" && exit 1)
	@echo "$(GREEN)✓ Docker is running$(NC)"
	@echo "$(GREEN)Environment check passed!$(NC)"

check-tfvars:
	@if [ ! -f "$(TFVARS_FILE)" ]; then \
		echo "$(RED)Error: $(TFVARS_FILE) not found$(NC)"; \
		echo "$(YELLOW)Please create it from the example:$(NC)"; \
		echo "  cp terraform/terraform.tfvars.example terraform/terraform.tfvars"; \
		echo "  Then edit it with your API keys and configuration"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ terraform.tfvars found$(NC)"

# =============================================================================
# GCS Bucket Setup
# =============================================================================
setup-bucket: check-env
	@echo "$(CYAN)Setting up GCS bucket...$(NC)"
	@if gcloud storage buckets describe gs://$(GCS_BUCKET_NAME) > /dev/null 2>&1; then \
		echo "$(GREEN)✓ GCS bucket already exists: $(GCS_BUCKET_NAME)$(NC)"; \
	else \
		echo "Creating bucket $(GCS_BUCKET_NAME)..."; \
		gcloud storage buckets create gs://$(GCS_BUCKET_NAME) --project=$(PROJECT_ID) --location=$(REGION) || true; \
		echo "$(GREEN)✓ GCS bucket ready: $(GCS_BUCKET_NAME)$(NC)"; \
	fi

# =============================================================================
# Artifact Registry Setup
# =============================================================================
setup-registry: check-env
	@echo "$(CYAN)Setting up Artifact Registry...$(NC)"
	@gcloud artifacts repositories describe $(REPOSITORY_NAME) \
		--location=$(REGION) > /dev/null 2>&1 || \
		gcloud artifacts repositories create $(REPOSITORY_NAME) \
			--repository-format=docker \
			--location=$(REGION) \
			--description="Docker repository for AstroIA"
	@echo "$(GREEN)✓ Artifact Registry repository ready$(NC)"
	@echo "$(CYAN)Configuring Docker for Artifact Registry...$(NC)"
	@gcloud auth configure-docker $(REGION)-docker.pkg.dev --quiet
	@echo "$(GREEN)✓ Docker configured for Artifact Registry$(NC)"

# =============================================================================
# Build
# =============================================================================
build: check-env
	@echo "$(CYAN)Building Docker image...$(NC)"
	@echo "  Image: $(IMAGE_NAME)"
	docker build --platform linux/amd64 -t $(IMAGE_NAME) -t $(IMAGE_LATEST) .
	@echo "$(GREEN)✓ Docker image built successfully$(NC)"

# =============================================================================
# Push to Artifact Registry
# =============================================================================
push: check-env
	@echo "$(CYAN)Pushing image to Artifact Registry...$(NC)"
	@echo "  Image: $(IMAGE_NAME)"
	docker push $(IMAGE_NAME)
	docker push $(IMAGE_LATEST)
	@echo "$(GREEN)✓ Image pushed successfully$(NC)"

# =============================================================================
# Terraform Commands
# =============================================================================
tf-init: check-env
	@echo "$(CYAN)Initializing Terraform...$(NC)"
	cd terraform && terraform init
	@echo "$(GREEN)✓ Terraform initialized$(NC)"

tf-plan: check-env check-tfvars
	@echo "$(CYAN)Planning Terraform changes...$(NC)"
	cd terraform && terraform plan \
		-var="project_id=$(PROJECT_ID)" \
		-var="region=$(REGION)" \
		-var="service_name=$(SERVICE_NAME)" \
		-var="image_name=$(IMAGE_NAME)" \
		-var="gcs_bucket_name=$(GCS_BUCKET_NAME)"

tf-apply: check-env check-tfvars
	@echo "$(CYAN)Applying Terraform configuration...$(NC)"
	cd terraform && terraform apply \
		-var="project_id=$(PROJECT_ID)" \
		-var="region=$(REGION)" \
		-var="service_name=$(SERVICE_NAME)" \
		-var="image_name=$(IMAGE_NAME)" \
		-var="gcs_bucket_name=$(GCS_BUCKET_NAME)" \
		-auto-approve
	@echo "$(GREEN)✓ Terraform applied successfully$(NC)"
	@echo ""
	@echo "$(CYAN)Service URL:$(NC)"
	@cd terraform && terraform output -raw service_url
	@echo ""

tf-destroy: check-env check-tfvars
	@echo "$(YELLOW)Warning: This will destroy all resources!$(NC)"
	cd terraform && terraform destroy \
		-var="project_id=$(PROJECT_ID)" \
		-var="region=$(REGION)" \
		-var="service_name=$(SERVICE_NAME)" \
		-var="image_name=$(IMAGE_NAME)" \
		-var="gcs_bucket_name=$(GCS_BUCKET_NAME)"

# =============================================================================
# Full Deployment Pipeline
# =============================================================================
deploy: check-env check-tfvars setup-bucket setup-registry build push tf-init tf-apply
	@echo ""
	@echo "$(GREEN)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║              Deployment completed successfully!               ║$(NC)"
	@echo "$(GREEN)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(CYAN)Service URL:$(NC) $$(cd terraform && terraform output -raw service_url)"
	@echo "$(CYAN)GCS Bucket:$(NC) gs://$(GCS_BUCKET_NAME) mounted at /mnt/data"
	@echo ""

# =============================================================================
# Deploy Config Only (Skip Build/Push) - Uses latest image
# =============================================================================
deploy-config: check-env check-tfvars setup-bucket tf-init tf-apply
	@echo ""
	@echo "$(GREEN)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║         Configuration deployed successfully!                  ║$(NC)"
	@echo "$(GREEN)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Note: Used existing image (build/push skipped)$(NC)"
	@echo "$(CYAN)Service URL:$(NC) $$(cd terraform && terraform output -raw service_url)"
	@echo "$(CYAN)GCS Bucket:$(NC) gs://$(GCS_BUCKET_NAME) mounted at /mnt/data"
	@echo ""

# =============================================================================
# Utility Commands
# =============================================================================
logs:
	@echo "$(CYAN)Streaming Cloud Run logs (Ctrl+C to stop)...$(NC)"
	gcloud run services logs tail $(SERVICE_NAME) --region $(REGION)

clean:
	@echo "$(CYAN)Cleaning local Docker images...$(NC)"
	-docker rmi $(IMAGE_NAME) 2>/dev/null
	-docker rmi $(IMAGE_LATEST) 2>/dev/null
	@echo "$(GREEN)✓ Cleanup complete$(NC)"
