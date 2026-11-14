# Handoff: Flame in Freefall (NASA Space Apps 2026)

*Last updated 2026-11-14. Read this first when continuing on another PC.*

**New on 14 Nov:** all docs re-verified against the raw data and PDFs (`VERIFICATION.md`); product ideas and decisions in `IDEAS.md` (P9 go-ahead, near-lunar band, explanation levels, languages). Next step: **UI design**.

## 1. What we're building
This is an AI-powered web dashboard that summarizes, ranks and interprets the 24 NASA PSI combustion investigations, for fire safety in spacecraft, the ISS, Moon/Mars bases and rovers. Every investigation is tagged with the fire-safety jobs it informs: **prevention**, **detection** and **suppression**.

The build plan, in order:

| Step | What | Status |
|---|---|---|
| 1a | Card facts from `investigation.json` | ✅ done |
| 1b | Clean every test table into `data/psi/clean/*.csv` | ✅ done, verified |
| 1c | Card tests and conditions, built from the cleaned tables | ✅ done, verified |
| 1c+ | `fire_safety: {jobs, psi_label}` on every card | ✅ done, verified |
| 1d | Card content: summary, findings (doc + page), limitations | ⏳ **next**, empty for all 24 |
| 2 | Filters (fuel type, safety job, O₂/pressure/flow ranges, lunar air, has results) | ⏳ |
| 3 | Ranker with user weights | ⏳ |
| 4 | AI assistant: RAG over the reports, plus a data tool for numbers | ⏳ |
| 5 | Models (predictors P1–P11, see `predictors/README.md`) | ✅ P1–P8 trained (`models/*.json`, scores in `models/REPORT.md`). ⏳ P9 extraction, P10 curve, P11 chart |

| 6 | **UI design**: structure + API contract done in `UI_BRIEF.md`; visual direction is next | ⏳ **next** |
| 7 | P9 solid outcomes: extraction in stages (Olson → T'ien → others → BASS) | ✅ 250 tests in `data/psi/extracted/` (scripts `extract_p9_*.py`, `build_p9_dataset.py`, `build_p10_points.py`). No model: chart + nearest tests. ⏳ human check of stage 3–4 labels |

Also pending:
- Images: 19 of 24 cards have none.
- `--analyzed` download, which is written but not yet run.
- Slider panel spec.
- Competitor notes. The competitor, "MicroFire Atlas", covers solids only.

## 2. Setup on a new PC
Requirements:
- Python 3.10+.
- No pip packages for the data pipeline and the app runtime (`scripts/predict.py`); they use the standard library. openpyxl is *not* needed, because `scripts/xlsx_read.py` reads `.xlsx` files itself.
- **Training only** (`scripts/train_predictors.py`) needs `pandas` + `scikit-learn` (+ `scipy` for the one-off Tad fit check).

```
git clone <repo-url>
cd Flame-in-Freefall
python scripts/psi_download.py          # re-downloads docs/ (git-ignored). Use --dry-run first to see sizes
python scripts/clean_tables.py          # rebuilds data/psi/clean/*.csv + _report.json
python scripts/build_cards.py           # rebuilds data/psi/cards.json
```

**Only the outputs are in git:** `data/psi/clean/` and `data/psi/cards.json`. So the app's data works straight after cloning.

The raw NASA data is git-ignored: the `PSI-*/` folders with `investigation.json`, `tables/` and `docs/`, plus `investigations.csv` and `inventory.csv`. Download it with `psi_download.py` before you re-run `clean_tables.py` or `build_cards.py`. The cleaner needs:
- `tables/`
- 2 workbooks from `docs/`: `PSI-39/docs/…CFI_DataSummary_Spreadsheet_Jan2021.xlsx` and `PSI-26/docs/…As Run_Test Matrix.xlsx`

so don't use `--no-docs`.

After rebuilding, `git status` should show no changes in `clean/` or `cards.json`. If it does show changes, the NASA data has changed since the last download.

Run the scripts **without** `python -I`. With that flag, `psi_download` can't be imported.

## 3. Pipeline and files

```
NASA PSI API ──psi_download.py──► data/psi/<PSI-id>/investigation.json, tables/*.csv, docs/*
                                   data/psi/investigations.csv, inventory.csv
tables + docs ──clean_tables.py──► data/psi/clean/<table>.csv + _report.json
investigation.json + clean/ + content/cards_curated.json ──build_cards.py──► data/psi/cards.json
```

| File | Role |
|---|---|
| `scripts/psi_download.py` | Downloader. Flags: `--only`, `--no-docs`, `--max-mb`, `--dry-run`, `--get`, `--analyzed` |
| `scripts/clean_tables.py` | One cleaner per table (the `JOBS` list). Shared standard columns, plus each table's own columns and trace columns |
| `scripts/build_cards.py` | Builds the cards. Prints a summary table plus problems/todo |
| `scripts/units.py` + `content/units.json` | Unit conversion. Values are stored in one standard unit and converted only for display (SI / Aerospace US / Lab presets) |
| `scripts/xlsx_read.py` | Minimal `.xlsx` reader |
| `content/cards_curated.json` | **Hand-edited** card fields: fuel_type, safety_jobs, hardware_group, summary, findings, limitations. Edit here, never in `cards.json` |
| `project-docs/` | `DATA_EXPLAINED.md`, `DOCS_FINDINGS.md`, `VISUALISATIONS.md`, `predictors/`, `IDEAS.md`, `VERIFICATION.md` |

### Standard units in the clean CSVs
| Quantity | Unit |
|---|---|
| Pressure | kPa |
| O₂ / gas fractions | % |
| Flow | cm/s |
| Temperature | K |
| Length | mm |
| Time | s |

### Key column flags
- `row_granularity`: what one row is (test, test_day, planned_range, measurement, …).
- `n_tests`: blank means unknown.
- `o2_location=burner_stream`: CFI-G inverse flames. This is not cabin air.
- `o2_assumed` / `pressure_assumed`: the value came from a NASA document, not the table (SPICE, s-Flame).
- `lunar_air`: O₂ ≥ 30% and pressure ≤ 70.3 kPa.

## 4. Verified numbers (use these to check a rebuild)
Rebuilding on the new PC should give these numbers:

| Table | Result |
|---|---|
| flex | 273 |
| cfig_normal | 179 (20 lunar) |
| cfig_inverse | 154 |
| cfi | 227 (146 with results) |
| flame_design | 207 / 120 |
| bre / cld / efield / sflame | 194 / 344 / 219 / 276 |
| bass2 / bass | 129 / 121 (0 unjoined) |
| saffire 1 / 2 / 3 | 2 / 9 / 2 |
| same_r | 67 tests (109 rows) |
| same | 4 tests (8 rows) |
| spice | 150 tests (469 rows, 34 duplicates flagged) |
| slice / flex2 | 0 / 0 (no per-test data: dates / planned ranges only) |

Totals: about 2,679 fires, about 596 tests with results, and 20 lunar-air tests (all CFI-G).

Example cards:
- PSI-159: 333 tests, 20 lunar.
- PSI-69: 273 tests, O₂ 12–34, 70.17–309.29 kPa, fire_safety `{'jobs': ['suppression', 'prevention'], 'psi_label': 'Spacecraft Fire Safety'}`.

## 5. Facts not to get wrong
- **Microgravity only.** There is no Moon/Mars gravity data. A Moon estimate must be a bounded range between the µg and 1 g results.
- CFI workbook: **227** tests, not 87.
- Images: only **5 of 24** investigations have an images entry.
- PMMA boundary (P10): O₂ = 6·exp(−0.5a) + 0.0167a + 13.4, with **a = 1.5·(U/r)·√(r/0.318 cm)** (not just U/r).
- P9 (solids burn outcome) needs outcomes extracted from BASS-II Appendix A plus the BASS as-run workbook first. The BASS-II Test.Matrices.xlsx has **no** outcomes.
- CFI-G fuel fraction = `Xf` column, **not** the "30% propane" label (26 tests differ).
- Lunar air = 20 tests (CFI-G). **Near-lunar** = 17 more FLEX tests at 71–72 kPa. Never call near-lunar "lunar".
- CFI: helium only at 21% O₂. 17% O₂ + He = "never tested".
- How we differ from MicroFire Atlas:
  - CFI-G and FLEX data at high O₂ (lunar + near-lunar)
  - all three fuel families
  - a bounded Moon range
  - cool flames
  - explanation levels + multiple languages (`IDEAS.md`)

## 6. Working rules agreed with Claude
- **Claude runs scripts itself** (changed 14 Nov 2026) and asks the user only when blocked or really unsure about a decision. Still no commits unless asked.
- Keep commands short. Long one-liners break when copied.
- After editing a file that's open in the editor, check that the change is really on disk.
- Cards: `fire_safety` holds only `jobs` + `psi_label`. No basis, stated_in or relevance.
- Documents on a card are just the PSI repository link. No docs list.

## 7. ⚠ Missing files
`project-docs/README.md` (reading order and corrections) and `Flame_in_Freefall_Project_Guide.md` were **not on disk** on 2026-11-13 and were never committed. Check the old PC's Recycle Bin or editor history. Section 5 above holds the key corrections from the README.
