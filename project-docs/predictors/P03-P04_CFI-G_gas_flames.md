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
| `Fuel` | 30% butane 52, 30% propane 36, 50% butane 30, 30% ethane 27, propane 20, ethane 14 | Use **only the gas name** (`fuel_gas`). **Don't take the fuel fraction from this label**: it's the bottle mix, not what burned (see `Xf`) |
| `XO2 before test` | 0.18 to 0.40 | Chamber O₂. × 100 → % |
| `approx p (bar)` | 0.51 to 3.04 | × 100 → kPa |
| `Xf` | 0.027 to 1 | **The real fuel fraction in the burner gas.** 26 tests labelled "30% propane/butane" actually ran at 2.7 to 4.7% fuel. `clean_tables.py` already uses `Xf` → `burner_fuel_pct` ✅ |
| `mHC (mg/s)` | | Fuel flow |
| `Tad (K)`, `Zst` | | **OK to use.** Both are calculated from the *starting* conditions (before ignition), so they don't leak the answer, and they carry the physics (flame temperature, mixture). Keep them as optional inputs and compare with/without. |
| `Day` | 11 days | For grouped split (only 11 groups, so the cross-validation is coarse) |

**Do not use as inputs** (they are measured after ignition or contain the answer):
- `burn time`, `Peak burner T`, `Color`, `XO2 after test`
- `Cool flame?`: an outcome
- `TFP`: "Yes" only on flames that ignited (18 of 18), so it leaks P3. Meaning not documented.
- `Comments`: contains answers ("direct cool - no hot ignition", "Cool flame!", "Lowest flow rate for ignition")

## Documents to use

| Document | Where | What for |
|---|---|---|
| **CFI-G Final Report** (2022) | `Data/psi/PSI-159/docs/PSI-159_Reports_FinalRpt_ACME.CFI-G.pdf` | Tables 1 and 2 (p. 21 to 22): flames ignited per test day, a **cross-check for row counts**. Table 3 (p. 46): 11 **gas cool flames** at ~39% O₂, 2 bar (for the "invisible fire" story). Normal vs inverse configuration. |
| ACME non-imaging data file description | `Data/psi/PSI-23/docs/PSI-23_Science Documents_ACME non-imaging data file description.pdf` | Column meanings for ACME logs |
| ACME fact sheets / ISS Researchers Guide | `Data/psi/PSI-23/docs/` | Plain-language hardware explanation |

## Caveats

- **Inverse flames are different physics.** Their `XO2` (0.12 to 0.85) is oxygen **inside the burner stream**, blown into a fuel-filled chamber. It is **not cabin oxygen.** Never plot on the same axis without a different marker and label. Never train P3/P4 on them.
- Inverse ignition values mix case (`Yes`/`yes`, `No`/`no`), plus `flash` (8). Normalise before counting.
- 115 normal flames are at ≥ 30% O₂, but only **20** are also at ≤ 70.3 kPa (lunar-like air): 17 ignited, 3 didn't; of those, SE 13 / FT 5 (one row is inconsistent, see below). **20 is too few for a separate model**: in the lunar zone show the nearest real tests, not a percentage.
- **Inconsistent row:** one test has `Hot ignition` = No but `Self-ext or flow term` = FT. Flag it and drop it from P4.

## Open questions

- [x] Count normal-flame tests in lunar-like air (≥30% O₂ and ≤70 kPa): **20** (verified 14 Nov 2026)
- [ ] Check row counts per day against report Tables 1 and 2
- [ ] Find what `TFP` means (ACME non-imaging data file description?)
