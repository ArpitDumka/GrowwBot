# Free TCP port 8000 and stop mf-api / uvicorn (including --reload parent + worker).
param(
    [int]$Port = 8000
)

$ErrorActionPreference = "SilentlyContinue"

function Stop-ProcId {
    param([int]$procId)
    if ($procId -le 0) { return }
    try {
        $p = Get-Process -Id $procId -ErrorAction Stop
        Write-Host "Stopping PID $procId ($($p.ProcessName))..." -ForegroundColor Yellow
        Stop-Process -Id $procId -Force -ErrorAction Stop
    } catch {
        Write-Host "Could not stop PID ${procId}: $($_.Exception.Message)" -ForegroundColor Red
    }
}

$targetPids = [System.Collections.Generic.HashSet[int]]::new()

# 1) Anything listening on the API port (skip PID 0 = system idle placeholder)
foreach ($conn in Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    [void]$targetPids.Add([int]$conn.OwningProcess)
}

# 2) mf-api / uvicorn processes (reload often leaves workers after Ctrl+C)
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $cmd = $_.CommandLine
        $cmd -and (
            $cmd -match 'mf-api(\.exe)?\s+serve' -or
            $cmd -match 'uvicorn' -and $cmd -match "port(\s+|=)$Port|:$Port"
        )
    } |
    ForEach-Object { [void]$targetPids.Add([int]$_.ProcessId) }

if ($targetPids.Count -eq 0) {
    Write-Host "Port $Port is free (no mf-api / uvicorn found)." -ForegroundColor Green
    exit 0
}

foreach ($procId in ($targetPids | Where-Object { $_ -gt 0 } | Sort-Object)) {
    Stop-ProcId $procId
}

Start-Sleep -Milliseconds 800

$still = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.OwningProcess -gt 0 } |
    Select-Object -ExpandProperty OwningProcess -Unique

$apiUp = $false
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/healthz" -UseBasicParsing -TimeoutSec 2
    $apiUp = ($r.StatusCode -eq 200)
} catch {}

if ($still -or $apiUp) {
    Write-Host ""
    Write-Host "Port $Port still busy or /healthz still OK - stopping python workers (mf-api / uvicorn)..." -ForegroundColor Yellow
    Get-Process -Name python -ErrorAction SilentlyContinue | ForEach-Object { Stop-ProcId $_.Id }
    Start-Sleep -Milliseconds 800
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$Port/healthz" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $apiUp = $true
    } catch {
        $apiUp = $false
    }
}

if ($apiUp) {
    Write-Host ""
    Write-Host "API still responding on port $Port." -ForegroundColor Yellow
    Write-Host "  Focus the terminal where you ran .\scripts\run_backend.ps1 and press Ctrl+C twice." -ForegroundColor Yellow
    Write-Host "  Or close that terminal tab, then run .\scripts\stop_backend.ps1 again." -ForegroundColor Yellow
} else {
    Write-Host "Done. Port $Port is free." -ForegroundColor Green
}
