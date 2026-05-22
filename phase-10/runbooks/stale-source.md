# Runbook: Stale Or Failed Groww Source

## Symptoms

- `mf-corpus-refresh` fails during Phase 2 ingest.
- A scheme page returns 4xx/5xx.
- Answers show older `Last updated from sources`.

## Triage

```powershell
.\phase-10\scripts\run_scheduler_once.ps1 -SkipIndex
Get-Content .\phase-10\reports\last_refresh.json
```

Check `phase-2/data/processed/ingest_manifest.json` for failed source ids.

## Mitigation

1. If only one source failed temporarily, keep serving the previous committed index.
2. Retry manually:
   ```powershell
   .\phase-10\scripts\run_scheduler_once.ps1
   ```
3. If the page is down for more than 24 hours, mark the incident and keep the last known good corpus.

## Verification

```powershell
cd phase-4
mf-build-index verify
```

