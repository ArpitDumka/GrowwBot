# Phase 9 — Edge Cases: Evaluation & QA

> Companion to `../architecture.md` Phase 9. ~95-question eval set, runs on every PR.

## Edge cases

| # | ID | Trigger | Expected behavior | Detection | Mitigation | Priority |
|---|---|---|---|---|---|---|
| 1 | 9.01 | **Eval set goes stale** (e.g., HDFC Pharma expense ratio changed from 1.51% → 1.49%) | Eval set stores `expected_value` AND `last_verified_date`. CI fails when `last_verified_date` is older than N days OR when expected fact mismatches the live source. | Date-aware test runner | Quarterly review + auto-fail on staleness | P0 |
| 2 | 9.02 | **Numeric tolerance** — exact match vs ±0.01% | Field-specific tolerance config: `expense_ratio: ±0.01`, `aum: ±5%`, `nav: ±0.5%` (because NAV moves daily) | Per-field comparator | `eval/tolerances.yaml` | P0 |
| 3 | 9.03 | **Citation URL changed** (Groww renamed slug — see 1.01) | Eval test compares URL after canonicalization (strip trailing slash, lowercase host); if redirected, follow once and accept the redirect target | URL canonicalizer | Redirect-aware comparator | P0 |
| 4 | 9.04 | **False positive**: LLM gave correct fact but with a wrong unit (`0.21` instead of `0.21%`) | Test parses the answer with a field-aware extractor and validates unit; failure logged with `WRONG_UNIT` reason | Unit-aware regex | Output guard 7.17 should prevent it; eval is the safety net | P0 |
| 5 | 9.05 | **New refusal phrasing** that the eval set doesn't cover (e.g., a new way of asking "best fund") | Eval set is treated as living: every observed false-pass in production becomes a new test case | Production logs feed back to eval | Weekly triage of "answered but should have been refused" | P1 |
| 6 | 9.06 | **LLM nondeterminism** at temperature=0 (still has minor drift across versions) | Tests assert on **content**, not exact string match: "answer must contain `0.21%` AND a Groww URL AND the footer" | Content-based assertions | Avoid string-equality on full answer | P0 |
| 7 | 9.07 | **Eval CI vs prod model drift** (Groq model id or snapshot changes) | Pin `pinned_model_id` in `phase-1/config/llm.yaml`; CI uses the same id; release notes track when we bump | Model ID assertion | Model pin + bump checklist | P0 |
| 8 | 9.08 | A passing eval suite **masks a regression** in retrieval quality (LLM compensates) | Add **retrieval-only** assertions: top-1 chunk for question Q must have `chunk_id = X`. Decoupled from LLM output. | Retrieval-stage golden set | Two-tier eval: retrieval golden + answer golden | P0 |
| 9 | 9.09 | **PII test set leaks** into git/log | PII test cases use **synthetic, clearly-fake** values (e.g., `ABCDE1234F` is the canonical fake PAN); add an explicit `# fake-pii` comment | Code review | Convention + linter rule | P0 |
| 10 | 9.10 | **Refusal test answers in unexpected ways** (e.g., LLM correctly refuses but adds a recommendation phrase) | Refusal tests assert on **template equality** (one of the known refusal templates) and absence of banned tokens | Template equality + denylist | Two-condition assertion | P0 |
| 11 | 9.11 | **Eval is too fast** — passes in 5 sec, missing slow-path tests (timeouts, retries) | Add a small set of **failure-injection** tests: simulate LLM timeout, source 503, etc. | Marker `@pytest.mark.failure_injection` | Mock provider + assertions on graceful degradation | P1 |
| 12 | 9.12 | **Eval data drift**: someone hand-edits a chunk in `data/processed/` to make a test pass | `data/processed/` is regenerated from `config/sources.yaml` every CI run; no manual edits permitted | Hash check at start of CI | Build the index from scratch in CI | P0 |
| 13 | 9.13 | A new scheme is added to the corpus but the eval set isn't updated | Eval validator asserts every scheme in `sources.yaml` has at least 3 factual + 1 advisory + 1 PII test | Coverage check | Coverage gate in CI | P0 |
| 14 | 9.14 | **Latency budget regression** (p95 jumps from 3s to 5s) | Eval reports per-stage latency; CI fails if regression > 25% vs baseline | Latency tracking per run | Trend file in `eval/baselines/` | P1 |
| 15 | 9.15 | A factual question has **multiple valid phrasings** of the same answer (e.g., "1% within 1 year" vs "1 percent if redeemed within one year") | Use semantic similarity (`bge-small`) ≥ 0.85 OR a regex-OR pattern as the comparator for free-text fields | Configurable per-test | `match_type: regex | semantic | exact` per case | P1 |
| 16 | 9.16 | **Eval false negative** — system gave a perfectly fine answer but with paraphrasing the test didn't expect | Triage process: tag false-fails for review; promote to a `match_type: semantic` case if reviewer agrees | Review queue | Weekly eval triage meeting | P1 |
| 17 | 9.17 | A test case asks about a field we **don't store** (e.g., Sharpe ratio) | Should be a **NOT_FOUND** case, not a factual case. Test asserts NOT_FOUND template, not a fabricated value. | Test type label | `expected: not_found` semantics | P0 |
| 18 | 9.18 | LLM provider is rate-limited during CI run | CI eval has its own quota and retry; on persistent rate limit, eval is marked `infra-failed` (distinct from regression) | Distinct exit codes | `infra_failed` vs `regression` | P1 |
| 19 | 9.19 | The **link-resolves** sub-check is flaky because Groww blocks CI's IP | Use a 30s timeout + 1 retry; if still fails, mark as `link_check_skipped` rather than failing the run | Status code 0 / timeout | Soft-fail on link checks; hard-fail on answer correctness | P1 |
| 20 | 9.20 | Someone **lowers a target** in `9.2` to make CI pass | Targets are tracked in `eval/targets.yaml` with code-owner protection on the file | Branch protection rule | CODEOWNERS gate | P0 |

## Eval question schema (`eval/qa_set.yaml`)

```yaml
- id: q.expense_ratio.hdfc_pharma
  question: "What is the expense ratio of HDFC Pharma & Healthcare Fund?"
  expected_type: factual
  expected_fields:
    expense_ratio: { value: 1.51, unit: "%", tolerance: 0.01 }
  expected_url: "https://groww.in/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth"
  match_type: exact
  last_verified: "2026-05-13"
  notes: "Update if AMC changes expense ratio"
```
