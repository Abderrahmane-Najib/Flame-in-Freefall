# What the reports and workbooks add (beyond the CSV tables)

We checked all **~120 documents** in `Data/psi/PSI-*/docs/` (PDF, DOCX, PPTX, XLSX; `.doc`/`.ppt` only roughly) for anything that helps the **predictors** or the **app**.
Checked 12 Nov 2026. Page numbers are PDF viewer pages unless marked "doc p.".

---

## 1. Summary

| # | Finding | Source | Helps | Value |
|---|---|---|---|---|
| 1 | **BASS-II report appendix has the full test log with results** (the CSV dropped the "observations" column) | BASS-II Summary Report, Appendix A | Predictor | ⭐⭐⭐ |
| 2 | **A published flammability-boundary equation** for PMMA (acrylic) in microgravity | BASS-II Summary Report §6.1, Eq. 6.1 | Predictor / chart | ⭐⭐⭐ |
| 3 | **Microgravity vs Earth flammability limits** (materials burn at *lower* O₂ in space) | BASS-II Summary Report §4, §6 | App headline | ⭐⭐⭐ |
| 4 | **BASS as-run workbook**: 109 tests with O₂, pressure, flow and a text result | `PSI-26/docs/…As Run_Test Matrix.xlsx` | Predictor | ⭐⭐ |
| 5 | **SIBAL fabric quench / blow-off / no-ignition table** | BASS-II Summary Report, Table 7.1 | Predictor / chart | ⭐⭐ |
| 6 | **Smoke particle sizes by material** + "smoke is bigger at low airflow" | SAME & SAME-R final reports | Detection pillar | ⭐⭐ |
| 7 | SAME-R: use **heater temperature, not `Rt/R0`** | SAME-R Final Report | Data cleaning | ⭐ |
| 8 | **SPICE smoke-point summary** per fuel | SPICE Final Report, Table 1 | Display | ⭐ |
| 9 | **CFI-G cool-flame test table** (11 gas cool flames) | CFI-G Final Report, Table 3 | Display / story | ⭐ |
| 10 | Good plain-language explainer sources for the AI assistant | ISS Researchers Guide, ACME fact sheets, PSI-117 2026 seminar | AI / app | ⭐ |

**Nothing useful for predictors** in: Saffire docs (pre-flight objectives and image lists only), Flame Design and s-Flame reports (per-day flame logs, results only in figures), DAFT, PSI-115 (SAME modelling), SAME software/ops manuals, crew training decks.

---

## 2. Predictor findings

### 2.1 BASS-II: the results exist, in the report appendix ⭐⭐⭐

`PSI-25/tables/PSI-25_Experimental table_BASS-II.csv` (129 rows) has **no result column**. But **Appendix A of the BASS-II Summary Report** (Tables A.1 to A.6, viewer pp. ~111 to 122, one table per scientist) reprints the same test matrix **with the "Test observations and anomalies" column**, e.g.:

> *"Spread at 10 cm/s, did not blowoff"*
> *"flame quenched after prolonged burn at 0.4 pot"*
> *"flame blew out at a fan pot of 7.0"*

Word counts in the appendix: *extinguish* 54, *blowoff/blow-off/blew off* 22, *quench* 6, *did not ignite* 2.

**What this enables (new predictor P9):** for a material + geometry + O₂ + flow: **does it keep burning, quench (too little flow), or blow off (too much flow)?** That is exactly the **prevention** pillar.

**Work needed:** the PDF table text is broken across lines. Extract per test with an LLM (or by hand for ~130 tests) into `test_id, outcome, flow_at_outcome`, and keep the page reference as the source. Join to the CSV on `Test #`.

**Watch out:**
- `Fan display` / `pot` values are **not cm/s**. Convert with `PSI-25/docs/PSI-25_Reference Data_Fan calibration data.xlsx`.
- `CO = OR` means **over range (>1,000 ppm)**, a lower bound (ReadMe).
- Flow was often **changed during a test** (e.g. "10, 5, 3, 2, 1"). The outcome belongs to the *last* flow, not the first.

### 2.2 A real flammability-boundary model, from NASA ⭐⭐⭐

BASS-II Summary Report §6.1 (Olson), viewer p. ~84, fits the microgravity flammability limit of **PMMA rods** as:

```
XO2 (%) = 6 · exp(−0.5 · a) + 0.0167 · a + 13.4
```

where `a` is the **stretch rate** (s⁻¹, roughly flow speed / rod radius).
- Left side (low flow) = **quenching branch**: flame dies from heat loss.
- Right side (high flow) = **blow-off branch**: flame is blown out.
- **Minimum ≈ 13.5% O₂ at a ≈ 8 to 12 s⁻¹** (we checked: the equation's minimum is 13.6% at a = 10.4 s⁻¹ ✅).

**Why it matters:** this is a validated, published predictor. We can draw the **U-shaped "will it burn?" curve** in the app, overlay the real test points, and mark the ISS (21%) and lunar (≥30%) oxygen levels. Every lunar-habitat O₂ level is far **above** this limit. Microgravity gravity only, PMMA rods only.

Also in the same report:
- **Table 2.1** (doc p. 28): extinction flow velocity for thin PMMA at 1 atm. 21% O₂ → **10 ± 5 mm/s**. 16% O₂ → **30 ± 5 mm/s**. Fuel thickness doesn't matter.
- **Table 5.1**: 11 thick-PMMA tests with **spread rate (mm/s)**, burn time, flow, O₂ (Miller). Small, but has real numbers.

### 2.3 Microgravity is *more* dangerous at low airflow ⭐⭐⭐

Two direct comparisons in the BASS-II report. **Strong pitch material:**

| Finding | Source |
|---|---|
| PMMA flame spread seen down to **17.5% O₂ in microgravity**, but **not below 19% on Earth** | §4 (Fernandez-Pello), doc p. 50 |
| Minimum O₂ for PMMA rods: **13.5% in microgravity** vs **15.4% upward limit on Earth** ("the material remains flammable under the weak ventilation only obtainable in microgravity") | §6.1 (Olson), viewer p. ~84 |
| The blow-off line is straight, so it can be extrapolated to zero flow as *"a conservative estimate of the minimum O₂ for material flammability in space"*, a method to correct Earth tests for space | §6.1 |

This directly answers the brief's *"micro- and normal-gravity results could bound what occurs at intermediate gravity levels."* For PMMA we have **both ends**, so the app can show a **bounded range for the Moon** instead of nothing.

### 2.4 BASS (PSI-26) as-run workbook ⭐⭐

`PSI-26/docs/PSI-26_Science Documents_As Run_Test Matrix.xlsx`, sheet `as run matrix`: **109 numbered tests**.
- Has **O₂ % (0.17 to 0.225), pressure (atm), CO₂ (mmHg), air display (cm/s)**, material, size.
- Has a free-text **"Test Observations and Anomalies (ignited, spread, extinguished, burn time, color…)"** column: *extinguish* 27, *spread* 18, *blow* 11, *no ignition / did not ignite / failed* ~8, *soot* 42, *blue* 48.
- Materials: PMMA (spheres, slabs, rods, 1 and 2 cm), SIBAL fabric, Nomex, candles/wax, Ultem.

**Use:** extract outcome + burn time from the text (LLM with the row as source). Combined with BASS-II, that's **~240 solid-fuel tests**, enough for a simple "will it keep burning?" classifier on PMMA. Material names need cleaning (`2 cm sphere`, `PMMA sphere 2 cm`, `pmma sphere` are the same thing).

### 2.5 SIBAL fabric limits (Table 7.1) ⭐⭐

BASS-II report Table 7.1 (viewer p. 104): **31 fabric tests** with width, flow (start → end), O₂ and result: *Quenched* (6), *No ignition* (3+), *Blow-off* (1), *No blowoff* (2). O₂ 16.4 to 21%.
**No ignition at 16.4 to 16.8% O₂**, so this gives an approximate **fabric ignition limit** in microgravity. Small but clean. Good for the chart.

---

## 3. Detection findings (SAME / SAME-R)

There's still no "alarm went off" column, so **no alarm predictor**. But the reports give what a detector-design user needs:

**SAME Final Science Report, Table 1: smoke particle size by material (flight)**

| Material | Mean diameter (nm) | Aged (nm) |
|---|---|---|
| Kapton | 105 | 186 |
| Teflon | 205 | 273 |
| Lamp wick (cotton) | 227 | 308 |
| Silicone | 257 | 422 |

(arithmetic mean diameter. Geometric mean and mass-average are also in the table.)

**Key conclusions (quoted):**
- *"The small diameters for the Kapton and Teflon will make detection of this smoke challenging for light scattering devices"*. The ISS detector is light-scattering.
- *"a strong trend of increased particle size at low flow rates … smoke trapped in an avionics enclosure can be expected to be substantially larger than smoke released in ventilated areas"* (SAME-R report, Figs. 6 to 8).
- *"to trigger an alarm for … small particles such as Teflon and Kapton without excessive nuisance alarms from large dust particles is difficult without some level of particle size discrimination"*.

**App use:** a **"Smoke fingerprint" card per material**, plus the message *one detector type doesn't fit all smoke*. That's a clear detection insight with sources.

**Cleaning note:** the SAME-R report says tests should be described by **sample heating temperature, not `Rt/R0`**: *"for the same Rt/R0, the actual heating temperature difference can be as large as 30 °C."* The SAME-R CSV only has `Rt/R0`. Label it as a setting, not a temperature.

---

## 4. Smaller findings

| Finding | Source | Use |
|---|---|---|
| SPICE: **52 smoke points** across 5 fuels (C₂H₄ 6, C₃H₈ 6, C₃H₆ 20, 75% C₃H₆ 13, 50% C₃H₆ 7), with ranges of nozzle size, coflow speed and smoke-point length. *"Increase in coflow velocity generally increases the smoke point length"* | SPICE Final Report Table 1 (viewer p. ~20). Same table in Dotson thesis Table 3.1. | Display. The 469-row CSV doesn't say which rows are smoke points. |
| CFI-G **gas cool flames**: 11 tests at ~39% O₂, 2 bar, 30% n-butane, with flame duration and hot/cool flame radii (hot flame ≈ 2.5× bigger) | CFI-G Final Report Table 3 (viewer p. 46) | Story: cool flames also appear in **gas** fires at lunar-like O₂, not only droplets |
| ACME daily flame logs (atmosphere O₂ per test day, flames ignited) | Flame Design, s-Flame, CFI-G reports, "Table 1" | Already in CSVs. Good cross-check. |
| ISS Researchers Guide: *Combustion in Reduced Gravity* (56 pp.), ACME fact sheets, *Unlocking Mysteries* | `PSI-23/docs/` | Plain-language text for the AI assistant and the "learn" pages |
| PSI-117: *Cool Flames in Space* seminar, **26 Mar 2026** (latest summary of cool-flame science) | `PSI-117/docs/` | AI assistant, pitch background |

---

## 5. Still missing (not in the local docs)

- **FLEX, FLEX-2 reports**: needed to define "Disruption" and the `Burning rate; mm` unit (search NTRS).
- **BRE, CLD, E-FIELD, SLICE reports**: no local docs, so E-FIELD's "artificial gravity" results aren't available.
- **Saffire results**: the local Saffire documents are pre-flight plans and image indexes. The µg vs 1 g spread numbers are only in the Saffire-II CSV (15 rows).

---

## 6. Updated predictor list

Adds to `predictors/README.md`:

| ID | Target | Source | Status |
|---|---|---|---|
| P1 to P8 | (see `predictors/`) | FLEX, CFI-G, CFI workbook | ✅ / ⚠️ |
| **P9** | Solid material: keeps burning / quenches / blows off / doesn't ignite | BASS-II appendix A + BASS as-run workbook (~240 tests) | ⚠️ needs text extraction |
| **P10** | PMMA flammability boundary (O₂ vs stretch rate) | **NASA's own equation** (BASS-II Eq. 6.1) + test points | ✅ ready (formula, no training) |
| P11 | Fabric (SIBAL) ignition / quench limit | BASS-II Table 7.1 (31 tests) | chart only, too few for a model |
