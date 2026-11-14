# Handoff: Flame in Freefall (NASA Space Apps 2026)

*Last updated 2026-11-14 (late evening). Read this first when continuing on another PC.*

**Newest (14 Nov, evening):** the web app **Ghostflame** exists (React + Vite in `web/`, the design of `ghostflame-home.html`), wired to every backend feature; report **upload** (chunk, embed, own chat, card agent, approve) and a **card-only chat** were added to the API. See sections 8c and 8d. Flame Lab research started (8e). Deadline: **Sun 15 Nov, 23:59**.

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
| 2 | Filters (fuel type, safety job, O₂/pressure/flow ranges, lunar air, has results) | ✅ `query_tests` tool, `GET /tests`, filter chips on the Experiments page |
| 3 | Ranker | ✅ done, **without weights**: investigations ranked by tests *measured* in the habitat's air (section 8) |
| 4 | AI assistant: RAG over the reports, plus a data tool for numbers | ✅ done (8b); plus a card-only chat and a per-upload chat (8c) |
| 5 | Models (predictors P1–P11, see `predictors/README.md`) | 🔧 P1–P8 trained (`models/*.json`, scores in `models/REPORT.md`, runtime `scripts/predict.py`, not yet wired to the API). P10 (PMMA boundary) done: `GET /predict/pmma` + Predict page; its test dots are in `data/psi/extracted/p10_olson_points.csv`. P11 chart data ready. See `PREDICTORS_TRAINING_AND_EXTRACTION.md` |
| 6 | **UI** (explanation levels, languages, accessibility: see `IDEAS.md`) | 🔧 Ghostflame web app working (8d); Flame Lab and Compare are placeholders; languages not started |
| 7 | P9 solid outcomes: extraction in stages (Olson → T'ien → others → BASS) | ✅ 250 tests in `data/psi/extracted/` (scripts `extract_p9_*.py`, `build_p9_dataset.py`, `build_p10_points.py`). No model: chart + nearest tests. ⏳ human check of stage 3–4 labels |

Also pending:
- Images: 19 of 24 cards have none.
- `--analyzed` download, which is written but not yet run.
- Slider panel spec.
- Competitor notes. The competitor, "MicroFire Atlas", covers solids only.

## 2. Setup on a new PC
Requirements:
- Python 3.10+.
- The data pipeline (`scripts/`) needs no pip packages; everything uses the standard library. openpyxl is *not* needed, because `scripts/xlsx_read.py` reads `.xlsx` files itself. The predictor runtime `scripts/predict.py` is standard library too.
- **Training the predictors only** (`scripts/train_predictors.py`) needs `pandas` + `scikit-learn` (+ `scipy` for the Tad fit check).
- The backend (`app/`) does: first `pip install torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu` (CPU-only torch), then `pip install -r app/requirements.txt`, then copy `app/.env.example` to `app/.env` and fill in `DATABASE_URL` and `GROQ_API_KEY` (ask the team lead; never commit `app/.env`).
- If `uvicorn` is "not recognized" in PowerShell, run it as `python -m uvicorn`.
- The web app (`web/`) needs **Node 18+** (tested with 22): `cd web; npm install`. Run the API (`cd app; python -m uvicorn main:app --reload`) and, in a second terminal, `cd web; npm run dev` → http://localhost:5173 (Vite forwards the API paths to :8000). `npm run build` writes `web/dist`, which FastAPI then serves at `/`.

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
- Lunar air = 20 tests (CFI-G). **Near-lunar** = 17 more FLEX tests at 71–72 kPa (exactly 71.23–72.37; the API's band is 70.3 < p ≤ 72.5 kPa, so never cut at 72). Never call near-lunar "lunar".
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
  main.py                 creates the app, plugs in the routes, serves ../web/dist at /
  core/config.py          settings from app/.env (DATABASE_URL, GROQ_API_KEY, GROQ_MODEL, CORS_ORIGINS)
  database/               connection.py + schema.sql (the tables)
  schemas/                request/response models (Pydantic)
  services/               logic (assistant, card_writer, uploads, indexing, search, embeddings, coverage,
                          graph, habitats, investigations, pmma, tests_query, chat, health)
  routes/                 endpoints only (list in 8c)
  scripts/push_data.py    pushes our data into the database; try_assistant.py = terminal chat
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

### 8c. API for the UI, uploads and the card chat (evening, 14 Nov)

All endpoints (Swagger at `/docs`):

| Endpoint | What |
|---|---|
| `GET /health` | database counts |
| `GET /investigations?fuel_type&safety_job` | short list (now with `summary`, `origin` = psi / upload) |
| `GET /investigations/{id}` | full card |
| `POST /investigations/{id}/chat` | **card-only chat**: tools locked to that card, its reports and its test rows (`make_card_agent`) |
| `GET /habitats`, `GET /habitats/{id}/ranking` | habitat air + ranking |
| `GET /tests?filters&limit` | test rows (≥ 1 filter) |
| `GET /coverage` | O₂ × pressure points (1,489), habitat boxes, near-lunar band, counts |
| `GET /predict/pmma?rod_diameter_mm&flow_cm_s&o2_pct` | P10 boundary curve + references + verdict |
| `GET /predict/droplet?fuel&o2_pct&pressure_kpa&d0_mm&diluent` | Flame Lab: 5 nearest droplet tests → K, end size, ending; `status` measured / interpolated / outside (no estimate). FLEX (methanol, heptane) and **CFI** (dodecane + 2 iso-dodecane blends, with a **cool-flame phase**: K_cool, end size, end). d² law vs recorded burn time: FLEX 0.95× (0.86–1.01), CFI 0.82× (0.37–1.10, CFI time likely includes ignition) |
| `GET /predict/models`, `POST /predict/models/{id}` | trained predictors P1–P8 (`models/*.json`, teammate's `scripts/train_predictors.py`), run by `scripts/predict.py` via `services/predictors.py`: answer + trust badge (tested_here / between / outside) + 7 nearest tests. Flame Lab shows P1b (FLEX) or P7 + P8 (CFI) as a "second opinion", nitrogen air only. `scripts/compare_nearest.py` → `models/NEAREST_VS_MODELS.md`: on the same held-out days the 5-nearest method ties the models on picking an ending (P1, P7) but loses on P1b (bal. acc. 0.70 vs 0.75) and badly on CFI end size P6b (R² 0.06 vs 0.43). So the lab now takes the CFI hot-flame end size from **P6b** (nitrogen, when trusted; `ext_ratio_source`) and no longer returns vote shares as probabilities. ⚠ Deploy: the image needs `models/` and `scripts/predict.py` (build from the repo root) |
| `GET /graph` | knowledge graph: 71 nodes, 154 edges (investigations, materials, families, jobs, hardware, habitats) |
| `GET /search?q` | hybrid report search |
| `POST /chat` | main assistant (NDJSON) |
| `/uploads…` | see below |

**Report upload** (`routes/uploads.py`, `services/uploads.py`, `services/card_writer.py`):
1. `POST /uploads` (PDF ≤ 20 MB, ≤ 300 pages, text PDFs only): pages + chunks stored at once (same chunker as NASA reports, now in `services/indexing.py`), status `processing`; BGE-M3 embedding runs in the background → `unreviewed`. Same file twice = the existing upload.
2. `POST /uploads/{id}/chat`: a chat that searches **only that report** (`make_report_agent`); citations point to `/uploads/{id}/pages/{n}` (page text).
3. `POST /uploads/{id}/card`: a **separate card agent** (not the chatbot) drafts a card in the NASA cards' shape. It reads only ~3,000 words of passages found by 5 fixed questions (Groq token limit); every point must name its page, points citing a page it was not shown are **dropped**, cite/url are built by code, never by the model.
4. `POST /uploads/{id}/approve` (optionally with the user-edited card) → investigation `UP-{id}`: appears in `/investigations`, the graph and the main search. `POST /uploads/{id}/reject` removes it from everything.
- ⚠ **Run once** `python app/scripts/push_data.py --no-reports` so the database gets the new `documents.card` column.
- ⚠ **Not tested end to end yet** against Neon + Groq. Risk: Groq JSON mode may not fill the card schema cleanly.

### 8d. Web app "Ghostflame" (`web/`, React 18 + Vite 5)

The design is `ghostflame-home.html` (the team's mock): its CSS is copied **unchanged** into `web/src/styles.css`; additions are appended below it. Photos extracted to `web/public/img/`. Plain hash routing (`#/predict`), no router library. Extra packages: `d3-force`, `d3-zoom`, `d3-selection` (graph only).

| Page | Uses | Notes |
|---|---|---|
| Home | rankings, coverage, tests, health, pmma | hero per habitat (ISS / Moon / rover / Mars), 4 KPIs per explanation level, ranked cards, mini coverage map (hover a card → its tests glow) |
| Experiments | `/investigations` | filter chips: fuel family, safety job |
| Coverage map | `/coverage` | log-pressure scatter, hover = NASA table + row, click → card; table by experiment |
| Knowledge graph | `/graph` | habitat chips redraw the graph with only that air's experiments; "Show" chips hide node types |
| Predict | `/predict/pmma` | rod / flow / O₂ sliders, ISS and Moon presets, live verdict |
| Search | `/search` | words vs meaning tags, source page links |
| My reports | `/uploads/*` | upload, progress, report chat, card draft (editable), approve / reject |
| Data & method | `/health` | counts + the rules behind every number |
| Flame Lab | `/predict/droplet` | three.js droplet (`components/FlameScene.jsx`): shrinks by d² = d0² − K·t with FLEX/CFI K, ends as extinction / disruption (burst) / completion, or (CFI) hot flame → brightened cool flame + vapour cloud; 1 g teardrop measured on the Researcher's Guide Fig. 1 heptane photo (3.5× taller than wide) + Saufi et al. (methanol 1 g flame ≲ 2 droplet diameters); habitat presets from `/habitats`; Moon/Mars = µg and 1 g shapes side by side; ghost wireframe outside the tested range. Flame size and the 1 g shape are illustrations (labelled) |
| Compare | — | "coming soon" placeholder |

Everywhere: card drawer (findings with links, "Why it matters for fire safety", **"Ask AI about this card"** inline chat), floating "Ask Ghostflame" chat (streams `/chat`).

Design rules applied:
- **Explanation level** (Explorer / Student / Researcher) changes KPI texts and the chat style (UI → API persona: explorer→student, student→researcher, researcher→researcher).
- **Avatars** per level (guide in a helmet / teacher with cap and glasses / scientist with lab glasses), `components/Avatar.jsx`, purely visual.
- **"Explain it simply"** button next to page titles (Explorer + Student only): a step-by-step tour that highlights parts of the chart (Predict, Coverage) or switches the graph view. Texts written by us, no new facts.
- **Chart colours:** the mock's purple/blue accents failed the colour-blind check, so charts use the validated fuel palette (gas `#2a78d6`, droplet `#eb6834`, solid `#1baf7a`; dark `#3987e5`, `#d95926`, `#199e70`) **plus shapes**. Coverage map and graph use a "space" night-sky theme in both modes.
- **Sources shown to users are NASA's only** (e.g. "NASA PSI test tables"), never our own pipeline ("cleaned tables").
- The 4 equipment cards on Home were **re-checked** and fixed: SAME Table 1 PDF p. 27 (Kapton 105 nm, Teflon 205 nm "challenging for light scattering"); FLEX near-lunar 0 of 17 self-extinguished (15 disruption, 2 completion); the old claim "CO₂ or helium is what stopped them" was **wrong** (58 of 185 extinctions had N₂ only) and was removed; BASS-II p. 84; ventilation ≈ 10 cm/s (Researcher's Guide p. 31).

### 8e. Flame Lab: research started (not built)

Goal (from the mock): real NASA test videos next to reconstructions built from their measurements, including the cool flame.
- **Videos exist:** 855 `.mp4` in PSI, none restricted: BASS-II (PSI-25) 296, s-Flame (PSI-23) 290, CFI (PSI-39) 126, BASS (PSI-26) 114, SPICE 18, SAME-R 8, SAME 2, CFI-G 1. Median 38 MB; BASS-II clips are small (3–8 MB).
- **BASS-II clips match test rows:** file `BASS_GMT50_SAMPLE_147_TEST_B1.mp4` = `bass2.csv` row with `sample=147`, `test_id=B1` (O₂ 22.2 %, flow 5 cm/s, PMMA film). So a clip can be shown with its measured conditions.
- **Streaming:** the PSI download URL answers **302 → a signed S3 URL** (expires, `attachment`). To play in a `<video>`: an API endpoint that redirects to a fresh signed URL, or copy a few chosen clips to our own storage.
- **Reference repos** (none models microgravity; we must remove buoyancy ourselves so the flame is a sphere): [`@wolffo/three-fire`](https://unpkg.com/@wolffo/three-fire@1.3.0/README.md) (ray-marched volumetric fire for three.js), [ThreeVolumetricFire](https://github.com/Housz/ThreeVolumetricFire), [SmokeGL](https://github.com/SqrtPapere/SmokeGL) (candle, particles), [WebGL-Fluid-Simulation](https://github.com/PavelDoGreat/WebGL-Fluid-Simulation), [Trinity](https://awesome.ecosyste.ms/projects/github.com%2Fportsmouth%2FTrinity) (GPU fluid with programmable forces). Droplet burning: the d² law (diameter² falls linearly in time) is a simple, honest model for a droplet reconstruction.

## 9. Planned next

| # | What | Notes |
|---|---|---|
| 1 | Finish the embedding run (BGE-M3) | `python app/scripts/push_data.py --no-reports --embed` until all 4,075 chunks are embedded; check `/health` → `chunks_embedded` |
| 2 | ~~AI assistant~~ | ✅ done (8b), on Groq instead of Gemini |
| 3 | Assistant tools | ✅ 5 done (8b). Still to do: `make_chart` (**Vega-Lite**, data must come from a `query_tests` result), `make_diagram` (**Mermaid**, labelled as an illustration) |
| 4 | ~~Personas~~ | ✅ done (8b) |
| 5 | ~~Rules for every answer~~ | ✅ in `INSTRUCTIONS` (8b). Open: the model still mixes "measured" and "suggests" sometimes; link text is the word "cite" |
| 5b | Groq token limit | Decide: Dev tier (paid) for the demo, or keep the free tier |
| 6 | ~~Report upload~~ | ✅ built (8c), the PDF itself is not stored (only its text). **Test it end to end** (upload → chat → `/card` → approve) |
| 7 | Deploy | API on **Google Cloud Run** (`europe-west3`, next to Neon) from `app/Dockerfile`; set `DATABASE_URL` and `GROQ_API_KEY`; CPU torch + BGE-M3 baked in (8b). The Dockerfile must also **build `web/`** (`npm ci && npm run build`) and copy `web/dist` next to `app/` |
| 8 | ~~API for the UI~~ | ✅ (8c, 8d) |
| 8b | **Flame Lab** | next: pick clips (BASS-II matched to rows), a video endpoint, and a microgravity flame reconstruction (8e) |
| 8c | Compare page, languages | placeholders now |
| 8d | Optional | backend answer styles matching the 3 avatars (explorer / teacher / researcher) — started, then cancelled by the user; not done |
| 9 | Before submitting | **Reset the Neon password** (it was shared in a chat); write the SI-usage description; list all libraries and data in References (add React, Vite, d3-force/zoom/selection, Geist font) |
