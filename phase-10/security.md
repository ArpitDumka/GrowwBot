# Phase 10 Security & Compliance

## Guarantees

- Groq key is server-side only (`GROQ_API_KEY`).
- `.env` must never be committed.
- Chat logs must use `query_hash`, not raw query text.
- PII is rejected before retrieval / LLM composition.
- Corpus refresh respects the Phase 2 fetcher rate limits and robots checks.

## Local Verification

```powershell
mf-log-scan
python -m pytest phase-5/phase5_tests/test_pii.py -q
```

## Deployment Notes

- Set `GROQ_API_KEY` in Render, not Vercel.
- Set `NEXT_PUBLIC_API_URL` in Vercel; this is public by design.
- Keep Chroma/BM25 index artifacts versioned with the deployed backend image.

