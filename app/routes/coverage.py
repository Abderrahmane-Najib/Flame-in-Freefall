from fastapi import APIRouter

from services.coverage import coverage

router = APIRouter(tags=["coverage"])


@router.get("/coverage")
def coverage_map() -> dict:
    """O2 vs pressure map: one point per test row (chamber O2 and pressure both known), the habitat
    boxes, the near-lunar band, counts, and each point's NASA table + row (link in 'tables')."""
    return coverage()
