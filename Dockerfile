# Etna: one image = the web UI (web/dist) + the API (app/), for Cloud Run.
# Starts FROM the base image (Python + torch + BGE-M3, see Dockerfile.base), so a deploy only
# builds the UI and copies the code: a few minutes instead of re-downloading ~3 GB.
# Deploy: see project-docs/DEPLOY.md.

ARG BASE=europe-west3-docker.pkg.dev/ghostflame/cloud-run-source-deploy/ghostflame-base:latest

# --- 1. Web UI (React + Vite) -> /web/dist ---
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- 2. API, on top of the base image ---
FROM ${BASE}
WORKDIR /srv/app

# Safety net: if requirements.txt gained a package since the base was built, install it here
# (seconds when nothing changed). Rebuild the base when this starts taking long.
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# main.py serves ../web/dist, i.e. /srv/web/dist.
COPY app/ ./
COPY --from=web /web/dist /srv/web/dist

# Trained predictors P1-P8 (app/services/predictors.py loads them from /srv/models and /srv/scripts).
COPY models/ /srv/models/
COPY scripts/predict.py /srv/scripts/predict.py

# Cloud Run sets PORT; 8080 elsewhere.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
