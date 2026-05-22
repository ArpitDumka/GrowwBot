# Run Phase 10.2 scheduled corpus refresh once, locally.
#
# Fast local smoke test:
#   .\phase-10\scripts\run_scheduler_once.ps1 -SkipIngest -TestEmbedder
#
# Real local refresh:
#   .\phase-10\scripts\run_scheduler_once.ps1
param(
    [switch]$SkipIngest,
    [switch]$SkipIndex,
    [switch]$Strict,
    [switch]$TestEmbedder,
    [switch]$NoExport,
    [switch]$DryRun
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

$argsList = @("-m", "mf_phase10.refresh")
if ($SkipIngest) { $argsList += "--skip-ingest" }
if ($SkipIndex) { $argsList += "--skip-index" }
if ($Strict) { $argsList += "--strict" }
if ($TestEmbedder) { $argsList += "--test-embedder" }
if ($NoExport) { $argsList += "--no-export" }
if ($DryRun) { $argsList += "--dry-run" }

Write-Host ""
Write-Host "=== Phase 10.2 local scheduler run ===" -ForegroundColor Cyan
Write-Host "Repo: $root" -ForegroundColor Gray
Write-Host ""

python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "Phase 10.2 scheduler run failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Corpus refresh finished. Restart the API so it reloads chunks + index from disk:" -ForegroundColor Yellow
Write-Host "  .\scripts\stop_backend.ps1" -ForegroundColor Gray
Write-Host "  .\scripts\run_backend.ps1" -ForegroundColor Gray
Write-Host "Then send a NEW chat message in the UI (refresh alone keeps old answer text)." -ForegroundColor Yellow
Write-Host ""
