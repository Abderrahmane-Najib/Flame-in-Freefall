"""Settings, read from the environment. Locally they come from app/.env; on Cloud Run from its env vars."""

import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parents[1]
load_dotenv(APP_DIR / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
# Web origins allowed to call the API from a browser, comma-separated (e.g. the UI's URL). "*" = any (demo).
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")  # chat model of the assistant
