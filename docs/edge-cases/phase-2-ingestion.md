# Phase 2 — Edge Cases: Ingestion (Fetch + Parse)

> Companion to `../architecture.md` Phase 2. Single-publisher, HTML-only path (10 Groww URLs).

## Edge cases

| # | ID | Trigger | Expected behavior | Detection | Mitigation | Priority |
|---|---|---|---|---|---|---|
| 1 | 2.01 | Groww returns **HTTP 429** (rate limit) | Fetcher backs off exponentially (2s → 4s → 8s → 16s, max 5 retries); on continued 429, marks source as `failed_429` and continues with the rest | Response code logged | `tenacity` retry policy with jitter; rate-limit governor at ≤ 1 req/sec across the batch | P0 |
| 2 | 2.02 | Groww returns **HTTP 503/504** (transient) | Same as 2.01 — exponential backoff, but a different log code so we can distinguish provider issues from rate limits | Response code logged | Same retry policy; alert if 3+ URLs fail in one cron run | P0 |
| 3 | 2.03 | Groww returns **HTTP 200 with a "page not found" body** (soft 404) | Detected by content sniff (e.g., title contains "Page not found" or page lacks the scheme header card); fetcher treats as 404 | Section extractor returns `< N` expected sections; or sniff title | Content-shape validator runs after every fetch | P0 |
| 4 | 2.04 | **Cloudflare bot challenge** (HTML page asking JS challenge) | Fetcher detects the challenge HTML and falls back to a cached snapshot for that URL; CI alert raised | Sniff for `cf-chl-bypass` / `__cf_chl_jschl_tk__` strings | Use a polite User-Agent; if challenged, serve last-known-good snapshot and alert | P0 |
| 5 | 2.05 | Groww **redesigns the page** and the section extractor finds 0 sections | Build does NOT overwrite the previous snapshot or re-index; CI fails loudly | Section count delta vs previous run > 50% | "Structural-break" assertion in `parser_html.py`; alert + halt re-index | P0 |
| 6 | 2.06 | **JS-rendered content** — some Groww values are populated client-side (e.g., NAV refreshed via JS) | If the section extractor finds the section node but the value is empty, fall back to a headless render (Playwright) for that URL only | Empty-text detection in known sections | Optional Playwright pass behind a config flag; off by default to keep ingestion lightweight | P1 |
| 7 | 2.07 | **Connection reset** / partial fetch | Discard the partial response; retry; never write a partial file to `data/raw/` | Content-Length mismatch or `httpx.ReadError` | Atomic write: `*.tmp` then `os.replace` | P0 |
| 8 | 2.08 | Encoding mismatch — page declares `utf-8` but body has stray cp1252 bytes (e.g., `â‚¹` instead of `₹`) | Decode with `utf-8` first, fall back to `cp1252` if currency symbol is mangled; emit a `ENCODING_FALLBACK` log | Sniff: if `?` or replacement char appears in known numeric sections | Encoding fallback chain in `fetcher.py` | P1 |
| 9 | 2.09 | **`robots.txt` disallows** the path | Fetcher refuses the URL and the build fails (we do not silently bypass robots) | `robotparser.can_fetch` returns False | Hard fail; document the policy; do not retry with another UA | P0 |
| 10 | 2.10 | Fetcher restarts mid-batch | Idempotent: a URL with an unchanged ETag/Last-Modified is skipped on the next run | ETag/Last-Modified cache file | Persist ETag cache to `data/raw/.cache/` | P0 |
| 11 | 2.11 | Snapshot disk full | Fetcher catches `OSError`, logs `DISK_FULL`, exits non-zero, leaves previous snapshots intact | `errno == ENOSPC` | CI alert + runbook entry | P1 |
| 12 | 2.12 | Same **content_hash** as last run, but `fetched_at` is new | Do NOT re-chunk or re-embed; only `last_fetched_at` field is bumped in the manifest | Hash equality check | Per-chunk hash compare in `build_index.py` | P0 |
| 13 | 2.13 | `fetched_at` time-zone confusion (UTC vs IST) | All timestamps stored in **UTC ISO-8601** with `Z` suffix; UI converts to IST for display | Schema validator on `fetched_at` | `datetime.now(timezone.utc).isoformat()` everywhere | P1 |
| 14 | 2.14 | Two URLs accidentally point to the same canonical page (e.g., one with trailing slash, one without) | Normalize URLs (strip trailing `/`, lowercase host, drop fragments) before fetch; deduplicate | Dedup check after normalization | URL canonicalization in `sources.py` loader | P1 |
| 15 | 2.15 | A 4xx that is **not** a structural failure (e.g., 451 Unavailable for legal reasons) | Mark source as `legally_blocked`, omit from index for this run, do not crash | Status code 451 explicitly | Specific handler in retry policy | P2 |

## Runbook quick refs
- `data/raw/<source_id>/` keeps the **last 7 daily snapshots**, then prunes (Phase 10).
- A single failed URL in nightly cron does not block the others — but eval CI will fail until restored.
