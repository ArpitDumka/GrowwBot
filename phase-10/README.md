# Phase 10 - Deployment, Observability & Maintenance

This folder contains the Phase 10 implementation:

- deployment/readiness wrapper
- scheduled corpus refresh runner
- active GitHub Actions scheduler template
- operational checks
- log-safety scan
- runbooks for common incidents

## 10.1 Deployment

Run readiness checks:

```powershell
.\phase-10\scripts\deploy.ps1
```

If `make` is available:

```bash
make deploy
```

The script does not push or deploy automatically. It verifies the repo and prints the Render/Vercel steps.

## 10.2 Refresh Scheduler

The refresh pipeline is:

```text
mf-ingest --no-strict
mf-chunk --summary
mf-build-index
mf-build-index export -o phase-4/data/index/embeddings.parquet
mf-build-index verify
```

Install the packages once from the repository root:

```powershell
pip install -e phase-2 -e phase-3 -e "phase-4[export]" -e phase-10
```

Run the scheduler once locally, using existing processed data and a fast test embedder:

```powershell
.\phase-10\scripts\run_scheduler_once.ps1 -SkipIngest -TestEmbedder
```

Run the real local refresh:

```powershell
.\phase-10\scripts\run_scheduler_once.ps1
```

The active GitHub Actions scheduler lives at:

```text
.github/workflows/corpus-refresh.yml
```

The source template also lives at:

```text
phase-10/workflows/corpus-refresh.yml
```

### Automated deploy path (no manual artifact copy)

After each successful nightly (or manual) refresh, the workflow **commits and pushes** `phase-3/data/chunks.jsonl`, `phase-4/data/index/`, and `phase-10/reports/last_refresh.json` to `main`. That updates chunk `last_updated` dates (footer: `Last updated from sources: YYYY-MM-DD`).

**Render** must have **Auto-Deploy** enabled for `main` so each push rebuilds the Docker image with the new index.

Manual run options:

- **test_embedder** or **skip_index** — does not push (smoke / partial runs).
- **skip_push** — refresh + artifact only, no git push.

## 10.3 Observability

```powershell
.\phase-10\scripts\verify_phase10.ps1
mf-log-scan
```

See `observability.md`.

## 10.4 Security & Compliance

See `security.md` and the PII tests in Phase 5.

## 10.5 Runbooks

See `runbooks/`.
