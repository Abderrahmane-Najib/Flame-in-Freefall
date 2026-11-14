# Handoff: Flame in Freefall (NASA Space Apps 2026)

*Last updated 2026-11-14. Read this first when continuing on another PC.*

**New on 14 Nov:** all docs re-verified against the raw data and PDFs (`VERIFICATION.md`); product ideas and decisions in `IDEAS.md` (P9 go-ahead, near-lunar band, explanation levels, languages). Next step: **UI design**.

**Also new on 14 Nov (backend side):** card content done with a source link on every item (step 1d), habitats + habitat ranking, the challenge resources checked, and the backend started in `app/` with a hosted database (Neon) and report search. See section 8. **Later on 14 Nov:** the AI assistant works (Agno + Groq, 5 tools, personas, chat history) behind `POST /chat`, and embeddings moved to the local BGE-M3 model. See section 8b.

## 1. What we're building
This is an AI-powered web dashboard that summarizes, ranks and interprets the 24 NASA PSI combustion investigations, for fire safety in spacecraft, the ISS, Moon/Mars bases and rovers. Every investigation is tagged with the fire-safety jobs it informs: **prevention**, **detection** and **suppression**.

The build plan, in order:

| Step | What | Status |
|---|---|---|
| 1a | Card facts from `investigation.json` | ✅ done |
| 1b | Clean every test table into `data/psi/clean/*.csv` | ✅ done, verified |
| 1c | Card tests and conditions, built from the cleaned tables | ✅ done, verified |
| 1c+ | `fire_safety: {jobs, psi_label}` on every card | ✅ done, verified |
| 1d | Card content: summary, findings (doc + page), limitations | ✅ done: 24 summaries, 56 findings on 17 cards, every item with a source link (section 8) |
| 2 | Filters (fuel type, safety job, O₂/pressure/flow ranges, lunar air, has results) | ⏳ will be the `query_tests` tool + API |
| 3 | Ranker | ✅ done, **without weights**: investigations ranked by tests *measured* in the habitat's air (section 8) |
| 4 | AI assistant: RAG over the reports, plus a data tool for numbers | 🔧 in progress: database + search done, assistant next (section 9) |
| 5 | Models (predictors P1–P11, see `predictors/README.md`) | ⏳ |

| 6 | **UI design** (explanation levels, languages, accessibility: see `IDEAS.md`) | ⏳ **next** |
| 7 | P9 solid outcomes: extraction in stages (Olson → T'ien → others → BASS) | ⏳ decided, see `predictors/P09_solids_burn_outcome.md` |

Also pending:
- Images: 19 of 24 cards have none.
- `--analyzed` download, which is written but not yet run.
- Slider panel spec.
- Competitor notes. The competitor, "MicroFire Atlas", covers solids only.

## 2. Setup on a new PC
Requirements:
- Python 3.10+.
- The data pipeline (`scripts/`) needs no pip packages; everything uses the standard library. openpyxl is *not* needed, because `scripts/xlsx_read.py` reads `.xlsx` files itself.
- The backend (`app/`) does: first `pip install torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu` (CPU-only torch), then `pip install -r app/requirements.txt`, then copy `app/.env.example` to `app/.env` and fill in `DATABASE_URL` and `GROQ_API_KEY` (ask the team lead; never commit `app/.env`).
- If `uvicorn` is "not recognized" in PowerShell, run it as `python -m uvicorn`.

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
- **Claude doesn't run scripts.** It writes or edits the code and gives the exact commands, and the user runs them and pastes the output. This rule lived in Claude's memory on the old PC. Tell Claude again on the new PC, or point it to this file.
- Keep commands short. Long one-liners break when copied.
- After editing a file that's open in the editor, check that the change is really on disk.
- Cards: `fire_safety` holds only `jobs` + `psi_label`. No basis, stated_in or relevance.
- Documents on a card are just the PSI repository link. No docs list. (Findings and limitations cite their exact document and page; see section 8.)
- **Build in small, clean steps**: only what the current step needs; the backend lives in `app/` (routes / schemas / services / database).
- **Secrets** stay in `app/.env` (git-ignored). Never paste keys or connection strings in chat or commits.

## 7. ⚠ Missing files
`project-docs/README.md` (reading order and corrections) and `Flame_in_Freefall_Project_Guide.md` were **not on disk** on 2026-11-13 and were never committed. Check the old PC's Recycle Bin or editor history. Section 5 above holds the key corrections from the README.

## 8. Done on 14 Nov (backend side)

### Data fixes (`scripts/`)
- **Flame Design:** text cells such as "LOW O2" were read as numbers (O₂ = 2%). They are now empty and flagged; "RAMP" rows are flagged too.
- **BASS:** test numbers 24, 85, 89, 90, 91 appear twice; each copy is now matched to its own workbook row, in order (flagged).
- **Saffire:** the 1-g columns are the Earth comparison (header says "1-g Burn Length"). Saffire-I length/width were swapped in the PSI table (fixed, flagged). Fabric thickness units are wrong in the source ("0.37 cm" = about 0.37 mm; flagged).
- `cards.json` no longer has a timestamp, so a rebuild with unchanged data shows no diff.

### Card content (step 1d), `content/cards_curated.json`
- 24 summaries, **56 findings on 17 cards**, limitations on all 24. Findings are stated **results only**, never goals or plans.
- Sources used: the PSI records, *A Researcher's Guide to Combustion Science* (2015, saved in `project-docs/sources/`), the reports in `data/psi/*/docs/` (BASS-II report, ACME final reports, SAME/SAME-R, SPICE, DAFT, PSI-115, PSI-117 slides, Saffire paper), and our own cleaned tables.
- **Every item carries its source**: `{text, src, where}`. `build_cards.py` turns it into a `cite` line and a `url`: the direct PSI download link of the file plus `#page=N`, or the original table CSV. Sources are defined once in `_sources`.
- 7 cards have no findings because PSI has no results for them: CLD, E-FIELD, PSI-60, PSI-62, FLEX-2, Saffire-III, SLICE.
- E-FIELD: the challenge says it is the only experiment that **mimicked partial gravity**.

### Habitats and ranking
- `content/habitats.json`: ISS, **Moon base & pressurized rover** (one entry), **Mars base (assumed same air as the Moon base)**, plus reference points (spacesuit, Shuttle, Skylab, Apollo).
- Sources, all quoted in the file: the **challenge text** (Moon: ≥30% O₂ at ≤10.2 psi = 70.3 kPa) and **NTRS 20240003211** (ISS 14.7 psia / 21%; lunar habitat recommendation 8.2 psia / 34%). Team choices are labelled as assumptions (ISS tolerance box, Mars).
- `build_cards.py` adds `habitat_match` to every card: tests inside each habitat's O₂/pressure box, chamber O₂ only, in 4 groups: **measured** (this group is the ranking), **from_note**, **o2_only** (pressure not recorded), **mixed** (a row lists several O₂ values). A plain count, no weights.
- Result: Moon base = **CFI-G 20 measured**; BRE has 188 flames on test days that included 34–40% O₂ (pressure and per-flame O₂ not recorded).

### Challenge rules and resources (checked on spaceappschallenge.org)
- Deadline **Sun 15 Nov, 23:59 local time**. Demo: **7 slides max or a 30-s video**, in English.
- The submission must **describe how SI (AI) tools were used**. Every external resource (code, data, images) goes in the References field.
- Judged 1–5 on Impact, Creativity, Validity, Relevance (NASA data use), Presentation.
- NASA gives data only. Free partner "Global Offers": Google Cloud (Cloud Run, Firebase, Gemini), Microsoft (Azure, GitHub Copilot), GoDaddy (domain + hosting), Miro.
- Competitors checked on GitHub (about 120 repos). Our edge: page-level citations from the reports, burner O₂ kept apart from cabin O₂ (another team counts 66 "lunar" tests; only 20 are cabin air), Saffire corrections.

### Backend, `app/`
```
app/
  main.py                 creates the app, plugs in the routes
  core/config.py          settings from app/.env (DATABASE_URL, GEMINI_API_KEY)
  database/               connection.py + schema.sql (the tables)
  schemas/                API response models (Pydantic)
  services/               logic: embeddings.py (Gemini), search.py (hybrid search), health.py
  routes/                 endpoints only: GET /health, GET /search
  scripts/push_data.py    pushes our data into the database
  Dockerfile, requirements.txt, .env.example
```
- **Database:** PostgreSQL on **Neon** (free plan, Frankfurt), with **pgvector**. Tables: `investigations` (full card as JSON), `tests` (the 2,128 cleaned rows; table-specific columns in `extra`), `habitats`, `documents` (66 unique report PDFs; 6 duplicates skipped), `pages` (2,327), `chunks` (4,075 pieces of about 250 words, never across a page).
- **Embeddings:** ~~Gemini, 768 dimensions~~ replaced by **BGE-M3** (see 8b).
- **Search** (`GET /search?q=…`): full-text (exact terms) + vector (meaning), merged with Reciprocal Rank Fusion. Every hit has its investigation, file, PDF page, link and `cite` line. Falls back to words only if the question can't be embedded.
- Run it:
```
python app/scripts/push_data.py            # data + reports + chunks
python app/scripts/push_data.py --embed    # + embeddings (local BGE-M3, no key)
cd app
python -m uvicorn main:app --reload        # then open http://localhost:8000/docs
```

### 8b. Assistant and embeddings (later on 14 Nov)

**Embeddings: BGE-M3** (`BAAI/bge-m3`, 1024 dimensions, `services/embeddings.py`), run locally with `sentence-transformers`.
- Why: Gemini's free tier stopped at about 1,000 chunks a day (and the Neon connection dropped during the quota waits).
- No API key and no quota; CPU is enough. The model (~2.3 GB) downloads once per machine into the Hugging Face cache.
- `schema.sql` drops an old 768-size column by itself; `push_data.py --embed` refills it and resumes if stopped.
- Deploy: bake the model into the Docker image; Cloud Run with about 4 GB RAM; `min-instances=1` for the demo (cold start ~20–40 s).

**Assistant** (`services/assistant.py`): Agno 3.2 + **Groq** (`openai/gpt-oss-120b`).
- Why Groq: Gemini chat kept answering 503 "high demand", even with a fallback model. Groq is fast (answers in ~4–9 s).
- ⚠ **Groq free tier = 8,000 tokens per minute.** One answer resends the whole conversation at every tool step, so questions needing 3+ lookups can fail with 413. Fix for the demo: Groq Dev tier (paid), or keep questions narrow.
- Tools, all read-only with fixed arguments (never free SQL):

| Tool | What it returns |
|---|---|
| `list_investigations(fuel_type?)` | id, name, fuel type, safety jobs |
| `get_investigation(psi_id)` | a **short** card: summary, findings, limitations (each with cite + url), test counts (full card is too big for the token limit) |
| `search_reports(query, psi_id?)` | 6 report passages with page, url, cite |
| `rank_for_habitat(habitat)` | habitat air + investigations by **measured** tests (other groups listed apart). Moon: CFI-G 20; BRE 0 measured / 6 O₂-only / 188 mixed |
| `query_tests(filters…)` | **at least one filter**; totals + ranges of all matches, max 10 rows, `more_rows` flag. O₂ filters = chamber O₂ only (`services/tests_query.py`) |

- Answer rules are in `INSTRUCTIONS`: no number that is not in a tool result; cite as a markdown link; a finding holds only for its own conditions (the 2 bar cool-flame result is **not** lunar air); `more_rows` = sample only; no Moon/Mars gravity claims; near-lunar ≠ lunar.
- Personas: `student` / `researcher` / `engineer`, one extra instruction each.
- Chat history: last 3 runs per `session_id`, **in memory** (lost on restart).
- `tool_call_limit=6`; `gpt-oss` writes `【cite](url)】`, cleaned to `[cite](url)` by `clean_citation`.
- Test in the terminal: `python app/scripts/try_assistant.py` (add `--debug` to see every model message).

**`POST /chat`** (`routes/chat.py`, `services/chat.py`): body `{message, session_id?, persona}`. Streams NDJSON, one event per line: `session` (send its id back next time) → `tool` (name, args) → `text` pieces → `error`? → `done`. Swagger shows "can't parse JSON" for this; that is expected.

Checked answers (all matched the data): solid fuels = 5; BASS-II findings with pages; Moon base = CFI-G 20; lunar ethane = 6 tests, O₂ 33.2–38.9 %; lunar tests = 50.67 kPa, O₂ 33.2–39.3 %.

## 9. Planned next

| # | What | Notes |
|---|---|---|
| 1 | Finish the embedding run (BGE-M3) | `python app/scripts/push_data.py --no-reports --embed` until all 4,075 chunks are embedded; check `/health` → `chunks_embedded` |
| 2 | ~~AI assistant~~ | ✅ done (8b), on Groq instead of Gemini |
| 3 | Assistant tools | ✅ 5 done (8b). Still to do: `make_chart` (**Vega-Lite**, data must come from a `query_tests` result), `make_diagram` (**Mermaid**, labelled as an illustration) |
| 4 | ~~Personas~~ | ✅ done (8b) |
| 5 | ~~Rules for every answer~~ | ✅ in `INSTRUCTIONS` (8b). Open: the model still mixes "measured" and "suggests" sometimes; link text is the word "cite" |
| 5b | Groq token limit | Decide: Dev tier (paid) for the demo, or keep the free tier |
| 6 | **Report upload** | A user uploads a PDF → stored in Google Cloud Storage → pages extracted, chunked, embedded → searchable as **unreviewed** → AI drafts findings, kept only if the quote is on the cited page → an admin approves it into the knowledge base |
| 7 | Deploy | API on **Google Cloud Run** (`europe-west3`, next to Neon) from `app/Dockerfile`; set `DATABASE_URL` and `GROQ_API_KEY` as env vars; CPU torch + BGE-M3 baked into the image (8b). Add CORS for the UI |
| 8 | API for the UI | Cards, habitat ranking, tests, chat events (text, chart, diagram). The UI colleague's design decides the rest |
| 9 | Before submitting | **Reset the Neon password** (it was shared in a chat); write the SI-usage description; list all libraries and data in References |
