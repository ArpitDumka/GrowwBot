# Phase 4 — Edge Cases: Embedding & Index Build

> Companion to `../architecture.md` Phase 4. Chroma (file-backed) + BM25 hybrid over ~60–80 chunks.

## Edge cases

| # | ID | Trigger | Expected behavior | Detection | Mitigation | Priority |
|---|---|---|---|---|---|---|
| 1 | 4.01 | Single-chunk change (e.g., NAV updated) | Only the changed chunk is re-embedded; vector store is **incrementally updated**, not rebuilt from scratch | Per-chunk hash diff vs `index_manifest.json` | Incremental builder; full rebuild only when `--full` flag is passed | P0 |
| 2 | 4.02 | **Embedding model version drift** (vector dim changes between deploys) | Index manifest stores `embedding_model + dim`; on mismatch the builder refuses to merge and forces a full rebuild | Manifest assertion at startup | Manifest file with `model_id` and `dim` checked at every load | P0 |
| 3 | 4.03 | BM25 index out-of-sync with vector index after a partial failure | Both indices are written **atomically** via tmp-then-rename; if either fails, both are rolled back | Manifest mtime divergence | Two-phase write with shared transaction id; sanity-check IDs match | P0 |
| 4 | 4.04 | Two cron runs racing (manual + scheduled) | Builder takes a **file-lock** on `data/processed/.lock`; the second run aborts cleanly with a clear log | `flock` / `portalocker` | Lock acquisition with timeout; exit code 75 (`EX_TEMPFAIL`) | P0 |
| 5 | 4.05 | Vector store file is corrupted (e.g., killed mid-write) | Loader detects corruption (Chroma raises) → automatically falls back to last good backup in `data/processed/backups/` | Try-load on startup, except → fallback | Keep last 3 successful builds in a rotating backup folder | P0 |
| 6 | 4.06 | Disk full during embedding write | Builder catches `OSError(ENOSPC)`, leaves previous index intact, exits non-zero | `errno` check on write exception | CI alert + runbook entry; cleanup script for old snapshots | P1 |
| 7 | 4.07 | Embedding API timeout (if remote model is used) | Per-chunk retry up to 3×; if a chunk consistently fails, build aborts (we do not deploy a partial index) | Per-batch timeout in `embedder.py` | All-or-nothing build semantics | P0 |
| 8 | 4.08 | Embedding text contains unusual unicode (₹, smart quotes, emoji) that some models tokenize oddly | Pre-embedding normalizer: NFKC normalize, replace common smart-quote pairs, drop unprintable chars | Pre-embed assert | `unicodedata.normalize("NFKC", text)` | P1 |
| 9 | 4.09 | Empty chunk text accidentally reaches the embedder | Pre-check rejects; build fails with the offending `chunk_id` | Length assert | Schema validator at chunker boundary (see 3.07) | P0 |
| 10 | 4.10 | Cross-encoder re-ranker model not yet downloaded on first run | Builder downloads on first run with a clear progress log; subsequent runs use the local cache | HF cache miss | Pre-warm step in `build_index.py`; document model download size | P1 |
| 11 | 4.11 | Filter on a misspelled scheme returns 0 chunks (e.g., `scheme = "HDFC Mdcap"`) | Retriever (Phase 6) catches this and falls back to no-filter search; logs a `FILTER_MISS` event | Result count == 0 with a non-empty filter | Soft fallback at retrieval, never at index time | P1 |
| 12 | 4.12 | Index contains chunks from a stale `source_id` after a config change (e.g., URL slug fix) | On every build, an "orphaned chunk" sweep removes any chunk whose `source_id` is not in current `sources.yaml` | Set diff between manifest and config | Garbage-collection step at end of `build_index.py` | P1 |
| 13 | 4.13 | Two chunks have identical text (e.g., same generic stamp-duty clause across schemes — see 3.14) | Both stored with distinct `chunk_id`; cosine similarity may tie at retrieval — handled by Phase 6 deterministic tiebreak | Hash-on-text dedup test deliberately allows duplicates | No-op here; tie-break is a Phase 6 concern (6.02) | P2 |
| 14 | 4.14 | BM25 stopword list omits Indian-finance-specific noise tokens (e.g., "scheme", "fund", "direct", "growth" appear in every chunk) | Custom stopword list extends the default to include these to keep BM25 discriminative | Manual inspection of top-10 BM25 results for "expense ratio" | `config/bm25_stopwords.txt` extension | P1 |
| 15 | 4.15 | Index build is fast enough that someone runs it during a query → vector store reload race | Reader holds a snapshot reference; new index is loaded only when no reads are in flight | Reader/writer pattern | Two-pointer loader; swap atomically | P1 |
