# P9: Will a solid material keep burning?

**Investigations:** BASS (PSI-26) and BASS-II (PSI-25), Burning and Suppression of Solids. ISS, Microgravity Science Glovebox (MSG) with the fan-driven SPICE flow duct.
**One row =** one solid sample (acrylic rod/sphere/slab/film, fabric, wax…) lit once. The flow was often changed during the test.

## What we predict

**For a material + shape + O₂ + airflow, what happens?**

| Class | Meaning |
|---|---|
| **Keeps burning** | Spread / burned to the end |
| **Quench** | Flow too low: the flame dies from heat loss |
| **Blow-off** | Flow too high: the flame is blown out |
| **No ignition** | Never lit |

Possible extra target: burn time (s), where the text gives it.

**Why it matters:** this is the **prevention** pillar of the brief (material flammability).

## Status: ⚠️ the outcomes must be extracted from text first

Neither CSV has a result column. The results are written as sentences in:
1. **BASS-II Summary Report, Appendix A** (observations column dropped from the CSV)
2. **BASS as-run workbook** (`Test Observations and Anomalies` column)

**Extraction plan:** for each test, an LLM (or a person) reads the row's observation text and fills `outcome`, `flow_at_outcome_cm_s`, `burn_time_s`, `confidence`, with the **document + page/row** as source. A person reviews every row. ~240 tests, so this is a few hours of review.

Expected size: **~240 tests** (BASS 109 + BASS-II ~129). Mostly PMMA, so first model = **PMMA only**.

## Data

| File | Use |
|---|---|
| `Data/psi/PSI-25/tables/PSI-25_Experimental table_BASS-II.csv` | BASS-II conditions (129 rows): material, fan/air display, calibrated O₂ before/after, CO₂, CO |
| `Data/psi/PSI-25/docs/PSI-25_Science Documents_BASS-II_Test.Matrices.xlsx` | Same tests, one sheet per scientist (Bhattacharjee 23, Ferkul 5, Miller 21, Olson 28, Fernandez-Pello 28, T'ien 30). Has `ext` notes inside the flow columns. |
| `Data/psi/PSI-25/docs/PSI-25_Reference Data_Fan calibration data.xlsx` | **Convert fan display to cm/s** |
| `Data/psi/PSI-26/tables/PSI-26_Experimental table_BASS.csv` | BASS IDs and materials only |
| **`Data/psi/PSI-26/docs/PSI-26_Science Documents_As Run_Test Matrix.xlsx`** | **BASS outcomes.** Sheet `as run matrix`: 109 tests with O₂ % (0.17 to 0.225), pressure (atm), CO₂ (mmHg), `Air display` (cm/s), material and the observation text. Sheets `2012`, `2013` split it by year. |
| `Data/psi/PSI-26/docs/PSI-26_Science Documents_Planned_Test Matrix.xlsx` | Planned vs as-run (check which tests were skipped) |

## Documents to use

| Document | Where | What for |
|---|---|---|
| **BASS-II Summary Report** (NASA/TM-20210011385) | `Data/psi/PSI-25/docs/PSI-25_Reports_BASS-II Summary Report.pdf` | **Appendix A, Tables A.1 to A.6 (p. 111 to ~122): the test log with observations → outcomes.** §1.4 (p. 14 to 15): O₂/CO₂/CO sensor use. Table 5.1 (p. 65): 11 thick-PMMA tests with spread rate (mm/s) and burn time. |
| **BASS-II ReadMe** | `Data/psi/PSI-25/docs/PSI-25_Science Documents_BASS-II_ReadMe.docx` | Column definitions: video date is one day off (leap year), fan display = voltage × 10, `OR` = CO over range (> 1,000 ppm), air display lags ~1 min, samples reused |
| BASS-II SRD | `…/PSI-25_Science Documents_BASS-II_SRD.pdf` | Planned variables and ranges |
| BASS presentations | `Data/psi/PSI-26/docs/PSI-26_Presentations_BASS_Overview of Recent ISS Results.pdf`, `…Flammability Aspects of Fabric…pdf` | Summary results and images for the app |
| BASS SRD | `Data/psi/PSI-26/docs/PSI-26_Science Documents_SRD_BASS.pdf` | Objectives |

## Inputs

| Input | Source | Cleaning |
|---|---|---|
| Material | CSV / workbook | **Normalise names:** `2 cm sphere`, `PMMA sphere 2 cm`, `pmma sphere` → `PMMA sphere, 2 cm` |
| Shape + size | Material text | Split into `shape` (rod, sphere, slab, film, fabric) and `size_mm` |
| Flow direction | Report / material text | Opposed vs concurrent (changes the physics) |
| O₂ % | Calibrated O₂ (BASS-II), `O2 % by volume` (BASS) | Use the **calibrated** value. Both before and after are given. |
| Pressure | BASS workbook (~0.97 atm) | Nearly constant |
| Flow (cm/s) | `Air display` or fan display + calibration | **Use the flow at the moment of the outcome**, not the starting flow |

## Caveats

- Fan display / "pot" values are **not cm/s**.
- `CO = OR` is a lower bound (> 1,000 ppm), not a value.
- Some samples were **reused** (partly burned). Flag them and keep them out of training.
- Very low flows (< 1 cm/s) have large uncertainty (report §6.1).
- Mixed shapes and directions make a single model weak. Start with PMMA, one flow direction.

## Open questions

- [ ] Extract outcomes from Appendix A and the as-run workbook (with page/row source)
- [ ] Join BASS-II CSV ↔ Appendix A on `Test #`
- [ ] Count tests per class after extraction. Is it enough for a model, or chart only?
