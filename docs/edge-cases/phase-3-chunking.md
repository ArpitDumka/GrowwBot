# Phase 3 — Edge Cases: Cleaning, Chunking & Metadata

> Companion to `../architecture.md` Phase 3. ~60–80 chunks total across the 10 Groww pages.

## Edge cases

| # | ID | Trigger | Expected behavior | Detection | Mitigation | Priority |
|---|---|---|---|---|---|---|
| 1 | 3.01 | Groww renames a section header (e.g., "Exit Load" → "Loads & Charges") | Section extractor uses a **set of synonyms per section** (configured in `config/sections.yaml`), not a single literal | Section count drops compared to previous run | Synonym map + structural-break alert (see 2.05) | P0 |
| 2 | 3.02 | Numeric value split across whitespace/newline (`₹4,433.\n98 Cr`) | Cleaner joins broken numbers using a regex that detects digit-then-newline-then-digit before tokenization | Field detector fails to find AUM where expected | Pre-cleaner pass: `re.sub(r'(\d)\s*\n\s*(\d)', r'\1\2', text)` | P0 |
| 3 | 3.03 | Multiple historical exit-load entries listed (Groww shows current + history) | Only the **most-recent** entry (top of the list) is kept in the chunk; older entries are discarded | Date sort on the exit-load list | Section parser sorts by date desc and keeps row 0 | P0 |
| 4 | 3.04 | Tax info has two clauses ("If you redeem within X… If you redeem after X…") | Both clauses must stay in the **same chunk**; never split mid-condition | Sentence splitter must not break on the period after "X." | Override sentence splitter to keep adjacent conditional clauses together | P0 |
| 5 | 3.05 | AUM in mixed units (₹Cr vs ₹Lakh vs ₹Crore vs full digits) | Field detector normalizes to **₹ Cr** (1 Lakh = 0.01 Cr; raw digits → divide by 1e7) | Unit suffix sniff | Post-extraction normalizer in `field_detector.py`; preserve original text in chunk for traceability | P1 |
| 6 | 3.06 | Currency symbol garbled to `?` due to upstream encoding (see 2.08) | Field detector treats `?\d` as `₹\d` only if other currency-shaped tokens are absent; otherwise drops the chunk and re-fetches | Sniff for replacement character | Encoding fallback in fetcher (2.08) is the real fix; this is the safety net | P1 |
| 7 | 3.07 | Section is empty (e.g., HDFC Manufacturing Fund has no 3Y returns yet) | Section is **omitted entirely** — not stored as an empty chunk; downstream queries get NOT_FOUND | Length check post-clean | `if len(text.strip()) < 30: skip` | P0 |
| 8 | 3.08 | Boilerplate "Understand terms" definitions block leaks into a chunk and pollutes BM25 | Cleaner has a **denylist** of definition phrases ("Annualised returns", "Absolute returns", "Expense ratio A fee payable…") that triggers excision | Substring match on known definitions | Denylist in `phase-3/mf_clean/cleaner.py`; assert removed in unit tests | P0 |
| 9 | 3.09 | ELSS-specific lock-in banner appears on a non-ELSS page (Groww UI bug, hypothetical) | Field detector trusts the **scheme metadata** (`category`), not the banner text; banner is ignored if `category != ELSS` | Cross-check banner vs category | Validator: `lock_in` field only allowed when `category == "ELSS"` | P1 |
| 10 | 3.10 | Holdings table has 50+ rows, blowing the 600-token chunk cap | Holdings chunker keeps **top 10 by `Assets %`**; trailing rows go into a single rolled-up "remaining N holdings" sentence | Token-count assertion | Holdings extractor sorts and slices to top 10 | P1 |
| 11 | 3.11 | Chunk smaller than 30 tokens (e.g., minimum_investments section is just three numbers) | Merge with the adjacent `header` chunk for the same scheme | Per-chunk token count | Merge pass after initial chunking | P1 |
| 12 | 3.12 | A chunk contains both a fact and a forecast/opinion (rare on Groww, but defensive) | Cleaner has a **forecast-token denylist** (`expected to`, `likely to`, `forecast`, `outlook`) — chunks containing them are kept but marked `risky: true` so the retriever de-prioritizes | Substring scan | Mark + downrank, do not delete (preserves traceability) | P1 |
| 13 | 3.13 | `last_updated` cannot be inferred from the page | Use the `fetched_at` date as a fallback `last_updated`; mark with `last_updated_inferred: true` | Missing `last_updated` field | Footer in answer says "Last updated from sources: <fetched_at>" — still honest | P0 |
| 14 | 3.14 | Two schemes share a section with identical text (e.g., generic stamp-duty clause) | Both chunks are kept (cheap on a 60–80 chunk corpus) but tagged with their distinct `scheme`; retriever's pre-filter on `scheme` keeps them separate | None needed | No dedup across schemes — by design | P2 |
| 15 | 3.15 | Field detector regex for `expense_ratio` matches a context like "Expense ratio is the…" (definition) instead of the value | Regex requires `\d+(\.\d+)?\s*%` within 20 chars and ignores matches inside the boilerplate definitions block (3.08) | Unit test with definition strings | Regex with positive numeric look-ahead + denylist | P0 |

## Quick example: post-chunking row

```json
{
  "chunk_id": "hdfc_pharma#exit_load_tax",
  "section": "exit_load_tax",
  "scheme": "HDFC Pharma & Healthcare Fund",
  "text": "Exit load of 1%, if redeemed within 30 days. Stamp duty on investment: 0.005% (from July 1st, 2020). If you redeem within one year, returns are taxed at 20%. If you redeem after one year, returns exceeding Rs 1.25 lakh in a financial year are taxed at 12.5%.",
  "fields_detected": ["exit_load", "tax", "stamp_duty"],
  "last_updated": "2026-05-13"
}
```
