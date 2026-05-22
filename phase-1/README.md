# Mutual Fund FAQ Assistant (RAG)

**Phase 1 root:** this directory (`phase-1/`) is the installable Python project and contains the full Phase 1 codebase. Repository-level docs stay one level up in `../docs/`.

> Facts-only Q&A over a curated corpus of mutual fund scheme pages.
> **Disclaimer**: Facts-only. No investment advice.

## What this is

A small, compliance-first Retrieval-Augmented Generation assistant that answers
**objective, verifiable** questions about a fixed set of HDFC mutual fund
schemes (e.g., expense ratio, exit load, lock-in, benchmark, min SIP). Every
answer is at most 3 sentences and carries exactly one citation back to the
source page. Advisory or comparison questions are politely refused.

Groww is the **reference product context**, not an additional source — see
[`../docs/architecture.md`](../docs/architecture.md) §1.3.

## Selected corpus

| | |
|---|---|
| AMC | **HDFC Mutual Fund** |
| Schemes | 10, spanning 5 SEBI categories (Mid Cap, Flexi Cap, Small Cap, ELSS, Thematic, Sectoral, Commodities, Liquid) |
| Sources | The 10 Groww scheme pages listed in [`config/sources.yaml`](config/sources.yaml) — **corpus is closed** |

## Documentation

| | |
|---|---|
| Problem statement | [`../docs/problemStatement.md`](../docs/problemStatement.md) |
| Phase-wise architecture | [`../docs/architecture.md`](../docs/architecture.md) |
| Per-phase edge cases | [`../docs/edge-cases/README.md`](../docs/edge-cases/README.md) |

## Phase status

| Phase | Topic | Status |
|---|---|---|
| 1 | Source selection & corpus lock | **Implemented** |
| Phase 2 | Ingestion (fetch + parse) | **Implemented** in [`phase-2/`](../phase-2/README.md) |
| 3 | Cleaning, chunking, metadata | **§3.1–§3.4** in [`phase-3/`](../phase-3/README.md); §3.5+ / index TBD |
| 4 | Embedding & index build | Stubbed |
| 5 | Query understanding & guardrails | Stubbed |
| 6 | Retrieval | Stubbed |
| 7 | Answer composition (**Groq** LLM + output guard) | Config in [`config/llm.yaml`](config/llm.yaml); composer stub |
| 8 | UI / UX | Stubbed |
| 9 | Evaluation harness | Stubbed |
| 10 | Deployment & maintenance | Stubbed |

Each `*.py` stub is docstring-only and points at the architecture / edge-case
section that owns its design. **Exceptions:** `ingest/cleaner.py` and
`ingest/chunker.py` are pointer stubs — Phase 3.1–3.4 live in **`phase-3/mf_clean/`**.

## Layout (inside `phase-1/`)

```
phase-1/
├── README.md
├── pyproject.toml
├── config/                  # YAML configs (source of truth)
│   ├── sources.yaml         # exactly 10 Groww URLs (Phase 1)
│   ├── aliases.yaml         # scheme aliases (Phase 1)
│   └── sections.yaml        # Groww section synonyms (Phase 2 parser + Phase 3 chunker)
├── ingest/                  # Phase 1-4: fetch -> parse -> clean -> chunk -> index
├── retrieval/               # Phase 4 + 6
├── app/
│   ├── api.py               # Phase 7: FastAPI service
│   ├── guards/              # Phase 5 + 7 guardrails
│   ├── compose/             # Phase 7 composer + prompts
│   # Phase 8 UI lives in ../phase-8/web/ (Next.js on Vercel)
├── eval/                    # Phase 9 harness
├── tests/                   # pytest
├── scripts/
│   └── verify_phase1.py     # CLI runner for Phase 1 exit criteria
└── data/
    ├── raw/                 # snapshotted Groww HTML (gitignored)
    └── processed/           # chunked JSONL + vector store (gitignored)
```

## Quickstart (Phase 1)

Requires **Python 3.11+**. From the **repository root**, run `cd phase-1`
first. If your shell is already **inside** this `phase-1/` folder, skip that
step in the snippets below.

### 1. Install

```powershell
cd phase-1
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e '.[dev]'
```

Use quotes around `.[dev]` so PowerShell does not treat `[` as a wildcard.

On macOS/Linux substitute the activate line:

```bash
cd phase-1
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Verify Phase 1

```powershell
python scripts/verify_phase1.py
# or, after editable install:
verify-phase1
```

Expected: a `PASS` for `sources.yaml`, `sections.yaml`, `aliases.yaml`, and the cross-checks,
followed by a corpus summary.

**Optional — Phase 1.6 network exit (robots + HTTP 200):** install Phase 2 (`pip install -e ../phase-2`) then:

```powershell
verify-phase1 --with-network
```

This shells to ``python -m mf_ingest.cli verify`` with ``PYTHONPATH`` set so it works without a second editable install in many setups.

You can also inspect individual configs:

```powershell
python -m ingest.sources
python -m ingest.aliases
```

### 3. Run tests

From **`phase-1/`** (uses `pyproject.toml` `pythonpath = ["."]`):

```powershell
pytest
```

From the **repository root** (parent of `phase-1/`):

```powershell
pytest
```

Root `pytest.ini` points at `phase-1/tests` and adds `phase-1` to `PYTHONPATH`.

## Phase 1 — what was implemented

- `config/sources.yaml` — the 10 locked Groww URLs with `id`, `scheme`,
  `category`, `publisher`, `refresh_frequency_days`.
- `config/aliases.yaml` — surface-form alias dictionary, including a
  `legacy_aliases` block for renamed funds (e.g., *HDFC Equity Fund* →
  *HDFC Flexi Cap Fund*).
- `config/sections.yaml` — section synonym map used by the Phase 3 chunker.
- `ingest/url_utils.py` — canonical URL helper (drives the dedup + allow-list
  invariants).
- `ingest/sources.py` — pydantic-backed loader with per-row + corpus-level
  invariants. CLI: `python -m ingest.sources`.
- `ingest/aliases.py` — alias loader, normalizer, longest-match resolver,
  cross-row collision check. CLI: `python -m ingest.aliases`.
- `scripts/verify_phase1.py` — single-command exit-criteria check.
- `tests/test_url_utils.py`, `tests/test_sources.py`, `tests/test_aliases.py`
  — coverage for every Phase 1.6 exit criterion plus the edge cases tagged
  1.04, 1.08, 1.10, 1.11, 1.12, and 2.14.

## Phase 1 exit criteria (from architecture.md §1.6)

- [x] AMC finalized — **HDFC Mutual Fund**
- [x] 10 schemes finalized across 5 SEBI categories
- [x] 10 Groww URLs captured (corpus is **closed** — no other URLs added)
- [x] `aliases.yaml` populated for all 10 schemes
- [x] Each of the 10 URLs HTTP-200 verified when `mf-ingest` completes successfully (`phase-2/mf_ingest/fetcher.py`)
- [x] `robots.txt` for `groww.in` read and enforced; rate limit ≤1 req/s (`phase-2/mf_ingest/robots.py`, `fetcher.py`)

## License

MIT.
