# P1 & P2: FLEX droplet fires and extinguishing gases

**Investigation:** FLEX, Flame Extinguishment Experiment (PSI-69). ISS, Combustion Integrated Rack (CIR) with the droplet module (MDCA), microgravity.
**One row =** one fuel droplet lit once.

## What we predict

| ID | Target | Column | Values | Baseline |
|---|---|---|---|---|
| **P1** | How the fire ended | `Test end` | Extinction 186 (68%), Disruption 61 (22%), Completion 27 (10%) | 68% |
| **P2** | Burn time (s) | `Burn time; s` | 268 values, 0.3 to 39.2 s | mean |

**App output for P1:** an **extinction boundary chart**: at a chosen O₂ and pressure, how much CO₂ or helium puts a droplet fire out. Shown as a curve on an O₂ vs diluent chart, with the real tests as dots.

## Data

| File | Use |
|---|---|
| `Data/psi/PSI-69/tables/PSI-69_Experimental table_FLEX.csv` | All inputs and both targets. **Windows-1252 encoding.** |
| `Data/psi/PSI-69/investigation.json` | Card text: objective, dates, DOI |

## Inputs

| Column | Range | Cleaning |
|---|---|---|
| `Fuel` | Methanol 157, Heptane 117 | |
| `Ambient pressure; mmHg` | 0 to 2,320 | × 0.1333 → kPa. **Drop the row with 0.** |
| `O initial ambient composition; mole fraction` | 0.12 to 0.34 | This is **O₂**. × 100 → %. |
| `N initial…` | 0.09 to 0.88 | N₂ |
| `CO initial…` | 0 to 0.70 | This is **CO₂** |
| `He initial…` | 0 to 0.45 | Helium |
| `Droplet initial diameter; mm` | 1.1 to 4.67 | **Missing on 12 rows** (261 of 273 filled). Impute or drop for P2. |

Derived: `pO2 = O₂ fraction × pressure_kPa`, `diluent = CO₂ / He / N₂ only`, `diluent_fraction`.

Coverage (fuel × diluent): methanol CO₂ 74 · N₂ 54 · He 28 · heptane CO₂ 48 · N₂ 47 · He 22. Every combination has ≥ 22 tests. 80 test days for the grouped split.

**Do not use as inputs** (these are results, so they would leak the answer): `Visible flame extinction diameter; mm`, `Burning rate; mm`, `Burn time; s` (for P1), `Test end` (for P2).

## Documents to use

| Document | Where | What for |
|---|---|---|
| CFI Science Final Report | `Data/psi/PSI-39/docs/PSI-39_Reports_CFI Science Final Report.pdf` | Background: FLEX is where cool flames were discovered. The report says FLEX observations differ from CFI reignition behaviour (p. 6). |
| CFI presentations | `Data/psi/PSI-39/docs/PSI-39_Presentations_*.pdf` | Plain-language FLEX/CFI story for the AI assistant |
| **FLEX papers, not local** | NASA NTRS | Needed: meaning of "Disruption", unit of `Burning rate; mm` |

## Caveats

- **"Disruption"** (droplet broke apart) isn't a safety outcome like the other two. Plan: also train a 2-class version (*went out early* vs *burned to the end*) until a FLEX paper confirms what Disruption means.
- `Burning rate; mm`: the unit label is ambiguous. **Don't use it** until checked.
- O₂ only up to 34%, and in microgravity only.

## Near-lunar finding (verified 14 Nov 2026)

**0 FLEX tests** meet the strict lunar rule (O₂ ≥ 30% **and** ≤ 70.3 kPa), so `lunar_air` is 0 for every FLEX row. But **17 tests ran at ≥ 30% O₂ and 71 to 72 kPa**, only ~1 kPa above the cutoff (about 10.3 psi vs the 10.2 psi in the brief):

| Fuel | Tests | Ended in |
|---|---|---|
| Heptane | 8 | Disruption 8 |
| Methanol | 9 | Disruption 7, Completion 2 |

**None of the 17 went out by itself** (all N₂ only, no CO₂ or He). Pitch line: *"in near-lunar air, every untreated droplet fire burned to the end or broke apart."* Show these with a **"near-lunar"** label, never as "lunar". See `../IDEAS.md` (near-lunar band).

## Open questions

- [ ] Find a FLEX paper on NTRS and define "Disruption"
- [ ] Check `Burning rate; mm` unit
- [x] Count tests per test day for the grouped split: **80 test days**
