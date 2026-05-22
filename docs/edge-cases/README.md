# Edge Cases — Index

Companion docs to `../architecture.md`. Each file lists known failure modes, weird inputs, and adversarial cases for the corresponding phase, plus how the system should behave.

## How to read these docs

Every edge case is a row in a table with:

| Column | Meaning |
|---|---|
| **ID** | Stable identifier (`<phase>.<nn>`). Reference these in PRs, tests, and bug reports. |
| **Trigger** | What input or condition exposes the case. |
| **Expected behavior** | What the system MUST do. This is the contract. |
| **Detection** | How we know the case is occurring (logs, metrics, asserts). |
| **Mitigation** | The code/config change that handles it. |
| **Priority** | `P0` = ship-blocker, `P1` = must-fix before scale, `P2` = nice-to-have. |

## Files

| Phase | Topic | File |
|---|---|---|
| 1 | Source selection & corpus lock | [phase-1-source-selection.md](./phase-1-source-selection.md) |
| 2 | Ingestion (fetch + parse) | [phase-2-ingestion.md](./phase-2-ingestion.md) |
| 3 | Cleaning, chunking, metadata | [phase-3-chunking.md](./phase-3-chunking.md) |
| 4 | Embedding & index build | [phase-4-indexing.md](./phase-4-indexing.md) |
| 5 | Query understanding & guardrails | [phase-5-guardrails.md](./phase-5-guardrails.md) |
| 6 | Retrieval | [phase-6-retrieval.md](./phase-6-retrieval.md) |
| 7 | Answer composition (LLM + output guard) | [phase-7-composition.md](./phase-7-composition.md) |
| 8 | UI / UX | [phase-8-ui.md](./phase-8-ui.md) |
| 9 | Evaluation & QA | [phase-9-evaluation.md](./phase-9-evaluation.md) |
| 10 | Deployment, observability, maintenance | [phase-10-deployment.md](./phase-10-deployment.md) |

## Test-coverage rule of thumb

- Every **P0** edge case MUST have an automated test (unit / integration / eval).
- Every **P1** edge case SHOULD have a test, or at minimum a runbook entry.
- **P2** cases are tracked but may be handled reactively.
