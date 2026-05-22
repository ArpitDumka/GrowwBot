# Free TCP ports used by the Next.js dev server (3000 + 3001 by default).
# Kills any orphaned node processes still holding them.
param(
    [int[]]$Ports = @(3000, 3001)
)

$ErrorActionPreference = "SilentlyContinue"

foreach ($Port in $Ports) {
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if (-not $conns) {
        Write-Host "Port $Port is free." -ForegroundColor Green
        continue
    }

    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        try {
            $p = Get-Process -Id $procId -ErrorAction Stop
            Write-Host "Stopping PID $procId ($($p.ProcessName)) on port $Port..." -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction Stop
        } catch {
            Write-Host "Could not stop PID ${procId}: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Start-Sleep -Milliseconds 700
Write-Host "Done." -ForegroundColor Green
