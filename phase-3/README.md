# Phase 3 — Cleaning & chunking (MF FAQ assistant)

## Phase 3.1 (implemented)

Text cleaning in **`mf_clean/cleaner.py`** (stdlib only):

- `clean_text()`, `collapse_whitespace()`, `join_split_numbers()` (edge 3.02)
- `compute_corpus_boilerplate_lines()`, `normalize_boilerplate_line()`

See [`../docs/architecture.md`](../docs/architecture.md) §3.1.

## Phase 3.2 (implemented)

Section-aware **one chunk per normalized section** (from `phase-2/data/processed/*.json`):

- `chunk_normalized_document()` / `chunk_corpus()`
- `performance` → `doc_type="performance"`; other sections → `doc_type="facts"`
- Holdings: top **10** rows by parsed weight (edge 3.10)
- §3.7: word-count proxy — merge fewer than **30** words into the **previous** facts chunk; cap at **600** words

`chunker` passes **`doc.category`** into `detect_fields` for §3.5 gating.

## Phase 3.3 (implemented)

Groww-specific stripping in **`mf_clean/groww_clean.py`** — `strip_groww_ui_noise()`:

- Nav substring removal (`Stocks / F&O / Mutual Funds`, etc.)
- Mega-menu **lines** (pipe/slash crumb rows of short menu tokens)
- Short **footer** lines (copyright, privacy, SEBI boilerplate)
- **`Understand terms`** glossary runs (after the heading, until a blank line)

Runs **before** §3.1 `clean_text` in `chunker._prepare_section_text`. Disable with `apply_groww_section_clean=False` or **`mf-chunk --no-groww-33`**.

## Phase 3.4 (implemented)

- **`mf_clean/chunk_models.py`** — Pydantic `Chunk` with `chunk_id`, `last_updated`, `url` validation.
- **`mf_clean/chunk_schema.py`** — `chunk_model_json_schema()`, `chunk_to_spec_dict()` (documentation-shaped dict with only the §3.4 keys), `dumps_chunk_spec_json()`.

Emit JSON Schema: **`mf-chunk --json-schema`**.

## Phase 3.5 (implemented)

**`mf_clean/field_detector.py`** — canonical 15 ids (`CANONICAL_FIELD_IDS`), `detect_fields(text, section=..., category=...)`, `validate_fields_detected()`. Edge **3.09**: `lock_in` only when `category` is ELSS. Edge **3.15**: `expense_ratio` needs a nearby `%` value; `nav` needs ₹/Rs digits or `%`, with a definition-prose guard.

## Phase 3.6 (implemented)

**`mf_clean/corpus_stats.py`** — `expected_chunk_bounds()` (default 60–80 for 10×6–8 sections), `summarize_chunk_corpus()`, optional `assert_chunk_count_in_bounds()` for tests/CI.

### CLI

```powershell
cd phase-3
pip install -e ".[dev]"
mf-chunk
mf-chunk --json-schema
mf-chunk --summary
# optional:
mf-chunk --processed-dir ..\phase-2\data\processed -o data\chunks.jsonl
mf-chunk --no-clean --no-groww-33
```

### Install & test

```powershell
cd phase-3
pip install -e ".[dev]"
pytest
```

From the **repository root**, tests also run via the root `pytest.ini` (`phase3_tests`).

### Import

```python
from mf_clean import clean_text, chunk_corpus, Chunk, strip_groww_ui_noise, chunk_to_spec_dict
from mf_clean import summarize_chunk_corpus, CANONICAL_FIELD_IDS
```

Phase 1’s `ingest/cleaner.py` and `ingest/chunker.py` remain **stub pointers** so Phase 1 stays independent of Phase 2/3 install layout.
