# Verification log (14 Nov 2026)

Every number and claim in `project-docs/` was re-checked against the raw files in `Data/` (download of 14 Nov), the cleaned CSVs in `data/psi/clean/`, and the report PDFs (text extracted with `pdftotext`). All corrections have been applied to the docs.

**Verdict:** almost everything is correct and doable. A few counts were off, one doc example didn't work, and P9 is more work than first described.

---

## 1. Confirmed exactly ✅

| Claim | Where |
|---|---|
| FLEX: Extinction 186 / Disruption 61 / Completion 27; burn time n = 268, 0.3–39.2 s; 1 row with pressure 0; methanol 157 / heptane 117; O₂ 0.12–0.34; CO₂ ≤ 0.70; He ≤ 0.45 | P01-P02 |
| CFI-G normal: ignition Yes 132 / No 47; SE 102 / FT 31 / – 46; fuels; XO₂ 0.18–0.40; p 0.51–3.04 bar; 20 lunar-air tests | P03-P04 |
| CFI-G inverse: 154 tests, XO₂ 0.12–0.85, mixed-case ignition + 8 "flash" | P03-P04 |
| CFI workbook: 227 tests, 146 analysed; O₂ 0.21 (118) / 0.17 (28); He 0 / 0.29 / 0.59; 3 analysed fuels; Farnesane not analysed. CSV = 87 rows / 79 unique | P05-P08 |
| PMMA Eq. 6.1 (viewer p. 83), minimum 13.5% at a = 8–12 s⁻¹ (formula: 13.61% at a = 10.4), Earth 15.4%, quote on p. 84, "conservative estimate" quote | P10 |
| 17.5% (µg) vs 19% (1 g) PMMA spread limit | P10, V7 |
| Table 2.1: 21% → 10 ± 5 mm/s, 16% → 30 ± 5 mm/s | P10 |
| Table 7.1: Quenched 6, No ignition 3 (16.4 / 16.4 / 16.8%), Blow-off 1, No blowoff 2, Reused 4; quench flows 2.2–2.8 cm/s | P11 |
| Appendix A (A.1–A.6) contains the observation text | P9 |
| SAME Table 1 particle sizes; "challenging for light scattering", "low flow rates → bigger particles", "particle size discrimination", 30 °C Rt/R0 quotes | context_sources, V8 |
| SPICE: 52 smoke points (6 + 6 + 20 + 13 + 7); "coflow velocity increases smoke point length" | context_sources |
| CFI-G Table 3: ~11 gas cool flames at ~0.39 O₂, 2.03 bar, 30% fuel, hot/cool radius ratio ~2.3–2.9 | DOCS_FINDINGS |
| CFI report: "above 2 atm, multiple reignition cycles … until the fuel droplet is completely consumed"; helium → larger cool-flame extinction diameter | P05-P08 |
| Images: 13 images across 5 investigations | V12 |
| 32 CFI summary PDFs, 144 SAME/SAME-R analysed spreadsheets, ~1 GB analysed data in total | VISUALISATIONS L2, L3 |

## 2. Corrected ✏️

| Was | Now | File(s) |
|---|---|---|
| CFI P5 147 / P6 144 / P7 71–48–27 / P8 151 (114 / 37) | **143 / 141 / 69–48–29 / 145 (110 / 35)**; baselines 59% / 76% (counts were not filtered to analysed tests) | P05-P08 |
| CFI-G fuel fraction "split from the Fuel label" | Use **`Xf`**: 26 tests labelled "30%" ran at 2.7–4.7% fuel (the cleaner already does this) | P03-P04 |
| CFI-G `Tad` "do not use" | Allowed (calculated from starting conditions, no leak); `Zst` too | P03-P04 |
| — | Added "do not use": `TFP` (Yes only on ignited flames), `Comments` (contain answers), `XO2 after`, `Cool flame?` | P03-P04 |
| — | Added "do not use" for FLEX results (extinction diameter, burning rate, burn time) | P01-P02 |
| Stretch rate "≈ flow ÷ radius" | **a = 1.5·(U/r)·√(r/0.318 cm)** (report p. 83) | P10, DOCS_FINDINGS, HANDOFF |
| BASS-II Test.Matrices "has `ext` notes" (implied outcome source) | **No observation column**; Appendix A is the only BASS-II outcome source | P09, DOCS_FINDINGS |
| BASS as-run "109 tests" | 125 rows, 124 with text, 109 with a flow value; word counts updated | P09, DOCS_FINDINGS |
| BASS-II Table 5.1 "11 tests" | **20** tests | P09, DOCS_FINDINGS |
| Saffire-II "15 rows", numeric µg vs 1 g | **9 tests** + 6 note rows; comparison is mostly words | context_sources, V7, DOCS_FINDINGS |
| SPICE "52 smoke points" (implied per-point data) | Report gives ranges per fuel only | context_sources, DOCS_FINDINGS |
| V1 "~750 tests with O₂ and pressure" | **~1,600** (some assumed); BASS-II, SAME, SAME-R, Saffire missing from map | VISUALISATIONS, DATA_EXPLAINED |
| 849 videos | 855 `.mp4` | VISUALISATIONS |
| Page numbers: Table 7.1 p. 104, Table 2.1 p. 36 / doc p. 28 | p. 103; viewer p. 35 / doc p. 27 | P10, P11, DOCS_FINDINGS |
| DATA_EXPLAINED §8: CFI "87 tests"; FLEX-2 / BRE / CLD / E-FIELD / SLICE IDs "—"; CFI-G fuel "ethylene, methane" | 227 tests; PSI-68 / 20 / 21 / 22 / 106; ethane / propane / butane | DATA_EXPLAINED |
| DATA_EXPLAINED §13 example: "FLEX tests near 30% O₂ and 70 kPa → 5 of 7 went out" | 0 FLEX tests in strict lunar air; 17 near-lunar, **0 went out** | DATA_EXPLAINED |
| HANDOFF same / spice / slice / flex2 "4+ / 150+ / ?" | 4 / 150 / 0 / 0 (from `_report.json`). SAME-R 67 tests = 109 rows (not an error) | HANDOFF |

## 3. New findings 🆕

- **Near-lunar FLEX**: 17 tests at ≥ 30% O₂, 71–72 kPa; none extinguished. → `IDEAS.md` §2
- **CFI helium gap**: helium only at 21% O₂; 17% + He never tested.
- **CFI blend coverage**: only 2 tests per blend at 5 atm.
- **CFI-G inconsistent row**: ignition "No" but outcome "FT".
- **Flow direction** for BASS-II is only in Appendix A (Opposed 67 / Concurrent 38 / Stagnation 15 mentions).
- **Fan calibration** workbook is organised per day and per restrictor count, with a `U cm/s` estimate column.
- **2 CFI `Dext,cool` values** are in the workbook (119) but blank in `clean/cfi.csv` (117). To check.
- **Challenge Resources tab** (10 links): no new data.

## 4. Still open

- [ ] Meaning of FLEX "Disruption" and `Burning rate; mm` unit (FLEX paper on NTRS)
- [ ] Meaning of CFI-G `TFP`
- [ ] The 2 missing CFI `Dext,cool` values in the cleaner
- [ ] Dotson thesis Table 3.1 (individual SPICE smoke points), not checked
- [ ] CFI-G rows per day vs report Tables 1 and 2, not checked

## 5. How it was checked

Read-only Python scripts (CSV + `openpyxl`) and `pdftotext` on the raw files. No project file or script was changed by the checks. The check scripts are not in the repo.
