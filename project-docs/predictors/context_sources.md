# Context sources (used in the app, not for predictions)

These investigations have no usable "result" to predict, but they give the app **sourced facts, charts and cards**.

## SAME / SAME-R: smoke detection

**Why no predictor:** no "alarm went off" data.
**What we show:** a **"Smoke fingerprint" card per material** and the message *one detector type doesn't fit all smoke*.

| Material | Mean smoke particle diameter (nm) | After aging (nm) |
|---|---|---|
| Kapton | 105 | 186 |
| Teflon | 205 | 273 |
| Lamp wick (cotton) | 227 | 308 |
| Silicone | 257 | 422 |

Key facts:
- Small Kapton and Teflon particles are **hard for light-scattering detectors** (the ISS type) to see.
- **Smoke is bigger at low airflow**: smoke trapped in an avionics box will differ from smoke in a ventilated cabin.
- In SAME-R, describe tests by **heater temperature, not `Rt/R0`**. The same setting can differ by up to 30 °C.

| File / document | Where | What for |
|---|---|---|
| SAME Final Science Report | `Data/psi/PSI-102/docs/PSI-102_Reports_SAME_Final Science Report.pdf` | **Table 1 (p. 8, repeated p. 27):** particle sizes above. Detector history: ionization (Shuttle) vs light-scattering (ISS). |
| SAME-R Final Report | `Data/psi/PSI-101/docs/PSI-101_Reports_SAME-R_Final Report.pdf` | Baseline diameters per material, particle size vs duct velocity (Figs. 6 to 8, p. ~79), heater-temperature note (p. 2 to 3) |
| SAME / SAME-R CSVs | `Data/psi/PSI-102/tables/…SAME.csv` (8 rows = 4 tests), `Data/psi/PSI-101/tables/…SAME-R.csv` (109 rows = 67 tests) | Test conditions. ⚠️ No O₂ or pressure columns, so they **don't appear on the V1 map** unless we assume ISS cabin air (flag it). |
| SAME-2 presentations | `Data/psi/PSI-101/docs/*.pptx` | Flight vs ground comparison, images |
| NIST/NASA "one detector doesn't fit all" (web) | nist.gov, 2018 | Outside source for the pitch |

## SPICE: soot and smoke points of gas flames

**Why no predictor:** the 469-row CSV doesn't mark which rows are smoke points.
**What we show:** 52 smoke points over 5 fuels (C₂H₄ 6, C₃H₈ 6, C₃H₆ 20, 75% C₃H₆ 13, 50% C₃H₆ 7, verified); *"an increase in coflow velocity generally increases the smoke point length"*.
⚠️ The Final Report Table 1 gives **ranges per fuel, not the 52 individual points**. For a per-point chart use Dotson thesis Table 3.1 (not yet checked).

| File / document | Where |
|---|---|
| SPICE Final Report, Table 1 | `Data/psi/PSI-107/docs/PSI-107_Reports_SPICE_FinalReport.pdf` (p. 4, p. 20) |
| Dotson thesis, Table 3.1 (µg) and 6.3 / 6.4 (1 g) | `Data/psi/PSI-107/docs/PSI-107_Reports_SMOKE POINTS OF MICROGRAVITY AND  NORMAL GRAVITY COFLOW DIFFUSION  FLAMES_DotsonThesis.pdf` |

## Saffire I to III: large fabric fires in a cargo ship

**Why no predictor:** 2 / 9 / 2 tests (the Saffire-II CSV has 15 lines, but 6 are flow-visualisation and note rows).
**What we show:** the only **large-scale** fires, and Saffire-II's microgravity vs Earth spread comparison (columns `?-g Spread Length`, `1-g Spread Rate`).
⚠️ That comparison is **mostly words**, not numbers: µg spread is `~ 0`, `n/a`, `29 cm`; 1 g is `Complete`, `Acceleratory`. Numeric rates exist only for a few samples (µg SIBAL 2.1 and 2.6 mm/s; 1 g silicone 1.2 and 0.6 mm/s). Show it as a **qualitative** table.

| File / document | Where |
|---|---|
| Saffire tables | `Data/psi/PSI-98/tables/`, `PSI-99/tables/`, `PSI-100/tables/` |
| Saffire Objectives, Development and Status | `Data/psi/PSI-98/docs/…pdf` (pre-flight plans, sample list Table 1, objectives Table 5) |
| Saffire-I / III ReadMe | `Data/psi/PSI-98/docs/…Readme.docx` (SIBAL fabric definition) |
| MergeResult workbooks | **Image file lists only**, not results |

## ACME Flame Design, s-Flame, BRE, CLD, E-FIELD, SLICE

**Why no predictor:** one row per test day, or results only in figures.
**What we show:** coverage-map points and investigation cards. E-FIELD is the only "artificial gravity" study, but **no local report**.

| Document | Where |
|---|---|
| Flame Design Final Report (Table 1: flames per day) | `Data/psi/PSI-10/docs/PSI-10_Reports_FinalRpt_ACMEFlameDesign.pdf` |
| s-Flame final report (Table 1) | `Data/psi/PSI-23/docs/PSI-23_Reports_s_Flame_final_report_20210729.pdf` |

## General explainers for the AI assistant

| Document | Where |
|---|---|
| ISS Researchers Guide: Combustion in Reduced Gravity | `Data/psi/PSI-23/docs/PSI-23_Presentations_ISS Researchers Guide - Combustion In Reduced Gravity.pdf` |
| ACME fact sheets / info sheets | `Data/psi/PSI-23/docs/PSI-23_Presentations_ACME fact sheet*.pdf`, `PS-0*.pdf` |
| "Unlocking Mysteries" | `Data/psi/PSI-23/docs/PSI-23_Presentations_PS_00538  Unlocking Mysteries.pdf` |
| Cool Flames in Space seminar (2026) | `Data/psi/PSI-117/docs/PSI-117_Presentations_PSI_Users_Group_Cool_Flames_in_Space_03302026.pdf` |

## Not useful

DAFT (dust, not fire), PSI-115 (SAME modelling), SAME software / ops / crew manuals, crew training decks, SAFFIRE image indexes.
