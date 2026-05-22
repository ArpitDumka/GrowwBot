# Start Phase 8 API on http://127.0.0.1:8000.
# Frees the port if a previous process is still bound to it.
#
# Usage:
#   .\scripts\run_backend.ps1                # default: auto-reload on Python changes in phase-5/6/7
#   .\scripts\run_backend.ps1 -Port 8001
#   .\scripts\run_backend.ps1 -NoReload        # single process (restart manually after code edits)
#   .\scripts\run_backend.ps1 -NoFreePort    # do not kill existing process on port
param(
    [int]$Port = 8000,
    [switch]$NoReload,
    [switch]$NoFreePort
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\phase-8"

$envFile = Join-Path $root ".env"

# Prefer this repo's phase packages (guard / retrieval / compose) over global PYTHONPATH.
$phasePaths = @(
    "$root\phase-5", "$root\phase-6", "$root\phase-7", "$root\phase-4", "$root\phase-1"
)
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = ($phasePaths + @($env:PYTHONPATH)) -join [System.IO.Path]::PathSeparator
} else {
    $env:PYTHONPATH = ($phasePaths -join [System.IO.Path]::PathSeparator)
}

$hasGroqKey = $false
if (Test-Path $envFile) {
    $hasGroqKey = (Select-String -Path $envFile -Pattern '^GROQ_API_KEY=\S+' -Quiet)
}

if (-not $hasGroqKey) {
    Write-Host "WARN: No GROQ_API_KEY in $envFile - LLM answers will fail." -ForegroundColor Yellow
    Write-Host "      Add: GROQ_API_KEY=gsk_..." -ForegroundColor Yellow
}

# Free the port if needed
if (-not $NoFreePort) {
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            try {
                $p = Get-Process -Id $procId -ErrorAction Stop
                Write-Host "Freeing port $Port (stopping PID $procId / $($p.ProcessName))..." -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction Stop
            } catch {}
        }
        Start-Sleep -Milliseconds 800
    }
}

$apiArgs = @("serve", "--host", "127.0.0.1", "--port", "$Port", "--test-reranker")
if (-not $NoReload) {
    $apiArgs += "--reload"
}

$modeLabel = if ($hasGroqKey) { "live Groq" } else { "no GROQ key (chat will error)" }

Write-Host ""
Write-Host "=== Backend (FastAPI) ===" -ForegroundColor Cyan
Write-Host "  URL:    http://127.0.0.1:$Port"     -ForegroundColor Green
Write-Host "  Docs:   http://127.0.0.1:$Port/docs" -ForegroundColor Green
Write-Host "  Health: http://127.0.0.1:$Port/healthz" -ForegroundColor Green
Write-Host "  LLM:    $modeLabel" -ForegroundColor Gray
if (-not $NoReload) {
    Write-Host "  Reload: on (phase-5/6/7 edits apply automatically)" -ForegroundColor Gray
} else {
    Write-Host "  Reload: off - re-run this script after Python edits" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Start the frontend in another terminal:" -ForegroundColor Yellow
Write-Host "  .\scripts\run_frontend.ps1" -ForegroundColor Yellow
Write-Host ""

& mf-api @apiArgs
