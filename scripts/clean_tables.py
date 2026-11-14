"""Step 1b: clean every PSI test table into one CSV per experiment.

Every cleaned table has:
  - the COMMON columns (same name + standard unit in every table, from content/units.json):
      investigation, psi_id, test_id, test_date, row_granularity, n_tests, fuel, fuel_type,
      o2_pct (+ min/max), o2_location, o2_assumed, pressure_kpa (+ min/max), pressure_assumed,
      flow_cm_s (+ min/max), n2_pct, co2_pct, he_pct, diluent, o2_partial_kpa, lunar_air, gravity, has_result
  - its OWN columns (kept, names tidied, units converted where the unit is known)
  - TRACE columns: source_file, source_row, original values/units of converted fields, flags

row_granularity = what one row is:
  test                one fire
  test_day            a day summary; n_tests = flames ignited that day (BRE, CLD, E-FIELD, s-Flame, SLICE)
  planned_range       planned conditions for one fuel, not tests (FLEX-2)
  same_as_samples_1_4 SAME rows that only say "same conditions as 1-4"
  aged_measurement    SAME-R re-measurement of an earlier burn, not a new fire
  measurement         SPICE: another data point on a flame already counted
  session             DAFT dust session (not a fire)
  reference           PSI-142 figure pointer (not a test)
n_tests = how many fires a row stands for (empty = unknown). A card's test count = sum of n_tests.

O2 / pressure are only filled when the row or a NASA document states them. Values taken from a
document rather than the row are marked o2_assumed / pressure_assumed. Nothing is invented.

Nothing is dropped except empty rows, notes, flow-visualisation entries and rows that cannot be
placed (e.g. pressure = 0); every drop is counted with its reason in clean/_report.json.

Reads:   the 22 tables in data/psi/PSI-*/tables/, plus two workbooks:
         PSI-39/docs/…CFI_DataSummary_Spreadsheet_Jan2021.xlsx  (replaces the CFI CSV: 227 tests vs 79)
         PSI-26/docs/…As Run_Test Matrix.xlsx                   (BASS conditions; the BASS CSV has none)
Writes:  data/psi/clean/<table>.csv (one per table) and data/psi/clean/_report.json

Usage:
  python scripts/clean_tables.py
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from psi_download import OUT as PSI_DIR, ROOT
from units import to_std
from xlsx_read import read_xlsx

CLEAN_DIR = PSI_DIR / "clean"

COMMON = ["investigation", "psi_id", "test_id", "test_date", "row_granularity", "n_tests", "fuel", "fuel_type",
          "o2_pct", "o2_min_pct", "o2_max_pct", "o2_location", "o2_assumed",
          "pressure_kpa", "pressure_min_kpa", "pressure_max_kpa", "pressure_assumed",
          "flow_cm_s", "flow_min_cm_s", "flow_max_cm_s",
          "n2_pct", "co2_pct", "he_pct", "diluent", "o2_partial_kpa", "lunar_air", "gravity", "has_result"]
TRACE = ["source_file", "source_row", "o2_raw", "o2_raw_unit", "pressure_raw", "pressure_raw_unit", "flags"]

# Lunar base / pressurized rover air from the challenge brief: O2 >= 30 %, pressure <= 10.2 psi (~70 kPa).
LUNAR_O2_MIN_PCT = 30.0
LUNAR_P_MAX_KPA = 70.3
ONE_ATM_KPA = 101.325


# ================================================================ reading helpers

def read_csv(path: Path) -> tuple[list[str], list[tuple[int, dict]], str]:
    """Return (headers, [(data_row_number, row_dict)], encoding). Row 1 = first row after the header."""
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    rows = list(csv.reader(io.StringIO(text, newline="")))  # keeps line breaks inside quoted cells
    headers = [norm_header(h) for h in rows[0]]
    out = []
    for i, r in enumerate(rows[1:], start=1):
        r = r + [""] * (len(headers) - len(r))
        out.append((i, {h: (v or "").strip() for h, v in zip(headers, r) if h}))
    return headers, out, enc


def norm_header(h: str) -> str:
    return re.sub(r"\s+", " ", (h or "").replace("﻿", "")).strip()


def find_col(headers: list[str], pattern: str, required: bool = True) -> str | None:
    rx = re.compile(pattern, re.IGNORECASE)
    for h in headers:
        if h and rx.search(h):
            return h
    if required:
        raise KeyError(f"no column matches /{pattern}/ in {headers}")
    return None


def is_empty(row: dict) -> bool:
    return not any(str(v).strip() for v in row.values())


def sheet_rows(sheet: list[list[str]], header_pattern: str | None = None) -> tuple[list[str], list[tuple[int, dict]]]:
    """Header = first row matching header_pattern (or first non-empty row). Row numbers = spreadsheet rows."""
    if header_pattern:
        rx = re.compile(header_pattern, re.IGNORECASE)
        start = next(i for i, r in enumerate(sheet) if any(rx.search(str(c)) for c in r))
    else:
        start = next(i for i, r in enumerate(sheet) if any(str(x).strip() for x in r))
    headers = [norm_header(h) for h in sheet[start]]
    out = []
    for i, r in enumerate(sheet[start + 1:], start=start + 2):
        r = list(r) + [""] * (len(headers) - len(r))
        d = {h: str(v).strip() for h, v in zip(headers, r) if h}
        if any(d.values()):
            out.append((i, d))
    return headers, out


# ================================================================ value helpers

_NUM = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")


def num(s) -> float | None:
    """First number in a cell ('~ 21.5' -> 21.5, '1 atm' -> 1.0, '' -> None)."""
    if s is None or str(s).strip().startswith("#"):  # spreadsheet errors (#DIV/0!, #N/A, #VALUE!) are blank
        return None
    m = _NUM.search(str(s).replace(",", ""))
    return float(m.group()) if m else None


def nums(s) -> list[float]:
    """All numbers in a cell. '1.5 - 5' and '30%-40%' are ranges, not negatives."""
    if s is None:
        return []
    t = str(s).replace(",", " ")
    t = re.sub(r"(?<=[\d%])\s*-\s*(?=[\d.])", " ", t)
    return [float(x) for x in _NUM.findall(t)]


def span(vals: list[float]) -> tuple[float | None, float | None]:
    return (min(vals), max(vals)) if vals else (None, None)


def fmt_list(vals: list[float]) -> str:
    return ";".join(f"{v:g}" for v in vals)


def rnd(v: float | None, nd: int = 4) -> float | None:
    return None if v is None else round(v, nd)


def as_int(v: float | None) -> int | None:
    return None if v is None else int(v)


def excel_date(s: str) -> str:
    """Excel serial day (e.g. '42803') -> ISO date; anything else is returned unchanged."""
    v = num(s)
    if v is not None and 20000 < v < 80000 and re.fullmatch(r"\s*\d+(\.0+)?\s*", s or ""):
        return (date(1899, 12, 30) + timedelta(days=int(v))).isoformat()
    return s or ""


def doy_date(s) -> str | None:
    """'19115' (YYDDD: year 2019, day 115) -> '2019-04-25'."""
    m = re.fullmatch(r"\s*(\d{2})(\d{3})\s*", str(s or ""))
    if not m or not 1 <= int(m.group(2)) <= 366:
        return None
    return (date(2000 + int(m.group(1)), 1, 1) + timedelta(days=int(m.group(2)) - 1)).isoformat()


def mdy_date(s) -> str | None:
    """'2/19/2014' -> '2014-02-19'."""
    m = re.fullmatch(r"\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*", str(s or ""))
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2))).isoformat()
    except ValueError:
        return None


_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def ymd_date(y, mon, d) -> str | None:
    """(2019, 'Feb' / 'Sept.' / '3', 8) -> '2019-02-08'."""
    try:
        mon = str(mon).strip()
        month = int(mon) if mon.isdigit() else _MONTHS[mon.lower()[:3]]
        return date(int(num(y)), month, int(num(d))).isoformat()
    except (KeyError, TypeError, ValueError):
        return None


def fraction_to_pct(v: float | None, flags: list[str], name: str) -> float | None:
    """Gas shares stored as mole fractions -> %. A value above 1 is taken as already in % (flagged)."""
    if v is None:
        return None
    if v > 1.0:
        flags.append(f"{name}_already_percent")
        return v
    return to_std(v, "gas_fraction", "fraction")


def pct_values(s, flags: list[str]) -> list[float]:
    """'21; 26.5; 40' -> [21, 26.5, 40]. Excel artifacts like '3400%' are read as 34 (flagged)."""
    out = []
    for v in nums(s):
        if v > 100:
            v /= 100
            flags.append("excel_percent_artifact")
        out.append(v)
    return out


def parse_gas_fuel(s: str) -> tuple[str | None, float | None]:
    """'100% C2H4' / '100%C2H4' / '40% CH4 (balance N2)' -> ('C2H4', 100.0); 'Ethylene' -> ('ethylene', None)."""
    s = (s or "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*([A-Za-z][A-Za-z0-9]*)", s)
    if m:
        return m.group(2), float(m.group(1))
    return (s.lower() or None), None


def diluent_of(co2: float | None, he: float | None) -> str:
    co2, he = co2 or 0, he or 0
    if co2 > 0 and he > 0:
        return "CO2+He"
    if co2 > 0:
        return "CO2"
    if he > 0:
        return "He"
    return "N2"


# ================================================================ common-column / output helpers

def finish_common(row: dict) -> dict:
    """Fill defaults for the common columns. A single value is also its own min and max."""
    for single, lo, hi in (("o2_pct", "o2_min_pct", "o2_max_pct"),
                           ("pressure_kpa", "pressure_min_kpa", "pressure_max_kpa"),
                           ("flow_cm_s", "flow_min_cm_s", "flow_max_cm_s")):
        row.setdefault(single, None)
        if row.get(lo) is None:
            row[lo] = row[single]
        if row.get(hi) is None:
            row[hi] = row[single]
    row.setdefault("row_granularity", "test")
    row.setdefault("n_tests", 1 if row["row_granularity"] == "test" else None)
    row.setdefault("o2_assumed", False)
    row.setdefault("pressure_assumed", False)
    for k in ("o2_location", "n2_pct", "co2_pct", "he_pct", "diluent", "test_date", "fuel"):
        row.setdefault(k, None)
    row.setdefault("has_result", False)
    row.setdefault("gravity", "microgravity")
    o2, p = row["o2_pct"], row["pressure_kpa"]
    chamber = row["o2_location"] == "chamber"
    row["o2_partial_kpa"] = rnd(o2 / 100 * p, 2) if (o2 is not None and p is not None and chamber) else None
    row["lunar_air"] = bool(chamber and o2 is not None and p is not None
                            and o2 >= LUNAR_O2_MIN_PCT and p <= LUNAR_P_MAX_KPA)
    return row


def mark_duplicates(rows: list[tuple[int, dict]]) -> dict[int, int]:
    """Map row number -> first identical row number (identical raw cells). Flagged, not dropped."""
    seen, dup = {}, {}
    for n, r in rows:
        key = tuple(sorted(r.items()))
        if key in seen:
            dup[n] = seen[key]
        else:
            seen[key] = n
    return dup


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def table_file(psi: str, pattern: str, folder: str = "tables") -> Path:
    found = sorted(p for p in (PSI_DIR / psi / folder).glob(pattern) if not p.name.startswith("~$"))
    if not found:
        raise FileNotFoundError(f"{psi}/{folder}/{pattern}")
    return found[0]


class Report:
    def __init__(self, name: str, source: Path):
        self.d = {"table": name, "source": rel(source), "rows_read": 0, "rows_written": 0, "tests": 0,
                  "tests_unknown_rows": 0, "dropped": {}, "duplicates_flagged": 0, "with_result": 0,
                  "lunar_air": 0}

    def drop(self, reason: str):
        self.d["dropped"][reason] = self.d["dropped"].get(reason, 0) + 1


def write(name: str, rows: list[dict], own: list[str], rep: Report) -> Path:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    path = CLEAN_DIR / f"{name}.csv"
    cols = COMMON + own + TRACE
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            unknown = set(r) - set(cols)
            if unknown:
                raise KeyError(f"{name}: columns not declared in the output list: {sorted(unknown)}")
            out = {}
            for c in cols:
                v = r.get(c)
                if isinstance(v, bool):
                    v = "true" if v else "false"
                elif isinstance(v, list):
                    v = ";".join(str(x) for x in v)
                out[c] = "" if v is None else v
            w.writerow(out)
    rep.d["rows_written"] = len(rows)
    rep.d["tests"] = sum(r["n_tests"] for r in rows if isinstance(r.get("n_tests"), int))
    rep.d["tests_unknown_rows"] = sum(1 for r in rows if r.get("n_tests") is None)
    rep.d["with_result"] = sum(1 for r in rows if r.get("has_result"))
    rep.d["lunar_air"] = sum(1 for r in rows if r.get("lunar_air"))
    rep.d["output"] = rel(path)
    return path


# ================================================================ PART 1: tables with results

# ---------------------------------------------------------------- FLEX (PSI-69)

FLEX_OWN = ["flex_identifier", "test_time_gmt", "droplet_d0_mm", "extinction_diameter_mm",
            "burning_rate_raw", "burn_time_s", "test_end", "test_end_raw"]


def clean_flex() -> Report:
    src = table_file("PSI-69", "*FLEX*.csv")
    rep = Report("flex", src)
    H, rows, enc = read_csv(src)
    rep.d["encoding"] = enc
    c = {
        "test": find_col(H, r"^FLEX Test"), "ident": find_col(H, r"^FLEX Identifier"),
        "date": find_col(H, r"^Test Date"), "gmt": find_col(H, r"GMT"), "fuel": find_col(H, r"^Fuel$"),
        "p": find_col(H, r"pressure.*mmhg"),
        # Column names lost their subscripts: 'O initial…' = O2, 'CO initial…' = CO2.
        "o2": find_col(H, r"^O[^A-Za-z]*initial"), "n2": find_col(H, r"^N[^A-Za-z]*initial"),
        "co2": find_col(H, r"^CO[^A-Za-z]*initial"), "he": find_col(H, r"^He[^A-Za-z]*initial"),
        "d0": find_col(H, r"initial diameter"), "dext": find_col(H, r"extinction diameter"),
        "rate": find_col(H, r"^Burning rate"), "time": find_col(H, r"^Burn time"), "end": find_col(H, r"^Test end"),
    }
    dups = mark_duplicates(rows)
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags: list[str] = []
        p_mmhg = num(r[c["p"]])
        if p_mmhg is None or p_mmhg <= 0:
            rep.drop("pressure missing or 0")
            continue
        o2 = fraction_to_pct(num(r[c["o2"]]), flags, "o2")
        n2 = fraction_to_pct(num(r[c["n2"]]), flags, "n2")
        co2 = fraction_to_pct(num(r[c["co2"]]), flags, "co2")
        he = fraction_to_pct(num(r[c["he"]]), flags, "he")
        total = sum(v for v in (o2, n2, co2, he) if v is not None)
        if abs(total - 100) > 3:
            flags.append(f"gas_sum_{total:.0f}pct")
        if n in dups:
            flags.append(f"duplicate_of_row_{dups[n]}")
            rep.d["duplicates_flagged"] += 1
        end_raw = r[c["end"]]
        out.append(finish_common({
            "investigation": "FLEX", "psi_id": "PSI-69", "test_id": r[c["test"]],
            "test_date": r[c["date"]], "fuel": r[c["fuel"]].lower() or None, "fuel_type": "droplet",
            "o2_pct": rnd(o2), "o2_location": "chamber",
            "pressure_kpa": rnd(to_std(p_mmhg, "pressure", "mmHg"), 2),
            "n2_pct": rnd(n2), "co2_pct": rnd(co2), "he_pct": rnd(he), "diluent": diluent_of(co2, he),
            "has_result": bool(end_raw),
            "flex_identifier": r[c["ident"]], "test_time_gmt": r[c["gmt"]],
            "droplet_d0_mm": num(r[c["d0"]]), "extinction_diameter_mm": num(r[c["dext"]]),
            "burning_rate_raw": r[c["rate"]],  # unit label 'mm' is ambiguous: kept as recorded
            "burn_time_s": num(r[c["time"]]),
            "test_end": end_raw.lower() or None, "test_end_raw": end_raw,
            "source_file": rel(src), "source_row": n,
            "o2_raw": r[c["o2"]], "o2_raw_unit": "mole fraction",
            "pressure_raw": r[c["p"]], "pressure_raw_unit": "mmHg", "flags": flags,
        }))
    write("flex", out, FLEX_OWN, rep)
    return rep


# ---------------------------------------------------------------- CFI-G (PSI-159)

def split_fuel(s: str) -> tuple[str | None, float | None]:
    """'30% butane' -> ('butane', 30.0); 'propane' -> ('propane', None)."""
    s = (s or "").strip().lower()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*%\s*(.+)$", s)
    return (m.group(2).strip(), float(m.group(1))) if m else (s or None, None)


IGNITION = {"yes": "yes", "no": "no", "flash": "flash"}
EXT_MODE = {"SE": "self_extinguished", "FT": "flow_terminated"}

CFIG_NORMAL_OWN = ["flame_type", "day", "test", "fuel_label", "burner_fuel_pct", "fuel_flow_mg_s",
                   "o2_after_pct", "cool_flame_raw", "tad_k_calculated", "zst", "ignition",
                   "extinction_mode", "burn_time_s", "peak_burner_temp_k", "comments"]
CFIG_INVERSE_OWN = ["flame_type", "day", "test", "chamber_fuel_pct", "chamber_fuel_after_pct",
                    "fuel_burn_rate_mg_s", "o2_flow_mg_s", "tad_k_calculated", "zst", "ignition",
                    "extinction_mode", "burn_time_s", "peak_burner_temp_k", "color", "comments"]


def peak_temp_k(r: dict, col_c: str | None, col_k: str | None) -> float | None:
    if col_k and num(r.get(col_k)) is not None:
        return num(r[col_k])
    if col_c and num(r.get(col_c)) is not None:
        return rnd(to_std(num(r[col_c]), "temperature", "°C"), 1)
    return None


def clean_cfig(kind: str) -> Report:
    src = table_file("PSI-159", f"*CFI-G_{kind} Flames.csv")
    name = f"cfig_{kind.lower()}"
    rep = Report(name, src)
    H, rows, enc = read_csv(src)
    rep.d["encoding"] = enc
    inverse = kind == "Inverse"
    c = {
        "type": find_col(H, r"^Flame Type"), "day": find_col(H, r"^Day$"), "fuel": find_col(H, r"^Fuel$"),
        "test": find_col(H, r"^Test$"), "p": find_col(H, r"approx p"),
        "tad": find_col(H, r"^Tad"), "zst": find_col(H, r"^Zst"), "ign": find_col(H, r"^Hot ignition"),
        "time": find_col(H, r"^burn time"), "ext": find_col(H, r"^Self\s*-?\s*ext"),
        "peak_c": find_col(H, r"^Peak burner (T|Temp)\b.*\(C", required=False),
        "peak_k": find_col(H, r"^Peak burner temp.*\(K", required=False),
        "comments": find_col(H, r"^Comments", required=False),
    }
    if inverse:
        c |= {"o2": find_col(H, r"^XO2$"), "xf": find_col(H, r"^Xf before"), "xf_after": find_col(H, r"^Xf after"),
              "rate": find_col(H, r"^HC burn ?rate"), "o2flow": find_col(H, r"^O2 flow"),
              "color": find_col(H, r"^Color", required=False)}
    else:
        c |= {"o2": find_col(H, r"^XO2 before"), "o2_after": find_col(H, r"^XO2 after"), "xf": find_col(H, r"^Xf$"),
              "mhc": find_col(H, r"^mHC"), "cool": find_col(H, r"^Cool flame", required=False)}
    dups = mark_duplicates([(n, r) for n, r in rows if not is_empty(r)])
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r) or not (r[c["day"]] or r[c["test"]]):
            rep.drop("empty row")
            continue
        flags: list[str] = []
        p_bar = num(r[c["p"]])
        if p_bar is None or p_bar <= 0:
            rep.drop("pressure missing or 0")
            continue
        o2 = fraction_to_pct(num(r[c["o2"]]), flags, "o2")
        if n in dups:
            flags.append(f"duplicate_of_row_{dups[n]}")
            rep.d["duplicates_flagged"] += 1
        gas, pct = split_fuel(r[c["fuel"]])
        ign_raw = r[c["ign"]].strip().lower()
        ignition = IGNITION.get(ign_raw, ign_raw or None)
        ext_raw = r[c["ext"]].strip().upper()
        row = {
            "investigation": "ACME CFI-G", "psi_id": "PSI-159",
            "test_id": f"{r[c['day']]}{r[c['test']]}",
            "fuel": gas, "fuel_type": "gas",
            "o2_pct": rnd(o2), "pressure_kpa": rnd(to_std(p_bar, "pressure", "bar"), 2),
            "co2_pct": 0.0, "he_pct": 0.0, "diluent": "N2",
            "has_result": ignition is not None,
            "flame_type": r[c["type"]], "day": r[c["day"]], "test": r[c["test"]],
            "tad_k_calculated": num(r[c["tad"]]), "zst": num(r[c["zst"]]),
            "ignition": ignition, "extinction_mode": EXT_MODE.get(ext_raw),
            "burn_time_s": num(r[c["time"]]),
            "peak_burner_temp_k": peak_temp_k(r, c["peak_c"], c["peak_k"]),
            "comments": r.get(c["comments"], "") if c["comments"] else "",
            "source_file": rel(src), "source_row": n,
            "o2_raw": r[c["o2"]], "o2_raw_unit": "mole fraction",
            "pressure_raw": r[c["p"]], "pressure_raw_unit": "bar", "flags": flags,
        }
        if inverse:
            # Inverse flame: O2/N2 flows OUT of the burner into a fuel/N2 chamber.
            # XO2 is the burner stream, never cabin air -> no lunar_air, no partial pressure.
            flags.append("o2_is_burner_stream")
            row |= {"o2_location": "burner_stream",
                    "chamber_fuel_pct": rnd(fraction_to_pct(num(r[c["xf"]]), flags, "xf")),
                    "chamber_fuel_after_pct": rnd(fraction_to_pct(num(r[c["xf_after"]]), flags, "xf_after")),
                    "fuel_burn_rate_mg_s": num(r[c["rate"]]), "o2_flow_mg_s": num(r[c["o2flow"]]),
                    "color": r.get(c["color"], "") if c["color"] else ""}
        else:
            row |= {"o2_location": "chamber", "fuel_label": r[c["fuel"]],
                    "burner_fuel_pct": rnd(fraction_to_pct(num(r[c["xf"]]), flags, "xf")),
                    "fuel_flow_mg_s": num(r[c["mhc"]]),
                    "o2_after_pct": rnd(fraction_to_pct(num(r[c["o2_after"]]), flags, "o2_after")),
                    "cool_flame_raw": r.get(c["cool"], "") if c["cool"] else ""}
            if pct is not None and row["burner_fuel_pct"] is None:
                row["burner_fuel_pct"] = pct
        out.append(finish_common(row))
    write(name, out, CFIG_INVERSE_OWN if inverse else CFIG_NORMAL_OWN, rep)
    return rep


# ---------------------------------------------------------------- CFI workbook (PSI-39)

CFI_OWN = ["fiber", "droplet_d0_mm", "dext_hot_mm", "dext_cool_mm", "khot_mm2_s", "kcool_mm2_s",
           "hf_burn_time_s", "reignitions", "reignited", "extrap_cool_flame", "cool_flame_end",
           "analysis_complete", "comment"]


def clean_cfi() -> Report:
    src = table_file("PSI-39", "*CFI_DataSummary_Spreadsheet*.xlsx", folder="docs")
    rep = Report("cfi", src)
    book = read_xlsx(src)
    mh, master = sheet_rows(book["Master Sheet"])
    dh, data = sheet_rows(book["DATA"])
    kh, comments = sheet_rows(book["Comments"])
    m = {"id": find_col(mh, r"^Flex Number"), "date": find_col(mh, r"^Test Date"), "p": find_col(mh, r"^Pressure"),
         "o2": find_col(mh, r"^Oxygen"), "n2": find_col(mh, r"^Nitrogen"), "he": find_col(mh, r"^Helium"),
         "fiber": find_col(mh, r"^Fiber"), "fuel": find_col(mh, r"^Fuel")}
    d = {"id": find_col(dh, r"^Flex Number"), "d0": find_col(dh, r"^D0"), "dhot": find_col(dh, r"^Dext,\s*hot"),
         "khot": find_col(dh, r"^khot"), "kcool": find_col(dh, r"^kcool"), "dcool": find_col(dh, r"^Dext,\s*cool"),
         "p": find_col(dh, r"^Pressure \(atm"), "reign": find_col(dh, r"^Reignitions"),
         "extrap": find_col(dh, r"^Extrap"), "hf": find_col(dh, r"^HF Burn Time"), "done": find_col(dh, r"^Completed")}
    k_id, k_txt = find_col(kh, r"^Flex Number"), find_col(kh, r"^Comments")
    data_by = {r[d["id"]]: r for _, r in data}
    comment_by = {r[k_id]: r.get(k_txt, "") for _, r in comments}
    rel_src = rel(src)
    out = []
    for n, r in master:
        rep.d["rows_read"] += 1
        fid = r[m["id"]]
        if not fid:
            rep.drop("no Flex Number")
            continue
        flags: list[str] = []
        dr = data_by.get(fid)
        if dr is None:
            flags.append("no_DATA_row")
            dr = {}
        # Pressure: numeric atm in DATA; Master Sheet has text like '1 atm' / '.5 atm' (fallback).
        p_atm, p_raw, p_src = num(dr.get(d["p"])), dr.get(d["p"], ""), "DATA"
        if p_atm is None:
            p_atm, p_raw, p_src = num(r[m["p"]]), r[m["p"]], "Master Sheet"
        if p_atm is None or p_atm <= 0:
            rep.drop("pressure missing or 0")
            continue
        o2 = fraction_to_pct(num(r[m["o2"]]), flags, "o2")
        n2 = fraction_to_pct(num(r[m["n2"]]), flags, "n2")
        he = fraction_to_pct(num(r[m["he"]]), flags, "he")
        done = dr.get(d["done"], "").strip().lower() == "yes"
        dcool = num(dr.get(d["dcool"], "").strip())
        # Our reading of Dext,cool (CFI Final Report p. 6 + data; to confirm in Nayagam et al. 2015):
        #   > 0 -> cool flame went out early;  0 -> cool flame consumed the droplet;  blank -> not measured.
        cool_end = None if dcool is None else ("consumed_droplet" if dcool == 0 else "early_extinction")
        reign = num(dr.get(d["reign"]))
        if not done:
            flags.append("analysis_not_completed")
        out.append(finish_common({
            "investigation": "CFI", "psi_id": "PSI-39", "test_id": fid, "test_date": excel_date(r[m["date"]]),
            "fuel": r[m["fuel"]] or None, "fuel_type": "droplet",
            "o2_pct": rnd(o2), "o2_location": "chamber", "pressure_kpa": rnd(to_std(p_atm, "pressure", "atm"), 2),
            "n2_pct": rnd(n2), "co2_pct": 0.0, "he_pct": rnd(he), "diluent": diluent_of(0, he),
            "has_result": done,
            "fiber": r[m["fiber"]].lower() or None,
            "droplet_d0_mm": num(dr.get(d["d0"])), "dext_hot_mm": num(dr.get(d["dhot"])),
            "dext_cool_mm": dcool, "khot_mm2_s": num(dr.get(d["khot"])), "kcool_mm2_s": num(dr.get(d["kcool"])),
            "hf_burn_time_s": num(dr.get(d["hf"])),
            "reignitions": as_int(reign),
            "reignited": None if reign is None else reign > 0,
            "extrap_cool_flame": {"1": True, "0": False}.get(dr.get(d["extrap"], "").strip()),
            "cool_flame_end": cool_end, "analysis_complete": done,
            "comment": comment_by.get(fid, ""),
            "source_file": rel_src, "source_row": f"Master Sheet row {n}",
            "o2_raw": r[m["o2"]], "o2_raw_unit": "mole fraction",
            "pressure_raw": p_raw, "pressure_raw_unit": f"atm ({p_src})", "flags": flags,
        }))
    write("cfi", out, CFI_OWN, rep)
    return rep


# ================================================================ PART 2: tables without results

# ---------------------------------------------------------------- ACME Flame Design (PSI-10)

FD_NORMAL_OWN = ["flame_type", "day", "burner_fuel_pct", "fuel_flow_mg_s", "n2_flow_mg_s", "total_flow_mg_s",
                 "o2_final_pct", "pressure_init_kpa", "pressure_final_kpa", "zst", "tad_k_calculated"]
FD_INVERSE_OWN = ["flame_type", "day", "o2_flow_mg_s", "n2_flow_mg_s", "total_flow_mg_s", "chamber_fuel_pct",
                  "chamber_fuel_final_pct", "pressure_init_kpa", "pressure_final_kpa", "zst", "tad_k_calculated"]


def clean_flame_design(kind: str) -> Report:
    src = table_file("PSI-10", f"*Flame Design_{kind} Flame.csv")
    name = f"flame_design_{kind.lower()}"
    rep = Report(name, src)
    H, rows, enc = read_csv(src)
    rep.d["encoding"] = enc
    inverse = kind == "Inverse"
    c = {"type": find_col(H, r"^Flame Type"), "day": find_col(H, r"^Day$"), "test": find_col(H, r"^Test$"),
         "mn2": find_col(H, r"^mN2"), "mtot": find_col(H, r"^mtot"), "pinit": find_col(H, r"^pinit"),
         "pfinal": find_col(H, r"^pfinal"), "pmean": find_col(H, r"^pmean"), "zst": find_col(H, r"Zst"),
         "tad": find_col(H, r"^Tad")}
    if inverse:
        c |= {"o2": find_col(H, r"^XO2$"), "mo2": find_col(H, r"^mO2"),
              "xc": find_col(H, r"^XC2H4 initial"), "xcf": find_col(H, r"^XC2H4 final")}
    else:
        c |= {"fuel": find_col(H, r"^Fuel$"), "xfuel": find_col(H, r"^Xfuel"), "mfuel": find_col(H, r"^mfuel"),
              "o2": find_col(H, r"^XO2 \(init"), "o2f": find_col(H, r"^XO2 \(final")}
    dups = mark_duplicates([(n, r) for n, r in rows if not is_empty(r)])
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags: list[str] = []

        def f(col: str) -> float | None:
            # Text cells ('RAMP', 'RAMPED', 'LOW O2') are notes, not numbers: num('LOW O2') would read 2.
            v = r.get(col, "").strip()
            return None if re.search(r"[A-Za-z]{2,}", v) else num(v)

        texts = {v.strip().upper() for v in r.values()}
        if texts & {"RAMP", "RAMPED"}:
            flags.append("ramped_flow_values_empty")
        if "LOW O2" in texts:
            flags.append("low_o2_note_values_empty")
        # Mean pressure, else initial, else final (day 21301 only lists pinit).
        p_col = next((k for k in ("pmean", "pinit", "pfinal") if (f(c[k]) or 0) > 0), None)
        if p_col is None:
            rep.drop("pressure missing or 0")
            continue
        if p_col != "pmean":
            flags.append(f"pressure_from_{p_col}_no_pmean")
        p_atm = f(c[p_col])
        if n in dups:
            flags.append(f"duplicate_of_row_{dups[n]}")
            rep.d["duplicates_flagged"] += 1
        test = r[c["test"]]
        row = {
            "investigation": "ACME/Flame Design", "psi_id": "PSI-10", "test_id": test,
            "test_date": doy_date(test[:5]), "fuel_type": "gas",
            "o2_pct": rnd(fraction_to_pct(f(c["o2"]), flags, "o2")),
            "pressure_kpa": rnd(to_std(p_atm, "pressure", "atm"), 2),
            "co2_pct": 0.0, "he_pct": 0.0, "diluent": "N2",
            "flame_type": r[c["type"]], "day": r[c["day"]],
            "n2_flow_mg_s": f(c["mn2"]), "total_flow_mg_s": f(c["mtot"]),
            "pressure_init_kpa": rnd(to_std(f(c["pinit"]), "pressure", "atm"), 2),
            "pressure_final_kpa": rnd(to_std(f(c["pfinal"]), "pressure", "atm"), 2),
            "zst": f(c["zst"]), "tad_k_calculated": f(c["tad"]),
            "source_file": rel(src), "source_row": n,
            "o2_raw": r[c["o2"]], "o2_raw_unit": "mole fraction",
            "pressure_raw": r[c[p_col]], "pressure_raw_unit": f"atm ({p_col})", "flags": flags,
        }
        if inverse:
            flags.append("o2_is_burner_stream")
            row |= {"fuel": "C2H4", "o2_location": "burner_stream", "o2_flow_mg_s": f(c["mo2"]),
                    "chamber_fuel_pct": rnd(fraction_to_pct(f(c["xc"]), flags, "xc2h4")),
                    "chamber_fuel_final_pct": rnd(fraction_to_pct(f(c["xcf"]), flags, "xc2h4_final"))}
        else:
            row |= {"fuel": r[c["fuel"]] or None, "o2_location": "chamber",
                    "burner_fuel_pct": rnd(fraction_to_pct(f(c["xfuel"]), flags, "xfuel")),
                    "fuel_flow_mg_s": f(c["mfuel"]),
                    "o2_final_pct": rnd(fraction_to_pct(f(c["o2f"]), flags, "o2_final"))}
        out.append(finish_common(row))
    write(name, out, FD_INVERSE_OWN if inverse else FD_NORMAL_OWN, rep)
    return rep


# ---------------------------------------------------------------- ACME BRE (PSI-20): one row per test day

BRE_OWN = ["burner_size_mm", "fuel_bottle", "burner_fuel_pct", "flames_ignited", "o2_values_pct", "notes"]


def clean_bre() -> Report:
    src = table_file("PSI-20", "*BRE*.csv")
    rep = Report("bre", src)
    H, rows, enc = read_csv(src)
    c = {"y": find_col(H, r"^Year"), "m": find_col(H, r"^Month"), "d": find_col(H, r"^Date$"),
         "burner": find_col(H, r"^Burner Size"), "bottle": find_col(H, r"^Fuel Bottle"),
         "o2": find_col(H, r"^Oxygen Conc"), "ign": find_col(H, r"^Flames Ignited"), "notes": find_col(H, r"^Notes")}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags = ["pressure_varied_not_recorded"]  # per the table's own note
        o2s = pct_values(r[c["o2"]], flags)
        lo, hi = span(o2s)
        fuel, pct = parse_gas_fuel(r[c["bottle"]])
        day = ymd_date(r[c["y"]], r[c["m"]], r[c["d"]])
        ign = as_int(num(r[c["ign"]]))
        out.append(finish_common({
            "investigation": "ACME BRE", "psi_id": "PSI-20", "test_id": day or f"row{n}", "test_date": day,
            "row_granularity": "test_day", "n_tests": ign,
            "fuel": fuel, "fuel_type": "gas",
            "o2_pct": o2s[0] if len(o2s) == 1 else None, "o2_min_pct": lo, "o2_max_pct": hi,
            "o2_location": "chamber", "co2_pct": 0.0, "he_pct": 0.0, "diluent": "N2",
            "burner_size_mm": num(r[c["burner"]]), "fuel_bottle": r[c["bottle"]], "burner_fuel_pct": pct,
            "flames_ignited": ign, "o2_values_pct": fmt_list(o2s), "notes": r[c["notes"]],
            "source_file": rel(src), "source_row": n,
            "o2_raw": r[c["o2"]], "o2_raw_unit": "% (list of values used that day)", "flags": flags,
        }))
    write("bre", out, BRE_OWN, rep)
    return rep


# ---------------------------------------------------------------- ACME CLD (PSI-21): one row per test day

CLD_OWN = ["test_type", "fuel_bottle_raw", "burner_fuel_pct", "fuel_mfc_slpm", "n2_mfc_slpm",
           "burner_fuel_min_pct", "burner_fuel_max_pct", "flames_ignited"]


def fix_fuel_formula(formula: str | None, flags: list[str]) -> str | None:
    """The CLD sheet auto-incremented formulas when filled down: CH5…CH14 -> CH4, C2H5…C2H11 -> C2H4."""
    if not formula:
        return formula
    for good, rx in (("CH4", r"CH\d+"), ("C2H4", r"C2H\d+")):
        if re.fullmatch(rx, formula) and formula != good:
            flags.append(f"fuel_typo_{formula}_read_as_{good}")
            return good
    return formula


def clean_cld() -> Report:
    src = table_file("PSI-21", "*CLD*.csv")
    rep = Report("cld", src)
    H, rows, enc = read_csv(src)
    c = {"type": find_col(H, r"^Test Type"), "day": find_col(H, r"^Test Day"), "fmfc": find_col(H, r"^Fuel MFC"),
         "nmfc": find_col(H, r"^N2 MFC"), "bottle": find_col(H, r"^Fuel Bottle"),
         "conc": find_col(H, r"^Fuel conc"), "ign": find_col(H, r"^Flames ignited")}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags = ["o2_pressure_not_recorded"]
        formula, pct = parse_gas_fuel(r[c["bottle"]])
        formula = fix_fuel_formula(formula, flags)
        lo, hi = span(nums(r[c["conc"]]))
        ign = as_int(num(r[c["ign"]]))
        out.append(finish_common({
            "investigation": "ACME CLD Flame", "psi_id": "PSI-21", "test_id": r[c["day"]],
            "test_date": doy_date(r[c["day"]]), "row_granularity": "test_day", "n_tests": ign,
            "fuel": formula, "fuel_type": "gas", "o2_location": "chamber",
            "test_type": r[c["type"]], "fuel_bottle_raw": r[c["bottle"]], "burner_fuel_pct": pct,
            "fuel_mfc_slpm": num(r[c["fmfc"]]), "n2_mfc_slpm": num(r[c["nmfc"]]),
            "burner_fuel_min_pct": lo, "burner_fuel_max_pct": hi, "flames_ignited": ign,
            "source_file": rel(src), "source_row": n, "flags": flags,
        }))
    write("cld", out, CLD_OWN, rep)
    return rep


# ---------------------------------------------------------------- ACME E-FIELD (PSI-22): one row per test day

EF_OWN = ["test_type", "mesh_polarity", "fuel_bottle", "burner_fuel_pct", "burner_fuel_values_pct", "flames_ignited"]


def clean_efield() -> Report:
    src = table_file("PSI-22", "*E-FIELD*.csv")
    rep = Report("efield", src)
    H, rows, enc = read_csv(src)
    c = {"type": find_col(H, r"^Test Type"), "day": find_col(H, r"^Test Day"), "y": find_col(H, r"^Year"),
         "m": find_col(H, r"^Month"), "d": find_col(H, r"^Date$"), "pol": find_col(H, r"^Mesh Polarity"),
         "bottle": find_col(H, r"^Fuel Bottle"), "conc": find_col(H, r"^Fuel Conc"),
         "ign": find_col(H, r"^Flames Ignited")}
    # Rows with an empty Test Day only add another fuel concentration to the day above: merge them.
    groups: list[dict] = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        if not r[c["day"]].strip():
            if groups:
                groups[-1]["concs"] += nums(r[c["conc"]])
                rep.drop("continuation row merged into the day above")
            else:
                rep.drop("continuation row without a day")
            continue
        groups.append({"n": n, "r": r, "concs": nums(r[c["conc"]])})
    seen: dict[tuple, int] = {}
    out = []
    for g in groups:
        r, n = g["r"], g["n"]
        flags = ["o2_pressure_not_recorded"]
        ign = as_int(num(r[c["ign"]]))
        key = (r[c["day"]], r[c["pol"]], r[c["bottle"]], tuple(g["concs"]), r[c["ign"]])
        n_tests = ign
        if key in seen:
            flags.append(f"duplicate_of_row_{seen[key]}_not_counted")
            rep.d["duplicates_flagged"] += 1
            n_tests = 0
        else:
            seen[key] = n
        fuel, pct = parse_gas_fuel(r[c["bottle"]])
        out.append(finish_common({
            "investigation": "ACME E-FIELD Flames", "psi_id": "PSI-22", "test_id": r[c["day"]],
            "test_date": ymd_date(r[c["y"]], r[c["m"]], r[c["d"]]) or doy_date(r[c["day"]]),
            "row_granularity": "test_day", "n_tests": n_tests,
            "fuel": fuel, "fuel_type": "gas", "o2_location": "chamber",
            "test_type": r[c["type"]], "mesh_polarity": r[c["pol"]], "fuel_bottle": r[c["bottle"]],
            "burner_fuel_pct": pct, "burner_fuel_values_pct": fmt_list(g["concs"]), "flames_ignited": ign,
            "source_file": rel(src), "source_row": n, "flags": flags,
        }))
    write("efield", out, EF_OWN, rep)
    return rep


# ---------------------------------------------------------------- ACME s-Flame (PSI-23): one row per test day

SF_OWN = ["test_type", "atmosphere_raw", "fuel_bottle", "flames_ignited"]


def clean_sflame() -> Report:
    src = table_file("PSI-23", "*s-Flame*.csv")
    rep = Report("sflame", src)
    H, rows, enc = read_csv(src)
    c = {"type": find_col(H, r"^Test Type"), "day": find_col(H, r"^Test Day"), "y": find_col(H, r"^Year"),
         "m": find_col(H, r"^Month"), "d": find_col(H, r"^Date$"), "atm": find_col(H, r"^Atmosphere"),
         "bottle": find_col(H, r"^Fuel Bottle"), "ign": find_col(H, r"^Flames Ignited")}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        atm = r[c["atm"]]
        # The table's note: "Atmosphere is ~1 atm but pressure increases and O2% drops with vitiation."
        flags = ["pressure_about_1_atm_per_table_note"]
        if "~" in atm:
            flags.append("o2_approximate")
        if re.search(r"with N[3-9]\b", atm):
            flags.append("diluent_typo_read_as_N2")
        o2s = [float(v) for v in re.findall(r"(\d+(?:\.\d+)?)\s*%", atm)]  # only 'NN%' values, not O2 / N3
        lo, hi = span(o2s)
        ign = as_int(num(r[c["ign"]]))
        out.append(finish_common({
            "investigation": "ACME s-Flame", "psi_id": "PSI-23", "test_id": r[c["day"]],
            "test_date": ymd_date(r[c["y"]], r[c["m"]], r[c["d"]]) or doy_date(r[c["day"]]),
            "row_granularity": "test_day", "n_tests": ign,
            "fuel": r[c["bottle"]] or None, "fuel_type": "gas",
            "o2_pct": o2s[0] if len(o2s) == 1 else None, "o2_min_pct": lo, "o2_max_pct": hi,
            "o2_location": "chamber",
            "pressure_kpa": ONE_ATM_KPA, "pressure_assumed": True,
            "diluent": "He" if re.search(r"\bHe\b", atm) else "N2",
            "test_type": r[c["type"]], "atmosphere_raw": atm, "fuel_bottle": r[c["bottle"]], "flames_ignited": ign,
            "source_file": rel(src), "source_row": n,
            "o2_raw": atm, "o2_raw_unit": "% (approximate, text)",
            "pressure_raw": "~1 atm (table note)", "pressure_raw_unit": "atm", "flags": flags,
        }))
    write("sflame", out, SF_OWN, rep)
    return rep


# ---------------------------------------------------------------- airflow text (BASS / BASS-II)

def air_speeds(text: str, flags: list[str]) -> list[float]:
    """Airflow readings in cm/s from free text like '5  3  2 ext', '10 max', '2 <1', '5   3   pot 0.4'.

    'pot' numbers are fan potentiometer settings, not speeds: they are removed. Words like ext / blowoff /
    max are kept in the raw column for the outcome extraction later (predictor P9)."""
    t = text or ""
    if re.search(r"pot", t, re.IGNORECASE):
        flags.append("air_display_has_fan_pot_values")
        t = re.sub(r"pot\s*[\d.]+", " ", t, flags=re.IGNORECASE)      # 'pot 0.4'
        t = re.sub(r"[\d.]+\s*pot\b", " ", t, flags=re.IGNORECASE)     # '0.5 pot'
    t = re.sub(r"\([^)]*\)", " ", t)                                   # '(52)' = fan display in brackets
    if "<" in t:
        flags.append("air_display_has_below_values")
        t = t.replace("<", " ")
    return nums(t)


# ---------------------------------------------------------------- BASS-II (PSI-25)

B2_OWN = ["pi", "sample", "gmt_day", "flow_restrictor", "fan_display_raw", "air_display_raw",
          "o2_final_pct", "co2_final_pct", "co_initial_ppm", "co_final_ppm", "frames_shot"]


def co_ppm(s: str, flags: list[str], name: str) -> float | None:
    s = (s or "").strip()
    if s.upper() == "OR":
        flags.append(f"{name}_over_range_above_1000ppm")
        return None
    return None if s.lower() in ("", "none") else num(s)


def clean_bass2() -> Report:
    src = table_file("PSI-25", "*BASS-II*.csv")
    rep = Report("bass2", src)
    H, rows, enc = read_csv(src)
    c = {"pi": find_col(H, r"^PI$"), "test": find_col(H, r"^Test #"), "date": find_col(H, r"^Date$"),
         "gmt": find_col(H, r"^GMT$"), "sample": find_col(H, r"^Sample #"), "mat": find_col(H, r"Material"),
         "restr": find_col(H, r"^Flow restrictor"), "fan": find_col(H, r"^Fan display"),
         "air": find_col(H, r"^Air display"), "frames": find_col(H, r"^Total Frames"),
         "o2i": find_col(H, r"^Calibrated initial O2"), "o2f": find_col(H, r"^Calibrated final O2"),
         "co2i": find_col(H, r"^Initial CO2"), "co2f": find_col(H, r"^Final CO2"),
         "coi": find_col(H, r"^Initial CO \("), "cof": find_col(H, r"^Final CO \(")}
    dups = mark_duplicates([(n, r) for n, r in rows if not is_empty(r)])
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags = ["pressure_not_recorded"]
        if n in dups:
            flags.append(f"duplicate_of_row_{dups[n]}")
            rep.d["duplicates_flagged"] += 1
        speeds = air_speeds(r[c["air"]], flags)
        lo, hi = span(speeds)
        out.append(finish_common({
            "investigation": "BASS-II", "psi_id": "PSI-25", "test_id": r[c["test"]],
            "test_date": mdy_date(r[c["date"]]),
            "fuel": re.sub(r"\s+", " ", r[c["mat"]]).strip().lower() or None, "fuel_type": "solid",
            "o2_pct": num(r[c["o2i"]]), "o2_location": "chamber",
            "flow_cm_s": speeds[0] if speeds else None, "flow_min_cm_s": lo, "flow_max_cm_s": hi,
            "co2_pct": num(r[c["co2i"]]), "he_pct": 0.0, "diluent": "N2",
            "pi": r[c["pi"]], "sample": r[c["sample"]], "gmt_day": r[c["gmt"]],
            "flow_restrictor": r[c["restr"]],
            "fan_display_raw": r[c["fan"]],  # fan voltage x10: never a speed
            "air_display_raw": r[c["air"]],
            "o2_final_pct": num(r[c["o2f"]]), "co2_final_pct": num(r[c["co2f"]]),
            "co_initial_ppm": co_ppm(r[c["coi"]], flags, "co_initial"),
            "co_final_ppm": co_ppm(r[c["cof"]], flags, "co_final"),
            "frames_shot": r[c["frames"]],
            "source_file": rel(src), "source_row": n,
            "o2_raw": r[c["o2i"]], "o2_raw_unit": "% by vol (calibrated, initial)", "flags": flags,
        }))
    write("bass2", out, B2_OWN, rep)
    return rep


# ---------------------------------------------------------------- BASS (PSI-26): CSV + as-run workbook

BASS_OWN = ["as_run_test", "test_no", "sample_no", "gmt_day", "fan_display_raw", "air_display_raw",
            "co2_mmhg", "observations"]


def run_key(s) -> str:
    """'1' / '1.0' -> '1'. Anything that is not a plain number (notes, 'SETUP', '') -> '' (no key)."""
    s = str(s or "").strip()
    if not re.fullmatch(r"\d+(\.0+)?", s):
        return ""
    return str(int(float(s)))


def clean_bass() -> Report:
    src = table_file("PSI-26", "*BASS*.csv")
    wb_path = table_file("PSI-26", "*As Run_Test Matrix.xlsx", folder="docs")
    rep = Report("bass", src)
    rep.d["source_workbook"] = rel(wb_path)
    H, rows, enc = read_csv(src)
    c = {"date": find_col(H, r"^Date$"), "gmt": find_col(H, r"^GMT$"), "asrun": find_col(H, r"^As Run Test"),
         "testno": find_col(H, r"^Test #"), "sample": find_col(H, r"^Sample #"), "mat": find_col(H, r"Material")}
    wh, wrows = sheet_rows(read_xlsx(wb_path)["as run matrix"], header_pattern=r"as run test no")
    w = {"run": find_col(wh, r"^As run test no"), "fan": find_col(wh, r"^Fan display"),
         "air": find_col(wh, r"^Air display"), "o2": find_col(wh, r"^O2 % by volume"),
         "p": find_col(wh, r"^pressure, atm"), "co2": find_col(wh, r"^CO2, mm ?Hg"),
         "obs": find_col(wh, r"^Test Observations")}
    # A few test numbers appear twice in the workbook AND twice in the CSV (24, 85, 89, 90, 91).
    # Match them in order: the 1st CSV row with number k joins the 1st workbook row with k, the 2nd the 2nd.
    by_run: dict[str, list[tuple[int, dict]]] = {}
    for wn, wr in wrows:
        k = run_key(wr[w["run"]])
        if not k:
            continue
        if k in by_run:
            rep.d.setdefault("workbook_duplicate_test_numbers", []).append(f"{k} (rows {by_run[k][0][0]} and {wn})")
        by_run.setdefault(k, []).append((wn, wr))
    used: dict[str, int] = {}
    dups = mark_duplicates([(n, r) for n, r in rows if not is_empty(r)])
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        if not run_key(r[c["asrun"]]):
            rep.drop("no as-run test number (not a burn, e.g. soot cleaning)")
            continue
        flags: list[str] = []
        if n in dups:
            flags.append(f"duplicate_of_row_{dups[n]}")
            rep.d["duplicates_flagged"] += 1
        k = run_key(r[c["asrun"]])
        matches = by_run.get(k, [])
        i = used.get(k, 0)
        used[k] = i + 1
        if i < len(matches):
            wn, wr = matches[i]
            if len(matches) > 1:
                flags.append(f"repeated_test_number_matched_in_order_{i + 1}_of_{len(matches)}")
        elif matches:  # more CSV rows than workbook rows for this number: reuse the last, flagged
            wn, wr = matches[-1]
            flags.append("repeated_test_number_more_csv_rows_than_workbook_rows")
        else:
            wn, wr = None, {}
            flags.append("no_as_run_workbook_row")
        p_atm = num(wr.get(w["p"]))
        co2_mmhg = num(wr.get(w["co2"]))
        co2_pct = None
        if co2_mmhg is not None:
            co2_pct = co2_mmhg / ((p_atm or 1.0) * 760) * 100
            if p_atm is None:
                flags.append("co2_pct_assumes_1_atm")
        speeds = air_speeds(wr.get(w["air"], ""), flags)
        lo, hi = span(speeds)
        out.append(finish_common({
            "investigation": "BASS", "psi_id": "PSI-26", "test_id": r[c["asrun"]],
            "test_date": mdy_date(r[c["date"]]),
            "fuel": re.sub(r"\s+", " ", r[c["mat"]]).strip().lower() or None, "fuel_type": "solid",
            "o2_pct": rnd(fraction_to_pct(num(wr.get(w["o2"])), flags, "o2")), "o2_location": "chamber",
            "pressure_kpa": rnd(to_std(p_atm, "pressure", "atm"), 2),
            "flow_cm_s": speeds[0] if speeds else None, "flow_min_cm_s": lo, "flow_max_cm_s": hi,
            "co2_pct": rnd(co2_pct), "he_pct": 0.0, "diluent": "N2",
            "as_run_test": r[c["asrun"]], "test_no": r[c["testno"]], "sample_no": r[c["sample"]],
            "gmt_day": r[c["gmt"]], "fan_display_raw": wr.get(w["fan"], ""),
            "air_display_raw": wr.get(w["air"], ""), "co2_mmhg": co2_mmhg,
            "observations": wr.get(w["obs"], ""),
            "source_file": rel(src),
            "source_row": f"CSV row {n}" + (f"; workbook 'as run matrix' row {wn}" if wn else ""),
            "o2_raw": wr.get(w["o2"], ""), "o2_raw_unit": "fraction (as-run workbook)",
            "pressure_raw": wr.get(w["p"], ""), "pressure_raw_unit": "atm (as-run workbook)", "flags": flags,
        }))
    write("bass", out, BASS_OWN, rep)
    return rep


# ---------------------------------------------------------------- SAFFIRE I-III (PSI-98/99/100)

SAF_OWN = ["material", "thickness_raw", "length_raw", "width_raw", "flow_direction", "ignition_power_w",
           "ignition_time_s", "burn_time_s", "burn_time_raw", "ug_burn_length_raw", "ug_spread_rate_mm_s",
           "ug_spread_raw", "g1_burn_length_raw", "g1_spread_rate_mm_s", "g1_spread_raw"]


def mm_per_s(s: str) -> float | None:
    return num(s) if s and "mm/s" in s else None


def clean_saffire(number: int, psi: str) -> Report:
    roman = "I" * number
    src = table_file(psi, "*SAFFIRE*.csv")
    name = f"saffire{number}"
    rep = Report(name, src)
    H, rows, enc = read_csv(src)
    c = {"sample": find_col(H, r"^Sample Number"), "mat": find_col(H, r"^Material"),
         "thick": find_col(H, r"^Sam\w*le Thickness"), "length": find_col(H, r"^Sample Length"),
         "width": find_col(H, r"^Sample Width"), "flow": find_col(H, r"^Air Flow"),
         "dir": find_col(H, r"Direction"),
         "o2": find_col(H, r"^Percent O2", required=False), "ipw": find_col(H, r"^Ignition Power", required=False),
         "it": find_col(H, r"^Ignition Time", required=False), "bt": find_col(H, r"^Burn Time", required=False),
         "ugb": find_col(H, r"^(?!1-g).*-g Burn Length", required=False),
         "ugs": find_col(H, r"^(?!1-g).*-g Spread", required=False),
         "g1b": find_col(H, r"^1-g Burn Length", required=False),
         "g1s": find_col(H, r"^1-g Spread", required=False)}

    def g(key: str) -> str:
        return r.get(c[key], "") if c[key] else ""

    last_material = None
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        sample = r[c["sample"]]
        if re.match(r"^F\d+C\d", sample):
            rep.drop("flow-visualisation entry (not a burn)")
            continue
        if sample.lower().startswith("note"):
            rep.drop("note row")
            continue
        flags = ["pressure_not_recorded"]
        material = r[c["mat"]].strip()
        if not material and last_material:
            material = last_material
            flags.append("material_filled_down_from_row_above")
        last_material = material or last_material
        o2_text = g("o2")
        o2s = nums(o2_text)
        lo, hi = span(o2s)
        if "~" in o2_text:
            flags.append("o2_approximate")
        if c["o2"] and "Note 1" in c["o2"]:
            flags.append("o2_derived_from_co2_production")
        if not c["o2"]:
            flags.append("o2_not_recorded")
        # Saffire-I lists the 94 x 40.6 cm sheet as length 40.6 / width 94; the Saffire paper (p. 2) and the
        # Saffire-III table give length 94 / width 40.6, so put the larger value in length.
        length, width = r[c["length"]], r[c["width"]]
        if num(length) is not None and num(width) is not None and num(length) < num(width):
            length, width = width, length
            flags.append("length_width_swapped_in_source")
        # SIBAL fabric is 0.33 mm thick (Saffire paper, Table 1); Saffire-I/III write 0.37 / .33 with a cm unit.
        thick = r[c["thick"]]
        if "sibal" in material.lower() and ("(cm)" in c["thick"] or thick.strip().endswith("cm")):
            flags.append("thickness_unit_doubtful_fabric_is_about_0.33_mm")
        if re.match(r"^0\d", thick.strip()):
            flags.append("thickness_typo_leading_zero_probably_0.37_mm")
        bt_raw = g("bt")
        burn_time = num(bt_raw) if re.search(r"\d", bt_raw) else None
        ug_spread, g1_spread = mm_per_s(g("ugs")), mm_per_s(g("g1s"))
        out.append(finish_common({
            "investigation": f"SAFFIRE-{roman}", "psi_id": psi, "test_id": sample,
            "fuel": material.lower() or None, "fuel_type": "solid",
            "o2_pct": o2s[0] if o2s else None, "o2_min_pct": lo, "o2_max_pct": hi, "o2_location": "chamber",
            "flow_cm_s": num(r[c["flow"]]), "diluent": "N2",
            "has_result": bool(burn_time is not None or bt_raw or ug_spread is not None),
            "material": material, "thickness_raw": thick, "length_raw": length,
            "width_raw": width, "flow_direction": r[c["dir"]].strip(),
            "ignition_power_w": num(g("ipw")), "ignition_time_s": num(g("it")),
            "burn_time_s": burn_time, "burn_time_raw": bt_raw,
            "ug_burn_length_raw": g("ugb"), "ug_spread_rate_mm_s": ug_spread, "ug_spread_raw": g("ugs"),
            "g1_burn_length_raw": g("g1b"), "g1_spread_rate_mm_s": g1_spread, "g1_spread_raw": g("g1s"),
            "source_file": rel(src), "source_row": n,
            "o2_raw": o2_text, "o2_raw_unit": "%" if o2_text else "", "flags": flags,
        }))
    write(name, out, SAF_OWN, rep)
    return rep


# ---------------------------------------------------------------- SAME-R (PSI-101)

SAMER_OWN = ["description", "date_raw", "rt_r0_setting", "duration_s", "primary_aging_s",
             "primary_mixing_s", "net_aging_s"]


def clean_same_r() -> Report:
    src = table_file("PSI-101", "*SAME-R*.csv")
    rep = Report("same_r", src)
    H, rows, enc = read_csv(src)
    c = {"type": find_col(H, r"^Sample Type"), "test": find_col(H, r"^SAME Test"),
         "desc": find_col(H, r"^Description"), "date": find_col(H, r"^Date$"),
         "v": find_col(H, r"^Inlet velocity"), "rt": find_col(H, r"Rt/R0"), "dur": find_col(H, r"^Duration"),
         "pa": find_col(H, r"^Primary aging"), "pm": find_col(H, r"^Primary mixing"),
         "na": find_col(H, r"^Net aging")}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags = ["o2_pressure_not_recorded"]
        test = r[c["test"]].strip()
        aged = re.fullmatch(r"\d+[a-z]", test) is not None
        if aged:
            flags.append(f"aged_remeasurement_of_test_{test[:-1]}")
        out.append(finish_common({
            "investigation": "SAME-R", "psi_id": "PSI-101", "test_id": test,
            "row_granularity": "aged_measurement" if aged else "test", "n_tests": 0 if aged else 1,
            "fuel": r[c["type"]].lower() or None, "fuel_type": "smoke",
            "flow_cm_s": num(r[c["v"]]),
            "description": r[c["desc"]], "date_raw": r[c["date"]],
            "rt_r0_setting": r[c["rt"]],  # heater resistance ratio: a setting, not a temperature
            "duration_s": num(r[c["dur"]]), "primary_aging_s": num(r[c["pa"]]),
            "primary_mixing_s": num(r[c["pm"]]), "net_aging_s": num(r[c["na"]]),
            "source_file": rel(src), "source_row": n, "flags": flags,
        }))
    write("same_r", out, SAMER_OWN, rep)
    return rep


# ---------------------------------------------------------------- SAME (PSI-102)

SAME_OWN = ["material", "weight_loss_mg_per_min", "aging_s"]


def clean_same() -> Report:
    src = table_file("PSI-102", "*SAME.csv")
    rep = Report("same", src)
    H, rows, enc = read_csv(src)
    c = {"sample": find_col(H, r"^Sample #"), "mat": find_col(H, r"^Sample Material"),
         "flow": find_col(H, r"^Air Flow"), "wl": find_col(H, r"^Weight loss"), "ag": find_col(H, r"^Aging")}
    real = [(n, r) for n, r in rows if not is_empty(r) and ":" not in r[c["mat"]]]
    base_lo, base_hi = span([v for _, r in real if (v := num(r[c["flow"]])) is not None])
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags = ["o2_pressure_not_recorded"]
        text = r[c["mat"]]
        same_as = ":" in text
        material = text.split(":")[0].strip()
        row = {"investigation": "SAME", "psi_id": "PSI-102", "test_id": r[c["sample"]],
               "fuel": material.lower() or None, "fuel_type": "smoke", "material": material,
               "source_file": rel(src), "source_row": n, "flags": flags}
        if same_as:
            # "Kapton: same conditions as 1-4": conditions copied from rows 1-4, number of runs not stated.
            flags.append("conditions_same_as_samples_1_4")
            row |= {"row_granularity": "same_as_samples_1_4", "n_tests": None,
                    "flow_min_cm_s": base_lo, "flow_max_cm_s": base_hi}
        else:
            row |= {"flow_cm_s": num(r[c["flow"]]), "weight_loss_mg_per_min": num(r[c["wl"]]),
                    "aging_s": rnd(to_std(num(r[c["ag"]]), "time", "min"), 1)}
        out.append(finish_common(row))
    write("same", out, SAME_OWN, rep)
    return rep


# ---------------------------------------------------------------- SLICE (PSI-106): one row per test day

SLICE_OWN = ["fuel_label", "burner_fuel_pct", "notes"]


def clean_slice() -> Report:
    src = table_file("PSI-106", "*Slice*.csv")
    rep = Report("slice", src)
    H, rows, enc = read_csv(src)
    c = {"date": find_col(H, r"^Test Date"), "fuel": find_col(H, r"^Fuel Type")}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags = ["o2_pressure_not_recorded", "flames_per_day_not_recorded"]
        m = re.search(r"(\d{4})-([A-Za-z]{3})-(\d{1,2})", r[c["date"]])
        day = ymd_date(m.group(1), m.group(2), m.group(3)) if m else None
        formula, pct = parse_gas_fuel(r[c["fuel"]])
        extra = re.sub(r"\d{4}-[A-Za-z]{3}-\d{1,2}", "", r[c["date"]]).strip()
        out.append(finish_common({
            "investigation": "SLICE", "psi_id": "PSI-106", "test_id": day or f"row{n}", "test_date": day,
            "row_granularity": "test_day", "n_tests": None,
            "fuel": formula, "fuel_type": "gas", "o2_location": "chamber",
            "fuel_label": r[c["fuel"]], "burner_fuel_pct": pct,
            "notes": " | ".join(x for x in (extra, r[c["fuel"]]) if x),
            "source_file": rel(src), "source_row": n, "flags": flags,
        }))
    write("slice", out, SLICE_OWN, rep)
    return rep


# ---------------------------------------------------------------- SPICE (PSI-107)

SPICE_OWN = ["gmt_day", "ignition_gmt", "flame_off_gmt", "nozzle_mm", "fuel_rate_sccm", "fuel_rate_mg_s",
             "hc_fuel_rate_mg_s"]


def clean_spice() -> Report:
    src = table_file("PSI-107", "*Spice*.csv")
    rep = Report("spice", src)
    H, rows, enc = read_csv(src)
    c = {"day": find_col(H, r"^GMT date"), "ign": find_col(H, r"^GMT ignition"), "off": find_col(H, r"Flame Off"),
         "fuel": find_col(H, r"^Fuel$"), "noz": find_col(H, r"^Nozzle"), "sccm": find_col(H, r"^Fuel Rate \(sccm"),
         "mgs": find_col(H, r"^Fuel Rate \(mg"), "hc": find_col(H, r"^HC Fuel Rate"), "air": find_col(H, r"^Air Rate")}
    dups = mark_duplicates([(n, r) for n, r in rows if not is_empty(r)])
    first_row_of_flame: dict[tuple, int] = {}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        # SPICE Final Report, Table 1 note: conditions of 298 K, 101 kPa and 21 +/- 1 % O2 (ISS cabin air in MSG).
        flags = ["o2_pressure_from_spice_report_table1_note"]
        if n in dups:
            flags.append(f"duplicate_of_row_{dups[n]}")
            rep.d["duplicates_flagged"] += 1
        flow = num(r[c["air"]])
        if flow is not None and flow < 0:
            # e.g. -0.28 (probe offset at zero coflow) or -5.92 (loss-of-signal rows): not a real speed
            flags.append(f"negative_air_rate_{r[c['air']]}_not_used")
            flow = None
        flame = (r[c["day"]], r[c["ign"]])
        if r[c["ign"]].strip().upper() == "LOS":
            # Loss of signal: no ignition time, so rows cannot be grouped into flames.
            flags.append("loss_of_signal_flame_unknown")
            granularity, n_tests = "measurement", None
        elif flame in first_row_of_flame:
            flags.append(f"same_flame_as_row_{first_row_of_flame[flame]}")
            granularity, n_tests = "measurement", 0
        else:
            first_row_of_flame[flame] = n
            granularity, n_tests = "test", 1
        out.append(finish_common({
            "investigation": "SPICE", "psi_id": "PSI-107", "test_id": f"GMT{r[c['day']]}-{r[c['ign']]}",
            "row_granularity": granularity, "n_tests": n_tests,
            "fuel": r[c["fuel"]].lower() or None, "fuel_type": "gas",
            "o2_pct": 21.0, "o2_assumed": True, "o2_location": "chamber",
            "pressure_kpa": 101.0, "pressure_assumed": True,
            "flow_cm_s": flow, "diluent": "N2",
            "gmt_day": r[c["day"]], "ignition_gmt": r[c["ign"]], "flame_off_gmt": r[c["off"]],
            "nozzle_mm": num(r[c["noz"]]), "fuel_rate_sccm": num(r[c["sccm"]]),
            "fuel_rate_mg_s": num(r[c["mgs"]]), "hc_fuel_rate_mg_s": num(r[c["hc"]]),
            "source_file": rel(src), "source_row": n,
            "o2_raw": "21 +/- 1 % (report)", "o2_raw_unit": "%",
            "pressure_raw": "101 kPa (report)", "pressure_raw_unit": "kPa", "flags": flags,
        }))
    write("spice", out, SPICE_OWN, rep)
    return rep


# ---------------------------------------------------------------- DAFT (PSI-47): dust sessions, not fires

DAFT_OWN = ["session", "actual_day", "hardware", "sample_material", "sampled_location"]


def clean_daft() -> Report:
    src = table_file("PSI-47", "*DAFT*.csv")
    rep = Report("daft", src)
    H, rows, enc = read_csv(src)
    c = {"s": find_col(H, r"^Session"), "day": find_col(H, r"^Actual Day"), "hw": find_col(H, r"^Hardware"),
         "mat": find_col(H, r"^Sample Material"), "loc": find_col(H, r"^Sampled Location")}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        out.append(finish_common({
            "investigation": "DAFT / DAFT-2", "psi_id": "PSI-47", "test_id": r[c["s"]],
            "row_granularity": "session", "n_tests": 0, "fuel_type": "smoke",
            "session": r[c["s"]], "actual_day": r[c["day"]], "hardware": r[c["hw"]],
            "sample_material": r[c["mat"]], "sampled_location": r[c["loc"]],
            "source_file": rel(src), "source_row": n, "flags": ["not_a_fire_test"],
        }))
    write("daft", out, DAFT_OWN, rep)
    return rep


# ---------------------------------------------------------------- FLEX-2 (PSI-68): planned ranges, not tests

FLEX2_OWN = ["fuel_label", "droplet_d0_min_mm", "droplet_d0_max_mm", "gas_mixture", "o2_values_pct",
             "pressure_values_kpa", "ambient_temp_k"]


def clean_flex2() -> Report:
    src = table_file("PSI-68", "*Flex2*.csv")
    rep = Report("flex2", src)
    H, rows, enc = read_csv(src)
    c = {"fuel": find_col(H, r"^Sample"), "d0": find_col(H, r"^Initial Droplet"),
         "mix": find_col(H, r"^Ambient Gas"), "o2": find_col(H, r"^Oxygen Mole"),
         "p": find_col(H, r"^Ambient Pressure"), "t": find_col(H, r"^Ambient Temperature"),
         "flow": find_col(H, r"^Flow Velocity")}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        flags = ["planned_conditions_not_individual_tests"]
        o2s = [to_std(v, "gas_fraction", "fraction") for v in nums(r[c["o2"]])]
        ps = [rnd(to_std(v, "pressure", "atm"), 2) for v in nums(r[c["p"]])]
        flows, d0s = nums(r[c["flow"]]), nums(r[c["d0"]])
        (olo, ohi), (plo, phi), (flo, fhi), (dlo, dhi) = span(o2s), span(ps), span(flows), span(d0s)
        mix = r[c["mix"]]
        out.append(finish_common({
            "investigation": "FLEX-2", "psi_id": "PSI-68", "test_id": f"plan-{n}",
            "row_granularity": "planned_range", "n_tests": None,
            "fuel": r[c["fuel"]].lower() or None, "fuel_type": "droplet",
            "o2_min_pct": olo, "o2_max_pct": ohi, "o2_location": "chamber",
            "pressure_min_kpa": plo, "pressure_max_kpa": phi,
            "flow_min_cm_s": flo, "flow_max_cm_s": fhi,
            "diluent": "N2 or He" if "He" in mix else "N2",
            "fuel_label": r[c["fuel"]], "droplet_d0_min_mm": dlo, "droplet_d0_max_mm": dhi,
            "gas_mixture": mix, "o2_values_pct": fmt_list(o2s), "pressure_values_kpa": fmt_list(ps),
            "ambient_temp_k": rnd(to_std(num(r[c["t"]]), "temperature", "°C"), 2),
            "source_file": rel(src), "source_row": n,
            "o2_raw": r[c["o2"]], "o2_raw_unit": "mole fraction (list)",
            "pressure_raw": r[c["p"]], "pressure_raw_unit": "atm (list)", "flags": flags,
        }))
    write("flex2", out, FLEX2_OWN, rep)
    return rep


# ---------------------------------------------------------------- PSI-142: figure references, not tests

P142_OWN = ["data_id", "description", "reference_url", "figure_id"]


def clean_psi142() -> Report:
    src = table_file("PSI-142", "*.csv")
    rep = Report("psi142", src)
    H, rows, enc = read_csv(src)
    c = {"id": find_col(H, r"^Data ID"), "desc": find_col(H, r"^Data Description"),
         "ref": find_col(H, r"^Reference"), "fig": find_col(H, r"^Figure")}
    out = []
    for n, r in rows:
        rep.d["rows_read"] += 1
        if is_empty(r):
            rep.drop("empty row")
            continue
        out.append(finish_common({
            "investigation": "PSI-142", "psi_id": "PSI-142", "test_id": r[c["id"]],
            "row_granularity": "reference", "n_tests": 0, "fuel_type": "ground", "gravity": "earth_lab",
            "data_id": r[c["id"]], "description": r[c["desc"]], "reference_url": r[c["ref"]],
            "figure_id": r[c["fig"]],
            "source_file": rel(src), "source_row": n, "flags": ["not_a_test_figure_reference"],
        }))
    write("psi142", out, P142_OWN, rep)
    return rep


# ================================================================ main

JOBS = [
    ("flex", clean_flex), ("cfig_normal", lambda: clean_cfig("Normal")),
    ("cfig_inverse", lambda: clean_cfig("Inverse")), ("cfi", clean_cfi),
    ("flame_design_normal", lambda: clean_flame_design("Normal")),
    ("flame_design_inverse", lambda: clean_flame_design("Inverse")),
    ("bre", clean_bre), ("cld", clean_cld), ("efield", clean_efield), ("sflame", clean_sflame),
    ("bass2", clean_bass2), ("bass", clean_bass),
    ("saffire1", lambda: clean_saffire(1, "PSI-98")), ("saffire2", lambda: clean_saffire(2, "PSI-99")),
    ("saffire3", lambda: clean_saffire(3, "PSI-100")),
    ("same_r", clean_same_r), ("same", clean_same), ("slice", clean_slice), ("spice", clean_spice),
    ("daft", clean_daft), ("flex2", clean_flex2), ("psi142", clean_psi142),
]


def main() -> int:
    reports, failures = [], 0
    for name, job in JOBS:
        try:
            reports.append(job().d)
        except Exception as e:  # report and continue with the other tables
            failures += 1
            print(f"FAILED {name}: {e!r}", file=sys.stderr)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    (CLEAN_DIR / "_report.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")

    print(f"{'table':21} {'read':>5} {'written':>7} {'tests':>5} {'?rows':>5} {'results':>7} "
          f"{'lunar':>5} {'dups':>4}  dropped")
    for r in reports:
        dropped = ", ".join(f"{k}: {v}" for k, v in r["dropped"].items()) or "-"
        print(f"{r['table']:21} {r['rows_read']:5} {r['rows_written']:7} {r['tests']:5} "
              f"{r['tests_unknown_rows']:5} {r['with_result']:7} {r['lunar_air']:5} "
              f"{r['duplicates_flagged']:4}  {dropped}")
    print(f"\ntests = fires counted (sum of n_tests); ?rows = rows whose number of fires is unknown.")
    print(f"Output in {CLEAN_DIR}  ({failures} failure(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
