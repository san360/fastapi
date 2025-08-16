# Docker Run Script for FastAPI Auto Sign-In Agent (PowerShell)
# This script builds and runs the application using Docker

$ErrorActionPreference = "Stop"

Write-Host "🐳 FastAPI Auto Sign-In Agent - Docker Deployment" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "📝 Please copy .env.docker to .env and configure your Azure credentials:" -ForegroundColor Yellow
    Write-Host "   Copy-Item .env.docker .env" -ForegroundColor White
    Write-Host "   # Then edit .env with your actual values" -ForegroundColor Gray
    Write-Host "   # Make sure to set HOST=0.0.0.0 for Docker" -ForegroundColor Yellow
    exit 1
}

# Build the Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
docker build -t fastapi-auto-signin-agent .

# Stop existing container if running
Write-Host "🛑 Stopping existing container (if any)..." -ForegroundColor Yellow
try {
    docker-compose down 2>$null
} catch {
    # Ignore errors if no containers are running
}

# Run the container
Write-Host "🚀 Starting new container..." -ForegroundColor Green
docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Container started successfully!" -ForegroundColor Green
    Write-Host "📊 Container status:" -ForegroundColor Cyan
    docker ps --filter name=fastapi-auto-signin-agent --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"
} else {
    Write-Host "❌ Failed to start container!" -ForegroundColor Red
    Write-Host "📋 Check logs with: docker-compose logs fastapi-agent" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🌐 Application URLs:" -ForegroundColor Cyan
Write-Host "   • Health Check: http://localhost:3978/health" -ForegroundColor White
Write-Host "   • API Docs:     http://localhost:3978/docs" -ForegroundColor White
Write-Host "   • Root:         http://localhost:3978/" -ForegroundColor White

Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Cyan
Write-Host "   • View logs:    docker-compose logs -f fastapi-agent" -ForegroundColor White
Write-Host "   • Stop:         docker-compose down" -ForegroundColor White
Write-Host "   • Restart:      docker-compose restart fastapi-agent" -ForegroundColor White
Write-Host "   • Rebuild:      docker-compose up -d --build" -ForegroundColor White
