# Phase 10 Runbooks

Operational playbooks for deployment, observability, and corpus freshness.

## Quick Checks

```powershell
.\phase-10\scripts\verify_phase10.ps1
```

## Runbooks

- `stale-source.md` - Groww source stale or fetch failing
- `llm-outage.md` - Groq outage or key problem
- `vector-store-corruption.md` - Chroma/BM25 index cannot load
- `inaccurate-answer.md` - User reports a wrong answer
- `deploy.md` - one-command deploy wrapper and manual deploy notes

