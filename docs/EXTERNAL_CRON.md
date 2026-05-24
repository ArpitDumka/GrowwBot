# External cron — reliable daily corpus refresh (8:30 AM IST)

GitHub's built-in `schedule` trigger is **best-effort** and often skips 8:30 AM IST on this repo.  
**Primary scheduler:** [cron-job.org](https://cron-job.org) (free) calls the GitHub API to start `corpus-refresh.yml` via `workflow_dispatch`.

The workflow no longer uses `on.schedule` — only **manual** or **external cron** starts a refresh.

---

## 1. Create a GitHub PAT (one time)

1. GitHub → **Settings** → **Developer settings** → **Fine-grained personal access tokens** → **Generate new token**
2. **Repository access:** Only select repositories → **GrowwBot**
3. **Permissions:**
   - **Actions:** Read and write
   - **Contents:** Read-only (optional; dispatch only needs Actions)
4. Generate and copy the token (`github_pat_...` or `ghp_...`). Store it in cron-job.org only — **never commit it**.

---

## 2. Configure cron-job.org (one time)

1. Sign up at [https://console.cron-job.org](https://console.cron-job.org)
2. **Cronjobs** → **Create cronjob**

| Field | Value |
|-------|--------|
| **Title** | GrowwBot corpus refresh |
| **URL** | `https://api.github.com/repos/ArpitDumka/GrowwBot/actions/workflows/corpus-refresh.yml/dispatches` |
| **Schedule** | Daily **08:30** — timezone **Asia/Kolkata** (or `30 8 * * *`) |
| **Request method** | **POST** |
| **Request timeout** | 30 seconds |

3. **Headers** (add each):

| Header | Value |
|--------|--------|
| `Accept` | `application/vnd.github+json` |
| `Authorization` | `Bearer YOUR_GITHUB_PAT` |
| `X-GitHub-Api-Version` | `2022-11-28` |
| `Content-Type` | `application/json` |

4. **Request body** (raw JSON):

```json
{"ref":"main"}
```

5. Save and **Enable** the cronjob.

6. **Test now:** use cron-job.org **“Run now”** (or run `.\scripts\trigger_corpus_refresh.ps1` locally with `GITHUB_PAT` set).

---

## 3. Verify it worked

1. Open [Actions → Corpus refresh](https://github.com/ArpitDumka/GrowwBot/actions/workflows/corpus-refresh.yml)
2. New run should show **Event: workflow_dispatch** and actor = your user (external API call)
3. After ~20–35 min, `main` should have `chore(corpus): automated refresh YYYY-MM-DD`
4. Render auto-deploys if enabled on `main`

---

## 4. Local / manual trigger (same API as cron-job.org)

```powershell
$env:GITHUB_PAT = "github_pat_..."   # your token
.\scripts\trigger_corpus_refresh.ps1
```

Optional flags: `-SkipIndex`, `-SkipPush`, `-TestEmbedder`

---

## 5. curl equivalent (for other schedulers)

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_PAT" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/ArpitDumka/GrowwBot/actions/workflows/corpus-refresh.yml/dispatches \
  -d '{"ref":"main"}'
```

Alternatives to cron-job.org: [EasyCron](https://www.easycron.com), GitHub Actions (unreliable `schedule`), or a small Cloudflare Worker cron.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `401 Bad credentials` | PAT expired or wrong token |
| `403 Resource not accessible` | PAT needs **Actions: Read and write** on GrowwBot |
| `404 Not Found` | Wrong repo name or workflow filename |
| Run queued but no corpus commit | Open run logs; check push step / workflow permissions on repo |
