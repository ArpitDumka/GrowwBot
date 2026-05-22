# Phase 10 — Edge Cases: Deployment, Observability & Maintenance

> Companion to `../architecture.md` Phase 10. Nightly cron re-fetches the 10 Groww URLs.

## Edge cases

| # | ID | Trigger | Expected behavior | Detection | Mitigation | Priority |
|---|---|---|---|---|---|---|
| 1 | 10.01 | **Nightly cron fails silently** (e.g., GitHub Actions runner outage) | Cron emits a heartbeat metric (`ingest_heartbeat_total`). If no heartbeat in 26 hours, alert fires. | Heartbeat absence | "Dead-man's switch" alert in monitoring | P0 |
| 2 | 10.02 | **Vector store volume not mounted** on container restart | Health check verifies index loadability on startup; container fails healthcheck and is not routed to | Index load probe | Liveness + readiness probes; rollback on first failure | P0 |
| 3 | 10.03 | **Groq API key rotation** — old key revoked before new one is in env | Use a single `GROQ_API_KEY` variable updated atomically via secret manager; rolling restart | Groq returns 401 | Secret rotation runbook | P0 |
| 4 | 10.04 | **Groq model retired** (e.g., `llama-3.3-70b-versatile` unavailable) | `pinned_model_id` in `config/llm.yaml` fails smoke test in CI before prod; migration ticket to update primary/fallback ids | Groq API error / model list | Pin model id + scheduled review | P0 |
| 5 | 10.05 | **DDoS / abuse** on `/chat` | IP-based rate limit (e.g., 30 req/min) at the edge; on burst, return 429 with `Retry-After` | Request rate metric | Cloud edge / Cloudflare WAF rule | P0 |
| 6 | 10.06 | **LLM provider outage** | Composer returns a fixed "service is briefly unavailable, please try again shortly" message; never invents an answer; exposes a metric `llm_unavailable_total` | Provider 5xx / timeout | Graceful degradation message; optional secondary provider failover | P0 |
| 7 | 10.07 | **Cost spike** from a runaway client | Per-IP daily quota; alert at 80% of monthly LLM budget | Cost dashboard | Quota + alert | P1 |
| 8 | 10.08 | **TLS certificate expiry** | Renewal automated via the host (e.g., Vercel / Render); calendar reminder 30 days out as a safety net | Cert expiry monitor | Auto-renewal + monitoring | P1 |
| 9 | 10.09 | **Storage growing unbounded** (snapshots in `data/raw/` accumulate) | Pruner retains the last 7 daily snapshots per source; older deleted in the cron tail | Disk usage metric | Pruner step in cron | P1 |
| 10 | 10.10 | **Logs leak the raw query** (regression introduces `log.info(query)`) | A log scrubber middleware redacts likely PII from any log line; CI test grep-fails on `log.*query` patterns | Static-analysis check | Log middleware + lint rule | P0 |
| 11 | 10.11 | **Monitoring alert noise** (false positives causing alert fatigue) | Alerts have `severity` tiers; only `critical` pages on-call. Warnings flow to a digest. | Alert routing rules | Tiered routing | P1 |
| 12 | 10.12 | **Groww 451 / legal block** for crawler in production region | Detected by fetcher (2.15); cron continues with cached snapshot; alert raised. Service still serves answers from the most recent good snapshot. | Status code | Cached-snapshot mode + alert | P1 |
| 13 | 10.13 | **Two ingest jobs run concurrently** (manual + scheduled) | File-lock (4.04) prevents collision; second run exits cleanly | Lock conflict log | Same lock as Phase 4 | P0 |
| 14 | 10.14 | **Index rebuild produces a worse top-1 score** distribution | After every build, a smoke-test runs the eval golden set; if accuracy drops > 5%, the new index is **not promoted**, previous version stays live | Smoke test compare | Blue-green index swap | P0 |
| 15 | 10.15 | **Schema migration** of `chunks.json` (e.g., add a new field) | Loader is **forward-compatible** (unknown fields ignored) and **backward-compatible** (missing optional fields default sensibly); add a `schema_version` field | Schema validator | Versioned schema + tests | P1 |
| 16 | 10.16 | **Disk corruption** on the Chroma volume | Loader detects and falls back to last known-good backup (4.05); cron restores from backup | Try-load on startup | Backups + healthcheck | P0 |
| 17 | 10.17 | **Time skew** between cron host and app host (NTP off) | All timestamps stored in UTC; UI converts to IST for display. Skew within a few seconds is harmless. | NTP monitoring | Use UTC everywhere; trust hosted-platform NTP | P2 |
| 18 | 10.18 | **PII regression** detected in production logs after deploy | Auto-trigger key rotation, log purge, and post-mortem; block further deploys until verified clean | PII pattern scan on log stream | Daily log-scrubber sweep | P0 |
| 19 | 10.19 | A user **reports an inaccurate answer** | Runbook: capture `trace_id`, fetch the `query_hash` (NOT the raw query), check retrieved chunks, decide whether it's a corpus issue (refresh source) or a composer issue (file regression) | Trace pipeline | Reproducible from `trace_id` | P0 |
| 20 | 10.20 | **Audit request**: "Where did this fact come from?" | `trace_id` returns: query_hash, retrieved chunk_ids, source URLs, content_hashes, fetched_at — full lineage | Trace storage | Persist trace metadata for 30 days | P1 |
| 21 | 10.21 | **Multi-region deployment** drift (vector store inconsistent across replicas) | Single source of truth: vector store is built once and copied to all regions; build_id stamped per replica; healthcheck verifies build_id matches | Build-id check | Single-build, multi-region copy | P2 |
| 22 | 10.22 | **GDPR-style "delete my data" request** | We don't store user-identifiable data (PII is rejected, only `query_hash` is logged), so there is nothing to delete; document this in the privacy posture | None | Privacy-by-design documentation | P1 |
| 23 | 10.23 | **CI eval is green but production is failing** (drift) | Daily prod-replay job runs the eval set against the live API; failures alert independently of the build pipeline | Prod-replay job | Independent monitor | P1 |
| 24 | 10.24 | A scheme **page is permanently down** (404 for > 24 hours) | After 24h of failed fetches, that scheme is marked `degraded` in the index; queries about it return a "this scheme's source page is temporarily unavailable" message with the URL | Failure window counter | Degraded-mode template | P0 |

## Runbook quick refs
- **Heartbeat metric**: `ingest_heartbeat_total{source_id="..."}` — incremented per successful fetch.
- **Trace ID**: returned in every `/chat` response header (`x-trace-id`); also in UI footer (small grey).
- **Backups**: last 3 successful index builds in `data/processed/backups/`.
- **Snapshots**: last 7 daily HTML snapshots in `data/raw/<source_id>/`.

## Privacy posture (recap)
- We do not collect PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers.
- We log `query_hash` (SHA-256), never the raw query.
- We do not set persistent cookies; sessions are per-tab and ephemeral (v1).
- All LLM calls are server-side; provider keys never reach the client.
