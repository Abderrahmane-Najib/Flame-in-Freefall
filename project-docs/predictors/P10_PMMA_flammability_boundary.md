# P10: PMMA flammability boundary (NASA's own formula)

**Investigation:** BASS-II (PSI-25), Olson experiments: PMMA (acrylic) rods in stagnation / concurrent flow, ISS, microgravity.
**No training needed:** NASA published the fitted boundary. We implement it and overlay the real tests.

## What we predict

**For a given airflow, the minimum O₂ at which a PMMA rod can keep burning in microgravity.** Below the curve the flame can't burn.

```
O₂_min (%) = 6 · exp(−0.5 · a) + 0.0167 · a + 13.4
```

- `a` = **stretch rate** (s⁻¹), roughly flow speed ÷ rod radius
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
| Minimum O₂, PMMA rods | **13.5%** | 15.4% (upward spread) | Report §6.1, p. 84 |
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
| **BASS-II Summary Report** | `Data/psi/PSI-25/docs/PSI-25_Reports_BASS-II Summary Report.pdf` | **Eq. 6.1 (p. 83):** the formula. **Figs. 6.9 and 6.10 (p. 83 to 84):** the boundary with flight and drop-tower data, for checking our curve. **Table A.5 (p. ~118):** Olson test log with outcomes. **§6.1.4.2:** how quenching was measured. **§4 (p. 58):** µg vs 1 g spread limit. **Table 2.1 (p. 36):** extinction flow for **thin** PMMA at 1 atm: 21% O₂ → 10 ± 5 mm/s, 16% O₂ → 30 ± 5 mm/s. |
| BASS-II ReadMe | `Data/psi/PSI-25/docs/PSI-25_Science Documents_BASS-II_ReadMe.docx` | Olson geometry (clear PMMA rods, upstream ignition) |

## Caveats

- **PMMA rods only**, one flow geometry. Doesn't transfer to fabrics or other plastics.
- `a` needs flow speed **and** rod radius. Get both per test. The radius is in the material name (6.35 / 9.53 / 12.7 mm rods).
- Very low flows (< 1 cm/s) are uncertain (report §6.1).
- The formula is a **fit to O₂ at extinction (final O₂)**, not starting O₂.

## Open questions

- [ ] Confirm the stretch-rate definition `a` used in Eq. 6.1 (in §6.1)
- [ ] Rebuild Fig. 6.10 from our extracted points as a check
