# Phase 9 — Evaluation, QA & Safety Testing

Automated harness over a **90-question** curated set (§9.1): factual, advisory, performance, PII, and out-of-scope cases.

## Layout

| Path | Role |
|------|------|
| `config/qa_set.yaml` | Hand-curated / generated test cases |
| `config/tolerances.yaml` | Per-field numeric tolerances, link-check policy |
| `config/targets.yaml` | §9.2 metric thresholds |
| `mf_eval/runner.py` | Runs pipeline or API, computes metrics |
| `eval/report.md` | Human-readable report (gitignored) |

## Commands

```powershell
pip install -e ..\phase-4 -e ..\phase-5 -e ..\phase-6 -e ..\phase-7 -e .

# Validate QA set coverage (10 schemes × min questions)
mf-eval validate

# Regenerate qa_set.yaml from sources + chunks
python scripts/generate_qa_set.py

# CI eval (stub LLM + test reranker, no Groq)
mf-eval run --ci --skip-link-check --test-reranker

# Live eval (needs GROQ_API_KEY)
mf-eval run --live-groq --test-reranker

# Against running API
mf-eval run --mode api --api-url http://127.0.0.1:8000
```

## Sub-phases

| § | Deliverable |
|---|-------------|
| 9.1 | `config/qa_set.yaml` — 40 factual + 20 advisory + 10 performance + 10 PII + 10 OOS |
| 9.2 | `config/targets.yaml` + metrics in report |
| 9.3 | `mf-eval run` → checks (outcome, regex, banned tokens, sentences, links) |
| 9.4 | `.github/workflows/eval.yml` — runs on PR |

See `docs/architecture.md` §9 and `docs/edge-cases/phase-9-evaluation.md`.
