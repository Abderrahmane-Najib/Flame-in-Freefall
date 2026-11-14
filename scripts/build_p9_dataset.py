"""Merge the four P9 extractions into one table of solid-fuel outcomes.

  data/psi/extracted/p9_olson.csv, p9_tien.csv, p9_stage3.csv, p9_bass.csv  ->  data/psi/extracted/p9_solids.csv

Common fields: material family, shape, size, flow direction, O2 (calibrated initial, %), outcome, flow at
the outcome in cm/s when it can be converted, and the flags needed to filter for modelling.
Flow conversion: air display -> U = 1.0066 x air; BASS-II pot -> that day's fan calibration
(scripts/fan_calibration.py); below the calibrated range or BASS fan values -> no single number
(u_cm_s blank; u_high_cm_s gives the ceiling when known).

  python scripts/build_p9_dataset.py
"""
import collections
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fan_calibration as fc  # noqa: E402
from build_p10_points import doy  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "data/psi/extracted"
OUT = EX / "p9_solids.csv"
CAL = fc.load()


def read(name):
    return list(csv.DictReader((EX / name).open(encoding="utf-8")))


def describe(material):
    """material text -> (family, shape, size_mm, size_kind)."""
    m = material.lower()
    if "sibal" in m or re.search(r"\bsi\b", m):
        fam, shape = "SIBAL fabric (cotton/fiberglass)", "fabric"
    elif "nomex" in m:
        fam, shape = "Nomex fabric", "fabric"
    elif "ultem" in m:
        fam, shape = "Ultem sheet", "sheet"
    elif "wax" in m or "candle" in m:
        fam = "wax"
        shape = "candle" if "candle" in m else "slab"
    elif "spherical section" in m:
        fam, shape = "unspecified (spherical section)", "spherical section"
    else:
        fam = "PMMA"
        shape = ("rod" if "rod" in m else "sphere" if "sphere" in m or re.fullmatch(r"pmma [12] cm", m)
                 else "film" if "film" in m or "um" in m or re.search(r"0\.\d+-?mm", m) else "slab")
    size, kind = "", ""
    if shape == "rod":
        mm = re.search(r"([\d.]+)-mm", m)
        inch = re.search(r'(\d)/(\d)"', m)
        size = float(mm.group(1)) if mm else round(25.4 * int(inch.group(1)) / int(inch.group(2)), 3)
        kind = "diameter_mm"
    elif shape == "sphere":
        cm = re.search(r"(\d) cm", m)
        size, kind = (float(cm.group(1)) * 10, "diameter_mm") if cm else ("", "")
    elif shape in ("film", "slab") and fam == "PMMA":
        um = re.search(r"(\d+)\s*-?\s*um", m)
        mm = re.search(r"(\d+(?:\.\d+)?)-?mm(?:-thick| thick)?", m)
        if um:
            size, kind = float(um.group(1)) / 1000, "thickness_mm"
        elif mm:
            size, kind = float(mm.group(1)), "thickness_mm"
        elif re.search(r"(\d) mm thick", m):
            size, kind = float(re.search(r"(\d) mm thick", m).group(1)), "thickness_mm"
    elif shape == "fabric" and "sibal" in m:
        size, kind = (12 if "1 cm" in m else 22), "width_mm"
    return fam, shape, size, kind


def to_u(raw, unit, date, restrictor):
    """(u, u_high, method)."""
    if raw in ("", None) or unit == "":
        return "", "", ""
    try:
        v = float(raw)
    except ValueError:
        return "", "", f"not numeric ('{raw}')"
    if unit == "air_cm_s":
        return round(v * fc.U_PER_AIR, 3), "", "air display"
    if v == 0:
        return 0.0, "", "flow off"
    if unit == "fan_display":
        return ("", "", "fan display, no BASS calibration") if v > 38 else (0.0, "", "fan off")
    d = doy(date) if date else None
    if not d or d[1] != 2014 or restrictor in ("", None):
        return "", "", "pot, no calibration for this date"
    u, method, used = fc.pot_to_u(CAL, d[0], int(float(restrictor)), v)
    if method == "below_calibration":
        ceil = fc.low_flow_ceiling(CAL, int(float(restrictor)))
        return "", round(ceil, 3) if ceil is not None else "", "below calibration (range only)"
    return round(u, 3), "", f"pot via fan calibration {used}"


def main():
    rows = []
    for name, program in (("p9_olson.csv", "BASS-II"), ("p9_tien.csv", "BASS-II"), ("p9_stage3.csv", "BASS-II")):
        last_date = ""
        for r in read(name):
            r["date"] = r["date"] or last_date
            last_date = r["date"]
            pi = r.get("pi") or {"O": "Olson", "T": "T'ien"}[r["test_id"][0]]
            unit = r.get("outcome_flow_unit", "air_cm_s" if "outcome_flow_cm_s" in r else "")
            raw = r.get("outcome_flow_raw", r.get("outcome_flow_cm_s", ""))
            u, uhi, method = to_u(raw, unit, r["date"], r["flow_restrictor"])
            fam, shape, size, kind = describe(r["material"])
            rows.append({"uid": f"BASS-II {r['test_id']}", "program": program, "pi": pi, "test_id": r["test_id"],
                         "date": r["date"], "sample_no": r["sample_no"], "material": r["material"],
                         "family": fam, "shape": shape, "size": size, "size_kind": kind,
                         "flow_direction": r["flow_direction"] or "unknown",
                         "o2_pct": r["o2_cal_initial_pct"], "outcome": r["outcome"],
                         "outcome_flow_raw": raw, "outcome_flow_unit": unit,
                         "u_cm_s": u, "u_high_cm_s": uhi, "u_method": method,
                         "reused": r["reused"] == "True", "n2_suppression_used": False,
                         "confidence": r["confidence"], "source_doc": r["source_doc"], "source_page": r["source_page"]})
    for r in read("p9_bass.csv"):
        u, uhi, method = to_u(r["outcome_flow_raw"], r["outcome_flow_unit"], "", "")
        fam, shape, size, kind = describe(r["material"])
        rows.append({"uid": f"BASS row {r['workbook_row']} ({r['test_no']})", "program": "BASS", "pi": "",
                     "test_id": r["test_no"], "date": r["date"], "sample_no": r["sample_no"], "material": r["material"],
                     "family": fam, "shape": shape, "size": size, "size_kind": kind,
                     "flow_direction": r["flow_direction"], "o2_pct": r["o2_pct"], "outcome": r["outcome"],
                     "outcome_flow_raw": r["outcome_flow_raw"], "outcome_flow_unit": r["outcome_flow_unit"],
                     "u_cm_s": u, "u_high_cm_s": uhi, "u_method": method,
                     "reused": r["reused"] == "True", "n2_suppression_used": r["n2_suppression_used"] == "True",
                     "confidence": r["confidence"], "source_doc": r["source_doc"], "source_page": r["source_page"]})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "solid tests ->", OUT)
    print("outcomes:", dict(collections.Counter(r["outcome"] or "(blank)" for r in rows)))
    usable = [r for r in rows if r["outcome"] and not r["reused"] and not r["n2_suppression_used"]]
    print(f"\nusable for modelling (labelled, fresh sample, no N2): {len(usable)}")
    grid = collections.defaultdict(collections.Counter)
    for r in usable:
        grid[(r["family"], r["shape"], r["flow_direction"])][r["outcome"]] += 1
    for k, c in sorted(grid.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"  {sum(c.values()):3d}  {k[0]:34s} {k[1]:17s} {k[2]:11s} {dict(c)}")


if __name__ == "__main__":
    main()
