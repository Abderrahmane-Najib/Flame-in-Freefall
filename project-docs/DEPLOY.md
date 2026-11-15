# Deploying Etna (Google Cloud Run + Firebase Hosting)

One container serves everything: the web UI (`web/`, built inside the image) and the API (`app/`). The data lives in Neon, so **a deploy only ships code**.

| What | Value |
|---|---|
| Google Cloud project | `ghostflame` (paid by the $300 / 90-day Space Apps free-trial credit) |
| Service | `ghostflame`, region `europe-west3` (Frankfurt, next to Neon) |
| Size | 4 GiB RAM, 2 vCPU, 0–3 instances |
| Secrets | `database-url`, `groq-api-key` in Secret Manager (never in the image or in git) |
| Public URL | **https://etna.web.app** (Firebase Hosting, forwards to the Cloud Run service) |
| Cloud Run URL | https://ghostflame-ryhaqcvtmq-ey.a.run.app (the same app; also printed at the end of every deploy) |
| Names | The app is called **Etna**. The Google Cloud project, the service and the images keep the technical name `ghostflame` (a project ID cannot be renamed; nobody sees it) |
| Deploy time | a few minutes (the slow part lives in the base image, see below) |

### Two images

| Image | File | Contains | Rebuilt when |
|---|---|---|---|
| `ghostflame-base` | `Dockerfile.base` (+ `cloudbuild-base.yaml`) | Python, CPU torch, `app/requirements.txt`, the BGE-M3 model (~3 GB) | **Rarely**: only after `app/requirements.txt` changes |
| the app | `Dockerfile` | starts `FROM ghostflame-base`, builds `web/`, copies `app/` | Every deploy |

Both live in Artifact Registry: `europe-west3-docker.pkg.dev/ghostflame/cloud-run-source-deploy/`.

---

## Deploy after a change (the usual case)

From the **repo root**, in PowerShell or a terminal:

```
gcloud run deploy ghostflame --source . --region europe-west3 --project ghostflame --quiet
```

- It uploads the code (only what `.gcloudignore` allows: `Dockerfile`, `app/`, `web/`), builds the image in Google's cloud, then switches traffic to the new version.
- Takes a few minutes. Settings from the first deploy (memory, CPU, secrets, public access) are kept, so this short command is enough.
- Nothing to build locally first: the `Dockerfile` runs `npm run build` itself.
- If the build fails, the old version keeps running. Nothing breaks.

Then check:
1. Open the Service URL: the home page loads.
2. `<URL>/health` → `"status":"ok"` and `chunks_embedded` equal to `chunks`.
3. Ask the chat one question.

## After changing `app/requirements.txt`: rebuild the base

Added, removed or changed a Python package? Rebuild the base first (~6–8 min), then deploy as usual:

```
gcloud builds submit --config cloudbuild-base.yaml --region europe-west3 --project ghostflame
gcloud run deploy ghostflame --source . --region europe-west3 --project ghostflame --quiet
```

If you forget, the deploy still works: the app `Dockerfile` re-runs `pip install -r requirements.txt` on top of the base and installs whatever is missing. It is just slower, and a torch or model change is never picked up without the base rebuild.

## Optional: test locally before deploying

Needs Docker Desktop running. Once per PC, let Docker pull the base image from our registry:

```
gcloud auth configure-docker europe-west3-docker.pkg.dev
```

Then:

```
docker build -t ghostflame .
docker run --rm -p 8080:8080 --env-file app/.env ghostflame
```

Open http://localhost:8080. Stop with `Ctrl+C`. The first build downloads the 3 GB base image once; later builds take about a minute.

## Common tasks

**Change a secret** (new Groq key, new database password):
```
gcloud secrets versions add groq-api-key --data-file=- --project ghostflame
```
Paste the value, then press `Ctrl+Z` and `Enter` (Windows) or `Ctrl+D` (Mac/Linux). Same for `database-url`. Then redeploy (command above) so the service picks up the new version.

**Always on for judging** (no ~30 s wait on the first visit; costs a few dollars a day from the credit):
```
gcloud run services update ghostflame --min-instances 1 --region europe-west3 --project ghostflame
```
**Back to scale-to-zero** afterwards (≈ free when nobody uses it):
```
gcloud run services update ghostflame --min-instances 0 --region europe-west3 --project ghostflame
```

**See errors / logs:**
```
gcloud run services logs read ghostflame --region europe-west3 --project ghostflame --limit 50
```
or in the console: Cloud Run → `ghostflame` → **Logs**.

**Roll back** to the previous version: console → Cloud Run → `ghostflame` → **Revisions** → pick the last good one → **Manage traffic** → 100 %.

**Where the money goes:** console → **Billing** → Reports. A budget alert is under **Billing → Budgets & alerts**.

## Setup on another PC (once)

1. Install the Google Cloud CLI: https://cloud.google.com/sdk/docs/install
2. `gcloud auth login` (with an account that has access to the `ghostflame` project; the owner adds teammates in **IAM & Admin → IAM → Grant access**, role *Cloud Run Developer* + *Cloud Build Editor*, or *Editor* for simplicity).
3. `gcloud config set project ghostflame`
4. Optional, so builds never time out: `gcloud config set builds/timeout 3600`

## Rules

- **Never commit `.env` or `app/.env`.** Keys go in Secret Manager only.
- The database is not touched by a deploy. Data changes are still pushed with `python app/scripts/push_data.py` (see `HANDOFF.md`).
- Changing memory, CPU, secrets or access needs the full command, which is how the service was first created:
  ```
  gcloud run deploy ghostflame --source . --region europe-west3 --memory 4Gi --cpu 2 --min-instances 0 --max-instances 3 --timeout 300 --allow-unauthenticated --set-secrets DATABASE_URL=database-url:latest,GROQ_API_KEY=groq-api-key:latest --project ghostflame --quiet
  ```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Deploy fails at `FROM …ghostflame-base` ("not found") | The base image is missing: run the base rebuild command above |
| Local `docker build` says "unauthorized" for the base | Run `gcloud auth configure-docker europe-west3-docker.pkg.dev` once |
| Build "timed out" | `gcloud config set builds/timeout 3600`, then deploy again |
| Page loads but chat fails | Groq key wrong or rate-limited: check logs; update `groq-api-key` |
| `/health` error | Neon connection string wrong or Neon down: check `database-url`; Neon console |
| First visit very slow | Normal after idle (scale to zero): the model loads in ~30 s. Use "always on" for demos |
| "Memory limit exceeded" in logs | Raise to `--memory 8Gi` with the full command |
| `PERMISSION_DENIED` on deploy | Your Google account lacks a role on the project: ask the owner |

## The etna.web.app link (Firebase Hosting)

`etna.web.app` is a Firebase Hosting site in the same Google Cloud project. It holds no files: every path is forwarded to the Cloud Run service (`firebase.json` at the repo root). So **a normal Cloud Run deploy updates etna.web.app too**, nothing else to do.

- The page is served through Firebase, but the app's API calls go **straight to the Cloud Run URL** (`web/src/lib/api.js`): Firebase buffers streamed chat answers (the user would see nothing until the end) and cuts requests off after 60 s. CORS is open (`CORS_ORIGINS=*`), so this works from any address. If the Cloud Run URL ever changes, update `CLOUD_RUN` in `api.js`.
- Only if `firebase.json` changes (it should not need to): `npm install -g firebase-tools`, `firebase login`, then `firebase deploy --only hosting` from the repo root.
- Console: https://console.firebase.google.com/project/ghostflame/hosting
