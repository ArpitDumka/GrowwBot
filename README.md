# Mutual Fund FAQ Assistant (RAG)

Facts-only HDFC mutual fund FAQ chatbot (Groww corpus). Phases 1–9 implemented.

| Layer | Location | Run locally |
|-------|----------|-------------|
| Ingest → index | `phase-1` … `phase-4` | See `docs/architecture.md` |
| Guard → retrieve → compose | `phase-5` … `phase-7` | `mf-compose` / tests |
| **API (Render)** | `phase-8/mf_api` | `mf-api serve` |
| **UI (Vercel)** | `phase-8/web` | `npm run dev` |
| **Eval (Phase 9)** | `phase-9` | `mf-eval run --ci --test-reranker` |

## Deploy (when ready to push to GitHub)

1. **Pre-flight:** `.\scripts\verify_deploy_ready.ps1` (from repo root)
2. **Guide:** [docs/DEPLOY.md](docs/DEPLOY.md) — Render (backend) + Vercel (frontend)
3. **Env templates:** `deploy/render.env.example`, `deploy/vercel.env.example`, `.env.example`

**Do not commit** `.env` or `phase-8/web/node_modules`. **Do commit** `phase-3/data/chunks.jsonl` and `phase-4/data/index/` for production API.

## Local quick start (separate backend + frontend)

**Two terminals** (recommended):

```powershell
# Terminal 1 — API http://127.0.0.1:8000
.\scripts\run_backend.ps1

# Terminal 2 — Next.js http://localhost:3000
.\scripts\run_frontend.ps1
```

Or one command (opens two windows): `.\scripts\run_local.ps1`

Full guide: **[docs/LOCAL_DEV.md](docs/LOCAL_DEV.md)** — fine-tuning, Groq live mode, curl tests.

Copy `.env.example` → `.env` and set `GROQ_API_KEY` for live LLM answers (`run_backend.ps1 -LiveGroq`).
