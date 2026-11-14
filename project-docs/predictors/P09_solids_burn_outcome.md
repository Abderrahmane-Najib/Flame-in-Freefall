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

## Stage 1 result (14 Nov 2026): Olson, 27 tests ⏳ awaiting human check

- `scripts/extract_p9_olson.py` → `data/psi/extracted/p9_olson.csv`. 24 rows from Table A.5 (viewer pp. 118–119, read from 220-dpi renders because the text layer drops most of each row) + O20–O22 (2016, workbook only, no observation text).
- Outcomes: quench 9 · blowoff 9 · keeps burning 3 · no ignition 3 · extinguished (cause unclear) 1 · blank 2. 7 reused samples flagged.
- Cross-check: calibrated initial/final O₂, restrictor and sample number match the BASS-II CSV on all 24 shared rows.
- Columns added beyond the plan: `last_stable_flow_raw` (NASA's boundary uses the extinction flow **and** the last stable flow, report §6.1.4.4), `observation` (verbatim), `notes`.
- **Too few for a model** (one material, ≤ 9 per class, flow direction mixed). Olson stays a P10 overlay.

## Stage 2 result (14 Nov 2026): T'ien, 29 tests ⏳ awaiting human check

- `scripts/extract_p9_tien.py` → `data/psi/extracted/p9_tien.csv` (Table A.6, viewer pp. 120–121) and `data/psi/extracted/p11_sibal.csv` (Table 7.1, viewer p. 104: 27 BASS-II fabric rows + 4 BASS rows, outcomes for the BASS rows pending stage 4).
- Flows and NASA's result label come from **Table 7.1** (already in cm/s); the verbatim observation from A.6. Where they disagree, NASA's summary label is used and the row says so (T12, T18).
- Outcomes: keeps burning 13 · quench 8 · no ignition 7 · blowoff 1. Fresh fabric samples: quench 6, no ignition 3, blowoff 1 = exactly the counts stated in report §7.1.4.
- Cross-check vs the BASS-II CSV: O₂ initial/final, restrictor, sample number match on all 29 rows.
- Fixes recorded in `notes`: dates 6/24/**2018** → 2014 (T9, T10, T18; Table 7.1 says GMT 175); final O₂ 0.9 / 40.4 (T28a/b) blanked; T24 width 2.2 cm (sample 133m, not "1 cm").
- T3 and T7 are **4 cm spherical sections in stagnation flow**, not fabric: kept in P9, excluded from P11.

## Stage 3 result (14 Nov 2026): Bhattacharjee, Ferkul, Fernandez-Pello, Miller, 73 tests

- `scripts/extract_p9_stage3.py` → `data/psi/extracted/p9_stage3.csv` (Tables A.1–A.4, viewer pp. 111–117).
- Bhattacharjee 22 (PMMA films, opposed), Ferkul 4 (Nomex + a wax candle), Fernandez-Pello 27 (PMMA rods, mostly opposed), Miller 20 (PMMA slabs, opposed).
- Cross-check vs the BASS-II CSV: O₂, restrictor and sample number match on all 73 rows; only the 3 typo final-O₂ values (B2 1.6, P22a 0.6, P22b 39.1) differ, blanked on purpose. **BASS-II complete: 27 + 29 + 73 = 129 = the CSV.**
- New label `self_extinguished`: went out on its own at a steady, not-low flow (Miller's long slab burns ending at 8–15 cm/s).
- Rule made explicit: went out when the flow was turned down **or off** → `quench` (flow 0 = off), with the last stable flow recorded.

## Stage 4 result (14 Nov 2026): BASS as-run workbook, 121 tests

- `scripts/extract_p9_bass.py` → `data/psi/extracted/p9_bass.csv`. Everything except the label is read straight from the workbook; the script holds one label line per workbook row, guarded by the test number.
- Mostly PMMA spheres (stagnation flow) and wax candles, plus SIBAL, Nomex, Ultem, PMMA and wax slabs.
- New flags: `n2_suppression_used` (17 tests used the nitrogen jet); label `suppressed_n2` for the 2 where nitrogen put the flame out. Igniter failures have a blank outcome (not a flammability result).
- `reused` is computed: a sample number seen in an earlier row.

## Merged dataset and decision (14 Nov 2026)

`scripts/build_p9_dataset.py` → `data/psi/extracted/p9_solids.csv`: **250 solid tests** with material family, shape, size, flow direction, O₂, outcome, flow in cm/s where convertible (air display or BASS-II fan calibration; below-calibration pots give a range; BASS fan/pot values have no calibration).

- Outcomes: quench 108 · keeps burning 70 · no ignition 32 · blowoff 12 · self-extinguished 11 · unclear 4 · N₂-suppressed 2 · blank 11.
- Usable for modelling (labelled, fresh sample, no N₂): **137**, split over 15 material × shape × direction groups; the largest is 29 (SIBAL, concurrent). Several groups are almost one class (PMMA rods opposed: 16 quench / 1 other).
- **Decision: no P9 model.** Classes are not balanced within any one material/geometry. P9 ships as the **outcome map** (VISUALISATIONS L4) plus nearest-real-tests lookup, which is what the data honestly supports.
- Headline (fresh samples, starting O₂): Nomex no ignition at 21.0–22.5% (burned once at 22.0% with the igniter left on); Ultem never ignited (21.9–22.5%); SIBAL fabric sustained a flame down to 16.9%, no ignition at 16.4–16.8%; PMMA rods down to 14.8%, no ignition at 13.6–14.5%; wax candles down to 15.9%.

## Open questions

- [x] Stage 1: extract Olson (Table A.5) with page source
- [x] Stage 2: extract T'ien (Table A.6 + Table 7.1)
- [x] Stage 3: Tables A.1–A.4
- [x] Stage 4: BASS as-run workbook
- [x] Count classes: chart only (see decision)
- [ ] Human check of the stage 3 and 4 labels (rows with `confidence` = low first)
- [ ] **Human check of `p9_olson.csv`**
- [ ] Join BASS-II CSV ↔ Appendix A on `Test #`
- [ ] Count tests per class after extraction. Is it enough for a model, or chart only?
