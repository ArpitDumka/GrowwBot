# Runbook: Deployment

## Goal

Verify Phase 10 readiness, then deploy the API on Render and the UI on Vercel.

## One-command local readiness

```powershell
.\phase-10\scripts\deploy.ps1
```

Optional Docker image check:

```powershell
.\phase-10\scripts\deploy.ps1 -Docker
```

If `make` is available:

```bash
make deploy
```

## Required secrets

- Render: `GROQ_API_KEY`
- Vercel: `NEXT_PUBLIC_API_URL`

Never commit `.env`.

## Verification

1. Render API:
   ```bash
   curl https://YOUR-RENDER-URL/healthz
   curl https://YOUR-RENDER-URL/api/v1/bootstrap
   ```
2. Vercel UI:
   - Open the Vercel URL.
   - Ask a sample question.
   - Confirm the answer includes a Groww source.
3. Scheduler:
   - GitHub Actions -> `Corpus refresh` -> Run workflow (both test boxes **off**).
   - Confirm green run, commit `chore(corpus): automated refresh YYYY-MM-DD` on `main`, and Render redeploy.
   - Ask a new chat question; footer `Last updated from sources` should match the refresh date.

