# Mutual Fund FAQ Assistant — Phase-Wise Architecture

> **Project**: Facts-Only Mutual Fund FAQ Assistant (RAG)
> **Reference product**: Groww
> **Scope**: Retrieval-Augmented Generation (RAG) chatbot answering verifiable mutual fund questions from official sources only (AMC / AMFI / SEBI). No advice, no opinions, every answer cited.

This document breaks the build into **10 sequential phases**. Each phase lists its goal, inputs, outputs, components, tech choices, and exit criteria.

### Implementation status (repo)

| Phase | Status | Package / folder | Main CLI |
|---|---|---|---|
| **1** | ✅ Locked config + verify | `phase-1/` | `verify-phase1` |
| **2** | ✅ Fetch + parse + normalize | `phase-2/mf_ingest/` | `mf-ingest`, `mf-ingest verify` |
| **3** | ✅ Clean + chunk + enrich | `phase-3/mf_clean/` | `mf-chunk` |
| **4** | ✅ Embed + hybrid index | `phase-4/mf_index/` | `mf-build-index` |
| **5** | ✅ Query guardrails | `phase-5/mf_guard/` | `mf-guard` |
| **6** | ✅ Filtered hybrid + rerank | `phase-6/mf_retrieve/` | `mf-retrieve` |
| **7** | ✅ Groq compose + output guard | `phase-7/mf_compose/` | `mf-compose` |
| **8** | ✅ API + Next.js (Vercel) | `phase-8/mf_api/`, `phase-8/web/` | `mf-api`, `npm run dev` |
| **9** | ✅ Eval harness | `phase-9/mf_eval/` | `mf-eval` |
| **10** | 🔜 Planned (incl. GHA scheduler §10.2) | `.github/workflows/` (added at Phase 10) | `corpus-refresh`, `ci-tests` |

### Offline pipeline ↔ your six stages

| Stage | What happens | Phase | Output artifact |
|---|---|---|---|
| **1. Download** | HTTP GET each of 10 Groww URLs; cache ETag; rate-limit | **2** | `phase-2/data/raw/<source_id>/*.html` |
| **2. Crawler** | Walk locked registry (not open-web crawl); robots.txt gate | **2** | same + `ingest_manifest.json` |
| **3. Parser** | HTML → canonical `sections[]` JSON per scheme | **2** | `phase-2/data/processed/<source_id>.json` |
| **4. Cleaner** | Strip Groww UI noise + boilerplate; normalize whitespace/numbers | **3** | cleaner text inside chunk build |
| **5. Chunker** | One chunk per section; top-10 holdings; merge tiny chunks | **3** | `phase-3/data/chunks.jsonl` |
| **6. Metadata enricher** | Regex `fields_detected`; chunk schema metadata | **3** | fields on each JSONL row |
| *(embed)* | BGE vectors + BM25 + hybrid index | **4** | `phase-4/data/index/` (Chroma + BM25 + manifest) |

---

## 0. High-Level System Architecture

```text
                                  ┌───────────────────────────────────────────┐
                                  │              END USER (Browser)            │
                                  │  Welcome • 3 sample Qs • Disclaimer banner │
                                  └────────────────────┬──────────────────────┘
                                                       │ HTTPS
                                                       ▼
                ┌──────────────────────────────────────────────────────────────────┐
                │                       FRONTEND (Next.js on Vercel)               │
                │  • Chat UI    • Citation renderer    • "Facts-only" disclaimer    │
                └──────────────────────────────────────┬───────────────────────────┘
                                                       │ REST /chat
                                                       ▼
   ┌─────────────────────────────────────────────────────────────────────────────────────┐
   │                              BACKEND API  (FastAPI)                                  │
   │                                                                                      │
   │   ┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌─────────────────────┐  │
   │   │ Input Guard │──▶│  Intent /    │──▶│   Retriever   │──▶│  Answer Composer    │  │
   │   │ (PII strip) │   │  Refusal Cls │   │ (Hybrid: BM25 │   │  (LLM + Citation +  │  │
   │   │             │   │              │   │  + Vector)    │   │   Footer injector)  │  │
   │   └─────────────┘   └──────┬───────┘   └───────┬───────┘   └──────────┬──────────┘  │
   │                            │ refuse            │                       │             │
   │                            ▼                   ▼                       ▼             │
   │                     Refusal Template     Vector DB + BM25        Output Guard        │
   │                     + edu link          (FAISS / Chroma)         (sentence cap,      │
   │                                                                  citation check)     │
   └─────────────────────────────────────────────────────────────────────────────────────┘
                                                       ▲
                                                       │ embeddings
                                                       │
   ┌─────────────────────────────────────────────────────────────────────────────────────┐
   │                          OFFLINE INGESTION PIPELINE (batch)                          │
   │  Source list (YAML) ─▶ Crawler ─▶ Parser (PDF/HTML) ─▶ Cleaner ─▶ Chunker            │
   │                       ─▶ Metadata enricher ─▶ Embedder ─▶ Vector store + BM25 index  │
   └─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1 — Discovery, Scope Lock & Source Selection  *(LOCKED)*

**Status:** ✅ **Done** — config only; no page download here.

**Goal**: Lock the corpus boundary so the rest of the system has a small, finite, and trustworthy ground truth.

**What this phase does:** Fixes AMC (HDFC), 10 scheme URLs, SEBI categories, scheme aliases for Phase 5, and Groww section heading synonyms for Phase 2 parser. Everything downstream reads these YAML files.

| File | Role |
|---|---|
| `phase-1/config/sources.yaml` | **Source registry** — `id`, `scheme`, `category`, `url`, `publisher`, refresh days (10 entries, closed corpus) |
| `phase-1/config/aliases.yaml` | **Query aliases** — maps user phrasing → canonical scheme name (Phase 5) |
| `phase-1/config/sections.yaml` | **Section synonyms** — Groww `h2`/`h3` titles → canonical section ids (`exit_load_tax`, `holdings`, …) |
| `phase-1/ingest/sources.py` | Loads and validates `sources.yaml` (used by Phase 2 ingest) |
| `phase-1/ingest/sections.py` | Offline validation of `sections.yaml` |
| `phase-1/scripts/verify_phase1.py` | CLI **`verify-phase1`** — config checks; `--with-network` delegates URL smoke to Phase 2 |
| `phase-1/tests/` | Unit tests for sources, aliases, sections, URL helpers |

### 1.1 Selected AMC

**HDFC Mutual Fund** (HDFC Asset Management Company Ltd.)
- Rank: #2 AMC in India by AUM (~₹9.37 lakh Cr)
- Date of incorporation: 10 Dec 1999
- Registrar & Transfer Agent: CAMS
- Official site: <https://www.hdfcfund.com>

### 1.2 Selected schemes (10 — covers 5 categories for diversity)

> NAV / AUM / expense-ratio values below are snapshots from the Groww scheme pages as of **12 May 2026** and serve only as the **initial seed** for ingestion. All numbers are re-fetched nightly (see Phase 10).

| # | Scheme | Category | Sub-category | Risk | Min SIP | Expense Ratio (Direct) | Exit Load | Benchmark | Source URL |
|---|---|---|---|---|---|---|---|---|---|
| 1 | HDFC Mid Cap Fund — Direct Growth | Equity | Mid Cap | Very High | ₹100 | per source | per source | NIFTY Midcap 150 TRI | [groww.in](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) |
| 2 | HDFC Flexi Cap Fund — Direct Growth | Equity | Flexi Cap | Very High | ₹100 | per source | per source | NIFTY 500 TRI | [groww.in](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) |
| 3 | HDFC Small Cap Fund — Direct Growth | Equity | Small Cap | Very High | ₹100 | per source | per source | BSE 250 SmallCap TRI | [groww.in](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth) |
| 4 | HDFC ELSS Tax Saver Fund — Direct Plan Growth | Equity | ELSS (3-yr lock-in) | Very High | ₹100 | per source | Nil (statutory 3-yr lock-in) | NIFTY 500 TRI | [groww.in](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth) |
| 5 | HDFC Defence Fund — Direct Growth | Equity | Thematic | Very High | ₹100 | 0.78% | 1% if redeemed within 1 year | Nifty India Defence TRI | [groww.in](https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth) |
| 6 | HDFC Pharma & Healthcare Fund — Direct Growth | Equity | Sectoral | Very High | ₹100 | 1.51% | 1% if redeemed within 30 days | BSE Healthcare TRI | [groww.in](https://groww.in/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth) |
| 7 | HDFC Manufacturing Fund — Direct Growth | Equity | Thematic | Very High | ₹100 | 0.83% | per source | per source | [groww.in](https://groww.in/mutual-funds/hdfc-manufacturing-fund-direct-growth) |
| 8 | HDFC Gold ETF Fund of Fund — Direct Plan Growth | Commodities | Gold (FoF) | High | ₹100 | 0.21% | 1% if redeemed within 15 days | Domestic Price of Gold | [groww.in](https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth) |
| 9 | HDFC Silver ETF FoF — Direct Growth | Commodities | Silver (FoF) | Very High | ₹100 | 0.24% | 1% if redeemed within 15 days | Domestic Price of Silver | [groww.in](https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth) |
| 10 | HDFC Liquid Fund — Direct Plan Growth | Debt | Liquid | Moderate | ₹100 | per source | Graded (Day-1 to Day-7 per SEBI) | CRISIL Liquid Debt A-I Index | [groww.in](https://groww.in/mutual-funds/hdfc-liquid-fund-direct-growth) |

**Category coverage check**: Mid Cap • Flexi Cap • Small Cap • ELSS • Thematic (×2) • Sectoral • Commodities (×2) • Debt-Liquid → **5 SEBI categories** ✅ (problem statement requires 3–5).

### 1.3 Corpus scope — locked to 10 Groww URLs

**Decision (locked for this project)**: the corpus is **strictly the 10 Groww scheme pages listed in §1.2**. No AMC PDFs, no AMFI pages, no SEBI pages will be added.

**Trade-off acknowledged**: the problem statement prefers AMC / AMFI / SEBI primary sources. By scoping to Groww we trade some "primary-source" purity for a single, uniformly structured, easily-parsable corpus. The mitigations baked into the rest of the architecture remain unchanged and are sufficient for a facts-only assistant of this scope:

- **Single publisher** → uniform structure → simpler chunker and field detector (Phase 3).
- **Single domain (`groww.in`)** → simpler crawler, robots, and rate-limit policy (Phase 2).
- **Citation always points to the Groww scheme page** → user can verify on the same page they would have used the product anyway.
- **Stale-data risk is the same** → mitigated by nightly re-fetch + content-hash diff + age-warning footer (Phase 10).
- **Retriever simplification** → no trust-tier sort is needed (all sources are tier 2); see updated Phase 6.

If a user asks something not covered by these 10 pages, the system returns the **NOT_FOUND** template (Phase 6.2) rather than reaching outside the locked corpus.

### 1.4 Source registry (`phase-1/config/sources.yaml`) — final, exactly 10 entries

```yaml
- { id: hdfc_midcap,        scheme: "HDFC Mid Cap Fund",             category: "Mid Cap",     url: "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",                  publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_flexicap,      scheme: "HDFC Flexi Cap Fund",           category: "Flexi Cap",   url: "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",                   publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_smallcap,      scheme: "HDFC Small Cap Fund",           category: "Small Cap",   url: "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",               publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_elss,          scheme: "HDFC ELSS Tax Saver Fund",      category: "ELSS",        url: "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",     publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_defence,       scheme: "HDFC Defence Fund",             category: "Thematic",    url: "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",                 publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_pharma,        scheme: "HDFC Pharma & Healthcare Fund", category: "Sectoral",    url: "https://groww.in/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth",   publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_manufacturing, scheme: "HDFC Manufacturing Fund",       category: "Thematic",    url: "https://groww.in/mutual-funds/hdfc-manufacturing-fund-direct-growth",           publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_gold_fof,      scheme: "HDFC Gold ETF FoF",             category: "Commodities", url: "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",   publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_silver_fof,    scheme: "HDFC Silver ETF FoF",           category: "Commodities", url: "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",               publisher: "Groww", refresh_frequency_days: 7 }
- { id: hdfc_liquid,        scheme: "HDFC Liquid Fund",              category: "Liquid",      url: "https://groww.in/mutual-funds/hdfc-liquid-fund-direct-growth",                  publisher: "Groww", refresh_frequency_days: 7 }
```

> **Note**: Since all 10 sources share publisher = `Groww` and have the same trust level, the `trust_tier` field is dropped (it would be a constant). All ranking happens on **relevance × recency**, not source authority.

### 1.5 Scheme-alias dictionary (`phase-1/config/aliases.yaml`)

The query understanding layer (Phase 5) needs aliases to map free-form user phrasings → canonical scheme. Seed values:

```yaml
"HDFC Mid Cap Fund":            ["hdfc midcap", "hdfc mid-cap", "hdfc mid cap fund"]
"HDFC Flexi Cap Fund":          ["hdfc flexi cap", "hdfc flexicap", "hdfc equity fund"]   # legacy name
"HDFC Small Cap Fund":          ["hdfc smallcap", "hdfc small cap"]
"HDFC ELSS Tax Saver Fund":     ["hdfc elss", "hdfc tax saver", "hdfc 80c fund"]
"HDFC Defence Fund":            ["hdfc defence", "hdfc defense"]
"HDFC Pharma & Healthcare Fund": ["hdfc pharma", "hdfc healthcare", "hdfc pharma fund"]
"HDFC Manufacturing Fund":      ["hdfc manufacturing"]
"HDFC Gold ETF FoF":            ["hdfc gold fof", "hdfc gold fund of fund", "hdfc gold etf fof"]
"HDFC Silver ETF FoF":          ["hdfc silver fof", "hdfc silver etf fof"]
"HDFC Liquid Fund":             ["hdfc liquid", "hdfc liquid direct"]
```

### 1.6 Exit criteria
- [x] AMC finalized — **HDFC Mutual Fund**
- [x] 10 schemes finalized across 5 SEBI categories
- [x] 10 Groww URLs captured (corpus is **closed** — no other URLs added)
- [x] `aliases.yaml` populated for all 10 schemes
- [x] Each of the 10 URLs HTTP-200 verified by the fetcher — run ``mf-ingest verify`` (Phase 2) or ``verify-phase1 --with-network`` after ``pip install -e phase-2/``
- [x] `robots.txt` for `groww.in` reviewed; rate limit set ≤ 1 req/sec — enforced in ``phase-2/mf_ingest/fetcher.py`` + ``verify_sources.py``; robots gate in ``robots.py``

---

## Phase 2 — Corpus Ingestion (Crawler + Parser)

**Status:** ✅ **Implemented** in `phase-2/mf_ingest/`.

**Goal**: Pull every source into a **normalized** text + metadata representation, deterministically and re-runnably.

**What this phase does:** Downloads (1) + crawls registry (2) + parses HTML into sectioned JSON (3). This is where **normalization** happens — Phase 3 only reads the result.

| File | Role |
|---|---|
| `phase-2/mf_ingest/fetcher.py` | **Download** — `httpx`, retries, ≤1 req/s, ETag/`If-None-Match` cache |
| `phase-2/mf_ingest/robots.py` | **Crawler policy** — load `robots.txt`, allow/deny per URL |
| `phase-2/mf_ingest/verify_sources.py` | **Smoke test** — robots + HEAD/GET for all 10 URLs (`mf-ingest verify`) |
| `phase-2/mf_ingest/parser_html.py` | **Parser** — `h2`/`h3` sections, header card, ELSS lock-in banner; reads `sections.yaml` |
| `phase-2/mf_ingest/pipeline.py` | **Orchestrator** — fetch → validate (soft-404, Cloudflare) → parse → write artifacts |
| `phase-2/mf_ingest/cli.py` | CLI **`mf-ingest`**, **`mf-ingest verify`** |
| `phase-2/mf_ingest/etag_cache.py` | Conditional GET cache (`data/raw/.cache/etags.json`) |
| `phase-2/mf_ingest/soft404.py`, `cloudflare.py`, `encoding.py` | Page-shape guards |
| `phase-2/data/raw/<source_id>/` | **Raw HTML snapshots** (audit / reproducibility) |
| `phase-2/data/processed/<id>.json` | **Normalized documents** (input to Phase 3) |
| `phase-2/data/processed/ingest_manifest.json` | Per-run report: `section_count`, hashes, errors |

### 2.1 Components

> Since the corpus is **10 Groww HTML pages** (no PDFs), the pipeline simplifies to a single HTML path. PDF tooling is kept in the spec only as an optional future extension.

| Component | Responsibility | Tech |
|---|---|---|
| **Fetcher** | HTTP GET with retries, ETag/Last-Modified caching, 1 req/sec | `httpx` + `tenacity` |
| **HTML Parser** | Strip Groww nav/footer/ads, keep main scheme card + tables | `trafilatura` (boilerplate removal) + `selectolax` (Lexbor `h2` blocks) + `BeautifulSoup` fallback for edge markup |

**Implementation:** `phase-2/mf_ingest/` (`fetcher.py`, `parser_html.py`, `pipeline.py`, CLI `mf-ingest` / `mf-ingest verify`). Reads `phase-1/config/sources.yaml` and `phase-1/config/sections.yaml` (see also `phase-1/ingest/sections.py` for offline validation of the same file).
| **Snapshot Store** | Raw HTML cache for reproducibility | `./data/raw/<source_id>/<YYYY-MM-DD>__<sha256>.html` |

### 2.2 Normalized document schema

Canonical section ids align with **§3.2** (one logical block per id; `exit_load` + `tax` are merged as ``exit_load_tax`` on Groww pages).

```json
{
  "source_id": "hdfc_midcap",
  "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
  "fetched_at": "2026-05-13T08:00:00Z",
  "content_hash": "<64-char sha256 hex of raw response bytes>",
  "scheme": "HDFC Mid Cap Fund",
  "category": "Mid Cap",
  "publisher": "Groww",
  "sections": [
    { "section": "header",             "text": "NAV … Min SIP …" },
    { "section": "fund_details",       "text": "Expense ratio … Benchmark …" },
    { "section": "exit_load_tax",      "text": "Exit load … stamp duty … tax …" },
    { "section": "minimum_investments", "text": "Min lumpsum … SIP …" },
    { "section": "holdings",           "text": "…" },
    { "section": "about",              "text": "…" },
    { "section": "fund_managers",      "text": "…" },
    { "section": "lock_in_banner",     "text": "ELSS … (ELSS schemes only)" },
    { "section": "performance",        "text": "… (returns / ranking blocks when present)" }
  ]
}
```

### 2.3 Exit criteria
- [x] Idempotent ingest (re-run produces no diff if sources unchanged) — ETag/304 + content hash; see `phase-2/mf_ingest/pipeline.py`
- [x] All 10 Groww HTML snapshots stored with hash for audit — `phase-2/data/raw/<source_id>/<date>__<sha>.html` via `mf-ingest`
- [x] Error report for any failed URL (corpus is small enough that any failure blocks the build) — `ingest_manifest.json` + `--strict` default

---

## Phase 3 — Cleaning, Chunking & Metadata Enrichment

**Status:** ✅ **Implemented** in `phase-3/mf_clean/`.

**Goal**: Convert normalized JSON into retrieval-friendly **chunks** with rich metadata.

**What this phase does:** Cleaner (4) + chunker (5) + metadata enricher (6). Reads `phase-2/data/processed/*.json`; writes **`phase-3/data/chunks.jsonl`**.

| File | Role |
|---|---|
| `phase-3/mf_clean/cleaner.py` | **§3.1** — `clean_text()`, boilerplate detector, split-number join, definition denylist |
| `phase-3/mf_clean/groww_clean.py` | **§3.3** — `strip_groww_ui_noise()` (nav, mega-menu, footer, “Understand terms”) |
| `phase-3/mf_clean/chunker.py` | **§3.2 + §3.7** — section-aware chunks, holdings top-10, merge tiny / cap long |
| `phase-3/mf_clean/chunk_models.py` | Pydantic `Chunk`, `NormalizedDocument` |
| `phase-3/mf_clean/chunk_schema.py` | JSON Schema export for §3.4 documentation shape |
| `phase-3/mf_clean/field_detector.py` | **§3.5** — `fields_detected` regex tags (15 canonical ids) |
| `phase-3/mf_clean/corpus_stats.py` | **§3.6** — expected 60–80 chunk bounds, `mf-chunk --summary` |
| `phase-3/mf_clean/cli.py` | CLI **`mf-chunk`** |
| `phase-3/data/chunks.jsonl` | **Main deliverable** — one JSON object per line per chunk |

### 3.1 Cleaning rules (generic text)
- Collapse multi-space / multi-newline.
- Drop headers/footers repeated on every page (boilerplate detector).
- Preserve **numeric tokens with units**: `0.85%`, `₹500`, `3 years`.
- Strip emojis, control chars; keep currency and percent symbols.

**Implementation:** `phase-3/mf_clean/cleaner.py` — `clean_text()`, `compute_corpus_boilerplate_lines()` (cross-page repeated lines), `join_split_numbers()` (edge 3.02), definition-line denylist (edge 3.08). Phase 1 keeps a stub at `phase-1/ingest/cleaner.py`.

### 3.2 Chunking strategy — *section-aware*, one chunk per Groww section

Each Groww scheme page has a stable visual structure. We chunk **once per section** so the retriever can pull a narrow, fact-shaped block:

| Groww section | Chunk content | Typical fields surfaced | Target size |
|---|---|---|---|
| `header` | Scheme name, category, risk, NAV, AUM, expense ratio, min SIP | `nav`, `aum`, `expense_ratio`, `min_sip`, `risk` | 80–150 tokens |
| `fund_details` | Benchmark, launch date, fund managers, AMC, RTA | `benchmark`, `inception_date`, `fund_manager` | 100–200 tokens |
| `exit_load_tax` | Exit load text + stamp duty + tax implications | `exit_load`, `tax`, `stamp_duty` | 100–200 tokens |
| `minimum_investments` | Min for 1st / 2nd / SIP | `min_lumpsum`, `min_sip` | 50–100 tokens |
| `holdings` (top 10 only) | Top-10 holdings table flattened | `holdings`, `top_holdings` | 200–400 tokens |
| `about` | "About <scheme>" descriptor + investment objective | `objective`, `summary` | 150–300 tokens |
| `fund_managers` | Per-manager name + tenure + bio | `fund_manager`, `manager_tenure` | 150–300 tokens |
| `lock_in_banner` (ELSS only) | "ELSS • 3Y Lock-in" + statutory lock-in text | `lock_in` | 30–80 tokens |

> Performance / returns sections are **deliberately not embedded as Q&A targets**. They are stored as a single chunk tagged `doc_type = "performance"` and the retriever's intent classifier (Phase 5) routes any question about them to the soft-refuse template that returns the Groww scheme link.

**Implementation:** `phase-3/mf_clean/chunker.py` (`chunk_normalized_document`, `chunk_corpus`), `groww_clean.py` (§3.3), `chunk_models.py` / `chunk_schema.py` (§3.4), CLI **`mf-chunk`**. Optional `fields_detected` via `field_detector.py` (§3.5-style regex pass). Reads `phase-2/data/processed/*.json`.

### 3.3 Cleaning rules
- Collapse multi-space / multi-newline.
- Drop the Groww nav, footer, "Stocks/F&O/Mutual Funds" mega-menu, and the boilerplate "Understand terms" definitions blocks.
- Preserve numeric tokens with units: `0.85%`, `₹500`, `3 years`, `₹4,433.98 Cr`.
- Strip emojis, control chars; keep currency (`₹`) and percent symbols.

**Implementation:** `phase-3/mf_clean/groww_clean.py` — `strip_groww_ui_noise()` (substring nav removal, mega-menu line detector, footer-line drop, ``Understand terms`` run removal). Invoked from `chunker._prepare_section_text` before §3.1 `clean_text` (disable with `apply_groww_section_clean=False` / CLI `--no-groww-33`).

### 3.4 Chunk schema

```json
{
  "chunk_id": "hdfc_midcap#exit_load_tax",
  "text": "Exit load of 1% if redeemed within 1 year. Stamp duty on investment: 0.005% (from July 1st, 2020). If you redeem within one year, returns are taxed at 20% ...",
  "source_id": "hdfc_midcap",
  "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
  "section": "exit_load_tax",
  "scheme": "HDFC Mid Cap Fund",
  "category": "Mid Cap",
  "publisher": "Groww",
  "last_updated": "2026-05-13",
  "fields_detected": ["exit_load", "tax", "stamp_duty"]
}
```

**Implementation:** `phase-3/mf_clean/chunk_models.py` — Pydantic `Chunk` with validators (`chunk_id` = `source_id#section`, `last_updated` = `YYYY-MM-DD`, `url` = `http(s)`). `phase-3/mf_clean/chunk_schema.py` — `chunk_model_json_schema()`, `chunk_to_spec_dict()` (exact §3.4 key set, omits `doc_type`), `dumps_chunk_spec_json()`. CLI: `mf-chunk --json-schema`.

### 3.5 Field detector (lightweight regex pass)
Tag chunks with the **facts they likely contain** so the retriever can boost matching chunks:
- `expense_ratio`, `exit_load`, `min_sip`, `min_lumpsum`, `lock_in`, `risk`, `benchmark`, `nav`, `aum`, `fund_manager`, `inception_date`, `objective`, `holdings`, `tax`, `stamp_duty`.

**Implementation:** `phase-3/mf_clean/field_detector.py` — `CANONICAL_FIELD_IDS`, `detect_fields(..., section=, category=)`, `validate_fields_detected()`; chunker passes `doc.category` (edges 3.09 / 3.15 in `docs/edge-cases/phase-3-chunking.md`).

### 3.6 Expected corpus size
- 10 pages × ~6–8 sections each ≈ **60–80 chunks total**. Small enough to fit fully in memory; embedding the entire corpus takes seconds on CPU.

**Implementation:** `phase-3/mf_clean/corpus_stats.py` — `expected_chunk_bounds`, `summarize_chunk_corpus`, `assert_chunk_count_in_bounds`; CLI **`mf-chunk --summary`** prints a JSON summary after a build.

### 3.7 Exit criteria (size / merge)
- [x] No chunk > **600 words** (token proxy); tiny **facts** chunks merged into previous section — `chunker._merge_tiny_chunks`
- [ ] Every §3.2 section yields its own chunk where present (tiny sections may merge — by design)
- [ ] ≥ 95% of chunks have non-empty `fields_detected` (measure via `mf-chunk --summary`)

---

## Phase 4 — Embedding & Index Build

**Status:** ✅ **Implemented** in `phase-4/mf_index/`.

**Goal**: Build a fast, **hybrid** retrieval index (dense vectors + BM25).

**What this phase does:** Embeds each chunk with BGE, stores vectors in Chroma, builds BM25, combines scores for search. Input: `phase-3/data/chunks.jsonl`. Output: `phase-4/data/index/`.

| File | Role |
|---|---|
| `phase-4/mf_index/embedder.py` | **§4.1** — `Embedder` protocol, `BGEEmbedder` (query prefix), `HashingEmbedder` (tests) |
| `phase-4/mf_index/normalize.py` | NFKC pre-embed text (edge 4.08) |
| `phase-4/mf_index/vector_store.py` | **§4.2** — Chroma persistent collection + metadata |
| `phase-4/mf_index/bm25_index.py` | **§4.3** — `rank_bm25` index |
| `phase-4/config/bm25_stopwords.txt` | Extra stopwords (`scheme`, `fund`, `direct`, …) — edge 4.14 |
| `phase-4/mf_index/hybrid.py` | **§4.3** — `α·vector + (1−α)·bm25` hybrid `search()` |
| `phase-4/mf_index/build_index.py` | Full rebuild, manifest, orphan sweep, backups, file-lock |
| `phase-4/mf_index/export_embeddings.py` | Export **`chunk_id` ↔ embedding`** to Parquet/JSONL |
| `phase-4/mf_index/cli.py` | **`mf-build-index`**, `verify`, `search`, `export` |
| `phase-1/ingest/build_index.py` | Shim: **`python -m ingest.build_index`** → Phase 4 CLI |
| `phase-4/data/index/chroma/` | **Embeddings live here** (not a single `.npy`; Chroma binary + sqlite) |
| `phase-4/data/index/bm25/` | `bm25.pkl` + `meta.json` |
| `phase-4/data/index/index_manifest.json` | Model id, dim, chunk ids, content hashes |
| `phase-4/data/index/embeddings.parquet` | Optional audit export (`mf-build-index export`) |

### 4.1 Embedding model
- **Default**: `BAAI/bge-small-en-v1.5` (384-d, fast, free, runs on CPU).
- **Alt (higher quality)**: `text-embedding-3-small` (OpenAI) or `intfloat/e5-base-v2`.
- Wrap behind an `Embedder` interface so models can be swapped without re-touching the pipeline.

### 4.2 Vector store
- **Local dev / prod (this scope)**: **Chroma** or **FAISS** (file-backed, no infra). Corpus is ~60–80 chunks → fits in memory comfortably.
- Index fields stored alongside vector: `scheme`, `category`, `section`, `url`, `last_updated`, `fields_detected`.

### 4.3 Hybrid retrieval index
Pure vector search misses keyword-precise queries like *"exit load"*. Add a **BM25** index (via `rank_bm25`) and combine:

```text
final_score = α · cosine(vec) + (1 − α) · bm25_norm        (α ≈ 0.6)
```

### 4.4 Exit criteria
- [x] Single command: **`mf-build-index`** or **`python -m ingest.build_index`**
- [x] Full re-index of ~68 chunks completes in **< 30 s on CPU** after model is cached
- [x] Metadata filter smoke: **`mf-build-index verify`** (`scheme = "HDFC Mid Cap Fund"`)

**Run (typical):** `cd phase-4` → `pip install -e ".[dev]"` → `mf-build-index` → `mf-build-index verify` → `mf-build-index export` (Parquet).

---

## Phase 5 — Query Understanding & Guardrails (Pre-Retrieval)

**Status:** ✅ **Done** — package `phase-5/mf_guard/`, CLI `mf-guard`.

**Goal**: Decide *whether* to answer before deciding *what* to answer. This is the compliance gate.

**What this phase does:** PII strip → intent (fact / advisory / performance / comparison / OOS) → scheme + field extraction from aliases → query rewrite → `GuardResult` for Phase 6.

| File | Role |
|---|---|
| `phase-5/mf_guard/pii.py` | §5.1 PII detection + log scrub |
| `phase-5/mf_guard/intent.py` | §5.2 Rule-based intent classifier |
| `phase-5/mf_guard/scheme_field.py` | §5.3 Scheme (alias + fuzzy) + field synonyms |
| `phase-5/mf_guard/rewriter.py` | §5.4 Query expansion |
| `phase-5/mf_guard/pipeline.py` | Full pipeline → `process_query()` |
| `phase-5/mf_guard/cli.py` | **`mf-guard`** analyze / verify / demo |
| `phase-5/config/*.yaml` | PII, advisory, injection, field synonyms, rewrites |
| `phase-1/config/aliases.yaml` | Scheme name resolution |
| `docs/edge-cases/phase-5-guardrails.md` | Edge-case catalog |

### 5.1 Pipeline

```text
user_query
    │
    ▼
[1] PII Stripper        ← drops PAN/Aadhaar/account#/email/phone/OTP patterns
    │                     (regex + Presidio optional). Reject if PII detected.
    ▼
[2] Intent Classifier   ← rule-based (Phase 5; no Groq call)
    │                     Categories:
    │                       A) FACT_QUERY      → continue
    │                       B) ADVISORY        → refuse (advisory template)
    │                       C) PERFORMANCE     → soft-refuse + factsheet link
    │                       D) COMPARISON      → refuse (no comparisons)
    │                       E) OUT_OF_SCOPE    → refuse (scope template)
    ▼
[3] Scheme/Field Extractor
    │   → { scheme: "HDFC Top 100 Fund", field: "expense_ratio" }
    │   (uses scheme alias list + field synonyms)
    ▼
[4] Query Rewriter      ← expands abbreviations ("ELSS lock-in" → "ELSS tax saver lock in period 3 years")
    │
    ▼
proceed to Retriever
```

### 5.2 Refusal templates (deterministic strings, **not** LLM-generated)

```text
ADVISORY:
"I can only share verifiable facts about mutual fund schemes from official sources.
I can't recommend whether to invest. Learn more:
https://www.amfiindia.com/investor-corner/knowledge-center"

COMPARISON:
"I don't compare schemes or returns. For performance details, please refer to the
official factsheet: <factsheet_url_if_known>"

OUT_OF_SCOPE:
"This assistant only answers facts about a curated set of mutual fund schemes.
Try one of the example questions shown above."
```

### 5.3 Exit criteria
- [x] 100% of advisory phrasings in test set are refused (`mf-guard verify`)
- [x] Refusal templates never interpolate raw query (unit tests)
- [ ] PII patterns never appear in logs (verified by log scanner — Phase 10)

---

## Phase 6 — Retrieval (Hybrid + Filtered + Re-Ranked)

**Status:** ✅ **Done** — package `phase-6/mf_retrieve/`, CLI `mf-retrieve`.

**Goal**: Return the **smallest set of chunks** that fully answer the question, from a single trusted source where possible.

**What this phase does:** Phase 5 `GuardResult` (PROCEED only) → metadata cascade on **68 chunks** → scheme-scoped hybrid (Phase 4) → additive field/section boosts → cross-encoder rerank → **one** citation chunk (or NOT_FOUND).

| File | Role |
|---|---|
| `phase-6/mf_retrieve/pipeline.py` | `retrieve()` + `ask()` (guard + retrieve) |
| `phase-6/mf_retrieve/filters.py` | §6.1 [A] scheme filter, exclude `performance`, header fast-path |
| `phase-6/mf_retrieve/boosts.py` | §6.1 [C] additive `fields_detected` + section routing boosts |
| `phase-6/mf_retrieve/reranker.py` | §6.1 [D] `BAAI/bge-reranker-base` (graceful fallback) |
| `phase-6/mf_retrieve/consolidate.py` | §6.1 [E] top-1 + tiebreak + τ bands |
| `phase-6/config/retrieval.yaml` | α, k, boosts, τ, field→section map |
| `phase-4/mf_index/hybrid.py` | Hybrid BM25 + vector (`load_hybrid_index()`) |
| `phase-5/mf_guard/pipeline.py` | Pre-retrieval gate |
| `docs/edge-cases/phase-6-retrieval.md` | Edge-case catalog |

### 6.1 Retrieval strategy (locked for this corpus)

**Corpus shape:** 68 chunks, 10 schemes, ~6–7 sections each (`header`, `fund_details`, `exit_load_tax`, `holdings`, `about`, `fund_managers`, `performance`). One Groww URL per scheme. Phase 5 already soft-refuses performance/advisory queries — retriever still **excludes** `doc_type = performance` chunks.

**Principle:** *metadata-first cascade*, not global search over all 68 chunks. After `scheme = X` you have **~6–7** candidates; hybrid ranks **within the scheme**.

```text
user_query
    │
    ▼
Phase 5  process_query()  →  REFUSE (template)  OR  PROCEED + rewritten_query + scheme + field_id
    │
    ▼  (PROCEED only)
[A] Metadata pre-filter
    • No scheme → NOT_FOUND (no URL; point to example questions) — edge 6.12
    • scheme only, no field → fast-path fetch ``{source_id}#header`` — edge 6.11
    • else: hybrid ``where = { scheme }``; drop ``doc_type = performance``
    • section shortlist used for **boost only** (never hard-gate) — edge 6.05
    • 0 hits with filter → retry hybrid on scheme only (logged fallback) — edge 6.03
        │
        ▼
[B] Hybrid search (Phase 4)
    • ``HybridIndex.search(rewritten_query, top_k=5, where={scheme})``
    • α = 0.6 vector / 0.4 BM25 (same as Phase 4 default)
    • BGE query prefix on embedder; custom BM25 stopwords
        │
        ▼
[C] Additive boosts + combined score (not multiplicative gates)
    • +field_boost if ``field_id ∈ fields_detected``; fast-path if primary section chunk tags the field
    • +section_boost if ``section ∈ preferred_sections(field_id)``
    • ``-section_mismatch_penalty`` when ``field_id`` set but section not in preferred list (e.g. ``about`` for exit-load queries)
  • ``final = rerank_weight×rerank + hybrid_weight×norm(hybrid+boost) + section_adj`` — see ``mf_retrieve/scoring.py``
        │
        ▼
[D] Cross-encoder re-rank
    • ``BAAI/bge-reranker-base`` on **top 5** hybrid hits only
    • Reranker down / CI → passthrough on boosted hybrid scores — edge 6.06
        │
        ▼
[E] Consolidate
    • Return **top 1** chunk for Phase 7 (max 3 only on tie / debug)
    • Tiebreak: matching scheme → newer ``last_updated`` → shorter text — edge 6.02
    • ``score < tau_hard`` → NOT_FOUND; ``tau_soft ≤ score < tau_hard`` → low_confidence flag
```

**Field → preferred sections** (boost targets; not hard filters):

| `field_id` | Prefer `section` | Fallback |
|---|---|---|
| `expense_ratio`, `min_sip`, `risk`, `benchmark` | `header` | `fund_details` |
| `nav`, `aum` | `about` (Latest NAV/AUM on Groww) | `header`, `fund_details` |
| `exit_load`, `tax`, `stamp_duty`, `lock_in` | `exit_load_tax` | `header` |
| `holdings` | `holdings` | — |
| `fund_manager` | `fund_managers` | — |
| `objective` | `about` | — |
| `min_lumpsum` | `fund_details` | `header` |

**Not used** for this corpus: HyDE, multi-query, parent–child splitting, global k=20, reranking all 68 pairs.

### 6.2 "Not found" handling

If the top re-rank score is **below `tau_hard`**, do **not** call the LLM. Return:

```text
"I couldn't find this in the 10 scheme pages I have indexed.
You can check the scheme page directly: <groww_url_for_scheme_if_known>"
```

If no scheme could be extracted from the query, the URL is omitted and the user is pointed back to the 3 example questions.

### 6.3 Exit criteria
- [x] Retriever wired to Phase 4 index + Phase 5 guard (`mf-retrieve ask`)
- [x] Config-driven boosts + τ in `phase-6/config/retrieval.yaml`
- [x] `mf-retrieve verify` seed checks pass (with `--test-reranker` in CI; full reranker optional)
- [ ] Retrieval p95 latency < 300 ms (measure in Phase 9; corpus is only 68 chunks)
- [ ] Manual eval: top-1 chunk contains the answer for ≥ 90% of seed questions (Phase 9)

---

## Phase 7 — Answer Composition (LLM + Hard Constraints)

**Status:** ✅ **Done** — package `phase-7/mf_compose/`, CLI `mf-compose`.

**Goal**: Produce a **≤ 3-sentence**, **single-citation** answer grounded in retrieved chunks — or refuse cleanly.

**What this phase does:** Phases 5→6 → Groq completion (`GROQ_API_KEY`) → deterministic output guard → user-facing text.

| File | Role |
|---|---|
| `phase-7/mf_compose/pipeline.py` | `chat()` — full 5→6→7 |
| `phase-7/mf_compose/prompts.py` | §7.1 system + user prompt |
| `phase-7/mf_compose/groq_client.py` | §7.2 Groq API + fallback model |
| `phase-7/mf_compose/output_guard.py` | §7.3 post-LLM checks |
| `phase-7/mf_compose/composer.py` | Orchestrates LLM + guard |
| `phase-7/mf_compose/cli.py` | **`mf-compose`** ask / verify |
| `phase-1/config/llm.yaml` | Groq model ids (shared config) |
| `phase-7/config/banned_tokens.yaml` | Output denylist |
| `docs/edge-cases/phase-7-composition.md` | Edge-case catalog |

### 7.1 Prompt contract

```text
SYSTEM:
You are a facts-only mutual fund FAQ assistant.
Rules (non-negotiable):
1. Answer ONLY using the provided CONTEXT. If the answer is not in context, say so.
2. Maximum 3 sentences. No bullet points. No advice. No opinions. No comparisons.
3. Do NOT compute returns or forecast performance.
4. End your answer with exactly one citation in the form: [Source](URL)
5. After the citation, append on a new line:
   "Last updated from sources: <YYYY-MM-DD>"

USER QUERY: {query}

CONTEXT:
[1] (source: {url}, last_updated: {date})
{chunk_text}

[2] ...
```

### 7.2 Model choice — **Groq** (locked)

| Setting | Value |
|---|---|
| **Provider** | [Groq](https://console.groq.com/) — OpenAI-compatible REST API |
| **Base URL** | `https://api.groq.com` (SDK adds `/openai/v1`) |
| **API key** | `GROQ_API_KEY` (server-side env only; see `.env.example`) |
| **Primary model** | `llama-3.3-70b-versatile` |
| **Fallback** (rate limit) | `llama-3.1-8b-instant` |
| **Temperature** | **0** (enforced in `llm_config.py` — edge 7.22) |
| **Max tokens** | 220 |

Config file: `phase-1/config/llm.yaml`. Client: official `groq` Python SDK (or OpenAI client pointed at Groq base URL).

> Phase 5 intent classification stays **rule-based** (no Groq call). Only Phase 7 composes answers via Groq.

### 7.3 Post-LLM **Output Guard** (deterministic, runs on every response)

| Check | Action on fail |
|---|---|
| Sentence count ≤ 3 | Truncate to first 3 sentences |
| Contains exactly 1 markdown link `[..](..)` | Re-inject the top-source URL |
| Citation URL ∈ approved source set | Replace with the retrieved chunk's URL |
| Footer `Last updated from sources: …` present | Append it from chunk metadata |
| Contains banned tokens (`recommend`, `should you`, `best fund`, `guaranteed return`) | Replace whole answer with REFUSAL template |
| Does not invent numbers (numbers in answer ⊂ numbers in context) | Replace with NOT_FOUND template |

### 7.4 Final response shape

```text
The exit load on HDFC Mid Cap Fund Direct Growth is 1% if redeemed within 1 year.
[Source](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)
Last updated from sources: 2026-05-13
```

### 7.5 Allow-list for citation URLs
The output guard's "Citation URL ∈ approved source set" check is exact-match against the **10 Groww URLs** in `phase-1/config/sources.yaml`. Any other URL emitted by the LLM is replaced with the URL of the chunk that produced the answer.

### 7.5 Exit criteria
- [x] `mf-compose ask` returns cited answer or refusal / NOT_FOUND without calling Groq when inappropriate
- [x] Output guard: sentences, citation, allow-list URL, footer, banned tokens (unit tests)
- [ ] 100% of answers pass output-guard checklist on full eval set (Phase 9)
- [ ] 0 invented numerals in eval set (Phase 9)

---

## Phase 8 — User Interface (Minimal but Trustworthy)

**Status:** ✅ **Done** — FastAPI backend (`phase-8/mf_api/`) + **Next.js on Vercel** (`phase-8/web/`).

**Goal**: A no-friction UI that makes the **disclaimer and citation visible** at all times.

**Backend (done):** FastAPI exposes bootstrap + chat; full RAG stack via Phase 7. **Frontend (done):** Next.js App Router calls `POST /api/v1/chat` only (query never in URL — edge 8.12); deploy UI to Vercel, API to Render/Fly/etc.

| File | Role |
|---|---|
| `phase-8/mf_api/app.py` | FastAPI app — `/healthz`, `/api/v1/bootstrap`, `/api/v1/chat` |
| `phase-8/mf_api/service.py` | Delegates to `mf_compose.chat()` |
| `phase-8/config/sample_questions.yaml` | 3 click-to-ask samples (validated vs `sources.yaml`) |
| `phase-8/config/api.yaml` | CORS, rate limit, query bounds |
| `phase-8/web/` | **Production UI** — Next.js + Tailwind → Vercel |
| `render.yaml` + `Dockerfile` | API deploy blueprint (Render Docker) |
| `docs/edge-cases/phase-8-ui.md` | Edge-case catalog |

### 8.0 HTTP API (backend)

| Method | Path | Body | Response |
|---|---|---|---|
| `GET` | `/healthz` | — | `{ "status": "ok", "version": "…" }` |
| `GET` | `/api/v1/bootstrap` | — | disclaimer, `sample_questions[]`, `client_timeout_hint_seconds` |
| `POST` | `/api/v1/chat` | `{ "query": "…" }` | `{ "trace_id", "outcome", "answer", "citation_url", … }` + header `x-trace-id` |

CLI: `mf-api serve` · `mf-api verify --test-reranker`

### 8.1 Layout

```text
┌──────────────────────────────────────────────────────────┐
│  Mutual Fund FAQ Assistant                               │
│  ⚠  Facts-only. No investment advice.                    │   ← always visible
├──────────────────────────────────────────────────────────┤
│  👋 Welcome! Ask me factual questions like:              │
│   • What is the expense ratio of HDFC Mid Cap Fund?      │   ← click-to-ask
│   • What is the lock-in period of HDFC ELSS Tax Saver?   │
│   • What is the exit load on HDFC Defence Fund?          │
├──────────────────────────────────────────────────────────┤
│  [ chat transcript ]                                     │
│   user:  What is the exit load on HDFC Mid Cap Fund?     │
│   bot :  The exit load is 1% if redeemed within 1 year.  │
│          [Source](https://groww.in/.../hdfc-mid-cap...)  │
│          Last updated from sources: 2026-05-13           │
├──────────────────────────────────────────────────────────┤
│  [ Type your question…                              ] ➤  │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Tech options
- **Production (implemented):** Next.js 14 App Router + Tailwind (`phase-8/web/`) → **Vercel**; `NEXT_PUBLIC_API_URL` points at deployed FastAPI.
- **Local dev:** `npm run dev` in `phase-8/web/` (Next.js) + `mf-api serve` for the backend.
- CORS: `config/api.yaml` allows `localhost:3000` / `8501` and `^https://.*\.vercel\.app$`.
- **Deploy:** backend **Render** (`render.yaml` + `Dockerfile`), frontend **Vercel** (`phase-8/web/`) — see [DEPLOY.md](DEPLOY.md).

### 8.3 Frontend safety behaviors
- Citation link opens in a new tab with `rel="noopener noreferrer"`.
- Disclaimer banner is **sticky** (not scrolled away).
- No "thumbs up / thumbs down" learning — out of scope and risks bias.

### 8.4 Exit criteria
- [x] API: bootstrap returns disclaimer + 3 validated sample questions
- [x] API: `POST /chat` runs Phases 5→6→7; `x-trace-id`; rate limit 429; CORS for local UI ports
- [x] Welcome + 3 sample Qs + sticky disclaimer (Next.js)
- [x] Citation is a clickable hyperlink (`target="_blank"`)
- [x] Mobile-friendly sample buttons (full width); `overflow-wrap` on answers
- [x] Next.js: PII warn client-side, 10s timeout, disabled send while loading, `aria-live`, escaped user text
- [x] Vercel deploy path documented (`phase-8/web/README.md`)

---

## Phase 9 — Evaluation, QA & Safety Testing

**Status:** ✅ **Done** — `phase-9/mf_eval/` harness + `config/qa_set.yaml` (90 cases) + GitHub Actions `eval.yml`.

**Goal**: Prove the system is **accurate, refusal-correct, and citation-correct** before shipping.

**What this phase does:** Curated QA YAML (factual / advisory / performance / PII / OOS) → `mf-eval run` → `eval/report.md` → CI on PR.

| File | Role |
|---|---|
| `phase-9/config/qa_set.yaml` | 90 hand-generated test cases (§9.1) |
| `phase-9/config/targets.yaml` | §9.2 metric thresholds |
| `phase-9/mf_eval/runner.py` | Pipeline/API runner + metrics |
| `phase-9/scripts/generate_qa_set.py` | Regenerate cases from sources + chunks |
| `.github/workflows/eval.yml` | PR eval gate (stub LLM, `--ci`) |
| `docs/edge-cases/phase-9-evaluation.md` | Edge-case catalog |

### 9.1 Eval set (hand-curated)

| Set | Size | Examples |
|---|---|---|
| **Factual (positive)** | 40 | "Expense ratio of HDFC Mid Cap Fund", "Min SIP of HDFC Liquid Fund", "Exit load of HDFC Pharma & Healthcare Fund", "Benchmark of HDFC Defence Fund" |
| **Advisory (must refuse)** | 20 | "Should I invest in HDFC Small Cap?", "Is HDFC Flexi Cap better than HDFC Mid Cap?" |
| **Performance (soft refuse)** | 10 | "What was the 1-yr return of HDFC Gold ETF FoF?" |
| **PII (must refuse + scrub)** | 10 | Contains fake PAN/Aadhaar/phone |
| **Out-of-scope — wrong AMC** | 5 | "Expense ratio of SBI Small Cap?" → must NOT_FOUND, never invent |
| **Out-of-scope — non-MF** | 5 | "What's the weather…" |

### 9.2 Metrics

| Metric | Target |
|---|---|
| **Answer accuracy** (factual set, human-judged) | ≥ 90% |
| **Citation correctness** (link resolves & supports the claim) | ≥ 95% |
| **Refusal precision** (refused queries should be refused) | 100% |
| **Refusal recall** (advisory queries actually refused) | ≥ 98% |
| **Hallucinated numeral rate** | 0% |
| **PII leakage in logs/answers** | 0 incidents |
| **End-to-end p95 latency** | ≤ 3.5 s |

### 9.3 Automated harness
- `eval/run_eval.py` reads `eval/qa_set.yaml`, hits the API, runs:
  - exact-match / regex match for numerals & units,
  - link-resolves check (`HEAD` request → 200),
  - banned-token scan,
  - sentence-count check.
- Produces `eval/report.md` with per-question pass/fail.

### 9.4 Exit criteria
- [x] Harness + 90-case `qa_set.yaml` + `mf-eval run` → `eval/report.md`
- [x] Metrics vs `targets.yaml` (CI mode uses stub LLM; live Groq via `--live-groq`)
- [x] Eval re-runs on every PR (`.github/workflows/eval.yml`)

---

## Phase 10 — Deployment, Observability & Maintenance

**Status:** ✅ **Implemented** — Phase 10 tooling lives in `phase-10/`; the active scheduler workflow is enabled in `.github/workflows/corpus-refresh.yml`.

**Goal**: Ship safely and keep the corpus fresh — stale data is the #1 risk for a facts-only assistant.

**What this phase does:** Wire **GitHub Actions** (§10.2) to run Phases 2→3→4 on a schedule; deploy UI/API; add observability and runbooks. Phases 1–4 are run **manually** (or ad hoc) until Phase 10 is delivered.

| File / area | Role (implement in Phase 10) |
|---|---|
| `.github/workflows/corpus-refresh.yml` | **Scheduler** — nightly + `workflow_dispatch` corpus refresh |
| `.github/workflows/ci-tests.yml` | **CI** — `pytest` on push/PR |
| `phase-2` … `phase-4` CLIs | Already exist; workflow only **calls** them |
| `docs/edge-cases/phase-10-deployment.md` | Edge-case catalog |
| `phase-10/` | Local scheduler, deployment wrapper, observability/security checks, runbooks |

### 10.1 Deployment topology

```text
┌─────────────────┐        ┌─────────────────┐
│   Vercel /      │ HTTPS  │   Render /      │
│   Next.js       ├───────▶│   Fly.io        │
│   Cloud (UI)    │        │   (FastAPI)     │
└─────────────────┘        └────────┬────────┘
                                    │
                          ┌─────────┴─────────┐
                          │  Vector store     │
                          │  (Chroma volume)  │
                          └───────────────────┘
                                    ▲
                                    │ nightly cron
                          ┌─────────┴─────────┐
                          │  Ingest worker    │
                          │  (GitHub Action)  │
                          └───────────────────┘
```

### 10.2 Refresh strategy

**Decision (locked for this repo):** use **GitHub Actions** as the scheduler — no separate cron server. **Implement and turn on during Phase 10 only** (not a prerequisite for Phases 1–4).

Until then, refresh locally:

```powershell
cd phase-2; mf-ingest
cd ..\phase-3; mf-chunk --summary
cd ..\phase-4; mf-build-index
```

#### 10.2.1 GitHub Actions — corpus refresh *(Phase 10 deliverable)*

Implementation source: **`phase-10/`**

- Local runner: `phase-10/scripts/run_scheduler_once.ps1`
- Python CLI: `mf-corpus-refresh` (`phase-10/mf_phase10/refresh.py`)
- Workflow template: `phase-10/workflows/corpus-refresh.yml`

GitHub executes the active workflow at `.github/workflows/corpus-refresh.yml`; `phase-10/workflows/corpus-refresh.yml` is the Phase 10 source template.

| Trigger | When | Purpose |
|---|---|---|
| `schedule` | Daily **02:30 UTC** (`cron: 30 2 * * *`) | Automatic “latest data” pull |
| `workflow_dispatch` | Manual, from GitHub → Actions tab | On-demand refresh (e.g. after Groww page changes) |

**Steps (in order):**

```text
mf-ingest          # Phase 2 — fetch + parse → phase-2/data/processed/*.json
mf-chunk --summary # Phase 3 → phase-3/data/chunks.jsonl
mf-build-index     # Phase 4 — Chroma + BM25 + manifest
mf-build-index verify
mf-build-index export  # optional Parquet audit: embeddings.parquet
```

**Artifacts:** Each successful run uploads a **`corpus-<run_id>`** artifact (14-day retention). On success it also **commits and pushes** `phase-3/data/chunks.jsonl` and `phase-4/data/index/` to `main` (footer `last_updated` follows chunk metadata). Render **Auto-Deploy** on `main` rebuilds the API image. Use workflow input **skip_push** for artifact-only runs.

**Caches:** pip + Hugging Face model cache (`BAAI/bge-small-en-v1.5`) to keep nightly runs fast after the first download.

**Manual options:** `workflow_dispatch` input `skip_index: true` runs ingest + chunk only (no embedding).

**Local equivalent (same pipeline):**

```powershell
.\phase-10\scripts\run_scheduler_once.ps1
```

Fast local scheduler smoke test (no Groww fetch, hashing embedder):

```powershell
.\phase-10\scripts\run_scheduler_once.ps1 -SkipIngest -TestEmbedder
```

#### 10.2.2 CI tests (no scheduler)

Workflow: **`.github/workflows/ci-tests.yml`** — runs `pytest` on push/PR; does **not** call Groww.

#### 10.2.3 Future optimizations

- **Incremental re-embed** when only `content_hash` changes (edge 4.01 / 2.12) — full rebuild today.
- **Commit / sync** refreshed `data/` to a deploy volume (Render/Fly persistent disk or self-hosted runner) instead of downloading artifacts by hand.
- **TTL warning** in answers: if `last_updated` > 14 days, soften footer (Phase 7):
  `"Last updated from sources: 2026-04-29 (verify on the linked Groww page for the latest)."`

### 10.3 Observability
- **Structured logs** (JSON): `{trace_id, query_hash, intent, retrieved_chunk_ids, latency_ms, guard_violations}`.
  Log **query_hash**, never raw query (privacy).
- **Metrics** (Prometheus / Datadog):
  - `requests_total{intent=…, outcome=answered|refused|not_found}`
  - `retrieval_top1_score` (histogram)
  - `guard_violation_total{rule=…}`
- **Alerts**:
  - `guard_violation_total` rate spike
  - Source URL returning non-200 for > 24 h
  - Eval CI failure

### 10.4 Security & compliance posture
- No user accounts, no cookies beyond session id.
- No PII storage — verified by §9.2 PII tests + log scanner.
- All **Groq** LLM calls are server-side only (`GROQ_API_KEY` never on client or in git).
- Robots.txt respected during crawling; rate-limited fetcher.

### 10.5 Exit criteria
- [x] Scheduled refresh live — `.github/workflows/corpus-refresh.yml` enabled on `main` (schedule + `workflow_dispatch`)
- [x] PR CI tests — `.github/workflows/ci-tests.yml`
- [ ] Nightly workflow green for 7 consecutive days on `main`
- [x] One-command deploy readiness (`make deploy` / `phase-10/scripts/deploy.ps1`) + bundled persistent index artifacts
- [x] Runbook documented for: stale source, LLM outage, vector-store corruption

---

## Appendix A — Suggested Repository Layout

Top-level **`docs/`** holds the problem statement, architecture, and edge-case specs.
Each **`phase-N/`** folder is its own installable Python package with a CLI.

```text
RAG-Chatbot-Groww/
├── README.md
├── pytest.ini                        # phase-1 … phase-4 tests
├── .github/workflows/
│   ├── corpus-refresh.yml            # Phase 10 — nightly + manual data refresh
│   └── ci-tests.yml                  # pytest on push/PR
├── docs/
│   ├── architecture.md             ← this file
│   └── edge-cases/                 # per-phase edge-case playbooks
├── phase-1/                        # ✅ Config + verify + stubs (5–10)
│   ├── config/                     # sources, aliases, sections (LOCKED)
│   ├── ingest/                     # sources.py, build_index.py shim → phase-4
│   ├── scripts/verify_phase1.py
│   └── tests/
├── phase-2/                        # ✅ Download + crawl + parse → normalized JSON
│   ├── mf_ingest/                  # fetcher, parser_html, pipeline, cli
│   └── data/
│       ├── raw/                    # HTML snapshots
│       └── processed/              # *.json + ingest_manifest.json
├── phase-3/                        # ✅ Clean + chunk + fields_detected
│   ├── mf_clean/                   # cleaner, groww_clean, chunker, field_detector
│   └── data/chunks.jsonl           # main handoff to Phase 4
├── phase-4/                        # ✅ Embed + Chroma + BM25 + hybrid
│   ├── mf_index/                   # embedder, vector_store, bm25, hybrid, build_index
│   └── data/index/                 # chroma/, bm25/, manifest, embeddings.parquet (export)
└── phase-1/ …                      # app/, retrieval/, eval/ — Phase 5–10 (planned)
```

### End-to-end commands (implemented path)

```powershell
cd phase-2 && pip install -e ".[dev]" && mf-ingest
cd ..\phase-3 && pip install -e ".[dev]" && mf-chunk --summary
cd ..\phase-4 && pip install -e ".[dev]" && mf-build-index && mf-build-index verify
```

## Appendix B — Tech Stack Summary

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 | Ecosystem fit (RAG, parsing, ML) |
| API | FastAPI + Uvicorn | Async, typed, fast |
| UI | Next.js (App Router + Tailwind) on Vercel | Production-leaning from day one |
| HTML parsing | trafilatura + selectolax + BeautifulSoup fallback | Boilerplate removal + Lexbor `h2` walk + BS4 for odd markup |
| Embeddings | `bge-small-en-v1.5` | Free, CPU-friendly, strong on short queries |
| Vector store | Chroma (file-backed) | Sufficient for 60–80 chunks; zero infra |
| Lexical | rank_bm25 | Zero infra, complements vectors |
| Re-ranker | `bge-reranker-base` | Major quality jump on top-k |
| LLM | **Groq** — `llama-3.3-70b-versatile` (fallback `llama-3.1-8b-instant`) | Fast inference, instruction-faithful, OpenAI-compatible API |
| Observability | structlog + Prometheus | Standard, low overhead |
| CI | GitHub Actions | Run eval harness on every PR + nightly ingest cron |

## Appendix C — Risk Register (Top 5)

| # | Risk | Mitigation |
|---|---|---|
| 1 | **Stale numbers** (NAV / expense ratios change frequently) | Nightly re-fetch of all 10 Groww URLs + content-hash diff + 14-day age-warning footer |
| 2 | **Hallucinated citation** (LLM invents a URL) | Output guard's allow-list = the 10 Groww URLs; any other URL is replaced with the source chunk's URL |
| 3 | **Advisory leak** ("best fund" sneaks through) | Banned-token check + refusal templates + 20 advisory queries in eval set |
| 4 | **PII in user query saved to logs** | Pre-log PII scrubber + `query_hash` logging only |
| 5 | **Groww blocks the crawler / changes page structure** | Respect `robots.txt`, ≤ 1 req/sec, exponential backoff. **Structural break** detected when section-extractor returns `< N` expected sections → CI alarm + cached previous snapshot served |
| 6 | **Question outside the 10-page corpus** (e.g. "expense ratio of SBI Small Cap?") | Pre-filter requires scheme ∈ alias dictionary; otherwise NOT_FOUND template — never invent |

---

**End of phase-wise architecture.**

**Done:** Phases **1–9** (through eval harness). **Next:** Phase **10** (deploy + **enable** GitHub Actions corpus scheduler per §10.2).
