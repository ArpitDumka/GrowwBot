# Open two PowerShell windows: backend (8000) + Next.js frontend (3000).
# Usage:
#   .\scripts\run_local.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

# Make sure port 8000 is free before opening windows
& "$root\scripts\stop_backend.ps1" | Out-Null

Write-Host "Opening backend terminal (http://127.0.0.1:8000)..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-Command",
    "& '$root\scripts\run_backend.ps1'"
)

Write-Host "Opening Next.js terminal (http://localhost:3000)..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-Command",
    "& '$root\scripts\run_frontend.ps1'"
)

Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000  (docs: /docs)" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Stop backend later: .\scripts\stop_backend.ps1" -ForegroundColor Yellow
