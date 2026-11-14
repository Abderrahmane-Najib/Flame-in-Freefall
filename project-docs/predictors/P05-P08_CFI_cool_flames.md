# P5 to P8: CFI cool flames ("the invisible fire")

**Investigation:** Cool Flames Investigation, CFI (PSI-39). ISS, CIR with the droplet module (MDCA), microgravity.
**One row =** one fuel droplet lit once.

**Pitch story:** the visible (hot) flame goes out, but an almost invisible **cool flame** keeps burning, and at higher pressure it can **re-light the hot flame**. Anyone watching for a visible flame would think the fire was out.

## What we predict

Only rows with `Completed Analysis?` = **Yes (146 of 227)**.

| ID | Target | Column (`DATA` sheet) | Rows | Range / classes | Baseline |
|---|---|---|---|---|---|
| **P5** | Hot-flame burn time (s) | `HF Burn Time` | 143 | 1.9 to 21.6 s | mean |
| **P6** | Hot-flame extinction diameter (mm) | `Dext, hot ( mm )` | 141 | 2.8 to 6.4 mm. Also try `Dext,hot / D0` to remove droplet size. | mean |
| **P7** | Cool-flame end state | `Dext,cool ( mm )` | 117 | **> 0** = cool flame went out early (69) · **= 0** = cool flame consumed the droplet (48) · blank = no measurement, **excluded** (29) | 59% |
| **P8** | Did it reignite? | `Reignitions` > 0 | 145 | none 110 / one or more 35 | 76% |

Extra target if useful: `khot ( mm²/s )` (hot burning rate, 145 rows).

*Counts re-checked on 14 Nov 2026 against `data/psi/clean/cfi.csv` (analysed tests only). The earlier numbers (147 / 144 / 71 / 151) didn't filter to analysed tests. ⚠️ The raw workbook has **119** `Dext,cool` values, the clean CSV **117**: check which 2 the cleaner blanked and why.*

## Data

| File | Use |
|---|---|
| **`Data/psi/PSI-39/docs/PSI-39_Science Documents_CFI_DataSummary_Spreadsheet_Jan2021.xlsx`** | **Main source.** Sheets joined on `Flex Number` (227 tests, no duplicates): `Master Sheet` (conditions), `DATA` (results), `Comments` (explains gaps), `Igniter`, `Camera Settings`. `Graphs` is empty. |
| `Data/psi/PSI-39/tables/PSI-39_Experimental table_CFI.csv` | **Don't use.** 87 rows = 79 unique tests, all already in the workbook. |
| `Data/psi/PSI-39/investigation.json` | Card text |

## Inputs (146 analysed tests)

| Input | Values | Cleaning |
|---|---|---|
| Pressure | 0.5 to 5 atm (7 levels) | Master Sheet is text (`"1 atm"`, `".5 atm"`). Use the numeric `Pressure (atm)` in `DATA`. × 101.325 → kPa. |
| O₂ | **0.21 (118) or 0.17 (28) only** | |
| He | 0, 0.29, 0.59 | ⚠️ **Helium was only used at 21% O₂** (21% + He 0: 89, He 29%: 17, He 59%: 12; 17% O₂: He 0 only). The app must not predict "17% O₂ + helium": show **"never tested"** instead. |
| Fuel | n-dodecane 72, 60/40 dodecane/iso-dodecane 42, 75/25 blend 32 | Farnesane (44) has no analysed results |
| Fiber | Yes / No / blank | Droplet on a support fibre or free-floating. Report: little effect on extinction diameter. |
| `D0 ( mm )` | 3.8 to 6.4 | Initial droplet size |

## Documents to use

| Document | Where | What for |
|---|---|---|
| **CFI Science Final Report** | `Data/psi/PSI-39/docs/PSI-39_Reports_CFI Science Final Report.pdf` | p. 6 (§c): *"above 2 atm, multiple reignition cycles … until the fuel droplet is completely consumed"*, the basis for reading `Dext,cool = 0`. p. 8 to 10 (§5.3, Figs. 4 and 5): cool-flame extinction vs pressure; *helium dilution gives a larger extinction diameter.* |
| CFI SCR / SRD | `…/PSI-39_Science Documents_CFI_SCR.pdf`, `…_SRD_CFI.pdf` | Definitions of `D0`, `Dext,hot`, `Dext,cool`, `khot`, `kcool` with worked examples |
| CFI presentations | `…/PSI-39_Presentations_*.pdf` | Pitch images and plain-language text |
| PSI-117 "Cool Flames in Space" seminar (26 Mar 2026) | `Data/psi/PSI-117/docs/PSI-117_Presentations_PSI_Users_Group_Cool_Flames_in_Space_03302026.pdf` | Latest cool-flame summary for the AI assistant |
| **Nayagam et al. 2015**, *Cool-flame extinction during n-alkane droplet combustion in microgravity*, Combustion and Flame 162(5). **Not local.** | Journal | Confirm the `Dext,cool` 0 / blank meaning |

## How we read the cool-flame columns (P7)

| `Dext,cool` | Tests | Has `kcool` | At ≥ 2 atm | With reignitions |
|---|---|---|---|---|
| > 0 | 69 | 69 | 17 | 12 |
| = 0 | 48 | 48 | 41 | 21 |
| blank | 29 | 7 | 4 | 2 |

**0 is not "no cool flame"**: every zero row has a cool-flame burning rate and almost all are at high pressure, which matches the report. Blank rows usually had a camera problem (e.g. test 1208: *"IPSUG did not switch to continuous mode"*). This is **our interpretation**, not a NASA definition.

`Extrap CF?` = 1 seems to mean the cool-flame diameter was **extrapolated**, not seen directly. Use it as a quality flag.

## Caveats

- **Not relevant to lunar oxygen:** only 17% and 21% O₂. Its value is **pressure (0.5 to 5 atm) and helium**.
- **Fuel × pressure coverage** (analysed tests): every fuel was run at all 7 pressures, but the blends are thin at the ends. n-dodecane: 4/4/30/4/3/16/11 tests at 0.5/0.75/1/1.25/2/3/5 atm. 60/40 blend: 4/4/11/4/4/13/2. 75/25 blend: 1/3/11/4/5/6/2. At 5 atm the blends have only 2 tests each, so show nearest tests there, not a model value.
- **Do not use as inputs** (results): `Dext,hot`, `Dext,cool`, `khot`, `kcool`, `HF Burn Time`, `Reignitions`, `Extrap CF?`, radiometer columns, `Actual D`.
- Radiometer columns (`Rad Ratio`, `CF Rad Ratio`, `Peak … Rad`, `2.5mm …`) are display only. `2.5mm CF` ranges oddly from 36 to 7,196.
- Report Fig. 3 caption says test 1268 was 12% O₂. The workbook says 21% (21 + 50 + 29 = 100). **Trust the workbook.**

## Open questions

- [ ] Confirm `Dext,cool` = 0 / blank and `Extrap CF?` in Nayagam et al. 2015
- [x] Check the fuel × pressure × He coverage grid (see Caveats)
- [ ] Find the 2 `Dext,cool` values that are in the workbook but blank in `clean/cfi.csv`
