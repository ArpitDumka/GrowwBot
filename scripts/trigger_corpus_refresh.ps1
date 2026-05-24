# Trigger corpus-refresh via GitHub Actions workflow_dispatch (external cron uses the same API).
#
# Usage:
#   $env:GITHUB_PAT = "ghp_..."   # fine-grained: Actions Read+Write on GrowwBot
#   .\scripts\trigger_corpus_refresh.ps1
#
# Optional:
#   .\scripts\trigger_corpus_refresh.ps1 -SkipIndex -SkipPush -TestEmbedder

param(
    [string]$Repo = "ArpitDumka/GrowwBot",
    [string]$Ref = "main",
    [string]$WorkflowFile = "corpus-refresh.yml",
    [switch]$SkipIndex,
    [switch]$SkipPush,
    [switch]$TestEmbedder
)

$ErrorActionPreference = "Stop"

$token = $env:GITHUB_PAT
if (-not $token) {
    throw "Set GITHUB_PAT (GitHub PAT with Actions: Read and write on $Repo). See docs/EXTERNAL_CRON.md"
}

$body = @{
    ref = $Ref
    inputs = @{
        skip_index     = if ($SkipIndex) { "true" } else { "false" }
        skip_push      = if ($SkipPush) { "true" } else { "false" }
        test_embedder  = if ($TestEmbedder) { "true" } else { "false" }
    }
} | ConvertTo-Json -Depth 3 -Compress

$uri = "https://api.github.com/repos/$Repo/actions/workflows/$WorkflowFile/dispatches"
$headers = @{
    Authorization        = "Bearer $token"
    Accept               = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

Write-Host "Dispatching $WorkflowFile on $Repo @ $Ref ..." -ForegroundColor Cyan
Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -ContentType "application/json; charset=utf-8"
Write-Host "OK — workflow queued. Check: https://github.com/$Repo/actions/workflows/$WorkflowFile" -ForegroundColor Green
