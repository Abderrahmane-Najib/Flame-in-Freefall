"""User-uploaded reports: PDF -> pages -> chunks -> embeddings, then a drafted card the user approves or rejects.

Life of an upload (documents.status):
  processing  pages and chunks stored, embedding running in the background
  unreviewed  searchable in its own chat; a card can be drafted (services/card_writer.py)
  approved    the user approved the card: it is a new investigation ('UP-<id>') and joins the main search
  rejected    kept out of everything
  failed      embedding failed (the error is not stored: see the server log)
"""

import hashlib
import io

from psycopg.types.json import Jsonb
from pypdf import PdfReader

from database.connection import connect
from services.embeddings import embed, to_pgvector
from services.indexing import EMBED_BATCH, MIN_PAGE_CHARS, clean_text, embed_text, split_words

MAX_BYTES = 20 * 1024 * 1024
MAX_PAGES = 300

UPLOAD_SQL = """
select id, file, sha1, status, origin, psi_id, n_pages, created_at, card,
       (select count(*) from chunks c join pages p on p.id = c.page_id where p.document_id = d.id) as chunks,
       (select count(*) from chunks c join pages p on p.id = c.page_id
        where p.document_id = d.id and c.embedding is not null) as chunks_embedded
from documents d
"""


class UploadError(ValueError):
    """A bad file: the message is safe to show to the user."""


def ingest(filename: str, data: bytes) -> dict:
    """Store a PDF's pages and chunks (fast). Returns the upload; embedding is a separate step (embed_document)."""
    if len(data) > MAX_BYTES:
        raise UploadError(f"file too large (max {MAX_BYTES // 1024 // 1024} MB)")
    if not data.startswith(b"%PDF"):
        raise UploadError("not a PDF file")
    sha1 = hashlib.sha1(data).hexdigest()
    with connect() as conn:
        if row := conn.execute("select id, origin, file, psi_id from documents where sha1 = %s", (sha1,)).fetchone():
            if row["origin"] != "upload":   # the same file is one of the NASA reports: not an upload
                raise UploadError(f"this PDF is already in the NASA library ({row['psi_id']}: {row['file']}), "
                                  "so it is already searchable")
            return {**get_upload(row["id"]), "already_uploaded": True}
    try:
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > MAX_PAGES:
            raise UploadError(f"too many pages (max {MAX_PAGES})")
        pages = [clean_text(p.extract_text() or "") for p in reader.pages]
    except UploadError:
        raise
    except Exception as e:
        raise UploadError(f"could not read the PDF ({type(e).__name__})") from e
    kept = [(i, t) for i, t in enumerate(pages, 1) if len(t) >= MIN_PAGE_CHARS]
    if not kept:
        raise UploadError("no text found: the PDF may be scanned images (OCR is not supported)")

    with connect() as conn:
        doc_id = conn.execute(
            """insert into documents (origin, file, sha1, status, n_pages)
               values ('upload', %s, %s, 'processing', %s) returning id""",
            (filename, sha1, len(pages))).fetchone()["id"]
        for page, text in kept:
            page_id = conn.execute("insert into pages (document_id, page, text) values (%s, %s, %s) returning id",
                                   (doc_id, page, text)).fetchone()["id"]
            with conn.cursor() as cur:
                cur.executemany("insert into chunks (page_id, chunk_index, text) values (%s, %s, %s)",
                                [(page_id, i, t) for i, t in enumerate(split_words(text))])
    return {**get_upload(doc_id), "already_uploaded": False}


def embed_document(doc_id: int) -> None:
    """Embed the document's chunks, then mark it 'unreviewed'. Runs in the background after the upload."""
    try:
        with connect() as conn:
            todo = conn.execute(
                """select c.id, c.text, d.file, p.page from chunks c
                   join pages p on p.id = c.page_id join documents d on d.id = p.document_id
                   where d.id = %s and c.embedding is null order by c.id""", (doc_id,)).fetchall()
        for i in range(0, len(todo), EMBED_BATCH):
            batch = todo[i:i + EMBED_BATCH]
            vectors = embed([embed_text(c["file"], c["page"], c["text"]) for c in batch])
            with connect() as conn, conn.cursor() as cur:  # short connection per batch (Neon drops idle ones)
                cur.executemany("update chunks set embedding = %s::vector where id = %s",
                                [(to_pgvector(v), c["id"]) for c, v in zip(batch, vectors)])
        status = "unreviewed"
    except Exception as e:
        print(f"embedding upload {doc_id} failed: {type(e).__name__}: {e}")
        status = "failed"
    with connect() as conn:
        conn.execute("update documents set status = %s where id = %s and status = 'processing'", (status, doc_id))


def get_upload(doc_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(UPLOAD_SQL + " where d.id = %s", (doc_id,)).fetchone()


def list_uploads() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(UPLOAD_SQL + " where d.origin = 'upload' order by d.id desc").fetchall()
    for r in rows:
        r["has_card"] = r.pop("card") is not None  # the list stays short; the card is in GET /uploads/{id}
    return rows


def page_text(doc_id: int, page: int) -> dict | None:
    """One page of an upload: the target of the upload citations ('/uploads/<id>/pages/<n>')."""
    with connect() as conn:
        return conn.execute(
            """select d.id as document_id, d.file, p.page, p.text from pages p join documents d on d.id = p.document_id
               where d.id = %s and d.origin = 'upload' and p.page = %s""", (doc_id, page)).fetchone()


def save_draft(doc_id: int, card: dict) -> None:
    with connect() as conn:
        conn.execute("update documents set card = %s where id = %s", (Jsonb(card), doc_id))


def approve(doc_id: int, card: dict) -> dict:
    """The user approved the card: it becomes investigation 'UP-<id>', and the report joins the main search."""
    card = {**card, "id": f"UP-{doc_id}", "origin": "upload",
            "review": {**(card.get("review") or {}), "status": "approved by the user"}}
    with connect() as conn:
        conn.execute(
            """insert into investigations (id, name, title, in_space, fuel_type, hardware_group, safety_jobs, card)
               values (%s, %s, %s, %s, %s, %s, %s, %s)
               on conflict (id) do update set name = excluded.name, title = excluded.title,
                   in_space = excluded.in_space, fuel_type = excluded.fuel_type,
                   safety_jobs = excluded.safety_jobs, card = excluded.card""",
            (card["id"], card["name"], card.get("title"), card.get("in_space"), card.get("fuel_type"),
             card.get("hardware_group"), (card.get("fire_safety") or {}).get("jobs") or [], Jsonb(card)))
        conn.execute("update documents set status = 'approved', psi_id = %s, card = %s where id = %s",
                     (card["id"], Jsonb(card), doc_id))
    return card


def reject(doc_id: int) -> None:
    """Rejected: out of every search. An approved card is removed again (its report is unlinked first)."""
    with connect() as conn:
        row = conn.execute("select psi_id from documents where id = %s", (doc_id,)).fetchone()
        conn.execute("update documents set status = 'rejected', psi_id = null where id = %s", (doc_id,))
        if row and row["psi_id"] and row["psi_id"].startswith("UP-"):
            conn.execute("delete from investigations where id = %s", (row["psi_id"],))
