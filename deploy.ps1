# AGI Prospection Hub — Deployment Script (PowerShell)
# This script handles both Docker and Local development environments.

param (
    [Parameter(Mandatory=$false)]
    [ValidateSet("docker", "local", "dev")]
    [string]$Mode = "docker",

    [Parameter(Mandatory=$false)]
    [switch]$Build = $false,

    [Parameter(Mandatory=$false)]
    [switch]$Stop = $false
)

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ComposeDir = Join-Path $PSScriptRoot "deployment\docker_compose"

function Show-Header {
    Clear-Host
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "   AGI PROSPECTION HUB DEPLOYMENT   " -ForegroundColor White -BackgroundColor Blue
    Write-Host "==========================================" -ForegroundColor Cyan
}

function Start-Docker {
    Write-Host "[DOCKER] Starting AGI Prospection in Docker mode..." -ForegroundColor Yellow
    
    if (!(Test-Path $ComposeDir)) {
        Write-Host "ERROR: Compose directory not found at $ComposeDir" -ForegroundColor Red
        return
    }

    Set-Location $ComposeDir
    
    if ($Stop) {
        Write-Host "[STOP] Stopping services..."
        docker compose down
        return
    }

    if ($Build) {
        Write-Host "[BUILD] Building images..."
        docker compose build
    }

    Write-Host "[LAUNCH] Launching containers..."
    docker compose up -d
    
    Write-Host "`nSUCCESS: AGI Prospection is running at http://localhost:3000" -ForegroundColor Green
    Write-Host "API Documentation: http://localhost:8080/docs" -ForegroundColor Gray
}

function Start-Local {
    Write-Host "[LOCAL] Starting AGI Prospection in Local mode..." -ForegroundColor Yellow
    
    # 1. Backend
    Write-Host "-> Starting Backend..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt; python main.py"
    
    # 2. Frontend
    Write-Host "-> Starting Frontend..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd web; npm install; npm run dev"
    
    Write-Host "`nSUCCESS: Local development servers started in separate windows." -ForegroundColor Green
}

function Start-Dev {
    Write-Host "[DEV] Starting in Hybrid mode (Infra in Docker + App Local)..." -ForegroundColor Yellow
    Set-Location $ComposeDir
    
    # 1. Start only infrastructure containers
    Write-Host "[INFRA] Starting Databases and Model Servers..." -ForegroundColor Gray
    docker compose up -d relational_db index cache inference_model_server indexing_model_server
    
    # 2. Wait for DB
    Write-Host "[WAIT] Waiting for databases to stabilize..." -ForegroundColor Gray
    Start-Sleep -Seconds 5

    # 3. Start Backend locally
    Write-Host "[APP] Starting Backend locally..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt; python main.py"
    
    # 4. Start Frontend locally
    Write-Host "[APP] Starting Frontend locally..." -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd web; npm install; npm run dev"
    
    Write-Host "`nSUCCESS: Hybrid Dev environment ready." -ForegroundColor Green
    Write-Host "Infra: Docker | App: Local (Hot-reload enabled)" -ForegroundColor Cyan
}

# Execution
Show-Header

if ($Mode -eq "docker") {
    Start-Docker
} elseif ($Mode -eq "dev") {
    Start-Dev
} else {
    Start-Local
}

Write-Host "`nDone!" -ForegroundColor Cyan
