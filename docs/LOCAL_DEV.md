# Local development — separate backend & frontend

Run the **API** and **UI** on different ports so you can test and tune before GitHub / Vercel / Render.

| Service | URL | Terminal script |
|---------|-----|-----------------|
| **Backend** (FastAPI) | http://127.0.0.1:8000 | `.\scripts\run_backend.ps1` |
| **Frontend** (Next.js) | http://localhost:3000 | `.\scripts\run_frontend.ps1` |
| API docs (Swagger) | http://127.0.0.1:8000/docs | (same as backend) |

Or open both at once: `.\scripts\run_local.ps1`

---

## One-time setup

From the **repository root**:

```powershell
# Python stack (phases 4–8)
pip install -e phase-4 -e phase-5 -e phase-6 -e phase-7 -e "phase-8[index,dev]"

# Optional: Phase 9 eval
pip install -e phase-9

# Groq (live answers) — copy and edit
copy .env.example .env
# Set GROQ_API_KEY=...

# Next.js deps
cd phase-8\web
npm install
copy .env.example .env.local
cd ..\..
```

Ensure the index exists (if you cloned fresh):

```powershell
cd phase-2; mf-ingest
cd ..\phase-3; mf-chunk --summary
cd ..\phase-4; mf-build-index
```

---

## Daily workflow (two terminals)

**Terminal 1 — backend only**

```powershell
.\scripts\run_backend.ps1
```

- Fast iteration without Groq: default uses `--test-reranker`.
- Real LLM answers:

```powershell
.\scripts\run_backend.ps1 -LiveGroq
```

- Auto-reload API code on save:

```powershell
.\scripts\run_backend.ps1 -Reload
```

**Terminal 2 — frontend only** (start backend first)

```powershell
.\scripts\run_frontend.ps1
```

The UI reads `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` from `phase-8/web/.env.local`.

---

## Test backend without the UI

```powershell
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/api/v1/bootstrap

curl -X POST http://127.0.0.1:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d "{\"query\": \"What is the expense ratio of HDFC Mid Cap Fund?\"}"
```

Or use **http://127.0.0.1:8000/docs** in the browser.

---

## Fine-tuning checklist

| What to tune | Where |
|--------------|--------|
| Retrieval / field routing | `phase-6/config/retrieval.yaml` |
| Guard / refusal | `phase-5/config/*.yaml` |
| LLM model / tokens | `phase-1/config/llm.yaml` + `.env` `GROQ_API_KEY` |
| Sample questions / CORS | `phase-8/config/` |
| UI copy / timeout | `phase-8/web/components/` |
| Automated QA | `mf-eval run --ci` or `--live-groq` |

After changing **chunks or index**:

```powershell
cd phase-3; mf-chunk --summary
cd ..\phase-4; mf-build-index
# Restart backend
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Frontend: “Cannot reach API” | Start `run_backend.ps1` first; check http://127.0.0.1:8000/healthz |
| CORS error in browser | Backend `phase-8/config/api.yaml` allows `localhost:3000` |
| Slow first question | First load downloads embedder; use `--test-reranker` for speed |
| Wrong / empty answers | Use `-LiveGroq` and valid `GROQ_API_KEY`; restart backend after index rebuild |
| Port in use | Change port: `mf-api serve --port 8001` and `run_frontend.ps1 -ApiUrl http://127.0.0.1:8001` |

---

## vs production

| | Local | Production |
|---|--------|------------|
| Backend | `127.0.0.1:8000` | Render (Docker) |
| Frontend | `localhost:3000` | Vercel (`phase-8/web`) |
| Env | `.env`, `phase-8/web/.env.local` | Render + Vercel dashboards |

See [DEPLOY.md](DEPLOY.md) when you are ready to push to GitHub.
