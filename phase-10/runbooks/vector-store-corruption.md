# Runbook: Vector Store Corruption

## Symptoms

- Backend startup warning: index or Chroma load failed.
- `/healthz` works but chat returns retrieval errors.
- `mf-build-index verify` fails.

## Triage

```powershell
cd phase-4
mf-build-index verify
```

Check:

- `phase-4/data/index/index_manifest.json`
- `phase-4/data/index/chroma/`
- `phase-4/data/index/bm25/`
- `phase-4/data/index/backups/`

## Mitigation

1. Rebuild from chunks:
   ```powershell
   cd phase-4
   mf-build-index
   mf-build-index verify
   ```
2. If rebuild fails, restore from the latest backup under `phase-4/data/index/backups/`.
3. Restart backend after restoring or rebuilding.

