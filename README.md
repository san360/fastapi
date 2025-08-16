# FastAPI Auto Sign-In Agent - Azure Deployment

A containerized FastAPI application that provides automatic sign-in capabilities, deployed to Azure Container Registry (ACR) and Azure App Service using secure managed identity authentication.

## 🚀 Live Application

**URL**: https://app-fastapi-agent-1755331446.azurewebsites.net

**Available Endpoints**:
- `/` - Main application status
- `/health` - Health check endpoint
- `/docs` - Interactive API documentation (Swagger UI)

## 📋 Overview

This project demonstrates a complete Azure deployment pipeline for a containerized FastAPI application with:

- **Docker containerization** with multi-stage builds
- **Azure Container Registry (ACR)** for secure image storage
- **Azure App Service** for scalable hosting
- **System-assigned managed identity** for secure ACR authentication
- **Cost-optimized infrastructure** (~$18/month total)
- **Automated deployment scripts** for both Bash and PowerShell

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   Developer     │───▶│   Docker Build   │───▶│  Azure Container│
│   Workstation   │    │   & Push to ACR  │    │   Registry (ACR)│
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   End Users     │◀───│   Azure App      │◀───│  Managed        │
│                 │    │   Service        │    │  Identity Auth  │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 💰 Cost Analysis

| Resource | SKU/Tier | Estimated Monthly Cost |
|----------|----------|----------------------|
| Azure Container Registry | Basic | ~$5 |
| Azure App Service Plan | B1 (Basic) | ~$13 |
| **Total** | | **~$18/month** |

*Costs are estimates and may vary by region and usage patterns.*

## 📦 Prerequisites

Before running the deployment scripts, ensure you have:

### Required Tools
- **Azure CLI** - [Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- **Docker** - [Install Guide](https://docs.docker.com/get-docker/)
- **Bash** (Linux/macOS/WSL) or **PowerShell** (Windows)

### Azure Access
- Active Azure subscription
- Sufficient permissions to create:
  - Resource Groups
  - Container Registries
  - App Service Plans and Apps
  - Role Assignments

### Authentication
```bash
# Login to Azure
az login

# Set your subscription (if multiple)
az account set --subscription "your-subscription-id"
```

## 🚀 Quick Start

### Option 1: Bash Script (Linux/macOS/WSL)

```bash
# Make the script executable
chmod +x deploy-to-azure.sh

# Run the deployment
./deploy-to-azure.sh
```

### Option 2: PowerShell Script (Windows)

```powershell
# Run the deployment
.\deploy-to-azure.ps1
```

### Option 3: Manual Configuration

If you prefer to customize the deployment, edit the `azure-config.json` file:

```json
{
  "resourceGroupName": "rg-fastapi-agent",
  "location": "eastus2",
  "acrName": "acrfastapieu2",
  "appServicePlanName": "asp-fastapi-agent",
  "appServiceName": "app-fastapi-agent-{timestamp}",
  "imageName": "fastapi-auto-signin-agent",
  "imageTag": "latest"
}
```

## 🔧 Deployment Process

The deployment scripts perform the following steps:

### 1. Infrastructure Setup
- Create Resource Group in specified region
- Create Azure Container Registry (Basic SKU)
- Create App Service Plan (Linux, B1 SKU)

### 2. Container Build & Push
- Build Docker image locally
- Tag image for ACR
- Push image to Azure Container Registry

### 3. App Service Configuration
- Create App Service with system-assigned managed identity
- Grant AcrPull role to managed identity for ACR access
- Configure container settings
- Deploy environment variables from `.env` file

### 4. Security Configuration
- Enable system-assigned managed identity
- Configure ACR authentication via managed identity
- Remove username/password credentials
- Set up secure container image pulling

## 🔐 Security Features

### Managed Identity Authentication
- **System-assigned managed identity** eliminates need for credentials
- **AcrPull role** grants minimum required permissions to ACR
- **Automatic credential rotation** managed by Azure
- **No stored passwords** in configuration or environment variables

### Network Security
- Container Registry access restricted to authorized identities
- HTTPS-only communication enforced
- App Service runs in isolated container environment

## 📁 Project Structure

```
.
├── deploy-to-azure.sh          # Bash deployment script
├── deploy-to-azure.ps1         # PowerShell deployment script
├── azure-config.json           # Deployment configuration
├── Dockerfile                  # Container image definition
├── .env                        # Environment variables (create from .env.TEMPLATE)
├── .env.TEMPLATE               # Environment variables template
├── requirements.txt            # Python dependencies
├── app.py                      # Main FastAPI application
└── src/                        # Source code directory
    ├── main.py
    ├── fastapi_agent.py
    └── ...
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from `.env.TEMPLATE` and configure:

```bash
# Azure Service Connections
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=your-client-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=your-client-secret
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=your-tenant-id

# Application Settings
HOST=0.0.0.0
PORT=3978

# Bot Framework Settings (if applicable)
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=GRAPH
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GITHUB__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=GITHUB
```

### Deployment Configuration

Modify `azure-config.json` to customize:

- **Resource names** and **location**
- **Container image** names and tags
- **Resource group** organization

## 🔄 CI/CD Integration

### GitHub Actions

Example workflow for automated deployment:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy to Azure
      run: ./deploy-to-azure.sh
```

### Manual Deployment

For manual deployments, both scripts support:
- **Incremental updates** (rebuild and redeploy)
- **Resource cleanup** (delete and recreate)
- **Environment-specific** configurations

## 🐛 Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Check Azure CLI authentication
az account show

# Re-authenticate if needed
az login
```

#### Image Pull Failures
```bash
# Verify managed identity configuration
az webapp config show --name your-app-name --resource-group your-rg --query "acrUseManagedIdentityCreds"

# Check role assignments
az role assignment list --assignee $(az webapp identity show --name your-app-name --resource-group your-rg --query principalId -o tsv)
```

#### Container Startup Issues
```bash
# Check application logs
az webapp log tail --name your-app-name --resource-group your-rg

# Verify container configuration
az webapp config container show --name your-app-name --resource-group your-rg
```

### Log Analysis

Access detailed logs via:
- **Azure Portal**: App Service → Monitoring → Log stream
- **Azure CLI**: `az webapp log tail --name <app-name> --resource-group <rg-name>`
- **Application Insights**: For advanced monitoring and analytics

## 🔧 Maintenance

### Updates and Scaling

```bash
# Scale the App Service Plan
az appservice plan update --name asp-fastapi-agent --resource-group rg-fastapi-agent --sku S1

# Update application settings
az webapp config appsettings set --name your-app-name --resource-group your-rg --settings KEY=VALUE

# Restart the application
az webapp restart --name your-app-name --resource-group your-rg
```

### Monitoring

- **Application health**: Monitor `/health` endpoint
- **Performance metrics**: Available in Azure Portal
- **Cost tracking**: Use Azure Cost Management tools

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the deployment scripts
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review Azure App Service documentation
- Open an issue in this repository

---

**Last Updated**: August 16, 2025  
**Azure Region**: East US 2  
**Application Status**: ✅ Running
