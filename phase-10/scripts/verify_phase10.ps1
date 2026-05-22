# Verify Phase 10 deployment, scheduler, observability, and security checks.
#
# Fast default:
#   .\phase-10\scripts\verify_phase10.ps1
#
# Include a safe scheduler execution:
#   .\phase-10\scripts\verify_phase10.ps1 -RunSchedulerSmoke
param(
    [switch]$RunSchedulerSmoke
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$env:PYTHONPATH = @(
    "$root\phase-10",
    "$root\phase-2",
    "$root\phase-3",
    "$root\phase-4"
) -join [System.IO.Path]::PathSeparator

Write-Host ""
Write-Host "=== Phase 10 verification ===" -ForegroundColor Cyan

Write-Host "`nInstall/check Phase 10 package..." -ForegroundColor Gray
python -m pip install -q -e "phase-10[dev]"
if ($LASTEXITCODE -ne 0) { throw "Failed to install phase-10" }

Write-Host "`nPhase 10 unit tests:" -ForegroundColor Gray
Push-Location "$root\phase-10"
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Phase 10 pytest failed" }
Pop-Location

Write-Host "`nOperational readiness:" -ForegroundColor Gray
mf-phase10-check
if ($LASTEXITCODE -ne 0) { throw "Phase 10 readiness check failed" }

Write-Host "`nLog safety scan:" -ForegroundColor Gray
mf-log-scan
if ($LASTEXITCODE -ne 0) { throw "Phase 10 log scan failed" }

if ($RunSchedulerSmoke) {
    Write-Host "`nScheduler smoke run:" -ForegroundColor Gray
    .\phase-10\scripts\run_scheduler_once.ps1 -SkipIngest -SkipIndex
}

Write-Host ""
Write-Host "Phase 10 verification passed." -ForegroundColor Green
