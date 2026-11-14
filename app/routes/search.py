from fastapi import APIRouter, Query

from schemas.search import SearchResponse
from services.search import search

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search_reports(
    q: str = Query(min_length=2, max_length=500, description="The question or keywords"),
    psi_id: str | None = Query(None, description="Only this investigation, e.g. PSI-25"),
    k: int = Query(8, ge=1, le=30, description="Number of passages"),
    include_unreviewed: bool = Query(False, description="Also search uploaded reports not yet reviewed"),
) -> dict:
    """Report passages that best answer q, each with its investigation, file, PDF page and link."""
    return search(q, psi_id, k, include_unreviewed)
