from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from services.tests_query import query_tests

router = APIRouter(tags=["tests"])


@router.get("/tests")
def tests(
    psi_id: str | None = Query(None, description="e.g. PSI-159"),
    fuel: str | None = Query(None, description="Part of the fuel name, e.g. butane"),
    fuel_type: Literal["solid", "droplet", "gas", "smoke", "ground"] | None = None,
    o2_min: float | None = Query(None, description="Chamber O2, %"),
    o2_max: float | None = Query(None, description="Chamber O2, %"),
    pressure_min_kpa: float | None = None,
    pressure_max_kpa: float | None = None,
    flow_min_cm_s: float | None = None,
    flow_max_cm_s: float | None = None,
    lunar_air: bool | None = Query(None, description="O2 >= 30% at <= 70.3 kPa"),
    has_result: bool | None = None,
    limit: int = Query(100, ge=1, le=500, description="Rows returned (totals always cover all matches)"),
) -> dict:
    """Test rows matching the filters (at least one): totals and ranges of all matches, the rows
    (each with its NASA table and row number), and the tables' links."""
    filters = {"psi_id": psi_id, "fuel": fuel, "fuel_type": fuel_type, "o2_min": o2_min, "o2_max": o2_max,
               "pressure_min_kpa": pressure_min_kpa, "pressure_max_kpa": pressure_max_kpa,
               "flow_min_cm_s": flow_min_cm_s, "flow_max_cm_s": flow_max_cm_s,
               "lunar_air": lunar_air, "has_result": has_result}
    result = query_tests(filters, max_rows=limit)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result
