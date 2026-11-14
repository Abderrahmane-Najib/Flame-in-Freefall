from fastapi import APIRouter

from schemas.health import HealthResponse
from services.health import database_counts

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    """Proves the app can reach the database, and shows how much data it holds."""
    return {"status": "ok", "database": database_counts()}
