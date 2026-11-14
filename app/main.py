"""FlameScope API: creates the app and plugs in the routes (logic lives in services/)."""

from fastapi import FastAPI

from routes import chat, health, search

app = FastAPI(title="FlameScope API")
app.include_router(health.router)
app.include_router(search.router)
app.include_router(chat.router)
