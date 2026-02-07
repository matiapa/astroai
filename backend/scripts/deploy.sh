#!/bin/bash
# =============================================================================
# AstroIA Backend - Automated Deployment Script
# =============================================================================
# This script automates the build, push, and deploy process for the backend
# service to Google Cloud Run via Artifact Registry and Terraform.
# =============================================================================

set -e  # Exit on error

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
TFVARS_FILE="$TERRAFORM_DIR/terraform.tfvars"

# Defaults (can be overridden by environment variables or arguments)
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-astroia-backend}"
REPOSITORY_NAME="${REPOSITORY_NAME:-astroia-repo}"
GCS_BUCKET_NAME="${GCS_BUCKET_NAME:-${SERVICE_NAME}-storage}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo "latest")}"

# Derived values
REGISTRY_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}"
IMAGE_NAME="${REGISTRY_URL}/${SERVICE_NAME}:${IMAGE_TAG}"
IMAGE_LATEST="${REGISTRY_URL}/${SERVICE_NAME}:latest"

# =============================================================================
# Helper Functions
# =============================================================================
# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         AstroIA Backend - Deployment Script                   ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_config() {
    echo -e "${CYAN}Configuration:${NC}"
    echo "  PROJECT_ID:       ${PROJECT_ID}"
    echo "  REGION:           ${REGION}"
    echo "  SERVICE_NAME:     ${SERVICE_NAME}"
    echo "  REPOSITORY_NAME:  ${REPOSITORY_NAME}"
    echo "  GCS_BUCKET_NAME:  ${GCS_BUCKET_NAME}"
    echo "  IMAGE_TAG:        ${IMAGE_TAG}"
    echo "  IMAGE_NAME:       ${IMAGE_NAME}"
    echo ""
}

usage() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  all              Run complete deployment pipeline (default)"
    echo "  build            Build Docker image only"
    echo "  push             Push image to Artifact Registry"
    echo "  deploy           Run Terraform apply only"
    echo "  destroy          Destroy all resources"
    echo ""
    echo "Options:"
    echo "  -p, --project    Google Cloud Project ID"
    echo "  -r, --region     Google Cloud Region (default: us-central1)"
    echo "  -t, --tag        Docker image tag (default: git short SHA)"
    echo "  -s, --service    Cloud Run service name (default: astroia-backend)"
    echo "  -b, --bucket     GCS bucket name for storage"
    echo "  --skip-build     Skip Docker build step"
    echo "  --skip-push      Skip Docker push step"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Full deployment with defaults"
    echo "  $0 -p my-project -t v1.0.0 all  # Deploy with custom project and tag"
    echo "  $0 build                        # Build only"
    echo "  $0 --skip-build deploy          # Deploy without building"
    echo ""
    echo "IMPORTANT: Before deploying, create terraform/terraform.tfvars with your API keys!"
    echo "  cp terraform/terraform.tfvars.example terraform/terraform.tfvars"
    echo ""
}

# =============================================================================
# Validation
# =============================================================================
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed."
        exit 1
    fi
    
    # Check terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Install from: https://developer.hashicorp.com/terraform/downloads"
        exit 1
    fi
    
    # Check gsutil
    if ! command -v gsutil &> /dev/null; then
        log_error "gsutil is not installed. Install Google Cloud SDK."
        exit 1
    fi
    
    # Check gcloud auth
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
        log_error "Not authenticated with gcloud. Run: gcloud auth login"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker."
        exit 1
    fi
    
    # Check PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
        log_error "PROJECT_ID is not set. Use -p flag or run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
    
    log_success "All prerequisites met!"
    echo ""
}

check_tfvars() {
    if [ ! -f "$TFVARS_FILE" ]; then
        log_error "terraform.tfvars not found at: $TFVARS_FILE"
        echo ""
        echo "Please create it from the example:"
        echo "  cp terraform/terraform.tfvars.example terraform/terraform.tfvars"
        echo "Then edit it with your API keys and configuration"
        exit 1
    fi
    log_success "terraform.tfvars found"
}

# =============================================================================
# Setup Functions
# =============================================================================
setup_gcs_bucket() {
    log_info "Setting up GCS bucket: ${GCS_BUCKET_NAME}..."
    
    if gsutil ls -b "gs://${GCS_BUCKET_NAME}" > /dev/null 2>&1; then
        log_info "Bucket '${GCS_BUCKET_NAME}' already exists"
    else
        log_info "Creating bucket '${GCS_BUCKET_NAME}'..."
        gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://${GCS_BUCKET_NAME}"
    fi
    
    log_success "GCS bucket setup complete!"
    echo ""
}

setup_artifact_registry() {
    log_info "Setting up Artifact Registry..."
    
    # Check if repository exists
    if gcloud artifacts repositories describe "$REPOSITORY_NAME" \
        --location="$REGION" > /dev/null 2>&1; then
        log_info "Repository '$REPOSITORY_NAME' already exists"
    else
        log_info "Creating repository '$REPOSITORY_NAME'..."
        gcloud artifacts repositories create "$REPOSITORY_NAME" \
            --repository-format=docker \
            --location="$REGION" \
            --description="Docker repository for AstroIA"
    fi
    
    # Configure Docker for Artifact Registry
    log_info "Configuring Docker authentication..."
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
    
    log_success "Artifact Registry setup complete!"
    echo ""
}

# =============================================================================
# Build Functions
# =============================================================================
build_image() {
    log_info "Building Docker image..."
    log_info "  Image: $IMAGE_NAME"
    
    cd "$PROJECT_ROOT"
    
    docker build \
        --platform linux/amd64 \
        -t "$IMAGE_NAME" \
        -t "$IMAGE_LATEST" \
        .
    
    log_success "Docker image built successfully!"
    echo ""
}

push_image() {
    log_info "Pushing image to Artifact Registry..."
    log_info "  Image: $IMAGE_NAME"
    
    docker push "$IMAGE_NAME"
    docker push "$IMAGE_LATEST"
    
    log_success "Image pushed successfully!"
    echo ""
}

# =============================================================================
# Terraform Functions
# =============================================================================
terraform_init() {
    log_info "Initializing Terraform..."
    
    cd "$TERRAFORM_DIR"
    terraform init -input=false
    
    log_success "Terraform initialized!"
    echo ""
}

terraform_plan() {
    log_info "Planning Terraform changes..."
    
    cd "$TERRAFORM_DIR"
    terraform plan \
        -var="project_id=${PROJECT_ID}" \
        -var="region=${REGION}" \
        -var="service_name=${SERVICE_NAME}" \
        -var="image_name=${IMAGE_NAME}" \
        -var="gcs_bucket_name=${GCS_BUCKET_NAME}"
    
    echo ""
}

terraform_apply() {
    log_info "Applying Terraform configuration..."
    
    cd "$TERRAFORM_DIR"
    terraform apply \
        -var="project_id=${PROJECT_ID}" \
        -var="region=${REGION}" \
        -var="service_name=${SERVICE_NAME}" \
        -var="image_name=${IMAGE_NAME}" \
        -var="gcs_bucket_name=${GCS_BUCKET_NAME}" \
        -auto-approve
    
    log_success "Terraform applied successfully!"
    echo ""
}

terraform_destroy() {
    log_warning "This will destroy all Cloud Run resources!"
    read -p "Are you sure you want to continue? (y/N) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$TERRAFORM_DIR"
        terraform destroy \
            -var="project_id=${PROJECT_ID}" \
            -var="region=${REGION}" \
            -var="service_name=${SERVICE_NAME}" \
            -var="image_name=${IMAGE_NAME}" \
            -var="gcs_bucket_name=${GCS_BUCKET_NAME}"
        
        log_success "Resources destroyed!"
    else
        log_info "Destroy cancelled"
    fi
}

# =============================================================================
# Output Functions
# =============================================================================
print_deployment_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Deployment completed successfully!               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    cd "$TERRAFORM_DIR"
    SERVICE_URL=$(terraform output -raw service_url 2>/dev/null || echo "N/A")
    
    echo -e "${CYAN}Deployment Details:${NC}"
    echo "  Service URL:   $SERVICE_URL"
    echo "  Image:         $IMAGE_NAME"
    echo "  Region:        $REGION"
    echo "  GCS Bucket:    gs://${GCS_BUCKET_NAME} (mounted at /mnt/data)"
    echo ""
    echo -e "${CYAN}Useful Commands:${NC}"
    echo "  View logs:    gcloud run services logs tail $SERVICE_NAME --region $REGION"
    echo "  Describe:     gcloud run services describe $SERVICE_NAME --region $REGION"
    echo ""
}

# =============================================================================
# Main Command Processing
# =============================================================================
SKIP_BUILD=false
SKIP_PUSH=false
COMMAND="all"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -b|--bucket)
            GCS_BUCKET_NAME="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-push)
            SKIP_PUSH=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        all|build|push|deploy|destroy)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Recalculate derived values after argument parsing
REGISTRY_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}"
IMAGE_NAME="${REGISTRY_URL}/${SERVICE_NAME}:${IMAGE_TAG}"
IMAGE_LATEST="${REGISTRY_URL}/${SERVICE_NAME}:latest"

# =============================================================================
# Execute Commands
# =============================================================================
print_banner
print_config
check_prerequisites

case $COMMAND in
    all)
        check_tfvars
        setup_gcs_bucket
        setup_artifact_registry
        
        if [ "$SKIP_BUILD" = false ]; then
            build_image
        else
            log_info "Skipping build step..."
        fi
        
        if [ "$SKIP_PUSH" = false ]; then
            push_image
        else
            log_info "Skipping push step..."
        fi
        
        terraform_init
        terraform_apply
        print_deployment_summary
        ;;
    build)
        build_image
        ;;
    push)
        setup_artifact_registry
        push_image
        ;;
    deploy)
        check_tfvars
        setup_gcs_bucket
        terraform_init
        terraform_apply
        print_deployment_summary
        ;;
    destroy)
        check_tfvars
        terraform_init
        terraform_destroy
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
