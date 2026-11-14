"""Build investigation cards for the app from the downloaded PSI records.

Reads (all local, no network):
  data/psi/PSI-*/investigation.json   identity, text, hardware, dates, DOI, publications, images, tables
  data/psi/clean/*.csv                cleaned test tables (scripts/clean_tables.py) -> "tests" + "conditions"
  content/cards_curated.json          hand-maintained fields: fuel type, safety jobs, hardware group,
                                      summary, findings, limitations (never overwritten by this script)

Writes:
  data/psi/cards.json                 one card per investigation, sorted by PSI number

"tests" and "conditions" are computed from the cleaned tables: test counts (sum of n_tests), results,
lunar-air tests, fuels, and O2 / pressure / flow ranges. O2 is reported separately for chamber air and
for burner streams (inverse flames), and values that come from a document rather than the table are
marked "assumed". Investigations with no test table get {"available": false}.

Documents are not listed one by one: each card links to its PSI repository page, where all
reports and files are. Contacts are left out on purpose (personal details).

Run scripts/clean_tables.py first.

Usage:
  python scripts/build_cards.py
  python scripts/build_cards.py --out path/to/cards.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from psi_download import DOWNLOAD_URL, OUT as PSI_DIR, REPO_PAGE, ROOT, safe_name

CURATED = ROOT / "content" / "cards_curated.json"
HABITATS = ROOT / "content" / "habitats.json"
CLEAN_DIR = PSI_DIR / "clean"
DEFAULT_OUT = PSI_DIR / "cards.json"

HARDWARE_GROUPS = {"CIR + ACME", "CIR + MDCA", "MSG", "Cygnus", "ground"}
FUEL_TYPES = {"solid", "droplet", "gas", "smoke", "ground"}
SAFETY_JOBS = {"prevention", "detection", "suppression"}


# ---------------------------------------------------------------- small helpers

def text(v) -> str | None:
    """Trimmed string, or None when empty. Normalises Windows line endings."""
    if v is None:
        return None
    s = str(v).replace("\r\n", "\n").strip()
    return s or None


def iso_date(v) -> str | None:
    """PSI uses 'MM-DD-YYYY' for project dates and 'DD-Mon-YYYY' for release dates."""
    s = text(v)
    if not s:
        return None
    for fmt in ("%m-%d-%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return s  # keep unknown formats visible rather than dropping them


def file_url(acc: str, name: str) -> str:
    return DOWNLOAD_URL.format(acc=acc, file=urllib.parse.quote(name))


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# ---------------------------------------------------------------- card parts

def publications(rec: dict) -> list[dict]:
    seen, out = set(), []
    for p in rec.get("publications") or []:
        title = text(p.get("title"))
        key = (title or "").lower()
        if not title or key in seen:
            continue
        seen.add(key)
        doi = text(p.get("doi"))
        out.append({
            "title": title,
            "authors": text(p.get("authorList")),
            "doi": doi,
            "doi_url": f"https://doi.org/{doi}" if doi and not doi.startswith("http") else doi,
            "status": text(p.get("status")),
        })
    return out


def images(acc: str, rec: dict) -> list[dict]:
    return [{"file_name": f["file_name"], "url": file_url(acc, f["file_name"])}
            for f in rec.get("images") or [] if not f.get("restricted") and f.get("file_name")]


def tables(acc: str, rec: dict) -> list[dict]:
    out, seen = [], set()
    for f in rec.get("experimentalTable") or []:
        name = f.get("file_name")
        if not name or name in seen:
            continue
        seen.add(name)
        local = PSI_DIR / acc / "tables" / safe_name(name)
        out.append({"file_name": name, "local_path": rel(local), "downloaded": local.exists()})
    return out


# ---------------------------------------------------------------- tests + conditions from the cleaned tables

def load_clean() -> dict[str, list[tuple[str, dict]]]:
    """psi_id -> [(clean table file name, row), ...] for every row of every cleaned table."""
    by_psi: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for f in sorted(CLEAN_DIR.glob("*.csv")):
        with open(f, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                by_psi[row["psi_id"]].append((f.name, row))
    return by_psi


def fnum(s: str) -> float | None:
    try:
        return float(s) if s not in ("", None) else None
    except ValueError:
        return None


def n_tests(row: dict) -> int | None:
    v = fnum(row.get("n_tests", ""))
    return None if v is None else int(v)


def truthy(s: str) -> bool:
    return str(s).strip().lower() == "true"


def value_range(rows: list[dict], lo: str, hi: str, assumed: str | None = None) -> dict | None:
    los = [v for r in rows if (v := fnum(r.get(lo, ""))) is not None]
    his = [v for r in rows if (v := fnum(r.get(hi, ""))) is not None]
    if not los and not his:
        return None
    out = {"min": round(min(los or his), 2), "max": round(max(his or los), 2),
           "rows_with_value": sum(1 for r in rows if fnum(r.get(lo, "")) is not None or fnum(r.get(hi, "")) is not None)}
    if assumed:
        out["assumed"] = any(truthy(r.get(assumed, "")) for r in rows
                             if fnum(r.get(lo, "")) is not None or fnum(r.get(hi, "")) is not None)
    return out


def summarize(entries: list[tuple[str, dict]]) -> tuple[dict, dict]:
    """Return (tests, conditions) for one investigation from its cleaned rows."""
    rows = [r for _, r in entries]
    counts = [n_tests(r) for r in rows]
    per_table = defaultdict(list)
    for name, r in entries:
        per_table[name].append(r)

    known = [c for c in counts if c is not None]
    tests = {
        "available": True,
        # None = unknown (e.g. SLICE days, FLEX-2 planned ranges); never shown as 0 fires
        "count": sum(known) if known else None,
        "rows_with_unknown_count": sum(1 for c in counts if c is None),
        "with_results": sum(1 for r in rows if truthy(r["has_result"])),
        "lunar_air": sum(n_tests(r) or 0 for r in rows if truthy(r["lunar_air"])),
        "row_types": dict(Counter(r["row_granularity"] for r in rows)),
        "tables": [{"clean_file": f"data/psi/clean/{name}",
                    "source_file": rs[0]["source_file"],
                    "rows": len(rs),
                    "tests": sum(n_tests(r) or 0 for r in rs)} for name, rs in per_table.items()],
    }

    fuels: dict[str, dict] = {}
    for r in rows:
        name = r["fuel"] or "unknown"
        f = fuels.setdefault(name, {"name": name, "tests": 0, "rows": 0})
        f["rows"] += 1
        f["tests"] += n_tests(r) or 0
    o2 = {}
    for loc in ("chamber", "burner_stream"):
        rng = value_range([r for r in rows if r["o2_location"] == loc], "o2_min_pct", "o2_max_pct", "o2_assumed")
        if rng:
            o2[loc] = rng
    conditions = {
        "fuels": sorted(fuels.values(), key=lambda f: (-f["tests"], -f["rows"], f["name"])),
        "o2_pct": o2 or None,
        "pressure_kpa": value_range(rows, "pressure_min_kpa", "pressure_max_kpa", "pressure_assumed"),
        "flow_cm_s": value_range(rows, "flow_min_cm_s", "flow_max_cm_s"),
        "diluents": sorted({r["diluent"] for r in rows if r["diluent"]}),
        "gravity": sorted({r["gravity"] for r in rows if r["gravity"]}),
        "notes": [],
    }
    if "burner_stream" in o2:
        conditions["notes"].append("burner_stream O2 is oxygen blown out of the burner (inverse flames), "
                                   "not cabin air; never compare it with chamber O2.")
    for key, label in (("o2_pct", "O2"), ("pressure_kpa", "pressure"), ("flow_cm_s", "airflow")):
        if conditions[key] is None:
            conditions["notes"].append(f"{label} not recorded in the test table")
    if tests["rows_with_unknown_count"]:
        conditions["notes"].append(f"{tests['rows_with_unknown_count']} row(s) do not say how many fires they stand for")
    return tests, conditions


NO_TABLE = {"available": False, "note": "No test table for this investigation."}


# ---------------------------------------------------------------- habitat match (content/habitats.json)

def in_box(v: float | None, box: list[float]) -> bool:
    return v is not None and box[0] <= v <= box[1]


def overlaps(lo: float | None, hi: float | None, box: list[float]) -> bool:
    return lo is not None and hi is not None and lo <= box[1] and hi >= box[0]


def habitat_match(entries: list[tuple[str, dict]], habitats: list[dict]) -> dict:
    """Per habitat, tests whose CHAMBER O2 and pressure fall inside the habitat's match box, in four groups
    (each test is counted in one group only):
      measured  - O2 and pressure both recorded per test in the table (this group is the ranking)
      from_note - inside the box, but O2 or pressure comes from a report or table note, not per test
      o2_only   - recorded O2 inside the box, pressure not recorded
      mixed     - the row covers several O2 values (e.g. a BRE test day '26.5; 34; 40') and some of them
                  are inside the box; how many of the row's tests were at that O2 is not recorded
    Burner-stream O2 (inverse flames) is never counted. Plain counts, no weights."""
    rows = [r for _, r in entries if r["o2_location"] == "chamber"]

    def tests(rs: list[dict]) -> int:
        return sum(n_tests(r) or 0 for r in rs)

    out = {}
    for h in habitats:
        o2_box, p_box = h["match"]["o2_pct"], h["match"]["pressure_kpa"]
        groups: dict[str, list[dict]] = {"measured": [], "from_note": [], "o2_only": [], "mixed": []}
        for r in rows:
            o2, p = fnum(r["o2_pct"]), fnum(r["pressure_kpa"])
            noted = truthy(r["o2_assumed"]) or truthy(r["pressure_assumed"])
            p_ok = in_box(p, p_box) or (p is None and overlaps(fnum(r["pressure_min_kpa"]), fnum(r["pressure_max_kpa"]), p_box))
            if in_box(o2, o2_box) and in_box(p, p_box):
                groups["from_note" if noted else "measured"].append(r)
            elif in_box(o2, o2_box) and p is None and not truthy(r["o2_assumed"]):
                groups["o2_only"].append(r)
            elif overlaps(fnum(r["o2_min_pct"]), fnum(r["o2_max_pct"]), o2_box) and (p is None or p_ok):
                groups["mixed"].append(r)
        out[h["id"]] = {k: {"tests": tests(v)} for k, v in groups.items()}
        out[h["id"]]["measured"]["with_results"] = tests([r for r in groups["measured"] if truthy(r["has_result"])])
    return out


# ---------------------------------------------------------------- sources

def page_anchor(where: str) -> str:
    """'84' or '76-77' -> '#page=84' (browsers' PDF viewers jump to that page)."""
    m = re.match(r"\s*(\d+)", where)
    return f"#page={m.group(1)}" if m else ""


def source_url(s: dict, ref: dict, acc: str, tables: list[dict]) -> str:
    """The most direct link to what is cited:
    - a PSI document (file under data/psi/<id>/docs/): its PSI download link, plus #page= for PDFs
    - a test table ('data' / 'psi_table'): the PSI download link of the original table CSV
    - otherwise the source's url (plus #page= when it is a PDF, e.g. the Researcher's Guide)."""
    f = s.get("file", "").format(id=acc)
    where = text(ref.get("where")) or ""
    if "/docs/" in f:
        url = file_url(f.split("/")[2], Path(f).name)
        return url + page_anchor(where) if f.lower().endswith(".pdf") else url
    if ref.get("src") in ("data", "psi_table") and tables:
        named = [t for t in tables if Path(t["clean_file"]).name in where]
        pick = named[0] if named else (tables[0] if len(tables) == 1 else None)
        if pick:
            return file_url(acc, Path(pick["source_file"]).name)
    url = s["url"].format(id=acc)
    return url + page_anchor(where) if url.lower().endswith(".pdf") else url


def cite(ref: dict, acc: str, sources: dict, tables: list[dict]) -> dict:
    """{src, where} -> adds a ready-to-display 'cite' line, the direct 'url' and the local 'file'.
    Unknown src keys get cite=None (reported by problems())."""
    s = sources.get(ref.get("src"))
    if not s:
        return {**ref, "cite": None, "url": None, "file": None}
    where = text(ref.get("where"))
    line = s["label"].format(id=acc) + (f", {s.get('where_prefix', '')}{where}" if where else "")
    return {**ref, "cite": line, "url": source_url(s, ref, acc, tables),
            "file": s.get("file", "").format(id=acc) or None}


def cited_summary(summary, acc: str, sources: dict, tables: list[dict]):
    if not summary:
        return None
    return {"text": summary["text"], "sources": [cite(r, acc, sources, tables) for r in summary.get("sources", [])]}


def build_card(rec: dict, curated: dict, clean: dict[str, list[tuple[str, dict]]], sources: dict,
               habitats: list[dict]) -> dict:
    acc = rec["accession"]
    cur = curated.get(acc, {})
    project_type = text(rec.get("projectType"))
    doi = text(rec.get("doi"))
    pubs = publications(rec)
    tests, conditions = summarize(clean[acc]) if clean.get(acc) else (NO_TABLE, NO_TABLE)
    return {
        "id": acc,
        "name": text(rec.get("investigationAcronym")) or acc,
        "title": text(rec.get("title")),
        "project_type": project_type,
        "in_space": project_type == "Microgravity Investigation",
        "flight_program": text(rec.get("flightProgram")),
        "nasa_center": text(rec.get("managingNasaCenter")),

        # curated (content/cards_curated.json)
        "fuel_type": cur.get("fuel_type"),
        "fire_safety": {
            "jobs": cur.get("safety_jobs", []),                  # prevention / detection / suppression
            "psi_label": text(rec.get("subResearchArea")),       # NASA PSI's own sub-research area
        },
        "hardware_group": cur.get("hardware_group"),
        "hardware_raw": text(rec.get("experimentHardware")),
        # every item carries its source: {text, src, where, cite, url}; summary = {text, sources: [...]}
        "summary": cited_summary(cur.get("summary"), acc, sources, tests.get("tables", [])),
        "findings": [cite(f, acc, sources, tests.get("tables", [])) for f in cur.get("findings", [])],
        "limitations": [cite(x, acc, sources, tests.get("tables", [])) for x in cur.get("limitations", [])],

        "dates": {
            "project_start": iso_date(rec.get("investigationStartDate")),
            "project_end": iso_date(rec.get("investigationEndDate")),
            "note": "Project dates from PSI, not flight dates.",
        },
        "text": {
            "objective": text(rec.get("objective")),
            "hypothesis": text(rec.get("hypothesis")),   # a hypothesis, not a result
            "approach": text(rec.get("approach")),
            "research_impacts": text(rec.get("researchImpacts")),
        },

        # from the cleaned test tables (data/psi/clean/)
        "tests": tests,
        "conditions": conditions,
        # tests run inside each habitat's O2 / pressure box (content/habitats.json); None = no test table
        "habitat_match": habitat_match(clean[acc], habitats) if clean.get(acc) else None,

        "tables": tables(acc, rec),
        "documents": {"url": REPO_PAGE.format(acc=acc), "note": "All reports and files on the PSI repository page."},
        "publications": {"count": len(pubs), "items": pubs},
        "images": images(acc, rec),
        "links": {
            "psi_page": REPO_PAGE.format(acc=acc),
            "doi": doi,
            "doi_url": f"https://doi.org/{doi}" if doi else None,
        },
        "source": {
            "record": rel(PSI_DIR / acc / "investigation.json"),
            "psi_release_date": iso_date(rec.get("releaseDate")),
            "psi_modified_date": iso_date(rec.get("modifiedDate")),
        },
    }


# ---------------------------------------------------------------- checks

def problems(card: dict) -> list[str]:
    out = []
    if card["fuel_type"] not in FUEL_TYPES:
        out.append(f"fuel_type={card['fuel_type']!r}")
    if card["hardware_group"] not in HARDWARE_GROUPS:
        out.append(f"hardware_group={card['hardware_group']!r}")
    bad_jobs = set(card["fire_safety"]["jobs"]) - SAFETY_JOBS
    if bad_jobs:
        out.append(f"safety_jobs has {sorted(bad_jobs)}")
    if card["in_space"] and card["fuel_type"] == "ground":
        out.append("marked ground but is a microgravity investigation")
    if not card["text"]["objective"]:
        out.append("no objective")
    missing = [t["file_name"] for t in card["tables"] if not t["downloaded"]]
    if missing:
        out.append(f"{len(missing)} table(s) not downloaded")
    if card["tables"] and not card["tests"]["available"]:
        out.append("has a PSI test table but no cleaned rows (run scripts/clean_tables.py)")
    refs = (card["summary"] or {}).get("sources", []) + card["findings"] + card["limitations"]
    if any(r.get("cite") is None for r in refs):
        out.append("an item has no or an unknown source (src)")
    if card["summary"] and not card["summary"]["sources"]:
        out.append("summary has no source")
    return out


def todo(card: dict) -> list[str]:
    out = []
    if not card["fire_safety"]["jobs"]:
        out.append("fire_safety")
    if not card["summary"]:
        out.append("summary")
    if not card["findings"]:
        out.append("findings")
    if not card["images"]:
        out.append("image")
    return out


# ---------------------------------------------------------------- main

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output file (default {rel(DEFAULT_OUT)})")
    a = p.parse_args()

    records = [json.loads(f.read_text(encoding="utf-8")) for f in PSI_DIR.glob("PSI-*/investigation.json")]
    if not records:
        print(f"No investigation.json files under {PSI_DIR}. Run scripts/psi_download.py first.", file=sys.stderr)
        return 1
    records.sort(key=lambda r: int(r["accession"].split("-")[1]))

    raw = json.loads(CURATED.read_text(encoding="utf-8"))
    sources = raw.get("_sources", {})
    curated = {k: v for k, v in raw.items() if not k.startswith("_")}
    if not CLEAN_DIR.exists():
        print(f"No cleaned tables in {CLEAN_DIR}. Run scripts/clean_tables.py first.", file=sys.stderr)
        return 1
    clean = load_clean()

    habitats = json.loads(HABITATS.read_text(encoding="utf-8"))["habitats"]
    cards = [build_card(r, curated, clean, sources, habitats) for r in records]
    for acc in sorted(set(curated) - {c["id"] for c in cards}):
        print(f"  warning: {acc} is in {rel(CURATED)} but has no investigation.json", file=sys.stderr)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        "generator": "scripts/build_cards.py",
        "count": len(cards),
        "cards": cards,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    def rng(d: dict | None) -> str:
        if not d:
            return "-"
        return f"{d['min']:g}" if d["min"] == d["max"] else f"{d['min']:g}-{d['max']:g}"

    def count(t: dict) -> str:
        if t["count"] is None:
            return "?"
        return f"{t['count']}+" if t["rows_with_unknown_count"] else str(t["count"])

    n_problems = 0
    print(f"{'id':8} {'name':18} {'fuel':8} {'tests':>5} {'res':>4} {'lunar':>5} {'O2 % (chamber)':>14} "
          f"{'kPa':>11} {'cm/s':>9}  to do / problems")
    for c in cards:
        probs = problems(c)
        n_problems += len(probs)
        flags = ", ".join(todo(c)) + (("  !! " + "; ".join(probs)) if probs else "")
        t, cond = c["tests"], c["conditions"]
        if t["available"]:
            o2 = rng((cond["o2_pct"] or {}).get("chamber"))
            if cond["o2_pct"] and "burner_stream" in cond["o2_pct"]:
                o2 += "*"
            line = (f"{count(t):>5} {t['with_results']:4} {t['lunar_air']:5} {o2:>14} "
                    f"{rng(cond['pressure_kpa']):>11} {rng(cond['flow_cm_s']):>9}")
        else:
            line = f"{'no test table':>53}"
        print(f"{c['id']:8} {c['name'][:18]:18} {str(c['fuel_type']):8} {line}  {flags}")
    print("\n* = also has burner-stream O2 (inverse flames), shown separately in the card."
          "\n? = number of fires unknown;  N+ = N fires counted plus rows with an unknown number.")
    print("\nTests inside each habitat's O2 / pressure box (chamber O2 only; content/habitats.json):")
    for h in habitats:
        hid = h["id"]
        matched = [c for c in cards if c["habitat_match"]]

        def group(key: str) -> str:
            ranked = sorted(matched, key=lambda c: (-c["habitat_match"][hid][key]["tests"],
                                                    -c["habitat_match"][hid][key].get("with_results", 0)))
            items = [f"{c['name']} {c['habitat_match'][hid][key]['tests']}" for c in ranked
                     if c["habitat_match"][hid][key]["tests"]]
            return ", ".join(items) or "none"

        print(f"  {h['label']}")
        print(f"    measured per test:                 {group('measured')}")
        print(f"    from a report or table note:       {group('from_note')}")
        print(f"    O2 matches, pressure not recorded: {group('o2_only')}")
        print(f"    row mixes several O2 values:       {group('mixed')}")
    print(f"\nWrote {len(cards)} cards to {a.out}. {n_problems} problem(s).")
    return 1 if n_problems else 0


if __name__ == "__main__":
    sys.exit(main())
