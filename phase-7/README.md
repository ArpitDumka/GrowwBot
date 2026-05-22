# Phase 7 — Answer Composition (Groq + Output Guard)

Turns Phase 6 retrieval into a **≤3 sentence** cited answer via **Groq**, then runs deterministic output guard (§7.3).

| Sub-phase | Module |
|---|---|
| 7.1 | `mf_compose/prompts.py` |
| 7.2 | `mf_compose/groq_client.py`, `llm_config.py` |
| 7.3 | `mf_compose/output_guard.py` |
| 7.4 | `mf_compose/composer.py`, `pipeline.py` |

## Setup

```powershell
copy ..\.env.example ..\.env
# Set GROQ_API_KEY in ..\.env

pip install -e "..\phase-4"
pip install -e "..\phase-5"
pip install -e "..\phase-6"
pip install -e ".[index,dev]"
```

## Run

```powershell
mf-compose ask "What is the exit load on HDFC ELSS Tax Saver Fund?"
mf-compose verify --test-reranker
mf-compose ask "..." --mock-llm
```

LLM config: `phase-1/config/llm.yaml`. Banned tokens: `phase-7/config/banned_tokens.yaml`.
