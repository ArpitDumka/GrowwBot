# Start Phase 8 Next.js dev server on http://localhost:3001 (hot reload + refresh picks up edits).
#
# Typical workflow (no repeated restarts):
#   1. Run this script ONCE:   .\scripts\run_frontend.ps1
#   2. Change UI code (or let the AI apply patches)  - Next.js recompiles automatically.
#   3. Refresh the browser on http://localhost:3001  - or rely on Fast Refresh without refreshing.
#   Leave this terminal open. Do not re-run this script for every edit.
#
# Restart dev only when needed:
#   - Changed dependencies (npm install)
#   - Changed next.config.mjs / tsconfig
#   - Changed NEXT_PUBLIC_* or .env.local (need new process to pick them up)
#   - Corrupted .next (see -FreshNext)
#
# If file saves don't trigger rebuilds on Windows/network drives, before running:
#   $env:NEXT_DEV_POLL = "1"
#
# Usage:
#   .\scripts\run_frontend.ps1
#   .\scripts\run_frontend.ps1 -ApiUrl http://127.0.0.1:8001
#   .\scripts\run_frontend.ps1 -Force              # stop whatever is on the port and start again
#   .\scripts\run_frontend.ps1 -Force -FreshNext # wipe .next then start (fixes rare chunk errors)
param(
    [string]$ApiUrl = "http://127.0.0.1:8000",
    [int]$Port = 3001,
    [switch]$Force,
    [switch]$FreshNext
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$web = Join-Path $root "phase-8\web"
Set-Location $web

$portBusy = [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
if ($portBusy -and -not $Force) {
    Write-Host ""
    Write-Host "Port $Port is already in use  - the dev server is probably already running." -ForegroundColor Yellow
    Write-Host "  Keep that terminal open; save files and refresh: http://localhost:$Port" -ForegroundColor Green
    Write-Host "  To restart from scratch: .\scripts\run_frontend.ps1 -Force" -ForegroundColor Gray
    Write-Host "  To fully reset cache:    .\scripts\run_frontend.ps1 -Force -FreshNext" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# Free any process holding 3000 or 3001 so dev always lands on $Port (only when -Force or port was free)
& (Join-Path $root "scripts\stop_frontend.ps1") -Ports @(3000, 3001) | Out-Null

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies (first time)..." -ForegroundColor Cyan
    npm install
}

# Do not run `npm run build` while dev is running  - both default to `.next` and corrupt each other.
# Use `npm run build:safe` (writes to `.next-build`) or stop dev first.
#
# Optional full wipe  - only when .next is corrupted (missing chunk / MODULE_NOT_FOUND).
if ($FreshNext -and (Test-Path ".next")) {
    Write-Host "Removing .next (-FreshNext)..." -ForegroundColor Gray
    Remove-Item -Recurse -Force ".next"
} elseif (-not $FreshNext -and (Test-Path ".next")) {
    Write-Host "Keeping existing .next  - edits will compile on save; refresh the browser to load changes." -ForegroundColor Gray
}

# Write .env.local
$envLocal = ".env.local"
"NEXT_PUBLIC_API_URL=$ApiUrl" | Set-Content -Encoding utf8 -Path $envLocal
Write-Host "Wrote $envLocal -> NEXT_PUBLIC_API_URL=$ApiUrl" -ForegroundColor Gray

# Wait for backend health (up to 60s)
Write-Host ""
Write-Host "Waiting for backend at $ApiUrl ..." -ForegroundColor Cyan
$up = $false
for ($i = 1; $i -le 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$ApiUrl/healthz" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            $up = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
    if ($i % 5 -eq 0) {
        Write-Host ('  still waiting... (' + $i + 's)') -ForegroundColor Gray
    }
}

if (-not $up) {
    Write-Host ""
    Write-Host "WARN: Backend not reachable at $ApiUrl after 60s." -ForegroundColor Yellow
    Write-Host "      Start it: .\scripts\run_backend.ps1" -ForegroundColor Yellow
    Write-Host "      Starting Next.js anyway (refresh the page once the API is up)." -ForegroundColor Yellow
} else {
    Write-Host "Backend is healthy." -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Frontend (Next.js dev) ===" -ForegroundColor Cyan
Write-Host "  UI:      http://localhost:$Port   - leave running; save files + refresh to see UI changes" -ForegroundColor Green
Write-Host "  API URL: $ApiUrl" -ForegroundColor Green
Write-Host ""

npm run dev -- -p $Port
