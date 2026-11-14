"""Flame Lab, droplet: how a fuel droplet burns at a chosen air, read from the nearest NASA droplet tests.

Two ISS experiments, both on the same droplet rig (MDCA):
- FLEX (PSI-69): methanol and n-heptane. One phase: the visible ("hot") flame.
- CFI (PSI-39): n-dodecane and two dodecane / iso-dodecane blends. Two phases: the hot flame goes out, then a
  near-invisible COOL flame keeps burning the droplet at its own rate K_cool until it goes out or the droplet is gone.

No trained model. For the chosen fuel and diluent we take the 5 tests closest in O2, pressure and starting droplet
size and average (inverse-distance) their K, end sizes and endings. The droplet shrinks by the d² law,
d² = d0² - K·t, in each phase; `check` says how well that law gives each experiment's recorded burn time.
Outside the tested O2 / pressure / droplet-size range we return the nearest tests but no estimate.

FLEX `burning_rate_raw` is labelled 'mm' in the PSI table; its values behave as mm²/s (see `check`).
Flame size and the Earth (1 g) shape are NOT in the tables: the UI draws them as an illustration and says so.
"""

import math
import os
import urllib.parse
from functools import lru_cache

from database.connection import connect
from services import predictors
from services.coverage import LUNAR_O2_MIN, LUNAR_P_MAX, NEAR_LUNAR_P_MAX
from services.tests_query import PSI_FILE_URL

# UI fuel id -> (experiment, fuel name in the table, label)
FUELS = {
    "methanol": ("FLEX", "methanol", "Methanol"),
    "heptane": ("FLEX", "heptane", "n-Heptane"),
    "dodecane": ("CFI", "C12H26", "n-Dodecane"),
    "dodecane_iso25": ("CFI", "[.75]/[.25] C12H26/iso-dodecane", "Dodecane + 25 % iso-dodecane"),
    "dodecane_iso40": ("CFI", "[.60]/[.40] C12H26/iso-dodecane", "Dodecane + 40 % iso-dodecane"),
}
EXPERIMENTS = {
    "FLEX": {"psi": "PSI-69", "file": "flex.csv", "name": "FLEX (Flame Extinguishment Experiment)"},
    "CFI": {"psi": "PSI-39", "file": "cfi.csv", "name": "CFI (Cool Flames Investigation)"},
}
DILUENTS = ("N2", "CO2", "He")    # N2 = habitat-like air; CO2 / He were the suppressant tests
K_NEAREST = 5
SCALE = {"o2": 3.0, "logp": math.log(1.25), "d0": 1.0}   # one "step" of distance: 3 % O2, 25 % pressure, 1 mm
MEASURED, INTERPOLATED = 0.35, 1.5                      # nearest-test distance limits for the two labels
D0_MARGIN = 0.5                                         # mm beyond the tested droplet sizes still allowed

SQL = """
select test_id, fuel, diluent, o2_pct, pressure_kpa, source_file, source_row, extra
from tests where clean_file = %s and o2_pct is not null and pressure_kpa is not null
"""


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _row(exp, r):
    """One test in a shape shared by both experiments. Hot phase: d0 -> d_ext at K. Cool phase (CFI only)."""
    x = r["extra"] or {}
    if exp == "FLEX":
        hot = {"d0_mm": _num(x.get("droplet_d0_mm")), "d_ext_mm": _num(x.get("extinction_diameter_mm")),
               "k_mm2_s": _num(x.get("burning_rate_raw")), "burn_time_s": _num(x.get("burn_time_s")),
               "end": x.get("test_end")}
        cool = None
    else:
        k_cool = _num(x.get("kcool_mm2_s"))
        hot = {"d0_mm": _num(x.get("droplet_d0_mm")), "d_ext_mm": _num(x.get("dext_hot_mm")),
               "k_mm2_s": _num(x.get("khot_mm2_s")), "burn_time_s": _num(x.get("hf_burn_time_s")),
               "end": "cool_flame" if k_cool else "extinction"}
        cool = k_cool and {"k_mm2_s": k_cool, "d_end_mm": _num(x.get("dext_cool_mm")),
                           "end": x.get("cool_flame_end") or None,
                           "extrapolated": x.get("extrap_cool_flame") == "true"}
    meta = EXPERIMENTS[exp]
    name = os.path.basename(r["source_file"] or "")
    return {"test_id": r["test_id"], "experiment": exp, "fuel": r["fuel"], "diluent": r["diluent"],
            "o2_pct": r["o2_pct"], "pressure_kpa": r["pressure_kpa"], **hot, "cool": cool,
            "cite": f"NASA PSI {exp} table, row {r['source_row']}",
            "url": PSI_FILE_URL.format(psi=meta["psi"], file=urllib.parse.quote(name))}


@lru_cache(maxsize=2)
def _rows(exp: str) -> tuple:
    with connect() as conn:
        raw = conn.execute(SQL, (EXPERIMENTS[exp]["file"],)).fetchall()
    return tuple(_row(exp, r) for r in raw)


def _check(exp: str, rows) -> dict:
    """Does d² = d0² - K·t with the table's own K give the recorded (hot-flame) burn time? Ratio predicted / recorded."""
    ratios = sorted((r["d0_mm"] ** 2 - r["d_ext_mm"] ** 2) / r["k_mm2_s"] / r["burn_time_s"] for r in rows
                    if r["d0_mm"] and r["d_ext_mm"] is not None and (r["k_mm2_s"] or 0) > 0.05 and r["burn_time_s"])
    n = len(ratios)
    if not n:
        return {"n": 0, "text": ""}
    q = lambda f: round(ratios[min(n - 1, int(f * n))], 2)
    text = (f"{exp}: with each test's own K, the d² law gives a burn time {q(0.5)}× the recorded one "
            f"(middle 80 %: {q(0.1)}–{q(0.9)}×, {n} tests).")
    if exp == "CFI":
        text += " CFI's recorded hot-flame time likely includes ignition, so the law runs short."
    return {"n": n, "median": q(0.5), "p10": q(0.1), "p90": q(0.9), "text": text}


def _zone(o2, p):
    if o2 >= LUNAR_O2_MIN and p <= LUNAR_P_MAX:
        return "lunar"
    if o2 >= LUNAR_O2_MIN and p <= NEAR_LUNAR_P_MAX:
        return "near_lunar"
    return None


def _wavg(pairs):
    """Inverse-distance weighted average of (weight, value) pairs, None values skipped."""
    pairs = [(w, v) for w, v in pairs if v is not None]
    return sum(w * v for w, v in pairs) / sum(w for w, _ in pairs) if pairs else None


def _votes(pairs):
    votes = {}
    for w, v in pairs:
        if v:
            votes[v] = votes.get(v, 0) + w
    return max(votes, key=votes.get) if votes else None   # the pick only: vote shares are not probabilities


def _cool_estimate(near, w, d_hot):
    """The cool-flame phase, if most of the nearest tests (by weight) had one; else None."""
    with_cool = [(wi, r) for wi, (_, r) in zip(w, near) if r["cool"]]
    if sum(wi for wi, _ in with_cool) / sum(w) < 0.5:
        return None
    k = _wavg([(wi, r["cool"]["k_mm2_s"]) for wi, r in with_cool])
    end = _votes([(wi, r["cool"]["end"]) for wi, r in with_cool])
    # end size as a fraction of the size where the hot flame went out
    ratio = _wavg([(wi, r["cool"]["d_end_mm"] / r["d_ext_mm"]) for wi, r in with_cool
                   if r["cool"]["d_end_mm"] is not None and r["d_ext_mm"]])
    d_end = 0.0 if end == "consumed_droplet" or ratio is None else min(ratio, 1.0) * d_hot
    return {
        "share": round(sum(wi for wi, _ in with_cool) / sum(w), 2),
        "k_mm2_s": round(k, 3), "d_end_mm": round(d_end, 3),
        "burn_time_s": round((d_hot ** 2 - d_end ** 2) / k, 2),
        "end": end,
        "extrapolated_share": round(sum(wi for wi, r in with_cool if r["cool"]["extrapolated"]) / sum(w), 2),
    }


def _p6b(table_fuel, o2_pct, pressure_kpa, d0_mm):
    """CFI hot-flame end size / start size from the trained P6b model, when it gives a value here (else None).
    On held-out test days P6b has R² 0.43 against 0.06 for the 5-nearest average (models/NEAREST_VS_MODELS.md)."""
    try:
        r = predictors.run("P6b", {"fuel": table_fuel, "o2_pct": o2_pct, "pressure_kpa": pressure_kpa,
                                   "he_pct": 0, "droplet_d0_mm": d0_mm})
    except ValueError:
        return None
    a = r.get("answer")
    return a["value"] if a and r["trust"] != "outside" else None


def droplet(fuel: str, o2_pct: float, pressure_kpa: float, d0_mm: float, diluent: str = "N2") -> dict:
    exp, table_fuel, label = FUELS[fuel]
    rows = _rows(exp)
    fuel_rows = [r for r in rows if r["fuel"] == table_fuel]
    group = [r for r in fuel_rows if r["diluent"] == diluent]
    usable = [r for r in group if r["k_mm2_s"] and r["d0_mm"] and r["d_ext_mm"] is not None]

    def dist(r):
        return math.sqrt(((r["o2_pct"] - o2_pct) / SCALE["o2"]) ** 2
                         + (math.log(r["pressure_kpa"] / pressure_kpa) / SCALE["logp"]) ** 2
                         + ((r["d0_mm"] - d0_mm) / SCALE["d0"]) ** 2)

    near = sorted(((dist(r), r) for r in usable), key=lambda t: t[0])[:K_NEAREST]
    tested = None
    if usable:
        tested = {k: [round(min(r[k] for r in usable), 2), round(max(r[k] for r in usable), 2)]
                  for k in ("o2_pct", "pressure_kpa", "d0_mm")}
    inside = bool(tested) and (tested["o2_pct"][0] <= o2_pct <= tested["o2_pct"][1]
                               and tested["pressure_kpa"][0] <= pressure_kpa <= tested["pressure_kpa"][1]
                               and tested["d0_mm"][0] - D0_MARGIN <= d0_mm <= tested["d0_mm"][1] + D0_MARGIN)

    if not near or not inside or near[0][0] > INTERPOLATED:
        status = "outside"
    else:
        status = "measured" if near[0][0] <= MEASURED else "interpolated"

    estimate = None
    if status != "outside":
        w = [1 / (d + 0.05) for d, _ in near]
        k = _wavg([(wi, r["k_mm2_s"]) for wi, (_, r) in zip(w, near)])
        ratio = _wavg([(wi, r["d_ext_mm"] / r["d0_mm"]) for wi, (_, r) in zip(w, near)])
        end = _votes([(wi, r["end"]) for wi, (_, r) in zip(w, near)])
        ratio_source = "nearest tests"
        if exp == "CFI" and diluent == "N2":
            model_ratio = _p6b(table_fuel, o2_pct, pressure_kpa, d0_mm)
            if model_ratio is not None:
                ratio, ratio_source = model_ratio, "P6b model"
        d_ext = min(ratio, 1.0) * d0_mm
        estimate = {
            "k_mm2_s": round(k, 3), "d_ext_mm": round(d_ext, 3), "ext_ratio": round(ratio, 3),
            "ext_ratio_source": ratio_source,   # where the hot-flame end size comes from
            "burn_time_s": round((d0_mm ** 2 - d_ext ** 2) / k, 2),
            "end": end,
            "cool": _cool_estimate(near, w, d_ext) if exp == "CFI" else None,
        }
        if exp == "CFI":   # the hot flame always went out; did a cool flame follow in most nearby tests?
            estimate["end"] = "cool_flame" if estimate["cool"] else "extinction"

    meta = EXPERIMENTS[exp]
    return {
        "fuel": fuel, "fuel_label": label, "table_fuel": table_fuel, "experiment": exp, "diluent": diluent,
        "diluents": sorted({r["diluent"] for r in fuel_rows if r["diluent"]}),   # what was tested for this fuel
        "query": {"o2_pct": o2_pct, "pressure_kpa": pressure_kpa, "d0_mm": d0_mm},
        "zone": _zone(o2_pct, pressure_kpa),
        "status": status,       # measured | interpolated | outside (no estimate)
        "estimate": estimate,
        "nearest": [{**{k: r[k] for k in ("test_id", "o2_pct", "pressure_kpa", "d0_mm", "d_ext_mm", "k_mm2_s",
                                          "burn_time_s", "end", "cool", "cite", "url")},
                     "distance": round(d, 2)} for d, r in near],
        "tested_range": tested,
        "n_tests": len(group),
        "check": _check(exp, rows),
        "fuels": {k: v[2] for k, v in FUELS.items()},
        "ends": {"extinction": "the flame went out before the droplet was gone",
                 "disruption": "the droplet burst or broke apart",
                 "completion": "the droplet burned away completely",
                 "cool_flame": "the hot flame went out, then a near-invisible cool flame kept burning the droplet",
                 "early_extinction": "the cool flame went out before the droplet was gone",
                 "consumed_droplet": "the cool flame burned the droplet away"},
        "illustration": ["Flame size around the droplet is not in the NASA tables: drawn as an illustration. "
                         "The cool flame is almost invisible in reality; it is shown brightened.",
                         "Earth (1 g) shape: the droplet tests have no 1 g runs. The teardrop (3.5x taller than "
                         "wide, blue only at the base) is measured on NASA's photo of an n-heptane droplet burning "
                         "in 1 g (A Researcher's Guide to Combustion, 2015, Fig. 1); the flame stays within about "
                         "2 droplet diameters of a methanol droplet in 1 g against 4-5 in microgravity (Saufi et "
                         "al., Fuel, doi:10.1016/j.fuel.2020.119413). The burn timing shown is the microgravity "
                         "one. Moon and Mars gravity were never tested; they lie between the two shapes."],
        "source": {"cite": f"NASA PSI, {meta['name']} ({meta['psi']}) experimental table",
                   "url": f"https://psi.nasa.gov/physci/repo/data/investigations/{meta['psi']}"},
    }
