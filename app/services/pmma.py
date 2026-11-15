"""P10: PMMA (acrylic) rod flammability boundary in microgravity: NASA's own fitted formula, no training.

BASS-II Summary Report (NASA/TM-20210011385), Eq. 6.1, PDF p. 83:
    O2_min (%) = 6 * exp(-0.5 * a) + 0.0167 * a + 13.4
    a = 1.5 * (U / r) * sqrt(r / r0),  r0 = 0.318 cm      (stretch rate, 1/s; U = flow, r = rod radius)
Below the curve a PMMA rod cannot keep burning: on the left the flame dies from heat loss (quenching),
on the right it is blown off. Rods only, one flow geometry; microgravity only. See project-docs/predictors/P10.
"""

import math

R0_CM = 0.318
ROD_DIAMETERS_MM = (6.35, 9.53, 12.7)   # the rods BASS-II tested (1/4", 3/8", 1/2")
A_RANGE = (0.5, 500.0)                  # stretch rates drawn (log scale, as in report Fig. 6.10)

REPORT = ("https://psi.nasa.gov/geode-py/ws/studies/PSI-25/download?"
          "file=PSI-25_Reports_BASS-II%20Summary%20Report.pdf#page={}")


def stretch_rate(flow_cm_s: float, rod_diameter_mm: float) -> float:
    r = rod_diameter_mm / 20  # mm diameter -> cm radius
    return 1.5 * (flow_cm_s / r) * math.sqrt(r / R0_CM)


def flow_for(a: float, rod_diameter_mm: float) -> float:
    r = rod_diameter_mm / 20
    return a * r / (1.5 * math.sqrt(r / R0_CM))


def o2_min(a: float) -> float:
    return 6 * math.exp(-0.5 * a) + 0.0167 * a + 13.4


def boundary(rod_diameter_mm: float, flow_cm_s: float | None = None, o2_pct: float | None = None) -> dict:
    lo, hi = (math.log10(x) for x in A_RANGE)
    curve = []
    for i in range(121):
        a = 10 ** (lo + (hi - lo) * i / 120)
        curve.append({"a": round(a, 3), "flow_cm_s": round(flow_for(a, rod_diameter_mm), 3),
                      "o2_min_pct": round(o2_min(a), 3)})

    result = {
        "model": "NASA fitted boundary, BASS-II Eq. 6.1 (not trained by us)",
        "cite": "BASS-II Summary Report (NASA/TM-20210011385), Eq. 6.1, PDF p. 83",
        "url": REPORT.format(83),
        "rod_diameter_mm": rod_diameter_mm,
        "curve": curve,  # x: flow_cm_s (or a, log scale), y: o2_min_pct; below = cannot keep burning
        "references": [
            {"o2_pct": 13.5, "label": "Lowest O2 measured for PMMA rods in microgravity",
             "cite": "BASS-II Summary Report, PDF p. 84", "url": REPORT.format(84)},
            {"o2_pct": 15.4, "label": "Earth (1 g) limit, NASA upward-burning test with 4 cm/s forced flow "
                                      "(different setup)",
             "cite": "BASS-II Summary Report, PDF p. 84", "url": REPORT.format(84)},
            {"o2_pct": 21.0, "label": "ISS / sea-level air", "cite": "NTRS 20240003211",
             "url": "https://ntrs.nasa.gov/citations/20240003211"},
            {"o2_pct": 30.0, "label": "Moon habitat: 30% O2 or more (challenge text)",
             "cite": "NASA Space Apps 2026, Flame in Freefall challenge",
             "url": "https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/"},
        ],
        "moon_range": {"o2_min_pct": [13.5, 15.4],
                       "label": "Bounded range between the microgravity and Earth limits: a reasonable bound, "
                                "not a measurement (no PMMA test at lunar gravity)"},
        "caveats": [
            "PMMA rods only, one flow geometry: does not transfer to fabrics or other plastics.",
            "Microgravity only. The formula fits O2 at extinction (final O2), not starting O2.",
            "Flows below 1 cm/s are uncertain (report section 6.1).",
        ],
    }

    if flow_cm_s is not None:
        a = stretch_rate(flow_cm_s, rod_diameter_mm)
        limit = o2_min(a)
        point = {"flow_cm_s": flow_cm_s, "a": round(a, 3), "o2_min_pct": round(limit, 2),
                 "branch": "quenching (heat loss)" if a < 10.4 else "blow-off (flow too strong)"}
        if o2_pct is not None:
            point["o2_pct"] = o2_pct
            point["margin_pct"] = round(o2_pct - limit, 2)  # > 0: above the boundary
            point["verdict"] = ("above the boundary: a PMMA rod can keep burning" if o2_pct > limit
                                else "below the boundary: a PMMA rod cannot keep burning")
        warnings = []
        if flow_cm_s < 1:
            warnings.append("flow below 1 cm/s: the boundary is uncertain here")
        if not A_RANGE[0] <= a <= A_RANGE[1]:
            warnings.append("stretch rate outside the drawn range of the fit")
        point["warnings"] = warnings
        result["point"] = point

    return result
