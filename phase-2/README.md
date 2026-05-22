# Phase 2 — Corpus ingestion (fetch + parse)

Implements **Phase 2** of [`../docs/architecture.md`](../docs/architecture.md): HTTP fetch with retries and rate limiting, `robots.txt` compliance, atomic HTML snapshots, Groww HTML section extraction, and normalized JSON documents.

## Layout

- `mf_ingest/` — Python package (fetcher, parser, pipeline, CLI)
- `data/raw/<source_id>/` — snapshotted HTML (`YYYY-MM-DD__<sha256>.html`)
- `data/raw/.cache/etags.json` — conditional GET cache (ETag / Last-Modified)
- `data/processed/` — per-source normalized JSON + `ingest_manifest.json`

Sources are read from **`../phase-1/config/sources.yaml`** (Phase 1 remains the single source registry).

## Install

From **`phase-2/`**:

```powershell
pip install -e ".[dev]"
```

## Run ingestion

Fetches all 10 Groww URLs, validates shape (soft-404 / Cloudflare), parses sections, writes snapshots + JSON.

```powershell
cd phase-2
mf-ingest
# or:
python -m mf_ingest.cli
```

Options:

| Flag | Meaning |
|------|---------|
| `--dry-run` | Fetch + parse only; do not write snapshots or processed JSON |
| `--strict` | Exit code 1 if any URL fails (default: yes for CI) |
| `--no-strict` | Continue on per-URL failure; still write manifest with errors |

## Verify registry URLs (Phase 1.6 + smoke)

Lightweight check: load Phase 1 `sources.yaml`, fetch `robots.txt`, assert each URL is allowed for our User-Agent, then **HEAD** (or **GET** if HEAD returns 405) with **≤ 1 req/s** between scheme requests.

```powershell
cd phase-2
mf-ingest verify
# or:
python -m mf_ingest.cli verify
```

From **`phase-1/`** after offline checks:

```powershell
verify-phase1 --with-network
```

## Tests

From repo root (see root `pytest.ini`) or from `phase-2/`:

```powershell
cd phase-2
pytest
```

Network-only checks are opt-in: `pytest -m internet` (mark not used yet; reserved for live Groww fetches).

## Exit criteria (architecture §2.3)

- Idempotent re-run when content unchanged (304 / ETag skip + same hash skips rewrite where applicable)
- All 10 snapshots on success path under `data/raw/<source_id>/`
- Error report in manifest for failures; `--strict` fails the process
