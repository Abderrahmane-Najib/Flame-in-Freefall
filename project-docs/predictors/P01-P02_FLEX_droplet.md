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
| `Droplet initial diameter; mm` | | |

Derived: `pO2 = O₂ fraction × pressure_kPa`, `diluent = CO₂ / He / N₂ only`, `diluent_fraction`.

## Documents to use

| Document | Where | What for |
|---|---|---|
| CFI Science Final Report | `Data/psi/PSI-39/docs/PSI-39_Reports_CFI Science Final Report.pdf` | Background: FLEX is where cool flames were discovered. The report says FLEX observations differ from CFI reignition behaviour (p. 6). |
| CFI presentations | `Data/psi/PSI-39/docs/PSI-39_Presentations_*.pdf` | Plain-language FLEX/CFI story for the AI assistant |
| **FLEX papers, not local** | NASA NTRS | Needed: meaning of "Disruption", unit of `Burning rate; mm` |

## Caveats

- **"Disruption"** (droplet broke apart) isn't a safety outcome like the other two. Plan: also train a 2-class version (*went out early* vs *burned to the end*) until a FLEX paper confirms what Disruption means.
- `Burning rate; mm`: the unit label is ambiguous. **Don't use it** until checked.
- O₂ only up to 34%, so a few tests sit near lunar-base air, but at microgravity.

## Open questions

- [ ] Find a FLEX paper on NTRS and define "Disruption"
- [ ] Check `Burning rate; mm` unit
- [ ] Count tests per test day for the grouped split
