# Visualisations

Charts and views for the app, apart from the predictors (see `predictors/`).
Split into **what we can build now** with the files in `Data/psi/`, and **what we can add later** once more data is downloaded or extracted.
Checked 12 Nov 2026. **Re-verified 14 Nov 2026** (see `VERIFICATION.md`): all V1–V13 are doable with the data on disk.

---

## 1. Ready now (data already on disk)

| # | Visual | What it shows | Data | Priority |
|---|---|---|---|---|
| V1 | **O₂ vs pressure coverage map** | Every test as a dot (O₂ % vs kPa), coloured by investigation | Clean CSVs: **~1,600 tests** have both O₂ and pressure (some SPICE / s-Flame values are assumed, see `o2_assumed` / `pressure_assumed`) | ⭐ main screen |
| V2 | **Evidence grid** | Fuel type × safety job, with number of investigations / tests per cell. Empty cells = evidence gaps. | Categories in `DATA_EXPLAINED.md` §7 | ⭐ |
| V3 | **Condition range bars** | One bar per investigation for its O₂, pressure and flow range, so overlaps are visible | Test tables | High |
| V4 | **"What changed / what stayed fixed"** | Per investigation: varied vs constant variables, and sensors used | Test tables + SRD documents | High |
| V5 | **Timeline** | Investigation dates, coloured by hardware | `Data/psi/investigations.csv` | Medium |
| V6 | **Hardware family tree** | Rack → module → investigations | `DATA_EXPLAINED.md` §5, `experimentHardware` in `investigation.json` | Medium |
| V7 | **Microgravity vs Earth comparison** | Paired values showing fire behaves differently in space | BASS-II report, Saffire-II CSV, SPICE thesis | ⭐ |
| V8 | **Smoke fingerprint** | Smoke particle size per material, fresh vs aged | SAME Final Science Report, Table 1 | High |
| V9 | **Shrinking droplet animation** | Hot flame → invisible cool flame, for a chosen CFI test | CFI workbook | ⭐ pitch hook |
| V10 | **Flame colour / soot strip** | Blue vs yellow flames against O₂ and pressure | CFI-G `Color` column, BASS observation text | Low |
| V11 | **Data quality panel** | Per table: rows, empty rows, repeats, has results?, conversions applied | Our checks | High (trust) |
| V12 | **Investigation cards with photo** | Goal, hardware, dates, DOI, publications, an official image | `investigation.json` (only 5 of 24 have an `images` entry, 13 images in total) | ⭐ |
| V13 | **PMMA flammability boundary** | U-shaped "will it burn?" curve | Predictor P10 | ⭐ |

### Details

**V1: Coverage map**
- Shaded zones: **ISS** (21%, 101 kPa) and **lunar base / rover** (≥ 30%, ≤ 70 kPa). Mars marked "not defined, assumed lunar-like".
- A dashed line for **O₂ partial pressure = 21 kPa** (same oxygen per breath as Earth air) to show why low pressure + high O₂ is a different environment.
- **CFI-G inverse flames use a different marker** with a label: their O₂ is inside the burner stream, not the cabin air.
- **Gravity toggle** (Orbit / Moon / Mars): the dots don't move, but every one is labelled *"tested in microgravity only"* for Moon and Mars.
- Click a dot → its source row and investigation card.
- Clean first: units to kPa, O₂ fractions to %, drop the FLEX 0-pressure row and the 861 empty CFI-G rows.
- **Near-lunar band** (new): a lighter zone around the lunar box (e.g. O₂ ≥ 30%, ≤ 75 kPa). It picks up the **17 FLEX tests at 71–72 kPa**, so the lunar evidence goes from 20 gas-flame tests to 20 + 17 across two fuel families. Always labelled "near-lunar".
- **Assumed values** use a hollow marker (SPICE, s-Flame). Tables with no O₂/pressure at all (BASS-II pressure, SAME, SAME-R, Saffire) are **missing from the map** unless we assume ISS cabin air. If we do, use the hollow marker and a note.
- Count check (clean CSVs, 14 Nov): FLEX 273, CFI 227, CFI-G 179 + 154 inverse, Flame Design 207 + 111, BASS 121, SPICE 150 tests (469 rows), s-Flame ~191.

**V2: Evidence grid**

| | Prevention | Detection | Suppression |
|---|---|---|---|
| Solid | BASS, BASS-II, Saffire | SAME, SAME-R | — |
| Liquid droplet | — | (CFI cool flames) | FLEX, FLEX-2, CFI |
| Gas | CFI-G, BRE | SPICE, SLICE | — |

Cell colour = number of tests. A "lunar air" switch shows only the **20 tests in lunar-like air**, which makes the gap obvious.

**V7: Microgravity vs Earth**

| Comparison | Space (µg) | Earth (1 g) | Source |
|---|---|---|---|
| Minimum O₂ for PMMA rods to burn | **13.5%** | 15.4% | BASS-II report §6.1, p. 84 ✅ verified |
| Lowest O₂ with PMMA flame spread | **17.5%** | 19% | BASS-II report §4, p. 58 ✅ verified |
| Saffire-II flame spread | `?-g Spread Length` (mostly words: `~ 0`, `29 cm`) | `1-g Spread Rate` (mostly words: `Complete`, `Acceleratory`) | `PSI-99/tables/…SAFFIRE-2.csv`, **9 tests**, qualitative only |
| SPICE smoke points | Thesis Table 3.1 | Thesis Tables 6.3, 6.4 | `PSI-107/docs/…DotsonThesis.pdf` |

Message: *some materials burn at lower oxygen in space than on Earth.*

**V8: Smoke fingerprint**

| Material | Mean diameter (nm) | Aged (nm) |
|---|---|---|
| Kapton | 105 | 186 |
| Teflon | 205 | 273 |
| Lamp wick | 227 | 308 |
| Silicone | 257 | 422 |

Dumbbell chart (fresh → aged) per material. Message: *small Kapton/Teflon smoke is hard for light-scattering detectors (the ISS type); smoke grows when it sits in still air.*

**V9: Shrinking droplet animation**
- Uses the workbook's real values per test: `D0`, `khot`, `Dext,hot`, `kcool`, `Dext,cool`.
- Droplet law: `d² = d₀² − k·t`. Hot phase until `Dext,hot`, then cool phase (dim blue glow) until `Dext,cool`. If `Dext,cool` = 0, the droplet disappears completely.
- Label it **"reconstructed from measured values"**, not real footage.
- Pair it with a slider for pressure to show reignitions happening above ~2 atm.

**V11: Data quality panel (examples to show)**
- CFI-G inverse: 1,015 lines, 154 real tests
- CFI CSV: 8 repeated rows. Workbook has 227 tests.
- CFI-G: 26 tests labelled "30% propane/butane" actually burned 2.7–4.7% fuel (`Xf`). One test says "no ignition" but "FT".
- SAME-R: 109 rows = 67 tests (several rows per test).
- Saffire-II CSV: 15 lines = 9 tests + 6 note rows.
- FLEX: 1 row with pressure = 0
- BASS-II: fan display is not cm/s. CO "OR" = over range.
- SAME-R: `Rt/R0` is a setting, not a temperature

---

## 2. Later (needs more data or extraction)

| # | Visual | What it needs | Effort |
|---|---|---|---|
| L1 | **Real test video next to the animation** | Pick 5 to 10 of the **855 `.mp4` videos** listed in `inventory.csv` (BASS-II 296, s-Flame/ACME 290, CFI 126, BASS 114, SPICE 18, SAME-R 8, SAME 2, CFI-G 1; median 38 MB). Download with `scripts/psi_download.py --get <acc> "<file>"`. | Small |
| L2 | **Real droplet-history curves** (d² vs time) for CFI tests | The **31 CFI per-test summary PDFs** (`PSI-39_Analyzed Data_FLEX-xxxx_Summary.pdf`, ~0.3 MB each). Replaces the reconstruction in V9 with real curves. | Small download + extraction |
| L3 | **Smoke size vs airflow / temperature chart** (maybe a detection predictor) | The **~144 SAME / SAME-R per-test spreadsheets** in "Analyzed Data". | Small download, then check contents |
| L4 | **Solid-material outcome map** (burned / quenched / blew off on O₂ vs flow, one panel per flow direction) | Outcomes extracted from BASS-II report Appendix A + BASS as-run workbook (predictor P9, **decided: do it in stages**) | Medium (text extraction + review) |
| L5 | **Fabric limits chart** | BASS-II report Table 7.1 (viewer p. 103) typed into a CSV (predictor P11) | Small, ✅ doable now |
| L6 | **Sensor time-series** (temperature, radiometer during one burn) | One or two raw ACME log files from the ~15,800 raw files | Medium |
| L7 | **Report figures embedded in cards** | Crop figures from the reports (e.g. BASS-II Fig. 6.10, CFI Figs. 4 and 5) with the page cited | Small |
| L8 | **Publication network** | The 352 publications in the `investigation.json` files, linked by shared authors / investigations | Medium |
| L9 | **Partial-gravity data** | Future LUCI and FM2 experiments (not in PSI yet) | Not possible now |

Verified 14 Nov: 32 CFI summary PDFs and 144 SAME / SAME-R spreadsheets exist; all "Analyzed Data" together is ~1 GB.

All of L1 to L3 are **"Analyzed Data" or video files** listed in `Data/psi/inventory.csv` but not downloaded. `scripts/psi_download.py --analyzed` (added, not run yet) downloads only the analyzed files into `<acc>/analyzed/`. Run `--analyzed --dry-run` first to see the list.

---

## 3. Suggested order for the demo

1. **V1 coverage map** with the gravity toggle (main screen)
2. **V9 shrinking droplet** (opening hook), plus **L1** a real CFI video if downloaded
3. **V7 microgravity vs Earth** + **V13 PMMA boundary** (strongest science)
4. **V2 evidence grid** (shows the gaps)
5. **V12 cards** and **V11 data quality** around everything

## 4. Rules for every visual

- Every point, bar or number links to its **source row or document page**.
- Show units after conversion (kPa, %, cm/s), with the original value on hover.
- No red/green "safe / unsafe" colours. Use "tested here / between tests / never tested".
- Moon and Mars views always show the **"microgravity evidence only"** label.
- Animations and reconstructions are labelled as such, never as real footage.
- **Every visual has 3 explanation levels** (Explorer / Student / Researcher) and is translatable. Numbers never change between levels or languages. See `IDEAS.md`.
- Colour-blind-safe palette, a text alternative for every chart (screen readers), and full keyboard navigation.
