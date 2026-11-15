"""Download NASA PSI combustion-science data for Etna.

Uses the public (undocumented) PSI web API that backs psi.nasa.gov/physci/repo.
No login needed. Standard library only.

What it downloads by default (small, well under 1 GB):
  data/psi/investigations.csv          one summary row per combustion investigation
  data/psi/inventory.csv               every file PSI lists (incl. raw video/images), NOT downloaded
  data/psi/<PSI-n>/investigation.json  full record: description, objective, publications, file lists
  data/psi/<PSI-n>/tables/*.csv        experiment tables (one row per test)
  data/psi/<PSI-n>/docs/*              PDFs/Office/CSV files from Science Documents, Reports,
                                       Reference Data, Presentations (size-capped; no video/zip)

Raw files (videos, image zips, telemetry) are skipped; fetch specific ones with --get.

Usage:
  python scripts/psi_download.py                     # default download
  python scripts/psi_download.py --dry-run           # show what would be downloaded
  python scripts/psi_download.py --only PSI-25,PSI-69
  python scripts/psi_download.py --no-docs           # metadata + tables only
  python scripts/psi_download.py --max-mb 20         # cap per document (default 50)
  python scripts/psi_download.py --get PSI-25 "PSI-25_Raw Data_BASS_GMT50_SAMPLE_147_TEST_B1.mp4"
  python scripts/psi_download.py --analyzed          # only the "Analyzed Data" files, into <acc>/analyzed/
                                                     # (leaves investigation.json and the CSV summaries untouched)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://psi.nasa.gov/geode-py/ws"
SEARCH_URL = API + "/repo/search?source=psi&type=investigation&size={size}&from={offset}"
DETAIL_URL = API + "/repo/investigations/{acc}"
DOWNLOAD_URL = API + "/studies/{acc}/download?file={file}"
REPO_PAGE = "https://psi.nasa.gov/physci/repo/data/investigations/{acc}"

RESEARCH_AREA = "Combustion Science"
DOC_CATEGORIES = {"Science Documents", "Reports", "Reference Data", "Presentations"}
DOC_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".csv", ".txt"}
HEADERS = {"User-Agent": "flamescope-psi-downloader/0.1 (NASA Space Apps 2026)"}

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "psi"


# ---------------------------------------------------------------- HTTP helpers

def _open(url: str, accept: str | None = None, timeout: int = 120):
    headers = dict(HEADERS)
    if accept:
        headers["Accept"] = accept
    last: Exception | None = None
    for attempt in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404):
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        time.sleep(2 ** attempt)
    raise RuntimeError(f"failed after retries: {url}: {last}")


def get_json(url: str) -> dict:
    with _open(url, accept="application/json") as r:
        return json.load(r)


def download(acc: str, file_name: str, dest: Path, expected_size: float | None) -> str:
    """Download one file. Returns 'ok', 'skip' (already complete) or raises."""
    if dest.exists() and expected_size and dest.stat().st_size == int(expected_size):
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = DOWNLOAD_URL.format(acc=acc, file=urllib.parse.quote(file_name))
    part = dest.with_name(dest.name + ".part")
    with _open(url, timeout=600) as r, open(part, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    part.replace(dest)
    return "ok"


# ---------------------------------------------------------------- PSI parsing

def list_combustion() -> list[dict]:
    hits, offset = [], 0
    while True:
        page = get_json(SEARCH_URL.format(size=200, offset=offset))["hits"]
        batch = page["hits"]
        hits.extend(h["_source"] for h in batch)
        offset += len(batch)
        if not batch or offset >= page["total"]:
            break
    combustion = [h for h in hits if h.get("Research Area") == RESEARCH_AREA]
    return sorted(combustion, key=lambda h: int(h["Accession"].split("-")[1]))


def category(acc: str, f: dict) -> str:
    """PSI files live under /psi-data/<acc>/<category>/...; fall back to the file-name token."""
    parts = (f.get("remote_path") or "").split("/")
    if acc in parts:
        i = parts.index(acc)
        if i + 1 < len(parts) - 1:
            return parts[i + 1]
    name = f.get("file_name", "")
    prefix = acc + "_"
    if name.startswith(prefix):
        return name[len(prefix):].split("_", 1)[0]
    return "?"


def subfolder(acc: str, f: dict) -> str:
    """Folder path below the category (e.g. 'Reduced Gravity/ Bhattacharjee/B1')."""
    parts = (f.get("remote_path") or "").split("/")
    if acc in parts:
        return "/".join(parts[parts.index(acc) + 2:-1])
    return ""


def safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()


def mb(n: float) -> str:
    return f"{n / 1e6:,.1f} MB"


# ---------------------------------------------------------------- main steps

def fetch_records(investigations: list[dict], dry_run: bool) -> dict[str, dict]:
    records = {}
    for inv in investigations:
        acc = inv["Accession"]
        rec = get_json(DETAIL_URL.format(acc=acc))
        records[acc] = rec
        if not dry_run:
            d = OUT / acc
            d.mkdir(parents=True, exist_ok=True)
            (d / "investigation.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {acc:8} {inv.get('Acronym') or '-':22} {len(rec.get('added') or []):5} files, "
              f"{len(rec.get('experimentalTable') or [])} tables")
        time.sleep(0.3)
    return records


def write_summaries(investigations: list[dict], records: dict[str, dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "investigations.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["accession", "acronym", "title", "project_type", "start", "end", "doi",
                    "n_files", "total_size_mb", "n_tables", "n_publications", "psi_page"])
        for inv in investigations:
            acc = inv["Accession"]
            rec = records[acc]
            w.writerow([acc, inv.get("Acronym", ""), rec.get("title", ""), rec.get("projectType", ""),
                        rec.get("investigationStartDate", ""), rec.get("investigationEndDate", ""),
                        rec.get("doi", ""), len(rec.get("added") or []),
                        round((rec.get("totalFileSize") or 0) / 1e6, 1),
                        len(rec.get("experimentalTable") or []), len(rec.get("publications") or []),
                        REPO_PAGE.format(acc=acc)])

    with open(OUT / "inventory.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["accession", "list", "category", "subfolder", "extension", "size_mb",
                    "restricted", "file_name"])
        for acc, rec in records.items():
            for lst in ("experimentalTable", "added"):
                for f in rec.get(lst) or []:
                    name = f.get("file_name", "")
                    w.writerow([acc, lst, "Experimental table" if lst == "experimentalTable" else category(acc, f),
                                subfolder(acc, f), Path(name).suffix.lower(),
                                round((f.get("file_size") or 0) / 1e6, 3), f.get("restricted", ""), name])


def plan_downloads(records: dict[str, dict], docs: bool, max_mb: float) -> tuple[list, list]:
    """Return (to_download, skipped_docs). Each item: (acc, file_name, dest, size)."""
    todo, skipped = [], []
    for acc, rec in records.items():
        seen = set()
        for f in rec.get("experimentalTable") or []:
            name = f["file_name"]
            if f.get("restricted") or name in seen:
                continue
            seen.add(name)
            todo.append((acc, name, OUT / acc / "tables" / safe_name(name), f.get("file_size")))
        if not docs:
            continue
        for f in rec.get("added") or []:
            name = f["file_name"]
            if (f.get("restricted") or name in seen or category(acc, f) not in DOC_CATEGORIES
                    or Path(name).suffix.lower() not in DOC_EXTENSIONS):
                continue
            seen.add(name)
            size = f.get("file_size") or 0
            item = (acc, name, OUT / acc / "docs" / safe_name(name), size)
            (todo if size <= max_mb * 1e6 else skipped).append(item)
    return todo, skipped


def plan_analyzed(records: dict[str, dict], max_mb: float) -> tuple[list, list]:
    """Only the 'Analyzed Data' files (per-test spreadsheets, summary PDFs). Same item shape as plan_downloads."""
    todo, skipped = [], []
    for acc, rec in records.items():
        seen = set()
        for f in rec.get("added") or []:
            name = f["file_name"]
            if f.get("restricted") or name in seen or category(acc, f) != "Analyzed Data":
                continue
            seen.add(name)
            size = f.get("file_size") or 0
            item = (acc, name, OUT / acc / "analyzed" / safe_name(name), size)
            (todo if size <= max_mb * 1e6 else skipped).append(item)
    return todo, skipped


def run_downloads(items: list) -> int:
    failures = 0
    for i, (acc, name, dest, size) in enumerate(items, 1):
        try:
            status = download(acc, name, dest, size)
            print(f"  [{i}/{len(items)}] {status:4} {acc} {name} ({mb(size or 0)})")
            if status == "ok":
                time.sleep(0.3)
        except Exception as e:  # keep going; report at the end
            failures += 1
            print(f"  [{i}/{len(items)}] FAIL {acc} {name}: {e}", file=sys.stderr)
    return failures


def get_specific(acc: str, names: list[str]) -> int:
    rec = get_json(DETAIL_URL.format(acc=acc))
    files = {f["file_name"]: f for lst in ("added", "experimentalTable") for f in rec.get(lst) or []}
    items = []
    for name in names:
        f = files.get(name)
        if f is None:
            print(f"  not in {acc}'s file list: {name}  (see data/psi/inventory.csv)", file=sys.stderr)
            continue
        items.append((acc, name, OUT / acc / "raw" / safe_name(name), f.get("file_size")))
    return run_downloads(items)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--only", help="comma-separated accessions, e.g. PSI-25,PSI-69")
    p.add_argument("--no-docs", action="store_true", help="skip documents; metadata + tables only")
    p.add_argument("--max-mb", type=float, default=50, help="max size per document (default 50)")
    p.add_argument("--dry-run", action="store_true", help="list what would be downloaded, write nothing")
    p.add_argument("--get", nargs="+", metavar=("ACCESSION", "FILE"),
                   help="download specific files of one investigation into <acc>/raw/")
    p.add_argument("--analyzed", action="store_true",
                   help="download only 'Analyzed Data' files into <acc>/analyzed/")
    a = p.parse_args()

    if a.get:
        if len(a.get) < 2:
            p.error("--get needs an accession and at least one file name")
        return 1 if get_specific(a.get[0], a.get[1:]) else 0

    print("Listing PSI combustion investigations...")
    investigations = list_combustion()
    if a.only:
        wanted = {s.strip().upper() for s in a.only.split(",")}
        investigations = [i for i in investigations if i["Accession"].upper() in wanted]
    print(f"Found {len(investigations)}. Fetching records...")
    # --analyzed must not rewrite the existing investigation.json / CSV summaries
    records = fetch_records(investigations, a.dry_run or a.analyzed)

    if a.analyzed:
        todo, skipped = plan_analyzed(records, max_mb=a.max_mb)
    else:
        todo, skipped = plan_downloads(records, docs=not a.no_docs, max_mb=a.max_mb)
    total = sum(s or 0 for *_, s in todo)
    print(f"\nPlan: {len(todo)} files, {mb(total)}"
          + (f"; {len(skipped)} documents over {a.max_mb:g} MB skipped" if skipped else ""))
    for acc, name, _, size in skipped:
        print(f"  skipped (too big): {acc} {name} ({mb(size)})")

    if a.dry_run:
        for acc, name, _, size in todo:
            print(f"  would get: {acc} {name} ({mb(size or 0)})")
        return 0

    if not a.analyzed:
        write_summaries(investigations, records)
    failures = run_downloads(todo)
    print(f"\nDone. Output in {OUT}. {failures} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
