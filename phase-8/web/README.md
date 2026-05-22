# Phase 8 — Next.js UI (Vercel)

Production frontend for the Mutual Fund FAQ assistant. Calls the FastAPI backend via `POST /api/v1/chat` only (query never in the URL).

## Local development

```powershell
# Terminal 1 — API (from phase-8)
mf-api serve --test-reranker

# Terminal 2 — Web
cd phase-8/web
copy .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` in `.env.local`.

## Deploy to Vercel (frontend)

1. Import the repo in [Vercel](https://vercel.com/).
2. **Root Directory:** `phase-8/web`
3. **Environment variable:** `NEXT_PUBLIC_API_URL` = your **Render** API URL (e.g. `https://mf-faq-api.onrender.com`)
4. Deploy.

See **[docs/DEPLOY.md](../../docs/DEPLOY.md)** for the full Render + Vercel checklist.

## Backend on Render

The API is **not** hosted on Vercel. Use the repo root **`render.yaml`** + **`Dockerfile`**:

1. Render → **New Blueprint** (or Web Service → Docker).
2. Set `GROQ_API_KEY`.
3. Copy the service URL into Vercel as `NEXT_PUBLIC_API_URL`.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Next.js dev server |
| `npm run build` | Production build |
| `npm test` | Vitest (PII + answer parser) |
