# Phase 5 — Query Understanding & Guardrails

Pre-retrieval compliance gate: **PII strip → intent classify → scheme/field extract → query rewrite**.

| Sub-phase | Module | Role |
|---|---|---|
| 5.1 | `mf_guard/pii.py` | PAN/Aadhaar/phone/email/OTP detection; log scrubbing |
| 5.2 | `mf_guard/intent.py` | Rule-based intent (FACT, ADVISORY, PERFORMANCE, …) |
| 5.3 | `mf_guard/scheme_field.py` | Alias + fuzzy scheme match; field synonyms |
| 5.4 | `mf_guard/rewriter.py` | Deterministic abbreviation expansion |
| 5.5 | `mf_guard/pipeline.py` | Ordered pipeline → `GuardResult` for Phase 6 |

Config: `phase-5/config/*.yaml`. Scheme aliases: `phase-1/config/aliases.yaml`.

## Install

```powershell
cd phase-5
pip install -e ".[dev]"
```

## Run

```powershell
mf-guard analyze "What is the expense ratio of HDFC Mid Cap Fund?"
mf-guard verify
mf-guard demo
pytest
```

`verify` checks §5.3: all advisory fixture queries are refused and refusal templates never echo the user query.
