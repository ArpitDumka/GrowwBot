# Phase 10 Observability

## Current Signals

- API responses include `trace_id`.
- API logs include:
  - `trace_id`
  - `query_hash`
  - `outcome`
  - `latency_ms`
  - `used_llm`
  - `chunk_id`
  - `guard_violations`
  - `log_safe`
- Phase 10 log scanner checks for obvious raw-query logging regressions:
  ```powershell
  mf-log-scan
  ```

## Local Checks

```powershell
.\phase-10\scripts\verify_phase10.ps1
```

## Alert Targets

- Corpus refresh failure in GitHub Actions
- Eval workflow failure
- Repeated `ERROR` outcomes from chat API
- `guard_violations` spike
- Source URL fetch failures lasting more than 24 hours

## Privacy

Logs should store hashes and operational metadata only. Do not log raw user queries,
PAN, Aadhaar, phone, email, account numbers, OTPs, or passwords.

