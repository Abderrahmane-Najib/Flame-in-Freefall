"""BASS-II fan calibration: fan pot setting -> flow velocity U (cm/s), per test day and flow restrictor count.

Source: data/psi/PSI-25/docs/PSI-25_Reference Data_Fan calibration data.xlsx (one sheet).
Layout: one 4-column block per calibration day (Pot | Fan Display | Air Display | blank), each
holding up to three sections in order: no restrictor, 1 restrictor, 2 restrictors.
U = 1.0066 x Air display (sheet footnote: SPICE calibration, duct centreline).

Rules from the sheet's note:
  * pot 0 (fan 3.8 V) is NOT a zero-flow point (the fan stops above 3.8 V), so it is never used.
  * not every day has every restrictor; then the nearest calibration day with that restrictor is used.
Below the lowest calibrated pot, U is NOT extrapolated: readings at pot 0.5 range from 0 to 3.8 cm/s
across days (anemometer resolution ~0.5-1 cm/s, ~1 min lag), so extrapolation gives arbitrary values.
Such flows are reported as a range (0, low_flow_ceiling]. Report section 6.1: flows < ~1 cm/s are uncertain.
"""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx_read import read_xlsx  # noqa: E402

XLSX = Path(__file__).resolve().parents[1] / "data/psi/PSI-25/docs/PSI-25_Reference Data_Fan calibration data.xlsx"
U_PER_AIR = 1.0066


def _f(s):
    try:
        return float(str(s).strip())
    except ValueError:
        return None


def _day_of_year(cell):
    """'41688' (Excel serial) or '7/31/2014 a.m.' -> 2014 day-of-year."""
    v = _f(cell)
    if v is not None:
        d = datetime.date(1899, 12, 30) + datetime.timedelta(days=int(v))
    else:
        m, d_, y = str(cell).split()[0].split("/")
        d = datetime.date(int(y), int(m), int(d_))
    return d.timetuple().tm_yday, d.isoformat()


def load():
    """{(doy, restrictors): {"date":..., "label":..., "points": [(pot, U), ...]}}"""
    rows = list(read_xlsx(XLSX).values())[0]
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    hdr = next(i for i, r in enumerate(rows) if str(r[0]).strip() == "Pot")
    out = {}
    for c in range(6, width):  # block 0 (cols 0-4) is the worked example, skip it
        if str(rows[hdr][c]).strip() != "Pot":
            continue
        date_row = next(i for i in range(hdr) if str(rows[i][c]).strip() == "DATE")
        doy, iso = _day_of_year(rows[date_row][c + 1])
        label = str(rows[date_row + 1][c + 1]).strip()
        sections, cur = [], None
        for r in rows[hdr + 1:]:
            pot = _f(r[c])
            if pot is None:
                if cur:
                    sections.append(cur)
                cur = None
                continue
            cur = cur or []
            cur.append((pot, _f(r[c + 2])))
        if cur:
            sections.append(cur)
        for n_restr, sec in enumerate(sections[:3]):
            pts = sorted({(p, a * U_PER_AIR) for p, a in sec if p > 0 and a is not None})
            if pts:
                key = (doy, n_restr)
                # a day can appear twice (e.g. 2014-188 post soot cleaning / end): keep the later block
                out[key] = {"date": iso, "label": label, "points": pts}
    return out


def pot_to_u(cal, doy, restrictors, pot):
    """(U cm/s, method, calibration day used). method: interpolated | below_calibration (U None)."""
    days = [d for d, r in cal if r == restrictors]
    if not days:
        return None, "no calibration for this restrictor count", None
    day = min(days, key=lambda d: (abs(d - doy), d))
    pts = cal[(day, restrictors)]["points"]
    used = cal[(day, restrictors)]["date"] + ("" if day == doy else " (nearest day)")
    for (p0, u0), (p1, u1) in zip(pts, pts[1:]):
        if p0 <= pot <= p1:
            return u0 + (u1 - u0) * (pot - p0) / (p1 - p0), "interpolated", used
    if pot > pts[-1][0]:
        return pts[-1][1], "above calibration (max used)", used
    return None, "below_calibration", used


def low_flow_ceiling(cal, restrictors, pot_max=0.5):
    """Highest U ever read at pot <= pot_max for this restrictor count (any day).
    Flows set below the calibrated range are only known to lie in (0, this value]."""
    us = [u for (d, r), v in cal.items() if r == restrictors for p, u in v["points"] if p <= pot_max]
    return max(us) if us else None


if __name__ == "__main__":
    cal = load()
    for (d, r), v in sorted(cal.items()):
        print(f"day {d:3d} {v['date']}  restrictors {r}  {v['label']:32s} " +
              ", ".join(f"{p:g}->{u:.1f}" for p, u in v["points"]))
