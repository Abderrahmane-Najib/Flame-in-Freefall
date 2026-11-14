"""P10 overlay points from the Olson extraction (P9 stage 1).

data/psi/extracted/p9_olson.csv -> data/psi/extracted/p10_olson_points.csv

One test gives up to two points, as in report section 6.1.4.4 / Fig. 6.10:
  * the outcome point (quench / blowoff / extinguished_unclear) at the outcome flow
  * a 'stable' point at the last flow where a stable flame was observed
Both use the calibrated FINAL O2 (the boundary is a fit to final O2).
Flow: pot -> U via that day's fan calibration (scripts/fan_calibration.py); air display -> U = 1.0066 x air.
Stretch rate: a = 1.5 (U / r) sqrt(r / 0.318 cm)    (report Eq. 6.1 context, p. 83)

  python scripts/build_p10_points.py
"""
import csv
import datetime
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fan_calibration as fc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/psi/extracted/p9_olson.csv"
OUT = ROOT / "data/psi/extracted/p10_olson_points.csv"
R0_CM = 0.318
LOW_FLOW_CM_S = 1.0          # report: flows below ~1 cm/s are uncertain
SOOTED_DAYS = {209, 210}     # anemometer read ~40% low vs neighbouring days; next cal is "post soot cleaning"


def boundary_o2(a):
    """NASA Eq. 6.1: minimum O2 (%) for a PMMA rod at stretch rate a (1/s)."""
    return 6 * math.exp(-0.5 * a) + 0.0167 * a + 13.4


def doy(date):
    if not date:
        return None
    m, d, y = date.split("/")
    y = int(y) + (2000 if len(y) == 2 else 0)
    return datetime.date(y, int(m), int(d)).timetuple().tm_yday, y


def to_u(cal, row, raw):
    """(U, U_low, U_high, method, calibration day). U is None when only a range is known."""
    if raw in ("", None):
        return None, None, None, "", ""
    try:
        v = float(raw)
    except ValueError:
        return None, None, None, f"not numeric ('{raw}')", ""
    if row["outcome_flow_unit"] == "air_cm_s":
        u = v * fc.U_PER_AIR
        return u, u, u, "air display", ""
    day = doy(row["date"])
    if day is None or day[1] != 2014:
        return None, None, None, "no calibration for this date", ""
    restr = int(row["flow_restrictor"])
    u, method, used = fc.pot_to_u(cal, day[0], restr, v)
    if method == "below_calibration":
        return None, 0.0, fc.low_flow_ceiling(cal, restr), method, used
    return u, u, u, method, used


def stretch(u, rad):
    return 1.5 * (u / rad) * math.sqrt(rad / R0_CM) if u is not None else None


def main():
    cal = fc.load()
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    last_date = ""
    out = []
    for r in rows:
        r["date"] = r["date"] or last_date  # O3b shares O3a's date (blank in the table)
        last_date = r["date"]
        rad = float(r["rod_diameter_mm"]) / 20  # mm diameter -> cm radius
        o2 = float(r["o2_cal_final_pct"]) if r["o2_cal_final_pct"] else None
        pts = []
        if r["outcome"] in ("quench", "blowoff", "extinguished_unclear"):
            pts.append((r["outcome"], r["outcome_flow_raw"]))
        if r["last_stable_flow_raw"] or r["outcome"] == "keeps_burning":
            pts.append(("stable", r["last_stable_flow_raw"] or r["outcome_flow_raw"]))
        for kind, raw in pts:
            u, ulo, uhi, method, used = to_u(cal, r, raw)
            a, alo, ahi = stretch(u, rad), stretch(ulo, rad), stretch(uhi, rad)
            flags = []
            if u is not None and u < LOW_FLOW_CM_S:
                flags.append("U<1cm/s")
            if method == "below_calibration":
                flags.append("flow_range_only")
            d = doy(r["date"])
            if d and d[0] in SOOTED_DAYS and r["outcome_flow_unit"] == "pot":
                flags.append("sooted_anemometer_day")
            if r["reused"] == "True":
                flags.append("reused_sample")
            if r["confidence"] == "low":
                flags.append("low_confidence_label")
            if r["flow_direction"] == "":
                flags.append("flow_direction_unknown")
            out.append({
                "test_id": r["test_id"], "kind": kind, "flow_direction": r["flow_direction"],
                "rod_diameter_mm": r["rod_diameter_mm"], "flow_raw": raw, "flow_unit": r["outcome_flow_unit"],
                "u_cm_s": round(u, 3) if u is not None else "",
                "u_low_cm_s": round(ulo, 3) if ulo is not None else "",
                "u_high_cm_s": round(uhi, 3) if uhi is not None else "",
                "u_method": method, "calibration_day": used,
                "stretch_a_per_s": round(a, 3) if a else "",
                "stretch_a_low": round(alo, 3) if alo is not None else "",
                "stretch_a_high": round(ahi, 3) if ahi is not None else "",
                "o2_final_pct": o2,
                "boundary_o2_pct": round(boundary_o2(a), 2) if a else "",
                "o2_minus_boundary": round(o2 - boundary_o2(a), 2) if a and o2 else "",
                "flags": ";".join(flags), "source_page": r["source_page"],
            })
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), "points ->", OUT)
    for p in out:
        uu = p["u_cm_s"] if p["u_cm_s"] != "" else f"{p['u_low_cm_s']}-{p['u_high_cm_s']}"
        print(f"{p['test_id']:5s} {p['kind']:20s} U={str(uu):>9s} a={str(p['stretch_a_per_s']):>8s} "
              f"O2f={p['o2_final_pct']:5.1f} O2-boundary={str(p['o2_minus_boundary']):>6s} {p['flags']}")


if __name__ == "__main__":
    main()
