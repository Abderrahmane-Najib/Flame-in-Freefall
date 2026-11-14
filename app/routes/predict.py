from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from services import predictors
from services.droplet import droplet
from services.pmma import ROD_DIAMETERS_MM, boundary

router = APIRouter(prefix="/predict", tags=["predictors"])


@router.get("/pmma")
def pmma_boundary(
    rod_diameter_mm: float = Query(6.35, description="A rod BASS-II tested: 6.35, 9.53 or 12.7"),
    flow_cm_s: float | None = Query(None, gt=0, le=100, description="Slider: airflow speed"),
    o2_pct: float | None = Query(None, gt=0, le=100, description="Slider: oxygen in the air"),
) -> dict:
    """P10: will a PMMA (acrylic) rod keep burning in microgravity? NASA's fitted boundary (BASS-II Eq. 6.1)
    as a curve, the reference lines (13.5% µg, 15.4% Earth, 21% ISS, 30% Moon), the bounded Moon range,
    and, with the sliders, where the chosen flow and O2 fall."""
    if rod_diameter_mm not in ROD_DIAMETERS_MM:
        raise HTTPException(400, f"rod_diameter_mm must be one of {ROD_DIAMETERS_MM} (the rods BASS-II tested)")
    return boundary(rod_diameter_mm, flow_cm_s, o2_pct)


@router.get("/droplet")
def droplet_burn(
    fuel: Literal["methanol", "heptane", "dodecane", "dodecane_iso25", "dodecane_iso40"] = "methanol",
    o2_pct: float = Query(21, gt=0, le=100),
    pressure_kpa: float = Query(101.3, gt=0, le=400),
    d0_mm: float = Query(2.5, gt=0, le=10, description="Starting droplet diameter"),
    diluent: Literal["N2", "CO2", "He"] = "N2",
) -> dict:
    """Flame Lab: a burning fuel droplet in microgravity, from the 5 nearest NASA droplet tests: FLEX (PSI-69) for
    methanol / heptane, CFI (PSI-39) for dodecane and its blends, which adds the cool-flame phase.
    Burning rate K, end sizes and endings; no estimate outside the tested range."""
    return droplet(fuel, o2_pct, pressure_kpa, d0_mm, diluent)


@router.get("/models")
def list_models() -> list[dict]:
    """The trained predictors P1-P8 (models/*.json): inputs, tested ranges, held-out scores vs an always-guess
    baseline. Scores are on test days the model never saw."""
    return [predictors.summary(pid) for pid in predictors.IDS]


@router.post("/models/{pid}")
def run_model(pid: str, inputs: dict) -> dict:
    """Run one predictor. Body = its inputs, e.g. P1b: {"fuel": "heptane", "o2_pct": 21, "pressure_kpa": 101.3,
    "co2_pct": 0, "he_pct": 0}. Outside the tested range there is no model value, only the nearest real tests."""
    if pid not in predictors.IDS:
        raise HTTPException(404, f"unknown predictor {pid}; known: {', '.join(predictors.IDS)}")
    try:
        return predictors.run(pid, inputs)
    except (ValueError, TypeError) as e:
        raise HTTPException(400, str(e)) from e
