# Build RAG corpus per docs/architecture.md Phase 3-4:
#   Phase 2 ingest -> Phase 3 chunk -> Phase 4 embed (BGE + Chroma + BM25)
#
# Usage (from repo root):
#   .\scripts\build_corpus.ps1
#   .\scripts\build_corpus.ps1 -SkipIngest      # reuse phase-2/data/processed/
#   .\scripts\build_corpus.ps1 -SkipIndex       # chunk only, no embeddings
#   .\scripts\build_corpus.ps1 -TestEmbedder    # fast hashing embedder (CI)
param(
    [switch]$SkipIngest,
    [switch]$SkipIndex,
    [switch]$TestEmbedder,
    [switch]$NoStrict
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Require-Cmd($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Command not found: $name. Install phase packages first (see below)."
    }
}

Write-Host ""
Write-Host "=== RAG corpus build (chunk + embed) ===" -ForegroundColor Cyan
Write-Host "  Repo: $root" -ForegroundColor Gray
Write-Host ""

Write-Host "Checking CLI tools..." -ForegroundColor Gray
if (-not $SkipIngest) { Require-Cmd "mf-ingest" }
Require-Cmd "mf-chunk"
if (-not $SkipIndex) { Require-Cmd "mf-build-index" }

$pyArgs = @("-m", "ingest.pipeline")
if ($SkipIngest) { $pyArgs += "--skip-ingest" }
if ($SkipIndex) { $pyArgs += "--skip-index" }
if ($TestEmbedder) { $pyArgs += "--test-embedder" }
if ($NoStrict) { $pyArgs += "--no-strict" }

$env:PYTHONPATH = @(
    "$root\phase-1", "$root\phase-2", "$root\phase-3", "$root\phase-4"
) -join [System.IO.Path]::PathSeparator

Push-Location "$root\phase-1"
try {
    python @pyArgs
    if ($LASTEXITCODE -ne 0) { throw "Corpus build failed (exit $LASTEXITCODE)" }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Done. Restart the backend to load the new index:" -ForegroundColor Green
Write-Host "  .\scripts\run_backend.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "If CLIs are missing, install once:" -ForegroundColor Gray
Write-Host "  pip install -e phase-2 phase-3 phase-4" -ForegroundColor Gray
Write-Host ""
