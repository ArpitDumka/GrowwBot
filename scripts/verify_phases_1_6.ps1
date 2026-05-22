# Verify Phases 1-6 (run from repo root after pip install -e in each phase package)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Step($name, $cmd) {
    Write-Host "`n=== $name ===" -ForegroundColor Cyan
    Push-Location $root
    try {
        Invoke-Expression $cmd
        if ($LASTEXITCODE -ne 0) { throw "Failed: $name" }
    } finally {
        Pop-Location
    }
}

Step "Phase 1" "cd phase-1; python -m scripts.verify_phase1"
Step "Phase 2 (network)" "cd phase-2; python -m mf_ingest.cli verify"
Step "Phase 3 summary" "cd phase-3; python -m mf_clean.cli --summary"
Step "Phase 4 index" "cd phase-4; python -m mf_index.cli verify"
Step "Phase 5 guard" "cd phase-5; python -m mf_guard.cli verify"
Step "Phase 6 retrieve" "cd phase-6; python -m mf_retrieve.cli verify --test-reranker"
Step "Phase 7 compose" "cd phase-7; python -m mf_compose.cli verify --test-reranker"
Step "Phase 8 API" "cd phase-8; python -m mf_api.cli verify --test-reranker"
Step "pytest" "pytest -q"

Write-Host "`nAll phase 1-8 checks passed." -ForegroundColor Green
