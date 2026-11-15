# The Etna data, explained for non-space people

This guide is for the team: developers, not space scientists. It explains why fire in space matters, what NASA tested, what the data looks like and what we can do with it. For the short technical version, see `DATA_NOTES.md`.

---

## 1. Why fire in space is a problem

On Earth, fire behaves the way it does because of **gravity**:
- the flame heats the air, and **hot air is lighter, so it rises**
- the rising air pulls **fresh oxygen** in from below, which feeds the flame
- this gives a flame its **teardrop shape**, and carries **smoke up** to the ceiling detector

In space (on the ISS) everything floats. This is called **microgravity**. So:
- hot air **doesn't rise**
- fresh oxygen only reaches the flame slowly, by drifting (**diffusion**) or if a fan blows it in
- the flame becomes a **dim, blue, round ball**
- smoke **stays near the fire** and may not reach the smoke detector

This makes space fires hard to predict. A flame can look weak and still keep burning. Some materials burn **better** in space when a fan is running. And Earth's fire safety rules don't apply.

**Why NASA cares now:** future Moon bases and rovers plan to use air with **more oxygen at lower pressure** (explained in section 6). More oxygen means things catch fire more easily. Before sending crews, NASA needs to know how fire behaves in that air.

**What the challenge asks us:** take NASA's existing fire experiments, organise them, and help people find what matters for fire safety in each type of habitat.

---

## 2. Where the data comes from

**NASA PSI** (Physical Sciences Informatics, https://psi.nasa.gov/physci/repo) is NASA's public library of physics experiments done in space.
- It holds 133 **investigations**. 24 of them are about **combustion** (fire). Those 24 are our data.
- Access is free with no login. Our script `scripts/psi_download.py` downloads everything into `data/psi/`.

---

## 3. Key words

| Word | Meaning |
|---|---|
| **Investigation** | One research project, e.g. "FLEX". Has an ID like `PSI-69`. Like a **repository**. |
| **Test** (or run) | One fire lit once under fixed conditions. An investigation has many tests. Like a **row** in a table. |
| **Conditions** | The settings chosen before lighting: oxygen, pressure, fuel, airflow. Like the **input**. |
| **Result** (outcome) | What happened: did it light, how long it burned, how it ended. Like the **output / label**. |
| **Microgravity** (µg) | "Almost zero gravity", what astronauts feel on the ISS. |
| **1 g** | Normal Earth gravity. |
| **ISS** | International Space Station, where almost all tests happened. |
| **Ignition** | The fire starting. |
| **Extinction** | The flame going out. |
| **Self-extinguished** | Went out by itself (not enough oxygen or fuel), which is good for safety. |
| **Flammability limit** | The boundary between "will burn" and "won't burn", e.g. "below 17% oxygen this material won't burn". |
| **Diluent** | A non-burning gas added to the air: nitrogen (N₂), carbon dioxide (CO₂), helium (He). It "thins" the oxygen. CO₂ is also what some fire extinguishers use. |
| **Soot** | The black particles in smoke. More soot means more smoke and a yellower flame. |
| **Spread rate** | How fast a flame moves along a material, in mm per second. |
| **Burn time** | How long the flame lasted, in seconds. |
| **Cool flame** | A strange, almost invisible low-temperature flame that can keep burning after the visible flame goes out. A hidden fire risk. |

---

## 4. What each investigation contains

Each investigation has up to 4 kinds of files:

| Part | Like… | Example | Downloaded? |
|---|---|---|---|
| **Record** (JSON) | A README: title, goal, dates, scientists, papers | `data/psi/PSI-69/investigation.json` | ✅ 24 files |
| **Test table** (CSV) | A spreadsheet: one row per test | `data/psi/PSI-69/tables/*.csv` | ✅ 22 tables, ~2,000 rows |
| **Reports** (PDF/Word) | The scientists' write-up of the results | final reports, papers, slides | ✅ 108 files; **31 useful** (`data/psi/docs_selected.csv`) |
| **Raw files** | Videos, camera images, sensor logs | test videos | ❌ ~6.3 TB, too big; we'll pick a few videos |

The full list of every PSI file (not downloaded) is in `data/psi/inventory.csv`.

**Important:** the tables mostly hold **numbers** (conditions, sometimes results). The reports hold **conclusions** (what the scientists learned). We need both:
- the tables for charts and predictions
- the reports for the AI chat and explanations

---

## 5. How a test works

Every space fire test follows the same steps:

1. **Seal** a small, strong box (a combustion chamber) on the ISS.
2. **Fill it** with chosen air: e.g. 30% oxygen + 70% nitrogen, at 70% of normal pressure.
3. **Set a fan** to blow air past the sample, if the hardware has one.
4. **Light** the sample:
   - a strip of **fabric** or a **plastic** rod
   - a tiny **droplet** of liquid fuel
   - a jet of **gas** from a small burner
5. **Record** with cameras and sensors: temperature, gases, smoke.
6. **Note the result:** did it light? How long did it burn? Did it go out by itself or burn everything?

Then repeat, changing one setting at a time. That gives one row per test in the table.

**Hardware groups:** the ISS has a few "fire boxes", and each runs several investigations:

| Hardware | What it burns | Investigations |
|---|---|---|
| **CIR + ACME** (Combustion Integrated Rack + gas burners) | gas flames | CFI-G, BRE, E-FIELD, Flame Design, s-Flame, CLD |
| **CIR + MDCA** (droplet module) | fuel droplets | FLEX, FLEX-2, CFI |
| **MSG** (Microgravity Science Glovebox) + small wind tunnel | solids, gas jets, smoke | BASS, BASS-II, SPICE, SLICE, SAME, SAME-R, DAFT |
| **Cygnus** (empty cargo spaceship, after leaving the ISS) | large fabric sheets | Saffire I–III |

Saffire is special: big fires are too dangerous on the ISS, so NASA burned them inside an empty cargo ship before it burned up in the atmosphere.

---

## 6. Habitats: where crews will live

The same fire behaves differently depending on the **air** and the **gravity**.

| Habitat | Oxygen | Pressure | Gravity |
|---|---|---|---|
| **ISS / spacecraft** | 21% (same as Earth) | 101 kPa (normal Earth pressure) | none (microgravity) |
| **Lunar base / pressurized rover** | **≥ 30%** (more) | **≤ 70 kPa** (lower) | 1/6 of Earth |
| **Mars habitat** | not defined yet; we assume lunar-like | | 0.38 of Earth |

**Why higher oxygen and lower pressure?** Astronauts going out on spacewalks wear suits with very low pressure. Lower habitat pressure makes it quicker and safer to put on a suit. To still breathe enough oxygen at low pressure, the air needs a higher oxygen %. The downside: **more oxygen means fire starts more easily and burns harder.**

**Very important:**
- **All tests were done in microgravity.** None were done at Moon or Mars gravity.
- Some ISS tests used **lunar-like air** (≥30% O₂, ≤70 kPa). **20 tests** match it, all ACME CFI-G gas flames. **17 FLEX droplet tests** are just outside (≥30% O₂ at 71–72 kPa): we call them **near-lunar**. No solid-material test was run in lunar or near-lunar air.
- So for a lunar base we can say how fire behaves *in that air*, but **not at Moon gravity**. The app always says this.

### Pressure units (the tables mix them)

| Unit | Normal Earth pressure |
|---|---|
| kPa | 101.3 |
| atm | 1 |
| bar | 1.013 |
| mmHg | 760 |
| psi | 14.7 |

We convert everything to **kPa**.

---

## 7. Data categories

We label each investigation two ways: **what burned**, and **which fire-safety job it helps**.

### What burned

| Category | What it is | Real-life example in a habitat |
|---|---|---|
| **Solid** | Fabrics, plastics, foam | Clothes, cable insulation, sleeping bags |
| **Liquid (droplet)** | A drop of liquid fuel | Leaking fuel, cleaning fluids |
| **Gas flame** | Burning gas from a nozzle | A gas leak, burning vapours |
| **Smoke / aerosol** | Particles in the air, not the flame itself | What a smoke detector must see |
| **Ground study** | Done on Earth: computer models, lab work | Helps explain the space results |

### Fire-safety job

| Job | Question | Investigations that help |
|---|---|---|
| **Prevention** | What will catch fire, and at what oxygen level? | BASS, BASS-II, Saffire, CFI-G, BRE |
| **Detection** | Will we notice the fire (smoke detectors)? | SAME, SAME-R, DAFT, SPICE, SLICE |
| **Suppression** | How do we put it out? | FLEX, FLEX-2 |

---

## 8. The investigations, one by one

| Name | ID | Category | In plain words | Usable test data? |
|---|---|---|---|---|
| **FLEX** (Flame Extinguishment) | PSI-69 | Droplet | Lit fuel droplets in different gas mixes (with CO₂ or helium) to see which mixes **put fires out** | ⭐ 273 tests (274 rows, 1 bad), conditions + result |
| **FLEX-2** | PSI-68 | Droplet | Follow-up of FLEX with fuel mixtures | 8 rows of *planned* conditions, not tests, no result |
| **CFI** (Cool Flames Investigation) | PSI-39 | Droplet | Studied **cool flames** that keep burning invisibly | ⭐ **227 tests in the CFI workbook** (146 with results). The CSV has only 87 rows |
| **ACME CFI-G** (Cool Flames with Gases) | PSI-159 | Gas | Lit gas flames at many oxygen levels and pressures: did it light? Did it go out by itself? | ⭐ 333 flames, conditions + result |
| **Flame Design** | PSI-10 | Gas | How oxygen and flame temperature change soot (smoke) | 327 tests, conditions only |
| **s-Flame** | PSI-23 | Gas | Round (spherical) gas flames | 18 test days, 276 flames; no per-flame rows |
| **BRE** (Burning Rate Emulator) | PSI-20 | Gas | A gas burner that **imitates a burning solid**, to measure when solids stop burning | 18 test days, 194 flames; no per-flame rows |
| **CLD**, **E-FIELD** | PSI-21, PSI-22 | Gas | Flame structure; E-FIELD uses electricity to push the flame around (like fake gravity) | Test days only: 344 and 219 flames |
| **SPICE** | PSI-107 | Gas (soot) | How much smoke gas flames make | 469 rows ≈ 150 flames (several rows per flame), conditions only |
| **SLICE** | PSI-106 | Gas | When a flame "lifts off" its burner | 12 test days, flames per day not recorded |
| **BASS** (Burning and Suppression of Solids) | PSI-26 | Solid | Burned fabrics and plastics with a fan, to find when they go out | 121 tests; conditions from the as-run workbook, results as sentences (P9) |
| **BASS-II** | PSI-25 | Solid | Same, 51 materials | 129 tests; results only as sentences in the report's Appendix A (P9) |
| **Saffire I–III** | PSI-98 to 100 | Solid | **Big** fabric fires inside an empty cargo ship | Very few tests (2 / 9 / 2) but rare space vs Earth comparison (Saffire-II: burn length in microgravity and on Earth) |
| **SAME** / **SAME-R** (Smoke Aerosol Measurement) | PSI-102 / PSI-101 | Smoke | Heated materials to make smoke and tested **smoke detectors** in space | SAME-R: 109 rows = 67 smoke tests + re-measurements of aged smoke. Conditions only: no detector or alarm column |
| **DAFT** | PSI-47 | Smoke | Tested an instrument that counts dust/smoke particles | Context only |
| **Ground studies** | PSI-60, 62, 115, 117, 142 | Ground | Models and lab experiments on Earth | Not usable as tests |

⭐ = our best tables: every test has **conditions and result**, so we can train predictors on them.

---

## 9. What's in a test table: examples

### FLEX (droplet fires): one row = one droplet lit once

| Column | Meaning | Example |
|---|---|---|
| Fuel | What liquid burned | heptane, methanol |
| Pressure | Chamber pressure (in mmHg) | 760 = normal |
| O₂ / N₂ / CO₂ / He | Gas mix in % | 21 / 79 / 0 / 0 = normal air |
| Droplet initial diameter | Starting droplet size (mm) | 3.5 |
| Burn time | Seconds the flame lasted | 12.4 |
| Extinction diameter | Droplet size when the flame went out | 1.8 |
| **Test end** (result) | How it ended | **Extinction** = went out early (fuel left) · **Completion** = burned all the fuel · **Disruption** = droplet broke apart |

### ACME CFI-G (gas flames): one row = one flame

| Column | Meaning | Example |
|---|---|---|
| Fuel | Gas used | ethane, propane, butane (often diluted, e.g. "30% butane"). The real fuel fraction is the `Xf` column |
| O₂ | Oxygen % | 18–40% (up to 85% in "inverse" flames) |
| Pressure | in bar | 0.5–3 |
| Fuel flow | How fast gas comes out | |
| **Ignition** (result) | Did it light? | yes 263 · no 62 · brief flash 8 |
| **Self-ext / flow term** (result) | Once lit, how did it end? | **SE** = went out by itself 183 · **FT** = kept burning until the gas was turned off 89 |
| Burn time, Color, Tad | Duration, blue/yellow, calculated flame temperature | |

*Normal flame* = gas blown into oxygen-rich air. *Inverse flame* = oxygen blown into fuel gas (the flame is "inside out").

### BASS-II (fabric and plastic): one row = one sample burned

| Column | Meaning |
|---|---|
| Material | e.g. cotton, Nomex, acrylic |
| O₂ / CO₂ / CO before and after | Gas levels before and after burning |
| Air display | Airflow in cm/s, often several values because the flow was changed during the test |
| Fan display / "pot" | Fan dial setting, **not** a speed; needs the calibration file |
| Result | **Not in the CSV.** It is in the report's Appendix A, as text ("flame blew out at a fan pot of 7.0") |

---

## 10. Data quality: why "cleaning" is needed

The tables were made by different teams over 15 years, so they are messy:

| Problem | Example | Fix |
|---|---|---|
| Different units | mmHg / bar / atm | Convert all to kPa |
| Numbers written as text | `"~ 21.5"`, `"22.1 to 22.0"`, `"20 cm/s"` | Parse to a number |
| Broken column names | `"O initial"` means O₂; `"?-g"` means µg | Rename |
| Fan dial instead of speed | BASS-II | Convert with the calibration file |
| Empty rows | CFI-G inverse file: 1,015 lines for 154 tests | Drop |
| Wrong values | One FLEX row has pressure = 0 | Remove / flag |
| Different text encodings | FLEX is Windows-1252 | Read with the right encoding |
| Result hidden in reports | BASS, Saffire | AI reads the report and fills it in, with the page as source |

The goal is **one clean table** in which every test has the same columns: investigation, fuel, O₂ %, pressure (kPa), diluent, result, and a link to the original row.

---

## 11. Key findings

1. **Three sources are excellent** (FLEX, CFI-G, the CFI workbook). They are the base of our predictors.
2. **Half the tables have conditions but no result.** For solids, the results are in the reports (P9 extracts them).
3. **~1,600 tests** record oxygen and pressure (1,611; for about 340 of them a value comes from a note, not the test row). Only **20** are in lunar-base air (all CFI-G gas flames). **17 more FLEX droplet tests are "near-lunar"** (≥ 30% O₂ at 71–72 kPa, just above the 70.3 kPa cutoff), and none of them went out by itself.
4. **No partial-gravity data:** nothing tested at Moon or Mars gravity.
5. **Some reports are missing** from PSI (FLEX, FLEX-2, Saffire-II, BRE, CLD, E-FIELD, SLICE; the BASS final report is broken). They can be found on NASA's report server (NTRS).
6. The challenge **Resources tab** (checked 14 Nov) has 10 links: the PSI repository (= our data), 2 NASA overview pages, a 2018 video, Apollo 1 / Apollo 13 / Mir history pages and 3 spinoff pages. **No new data**: useful only for the "About", "Why it matters" and "Earth applications" pages.

---

## 12. What we can and can't do with this data

### ✅ We can
- **Show every experiment** as a card: goal, fuel, conditions, results, sources.
- **Filter and rank** them for each habitat by matching the air.
- **Map** all tests on oxygen vs pressure, and show which habitat zones are covered.
- **Predict** (only where we have results):
  - will a droplet fire go out, and how long will it burn (FLEX)
  - will a gas flame light, and will it go out by itself (CFI-G)
- **Answer questions** with AI, citing the report and page.
- **Replay a test** as an animation, next to the real video.

### ❌ We can't
- Predict fire **at Moon or Mars gravity** (never tested). We show an "untested" range instead.
- Give one **"fire risk %"** for everything. Each experiment measures something different.
- Predict **smoke alarms** (no "alarm went off" column).
- Predict **solid / fabric burning** until the results are extracted from the reports (P9, planned in stages; ~250 tests in total).

### How a prediction stays honest
Every prediction shows:
- **the 7 most similar real tests** (so you can check)
- a **trust badge**: *Tested here* / *Between tests* / *Never tested*

---

## 13. Example to tie it all together

**Question:** "If leaking gas catches fire in a lunar rover, will the flame go out by itself?"

1. **Habitat → air:** lunar rover = ~30% O₂, ~70 kPa.
2. **Category:** liquid droplet, so we use **FLEX**.
3. **Find similar tests:** no FLEX test is strictly inside lunar air, but **17 are near-lunar** (≥ 30% O₂ at 71–72 kPa, all on the ISS, in microgravity).
4. **Result (real data):** "**0 of the 17** went out early: 15 broke apart, 2 burned all the fuel." Prediction: **unlikely to go out by itself**, trust badge *Tested here* with a **near-lunar** label.
5. **Caveat shown:** "Tested in near-lunar air (1 kPa above the lunar limit) and in microgravity. Moon gravity was never tested. These tests had no CO₂ or helium added."
6. **Source:** links to the FLEX rows and the PSI-69 record.

The same question for a **gas flame** would use **ACME CFI-G**, the only table with tests strictly inside lunar air (20 flames).

---

## 14. Where things are in our folder

| Path | What |
|---|---|
| `data/psi/investigations.csv` | One line per investigation (summary) |
| `data/psi/inventory.csv` | Every file in PSI, downloaded or not |
| `data/psi/PSI-xx/investigation.json` | Full record of one investigation |
| `data/psi/PSI-xx/tables/*.csv` | Its test tables |
| `data/psi/PSI-xx/docs/*` | Its reports |
| `data/psi/docs_selected.csv` | The 31 reports we will actually use, and why |
| `DATA_NOTES.md` | Short technical summary |
| `PROJECT_PLAN.md` | What we build, who does what, timeline |
| `FlameScope Preview (real data).html` | Clickable preview using the real data |
