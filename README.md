# Etna

**Fire safety for the Moon, Mars and the ISS, built on what NASA actually measured in microgravity.**
NASA Space Apps Challenge 2026 · *Flame in Freefall*

**▶ Live app: https://etna.web.app**

NASA's Physical Sciences Informatics (PSI) system holds 24 combustion investigations flown on the ISS: thousands of test rows and dozens of reports, spread over spreadsheets and PDFs. Etna turns them into one place where a student, an engineer or a researcher can ask *"what do we really know about fire in this habitat's air?"* and get an answer that points back to the exact test or report page.

Every answer says how far it can be trusted. Where NASA never tested something (for example Moon or Mars gravity), Etna says so instead of guessing.

---

## What you can do

| Page | What it does |
|---|---|
| **Home** | Pick a habitat (ISS, Moon base, rover, Mars). The 24 investigations are ranked by how many tests were *measured* in that habitat's air (O₂ and pressure), and tagged by the fire-safety job they inform: prevention, detection, suppression. |
| **Experiments** | All investigations as cards: summary, key findings with report page links, limitations. Filter the 2,100+ test rows by fuel, O₂, pressure, flow, lunar air. |
| **Coverage map** | Which O₂ / pressure conditions were tested, and where the gaps are. |
| **Knowledge graph** | Investigations linked to fuels, materials, safety jobs, hardware and the habitats whose air they were tested in. |
| **Predict** | Will an acrylic (PMMA) rod keep burning? NASA's own flammability boundary from the BASS-II tests: pick O₂ and air flow and see which side of the curve you are on. |
| **Flame Lab** | A burning fuel droplet in 3D. Choose a habitat or your own air: the droplet shrinks and goes out the way the 5 nearest NASA droplet tests (FLEX, CFI) did, including the near-invisible cool flame. Trained models give a second opinion with a **trust badge** (*tested here* / *between tests* / *outside tested range*). |
| **Mir 1997** | An interactive story of the 1997 fire aboard the Mir space station: NASA photos, five crew decisions, and what the record says happened. |
| **Assistant** | A chat that answers from the NASA reports (semantic search over every page) and from the test data, and cites what it used. |
| **My reports** | Upload your own report: it is searched, gets its own chat, and an AI draft card that a human approves. |
| **Data & method** | Where every number comes from and how it was checked. |

Three explanation levels (**Explorer** plain language, **Student** exact numbers, **Researcher** full detail) and a light / dark mode.

## The data, and how far to trust it

- **Source:** NASA PSI, 24 combustion investigations (FLEX, CFI, CFI-G, BASS, BASS-II, SAFFIRE, ACME and others), downloaded with `scripts/psi_download.py`.
- **Cleaning:** each test table is cleaned into `data/psi/clean/*.csv` with units normalised and every change logged (`data/psi/clean/_report.json`). Every claim in the docs was re-checked against the raw files and PDFs: [`project-docs/VERIFICATION.md`](project-docs/VERIFICATION.md).
- **Hand extraction:** the outcome of 250 solid-fuel tests (BASS / BASS-II) existed only as tables in PDF reports. We transcribed them from page images, with the page reference and a confidence on every row (`data/psi/extracted/`).
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

"API only" models are served at `/predict/models/{id}` (see `/docs` on the live app), each answer with its trust badge, the 7 nearest real tests and the sources, but no page shows them yet. Flame Lab's main answer comes from the 5 nearest NASA tests, which score about as well as the trained models on held-out days ([`models/NEAREST_VS_MODELS.md`](models/NEAREST_VS_MODELS.md)); the models are shown next to it as a second opinion.

Solid materials (P9) have **no model on purpose**: 137 usable tests over 15 material groups is too thin. The 250 hand-extracted solid-fuel outcomes are in `data/psi/extracted/` but are not in the app yet.

Full method and confusion matrices: [`project-docs/PREDICTORS_TRAINING_AND_EXTRACTION.md`](project-docs/PREDICTORS_TRAINING_AND_EXTRACTION.md), [`models/REPORT.md`](models/REPORT.md).

## How it is built

```
NASA PSI ──► scripts/ (download, clean, extract, train) ──► data/psi/, models/
                                                              │
                                          app/scripts/push_data.py
                                                              ▼
web/ (React + Vite) ◄──► app/ (FastAPI) ◄──► Neon PostgreSQL + pgvector
                             │                 (tests, cards, report pages, embeddings)
                             ├── BGE-M3 embeddings (local, for report search)
                             ├── Groq LLM via Agno (assistant with data + search tools)
                             └── scripts/predict.py + models/*.json (predictors, standard library only)
```

| Folder | What is in it |
|---|---|
| `web/` | The React app (Vite, Three.js for Flame Lab, D3 for the graph) |
| `app/` | FastAPI backend: routes, assistant, search, uploads, predictors |
| `scripts/` | Data pipeline and model training (standard-library Python, except training) |
| `data/psi/` | Cleaned test tables, investigation cards, hand-extracted solid-fuel outcomes |
| `models/` | Trained predictors as JSON, plus the evaluation report |
| `content/` | Curated card content, habitat atmospheres, units |
| `project-docs/` | Data notes, verification log, predictor specs, deploy guide |

One container serves both the UI and the API on **Google Cloud Run** ([`project-docs/DEPLOY.md`](project-docs/DEPLOY.md)).

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

Data: NASA Physical Sciences Informatics (PSI), [psi.nasa.gov](https://psi.nasa.gov/). Etna is a NASA Space Apps 2026 project and is not affiliated with or endorsed by NASA.
