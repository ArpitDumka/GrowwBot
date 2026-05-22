# Runbook: Inaccurate Answer

## Symptoms

- User reports a wrong fact.
- Citation points to a Groww page, but the answer text does not match the page.
- Eval harness fails a known QA case.

## Triage

1. Reproduce with the exact user question.
2. Check the retrieved chunk:
   ```powershell
   cd phase-4
   mf-build-index search "USER QUESTION HERE" --top-k 5
   ```
3. Check output guard behavior:
   ```powershell
   cd phase-7
   python -m pytest phase7_tests -q
   ```
4. Run eval:
   ```powershell
   cd phase-9
   mf-eval run --ci --skip-link-check --test-reranker
   ```

## Mitigation

- If retrieval picked the wrong chunk, tune Phase 6 field/section boosts or rebuild the corpus.
- If the chunk is stale, run:
  ```powershell
  .\phase-10\scripts\run_scheduler_once.ps1
  ```
- If Groq invented a number, keep the output guard strict and add the case to Phase 9 eval.

## Verification

- The same query returns the corrected answer.
- The answer source URL is allow-listed and visible in the UI.
- Phase 9 eval passes.

