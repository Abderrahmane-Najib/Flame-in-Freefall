from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from schemas.chat import ChatRequest
from schemas.investigations import InvestigationSummary
from services.assistant import make_card_agent
from services.chat import chat_events
from services.investigations import all_findings, get_card, list_investigations

router = APIRouter(tags=["investigations"])

FuelType = Literal["solid", "droplet", "gas", "smoke", "ground"]
SafetyJob = Literal["prevention", "detection", "suppression"]


@router.get("/investigations", response_model=list[InvestigationSummary])
def investigations(
    fuel_type: FuelType | None = Query(None, description="Only this fuel family"),
    safety_job: SafetyJob | None = Query(None, description="Only investigations that inform this job"),
) -> list[dict]:
    """The 24 investigations, short form (for the list / grid of cards)."""
    return list_investigations(fuel_type, safety_job)


@router.get("/investigations/findings")
def findings() -> list[dict]:
    """Every finding on the NASA cards, word for word, each with its cite line and document page link
    (for the "Did you know?" panel). Declared before /investigations/{psi_id} so 'findings' is not read as an id."""
    return all_findings()


@router.post("/investigations/{psi_id}/chat")
def investigation_chat(psi_id: str, req: ChatRequest) -> StreamingResponse:
    """Chat about this card only: the assistant's tools are locked to this investigation's card, reports and
    test rows. Same NDJSON events as /chat."""
    card = get_card(psi_id)
    if not card:
        raise HTTPException(404, f"unknown investigation {psi_id}")
    return StreamingResponse(chat_events(make_card_agent(psi_id, card["name"], req.persona), req.message, req.session_id),
                             media_type="application/x-ndjson")


@router.get("/investigations/{psi_id}")
def investigation(psi_id: str) -> dict:
    """One full card: summary, findings and limitations (each with cite + url), tests, conditions,
    habitat_match, publications, images, links. Same content as data/psi/cards.json."""
    card = get_card(psi_id)
    if not card:
        raise HTTPException(404, f"unknown investigation {psi_id}")
    return card
