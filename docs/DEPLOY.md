# Deploy: Vercel (frontend) + Render (backend)

## Before you push to GitHub

Run the readiness check from the **repository root**:

```powershell
.\scripts\verify_deploy_ready.ps1
# optional full Docker build (slow):
.\scripts\verify_deploy_ready.ps1 -Docker
```

**Commit these for production** (they are no longer gitignored):

| Path | Why |
|------|-----|
| `phase-3/data/chunks.jsonl` | Retrieval corpus |
| `phase-4/data/index/` | Chroma + BM25 + manifest (not `backups/`) |
| `phase-1/config/` | Sources + LLM config |
| `render.yaml`, `Dockerfile` | Render |
| `phase-8/web/` (no `node_modules/`) | Vercel |

**Never commit:** `.env`, `phase-8/web/node_modules/`, `phase-8/web/.next/`

Optional local Docker smoke test (needs `GROQ_API_KEY` in `.env`):

```powershell
docker compose up --build
```

---

Production layout:

```text
Browser → Vercel (Next.js, phase-8/web)
              ↓ HTTPS POST /api/v1/chat
          Render (FastAPI Docker, repo root Dockerfile)
              ↓
          Chroma + BM25 index (bundled in image)
          Groq API (GROQ_API_KEY)
```

---

## 1. Render — backend API

### Option A — Blueprint (recommended)

1. Push this repo to GitHub.
2. [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**.
3. Connect the repo. Render reads **`render.yaml`** at the repository root.
4. Set **`GROQ_API_KEY`** when prompted (same key as local `.env`).
5. Deploy. Note the service URL, e.g. `https://mf-faq-api.onrender.com`.

### Option B — Manual Docker service

1. **New** → **Web Service** → connect repo.
2. **Runtime:** Docker  
3. **Dockerfile path:** `./Dockerfile`  
4. **Health check path:** `/healthz`  
5. **Environment variables:**

| Key | Value |
|-----|--------|
| `GROQ_API_KEY` | Your Groq API key (required) |
| `CORS_EXTRA_ORIGINS` | Optional — custom Vercel URL, e.g. `https://your-app.vercel.app` |
| `FRONTEND_URL` | Vercel app URL shown on `GET /` (e.g. `https://groww-bot.vercel.app`) |

**Corpus auto-update:** `.github/workflows/corpus-refresh.yml` runs daily at 02:30 UTC, then **commits and pushes** refreshed `phase-3/data/chunks.jsonl` and `phase-4/data/index/` to `main`. Enable **Auto-Deploy** on Render for `main` so production picks up new `Last updated from sources` dates without manual artifact download. If push fails, check branch protection (allow `github-actions[bot]` to push) or run workflow with **skip_push** and deploy manually.

6. **Plan:** Use at least **Starter** (512MB+ RAM). The embedder + Chroma need memory; free tier may OOM.

### Verify API

```bash
curl https://YOUR-SERVICE.onrender.com/healthz
curl https://YOUR-SERVICE.onrender.com/api/v1/bootstrap
```

First chat request after idle may take **30–90s** (cold start + model load).

---

## 2. Vercel — frontend

1. [Vercel Dashboard](https://vercel.com/) → **Add New** → **Project** → import the GitHub repo.
2. **Root Directory:** `phase-8/web`
3. **Framework:** Next.js (auto-detected)
4. **Environment variables** (Production + Preview):

| Key | Value |
|-----|--------|
| `NEXT_PUBLIC_API_URL` | Render API URL, e.g. `https://mf-faq-api.onrender.com` (no trailing slash) |

5. **Deploy**.

CORS: `*.vercel.app` is already allowed in `phase-8/config/api.yaml`. For a **custom domain**, add it to Render as `CORS_EXTRA_ORIGINS=https://your-domain.com`.

### Verify UI

Open the Vercel URL → sample question → answer with `[Source](...)` link.

If you see “Cannot reach API”, check `NEXT_PUBLIC_API_URL` and that Render service is **Live**.

---

## 3. Local parity

```powershell
# Terminal 1 — API
cd phase-8
mf-api serve --test-reranker

# Terminal 2 — Web
cd phase-8\web
copy .env.example .env.local
npm run dev
```

---

## 4. Troubleshooting

| Symptom | Fix |
|---------|-----|
| CORS error in browser | Set `CORS_EXTRA_ORIGINS` on Render to your exact Vercel URL; redeploy API. |
| 502 / timeout on Render | Upgrade plan; first request warms embedder — retry. |
| `GROQ_API_KEY is not set` | Add key in Render → Environment, redeploy. |
| Empty / NOT_FOUND for all queries | Ensure `phase-4/data/index` is committed and included in Docker build. |
| Vercel build fails | Root directory must be `phase-8/web`, not repo root. |

---

## Files reference

| File | Purpose |
|------|---------|
| `render.yaml` | Render Blueprint (Docker service) |
| `Dockerfile` | API image (phases 1–8 data + deps) |
| `phase-8/web/vercel.json` | Vercel build settings |
| `phase-8/config/api.yaml` | CORS + rate limits |
