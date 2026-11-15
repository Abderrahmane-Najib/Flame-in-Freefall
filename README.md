# Etna

**Fire safety for the Moon, Mars and the ISS, built on what NASA actually measured in microgravity.**
NASA Space Apps Challenge 2026 · *Flame in Freefall*

**▶ Live app: https://etna.web.app**

NASA's Physical Sciences Informatics (PSI) system holds 24 combustion investigations: 2,128 test rows and 67 reports (2,331 pages), spread over spreadsheets and PDFs. Etna turns them into one place where a student, an engineer or a researcher can ask *"what do we really know about fire in this habitat's air?"* and get an answer that points back to the exact test row or report page.

Every answer says how far it can be trusted. Where NASA never tested something (for example Moon or Mars gravity), Etna says so instead of guessing.

---

## What you can do

### Find and compare the evidence

| Page | What it does |
|---|---|
| **Home** | *"Where will your crew live?"* Pick the ISS, a Moon base, a pressurized rover or a Mars habitat. The investigations are ranked by how many tests were **measured** in that habitat's air (O₂ and pressure), with badges for *in this air*, *just outside it* (near-lunar) and *no tests in this air*; hovering a card highlights its tests on a mini coverage map. Below: collection figures, four Earth-facing evidence cards (smoke detectors, extinguishers, materials, ventilation), each linked to its NASA report or test table, and a Flame Lab preview. |
| **Experiments** | Every investigation as a card, filtered by fuel family (solid, droplet, gas, smoke, ground) and by fire-safety job (prevention, detection, suppression). Approved user uploads appear here too, labelled as uploads. |
| **Study details** | Opens over any page: summary, sourced findings (each with its report page), why it matters for fire safety, and **how it was tested**: hardware, fuels and sample sizes, cabin O₂, burner O₂ (kept apart: not cabin air), pressure (kPa and psi), airflow and diluent gas, each marked *varied* or *held fixed* across the tests. **Download the cleaned test rows as CSV**, open the original NASA table, compare with other studies, or chat about this study only. |
| **Compare** | Up to three investigations side by side: fuel family, hardware, tests, tests in Moon-base air, fuels, O₂, pressure, airflow, diluents, safety job, key finding and limitation (with sources). Rows where they differ are highlighted, rows that match are marked *same*. The choice is in the address, so a comparison can be shared (`#/compare?ids=PSI-26,PSI-25`). |
| **Coverage map** | Every test with O₂ and pressure plotted against the ISS and Moon-base / rover air zones, plus a dashed near-lunar band. Hover a dot for its study, fuel, air and source table row; toggle categories; counts of lunar, near-lunar and excluded rows; a by-experiment table. It shows the gap: only 20 tests sit inside proposed Moon-base air. |
| **Knowledge graph** | Experiments, materials, fuel families, habitats, fire-safety jobs and hardware (CIR + ACME, CIR + MDCA, MSG, Cygnus) as a connected map. Filter by habitat (all, ISS, Moon base & rover, Mars, near-lunar) and by node type; select a node to see what it connects to. |
| **Search** (`Ctrl+K` / `⌘K`) | Search every NASA report page in your own words. Full-text and meaning (BGE-M3) search are merged; each result shows the report and page. Optionally include your own unreviewed uploads, labelled as such. |

### Explore what the data predicts

| Page | What it does |
|---|---|
| **Predict** | Will an acrylic (PMMA) rod keep burning? NASA's own flammability boundary from the BASS-II report (Eq. 6.1): pick the rod size, O₂ and airflow and see which side of the curve you are on, with ISS and Moon-base reference levels. |
| **Flame Lab** | A burning fuel droplet in 3D. Choose a habitat or your own air, a fuel (FLEX, CFI), O₂, pressure, droplet size and diluent: the droplet shrinks and goes out the way the 5 nearest NASA tests did, including the near-invisible cool flame, with a size-over-time chart. Trained models give a second opinion with a **trust badge** (*tested here* / *between tests* / *outside tested range*). The Earth and Moon/Mars flame shapes are labelled illustrations, not measurements. |

### Ask, learn and bring your own

| Feature | What it does |
|---|---|
| **Ask Etna** | A chat panel on every page. It searches the reports, reads the study cards and queries the test tables, can draw a chart, and cites every claim. Each study and each upload also has its own chat, limited to its sources. |
| **My reports** | Upload a text PDF (up to 20 MB): it is indexed, gets its own chat, and an AI-drafted study card (summary, findings, limitations) that you review, edit, approve or reject. Only approved cards join the collection, always labelled as uploads. |
| **Mir 1997** | An interactive history lesson on the 1997 Mir fire: NASA photographs, five crew decisions, the documented choice versus clearly labelled *imagined* branches, and a debrief with NASA and ESA sources. |
| **Did you know?** | Short curated facts from NASA findings and NASA Spinoff (for example the fine-water-mist extinguisher), each linked to its source. |
| **Data & method** | Live collection counts and the rules behind every number. |

**Three explanation levels:** **Explorer** (plain language, with a step-by-step *Explain it simply* tour), **Student** (exact numbers) and **Researcher** (full detail). The level also changes the assistant's persona: space guide, teacher or research colleague. Light and dark modes; works on phones.

## The data, and how far to trust it

- **Source:** NASA PSI, 24 combustion investigations (ACME's six experiments including CFI-G and E-FIELD Flames, FLEX, FLEX-2, CFI, BASS, BASS-II, SPICE, SLICE, Saffire-I/II/III, SAME, SAME-R, DAFT and ground studies), downloaded with `scripts/psi_download.py`.
- **Cleaning:** each test table is cleaned into `data/psi/clean/*.csv` with units normalised and every change logged (`data/psi/clean/_report.json`). Every claim in the docs was re-checked against the raw files and PDFs: [`project-docs/VERIFICATION.md`](project-docs/VERIFICATION.md).
- **Habitat air rules:** a test counts for a habitat only when both its chamber O₂ and pressure fall inside the habitat's range (Moon base / rover: O₂ ≥ 30 % at ≤ 70.3 kPa / 10.2 psi). 17 FLEX tests about 1 kPa outside are shown as **near-lunar**, never as lunar. O₂ blown out of a burner is never treated as cabin air. Mars uses the Moon-base air, which is a team assumption.
- **Hand extraction:** the outcome of about 250 solid-fuel tests (BASS / BASS-II) existed only as tables in PDF reports. We transcribed them from page images, with the page reference and a confidence on every row (`data/psi/extracted/`). They are not in the app yet.
- **Limits, stated in the app:** all evidence is from microgravity. Moon and Mars gravity were never tested; partial gravity is shown as a gap, not predicted.

More: [`project-docs/DATA_EXPLAINED.md`](project-docs/DATA_EXPLAINED.md).

## The predictors

Small, readable models (logistic / ridge regression), each scored on **whole test days it never saw**. Gradient boosting was tried on the same folds as a challenger and never clearly won, so we kept the simpler models.

| ID | Question | Held-out result (baseline) | Where |
|---|---|---|---|
| P1b | Does a fuel droplet's flame go out early? (FLEX) | 81% accuracy (68%), AUC 0.85 | Flame Lab |
| P6b | Droplet size when the hot flame goes out, relative to its start (CFI) | R² 0.44 (5 nearest tests: 0.06) | Flame Lab |
| P7 | How does the cool flame end? (CFI) | 79% (59%), AUC 0.87 | Flame Lab |
| P8 | Does it reignite? (CFI) | 79% (76%), AUC 0.89 | Flame Lab |
| P10 | PMMA flammability boundary (BASS-II) | NASA's own equation (Eq. 6.1), nothing to train | Predict page, Home |
| P1 | How does a droplet fire end? (3 outcomes) | 74% (68%), AUC 0.77 | API only |
| P2 | Droplet burn time (FLEX) | MAE 3.4 s (6.0 s) | API only |
| P3 | Will a gas flame ignite? (CFI-G) | 79% (75%), AUC 0.75 | API only |
| P4 | Will it go out by itself? (CFI-G) | AUC 0.83 | API only |
| P5 | Hot-flame burn time (CFI) | MAE 1.0 s (3.2 s) | API only |
| P6 | Droplet size when the flame goes out (CFI) | MAE 0.14 mm (0.64 mm), R² 0.92 | API only |

"API only" models are served at `/predict/models/{id}` (see `/docs` on the API), each answer with its trust badge, the 7 nearest real tests and the sources, but no page shows them yet. Flame Lab's main answer comes from the 5 nearest NASA tests, which score about as well as the trained models on held-out days ([`models/NEAREST_VS_MODELS.md`](models/NEAREST_VS_MODELS.md)); the models are shown next to it as a second opinion.

Solid materials (P9) have **no model on purpose**: 137 usable tests over 15 material groups is too thin.

Full method and confusion matrices: [`project-docs/PREDICTORS_TRAINING_AND_EXTRACTION.md`](project-docs/PREDICTORS_TRAINING_AND_EXTRACTION.md), [`models/REPORT.md`](models/REPORT.md).

## Data for your own models

Every investigation's cleaned, unit-normalised test rows download as CSV, from its details panel, the Compare page, or the API:

```
GET /tests.csv?psi_id=PSI-25        # one investigation
GET /tests.csv?fuel_type=droplet    # a fuel family: solid, droplet, gas, smoke, ground
GET /tests.csv?lunar_air=true       # the 20 tests in Moon-base air
```

Each row keeps every cleaned column (including the table-specific result columns), its NASA table, row number and a `source_url` to the original PSI file. The same rows are in `data/psi/clean/`.

## API

FastAPI, documented at `/docs`.

| Endpoint | What it returns |
|---|---|
| `GET /investigations`, `/investigations/{id}` | Study cards (short list, filterable by `fuel_type` and `safety_job`; one full card) |
| `GET /investigations/findings` | Every sourced finding on the NASA cards |
| `GET /habitats`, `/habitats/{id}/ranking` | Habitat air ranges and the ranking of investigations by tests in that air |
| `GET /tests`, `/tests.csv` | Test rows filtered by investigation, fuel, O₂, pressure, flow, lunar air, results (JSON or CSV) |
| `GET /coverage`, `/graph` | Coverage-map points and knowledge-graph nodes and links |
| `GET /predict/pmma`, `/predict/droplet`, `/predict/models`, `POST /predict/models/{id}` | PMMA boundary, Flame Lab droplet answer, trained predictors |
| `GET /search` | Report passages (full text + meaning) with document and page |
| `POST /chat`, `/investigations/{id}/chat`, `/uploads/{id}/chat` | The assistant (streamed NDJSON events) |
| `/uploads…` | Upload a PDF, read its pages, draft, approve or reject its card |
| `GET /health` | Database counts |

## How it is built

```
NASA PSI ──► scripts/ (download, clean, extract, train) ──► data/psi/, models/
                                                              │
                                          app/scripts/push_data.py
                                                              ▼
web/ (React + Vite) ◄──► app/ (FastAPI) ◄──► Neon PostgreSQL + pgvector
                             │                 (tests, cards, report pages, embeddings)
                             ├── BGE-M3 embeddings (local, for report search)
                             ├── gpt-oss-120b on Groq via Agno (assistant with data + search tools, draft cards)
                             └── scripts/predict.py + models/*.json (predictors, standard library only)
```

| Folder | What is in it |
|---|---|
| `web/` | The React app (Vite, Three.js for Flame Lab, d3-force for the graph, Mermaid for assistant diagrams) |
| `app/` | FastAPI backend: routes, assistant, search, uploads, predictors, CSV export |
| `scripts/` | Data pipeline and model training (standard-library Python, except training) |
| `data/psi/` | Cleaned test tables, investigation cards, hand-extracted solid-fuel outcomes |
| `models/` | Trained predictors as JSON, plus the evaluation report |
| `content/` | Curated card content, habitat atmospheres, units |
| `project-docs/` | Data notes, verification log, predictor specs, deploy guide |

One container serves both the UI and the API on **Google Cloud Run**, with **Firebase Hosting** at etna.web.app in front ([`project-docs/DEPLOY.md`](project-docs/DEPLOY.md)).

## Use of AI

- **In the app:** the assistant, the per-study and per-upload chats, and the draft cards of uploaded reports are written by an LLM (gpt-oss-120b on Groq, via Agno). It answers only from tool results (report passages, study cards, test rows) and cites them. Draft cards are published only after a person approves them. Report search uses BGE-M3 embeddings.
- **Numbers come from the data, never from the AI:** counts, ranges, rankings, the coverage map, the PMMA boundary and the predictors are computed from the NASA tables and reports.
- **In development:** AI coding assistants helped write code and documentation; every data claim was checked against the NASA files ([`project-docs/VERIFICATION.md`](project-docs/VERIFICATION.md)).

## Run it locally

Needs Python 3.10+, Node 18+, a PostgreSQL database with pgvector and a free Groq API key.

```bash
# backend
pip install torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r app/requirements.txt
cp app/.env.example app/.env          # fill in DATABASE_URL and GROQ_API_KEY
python app/scripts/push_data.py --no-reports   # load cards, habitats and tests into the database
cd app && python -m uvicorn main:app --reload

# frontend (second terminal)
cd web && npm install && npm run dev  # http://localhost:5173
```

Report search also needs the NASA PDFs (`python scripts/psi_download.py`, then `push_data.py --embed`). To rebuild the data or retrain the models from scratch: [`project-docs/PREDICTORS_TRAINING_AND_EXTRACTION.md`](project-docs/PREDICTORS_TRAINING_AND_EXTRACTION.md).

## Team

- **Wiame Adnane** (team owner)
- **Abderrahmane Najib**
- **Imad Adnane**
- **Yassine Oudghiri**

## Credits

Data: NASA Physical Sciences Informatics (PSI), [psi.nasa.gov](https://psi.nasa.gov/); NASA Spinoff; NASA History Office, NASA NESC and ESA material for the Mir story (sources linked in the app). Etna is a NASA Space Apps 2026 project and is not affiliated with or endorsed by NASA.
