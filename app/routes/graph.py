from fastapi import APIRouter

from services.graph import graph

router = APIRouter(tags=["graph"])


@router.get("/graph")
def knowledge_graph() -> dict:
    """Knowledge graph: investigations linked to fuel families, materials, safety jobs, hardware and the
    habitats whose air they were tested in. Investigation nodes carry their findings (cite + url)."""
    return graph()
