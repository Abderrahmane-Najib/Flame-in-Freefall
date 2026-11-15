# Predictors: training (P1–P8) and solid-fuel extraction (P9–P11)

*Work of 14 Nov 2026, branch `predictors-and-solids-extraction`. Background and per-predictor specs: `predictors/README.md` and `predictors/P*.md`.*

## In one paragraph

P1–P8 are trained and saved as small JSON models that the app can run with the Python standard library alone. Each answer comes with a trust badge, the 7 nearest real tests, caveats and sources. Every model was scored on test days it never saw, and every one beats its baseline. For solids, we transcribed the outcome of **250 BASS / BASS-II tests** from the NASA report and workbooks into CSVs with page references. That data is ready to give P10 its real test dots (the blowoff branch lands on NASA's curve), P11 its fabric chart and P9 an outcome map; none of the three is drawn in the app yet. **P9 has no model**: the classes are too unbalanced within any one material.

## What is trained and what is not

| ID | What | Status |
|---|---|---|
| P1 / P1b | FLEX droplet: how the fire ends (3 classes / went out early vs burned on) | ✅ trained |
| P2 | FLEX droplet burn time | ✅ trained |
| P3 / P4 | CFI-G gas flame: ignites? / goes out by itself? | ✅ trained |
| P5 / P6 / P6b | CFI hot-flame burn time / extinction diameter (/ D₀) | ✅ trained |
| P7 / P8 | CFI cool-flame end state / reignition | ✅ trained |
| P9 | Solid material outcome | 📊 250 tests extracted, **no model** (see below) |
| P10 | PMMA flammability boundary | NASA's formula, nothing to train. 38 test points built |
| P11 | Fabric ignition / quench limits | 📊 chart data built (by design, no model) |

## How to run

```
pip install pandas scikit-learn scipy          # training only; the app runtime needs none of these
python scripts/train_predictors.py             # trains P1–P8 → models/<ID>.json + models/REPORT.md
python scripts/predict.py P3 '{"fuel":"propane","o2_pct":21,"pressure_kpa":101,"burner_fuel_pct":30,"fuel_flow_mg_s":1}'

# solids (needs the raw docs: python scripts/psi_download.py --only PSI-25,PSI-26)
python scripts/extract_p9_olson.py      # stage 1  → data/psi/extracted/p9_olson.csv
python scripts/extract_p9_tien.py       # stage 2  → p9_tien.csv + p11_sibal.csv
python scripts/extract_p9_stage3.py     # stage 3  → p9_stage3.csv
python scripts/extract_p9_bass.py       # stage 4  → p9_bass.csv
python scripts/build_p9_dataset.py      # merge    → p9_solids.csv (+ class counts)
python scripts/build_p10_points.py      # P10 dots → p10_olson_points.csv
```

The outputs (`models/`, `data/psi/extracted/`) are committed, so the app works straight after cloning.

## Part 1: training P1–P8

### Method

- **Models:** logistic regression for classes, ridge (lightly penalised) linear regression for numbers. Shallow gradient boosting (depth 2, 150 trees) runs on the same folds as a challenger. It is adopted only if it clearly wins (≥ 10% lower log loss or MAE, and ≥ 3 points of balanced accuracy for classes). **It won nowhere.** XGBoost was not used: it is the same family and brings no gain at 117–273 rows.
- **Validation:** whole test days are held out, never random rows. CFI-G uses leave-one-day-out (11 days); FLEX (80 days) and CFI (40 days) use 10 grouped folds. Baselines (majority class or mean) come from the training folds only.
- **Inputs:** only starting conditions. The "do not use" columns in each predictor spec are excluded.
- **Runtime (`scripts/predict.py`):** standard library only. It reads `models/<ID>.json` and returns the answer, the trust badge (*tested here* / *between tests* / *outside*), the 7 nearest real tests, caveats and sources. The trainer and the runtime share the same feature code (`derive()`), and the trainer checks that the runtime reproduces scikit-learn's outputs to 1e-9.
- **Display rules in the JSON:**
  - lunar zone (CFI-G, O₂ ≥ 30% and ≤ 70.3 kPa) → nearest tests only
  - CFI 17% O₂ + helium → "never tested"
  - CFI blends at 5 atm → nearest tests only
  - FLEX near-lunar (70.3 < p ≤ 72.5 kPa, same band as the API) → label

### Results (held-out test days)

| ID | Rows | Baseline | Linear model | Verdict |
|---|---|---|---|---|
| P1 | 273 | acc 68% | acc 74%, AUC 0.77 | Never predicts "completion" (27 tests); prefer P1b |
| P1b | 273 | acc 68% | acc 81%, AUC 0.85 | Good |
| P2 | 259 | MAE 6.0 s | MAE 3.4 s, R² 0.63 | Usable, show the range |
| P3 | 177 | acc 75% | acc 79%, AUC 0.75 | Weakest |
| P4 | 132 | acc 77% | acc 77%, AUC 0.83 | Ranks risk well; accuracy equals baseline |
| P5 | 143 | MAE 3.2 s | MAE 1.0 s, R² 0.83 | Strong |
| P6 | 141 | MAE 0.64 mm | MAE 0.14 mm, R² 0.92 | Strong |
| P7 | 117 | acc 59% | acc 79%, AUC 0.87 | Good |
| P8 | 145 | acc 76% | acc 79%, AUC 0.89 | Good (35 positives) |

Full tables with confusion matrices: `models/REPORT.md`.

### Decisions and fixes made while training

- **Cleaning bug fixed:** `clean_tables.py` read spreadsheet error cells (`#DIV/0!`) as 0; they are now blank. This changed 2 rows of `cfig_normal.csv`: aborted CFI-G attempts with no fuel flow (`Xf = 0`). Those 2 rows are excluded from P3/P4.
- **P3 needs flame physics:** with the plain inputs, ignition was not predictable on unseen days (AUC 0.49), because ignition rises and then falls with fuel strength. We compute `Zst` exactly from fuel, `Xf` and O₂ (matches NASA's column to 1e-6). We estimate `Tad = 300 + 2859·(1 − exp(−h / 2.495 MJ/kg))`, with h = Zst·Y_fuel·LHV, which is within ~21 K of NASA's column. With these, P3 scores as well as with NASA's own columns, and the app can compute both from user inputs. The trainer re-checks both on every run.
- **P2:** heptane gets its own slope per input, plus O₂² (MAE 4.5 → 3.4 s; this is what beat boosting). **P5:** pressure enters both as log and linear (MAE 1.28 → 1.01 s).
- CFI `fiber` is not used (blank on a third of rows; the report says it has little effect).

## Part 2: solid-fuel extraction (P9, P10, P11)

### Sources and stages

| Stage | Source | Tests | Output |
|---|---|---|---|
| 1 | BASS-II report Table A.5 (Olson, PMMA rods), viewer pp. 118–119, + 3 workbook-only 2016 tests | 27 | `p9_olson.csv` |
| 2 | Table A.6 (T'ien, SIBAL fabric), pp. 120–121, + Table 7.1 (p. 104) | 29 | `p9_tien.csv`, `p11_sibal.csv` |
| 3 | Tables A.1–A.4 (Bhattacharjee films, Ferkul Nomex, Fernandez-Pello rods, Miller slabs), pp. 111–117 | 73 | `p9_stage3.csv` |
| 4 | BASS as-run workbook (spheres, candles, fabrics, slabs) | 121 | `p9_bass.csv` |
| | **Merged** | **250** | `p9_solids.csv` |

- **How:** the PDF text layer drops most of each table row, so stages 1–3 were read from 220-dpi page renders. Stage 4's text was already in the workbook, so only the label is hand-written there. Every row keeps the verbatim observation, a `confidence`, `notes` and its page or workbook row.
- **Checks:** all 129 BASS-II rows match NASA's BASS-II CSV on calibrated O₂, flow restrictor and sample number. The fresh SIBAL counts (6 quench, 3 no ignition, 1 blowoff) equal the counts stated in report §7.1.4.
- **Labels:** `keeps_burning`, `quench` (out while flow turned down or off; flow off = 0), `blowoff` (out when flow turned up), `self_extinguished` (out at a steady, not-low flow), `no_ignition`, `extinguished_unclear`, `suppressed_n2` (put out by the nitrogen jet), blank (end not stated, or igniter failure).
- **Flags:** `reused` (partly burned sample), `n2_suppression_used`, `low_confidence_label`, typos fixed and noted (2018 dates → 2014, impossible final-O₂ values blanked).

### Flow conversion (pot → cm/s)

`scripts/fan_calibration.py` reads the BASS-II fan calibration (per day and per restrictor count; U = 1.0066 × air display).

- **Below the lowest calibrated pot (0.5) we do not extrapolate.** Readings there range from 0 to 3.8 cm/s from day to day, so those flows are stored as a range (0, ceiling]. NASA's Fig. 6.10 shows the same uncertainty as wide error bars.
- Days 209–210 are flagged: the anemometer read ~40% low until a "post soot cleaning" calibration.
- BASS (2012–13) fan values have no calibration file; only air-display flows are converted.

### What it gives the app

- **P10:** 38 points (outcome + last stable flow per Olson test, final O₂). The **8 blowoff points lie on NASA's Eq. 6.1** (O₂ − boundary = −0.84 to +0.47). Quench points are flow ranges that all cross the quench branch. Draw them as horizontal bars.
- **P11:** Table 7.1 as a chart table. Fabric: no ignition at 16.4–16.8% O₂, complete burn at 17.1%, quench at 2–5 cm/s.
- **P9: no model.** Usable rows (labelled, fresh sample, no N₂): 137, spread over 15 material × shape × flow-direction groups. The largest group has 29 tests, and several are almost one class (PMMA rods in opposed flow: 16 quench, 1 other). P9 is meant to ship as an outcome map plus the nearest real tests (data ready, not in the app yet).
- **Headline numbers** (fresh samples, starting O₂):
  - Nomex: no ignition at 21–22.5% (burned once at 22.0% with the igniter left on)
  - Ultem: never ignited
  - SIBAL fabric: sustained flame down to 16.9%
  - PMMA rods: down to 14.8%
  - wax candles: down to 15.9%

## Open items

- **In the app (15 Nov):** Flame Lab uses P1b, P6b, P7, P8; the Predict page uses P10. P1–P6 are served by the API only (`/predict/models`), and the P9 / P10 dots / P11 data is not drawn yet.

- **Human check** of the stage 3 and 4 labels, starting with the rows where `confidence` = low. Stages 1–2 were checked.
- P1's extinction-boundary chart (sweep CO₂/He at P(extinction) = 0.5) is not built yet. P7: find the 2 `Dext,cool` values blank in the clean CSV (needs the PSI-39 workbook).
- Hooking `scripts/predict.py` into the API: `predict(pid, inputs)` already returns everything the Predict page needs (answer, trust, nearest tests, caveats, sources).
- `clean_tables.py` was re-run only for CFI-G on this PC. A full rebuild with all raw data should be checked for other `#…!` cells.
