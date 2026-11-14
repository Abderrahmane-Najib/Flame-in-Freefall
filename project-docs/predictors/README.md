# Predictors

What the app will predict, the data and documents each prediction uses, and the rules every prediction must follow.
All counts were taken from the files in `Data/psi/` on 12 Nov 2026 and **re-verified against the raw files and report PDFs on 14 Nov 2026** (see `../VERIFICATION.md`). Background research: `../DOCS_FINDINGS.md`. Product ideas: `../IDEAS.md`.

## The predictors

| ID | What we predict | Fire type | Safety job | File | Status |
|---|---|---|---|---|---|
| P1 | How a droplet fire ends (extinction / disruption / completion) | Liquid droplet | Suppression | [P01-P02_FLEX_droplet.md](P01-P02_FLEX_droplet.md) | ✅ ready |
| P2 | Droplet burn time (s) | Liquid droplet | Suppression | [P01-P02_FLEX_droplet.md](P01-P02_FLEX_droplet.md) | ✅ ready |
| P3 | Will a gas flame ignite? | Gas | Prevention | [P03-P04_CFI-G_gas_flames.md](P03-P04_CFI-G_gas_flames.md) | ✅ ready |
| P4 | Once lit, does it go out by itself? | Gas | Prevention | [P03-P04_CFI-G_gas_flames.md](P03-P04_CFI-G_gas_flames.md) | ✅ ready |
| P5 | Hot-flame burn time (s) | Liquid droplet | Detection / suppression | [P05-P08_CFI_cool_flames.md](P05-P08_CFI_cool_flames.md) | ✅ ready |
| P6 | Hot-flame extinction diameter (mm) | Liquid droplet | Suppression | [P05-P08_CFI_cool_flames.md](P05-P08_CFI_cool_flames.md) | ✅ ready |
| P7 | Cool-flame end state (goes out early / consumes the droplet) | Liquid droplet | Detection | [P05-P08_CFI_cool_flames.md](P05-P08_CFI_cool_flames.md) | ⚠️ caveats |
| P8 | Will the flame reignite? | Liquid droplet | Detection | [P05-P08_CFI_cool_flames.md](P05-P08_CFI_cool_flames.md) | ⚠️ small |
| P9 | Solid material: keeps burning / quenches / blows off / no ignition | Solid | Prevention | [P09_solids_burn_outcome.md](P09_solids_burn_outcome.md) | ✅ **250 tests extracted** (`data/psi/extracted/p9_solids.csv`). 📊 chart + nearest tests, **no model** (classes too unbalanced per material) |
| P10 | PMMA flammability boundary (O₂ vs flow) | Solid | Prevention | [P10_PMMA_flammability_boundary.md](P10_PMMA_flammability_boundary.md) | ✅ curve + 38 test points (`p10_olson_points.csv`); blowoff branch reproduced |
| P11 | Fabric ignition / quench limits | Solid | Prevention | [P11_fabric_limits.md](P11_fabric_limits.md) | 📊 chart only, ✅ data ready (`p11_sibal.csv`) |

**Build order:** P1–P4 and P10 curve first → P5–P8 → P11 → P9 stages 1 to 4 → P9 model (optional).

Sources used in the app but **not** for predictions (smoke, soot, Saffire): [context_sources.md](context_sources.md).

## Training (done 14 Nov 2026)

```
python scripts/train_predictors.py          # trains P1-P8 → models/<ID>.json + models/REPORT.md
python scripts/predict.py P3 '{"fuel":"propane","o2_pct":21,"pressure_kpa":101,"burner_fuel_pct":30,"fuel_flow_mg_s":1}'
```

- **Models:** logistic regression (classes) and ridge linear regression (numbers). Shallow gradient boosting runs as a challenger on the same folds and is adopted only if it clearly wins (≥ 10% lower log loss / MAE and, for classes, ≥ 3 points balanced accuracy). **It won nowhere.**
- **Validation:** whole test days held out (leave-one-day-out for CFI-G's 11 days, 10 grouped folds for FLEX and CFI). Baselines come from the training folds only.
- **Runtime:** `scripts/predict.py` is standard-library only. It reads the JSON, computes the same derived inputs as training (shared `derive()`), and returns answer + trust badge + 7 nearest tests + caveats + sources. The trainer checks the runtime reproduces scikit-learn exactly.
- **Extra models:** `P1b` (2-class FLEX: went out early vs burned on) and `P6b` (Dext,hot / D0).

| ID | Rows | Baseline | Linear model (held-out days) |
|---|---|---|---|
| P1 | 273 | acc 68% | acc 74%, bal. acc 0.48, AUC 0.77. Completion is never predicted (27 tests) → prefer P1b in the app |
| P1b | 273 | acc 68% | acc 81%, bal. acc 0.76, AUC 0.85 |
| P2 | 259 | MAE 6.0 s | MAE 3.4 s, R² 0.63 |
| P3 | 177 | acc 75% | acc 79%, bal. acc 0.67, AUC 0.75. **Weakest model**: needs Tad/Zst (see below) |
| P4 | 132 | acc 77% | acc 77%, bal. acc 0.63, AUC 0.83 |
| P5 | 143 | MAE 3.2 s | MAE 1.0 s, R² 0.83 |
| P6 | 141 | MAE 0.64 mm | MAE 0.14 mm, R² 0.92 |
| P6b | 141 | MAE 0.048 | MAE 0.031, R² 0.44 |
| P7 | 117 | acc 59% | acc 79%, bal. acc 0.79, AUC 0.87 |
| P8 | 145 | acc 76% | acc 79%, bal. acc 0.72, AUC 0.89 |

**Decisions made while training:**
- **P3/P4: 2 CFI-G rows excluded** (`521125 A4`, `521125 H3`): Xf = 0 and fuel flow = 0, so no fuel flowed (aborted attempts, `Tad = #DIV/0!` in the raw table). `clean_tables.py` used to turn `#DIV/0!` into 0; spreadsheet error cells are now blank.
- **P3 uses Zst and an estimated Tad.** The plain inputs can't predict ignition on unseen days (AUC 0.49) because ignition rises then falls with fuel strength. `Zst` is computed exactly from fuel, Xf and O₂ (matches NASA's column to 1e-6). `Tad` is estimated as `300 + 2859·(1 − exp(−h/2.495 MJ/kg))`, h = Zst·Y_fuel·LHV, within ~21 K of NASA's value. With these, P3 scores the same as with NASA's own columns. The trainer re-checks both on every run.
- **P2:** heptane gets its own slope per input, plus O₂² (MAE 4.5 → 3.4 s). **P5:** pressure enters both as log and linear (MAE 1.28 → 1.01 s).
- **CFI `fiber` not used** (blank on a third of rows; report says little effect).
- Trust badge: *tested here* if a same-category test is within 0.25 SD; *between* if inside that category's tested box and within 1 SD; else *outside*.

## Coverage of the three safety jobs

| Job | Predictors | Notes |
|---|---|---|
| **Prevention** (what will burn?) | P3, P4, P9, P10, P11 | P4 is the only one **in** lunar-like air (20 tests). P1 adds 17 **near-lunar** FLEX tests (≥ 30% O₂, 71–72 kPa) |
| **Detection** (will we notice it?) | P7, P8 | Indirect: the "invisible fire" risk. No smoke-alarm predictor is possible (see context_sources.md). |
| **Suppression** (how do we put it out?) | P1, P2, P5, P6 | P1 gives the CO₂ / helium extinction boundary |

## Rules for every predictor

### Building
1. **One model per dataset.** Never pool droplets, gas flames and solids.
2. **Small, interpretable models first:** logistic regression for yes/no targets, linear regression for numbers. Use gradient boosting only if it clearly wins. 100 to 300 rows is too few for deep models.
3. **Inputs with physical meaning:** O₂ partial pressure (`O₂ fraction × pressure`), total diluent fraction, diluent type, fuel, flow. Keep pressure as its own input too.
4. **Test on whole groups.** Hold out whole test days or campaigns, not random rows. Tests from the same day are near-copies.
5. **Always report the baseline** (majority class % or the mean) next to the score.
6. **Missing stays missing.** A blank result is excluded, never counted as "no".
7. **Keep provenance.** Every training row keeps `source_file`, `source_row` and, for values pulled from reports, the page.
8. **No leaking inputs.** Never use a column measured *after* ignition, or a free-text comment, as an input. Each predictor file lists its "do not use" columns. Calculated values from the *starting* conditions (e.g. CFI-G `Tad`, `Zst`) are allowed.
9. **No untested combinations.** If a combination of inputs never appears in the data (e.g. CFI 17% O₂ + helium), show "never tested" and nearest tests only, not a model value.

### Showing a prediction
- **The 7 closest real tests** with their real outcomes.
- **A trust badge:** *Tested here* / *Between tests* / *Outside tested range* (no prediction shown, only nearest tests).
- **The gravity caveat:** every test was in microgravity. For Moon or Mars: *"microgravity evidence only. Moon/Mars gravity never tested."* P10 can also show the Earth (1 g) limit, so the Moon is shown as a **range between the two**, not a number.
- **Links to the source rows and document pages** listed in each predictor file.
- **Lunar vs near-lunar:** "lunar-like air" = O₂ ≥ 30% and ≤ 70.3 kPa (strict). Tests just outside (e.g. FLEX at 71–72 kPa) get a separate **"near-lunar"** label, never "lunar".
- **Explanation level:** the same numbers are shown at every level (Explorer / Student / Researcher, see `../IDEAS.md`). Only the wording changes.

## What we will not predict

| Not possible | Why |
|---|---|
| A single "fire risk %" | Each dataset measures something different |
| Anything at Moon or Mars gravity | No partial-gravity data in PSI |
| Smoke alarm timing | No "alarm went off" data in SAME / SAME-R |
| Saffire large fires | 2 to 9 tests per mission |
| CFI-G inverse ignition | Only 15 failures out of 154 |
