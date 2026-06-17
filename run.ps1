# Fraud Monitor - start server (Windows)
# Run: powershell -ExecutionPolicy Bypass -File run.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
& .venv\Scripts\Activate.ps1
$PORT = if ($env:PORT) { $env:PORT } else { "8888" }
Write-Host "Fraud Monitor: http://localhost:$PORT" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop. Keep this window open." -ForegroundColor Yellow
.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port $PORT
