# Phase 6 — Edge Cases: Retrieval

> Companion to `../architecture.md` Phase 6. Hybrid (vector + BM25) + cross-encoder re-rank, scoped to one scheme via metadata pre-filter.

## Edge cases

| # | ID | Trigger | Expected behavior | Detection | Mitigation | Priority |
|---|---|---|---|---|---|---|
| 1 | 6.01 | **Top-1 score barely above τ** (the NOT_FOUND threshold) | Tightly borderline: log it; still answer but mark response as `low_confidence`; UI may show a subtle "double-check on the linked page" hint | Re-rank score within `τ ± 0.05` | Two-band threshold: `hard_τ` (refuse), `soft_τ` (answer with hint) | P0 |
| 2 | 6.02 | **Two chunks tie** on score (e.g., shared boilerplate clause across schemes) | Deterministic tiebreak: prefer the chunk whose `scheme` matches the extracted scheme; then prefer newer `last_updated`; then prefer shorter text | Tie detection: top-1 == top-2 score | Stable sort with a fixed key tuple | P0 |
| 3 | 6.03 | Pre-filter on `scheme = X` returns **0 chunks** (e.g., extractor mis-fired or scheme genuinely not in corpus) | Soft-fallback to no-filter search; if still empty, NOT_FOUND template | Result count check | Two-stage retrieval with logged fallback | P0 |
| 4 | 6.04 | Retrieved chunk **contains the field but with a stale value** (e.g., NAV from yesterday) | Acceptable — answer is honest about staleness via the footer; staleness > 14 days appends warning (Phase 10.2) | `last_updated` age check at compose time | Age-warning footer rule | P0 |
| 5 | 6.05 | Field requested is in a **different section** than the field detector indexed (Groww re-arranges) | Re-rank still finds it because the chunk text matches the query semantically; field-detector boost is just a tie-breaker, never a hard filter | Manual eval | Boost is additive, not multiplicative; never gates retrieval | P0 |
| 6 | 6.06 | **Cross-encoder re-ranker unavailable** (model load fail, OOM) | Fall back to hybrid score (vector + BM25) without re-ranking; log `RERANKER_DOWN`; alert | Try/except around re-rank step | Graceful degradation, never crash the request | P0 |
| 7 | 6.07 | **Latency budget exceeded** (e.g., re-rank slow on cold cache) | Abort retrieval at the budget cutoff (e.g., 800 ms); return what we have or NOT_FOUND if nothing usable | Per-stage timer | `asyncio.wait_for(...)` per stage with deadlines | P1 |
| 8 | 6.08 | **Empty corpus** at cold start (first deploy before the first ingest succeeded) | API returns a clear "system warming up — try again in a minute" message; UI shows a non-fatal banner | Index size == 0 at startup | Health check fails until index is populated; load balancer doesn't route until healthy | P0 |
| 9 | 6.09 | The same scheme has **two contradictory chunks** (e.g., header says one expense ratio, fund_details says another due to extraction bug) | Re-ranker picks the more relevant; log a `FIELD_CONFLICT` event for the scheme | Cross-section field consistency check (offline test) | Periodic consistency assertion as part of CI eval | P1 |
| 10 | 6.10 | Field extractor returned a field, but the retrieved chunk's `fields_detected` doesn't include it (boost mismatch) | No issue — boost is optional. Continue with re-rank score as the deciding factor. | None | Boost is additive; missing tag just means no bonus | P2 |
| 11 | 6.11 | User query is **scheme-only**, no field ("HDFC Mid Cap Fund?") | Return the `header` chunk (snapshot card) for that scheme; ask the user a follow-up suggestion ("Did you want to know expense ratio, exit load, …?") | Field extractor returns null | Fallback to `header` chunk + suggestion list in answer | P1 |
| 12 | 6.12 | User query has **field-only**, no scheme ("What's an exit load?") | Treat as OUT_OF_SCOPE for an MF FAQ assistant (we don't define terms); refuse and link to AMFI knowledge center as a one-time concession | Scheme extractor returns null AND query is definitional | DEFINITION refusal template | P1 |
| 13 | 6.13 | BM25 top-k matches a **fragment of a longer-tailed term** (e.g., query "load" matches "Loads") | Vector search compensates because semantic match dominates; final re-rank decides | Manual eval | Hybrid α tuning (default 0.6 vector, 0.4 BM25) | P2 |
| 14 | 6.14 | Retrieval returns the **right chunk but in the wrong language** (defensive — Groww is English) | Section-language detector; reject non-English chunks at index time so this never happens at retrieval | Language detect at chunking | Phase 3 invariant | P2 |
| 15 | 6.15 | A chunk for a **closed/merged** scheme (1.03) is retrieved | Retriever respects the `status = closed` flag and routes to the `closed_scheme` refusal instead of composing | Status check in `[A] Metadata pre-filter` | Pre-filter excludes `status != "active"` chunks unless explicitly asked | P1 |

## Score tuning notes
- Thresholds (`hard_τ`, `soft_τ`) are calibrated against the eval set (Phase 9). Re-tune whenever the corpus or embedding model changes.
- `α` (vector vs BM25 weight) starts at 0.6 — keep tracked in `config/retrieval.yaml`.
