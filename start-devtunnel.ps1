#!/usr/bin/env pwsh
# Start DevTunnel and FastAPI Bot for local development
# Usage: .\start-devtunnel.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FastAPI Bot - DevTunnel Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$TUNNEL_NAME = "fastapi-bot-euw"
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

# Delete existing tunnel and recreate for fresh start
Write-Host "Deleting existing tunnel '$TUNNEL_NAME' if it exists..." -ForegroundColor Yellow
$deleteResult = devtunnel delete $TUNNEL_NAME --force 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Existing tunnel deleted" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No existing tunnel found to delete" -ForegroundColor DarkGray
}

Write-Host "Creating new tunnel '$TUNNEL_NAME'..." -ForegroundColor Yellow
devtunnel create $TUNNEL_NAME --allow-anonymous

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create tunnel!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Tunnel created" -ForegroundColor Green

# Add port to tunnel (required by newer CLI)
Write-Host "Adding port $PORT to tunnel..." -ForegroundColor Yellow
devtunnel port create $TUNNEL_NAME --port-number $PORT

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to add port to tunnel!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Port added" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting DevTunnel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start DevTunnel in separate window (non-blocking)
Write-Host "Starting tunnel host in separate window..." -ForegroundColor Yellow
$tunnelProcess = Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-Command", "devtunnel host $TUNNEL_NAME" -PassThru -WindowStyle Normal

Write-Host "✅ DevTunnel process started (PID: $($tunnelProcess.Id))" -ForegroundColor Green

# Wait for tunnel to be ready and get URL
Write-Host "Waiting for tunnel to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Retrieve tunnel info with retry logic
$tunnelUrl = $null
$maxRetries = 5
$retryCount = 0

while ($retryCount -lt $maxRetries -and -not $tunnelUrl) {
    try {
        $tunnelInfoJson = devtunnel show $TUNNEL_NAME --json 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0 -and $tunnelInfoJson) {
            $tunnelInfo = $tunnelInfoJson | ConvertFrom-Json
            
            # Parse the new JSON structure: tunnel.ports[0].portUri
            if ($tunnelInfo.tunnel -and $tunnelInfo.tunnel.ports -and $tunnelInfo.tunnel.ports.Count -gt 0) {
                $tunnelUrl = $tunnelInfo.tunnel.ports[0].portUri
                Write-Host "✅ Retrieved tunnel URL from JSON" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "⚠️  Retry $($retryCount + 1)/$maxRetries..." -ForegroundColor Yellow
    }
    
    if (-not $tunnelUrl) {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Start-Sleep -Seconds 3
        }
    }
}

if (-not $tunnelUrl) {
    Write-Host "❌ Could not retrieve tunnel URL after $maxRetries attempts" -ForegroundColor Red
    Write-Host "ℹ️  Check tunnel manually with: devtunnel show $TUNNEL_NAME" -ForegroundColor Yellow
    $tunnelUrl = "[URL not available - check manually]"
}

Write-Host "✅ DevTunnel is running!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Tunnel Information" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Public URL: $tunnelUrl" -ForegroundColor Green
Write-Host "Bot Endpoint: ${tunnelUrl}api/messages" -ForegroundColor Green
Write-Host ""
Write-Host "Update your Azure Bot messaging endpoint to:" -ForegroundColor Yellow
Write-Host "  ${tunnelUrl}api/messages" -ForegroundColor White
Write-Host ""

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
    Write-Host "Stopping DevTunnel process..." -ForegroundColor Yellow
    
    if ($tunnelProcess -and -not $tunnelProcess.HasExited) {
        Stop-Process -Id $tunnelProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "✅ DevTunnel process stopped" -ForegroundColor Green
    }
    
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
