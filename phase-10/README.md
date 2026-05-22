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
