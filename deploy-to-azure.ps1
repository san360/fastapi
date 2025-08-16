# Azure Deployment Script for FastAPI Auto Sign-In Agent (PowerShell)
# This script creates Azure resources, builds Docker image, pushes to ACR, and deploys to App Service

param(
    [string]$ConfigFile = "azure-config.json"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Load configuration
function Load-Configuration {
    if (Test-Path $ConfigFile) {
        Write-Status "Loading configuration from $ConfigFile..."
        $config = Get-Content $ConfigFile | ConvertFrom-Json
        return $config
    } else {
        Write-Warning "Configuration file $ConfigFile not found. Using default values..."
        $timestamp = [int][double]::Parse((Get-Date -UFormat %s))
        return @{
            resourceGroupName = "rg-fastapi-agent"
            location = "eastus"
            acrName = "acrfastapi$timestamp"
            appServicePlanName = "asp-fastapi-agent"
            appServiceName = "app-fastapi-agent-$timestamp"
            imageName = "fastapi-auto-signin-agent"
        }
    }
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    try {
        $null = az version 2>$null
    } catch {
        Write-Error "Azure CLI is not installed. Please install it first."
        Write-Host "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    }
    
    # Check if user is logged in
    try {
        $null = az account show 2>$null
    } catch {
        Write-Error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    }
    
    # Get current subscription
    $script:subscriptionId = az account show --query id --output tsv
    Write-Success "Using subscription: $script:subscriptionId"
    
    # Check if Docker is running
    try {
        $null = docker info 2>$null
    } catch {
        Write-Error "Docker is not running. Please start Docker first."
        exit 1
    }
    
    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found."
        if (Test-Path ".env.docker") {
            Copy-Item ".env.docker" ".env"
            Write-Warning "Please edit .env file with your Azure credentials before deployment."
        } else {
            Write-Error "Neither .env nor .env.docker found. Please create environment configuration."
            exit 1
        }
    }
    
    Write-Success "Prerequisites check completed"
}

# Function to create resource group
function New-ResourceGroup {
    param($config)
    
    Write-Status "Creating resource group: $($config.resourceGroupName) in $($config.location)..."
    
    $existingRg = az group show --name $config.resourceGroupName 2>$null
    if ($existingRg) {
        Write-Warning "Resource group $($config.resourceGroupName) already exists"
    } else {
        az group create --name $config.resourceGroupName --location $config.location --output table
        Write-Success "Resource group created successfully"
    }
}

# Function to create Azure Container Registry
function New-ContainerRegistry {
    param($config)
    
    Write-Status "Creating Azure Container Registry: $($config.acrName)..."
    
    az acr create `
        --resource-group $config.resourceGroupName `
        --name $config.acrName `
        --sku Basic `
        --admin-enabled true `
        --location $config.location `
        --output table
    
    Write-Success "Azure Container Registry created successfully"
    
    # Get ACR login server
    $script:acrLoginServer = az acr show --name $config.acrName --resource-group $config.resourceGroupName --query loginServer --output tsv
    Write-Status "ACR Login Server: $script:acrLoginServer"
}

# Function to build and push Docker image
function Push-DockerImage {
    param($config)
    
    Write-Status "Building and pushing Docker image to ACR..."
    
    # Login to ACR
    az acr login --name $config.acrName
    
    # Build the Docker image locally
    Write-Status "Building Docker image locally..."
    docker build -t "$($config.imageName):latest" .
    
    # Tag the image for ACR
    docker tag "$($config.imageName):latest" "$script:acrLoginServer/$($config.imageName):latest"
    docker tag "$($config.imageName):latest" "$script:acrLoginServer/$($config.imageName):v1.0"
    
    # Push the image to ACR
    Write-Status "Pushing image to ACR..."
    docker push "$script:acrLoginServer/$($config.imageName):latest"
    docker push "$script:acrLoginServer/$($config.imageName):v1.0"
    
    Write-Success "Docker image pushed successfully to ACR"
    
    # Verify the image in ACR
    Write-Status "Verifying image in ACR..."
    az acr repository list --name $config.acrName --output table
}

# Function to create App Service Plan
function New-AppServicePlan {
    param($config)
    
    Write-Status "Creating App Service Plan: $($config.appServicePlanName)..."
    
    az appservice plan create `
        --name $config.appServicePlanName `
        --resource-group $config.resourceGroupName `
        --location $config.location `
        --sku B1 `
        --is-linux `
        --output table
    
    Write-Success "App Service Plan created successfully"
}

# Function to create and configure App Service
function New-AppService {
    param($config)
    
    Write-Status "Creating App Service: $($config.appServiceName)..."
    
    # Check if App Service already exists
    $existingApp = az webapp show --name $config.appServiceName --resource-group $config.resourceGroupName 2>$null
    if ($existingApp) {
        Write-Warning "App Service $($config.appServiceName) already exists. Deleting and recreating..."
        az webapp delete --name $config.appServiceName --resource-group $config.resourceGroupName
        Write-Status "Waiting for deletion to complete..."
        Start-Sleep -Seconds 30
    }
    
    # Create the web app with system-assigned managed identity
    Write-Status "Creating App Service with system-assigned managed identity..."
    az webapp create `
        --resource-group $config.resourceGroupName `
        --plan $config.appServicePlanName `
        --name $config.appServiceName `
        --container-image-name "$script:acrLoginServer/$($config.imageName):latest" `
        --assign-identity "[system]" `
        --output table
    
    Write-Success "App Service created successfully"
    
    # Configure managed identity for ACR access
    Set-ManagedIdentityAcrAccess -config $config
    
    # Wait for the app service to be fully provisioned
    Write-Status "Waiting for App Service to be fully provisioned..."
    Start-Sleep -Seconds 30
}

# Function to configure managed identity for ACR access
function Set-ManagedIdentityAcrAccess {
    param($config)
    
    Write-Status "Configuring managed identity for ACR access..."
    
    # Get the principal ID of the system-assigned managed identity
    $principalId = az webapp identity show `
        --resource-group $config.resourceGroupName `
        --name $config.appServiceName `
        --query principalId `
        --output tsv
    
    Write-Status "App Service Managed Identity Principal ID: $principalId"
    
    # Get the ACR resource ID
    $acrResourceId = az acr show `
        --resource-group $config.resourceGroupName `
        --name $config.acrName `
        --query id `
        --output tsv
    
    Write-Status "ACR Resource ID: $acrResourceId"
    
    # Grant AcrPull role to the managed identity
    Write-Status "Granting AcrPull role to the managed identity..."
    az role assignment create `
        --assignee $principalId `
        --scope $acrResourceId `
        --role "AcrPull" `
        --output table
    
    # Configure the App Service to use managed identity for ACR authentication
    Write-Status "Configuring App Service to use managed identity for ACR..."
    az webapp config set `
        --resource-group $config.resourceGroupName `
        --name $config.appServiceName `
        --generic-configurations '{\"acrUseManagedIdentityCreds\": true}' `
        --output table
    
    # Remove any existing registry credentials (if any)
    Write-Status "Removing any existing registry credentials..."
    try {
        az webapp config appsettings delete `
            --resource-group $config.resourceGroupName `
            --name $config.appServiceName `
            --setting-names DOCKER_REGISTRY_SERVER_USERNAME DOCKER_REGISTRY_SERVER_PASSWORD `
            --output none 2>$null
    } catch {
        # Ignore errors if settings don't exist
    }
    
    Write-Success "Managed identity for ACR access configured successfully"
}

# Function to configure app settings
function Set-AppConfiguration {
    param($config)
    
    Write-Status "Configuring application settings..."
    
    $settings = @(
        "WEBSITES_PORT=3978",
        "WEBSITES_ENABLE_APP_SERVICE_STORAGE=false",
        "HOST=0.0.0.0",
        "PORT=3978"
    )
    
    # Read environment variables from .env file
    if (Test-Path ".env") {
        Write-Status "Loading environment variables from .env file..."
        
        $envContent = Get-Content ".env"
        foreach ($line in $envContent) {
            $line = $line.Trim()
            if ($line -and -not $line.StartsWith("#")) {
                $settings += $line
            }
        }
    }
    
    # Convert to Azure CLI format
    $settingsArgs = $settings | ForEach-Object { $_ }
    
    az webapp config appsettings set `
        --resource-group $config.resourceGroupName `
        --name $config.appServiceName `
        --settings @settingsArgs `
        --output table
    
    Write-Success "Application settings configured"
}

# Function to restart App Service
function Restart-AppService {
    param($config)
    
    Write-Status "Restarting App Service to apply changes..."
    
    az webapp restart `
        --name $config.appServiceName `
        --resource-group $config.resourceGroupName
    
    Write-Success "App Service restarted successfully"
}

# Function to display deployment information
function Show-DeploymentInfo {
    param($config)
    
    Write-Success "🎉 Deployment completed successfully!"
    Write-Host ""
    Write-Host "=== 📋 Deployment Summary ===" -ForegroundColor Cyan
    Write-Host "Resource Group:     $($config.resourceGroupName)"
    Write-Host "Location:           $($config.location)"
    Write-Host "ACR Name:           $($config.acrName)"
    Write-Host "ACR Login Server:   $script:acrLoginServer"
    Write-Host "App Service Plan:   $($config.appServicePlanName)"
    Write-Host "App Service Name:   $($config.appServiceName)"
    Write-Host "Image:              $script:acrLoginServer/$($config.imageName):latest"
    Write-Host ""
    
    # Get the app URL
    $appUrl = az webapp show --name $config.appServiceName --resource-group $config.resourceGroupName --query defaultHostName --output tsv
    Write-Host "=== 🌐 Application URLs ===" -ForegroundColor Cyan
    Write-Host "Application URL:    https://$appUrl"
    Write-Host "Health Check:       https://$appUrl/health"
    Write-Host "API Documentation:  https://$appUrl/docs"
    Write-Host ""
    
    Write-Host "=== 💰 Cost Information ===" -ForegroundColor Cyan
    Write-Host "ACR SKU:           Basic (Low cost)"
    Write-Host "App Service Plan:  B1 (Basic, ~$13/month)"
    Write-Host ""
    
    Write-Host "=== 📋 Useful Commands ===" -ForegroundColor Cyan
    Write-Host "View logs:         az webapp log tail --name $($config.appServiceName) --resource-group $($config.resourceGroupName)"
    Write-Host "SSH into container: az webapp ssh --name $($config.appServiceName) --resource-group $($config.resourceGroupName)"
    Write-Host "Restart app:       az webapp restart --name $($config.appServiceName) --resource-group $($config.resourceGroupName)"
    Write-Host "Delete resources:  az group delete --name $($config.resourceGroupName) --yes --no-wait"
    Write-Host ""
    
    Write-Status "Waiting for application to start up..."
    Start-Sleep -Seconds 30
    
    # Test the deployment
    Write-Host "=== 🧪 Testing Deployment ===" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "https://$appUrl/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Success "✅ Health check passed!"
            Write-Host $response.Content
        }
    } catch {
        Write-Warning "⚠️  Health check failed. The app might still be starting up."
        Write-Host "Please wait a few minutes and try: https://$appUrl/health"
    }
}

# Main function
function Main {
    Write-Host "🚀 FastAPI Auto Sign-In Agent - Azure Deployment Script (PowerShell)" -ForegroundColor Magenta
    Write-Host "=====================================================================" -ForegroundColor Magenta
    
    try {
        # Load configuration
        $config = Load-Configuration
        
        # Display configuration
        Write-Host ""
        Write-Host "Current configuration:" -ForegroundColor Yellow
        Write-Host "  Resource Group: $($config.resourceGroupName)"
        Write-Host "  Location: $($config.location)"
        Write-Host "  ACR Name: $($config.acrName)"
        Write-Host "  App Service: $($config.appServiceName)"
        Write-Host ""
        
        $continue = Read-Host "Do you want to continue with this configuration? (y/n)"
        if ($continue -notmatch "^[Yy]") {
            Write-Host "Please modify the configuration in $ConfigFile or script variables."
            exit 1
        }
        
        # Execute deployment steps
        Test-Prerequisites
        New-ResourceGroup $config
        New-ContainerRegistry $config
        Push-DockerImage $config
        New-AppServicePlan $config
        New-AppService $config
        Set-AppConfiguration $config
        Restart-AppService $config
        Show-DeploymentInfo $config
        
        Write-Success "🎉 FastAPI Auto Sign-In Agent deployed successfully to Azure!"
        
    } catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        $cleanup = Read-Host "Would you like to clean up created resources? (y/n)"
        if ($cleanup -match "^[Yy]") {
            Write-Status "Cleaning up resources..."
            az group delete --name $config.resourceGroupName --yes --no-wait
            Write-Success "Cleanup initiated. Resources will be deleted in the background."
        }
        exit 1
    }
}

# Run the main function
Main
