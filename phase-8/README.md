# Phase 8 — HTTP API (FastAPI backend)

REST backend for the Phase 8 UI. Wires **Phases 5→6→7** via `mf_compose.chat()`.

| Sub-phase | Module |
|---|---|
| 8.API | `mf_api/app.py` — routes, CORS, rate limit |
| 8.Bootstrap | `mf_api/bootstrap.py`, `config/sample_questions.yaml` |
| 8.Service | `mf_api/service.py` |

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/healthz` | Liveness |
| `GET` | `/api/v1/bootstrap` | Disclaimer + 3 sample questions (for UI) |
| `POST` | `/api/v1/chat` | Ask a question (`{"query": "..."}` only — not in URL) |

Response header: `x-trace-id` on every `/chat` response.

## Setup

```powershell
pip install -e "..\phase-4" -e "..\phase-5" -e "..\phase-6" -e "..\phase-7"
pip install -e ".[index,dev]"
copy ..\.env.example ..\.env   # GROQ_API_KEY for live answers
```

## Run

```powershell
mf-api verify --test-reranker
mf-api serve --test-reranker
```

Smoke:

```powershell
curl http://127.0.0.1:8000/api/v1/bootstrap
curl -X POST http://127.0.0.1:8000/api/v1/chat -H "Content-Type: application/json" -d "{\"query\": \"What is the exit load on HDFC ELSS Tax Saver Fund?\"}"
```

## UI — Next.js on Vercel (`phase-8/web/`)

See [web/README.md](web/README.md). Summary:

```powershell
# Terminal 1 — API
mf-api serve --test-reranker

# Terminal 2 — Web
cd web
copy .env.example .env.local
npm install && npm run dev   # http://localhost:3000
```

Vercel: root directory `phase-8/web`, env `NEXT_PUBLIC_API_URL=<deployed-api-url>`.

**Full steps:** [docs/DEPLOY.md](../docs/DEPLOY.md) (Render Docker + Vercel).
