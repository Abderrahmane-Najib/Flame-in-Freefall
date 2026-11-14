"""Push FlameScope data into the database (the one in DATABASE_URL).

Run it from your computer, where the pipeline outputs and the downloaded NASA PDFs are:

  data/psi/cards.json                investigation cards           -> investigations
  content/habitats.json              habitat atmospheres           -> habitats
  data/psi/clean/*.csv               cleaned test rows             -> tests
  data/psi/PSI-*/docs/*.pdf          NASA reports (page text)      -> documents + pages
  (pages in the database)            ~250-word pieces of a page    -> chunks
  (chunks without a vector)          BGE-M3 embeddings (--embed)   -> chunks.embedding

Safe to run again: investigations and habitats are updated in place, tests are replaced as a whole,
a report already in the database (same file content) is skipped, pages already chunked are skipped,
and --embed only embeds chunks that have no vector yet (so an interrupted run just continues).

Usage:
  python app/scripts/push_data.py                 # data, reports and chunks
  python app/scripts/push_data.py --no-reports    # skip the PDFs (fast)
  python app/scripts/push_data.py --embed         # also embed new chunks (local BGE-M3 model)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path

from psycopg.types.json import Jsonb
from pypdf import PdfReader

APP_DIR = Path(__file__).resolve().parents[1]
ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))
from database.connection import connect, create_schema  # noqa: E402
from services.indexing import EMBED_BATCH, MIN_PAGE_CHARS, clean_text, embed_text, split_words  # noqa: E402

CARDS = ROOT / "data" / "psi" / "cards.json"
HABITATS = ROOT / "content" / "habitats.json"
CLEAN_DIR = ROOT / "data" / "psi" / "clean"
PSI_DIR = ROOT / "data" / "psi"
PSI_FILE_URL = "https://psi.nasa.gov/geode-py/ws/studies/{acc}/download?file={file}"
REPORT_KINDS = ("_Reports_", "_Presentations_", "_Science Documents_")  # software documents are skipped

TEST_COLUMNS = {  # column -> type; every other CSV column goes to "extra"
    "investigation": str, "test_id": str, "test_date": str, "row_granularity": str, "n_tests": int,
    "fuel": str, "fuel_type": str, "o2_pct": float, "o2_min_pct": float, "o2_max_pct": float,
    "o2_location": str, "o2_assumed": bool, "pressure_kpa": float, "pressure_min_kpa": float,
    "pressure_max_kpa": float, "pressure_assumed": bool, "flow_cm_s": float, "flow_min_cm_s": float,
    "flow_max_cm_s": float, "n2_pct": float, "co2_pct": float, "he_pct": float, "diluent": str,
    "o2_partial_kpa": float, "lunar_air": bool, "gravity": str, "has_result": bool, "flags": list,
    "source_file": str, "source_row": int,
}


def convert(value: str, kind):
    if value in ("", None):
        return [] if kind is list else None
    if kind is bool:
        return value.strip().lower() == "true"
    if kind is list:
        return [v for v in value.split(";") if v]
    if kind in (int, float):
        try:
            return kind(float(value))
        except ValueError:
            return None
    return value


def push_investigations(conn) -> int:
    cards = json.loads(CARDS.read_text(encoding="utf-8"))["cards"]
    for c in cards:
        conn.execute(
            """insert into investigations (id, name, title, in_space, fuel_type, hardware_group, safety_jobs, card)
               values (%s, %s, %s, %s, %s, %s, %s, %s)
               on conflict (id) do update set name = excluded.name, title = excluded.title,
                   in_space = excluded.in_space, fuel_type = excluded.fuel_type,
                   hardware_group = excluded.hardware_group, safety_jobs = excluded.safety_jobs,
                   card = excluded.card""",
            (c["id"], c["name"], c["title"], c["in_space"], c["fuel_type"], c["hardware_group"],
             c["fire_safety"]["jobs"], Jsonb(c)))
    return len(cards)


def push_habitats(conn) -> int:
    habitats = json.loads(HABITATS.read_text(encoding="utf-8"))["habitats"]
    for h in habitats:
        conn.execute(
            """insert into habitats (id, label, data) values (%s, %s, %s)
               on conflict (id) do update set label = excluded.label, data = excluded.data""",
            (h["id"], h["label"], Jsonb(h)))
    return len(habitats)


def push_tests(conn) -> int:
    cols = list(TEST_COLUMNS)
    rows = []
    for f in sorted(CLEAN_DIR.glob("*.csv")):
        with open(f, encoding="utf-8", newline="") as fh:
            for raw in csv.DictReader(fh):
                extra = {k: v for k, v in raw.items() if k not in TEST_COLUMNS and k != "psi_id" and v != ""}
                rows.append([raw["psi_id"], f.name] + [convert(raw.get(c, ""), TEST_COLUMNS[c]) for c in cols]
                            + [Jsonb(extra)])
    conn.execute("delete from tests")  # replaced as a whole, inside the same transaction
    with conn.cursor() as cur:
        cur.executemany(
            f"insert into tests (psi_id, clean_file, {', '.join(cols)}, extra) "
            f"values ({', '.join(['%s'] * (len(cols) + 3))})", rows)
    return len(rows)


def push_reports(conn) -> tuple[int, int, int]:
    pdfs = sorted(p for p in PSI_DIR.glob("PSI-*/docs/*.pdf") if any(k in p.name for k in REPORT_KINDS))
    added = skipped = n_pages = 0
    for pdf in pdfs:
        acc = pdf.parent.parent.name
        sha1 = hashlib.sha1(pdf.read_bytes()).hexdigest()
        if conn.execute("select 1 from documents where sha1 = %s", (sha1,)).fetchone():
            skipped += 1
            continue
        try:
            pages = [clean_text(p.extract_text() or "") for p in PdfReader(pdf).pages]
        except Exception as e:  # one broken PDF must not stop the others
            print(f"  !! {pdf.name}: {e}", file=sys.stderr)
            continue
        url = PSI_FILE_URL.format(acc=acc, file=urllib.parse.quote(pdf.name))
        doc_id = conn.execute(
            """insert into documents (origin, psi_id, file, url, sha1, status, n_pages)
               values ('psi', %s, %s, %s, %s, 'approved', %s) returning id""",
            (acc, pdf.name, url, sha1, len(pages))).fetchone()["id"]
        kept = [(doc_id, i, t) for i, t in enumerate(pages, 1) if len(t) >= MIN_PAGE_CHARS]
        with conn.cursor() as cur:
            cur.executemany("insert into pages (document_id, page, text) values (%s, %s, %s)", kept)
        conn.commit()  # one report at a time, so an interrupted run keeps what is done
        added += 1
        n_pages += len(kept)
        print(f"  {acc:8} {len(kept):4} pages  {pdf.name}")
    return added, skipped, n_pages


def push_chunks(conn) -> tuple[int, int]:
    """Chunk every page that has no chunks yet (chunks never cross a page, so every hit keeps its page)."""
    pages = conn.execute(
        "select p.id, p.text from pages p where not exists (select 1 from chunks c where c.page_id = p.id)"
    ).fetchall()
    rows = [(p["id"], i, t) for p in pages for i, t in enumerate(split_words(p["text"]))]
    with conn.cursor() as cur:
        cur.executemany("insert into chunks (page_id, chunk_index, text) values (%s, %s, %s)", rows)
    conn.commit()
    return len(pages), len(rows)


def embed_chunks() -> int:
    """Embed chunks that have no vector yet, EMBED_BATCH at a time (local BGE-M3 model)."""
    from services.embeddings import embed, to_pgvector

    with connect() as conn:
        todo = conn.execute(
            """select c.id, c.text, d.file, p.page from chunks c
               join pages p on p.id = c.page_id join documents d on d.id = p.document_id
               where c.embedding is null order by c.id"""
        ).fetchall()
    print(f"chunks to embed: {len(todo)}")
    done = 0
    for i in range(0, len(todo), EMBED_BATCH):
        batch = todo[i:i + EMBED_BATCH]
        texts = [embed_text(c["file"], c["page"], c["text"]) for c in batch]
        vectors = embed(texts)
        # A fresh short connection per batch: Neon drops connections left idle for long.
        with connect() as wconn, wconn.cursor() as cur:
            cur.executemany("update chunks set embedding = %s::vector where id = %s",
                            [(to_pgvector(v), c["id"]) for c, v in zip(batch, vectors)])
        # committed when the with block ends, batch by batch, so an interrupted run keeps what is done
        done += len(batch)
        print(f"  embedded {done}/{len(todo)}")
    return done


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--no-reports", action="store_true", help="skip the report PDFs")
    p.add_argument("--embed", action="store_true", help="embed chunks that have no vector yet (BGE-M3)")
    a = p.parse_args()

    with connect() as conn:
        create_schema(conn)
        conn.commit()
        print(f"investigations: {push_investigations(conn)}")
        print(f"habitats:       {push_habitats(conn)}")
        print(f"test rows:      {push_tests(conn)}")
        conn.commit()
        if not a.no_reports:
            added, skipped, n_pages = push_reports(conn)
            print(f"reports:        {added} added ({n_pages} pages), {skipped} already in the database")
        n_pages, n_chunks = push_chunks(conn)
        print(f"chunks:         {n_chunks} new from {n_pages} pages")
    if a.embed:  # after the data connection is closed: embedding all chunks takes a while
        print(f"embeddings:     {embed_chunks()} chunks embedded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
