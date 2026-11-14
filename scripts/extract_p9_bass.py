"""P9 stage 4: BASS (PSI-26) outcomes from the as-run workbook.

Source: data/psi/PSI-26/docs/PSI-26_Science Documents_As Run_Test Matrix.xlsx, sheet 'as run matrix'.
Unlike stages 1-3 the observation text is already in the workbook, so every field except the label is read
from it; LABELS below holds only the human-readable judgement per workbook row (keyed by row index, with
the test number as a guard). Every label needs a human check.

Labels as in stages 1-3, plus:
  suppressed_n2   put out by the nitrogen (GN2) suppression jet
  ''              no flammability result: equipment failure (igniter broke) or end not stated
Rules kept from stage 3: out when flow turned DOWN / OFF -> quench (flow 0 = off); out on its own at a
steady LOW flow (pot <= ~0.5 / fan <= ~42) -> quench; at a steady higher flow -> self_extinguished;
burned the whole sample / fuel ran out -> keeps_burning.
Flow units: air_cm_s (air display), pot (fan potentiometer), fan_display (38 = fan off; pot ~ (fan-38)/8.4).

  python scripts/extract_p9_bass.py  ->  data/psi/extracted/p9_bass.csv
"""
import collections
import csv
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx_read import read_xlsx  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data/psi/PSI-26/docs/PSI-26_Science Documents_As Run_Test Matrix.xlsx"
OUT = ROOT / "data/psi/extracted/p9_bass.csv"
SRC = "PSI-26_Science Documents_As Run_Test Matrix.xlsx (sheet 'as run matrix')"
A, P, FD = "air_cm_s", "pot", "fan_display"
KB, Q, BO, SE, NI, EU, SN = ("keeps_burning", "quench", "blowoff", "self_extinguished", "no_ignition",
                             "extinguished_unclear", "suppressed_n2")

# row: (test_no, outcome, outcome_flow_raw, unit, last_stable_flow_raw, burn_time_s, confidence, note)
LABELS = {
    3: ("1", KB, 5, A, 5, "", "high", "Burned to the end of the sample ('extinguishes at burnout')."),
    4: ("42", KB, 3, A, 3, 120, "low", "2-minute burn; end not stated."),
    5: ("18", Q, 0, A, "3-4", 120, "medium", "N2 did not put out the wake flame; went out only when all flow stopped."),
    6: ("7", KB, 10, A, 10, 40, "medium", "~40 s burn; fabric burned through (Table 7.1: BASS T7 at 10 cm/s)."),
    7: ("8", KB, 5, A, 5, 60, "medium", "~60 s burn; fabric burned through (Table 7.1: BASS T8 at 5 cm/s)."),
    8: ("43", "", "", "", "", "", "low", "No flame description (camera notes only)."),
    9: ("44", "", "", "", "", "", "low", "No flame description (camera notes only)."),
    10: ("45", Q, 38, FD, 42, "", "medium", "Flame does not go out until fan 38 (fan off); N2 also used."),
    11: ("19", Q, 0, A, 6, "", "high", "Crew turned the flow off to extinguish."),
    12: ("20", Q, 0, A, 1, "", "high", "Sooty even at 1 cm/s; extinguished when fan off."),
    13: ("21", KB, "max", FD, "max", "", "medium", "No blowoff at max fan; flow turned off when fuel ran out."),
    14: ("4", KB, 22, A, 22, 26, "medium", "26 s burn at 22 cm/s (fabric)."),
    15: ("10", KB, 11, A, 11, "", "low", "Very dim after ignition; end not stated (Table 7.1: BASS T10 at 11 cm/s)."),
    16: ("12", NI, 15, A, "", 2, "high", "Burned 2 s, died when igniter turned off; re-ignition failed."),
    17: ("54", Q, 40, FD, 61, "", "medium", "Flame went out 12 s after fan turned to 40; N2 used earlier (did not extinguish)."),
    18: ("55", Q, 0, A, 42, "", "high", "Fan off -> flame out right away; N2 used earlier."),
    19: ("56", Q, 0, A, 43, "", "high", "Turned off fan and it extinguished right away."),
    20: ("57", Q, 40.5, FD, 41, "", "high", "Turned flow down to 40.5 -> flame extinguished."),
    21: ("110", Q, 0, A, 21, 120, "high", "Burned ~2 min, extinguished when flow turned off."),
    22: ("30", KB, 5.5, A, 5.5, 180, "low", "Burned about 3 min; end not stated."),
    23: ("31", Q, 39, FD, 42, "", "medium", "'Extinguished when pot ~ 39' read as fan display 39."),
    24: ("32", Q, 41, FD, 41, "", "low", "'All blue sphere just before extinction'; flow at extinction not stated (last fan 41)."),
    25: ("33", KB, 40.5, FD, 40.5, "", "low", "Burning at fan ~40.5; end not stated."),
    26: ("12-R", NI, 9, A, "", "", "high", "Did not ignite, only smoked."),
    27: ("12-R2", NI, 9, A, "", "", "high", "No ignition."),
    28: ("46", Q, 0, A, 41, "", "high", "First ignition died at fan 41/40; second burned long, extinguished when flow turned off. N2 used."),
    29: ("47", Q, 0, A, 41, "", "high", "Slowly turned off flow -> out. N2 used."),
    30: ("48", Q, 0, A, 41, "", "high", "Shut flow off after several minutes."),
    31: ("49", Q, 0, A, 41, "", "high", "Shut flow off after several minutes; very dim blue before extinction."),
    32: ("22", Q, 0, A, 42, "", "high", "Fan off -> blue, oscillates, extinction."),
    33: ("23", Q, 0, A, 41, "", "high", "Fan off -> extinguished."),
    34: ("24", Q, 0, A, 42, "", "high", "N2 max did not blow out; N2 and air off -> out."),
    35: ("25", KB, 4, A, 4, "", "high", "Fuel ran out and flame extinguished."),
    36: ("58", KB, 4, A, 4, 285, "low", "Burned ~4.75 min; end not stated (fan column ends at 0)."),
    37: ("59", KB, 11, A, 11, 240, "low", "4-minute burn; end not stated (fan column ends at 0)."),
    38: ("60", Q, 0, A, 2, 360, "high", "Flow off -> out at ~6 min."),
    39: ("61", Q, 0, A, 2, 405, "high", "Extinguished with flow off at ~6.75 min; N2 used earlier."),
    40: ("5", Q, 41, FD, 42, "", "high", "Extinguished at fan 41 while reducing flow."),
    41: ("14", KB, 14.5, A, 14.5, "", "medium", "Spread to ~1 cm from the end (narrow flame)."),
    42: ("66", SE, 4, A, 4, "", "medium", "Steady size, very slow spread, then 'extinguished all by itself' at fan 46 (~4 cm/s)."),
    43: ("67", "", "", "", "", "", "high", "Igniter broken: no flammability result."),
    44: ("34", Q, 0, A, 0, "", "high", "N2 on; extinction when air flow off (was at ~1 cm/s)."),
    45: ("35", KB, 0, A, 0, "", "high", "Burned out completely at very slow flow."),
    46: ("16", NI, 14.5, A, "", "", "high", "Just smoked slightly, no ignition."),
    47: ("5b", SE, 10, A, "", "", "low", "Opposed flow on a preburned sample: spread a little, 'seemed to quench' 5 mm from the end."),
    48: ("6", KB, 9, A, 9, "", "high", "Opposed flow: steady spread at 9 cm/s, burned the whole sample."),
    49: ("82", Q, 40, FD, 42, "", "high", "Extinguished when fan set to 40."),
    50: ("82a", Q, 40, FD, 41, "", "high", "Out at fan 40 again."),
    51: ("82b", KB, 41, FD, 41, "", "high", "Burned to completion."),
    52: ("68", SE, 6, A, "", "", "medium", "Tiny blue flame, self-extinguished (re-ignition of a burned slab)."),
    53: ("69", NI, 10, A, "", "", "medium", "Brief flames went out; igniter problems."),
    54: ("111", Q, 0, A, 10, "", "high", "N2 max weakened it; went out when air flow turned off."),
    55: ("112", Q, 0, A, 41, 360, "high", "Air off -> flame out; 6 min burn. N2 used."),
    56: ("113", SN, 0.32, P, 0.32, "", "high", "At minimum flame (pot 0.32), GN2 max eventually extinguished it."),
    57: ("2", KB, 44, A, 44, "", "high", "Did not blow out at max flow (44 cm/s)."),
    58: ("3", KB, 44, A, 44, "", "medium", "Did not blow out at 44 cm/s; got smaller, one half may have gone out."),
    59: ("15", NI, 30, A, "", "", "high", "Did not ignite, igniter on the whole test."),
    60: ("13", NI, 15, A, "", 3, "high", "Brief ignition, extinguished in ~3 s, no spread."),
    61: ("17", NI, 8, A, "", 4, "high", "Brief ignition, extinguished after 4 s, no spread."),
    62: ("114", "", "", "", "", "", "high", "Igniter broke before ignition: no flammability result."),
    63: ("62", KB, 44, A, 44, "", "high", "Did not blow out at high flow (44 cm/s) or with GN2 (stagnation region blew out)."),
    64: ("63", KB, 10, A, 10, "", "high", "GN2 blew out bottom half only."),
    65: ("64", SN, 5, A, 5, "", "high", "Flame blew out with GN2 at about pot 6."),
    66: ("65", KB, 5, A, 5, "", "high", "GN2 up to pot 10 did not blow it out (stagnation region out at 3.5)."),
    67: ("118", "", "", "", "", "", "high", "Igniter broken, no images: no flammability result."),
    69: ("11", KB, 20, A, 20, "", "high", "Nice burn, steady size (Table 7.1: BASS T11 at 19 cm/s)."),
    70: ("9", KB, 40, FD, 40, "", "high", "Kept going to the end of the sample at the lowest flows."),
    71: ("102", KB, 5, A, 5, "", "low", "Igniter check, 'worked like a charm'; end not stated."),
    72: ("83a", Q, 0.32, P, 0.35, "", "high", "Decreased flow; flame went out at pot 0.32."),
    73: ("83b", Q, 0.31, P, 0.32, "", "medium", "Fan column: 0.31 (out)."),
    74: ("83c", KB, 0.45, P, 0.45, "", "high", "Burned out all wax."),
    75: ("84a", Q, 0.31, P, 0.32, 600, "high", "~10 min burn; steady at 0.32, 'consistently goes out at pot 0.31'."),
    76: ("84b", Q, 0.31, P, "", "", "low", "'Extinguished/burned out at 0.31': running out of wax, so may be burnout."),
    77: ("86a", Q, 0.31, P, 0.35, "", "low", "Text: 'stepped to 0 flow, went out'; fan column: '0.31 (out)'. Column value used."),
    78: ("86b", Q, 0, P, 0.31, "", "high", "Persisted at 0.31 a long time; out when fan off (38). N2 at each flow setting."),
    79: ("86c", KB, 0.53, P, 0.53, "", "medium", "Ran out of fuel."),
    80: ("70", KB, 7, A, 7, "", "low", "Steady all-blue flame at 7 cm/s, spread ~1 cm; end not stated."),
    81: ("71", KB, 9, A, 9, 480, "low", "Burned 8 minutes; end not stated."),
    82: ("74", SE, 3, A, 3, "", "medium", "At 3 cm/s it shrank slowly 'and extinguished by itself' as the leading edge burned out."),
    83: ("75", NI, 6, A, "", "", "high", "Went out when igniter retracted, twice."),
    88: ("98", KB, 12, A, 12, "", "low", "Nice ignition; end not stated (lens cap on)."),
    89: ("99", Q, 0, A, "", "", "low", "'Extinguished at very low flow' while fan was turned slowly to zero."),
    90: ("114", "", "", "", "", "", "low", "No flame description; igniter failed after this test."),
    91: ("115", KB, 0, A, 0, "", "low", "Dim flame spreading upstream; end not stated."),
    92: ("116", Q, 0, A, 0, "", "high", "Put out by turning air off (was at fan 42 / pot 0.5)."),
    93: ("117", Q, 0.32, P, "", "", "high", "Went out at pot 0.32."),
    94: ("117a", Q, 0, A, 1, "", "medium", "Still burning at 1 cm/s; fan column ends 'off'."),
    95: ("100", Q, 39, FD, 42, "", "high", "Went out when fan set to 39. GN2 vitiation ran during the test (final O2 17.3%)."),
    96: ("85", KB, 41, FD, 41, "", "low", "Steady blue at fan 41; end not stated. GN2 vitiation during the test (O2 to 16.8%)."),
    97: ("93", Q, 41, FD, 41, "", "medium", "Went out on its own at a steady low flow (fan 41)."),
    98: ("26", KB, 0.33, P, 0.33, 195, "low", "Still burning in the last picture (~3:15)."),
    99: ("27", Q, 0, P, 0.35, "", "high", "Stable at pot 0.35, out when fan off."),
    100: ("28", KB, 0.35, P, 0.35, "", "high", "Burned out the sample."),
    101: ("87", Q, 41, FD, 42, "", "medium", "Long burn at very low flow; 'candle out at flow change' (to fan 41)."),
    102: ("103", Q, 0.32, P, 0.35, "", "high", "Extinguished on the last flow change (pot 0.35 -> 0.32)."),
    103: ("104", Q, 0, A, 1, "", "high", "GN2 max could not blow it out; extinguished when flow off."),
    104: ("105", Q, 41, FD, 41, "", "medium", "Out at a finite, extremely low flow (fan 41)."),
    105: ("38", NI, 8, A, "", "", "high", "Repeated ignition attempts, only brief flames."),
    106: ("39", Q, 0.32, P, 0.35, "", "high", "Fan turned down in steps; self-extinguished at pot 0.32."),
    107: ("40", KB, 0.3, P, 0.3, "", "high", "All blue at low flows, burned out the fuel."),
    108: ("72", NI, 9, A, "", "", "high", "Opposed flow: no sustained flame, winks out after igniter retract."),
    109: ("73", NI, 15, A, "", 15, "high", "Opposed flow: brief flame ~15 s, did not sustain."),
    110: ("118", Q, 0.32, P, "", "", "medium", "Burned on the stagnation region only; 'went out at finite flow' (fan column ends 0.32)."),
    111: ("119", Q, 0, P, 0.3, "", "high", "Down to pot 0.3, then flow shut off to put it out."),
    112: ("89", Q, 0.32, P, 0.33, "", "medium", "Pots stepped down to 0.32, then 'out'."),
    113: ("95", NI, 5, A, "", "", "low", "No ignition despite prolonged attempt; 'candle out of wax?'."),
    114: ("92", KB, 0.4, P, 0.4, "", "medium", "Went out at low flow because it ran out of wax."),
    115: ("78", Q, 0.4, P, "", 75, "high", "Did not propagate; went out on its own at pot 0.4 after 75 s."),
    116: ("50", EU, 5, A, "", 120, "low", "'Short burn about 2 minutes' at 5 cm/s; cause not stated. Date reads 2103 (typo)."),
    117: ("51", KB, 5, A, 5, "", "low", "Blue flame; end not stated."),
    118: ("52", KB, 0.5, P, 0.5, "", "low", "Burning (blue with soot balls); end not stated."),
    119: ("53", "", "", "", "", "", "high", "Broke 2 igniters, no ignition: equipment, no flammability result."),
    120: ("106", KB, 0.5, P, 0.5, "", "low", "All blue at < 1 cm/s; end not stated."),
    121: ("107", "", "", "", "", "", "low", "Only 'ignition in 1.5 min'; no flame outcome."),
    122: ("108", Q, 0.29, P, 0.35, "", "high", "Went out when pot turned down to 0.29."),
    123: ("109", Q, 0.27, P, "", "", "high", "Went out at pot 0.27 with oscillations and a flash."),
    124: ("79", NI, "", "", "", "", "high", "Ignited briefly, went out, could not re-ignite."),
    125: ("80", NI, 10, A, "", "", "low", "No flame: 'not enough fuel in forward patch'."),
    126: ("75", NI, 10, A, "", "", "high", "No ignition, puff of smoke."),
    127: ("53", KB, "", "", "", "", "low", "Good ignition and flow dynamics; end not stated."),
    128: ("53a", Q, 0.28, P, "", "", "medium", "'Limit pot setting about 0.28'."),
}
SKIP = {68, 84, 85, 86, 87}  # soot cleaning, stow, blank, setup, dilution check: not burns
N2_SUPPRESSION_ROWS = {5, 10, 17, 18, 28, 29, 34, 44, 54, 55, 56, 63, 64, 65, 66, 78, 103}


def iso(cell):
    try:
        return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(cell)))).isoformat()
    except ValueError:
        return str(cell).strip()


def flow_direction(material, dist):
    t = f"{material} {dist}".lower()
    if "oppos" in t or "oppsed" in t:
        return "opposed"
    if "sphere" in t or "candle" in t or (t.startswith("pmma") and " cm" in t and "slab" not in t):
        return "stagnation"
    return "concurrent"


def main():
    rows = read_xlsx(XLSX)["as run matrix"]
    out, seen_samples = [], set()
    for i, r in enumerate(rows):
        if i < 3 or i in SKIP or i > 128:
            continue
        r = r + [""] * (30 - len(r))
        test = str(r[3]).strip()
        lab = LABELS[i]
        assert lab[0] == test, (i, lab[0], test)
        sample = str(r[4]).strip()
        reused = sample != "" and sample in seen_samples
        seen_samples.add(sample)
        o2 = float(r[26]) * 100 if r[26] not in ("", None) else ""
        out.append({
            "workbook_row": i + 1, "as_run_no": str(r[2]).strip(), "test_no": test, "date": iso(r[0]),
            "sample_no": sample, "material": str(r[5]).strip(), "flow_restrictor": str(r[7]).strip(),
            "sample_distance": str(r[8]).strip(), "flow_direction": flow_direction(r[5], r[8]),
            "fan_display_raw": str(r[9]).strip(), "air_display_raw": str(r[10]).strip(),
            "o2_pct": round(o2, 2) if o2 != "" else "", "pressure_atm": round(float(r[27]), 3) if r[27] else "",
            "co2_mmhg": str(r[28]).strip(),
            "outcome": lab[1], "outcome_flow_raw": lab[2], "outcome_flow_unit": lab[3],
            "last_stable_flow_raw": lab[4], "burn_time_s": lab[5], "reused": reused,
            "n2_suppression_used": i in N2_SUPPRESSION_ROWS, "confidence": lab[6],
            "observation": " ".join(str(r[29]).split()), "notes": lab[7],
            "source_doc": SRC, "source_page": f"row {i + 1}",
        })
    assert len(out) == len(LABELS) == 121, len(out)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), "rows ->", OUT)
    print(dict(collections.Counter(r["outcome"] or "(blank)" for r in out)))
    print("flow direction:", dict(collections.Counter(r["flow_direction"] for r in out)))
    print("reused:", sum(r["reused"] for r in out), " N2 used:", sum(r["n2_suppression_used"] for r in out))


if __name__ == "__main__":
    main()
