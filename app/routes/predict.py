from fastapi import APIRouter, HTTPException, Query

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
