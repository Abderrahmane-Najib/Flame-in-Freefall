"""FlameScope API: creates the app and plugs in the routes (logic lives in services/)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import CORS_ORIGINS
from routes import chat, coverage, graph, habitats, health, investigations, predict, search, tests, uploads

app = FastAPI(title="FlameScope API")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"])

app.include_router(health.router)
app.include_router(investigations.router)
app.include_router(habitats.router)
app.include_router(tests.router)
app.include_router(coverage.router)
app.include_router(predict.router)
app.include_router(graph.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(uploads.router)

# The web UI (React, built with `npm run build` into ../web/dist), served last so the API routes above win.
# In development run `npm run dev` in web/ instead (hot reload, proxies the API).
WEB_DIR = Path(__file__).resolve().parents[1] / "web" / "dist"
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
