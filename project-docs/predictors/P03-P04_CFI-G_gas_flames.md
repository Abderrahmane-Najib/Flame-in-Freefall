# P3 & P4: CFI-G gas flames at high oxygen

**Investigation:** ACME Cool Flames Investigation with Gases, CFI-G (PSI-159). ISS, CIR with the ACME hardware, spherical porous burner, microgravity.
**One row =** one gas flame lit once.

## What we predict

| ID | Target | Column | Values | Baseline |
|---|---|---|---|---|
| **P3** | Did the flame ignite? | `Hot ignition` | Yes 132 / No 47 | 74% |
| **P4** | Once lit: did it go out by itself? | `Self-ext or flow term` | **SE** (self-extinguished) 102 / **FT** (kept burning until the gas was cut) 31. `-` (46) = not lit, excluded. | 77% |

**Why it matters:** P4 is the closest thing in the data to *"is this fire self-limiting?"*, and CFI-G goes up to **40% chamber O₂**, the only source near lunar-base air (≥30%).

## Data

| File | Use |
|---|---|
| `Data/psi/PSI-159/tables/PSI-159_Experimental table_CFI-G_Normal Flames.csv` | **Training data** (179 tests) |
| `Data/psi/PSI-159/tables/PSI-159_Experimental table_CFI-G_Inverse Flames.csv` | **Chart only**: 1,015 lines, 154 real tests (861 empty) |
| `Data/psi/PSI-159/investigation.json` | Card text |

## Inputs (normal flames)

| Column | Range | Cleaning |
|---|---|---|
| `Fuel` | 30% butane 52, 30% propane 36, 50% butane 30, 30% ethane 27, propane 20, ethane 14 | Split into `fuel_gas` + `fuel_fraction` |
| `XO2 before test` | 0.18 to 0.40 | Chamber O₂. × 100 → % |
| `approx p (bar)` | 0.51 to 3.04 | × 100 → kPa |
| `Xf` | 0 to 1 | Fuel fraction in burner gas |
| `mHC (mg/s)` | | Fuel flow |
| `Day` | | For grouped split |

**Do not use as inputs:** `Tad (K)` (a *calculated* flame temperature, not measured), `burn time`, `Peak burner T`, `Color` (these happen after ignition, so they would leak the answer).

## Documents to use

| Document | Where | What for |
|---|---|---|
| **CFI-G Final Report** (2022) | `Data/psi/PSI-159/docs/PSI-159_Reports_FinalRpt_ACME.CFI-G.pdf` | Tables 1 and 2 (p. 21 to 22): flames ignited per test day, a **cross-check for row counts**. Table 3 (p. 46): 11 **gas cool flames** at ~39% O₂, 2 bar (for the "invisible fire" story). Normal vs inverse configuration. |
| ACME non-imaging data file description | `Data/psi/PSI-23/docs/PSI-23_Science Documents_ACME non-imaging data file description.pdf` | Column meanings for ACME logs |
| ACME fact sheets / ISS Researchers Guide | `Data/psi/PSI-23/docs/` | Plain-language hardware explanation |

## Caveats

- **Inverse flames are different physics.** Their `XO2` (0.12 to 0.85) is oxygen **inside the burner stream**, blown into a fuel-filled chamber. It is **not cabin oxygen.** Never plot on the same axis without a different marker and label. Never train P3/P4 on them.
- Inverse ignition values mix case (`Yes`/`yes`, `No`/`no`), plus `flash` (8). Normalise before counting.
- High O₂ tests are at a range of pressures. Check how many are both ≥30% O₂ **and** ≤70 kPa before claiming lunar relevance.

## Open questions

- [ ] Count normal-flame tests in lunar-like air (≥30% O₂ and ≤70 kPa)
- [ ] Check row counts per day against report Tables 1 and 2
