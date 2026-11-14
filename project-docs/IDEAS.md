# Ideas and decisions

Product ideas and team decisions, agreed on 14 Nov 2026. For the data behind them see `VERIFICATION.md`, `predictors/` and `VISUALISATIONS.md`.

---

## 1. Features: baseline vs what sets us apart

### Baseline (what every team will have; maps to the brief's three bullets)
1. **Investigation cards**: objective, fuel (with sample shape and size), O₂ / pressure / flow ranges, varied vs fixed variables, sensors, hardware, DOI, publications. The brief lists exactly these.
2. **Filter and search**: fuel family, safety job (prevention / detection / suppression), hardware, O₂ / pressure / flow ranges.
3. **Habitat relevance ranking**: pick ISS / lunar base / pressurized rover / Mars, and investigations are ranked by how close their test air is, with a "why it ranked here" line.
4. **AI assistant (RAG)** over the selected reports, with citations (document + page).
5. **Compare view**: 2 to 3 investigations side by side.
6. **Data export**: the cleaned, unit-normalised CSVs (the brief's "extract data for predictive modeling").

### What sets us apart
1. **O₂ vs pressure coverage map** with habitat zones and a **near-lunar band** (see §2). It shows how thin the lunar evidence is.
2. **Predictors with nearest real tests + trust badge** (P1–P4, P10): every answer can be checked.
3. **Moon/Mars bounded range** (PMMA: 13.5% µg ↔ 15.4% 1 g) instead of an invented number.
4. **Data recovered from reports and workbooks**: CFI's 227 tests, and P9's ~250 solid outcomes. CSV-only teams won't have these.
5. **Cool-flame "invisible fire" story**: droplet animation + real CFI video.
6. **Smoke fingerprint**: one detector doesn't fit all smoke.
7. **Data quality and provenance panel**: every number links to its source row or page.
8. **Explanation levels** and **multiple languages** (§3, §4).
9. **Earth spin-off panel** (optional, cheap): the brief invites it and the Resources tab gives the content.

---

## 2. Near-lunar band (new finding)

- **Lunar-like air** (strict, from the brief): O₂ ≥ 30% and ≤ 70.3 kPa (10.2 psi) → **20 tests**, all CFI-G gas flames.
- **Near-lunar** (new): **17 FLEX droplet tests** at ≥ 30% O₂ and **71 to 72 kPa** (exactly 71.23–72.37 kPa, ~10.3 psi), only ~1 kPa outside.
- **None of the 17 went out by itself** (15 broke apart, 2 burned all the fuel; no CO₂ or He added).
- Effect: lunar evidence goes from 20 tests in 1 fuel family to **37 tests in 2 fuel families**.
- **Rule:** always label them "near-lunar", never "lunar". Show them as a lighter band around the lunar box on the map, and as a separate filter option.
- Pitch line: *"In near-lunar air, every untreated droplet fire burned to the end or broke apart; none went out by itself."*

---

## 3. Explanation levels

Same data, three ways of explaining it. The user picks a level once (it can be changed anytime).

| Level | For | Example: P4 in lunar air |
|---|---|---|
| 🌱 **Explorer** | public, school students | "In Moon-base air, most small gas fires went out by themselves, but not all." |
| 🎓 **Student** | undergraduates | "13 of the lit flames at ≥ 30% O₂ and ≤ 70 kPa self-extinguished. More oxygen makes fires harder to stop." |
| 🔬 **Researcher** | engineers, grad students, professors | "P(SE) with nearest 7 tests (CFI-G), XO₂ 0.30–0.40, logistic model, grouped-CV accuracy vs 77% baseline. µg only." |

**Rules**
- **Numbers come from the data, never from the AI.** The AI only writes the words around fixed facts. Explorer and Researcher must never disagree.
- The level also changes:
  - charts (simple ↔ full axes, units, uncertainty)
  - units (the SI / Aerospace US / Lab presets already exist in `scripts/units.py`)
  - glossary pop-ups (on for Explorer, off for Researcher)
  - how many caveats are shown up front (Researcher: all; Explorer: the key one, e.g. "tested in space station gravity only")
- The gravity / "microgravity only" caveat is shown at **every** level.

---

## 4. Languages

- **AI answers:** the model answers in the user's language.
- **Interface text:** i18n translation files (one file per language).
- **Demo scope:** 3 to 4 languages, **including one right-to-left language (e.g. Arabic)** to prove the layout works for every script. Better than many half-finished languages.
- **Never translated:** numbers, units, chemical names (CO₂, PMMA), investigation names (FLEX, BASS-II), document titles. Citations stay in the original English.
- **Fixed glossary** (~30 terms: quench, blow-off, cool flame, extinction, microgravity…), translated once, so every page uses the same words.

---

## 5. Accessibility

- Colour-blind-safe chart palette; never rely on colour alone (also shape / label).
- Text alternative for every chart (screen readers).
- Full keyboard navigation.
- Readable font sizes and contrast in light and dark mode.

---

## 6. P9 decision

**Do it, in stages** (details in `predictors/P09_solids_burn_outcome.md`):
Olson (→ P10 dots) → T'ien (→ P11 fabric) → other BASS-II scientists → BASS as-run workbook → model only if the classes are balanced. Each stage is usable on its own.

**Why:** the brief names solids (fabrics, plastics, BASS, Saffire) as the focus of flammability work, the competitor covers solids, and it turns the P10 curve from a formula into a curve with real test dots.

---

## 7. Next step

**UI design.** Inputs for it: this file, `VISUALISATIONS.md` (V1–V13, demo order in §3) and `predictors/README.md` ("Showing a prediction").
