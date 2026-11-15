"""Uploaded reports: upload -> (background embedding) -> own chat -> drafted card -> approve / reject.

The UI flow:
  POST /uploads                      send the PDF; status 'processing'
  GET  /uploads/{id}                 poll until status 'unreviewed' (embedded); 'failed' = try again
  POST /uploads/{id}/chat            chat about this report only (NDJSON, same events as /chat)
  POST /uploads/{id}/card            the card agent drafts a card (saved on the upload)
  POST /uploads/{id}/approve         the card becomes investigation 'UP-<id>' (in /investigations, main chat, graph)
  POST /uploads/{id}/reject          out of every search
  DELETE /uploads/{id}               delete it for good (pages, passages and its card)
"""

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from schemas.uploads import ApproveRequest, UploadChatRequest
from services import uploads
from services.assistant import make_report_agent
from services.card_writer import draft_card
from services.chat import chat_events

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _upload(doc_id: int, statuses: tuple[str, ...] | None = None) -> dict:
    """The upload, or 404; with statuses: 409 if it is not in one of them."""
    u = uploads.get_upload(doc_id)
    if not u or u["origin"] != "upload":
        raise HTTPException(404, f"unknown upload {doc_id}")
    if statuses and u["status"] not in statuses:
        raise HTTPException(409, f"upload {doc_id} is '{u['status']}', needs: {', '.join(statuses)}")
    return u


@router.post("")
def upload(background: BackgroundTasks, file: UploadFile = File(..., description="A PDF report")) -> dict:
    """Store the PDF's text (pages and chunks), then embed it in the background (status 'processing')."""
    try:
        u = uploads.ingest(file.filename or "upload.pdf", file.file.read())
    except uploads.UploadError as e:
        raise HTTPException(400, str(e)) from e
    if u["status"] == "processing":
        background.add_task(uploads.embed_document, u["id"])
    return u


@router.get("")
def list_uploads() -> list[dict]:
    """All uploads, newest first, with their status and embedding progress."""
    return uploads.list_uploads()


@router.get("/{doc_id}")
def get_upload(doc_id: int) -> dict:
    """One upload: status, embedding progress (chunks_embedded / chunks) and the drafted card, if any."""
    return _upload(doc_id)


@router.get("/{doc_id}/pages/{page}")
def page(doc_id: int, page: int) -> dict:
    """One page's text: where the upload citations point."""
    p = uploads.page_text(doc_id, page)
    if not p:
        raise HTTPException(404, f"no page {page} in upload {doc_id}")
    return p


@router.post("/{doc_id}/chat")
def chat(doc_id: int, req: UploadChatRequest) -> StreamingResponse:
    """Chat about this report only. Same NDJSON events as /chat."""
    u = _upload(doc_id, ("unreviewed", "approved"))
    return StreamingResponse(chat_events(make_report_agent(doc_id, u["file"], req.persona), req.message, req.session_id),
                             media_type="application/x-ndjson")


@router.post("/{doc_id}/card")
def card(doc_id: int) -> dict:
    """The card agent drafts a card from the report (one model call). Saved on the upload; call again to redo."""
    u = _upload(doc_id, ("unreviewed",))
    try:
        draft = draft_card(doc_id, u["file"])
    except ValueError as e:
        raise HTTPException(502, str(e)) from e
    uploads.save_draft(doc_id, draft)
    return draft


@router.post("/{doc_id}/approve")
def approve(doc_id: int, req: ApproveRequest | None = None) -> dict:
    """The user approves the card (as drafted, or as edited in the request): it becomes a new investigation."""
    u = _upload(doc_id, ("unreviewed", "approved"))
    card = (req.card if req else None) or u["card"]
    if not card or not card.get("name"):
        raise HTTPException(409, "no card to approve: draft one first (POST /uploads/{id}/card)")
    return uploads.approve(doc_id, card)


@router.post("/{doc_id}/reject")
def reject(doc_id: int) -> dict:
    """Reject the upload: out of every search; an approved card is removed."""
    _upload(doc_id)
    uploads.reject(doc_id)
    return _upload(doc_id)


@router.delete("/{doc_id}")
def delete(doc_id: int) -> dict:
    """Delete the upload for good: its pages, passages and approved card. It can be uploaded again afterwards."""
    _upload(doc_id)
    uploads.delete(doc_id)
    return {"deleted": doc_id}
