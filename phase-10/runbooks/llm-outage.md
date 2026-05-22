# Runbook: Groq / LLM Outage

## Symptoms

- Chat responses return `ERROR`.
- Backend logs include `Groq completion failed`.
- `/api/v1/chat` works for refusals but not normal RAG answers.

## Triage

1. Confirm `GROQ_API_KEY` exists in the backend environment.
2. Check `phase-1/config/llm.yaml` model ids.
3. Test a normal factual query and inspect `used_llm`.

## Mitigation

- Rotate or re-add `GROQ_API_KEY` in Render.
- If the primary model is retired, update `model.id` and `pinned_model_id` in `phase-1/config/llm.yaml`.
- Keep guardrails enabled; never bypass output guard to recover service.

## Verification

```powershell
cd phase-7
python -m pytest phase7_tests -q
```

