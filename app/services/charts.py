"""Charts for the assistant, built from the cleaned NASA test rows (never from numbers the model writes).

build_chart returns two things:
  spec     the full chart (every point, its table and row), streamed to the UI as a 'chart' event
  summary  a short text for the model (counts, ranges, source tables): the points never go back to it
"""

import os
import urllib.parse

from services import investigations, tests_query

# Test-row columns that can be an axis; any numeric result field (e.g. burn_time_s) works too.
COLUMNS = {"o2_pct": "Chamber O₂ (%)", "pressure_kpa": "Pressure (kPa)", "flow_cm_s": "Flow (cm/s)"}
UNITS = [("_mm2_s", "mm²/s"), ("_mm_s", "mm/s"), ("_mg_s", "mg/s"), ("_kpa", "kPa"), ("_pct", "%"),
         ("_mm", "mm"), ("_k", "K"), ("_s", "s")]
NAMES = {"khot_mm2_s": "Hot-flame burning rate K (mm²/s)", "kcool_mm2_s": "Cool-flame burning rate K (mm²/s)",
         "droplet_d0_mm": "Start droplet size (mm)", "dext_hot_mm": "Hot-flame end size (mm)",
         "dext_cool_mm": "Cool-flame end size (mm)", "hf_burn_time_s": "Hot-flame burn time (s)"}
FAMILIES = {"gas": "Gas flames", "droplet": "Liquid droplets", "solid": "Solid materials"}
MAX_BARS = 12


def _label(key: str) -> str:
    if key in COLUMNS or key in NAMES:
        return COLUMNS.get(key) or NAMES[key]
    for suffix, unit in UNITS:
        if key.endswith(suffix):
            return f"{key[:-len(suffix)].replace('_', ' ').capitalize()} ({unit})"
    return key.replace("_", " ").capitalize()


def _value(row: dict, key: str) -> float | None:
    if key == "o2_pct" and row["o2_location"] != "chamber":
        return None  # burner-stream O2 is not cabin air
    v = row.get(key) if key in COLUMNS else (row["extra"] or {}).get(key)
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _tables(rows: list[dict]) -> dict:
    out = {}
    for r in rows:
        name = os.path.basename(r["source_file"] or "")
        out[name] = tests_query.PSI_FILE_URL.format(psi=r["psi_id"], file=urllib.parse.quote(name))
    return out


def _scatter(rows: list[dict], x: str, y: str, group_by: str, title: str) -> tuple[dict, str]:
    pts, used = [], []
    for r in rows:
        vx, vy = _value(r, x), _value(r, y)
        if vx is not None and vy is not None:
            used.append(r)
            pts.append({"x": vx, "y": vy, "g": r[group_by] or "other", "psi": r["psi_id"],
                        "table": os.path.basename(r["source_file"] or ""), "row": r["source_row"]})
    if not pts:
        return None, f"No matching row has both {x} and {y}. Try other axes (result fields are listed in query_tests rows)."

    # Groups: the 3 fuel families, or the 3 most common fuels; everything else is 'Other' (palette has 3 hues).
    if group_by == "fuel_type":
        groups = [{"id": k, "label": v} for k, v in FAMILIES.items() if any(p["g"] == k for p in pts)]
    else:
        counts = {}
        for p in pts:
            counts[p["g"]] = counts.get(p["g"], 0) + 1
        groups = [{"id": k, "label": k} for k in sorted(counts, key=counts.get, reverse=True)[:3]]
    ids = {g["id"] for g in groups}
    for p in pts:
        if p["g"] not in ids:
            p["g"] = "other"
    if any(p["g"] == "other" for p in pts):
        groups.append({"id": "other", "label": "Other"})

    spec = {"kind": "scatter", "title": title, "x": {"key": x, "label": _label(x)}, "y": {"key": y, "label": _label(y)},
            "groups": groups, "points": pts, "tables": _tables(used), "skipped": len(rows) - len(pts)}
    xs, ys = [p["x"] for p in pts], [p["y"] for p in pts]
    # Medians of y in 4 equal x ranges: lets the model describe the trend from real numbers.
    lo, hi = min(xs), max(xs)
    step = (hi - lo) / 4 or 1
    bins = []
    for i in range(4):
        a, b = lo + i * step, lo + (i + 1) * step
        sel = sorted(p["y"] for p in pts if a <= p["x"] < b or (i == 3 and p["x"] == hi))
        if sel:
            bins.append(f"{_label(x)} {a:.3g}–{b:.3g}: {len(sel)} rows, median {sel[len(sel) // 2]:.3g}, "
                        f"range {sel[0]:.3g}–{sel[-1]:.3g}")
    summary = (f"Chart shown to the user: {len(pts)} test rows, x = {_label(x)} {lo:g}–{hi:g}, "
               f"y = {_label(y)} {min(ys):g}–{max(ys):g}. Colour = {group_by}: {', '.join(g['label'] for g in groups)}. "
               f"{spec['skipped']} matching rows had no value for an axis and are not drawn. "
               f"y by x range: {'; '.join(bins)}. Other conditions (droplet size, pressure, diluent) vary between rows.")
    return spec, summary + f" Source tables (cite them): {spec['tables']}"


def _bar(rows: list[dict], group_by: str, title: str) -> tuple[dict, str]:
    names = {i["id"]: i["name"] for i in investigations.list_investigations(None)} if group_by == "psi_id" else {}
    fires, unknown = {}, 0
    for r in rows:
        k = r[group_by] or "unknown"
        if r["n_tests"] is None:
            unknown += 1
        fires[k] = fires.get(k, 0) + (r["n_tests"] or 0)
    order = sorted(fires, key=fires.get, reverse=True)
    bars = [{"label": names.get(k, k), "id": k, "value": fires[k]} for k in order[:MAX_BARS]]
    if len(order) > MAX_BARS:
        bars.append({"label": f"{len(order) - MAX_BARS} others", "id": "other", "value": sum(fires[k] for k in order[MAX_BARS:])})
    spec = {"kind": "bar", "title": title, "x": {"label": "Fires (known test counts)"}, "bars": bars,
            "tables": _tables(rows), "unknown_rows": unknown}
    summary = (f"Chart shown to the user: fires per {group_by}: "
               + ", ".join(f"{b['label']} {b['value']}" for b in bars)
               + f". {unknown} matching rows have no recorded test count and are not counted."
               + f" Source tables (cite them): {spec['tables']}")
    return spec, summary


def build_chart(kind: str, filters: dict, x: str = "o2_pct", y: str = "pressure_kpa",
                group_by: str = "fuel_type", title: str = "") -> tuple[dict | None, str]:
    rows = tests_query.chart_rows(filters)
    if rows is None:
        return None, "Give at least one filter (e.g. fuel_type, psi_id, lunar_air)."
    if not rows:
        return None, "No test matches these filters: no chart."
    if kind == "bar":
        if group_by not in ("psi_id", "fuel", "fuel_type"):
            group_by = "psi_id"
        spec, summary = _bar(rows, group_by, title or f"Fires per {group_by}")
    else:
        if group_by not in ("fuel", "fuel_type"):
            group_by = "fuel_type"
        spec, summary = _scatter(rows, x, y, group_by, title or f"{_label(y)} vs {_label(x)}")
    if spec:  # shown under the chart, so the user sees exactly what was counted
        spec["filters"] = {k: v for k, v in filters.items() if v is not None}
    return spec, summary
