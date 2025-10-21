#!/usr/bin/env pwsh
# Start DevTunnel and FastAPI Bot for local development
# Usage: .\start-devtunnel.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FastAPI Bot - DevTunnel Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$TUNNEL_NAME = "fastapi-bot"
$PORT = 3978

# Check if DevTunnel is installed
Write-Host "Checking DevTunnel installation..." -ForegroundColor Yellow
$devtunnel = Get-Command devtunnel -ErrorAction SilentlyContinue

if (-not $devtunnel) {
    Write-Host "❌ DevTunnel not found!" -ForegroundColor Red
    Write-Host "Install with: winget install Microsoft.devtunnel" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ DevTunnel found" -ForegroundColor Green
Write-Host ""

# Check if user is logged in
Write-Host "Checking DevTunnel authentication..." -ForegroundColor Yellow
$userCheck = devtunnel user show 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Not logged in to DevTunnel" -ForegroundColor Yellow
    Write-Host "Logging in..." -ForegroundColor Yellow
    devtunnel user login
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Login failed!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Authenticated" -ForegroundColor Green
Write-Host ""

# Check if tunnel exists
Write-Host "Checking for existing tunnel '$TUNNEL_NAME'..." -ForegroundColor Yellow
$tunnelExists = devtunnel show $TUNNEL_NAME 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Tunnel '$TUNNEL_NAME' not found. Creating..." -ForegroundColor Yellow
    devtunnel create $TUNNEL_NAME --allow-anonymous
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create tunnel!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Tunnel created" -ForegroundColor Green
} else {
    Write-Host "✅ Tunnel exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting DevTunnel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start DevTunnel in background job
Write-Host "Starting tunnel on port $PORT..." -ForegroundColor Yellow
$tunnelJob = Start-Job -ScriptBlock {
    param($name)
    devtunnel host $name
} -ArgumentList $TUNNEL_NAME

# Wait for tunnel to initialize
Start-Sleep -Seconds 3

# Get tunnel URL
$tunnelInfo = devtunnel show $TUNNEL_NAME --output json | ConvertFrom-Json
$tunnelUrl = $tunnelInfo.uri

if ($tunnelUrl) {
    Write-Host "✅ DevTunnel is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Tunnel Information" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Public URL: $tunnelUrl" -ForegroundColor Green
    Write-Host "Bot Endpoint: ${tunnelUrl}/api/messages" -ForegroundColor Green
    Write-Host ""
    Write-Host "Update your Azure Bot messaging endpoint to:" -ForegroundColor Yellow
    Write-Host "  ${tunnelUrl}/api/messages" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  Could not retrieve tunnel URL" -ForegroundColor Yellow
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting FastAPI Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "⚠️  Virtual environment not found at .\venv" -ForegroundColor Yellow
    Write-Host "Continuing without venv..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting FastAPI application..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop both DevTunnel and FastAPI" -ForegroundColor Yellow
Write-Host ""

# Cleanup function
function Cleanup {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Shutting down..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Stopping DevTunnel..." -ForegroundColor Yellow
    Stop-Job $tunnelJob -ErrorAction SilentlyContinue
    Remove-Job $tunnelJob -ErrorAction SilentlyContinue
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

# Register cleanup on exit
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }

# Run FastAPI
try {
    python main.py
} catch {
    Write-Host "❌ Error running FastAPI: $_" -ForegroundColor Red
} finally {
    Cleanup
}
