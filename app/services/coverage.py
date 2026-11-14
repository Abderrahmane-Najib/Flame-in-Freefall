"""O2 vs pressure coverage map (visual V1): one point per test row that has both chamber O2 and pressure,
plus the habitat boxes and the near-lunar band, so the map shows how thin the lunar evidence is.

Burner-stream O2 (CFI-G / Flame Design inverse flames) is left out: it is gas blown out of the burner,
not cabin air. Rows without a single O2 or pressure value (ranges, mixed rows) cannot be drawn as points.
"""

import os
import urllib.parse

from database.connection import connect
from services.habitats import list_habitats
from services.tests_query import PSI_FILE_URL

# Near-lunar (IDEAS.md §2): lunar O2 but just above the 70.3 kPa limit. Holds the 17 FLEX tests
# at 71.2-72.4 kPa and nothing else. Never call these "lunar".
LUNAR_O2_MIN, LUNAR_P_MAX, NEAR_LUNAR_P_MAX = 30.0, 70.3, 72.5

POINTS_SQL = """
select t.psi_id, i.name, t.fuel_type, t.fuel, t.o2_pct, t.pressure_kpa, t.n_tests, t.has_result, t.lunar_air,
       coalesce(t.o2_assumed, false) or coalesce(t.pressure_assumed, false) as assumed,
       t.source_file, t.source_row
from tests t join investigations i on i.id = t.psi_id
where t.o2_location is distinct from 'burner_stream' and t.o2_pct is not null and t.pressure_kpa is not null
order by t.psi_id, t.source_file, t.source_row
"""

LEFT_OUT_SQL = """
select count(*) filter (where o2_location = 'burner_stream') as burner_stream_rows,
       count(*) filter (where o2_location is distinct from 'burner_stream'
                        and (o2_pct is null or pressure_kpa is null)) as rows_without_single_value
from tests
"""


def _zone(o2: float, p: float) -> str | None:
    if o2 >= LUNAR_O2_MIN and p <= LUNAR_P_MAX:
        return "lunar"
    if o2 >= LUNAR_O2_MIN and LUNAR_P_MAX < p <= NEAR_LUNAR_P_MAX:
        return "near_lunar"
    return None


def coverage() -> dict:
    with connect() as conn:
        rows = conn.execute(POINTS_SQL).fetchall()
        left_out = conn.execute(LEFT_OUT_SQL).fetchone()

    tables, points = {}, []
    for r in rows:
        name = os.path.basename(r["source_file"] or "")
        tables[name] = PSI_FILE_URL.format(psi=r["psi_id"], file=urllib.parse.quote(name))
        points.append({
            "psi_id": r["psi_id"], "name": r["name"], "fuel_type": r["fuel_type"], "fuel": r["fuel"],
            "o2_pct": round(r["o2_pct"], 2), "pressure_kpa": round(r["pressure_kpa"], 2),
            "n_tests": r["n_tests"],          # fires in this row (null = unknown); most rows are 1 test
            "has_result": r["has_result"],
            "assumed": r["assumed"],          # O2 or pressure taken from a NASA document, not the table
            "zone": _zone(r["o2_pct"], r["pressure_kpa"]),
            "table": name, "row": r["source_row"],
        })

    def fires(zone):
        return sum(p["n_tests"] or 0 for p in points if p["zone"] == zone)

    return {
        "axes": {"x": "pressure_kpa", "y": "o2_pct"},
        "zones": {
            "habitats": [{"id": h["id"], "label": h["label"], "target": h["target"], "box": h["match"]}
                         for h in list_habitats()],
            "near_lunar": {"o2_pct": [LUNAR_O2_MIN, 100], "pressure_kpa": [LUNAR_P_MAX, NEAR_LUNAR_P_MAX],
                           "label": "Near-lunar (just above 70.3 kPa): not lunar air"},
        },
        "counts": {
            "points": len(points),
            "lunar_tests": fires("lunar"),
            "near_lunar_tests": fires("near_lunar"),
            **left_out,
        },
        "notes": ["Microgravity tests only: the Moon and Mars boxes show their air, not their gravity.",
                  "Burner-stream O2 of inverse flames is not cabin air and is not drawn.",
                  "assumed = O2 or pressure from a NASA document, not the test table (SPICE, s-Flame)."],
        "tables": tables,
        "points": points,
    }
