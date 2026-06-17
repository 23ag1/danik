# Fraud Monitor - Windows installer
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Fraud Monitor - install ===" -ForegroundColor Cyan

# Check dependencies
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python 3.10+ required  ->  https://python.org/downloads" -ForegroundColor Red; exit 1
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js 18+ required  ->  https://nodejs.org" -ForegroundColor Red; exit 1
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "npm required (comes with Node.js)" -ForegroundColor Red; exit 1
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# Python venv
if (-not (Test-Path ".venv\Scripts\activate.ps1")) {
    Write-Host "--- creating .venv ---" -ForegroundColor Yellow
    python -m venv .venv
}
& .venv\Scripts\Activate.ps1

Write-Host "--- pip install ---" -ForegroundColor Yellow
pip install -q -r requirements.txt

# ML model
if (-not (Test-Path "models\fraud_pipeline.joblib")) {
    Write-Host "--- training ML model (1-2 min) ---" -ForegroundColor Yellow
    python -m app.ml.train
} else {
    Write-Host "--- ML model already exists ---" -ForegroundColor Green
}

# Frontend
if (-not (Test-Path "frontend\dist")) {
    Write-Host "--- building frontend ---" -ForegroundColor Yellow
    Set-Location frontend
    npm install --silent
    npm run build
    Set-Location $Root
} else {
    Write-Host "--- frontend already built ---" -ForegroundColor Green
}

# Seed demo data
Write-Host "--- seeding demo data ---" -ForegroundColor Yellow
$PORT = if ($env:PORT) { $env:PORT } else { "8888" }

Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$srvProc = Start-Process -FilePath ".venv\Scripts\uvicorn.exe" `
    -ArgumentList "app.main:app --host 127.0.0.1 --port $PORT" `
    -PassThru -WindowStyle Hidden

$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $ready = $true; break
    } catch {}
}
if (-not $ready) { Write-Host "Server failed to start" -ForegroundColor Red; exit 1 }

python scripts/seed_demo.py "http://127.0.0.1:$PORT"
python scripts/seed_sources.py

# Stop the temporary seed server and wait until the port is fully released
$srvProc | Stop-Process -Force -ErrorAction SilentlyContinue
for ($i = 0; $i -lt 10; $i++) {
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/health" -UseBasicParsing -TimeoutSec 1 | Out-Null
        Start-Sleep -Seconds 1   # still up, wait
    } catch { break }            # down -> port free
}

# Final run: a separate visible window that stays open after this script exits
Write-Host "--- starting server ---" -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "run.ps1"

# Wait until the final server answers before opening the browser
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $ready = $true; break
    } catch {}
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
if ($ready) {
    Write-Host " Fraud Monitor is running!" -ForegroundColor Green
} else {
    Write-Host " Server is starting (check the new window)" -ForegroundColor Yellow
}
Write-Host " http://localhost:$PORT" -ForegroundColor Cyan
Write-Host " Swagger: http://localhost:$PORT/docs" -ForegroundColor Cyan
Write-Host " To restart later: powershell -ExecutionPolicy Bypass -File run.ps1" -ForegroundColor Gray
Write-Host "======================================" -ForegroundColor Green

if ($ready) { Start-Process "http://localhost:$PORT" }
