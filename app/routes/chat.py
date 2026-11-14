from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.chat import ChatRequest
from services.chat import chat_events

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    """Ask the assistant. The answer streams as NDJSON events (session, tool, text, error, done):
    see services/chat.py."""
    return StreamingResponse(chat_events(req.message, req.session_id, req.persona),
                             media_type="application/x-ndjson")
