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
import sys
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from psi_download import DOWNLOAD_URL, OUT as PSI_DIR, REPO_PAGE, ROOT, safe_name

CURATED = ROOT / "content" / "cards_curated.json"
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


def build_card(rec: dict, curated: dict, clean: dict[str, list[tuple[str, dict]]]) -> dict:
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
        "summary": cur.get("summary"),
        "findings": cur.get("findings", []),
        "limitations": cur.get("limitations", []),

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

    curated = {k: v for k, v in json.loads(CURATED.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    if not CLEAN_DIR.exists():
        print(f"No cleaned tables in {CLEAN_DIR}. Run scripts/clean_tables.py first.", file=sys.stderr)
        return 1
    clean = load_clean()

    cards = [build_card(r, curated, clean) for r in records]
    for acc in sorted(set(curated) - {c["id"] for c in cards}):
        print(f"  warning: {acc} is in {rel(CURATED)} but has no investigation.json", file=sys.stderr)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
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
    print(f"\nWrote {len(cards)} cards to {a.out}. {n_problems} problem(s).")
    return 1 if n_problems else 0


if __name__ == "__main__":
    sys.exit(main())
