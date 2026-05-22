# Phase 10 deployment wrapper.
#
# This does not push or deploy to cloud automatically. It runs the production readiness
# checks and prints the exact Render/Vercel actions to take.
param(
    [switch]$Docker
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

Write-Host ""
Write-Host "=== Phase 10 deploy readiness ===" -ForegroundColor Cyan

.\phase-10\scripts\verify_phase10.ps1
if ($LASTEXITCODE -ne 0) { throw "Phase 10 verification failed" }

if ($Docker) {
    .\scripts\verify_deploy_ready.ps1 -Docker
} else {
    .\scripts\verify_deploy_ready.ps1
}
if ($LASTEXITCODE -ne 0) { throw "Deploy readiness failed" }

Write-Host ""
Write-Host "Ready for deployment." -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Commit and push the repo."
Write-Host "  2. Render reads render.yaml for the backend."
Write-Host "  3. Vercel deploys phase-8/web with NEXT_PUBLIC_API_URL set to the Render URL."
Write-Host "  4. GitHub Actions will run .github/workflows/corpus-refresh.yml on schedule/manual dispatch."
