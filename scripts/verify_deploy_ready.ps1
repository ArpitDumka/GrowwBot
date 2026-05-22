# Pre-push / pre-deploy checklist (Render + Vercel).
# Run from repository root: .\scripts\verify_deploy_ready.ps1
# Optional: .\scripts\verify_deploy_ready.ps1 -Docker

param(
    [switch]$Docker
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$fail = 0
function Check($label, $path) {
    if (Test-Path $path) {
        Write-Host "  OK  $label"
    } else {
        Write-Host "  FAIL $label - missing: $path" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "`n=== Deploy readiness (Render API + Vercel UI) ===`n"

Write-Host "Deploy config files:"
Check "render.yaml" "$Root\render.yaml"
Check "Dockerfile" "$Root\Dockerfile"
Check ".dockerignore" "$Root\.dockerignore"
Check "Vercel config" "$Root\phase-8\web\vercel.json"
Check "DEPLOY.md" "$Root\docs\DEPLOY.md"

Write-Host "`nRAG data (must be committed before git push):"
Check "chunks.jsonl" "$Root\phase-3\data\chunks.jsonl"
Check "index manifest" "$Root\phase-4\data\index\index_manifest.json"
Check "Chroma DB" "$Root\phase-4\data\index\chroma"
Check "BM25 index" "$Root\phase-4\data\index\bm25"

Write-Host "`nConfigs:"
Check "sources.yaml" "$Root\phase-1\config\sources.yaml"
Check "llm.yaml" "$Root\phase-1\config\llm.yaml"
Check "api.yaml" "$Root\phase-8\config\api.yaml"

Write-Host "`nFrontend:"
Check "package.json" "$Root\phase-8\web\package.json"
Check "package-lock.json" "$Root\phase-8\web\package-lock.json"
if (Test-Path "$Root\phase-8\web\node_modules") {
    Write-Host "  OK  node_modules (local only - not pushed; Vercel runs npm install)"
} else {
    Write-Host "  WARN node_modules missing - run: cd phase-8/web; npm install" -ForegroundColor Yellow
}

$manifest = Get-Content "$Root\phase-4\data\index\index_manifest.json" -Raw | ConvertFrom-Json
if ($manifest.chunks_path -match '^[A-Za-z]:\\') {
    Write-Host "  FAIL index_manifest chunks_path is Windows-absolute - rebuild index or fix manifest" -ForegroundColor Red
    $fail++
} else {
    Write-Host "  OK  index_manifest chunks_path is portable ($($manifest.chunks_path))"
}

Write-Host "`nPhase 8 API tests:"
Push-Location "$Root\phase-8"
python -m pytest phase8_tests -q --tb=no
if ($LASTEXITCODE -ne 0) { $fail++ }
Pop-Location

Write-Host "`nNext.js build:"
Push-Location "$Root\phase-8\web"
# Next.js may write to stderr on success; only trust exit code (not PowerShell NativeCommandError).
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
npm run build --silent 2>&1 | Out-Host
$buildExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($buildExit -ne 0) {
    Write-Host "  FAIL npm run build" -ForegroundColor Red
    $fail++
} else {
    Write-Host "  OK  npm run build"
}
Pop-Location

if ($Docker) {
    Write-Host "`nDocker image (slow, optional):"
    docker build -t mf-faq-api:test .
    if ($LASTEXITCODE -ne 0) { $fail++ } else { Write-Host "  OK  docker build" }
}

Write-Host ""
if ($fail -gt 0) {
    Write-Host "NOT READY: $fail check(s) failed. See docs/DEPLOY.md" -ForegroundColor Red
    exit 1
}

Write-Host "READY for git push -> Render (API) + Vercel (UI)." -ForegroundColor Green
Write-Host @"

Before pushing:
  1. Ensure .env is NOT staged (secrets: local .env or Render/Vercel dashboards).
  2. git add phase-3/data/chunks.jsonl phase-4/data/index/ ...
  3. git commit && git push
  4. Follow docs/DEPLOY.md for Render Blueprint + Vercel project setup.

"@
