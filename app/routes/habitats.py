from fastapi import APIRouter, HTTPException

from services.habitats import list_habitats, rank

router = APIRouter(tags=["habitats"])


@router.get("/habitats")
def habitats() -> list[dict]:
    """The habitats (ISS, Moon base & rover, Mars base) with their air, sources and assumptions."""
    return list_habitats()


@router.get("/habitats/{habitat_id}/ranking")
def habitat_ranking(habitat_id: str) -> dict:
    """Investigations ordered by tests measured in this habitat's air. A plain count, no weights;
    the from_note / o2_only / mixed groups are listed but do not set the order."""
    result = rank(habitat_id)
    if not result:
        raise HTTPException(404, f"unknown habitat {habitat_id}")
    return result
