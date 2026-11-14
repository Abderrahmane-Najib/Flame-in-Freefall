# P10: PMMA flammability boundary (NASA's own formula)

**Investigation:** BASS-II (PSI-25), Olson experiments: PMMA (acrylic) rods in stagnation / concurrent flow, ISS, microgravity.
**No training needed:** NASA published the fitted boundary. We implement it and overlay the real tests.

## What we predict

**For a given airflow, the minimum O₂ at which a PMMA rod can keep burning in microgravity.** Below the curve the flame can't burn.

```
O₂_min (%) = 6 · exp(−0.5 · a) + 0.0167 · a + 13.4
```

- `a` = **stretch rate** (s⁻¹). **Exact definition (report §6.1, p. 83, verified):**
  ```
  a = (3/2) · (U / r) · (r / r₀)^½      with r₀ = 0.318 cm (base rod radius)
  ```
  `U` = free-stream flow velocity, `r` = rod radius. The square root corrects for the different rod sizes. **Don't use "U ÷ r" alone**, or the test dots will land in the wrong place on the curve.
- Low `a` (weak flow): **quenching branch**, the flame dies from heat loss (exponential term)
- High `a` (strong flow): **blow-off branch**, the flame is blown out (linear term)
- **Minimum ≈ 13.5% O₂ at a ≈ 8 to 12 s⁻¹** (checked: the formula gives 13.6% at a = 10.4 s⁻¹ ✅)

**App output:** the **U-shaped "will it burn?" curve** (log x-axis, as in report Fig. 6.10) with:
- the BASS-II test points (burned / quenched / blew off)
- horizontal lines at **21% (ISS)** and **≥ 30% (lunar base)**. Both are far above the curve.
- the **Earth (1 g) limit: 15.4% O₂**, so the Moon is shown as a range between microgravity and Earth, not one number

## Headline finding for the pitch

| | Microgravity | Earth (1 g) | Source |
|---|---|---|---|
| Minimum O₂, PMMA rods | **13.5%** | 15.4% (upward spread, with an extra 4 cm/s forced flow) | Report §6.1, p. 84 |
| Lowest O₂ with flame spread, PMMA rods (opposed flow) | **17.5%** | 19% | Report §4, p. 58 |

> *"the material remains flammable under the weak ventilation only obtainable in microgravity"* (§6.1, p. 84)

So **materials can burn at lower oxygen in space than on Earth**, and Earth flammability tests aren't automatically safe for space. The report also says the straight blow-off line can be extrapolated to zero flow as *"a conservative estimate of the minimum O₂ concentration for material flammability in space"*.

## Data

| File | Use |
|---|---|
| `Data/psi/PSI-25/tables/PSI-25_Experimental table_BASS-II.csv` | Olson test rows (`Test #` O1, O2…) for the overlay points |
| `Data/psi/PSI-25/docs/PSI-25_Science Documents_BASS-II_Test.Matrices.xlsx`, sheet `Olson` | Same 28 tests with flows and O₂ |
| `Data/psi/PSI-25/docs/PSI-25_Reference Data_Fan calibration data.xlsx` | Fan display → cm/s |

## Documents to use

| Document | Where | What for |
|---|---|---|
| **BASS-II Summary Report** | `Data/psi/PSI-25/docs/PSI-25_Reports_BASS-II Summary Report.pdf` | **Eq. 6.1 (p. 83):** the formula. **Figs. 6.9 and 6.10 (p. 83 to 84):** the boundary with flight and drop-tower data, for checking our curve. **Table A.5 (p. ~118):** Olson test log with outcomes. **§6.1.4.2:** how quenching was measured. **§4 (p. 58):** µg vs 1 g spread limit. **Table 2.1 (viewer p. 35, doc p. 27):** extinction flow for **thin** PMMA at 1 atm: 21% O₂ → 10 ± 5 mm/s, 16% O₂ → 30 ± 5 mm/s. |
| BASS-II ReadMe | `Data/psi/PSI-25/docs/PSI-25_Science Documents_BASS-II_ReadMe.docx` | Olson geometry (clear PMMA rods, upstream ignition) |

## Caveats

- **PMMA rods only**, one flow geometry. Doesn't transfer to fabrics or other plastics.
- `a` needs flow speed **and** rod radius. Get both per test. The radius is in the material name (6.35 / 9.53 / 12.7 mm rods).
- Very low flows (< 1 cm/s) are uncertain (report §6.1).
- The formula is a **fit to O₂ at extinction (final O₂)**, not starting O₂.
- The Earth value (15.4%) comes from a different setup (upward spread + 4 cm/s forced flow). The "Moon range between 13.5% and 15.4%" is a **reasonable bound, not a measurement**. Label it that way.
- **Status:** the curve is ready now. The overlay dots depend on **P9 stage 1** (extracting Olson, Table A.5).

## Open questions

- [x] Confirm the stretch-rate definition `a` used in Eq. 6.1: **a = 1.5 · (U/r) · √(r/0.318 cm)** (verified 14 Nov 2026)
- [x] Rebuild Fig. 6.10 from our extracted points as a check (14 Nov 2026, see below)

## Overlay points (14 Nov 2026)

`scripts/build_p10_points.py` → `data/psi/extracted/p10_olson_points.csv` (38 points: outcome point + last-stable point per test, final O₂).

- Flow: pot → U with that day's fan calibration for the test's restrictor count (`scripts/fan_calibration.py`, U = 1.0066 × air display); air-display flows used directly.
- **Blowoff branch reproduced:** 8 blowoff points with exact flows lie on Eq. 6.1 (O₂ − boundary = −0.84 to +0.47).
- **Quench branch: flow known only as a range.** Every quench was at pot 0.27–0.36, below the lowest calibrated pot (0.5), where readings vary 0–3.8 cm/s between days. Extrapolating gave arbitrary values, so these points carry `u_low_cm_s = 0`, `u_high_cm_s` = highest reading ever at pot ≤ 0.5 for that restrictor count. Draw them as horizontal bars. All of them cross the quench branch, consistent with NASA's wide error bars in Fig. 6.10.
- Flags: `sooted_anemometer_day` (days 209–210 read ~40% low before a "post soot cleaning" calibration), `reused_sample`, `low_confidence_label` (O3a "probably overshot" sits 4.4 points above the curve).
