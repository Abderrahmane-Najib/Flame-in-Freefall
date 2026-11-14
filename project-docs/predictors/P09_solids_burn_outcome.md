# P9: Will a solid material keep burning?

**Investigations:** BASS (PSI-26) and BASS-II (PSI-25), Burning and Suppression of Solids. ISS, Microgravity Science Glovebox (MSG) with the fan-driven SPICE flow duct.
**One row =** one solid sample (acrylic rod/sphere/slab/film, fabric, wax…) lit once. The flow was often changed during the test.

## What we predict

**For a material + shape + O₂ + airflow + flow direction, what happens?**

| Class | Meaning |
|---|---|
| **Keeps burning** | Spread / burned to the end |
| **Quench** | Flow too low: the flame dies from heat loss |
| **Blow-off** | Flow too high: the flame is blown out |
| **No ignition** | Never lit |

Possible extra target: burn time (s), where the text gives it.

## Decision (14 Nov 2026): ✅ do it, as **data extraction first, model second**

**Why it's worth it:**
- The brief names solids directly: *"Flammability studies focus on solid materials such as fabrics and plastics … BASS and BASS-II … Saffire."* Fabric and plastic are the most realistic habitat fires (clothes, cables, foam).
- Without P9, solids = only the P10 curve and the small P11 chart. With P9 we have **~250 real solid outcomes**, which also covers the brief's *"extract data that supports predictive modeling"*.
- It gives the **P10 curve its real test dots** (Olson, Table A.5).
- The competitor (MicroFire Atlas) covers solids, so skipping P9 means they have more solids data than us.

**Why it's hard:** the results are sentences in a PDF whose table rows are broken across lines and cut off by text extraction. Each row has to be read and labelled.

**Plan in stages.** Each stage is useful on its own, so we can stop at any point:

| Stage | Source | Rows | Time | What we get |
|---|---|---|---|---|
| 1 | **Olson**, Table A.5 (PMMA rods) | ~28 | ~1 h | Real dots on the P10 curve ⭐ |
| 2 | **T'ien**, Table A.6 (SIBAL fabric) | ~30 | ~1 h | Bigger P11 fabric chart |
| 3 | Bhattacharjee, Ferkul, Fernandez-Pello, Miller (A.1 to A.4) | ~70 | ~2 h | BASS-II outcome map |
| 4 | BASS as-run workbook (text already in Excel, easier) | ~124 | ~2 h | ~250 solid tests in total |
| 5 | Model, **only if the classes are balanced enough** | | ~1 h | Predictor. Otherwise P9 stays a chart (outcome map, VISUALISATIONS L4) |

**Extraction method:** an LLM reads each row's observation text and fills `test_id, outcome, flow_direction, final_flow_raw, burn_time_s, confidence, source_doc, source_page`. A person checks every row. Never let the LLM invent a value: blank if the text doesn't say.

## Status: ⚠️ the outcomes must be extracted from text first

Neither CSV has a result column. The results are written as sentences in:
1. **BASS-II Summary Report, Appendix A** (Tables A.1 to A.6). Verified: the observation text is there (viewer pp. 111 to ~122). Outcome words in the appendix: *extinguish* 56, *blowoff* 22, *blew* 6, *quench* 6, *did not ignite / no ignition* 2. The layout is broken by `pdftotext -layout` (one row spread over several lines, long sentences cut), so extract from the page image or by hand if the text is unreadable.
2. **BASS as-run workbook** (`Test Observations and Anomalies` column): **125 rows, 124 with text**. Words: *extinguish* 31, *spread* 24, *blow* 11, *quench* 1, *no ignition / did not ignite* 6, *soot* 72, *blue* 60.

⚠️ **The BASS-II `Test.Matrices.xlsx` has NO observation column** (verified). It only has a few `ext` notes inside flow cells (Fernandez-Pello 16, Olson 5, others ≤ 2). Don't count on it for outcomes.

Expected size: **~250 tests** (BASS ~124 + BASS-II 129). Mostly PMMA, so first model = **PMMA only, one flow direction**.

## Data

| File | Use |
|---|---|
| `Data/psi/PSI-25/tables/PSI-25_Experimental table_BASS-II.csv` | BASS-II conditions (129 rows): material, fan/air display, calibrated O₂ before/after, CO₂, CO. **No pressure column.** |
| `Data/psi/PSI-25/docs/PSI-25_Science Documents_BASS-II_Test.Matrices.xlsx` | Same tests, one sheet per scientist (Bhattacharjee 23, Ferkul 5, Miller 21, Olson 28, Fernandez-Pello 28, T'ien 30). Cross-check only: no observations. |
| `Data/psi/PSI-25/docs/PSI-25_Reference Data_Fan calibration data.xlsx` | **Convert fan display to cm/s.** Organised **per test day and per number of flow restrictors** (Pot → Fan display → Air display → `U cm/s`). Not every day is complete. The note says don't use the 3.8 V zero-flow value. Match each test to its day + restrictor. |
| `Data/psi/PSI-26/tables/PSI-26_Experimental table_BASS.csv` | BASS IDs and materials only |
| **`Data/psi/PSI-26/docs/PSI-26_Science Documents_As Run_Test Matrix.xlsx`** | **BASS outcomes.** Sheet `as run matrix`: **125 rows** (124 with observation text, 109 with an `Air display` value) with O₂ % (0.17 to 0.225), pressure (~0.97 atm), CO₂ (mmHg), `Air display` (cm/s, often a sequence like `10, 5, 3`), material and the observation text. Sheets `2012`, `2013` split it by year. |
| `Data/psi/PSI-26/docs/PSI-26_Science Documents_Planned_Test Matrix.xlsx` | Planned vs as-run (check which tests were skipped). Low value. |

## Documents to use

| Document | Where | What for |
|---|---|---|
| **BASS-II Summary Report** (NASA/TM-20210011385) | `Data/psi/PSI-25/docs/PSI-25_Reports_BASS-II Summary Report.pdf` | **Appendix A, Tables A.1 to A.6 (viewer p. 111 to ~122): the test log with observations → outcomes, and the flow direction column.** A.5 Olson starts p. 118, A.6 T'ien p. 120. §1.4 (p. 14 to 15): O₂/CO₂/CO sensor use. **Table 5.1: 20 BASS-II tests** (Miller, thick PMMA) with spread rate (mm/s) and burn time. |
| **BASS-II ReadMe** | `Data/psi/PSI-25/docs/PSI-25_Science Documents_BASS-II_ReadMe.docx` | Column definitions: video date is one day off (leap year), fan display = voltage × 10, `OR` = CO over range (> 1,000 ppm), air display lags ~1 min, samples reused |
| BASS-II SRD | `…/PSI-25_Science Documents_BASS-II_SRD.pdf` | Planned variables and ranges |
| BASS presentations | `Data/psi/PSI-26/docs/PSI-26_Presentations_BASS_Overview of Recent ISS Results.pdf`, `…Flammability Aspects of Fabric…pdf` | Summary results and images for the app |
| BASS SRD | `Data/psi/PSI-26/docs/PSI-26_Science Documents_SRD_BASS.pdf` | Objectives |

## Inputs

| Input | Source | Status | Cleaning |
|---|---|---|---|
| Material | CSV / workbook | ⚠️ free text | **Normalise names:** `2 cm sphere`, `PMMA sphere 2 cm`, `pmma sphere` → `PMMA sphere, 2 cm` |
| Shape + size | Material text | ⚠️ parse | Split into `shape` (rod, sphere, slab, film, fabric) and `size_mm` |
| **Flow direction** | **Appendix A only** (not in any CSV) | ❌ extract | Opposed 67 / Concurrent 38 / Stagnation 15 mentions in Appendix A. Changes the physics: never mix directions in one model. |
| O₂ % | Calibrated O₂ (BASS-II), `O2 % by volume` (BASS) | ✅ | Use the **calibrated** value. Both before and after are given. |
| Pressure | BASS workbook (~0.97 atm) | ⚠️ BASS-II has none | BASS-II: assume ISS cabin pressure and set `pressure_assumed = true` |
| Flow (cm/s) | `Air display` or fan display + calibration | ⚠️ | **Use the flow at the moment of the outcome**, not the starting flow (sequences like `10, 5, 3, 2, 1`) |

**Do not use as inputs:** final O₂ / CO₂ / CO (measured after burning), `total frames shot`, radiometer columns.

## Caveats

- Fan display / "pot" values are **not cm/s**.
- `CO = OR` is a lower bound (> 1,000 ppm), not a value.
- Some samples were **reused** (partly burned). Flag them and keep them out of training.
- Very low flows (< 1 cm/s) have large uncertainty (report §6.1).
- Mixed shapes and directions make a single model weak. Start with PMMA, one flow direction.

## Open questions

- [ ] Stage 1: extract Olson (Table A.5) with page source
- [ ] Join BASS-II CSV ↔ Appendix A on `Test #`
- [ ] Count tests per class after extraction. Is it enough for a model, or chart only?
