# Phase 4 — Embedding & hybrid index

Implements **Phase 4** of [`../docs/architecture.md`](../docs/architecture.md): BGE embeddings, Chroma vector store, BM25 lexical index, and hybrid scoring.

## Sub-phases

| § | Component | Module |
|---|-----------|--------|
| 4.1 | `BAAI/bge-small-en-v1.5` + `Embedder` interface | `mf_index/embedder.py` |
| 4.2 | Chroma (file-backed) + chunk metadata | `mf_index/vector_store.py` |
| 4.3 | BM25 + `α·vector + (1-α)·bm25` | `mf_index/bm25_index.py`, `mf_index/hybrid.py` |
| 4.4 | Build CLI, manifest, lock, verify | `mf_index/build_index.py`, `mf_index/cli.py` |

**Input:** `phase-3/data/chunks.jsonl`  
**Output:** `phase-4/data/index/` (Chroma, BM25, `index_manifest.json`)

## Install

```powershell
cd phase-4
pip install -e ".[dev]"
```

## Build index

```powershell
mf-build-index
# or from repo root (Phase 1 entry point):
cd phase-1
python -m ingest.build_index
```

Options:

| Flag | Meaning |
|------|---------|
| `--chunks PATH` | Override chunks JSONL |
| `--test-embedder` | No HuggingFace download (tests only) |
| `verify` | Metadata filter smoke test (§4.4) |
| `search QUERY` | Debug hybrid search |

## Verify §4.4

```powershell
mf-build-index verify
mf-build-index search "exit load" --scheme "HDFC Mid Cap Fund"
```

### Inspect embeddings (chunk_id ↔ vector)

Vectors live in Chroma; export a readable **Parquet** table:

```powershell
pip install pyarrow
mf-build-index export
# -> phase-4/data/index/embeddings.parquet
```

Each row has `chunk_id`, `embedding` (384 floats), `scheme`, `section`, `source_id`, etc.

```python
import pandas as pd
df = pd.read_parquet("data/index/embeddings.parquet")
print(df[["chunk_id", "scheme", "section", "embedding_dim"]].head())
print(len(df.loc[0, "embedding"]))  # 384
```

JSONL alternative: `mf-build-index export --jsonl -o data/index/embeddings.jsonl`

## Tests

```powershell
cd phase-4
pytest
```

From repo root: `pytest phase-4/phase4_tests` (see root `pytest.ini`).

