#!/bin/bash

# Azure Deployment Script for FastAPI Auto Sign-In Agent
# This script creates Azure resources, builds Docker image, pushes to ACR, and deploys to App Service

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables (modify as needed)
TIMESTAMP=$(date +%s)
RESOURCE_GROUP_NAME="rg-fastapi-agent"  # Unique name with timestamp
LOCATION="eastus2"  # Change this to your preferred region
ACR_NAME="acrfastapieu2"  # Unique name with timestamp
APP_SERVICE_PLAN_NAME="asp-fastapi-agent"
APP_SERVICE_NAME="app-fastapi-agent-$TIMESTAMP"  # Unique name with timestamp
IMAGE_NAME="fastapi-auto-signin-agent"
SUBSCRIPTION_ID=""  # Will be detected automatically
ACR_LOGIN_SERVER=""  # Will be set during ACR creation

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Azure CLI is installed and user is logged in
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        echo "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    # Check if user is logged in
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    
    # Get current subscription
    SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    print_success "Using subscription: $SUBSCRIPTION_ID"
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.docker" ]; then
            cp .env.docker .env
            print_warning "Please edit .env file with your Azure credentials before deployment."
        else
            print_error "Neither .env nor .env.docker found. Please create environment configuration."
            exit 1
        fi
    fi
    
    print_success "Prerequisites check completed"
}

# Function to create resource group
create_resource_group() {
    print_status "Creating resource group: $RESOURCE_GROUP_NAME in $LOCATION..."
    
    if az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
        print_warning "Resource group $RESOURCE_GROUP_NAME already exists"
    else
        az group create \
            --name "$RESOURCE_GROUP_NAME" \
            --location "$LOCATION" \
            --output table
        print_success "Resource group created successfully"
    fi
}

# Function to create Azure Container Registry (Basic SKU for cost optimization)
create_acr() {
    print_status "Creating Azure Container Registry: $ACR_NAME..."
    
    az acr create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$ACR_NAME" \
        --sku Basic \
        --admin-enabled true \
        --location "$LOCATION" \
        --output table
    
    print_success "Azure Container Registry created successfully"
    
    # Get ACR login server
    export ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query loginServer --output tsv)
    print_status "ACR Login Server: $ACR_LOGIN_SERVER"
}

# Function to build and push Docker image to ACR
build_and_push_image() {
    print_status "Building and pushing Docker image to ACR..."
    
    # Login to ACR
    az acr login --name "$ACR_NAME"
    
    # Build the Docker image locally first
    print_status "Building Docker image locally..."
    docker build -t "$IMAGE_NAME:latest" .
    
    # Tag the image for ACR
    docker tag "$IMAGE_NAME:latest" "$ACR_LOGIN_SERVER/$IMAGE_NAME:latest"
    docker tag "$IMAGE_NAME:latest" "$ACR_LOGIN_SERVER/$IMAGE_NAME:v1.0"
    
    # Push the image to ACR
    print_status "Pushing image to ACR..."
    docker push "$ACR_LOGIN_SERVER/$IMAGE_NAME:latest"
    docker push "$ACR_LOGIN_SERVER/$IMAGE_NAME:v1.0"
    
    print_success "Docker image pushed successfully to ACR"
    
    # Verify the image in ACR
    print_status "Verifying image in ACR..."
    az acr repository list --name "$ACR_NAME" --output table
}

# Function to create App Service Plan (Free tier for cost optimization)
create_app_service_plan() {
    print_status "Creating App Service Plan: $APP_SERVICE_PLAN_NAME..."
    
    az appservice plan create \
        --name "$APP_SERVICE_PLAN_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --location "$LOCATION" \
        --sku B1 \
        --is-linux \
        --output table
    
    print_success "App Service Plan created successfully"
}

# Function to create and configure App Service
create_app_service() {
    print_status "Creating App Service: $APP_SERVICE_NAME..."
    
    # Check if App Service already exists
    if az webapp show --name "$APP_SERVICE_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
        print_warning "App Service $APP_SERVICE_NAME already exists. Deleting and recreating..."
        az webapp delete --name "$APP_SERVICE_NAME" --resource-group "$RESOURCE_GROUP_NAME"
        print_status "Waiting for deletion to complete..."
        sleep 30
    fi
    
    # Ensure ACR_LOGIN_SERVER is set
    if [ -z "$ACR_LOGIN_SERVER" ]; then
        ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query loginServer --output tsv)
        print_status "Retrieved ACR Login Server: $ACR_LOGIN_SERVER"
    fi
    
    # Create the web app (Linux container app) with system-assigned managed identity
    print_status "Creating App Service with system-assigned managed identity..."
    az webapp create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --plan "$APP_SERVICE_PLAN_NAME" \
        --name "$APP_SERVICE_NAME" \
        --container-image-name "$ACR_LOGIN_SERVER/$IMAGE_NAME:latest" \
        --assign-identity "[system]" \
        --output table
    
    print_success "App Service created successfully"
    
    # Configure managed identity for ACR access
    configure_managed_identity_acr_access
    
    # Wait a moment for the app service to be fully provisioned
    print_status "Waiting for App Service to be fully provisioned..."
    sleep 30
}

# Function to configure managed identity for ACR access
configure_managed_identity_acr_access() {
    print_status "Configuring managed identity for ACR access..."
    
    # Get the principal ID of the system-assigned managed identity
    PRINCIPAL_ID=$(az webapp identity show \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$APP_SERVICE_NAME" \
        --query principalId \
        --output tsv)
    
    print_status "App Service Managed Identity Principal ID: $PRINCIPAL_ID"
    
    # Get the ACR resource ID
    ACR_RESOURCE_ID=$(az acr show \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$ACR_NAME" \
        --query id \
        --output tsv)
    
    print_status "ACR Resource ID: $ACR_RESOURCE_ID"
    
    # Grant AcrPull role to the managed identity
    print_status "Granting AcrPull role to the managed identity..."
    az role assignment create \
        --assignee "$PRINCIPAL_ID" \
        --scope "$ACR_RESOURCE_ID" \
        --role "AcrPull" \
        --output table
    
    # Configure the App Service to use managed identity for ACR authentication
    print_status "Configuring App Service to use managed identity for ACR..."
    az webapp config set \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$APP_SERVICE_NAME" \
        --generic-configurations '{"acrUseManagedIdentityCreds": true}' \
        --output table
    
    # Remove any existing registry credentials (if any)
    print_status "Removing any existing registry credentials..."
    az webapp config appsettings delete \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$APP_SERVICE_NAME" \
        --setting-names DOCKER_REGISTRY_SERVER_USERNAME DOCKER_REGISTRY_SERVER_PASSWORD \
        --output none 2>/dev/null || true
    
    print_success "Managed identity for ACR access configured successfully"
}

# Function to configure environment variables
configure_app_settings() {
    print_status "Configuring application settings..."
    
    # Set essential App Service settings first
    print_status "Setting essential App Service settings..."
    az webapp config appsettings set \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$APP_SERVICE_NAME" \
        --settings \
            WEBSITES_PORT=3978 \
            WEBSITES_ENABLE_APP_SERVICE_STORAGE=false \
        --output table
    
    # Read environment variables from .env file and set them individually
    if [ -f ".env" ]; then
        print_status "Loading environment variables from .env file..."
        
        # Process .env file line by line
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip empty lines and comments
            if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                # Check if line contains = and is a valid key=value pair
                if [[ "$line" =~ ^[^=]+=[^=]*$ ]]; then
                    # Extract key and value
                    KEY="${line%%=*}"
                    VALUE="${line#*=}"
                    
                    # Set the environment variable
                    print_status "Setting $KEY..."
                    az webapp config appsettings set \
                        --resource-group "$RESOURCE_GROUP_NAME" \
                        --name "$APP_SERVICE_NAME" \
                        --settings "$KEY=$VALUE" \
                        --output none
                fi
            fi
        done < .env
        
        print_success "Environment variables from .env file configured"
    else
        print_warning "No .env file found. Only basic settings will be configured."
    fi
    
    print_success "Application settings configured"
}

# Function to restart the web app
restart_app_service() {
    print_status "Restarting App Service to apply changes..."
    
    az webapp restart \
        --name "$APP_SERVICE_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME"
    
    print_success "App Service restarted successfully"
}

# Function to display deployment information
display_deployment_info() {
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "=== 📋 Deployment Summary ==="
    echo "Resource Group:     $RESOURCE_GROUP_NAME"
    echo "Location:           $LOCATION"
    echo "ACR Name:           $ACR_NAME"
    echo "ACR Login Server:   $ACR_LOGIN_SERVER"
    echo "App Service Plan:   $APP_SERVICE_PLAN_NAME"
    echo "App Service Name:   $APP_SERVICE_NAME"
    echo "Image:              $ACR_LOGIN_SERVER/$IMAGE_NAME:latest"
    echo ""
    
    # Get the app URL
    APP_URL=$(az webapp show --name "$APP_SERVICE_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query defaultHostName --output tsv)
    echo "=== 🌐 Application URLs ==="
    echo "Application URL:    https://$APP_URL"
    echo "Health Check:       https://$APP_URL/health"
    echo "API Documentation:  https://$APP_URL/docs"
    echo ""
    
    echo "=== 💰 Cost Information ==="
    echo "ACR SKU:           Basic (Low cost)"
    echo "App Service Plan:  B1 (Basic, ~$13/month)"
    echo ""
    
    echo "=== 📋 Useful Commands ==="
    echo "View logs:         az webapp log tail --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP_NAME"
    echo "SSH into container: az webapp ssh --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP_NAME"
    echo "Restart app:       az webapp restart --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP_NAME"
    echo "Delete resources:  az group delete --name $RESOURCE_GROUP_NAME --yes --no-wait"
    echo ""
    
    print_status "Waiting for application to start up..."
    sleep 30
    
    # Test the deployment
    echo "=== 🧪 Testing Deployment ==="
    if curl -f "https://$APP_URL/health" &> /dev/null; then
        print_success "✅ Health check passed!"
        curl "https://$APP_URL/health"
        echo ""
    else
        print_warning "⚠️  Health check failed. The app might still be starting up."
        echo "Please wait a few minutes and try: https://$APP_URL/health"
    fi
}

# Function to clean up conflicting resources
cleanup_existing_resources() {
    print_status "Checking for existing conflicting resources..."
    
    # Check and clean up existing App Service with the old name
    if az webapp show --name "app-fastapi-agent" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
        print_warning "Found existing App Service 'app-fastapi-agent'. Deleting to avoid conflicts..."
        az webapp delete --name "app-fastapi-agent" --resource-group "$RESOURCE_GROUP_NAME"
        print_status "Waiting for deletion to complete..."
        sleep 20
    fi
    
    print_success "Resource cleanup completed"
}

# Function to cleanup on error
cleanup_on_error() {
    print_error "Deployment failed. Would you like to clean up created resources? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Cleaning up resources..."
        az group delete --name "$RESOURCE_GROUP_NAME" --yes --no-wait
        print_success "Cleanup initiated. Resources will be deleted in the background."
    fi
}

# Main deployment function
main() {
    echo "🚀 FastAPI Auto Sign-In Agent - Azure Deployment Script"
    echo "======================================================"
    
    # Trap errors and cleanup
    trap cleanup_on_error ERR
    
    # Check if user wants to customize configuration
    echo ""
    echo "Current configuration:"
    echo "  Resource Group: $RESOURCE_GROUP_NAME"
    echo "  Location: $LOCATION"
    echo "  ACR Name: $ACR_NAME"
    echo "  App Service: $APP_SERVICE_NAME"
    echo ""
    
    read -p "Do you want to continue with this configuration? (y/n): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please modify the configuration variables at the top of this script."
        exit 1
    fi
    
    # Execute deployment steps
    check_prerequisites
    cleanup_existing_resources
    create_resource_group
    create_acr
    build_and_push_image
    create_app_service_plan
    create_app_service
    configure_app_settings
    restart_app_service
    display_deployment_info
    
    print_success "🎉 FastAPI Auto Sign-In Agent deployed successfully to Azure!"
}

# Run the main function
main "$@"
