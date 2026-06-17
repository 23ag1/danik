# Fraud Monitor — установка на Windows
# Запуск: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Fraud Monitor — установка ===" -ForegroundColor Cyan

# Проверить зависимости
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Нужен Python 3.10+  ->  https://python.org/downloads" -ForegroundColor Red; exit 1
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Нужен Node.js 18+  ->  https://nodejs.org" -ForegroundColor Red; exit 1
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "Нужен npm (входит в Node.js)" -ForegroundColor Red; exit 1
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# Python окружение
if (-not (Test-Path ".venv\Scripts\activate.ps1")) {
    Write-Host "--- создаю .venv ---" -ForegroundColor Yellow
    python -m venv .venv
}
& .venv\Scripts\Activate.ps1

Write-Host "--- pip install ---" -ForegroundColor Yellow
pip install -q -r requirements.txt

# ML модель
if (-not (Test-Path "models\fraud_pipeline.joblib")) {
    Write-Host "--- обучаю ML модель (1-2 мин) ---" -ForegroundColor Yellow
    python -m app.ml.train
} else {
    Write-Host "--- ML модель уже есть ---" -ForegroundColor Green
}

# Фронтенд
if (-not (Test-Path "frontend\dist")) {
    Write-Host "--- сборка фронтенда ---" -ForegroundColor Yellow
    Set-Location frontend
    npm install --silent
    npm run build
    Set-Location $Root
} else {
    Write-Host "--- фронтенд уже собран ---" -ForegroundColor Green
}

# Запустить сервер для seed-данных
Write-Host "--- загружаю демо-данные ---" -ForegroundColor Yellow
$PORT = if ($env:PORT) { $env:PORT } else { "8888" }

# Остановить старый процесс если есть
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$srvProc = Start-Process -FilePath ".venv\Scripts\uvicorn.exe" `
    -ArgumentList "app.main:app --host 127.0.0.1 --port $PORT" `
    -PassThru -WindowStyle Hidden

# Ждать запуска
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $ready = $true; break
    } catch {}
}
if (-not $ready) { Write-Host "Сервер не запустился" -ForegroundColor Red; exit 1 }

python scripts/seed_demo.py "http://127.0.0.1:$PORT"
python scripts/seed_sources.py

$srvProc | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Финальный запуск в фоне
Write-Host "--- запускаю сервер ---" -ForegroundColor Yellow
Start-Process -FilePath ".venv\Scripts\uvicorn.exe" `
    -ArgumentList "app.main:app --host 0.0.0.0 --port $PORT" `
    -WindowStyle Hidden

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host " Fraud Monitor запущен!" -ForegroundColor Green
Write-Host " http://localhost:$PORT" -ForegroundColor Cyan
Write-Host " Swagger: http://localhost:$PORT/docs" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Green

# Открыть браузер
Start-Process "http://localhost:$PORT"
