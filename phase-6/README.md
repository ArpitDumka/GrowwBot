# Phase 6 — Retrieval (Filtered Hybrid + Rerank)

Implements architecture §6.1: **filter → hybrid (Phase 4) → boost → rerank → one chunk**.

Requires Phases **4** (built index) and **5** (guard). Install Phase 4 index deps:

```powershell
cd phase-4
pip install -e .
cd ..\phase-5
pip install -e .
cd ..\phase-6
pip install -e ".[index,dev]"
```

## CLI

```powershell
mf-retrieve ask "What is the expense ratio of HDFC Mid Cap Fund?"
mf-retrieve verify --test-reranker
mf-retrieve ask "..." --json
```

`--test-embedder` / `--test-reranker` avoid large HF downloads in CI.

Config: `phase-6/config/retrieval.yaml`.
