"""Filter the cleaned test rows with fixed filters (never free SQL). At least one filter is required,
so a call never returns a whole table: only the matching rows (capped), their counts and ranges.
"""

import os
import urllib.parse

from database.connection import connect

MAX_ROWS = 10
PSI_FILE_URL = "https://psi.nasa.gov/geode-py/ws/studies/{psi}/download?file={file}"

# filter name -> SQL condition; values are always passed as parameters
FILTERS = {
    "psi_id": "psi_id = %(psi_id)s",
    "fuel": "fuel ilike %(fuel)s",
    "fuel_type": "fuel_type = %(fuel_type)s",
    "o2_min": "o2_location = 'chamber' and o2_pct >= %(o2_min)s",
    "o2_max": "o2_location = 'chamber' and o2_pct <= %(o2_max)s",
    "pressure_min_kpa": "pressure_kpa >= %(pressure_min_kpa)s",
    "pressure_max_kpa": "pressure_kpa <= %(pressure_max_kpa)s",
    "flow_min_cm_s": "flow_cm_s >= %(flow_min_cm_s)s",
    "flow_max_cm_s": "flow_cm_s <= %(flow_max_cm_s)s",
    "lunar_air": "lunar_air = %(lunar_air)s",
    "has_result": "has_result = %(has_result)s",
}

TOTALS_SQL = """
select count(*) as rows, sum(n_tests) as fires, count(*) filter (where n_tests is null) as rows_fires_unknown,
       min(o2_pct) as o2_min, max(o2_pct) as o2_max,
       min(pressure_kpa) as pressure_min_kpa, max(pressure_kpa) as pressure_max_kpa,
       min(flow_cm_s) as flow_min_cm_s, max(flow_cm_s) as flow_max_cm_s
from tests where {where}
"""

ROWS_SQL = """
select psi_id, test_id, fuel, o2_pct, o2_location, pressure_kpa, flow_cm_s, diluent, lunar_air, has_result,
       source_file, source_row, extra
from tests where {where}
order by psi_id, source_file, source_row
limit %(limit)s
"""


def query_tests(filters: dict, max_rows: int = MAX_ROWS) -> dict:
    """max_rows: 10 for the assistant (token limit); the API allows more for tables and charts."""
    used = {k: v for k, v in filters.items() if k in FILTERS and v is not None}
    if not used:
        return {"error": "give at least one filter", "filters": list(FILTERS)}
    params = dict(used, limit=max_rows)
    if "fuel" in params:
        params["fuel"] = f"%{params['fuel']}%"
    where = " and ".join(FILTERS[k] for k in used)

    with connect() as conn:
        totals = conn.execute(TOTALS_SQL.format(where=where), params).fetchone()
        rows = conn.execute(ROWS_SQL.format(where=where), params).fetchall()

    # Each table's link once (rows only name their table and row), and no empty fields: keeps the result small.
    tables, slim = {}, []
    for r in rows:
        name = os.path.basename(r.pop("source_file") or "")
        tables[name] = PSI_FILE_URL.format(psi=r["psi_id"], file=urllib.parse.quote(name))
        r["table"], r["row"] = name, r.pop("source_row")
        r["results"] = {k: v for k, v in (r.pop("extra") or {}).items() if "raw" not in k}
        slim.append({k: v for k, v in r.items() if v is not None})

    return {
        "filters": used,
        "totals": totals,
        "tables": tables,  # cite a row as: NASA PSI test table <table>, row <row>, with this url
        "rows": slim,
        "more_rows": totals["rows"] > len(rows),  # true: add a filter to narrow it down
        "shown": f"{len(rows)} of {totals['rows']} matching rows"
                 + ("; the rest are NOT shown: do not generalise from these" if totals["rows"] > len(rows) else ""),
        "notes": "O2 filters use chamber O2 only (burner-stream O2 is not cabin air). "
                 "'fires' sums known test counts; rows_fires_unknown rows have no count.",
    }
