$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "No .venv found. Creating environment and installing dependencies..." -ForegroundColor Yellow
    python -m venv .venv
    & $python -m pip install --quiet --upgrade pip
    & $python -m pip install --quiet -r requirements.txt
}

Write-Host ""
Write-Host "Open your browser at:  http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server."
Write-Host ""

& $python app.py
