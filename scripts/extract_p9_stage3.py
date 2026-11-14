"""P9 stage 3: Bhattacharjee (A.1), Ferkul (A.2), Fernandez-Pello (A.3), Miller (A.4).

Hand-transcribed from PSI-25_Reports_BASS-II Summary Report.pdf, Appendix A (viewer pp. 111-117,
printed 103-109), read from 220-dpi page renders. Observation copied verbatim; outcome only from the
text (or the fan/air column when the text is silent, see notes). Every row needs a human check.

Outcome labels (same as stages 1-2, plus one):
  keeps_burning      still burning / burned the whole sample / ended by the crew
  quench             went out while or just after the flow was turned DOWN (incl. flow turned off)
  blowoff            blown out when the flow was turned UP
  self_extinguished  went out on its own at a steady, not-low flow (no flow change at the time)
  no_ignition        no sustained flame
  extinguished_unclear  went out, cause not stated
  (blank)            end not stated

  python scripts/extract_p9_stage3.py   ->  data/psi/extracted/p9_stage3.csv
"""
import collections
import csv
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data/psi/extracted/p9_stage3.csv"
DOC = "PSI-25_Reports_BASS-II Summary Report.pdf"

F = ["test_id", "as_run_no", "date", "sample_no", "material", "igniter", "flow_restrictor", "flow_direction",
     "fan_display_raw", "air_display_raw", "o2_cal_initial_pct", "o2_cal_final_pct",
     "outcome", "outcome_flow_raw", "outcome_flow_unit", "last_stable_flow_raw", "burn_time_s",
     "reused", "confidence", "observation", "notes"]
O, CO, ST = "opposed", "concurrent", "stagnation"
P, A = "pot", "air_cm_s"

R = [
    # ===== A.1 Bhattacharjee, viewer p. 111 (printed 103): PMMA films, opposed flow
    ("B1", 7, "2/19/2014", "147", "100-um PMMA film, 2 cm wide", "Integral", 2, O, "62", "5", 22.2, 22.2,
     "quench", 0, A, 5, "", False, "medium",
     "Ignited very quickly, turned flow off after spread halfway; flame extinguished very quickly; and sooty with blue leading edge",
     "Went out after the flow was turned off."),
    ("B10", 62, "7/7/2014", "173m", "1-cm, 0.2-mm PMMA film", "Integral", 2, O, "1.7 (52), 1.25, 0.9, 0.6, 0.4, 0.35", "5, 4, 3, 2, 1", 21.0, 20.8,
     "quench", 0.35, P, 0.4, "", False, "high", "Multiple velocities for steady spread, extinguished at pot 0.35", ""),
    ("B11", 61, "7/7/2014", "158m", "2-cm, 0.2-mm PMMA film", "Integral", 2, O, "2.5 (59), 1.3, 0.7, 0.5, 0.35", "5, 3, 1, <1", 21.0, 20.7,
     "quench", 0.35, P, 0.5, "", False, "high", "Multiple velocities for steady spread, extinguished at pot 0.35", ""),
    ("B12", 13, "2/19/2014", "160", "300-um film, 2 cm wide", "Integral", 2, O, "46.5", "2", 22.2, 22.1,
     "keeps_burning", 2, A, 2, "", False, "medium", "Mostly blue, soot only on bottom", "No extinction described."),
    ("B13", 63, "7/7/2014", "162m", "2-cm, 0.4-mm thick film", "Integral", 2, O, "3.5 (68), 1.7, 1.25, 0.9, 0.6, 0.4, 0.35", "10, 5, 4, 3, 2, 1", 21.0, 20.5,
     "quench", 0.35, P, 0.4, "", False, "high", "Multiple velocities for steady spread, extinguished at pot 0.35", ""),
    ("B14", 47, "7/2/14", "174m", "1-cm-wide, 200-um-thick PMMA", "Integral", 2, O, "", "5, 3, 2, extinction", 15.0, "",
     "no_ignition", 5, A, "", "", False, "medium", "HCl O, only brief ignition, flame extinguished",
     "'Only brief ignition' = no sustained flame (air column lists 5, 3, 2, extinction). Final O2 '-----'."),
    ("B15", 59, "7/7/2014", "149m", "2-cm, 0.1-mm PMMA film", "Integral", 0, O, "1.4 (50) increase to 10.0 pot", "10, max", 21.0, 20.8,
     "keeps_burning", 10, P, 10, "", False, "high", "Spread at 10 cm/s, did not blowoff", "No blowoff at maximum flow (pot 10, no restrictor)."),
    ("B16", 51, "7/2/14", "150m", "2-cm 100-um-thick PMMA", "Integral", 2, O, "", "3, 5 pot, 0.4 pot", 17.3, 17.2,
     "quench", 0.4, P, "", "", False, "high",
     "HCl 1.1 > 1.3; flame quenched after prolonged burn at 0.4 pot, one-sided flame; spread to top side and quenched immediately; did igniter wire affect top flame?", ""),
    ("B17", 48, "7/2/14", "175m", "1-cm-wide, 200-um-thick PMMA", "Integral", 2, O, "", "5, 3, pot 0.4", 17.5, 17.4,
     "quench", 0.4, P, "", "", False, "high",
     "Burned steadily at higher flows, extinguished just as we reached a pot of 0.4; vapor jetting more on bottom, possibly because of sample tilted slightly to flow?", ""),
    # ===== A.1 concluded, viewer p. 112 (printed 104)
    ("B18", 49, "7/2/14", "176m", "1-cm-wide, 200-um-thick PMMA", "Integral", 0, O, "", "10, blowoff", 17.4, 17.4,
     "blowoff", 7.0, P, "", "", False, "high", "HCl 0.6 > 0.9, flame blew out at a fan pot of 7.0", ""),
    ("B19", 52, "7/2/14", "151m", "2-cm, 100-um-thick PMMA", "Integral", 0, O, "", "10, blowoff", 17.3, 17.2,
     "blowoff", 6.0, P, "", "", False, "high", "HCl 1.3 > 1.4; flame blew out at a pot of 6.0", ""),
    ("B2", 8, "2/19/2014", "155", "200-um PMMA film, 2 cm wide", "Integral", 2, O, "62", "5", 22.2, "",
     "", "", "", "", "", False, "low", "No stills taken, cable came loose; not quite a straight on edge view",
     "End not stated (camera problem). Table final O2 reads 1.6 (typo), left blank."),
    ("B20", 50, "7/2/14", "152m", "2-cm, 100-um-thick PMMA", "Integral", 2, O, "", "5, 3, pot 0.5", 17.4, 17.4,
     "keeps_burning", 0.5, P, 0.5, "", False, "high", "HCl 0.9 > 1.1; flame burned entire sample", ""),
    ("B21", 121, "8/4/14", "174m", "1-cm-wide, 200-um-thick PMMA", "46", 1, O, "53 and down", "5 down to extinction", 20.8, 20.6,
     "quench", 0.355, P, "", "", True, "high",
     "Ignition at 5 cm/s then fan pot turned down slowly after flame; spreads halfway; flame goes out at 0.355 pot setting",
     "Sample 174m was used in B14 (reused)."),
    ("B22", 126, "8/4/14", "176m", "1-cm-wide, 200-um-thick PMMA", "39", 1, O, "53, 42, 41, 40.5", "5, 2, 0", 20.7, 20.5,
     "quench", 0.36, P, 0.4, "", True, "high",
     "Ignition at 5 cm/s then decreased flow in step, fan pot 1.7, 0.5, 0.4, 0.36 (flame out)",
     "Sample 176m was used in B18 (reused)."),
    ("B3", 11, "2/19/2014", "148", "100-um film, 2 cm wide", "Integral", 2, O, "47", "2", 22.2, 21.8,
     "keeps_burning", 2, A, 2, "", False, "medium",
     "Probably 20.6 O2 to start; lower flow flames much more blue overall; still some soot though",
     "No extinction described. Text says initial O2 was probably 20.6, not 22.2."),
    ("B4", 9, "2/19/2014", "159", "300-um PMMA film, 2 cm wide", "Integral", 2, O, "61", "5", 22.2, 22.2,
     "keeps_burning", 5, A, 5, "", False, "low", "Bubble layer thickness increases with sample thickness",
     "No extinction described; text is about the bubble layer only."),
    ("B5", 10, "2/19/2014", "156", "200 um 2 cm wide", "Integral", 2, O, "59", "5", 22.2, 21.9,
     "keeps_burning", 5, A, 5, "", False, "low",
     "Repeat of B2 test conditions, to get top view images; question the 20.9 reading; all others were 20.6 this day",
     "No extinction described. O2 reading questioned in the text."),
    ("B6", 57, "7/7/2014", "153m", "2-cm, 0.1-mm PMMA film", "Integral", 2, O, "0.9, 1.3, 2.75", "3, 5, approaching 10", 21.0, 20.9,
     "keeps_burning", 2.75, P, "", "", False, "high",
     "Steady burning at 3 and 5 cm/s, did not reach 10 cm/s before end of sample, complete burnout, HCl -->0.3", ""),
    ("B7", 12, "2/19/2014", "161", "400-um film, 2 cm wide", "Integral", 2, O, "47", "2", 22.2, 22.1,
     "keeps_burning", 2, A, 2, "", False, "low", "Very long bubble layer", "No extinction described."),
    ("B8", 60, "7/7/2014", "157m", "2-cm, 0.2-mm PMMA film", "Integral", 0, O, "1.4, increase to 10.0", "10, maximum", 21.0, 20.5,
     "keeps_burning", 10, P, 10, "", False, "high", "Spread at 10 cm/s, did not blowoff", "No blowoff at maximum flow (pot 10, no restrictor)."),
    ("B9", 58, "7/7/2014", "154m", "2-cm, 0.1-mm PMMA film", "Integral", 2, O, "0.6, 0.35", "2, <1", 21.0, 20.9,
     "quench", 0.35, P, 0.6, "", False, "high", "Steady burning at 2 cm/s, extinguished at 0.35", ""),
    # ===== A.2 Ferkul, viewer p. 113 (printed 105)
    ("F1", 14, "2/19/2014", "227", "Nomex III natural", "Integral", 2, CO, "82", "9.5", 22.2, 22.2,
     "no_ignition", 9.5, A, "", "", False, "high",
     "Ignited briefly but did not spread at all and extinguished while the igniter was still on", ""),
    ("F2", 103, "7/28/2014", "228m", "Nomex III natural", "Integral", 2, CO, "92", "15", 21.0, 21.0,
     "no_ignition", 15, A, "", "", False, "high", "Tried to ignite, flame would not sustain", ""),
    ("F3", 115, "8/1/14", "229m", "Nomex III natural", "Integral", 1, CO, "61", "8", 21.7, "",
     "no_ignition", 8, A, "", "", False, "high", "Brief ignition flash, no sustained flame; no postburn sensor readings taken",
     "Table final O2 reads 0.9 (no postburn reading), left blank."),
    ("F4", 36, "6/24/2014", "39M", "Japan Wax candle", "Integral", 2, ST, "See notes", "3 ignition", 17.4, 17.4,
     "quench", 0.305, P, 0.31, "", False, "high",
     "Long ignition, but blue flame established at 3 cm/s, reduced flow in increments: potentiometers 0.6, 0.4, 0.35, 0.32, 0.31, 0.305 flame extinguished",
     "Date reads 6/24/2018 in the table (typo, same day as T9/T10/T18)."),
    # ===== A.3 Fernandez-Pello, viewer p. 114 (printed 106): PMMA rods
    ("P1", 25, "6/16/14", "185m", "6.35-mm black rod", "-22", 2, O, "", "5, 2, slow decrease to extinction", 17.7, 17.5,
     "quench", 0.315, P, "", "", False, "high",
     "Broke -20, -21 igniters, -22 worked; nice flame, got down to extinction at pot 0.315 (finite low flow), very slow increments", ""),
    ("P10", 55, "7/3/2014", "187m", "6.35-mm black rod", "-35", 2, O, "48, 41", "5, pots 0.4, 0.36, 0.32, 0.31, 0.30 extinguished", 17.0, 16.4,
     "quench", 0.30, P, 0.31, "", False, "high", "HCl 0.3 > 0.9, steady burn at multiple velocities, finite quench at pot 0.3", ""),
    ("P12", 104, "7/29/14", "199m", "9.525-mm black rod", "-36", 2, O, "60, 52, 48, 44.5, 42, 41.5, 41 (2.6, 1.6, 1.2, 0.75, 0.5, 0.4, 0.36, 0.34)", "5, 3, 2, 1, 0.5, lower", 17.5, 16.8,
     "quench", 0.34, P, 0.36, "", False, "high",
     "Loss of signal before extinguished, oscillating at 0.36, out immediately at 0.34, multiple steady spread flows", ""),
    ("P13a", 85, "7/14/14", "203m", "12.7-mm black rod", "-37", 2, O, "Fan pot 1.1 (5cm/s), 0.4, 0.36, 0.32, 0.3, 0.28, 0.26, 0 ext", "5 down to extinction", 20.7, 19.1,
     "quench", 0, P, 0.26, "", False, "high",
     "Fan pot 1.1 (5 cm/s), 0.4, 0.36, 0.32, 0.3, 0.28, 0.26; flame out when pot turned to 0; HCL 0.5 > 4.1; flame reached front of sample and began to wrap around",
     "Burned at every finite flow; went out only when the flow was turned off."),
    ("P13b", 86, "7/14/14", "203m", "12.7-mm black rod", "-37", 2, O, "Fan pot 1.3 (5cm/s), 0.4, 0.36, 0.32 ext", "5 down to extinction", 20.6, 20.2,
     "quench", 0.32, P, 0.36, "", True, "high", "Fan pot 1.3 (5 cm/s), 0.4, 0.36, 0.32; flame out when pot turned to 0.32", "Same sample as P13a."),
    ("P14", 29, "6/23/2014", "189M", "6.35-mm black rod", "-22", 2, O, "46, 41", "5, low (0.85, 0.4, 0.32)", 18.4, 18.0,
     "quench", 0.31, P, 0.32, "", False, "high", "All blue, extinguished at 0.31", ""),
    ("P15", 30, "6/23/2014", "190M", "6.35-mm black rod", "-22", 2, O, "46, 41", "5, (0.36)", 18.0, 17.5,
     "keeps_burning", 0.36, P, 0.36, "", False, "medium", "Nice stable burn with sooty tail but blue leading edge", "No extinction described."),
    ("P16", 93, "7/22/14", "191m", "6.35-mm black rod", "-36", 2, CO, "49, 62, 44, 41.5, 41 (pots 1.3, 2.8, 0.7, 0.4, 0.36, 0.32)", "5, 8, 2, low", 18.2, 17.4,
     "quench", 0.32, P, 0.36, "", False, "high", "Extinguished at pot 0.32, one high flow setting", "Concurrent flow."),
    ("P17", 105, "7/29/14", "192m", "6.35-mm rod", "-36", 2, O, "60, 52, 48, 233, 48, 41 (2.6, 1.6, 1.2, 10, 1.2, 0.36, 0.34)", "5, 3, 22, 2, low", 16.8, 16.5,
     "quench", 0.34, P, 0.36, "", False, "high",
     "A few finite flows, then tried blowoff without success, turned back down to 2 cm/s, then 0.36, 0.34 pots, oscillated and out at 0.34; leading edge receded slightly but did not blowoff",
     "No blowoff at pot 10 (air 22 cm/s) before the quench."),
    ("P18", 107, "7/30/14", "193m", "6.35-mm black rod", "36", 2, O, "55, 47, etc. (pot 1,2,1,2, etc.)", "2, 0, 2, 0, etc.", 20.0, 19.0,
     "quench", 0.32, P, "", "", False, "high",
     "Alternated fan pot between 1 and 2 at 1-min intervals to try to get time constant resolution; finally turned pot down slowly, extinction at fan pot 0.32", ""),
    ("P19", 94, "7/22/14", "194m", "6.35-mm black rod", "-36", 2, CO, "49, 62, 44, 41.5, 122, 41 (pots 1.3, 2.8, 0.7, 0.4, 0.36, 10., 0.32)", "5, 8, 2, maximum, 0", 17.5, 16.7,
     "quench", 0.32, P, "", "", False, "high",
     "Tried blowoff, did not blowoff at pot 10 2 restrictors, flame out at 0.32, sample mostly gone",
     "Concurrent flow. No blowoff at pot 10 before the quench."),
    ("P2", 26, "6/16/2014", "188M", "6.35-mm black rod", "-22", 2, O, "", "5, 2.5 (pot 0.9, 0.5, 0.35, 0.33)", 17.4, 17.2,
     "quench", 0, P, 0.33, "", False, "medium",
     "Nice stable burn at low velocity, mostly blue with some inner soot at higher flow, stable flame at pot 0.33, did not get extinction on stills, but was just fan off, not slow ramp",
     "Stable at pot 0.33; went out when the fan was switched off."),
    ("P20", 109, "7/30/14", "195m", "6.35-mm black rod", "36", 2, O, "55, 47, etc. (pot 1, 2, 1, 2, etc.)", "2, 0, 2, 0, etc.", 19.0, 18.2,
     "quench", 0.335, P, "", "", False, "high",
     "Alternated fan pot between 1 and 2 at 1-min intervals to try to get time constant resolution; finally turned pot down slowly, extinction at fan pot 0.335", ""),
    ("P21a", 31, "6/23/2014", "196M", "6.35-mm black rod", "-22", 2, O, "46", "5", 16.3, 16.3,
     "self_extinguished", 5, A, "", "", False, "high", "Flame self-extinguished at 5 cm/s after sample end became flat, dim flame",
     "Went out at a steady 5 cm/s, no flow change."),
    ("P21b", 32, "6/23/2014", "196M", "6.35-mm black rod", "-22", 2, O, "46", "5", 16.3, 16.3,
     "no_ignition", 5, A, "", "", True, "high", "Igniter broke after third attempt to ignite flattened end of sample", "Same sample as P21a."),
    # ===== A.3 concluded, viewer p. 115 (printed 107)
    ("P22a", 68, "7/8/2014", "200m", "9.525-mm black rod", "-35", 2, O, "5, 0.36, 0.32 extinction after some time", "5 down to extinction", 20.8, "",
     "quench", 0.32, P, 0.36, "", False, "high",
     "Extinguished at higher flow, possibly rod not preheated enough by a bit, CO readings elevated, slow response",
     "Flow from the fan column. Table final O2 reads 0.6 (typo), left blank."),
    ("P22b", 69, "7/8/2014", "200m", "9.525-mm black rod", "-35", 2, O, "5, 0.36, 0.34, 0.33, 0.32, 0.31, extinction", "5 down to extinction", 20.0, "",
     "quench", 0.31, P, 0.32, "", True, "high",
     "Extinguished at lower flow than P22a by a bit, longer slower decrease in flow, CO elevated, slow response",
     "Same sample as P22a. Initial O2 printed in red in the table; final O2 reads 39.1 (typo), left blank."),
    ("P23", 110, "7/30/14", "201m", "9.525-mm black rod", "36", 2, O, "55, 47, etc. (pot 1, 2, 1, 2, etc.)", "2, 0, 2, 0, etc.", 18.2, 17.0,
     "quench", 0.38, P, "", "", False, "high",
     "Alternated fan pot between 1 and 2 at 1-min then 2-min intervals to try to get time constant resolution; finally turned pot down slowly, extinction at fan pot 0.38", ""),
    ("P24", 108, "7/30/14", "819L", "9.525-mm black rod", "36", 2, O, "55, 47, etc. (pot 1,2,1,2, etc.)", "2, 0, 2, 0, etc.", 19.0, 17.5,
     "quench", 0.30, P, "", "", False, "high",
     "Alternated fan pot between 1 and 2 at 1-min intervals to try to get time constant resolution; finally turned pot down slowly, extinction at fan pot 0.30", ""),
    ("P25", 70, "7/8/2014", "217m", "9.525-mm clear rod", "-36", 2, O, "5, 0.36, 0.34, 0.33, 0.32, 0.31, extinction", "5 down to extinction", 20.9, 20.2,
     "quench", 0.31, P, 0.32, "", True, "high",
     "Reburn of 217m in opposed geometry, repeat of P22b, extinguished at same 0.31 pot, more sparklers from flame, and less leading edge vapor jetting, or more central jetting; rod warped downward in video view at end of test, asymmetrical instabilities noted briefly at pot change to 0.32, CO elevated, slow response",
     "Sample 217m was first burned in Olson O12 (reused)."),
    ("P3a", 27, "6/16/2014", "215M", "6.35-mm clear rod", "-22", 2, O, "", "5, 2.5 (1.15, 0.5, 0.35, 0.33. 0.32, 0.315, 0.31, 0.3)", 17.7, 17.4,
     "quench", 0.3, P, 0.31, "", False, "high", "Repeat of last test with clear rod; extinguished at 0.3 pot very small flame, but steady spread", ""),
    ("P3b", 28, "6/16/2014", "215M", "6.35-mm clear rod", "-22", 2, O, "", "5, very low (0.85, 0.32, 0.31, 0.305, 0.30, 0.295)", 17.4, 16.8,
     "keeps_burning", 0.295, P, 0.295, "", True, "low",
     "Very low velocity test to get limiting spread rate, pot 0.32 spread, 0.31 spread, etc.; power failed to camera?; fan still running; camera power cable needed repair and taping to camera body to make it work",
     "Same sample as P3a. End not stated; still spreading at the lowest pot listed (0.295)."),
    ("P4", 54, "7/3/2014", "197m", "9.525-mm black rod", "-35", 2, O, "48, 41", "5, pots 0.4, 0.36, 0.32, 0.308, .3, off", 18.5, 17.1,
     "quench", 0, P, 0.3, "", False, "high", "HCl 0.9 > 1.8, long slow burn, steady at multiple pots until turned off flow",
     "Burned at every finite flow; went out only when the flow was turned off."),
    ("P5", 83, "7/14/14", "202m", "12.7-mm black rod", "-37", 2, O, "Fan pot 1.5 (5cm/s), 0.9, 0.4, 0.36, 0.32, 0.308, 0.3, 0.29, 0.28, 0, extinction", "5 down to extinction", 19.3, 17.6,
     "quench", 0, P, 0.28, "", False, "high",
     "Fan pot 1.5 (5 cm/s), 0.9, 0.4, 0.36, 0.32, 0.308, 0.3, 0.29, 0.28 (flame persisted for all) finally turned down flow to 0 to extinguish; HCL 0 > 4.7; lots of fuel left behind, conical shape",
     "Burned at every finite flow; went out only when the flow was turned off."),
    ("P6", 53, "7/3/2014", "186m", "6.35-mm black rod", "-35", 2, O, "48, 41", "5, pots 0.4, 0.36, 0.32, 0.31, off", 18.9, 18.5,
     "quench", 0, P, 0.31, "", False, "high", "HCl 0 > 0.9, steady burning until turned flow off, multiple pot settings",
     "Burned at every finite flow; went out only when the flow was turned off."),
    ("P8", 56, "7/3/2014", "197m", "9.525-mm black rod", "-35", 2, O, "48, 62, 75", "5, would not stay lit, 10, 15 ibid", 16.4, 16.3,
     "no_ignition", 15, A, "", "", True, "high", "HCl 0.9 > 0.9, would not stay lit, tip of sample was flat",
     "Same sample as P4. Tried 5, 10 and 15 cm/s."),
    ("P9", 84, "7/14/14", "202m", "12.7-mm black rod", "-37", 2, O, "Fan pot 1.5 (5cm/s), 0.9, 0.4, 0.36, 0.32, 0.3, 0.28 extinction", "5 down to extinction", 17.6, 17.1,
     "quench", 0.28, P, 0.3, "", True, "high",
     "Fan pot 1.5 (5 cm/s), 0.9, 0.4, 0.36, 0.32, 0.3, 0.28 flame out at 0.28; HCL 4.7 > 4.5; flame did not leave conical portion behind, rather fuel was consumed but final sample shape was very irregular",
     "Same sample as P5."),
    # ===== A.4 Miller, viewer p. 116 (printed 108): PMMA slabs, opposed flow
    ("M1", 15, "2/20/14", "222", "1-mm-thick PMMA, one-sided, 2 cm", "Integral", 2, O, "58, 54", "10, 8", 22.2, 21.9,
     "quench", 0, A, 8, "", False, "medium",
     "Prolonged ignition, flame initially on both sides, after igniter off and flame moved away from end, bottom flame died and top flame became all blue and small; very slow propagation; changed flow from 10 to 8 cm/s and flame shrank to a circle; spread just over 1/3 of sample when we ran out of camera card, and put flame out by turning off flow",
     "Still spreading at 8 cm/s; went out when the crew turned the flow off (same rule as P4/P13a: flow-off extinction = quench at 0)."),
    ("M10", 97, "7/23/14", "180m", "4-mm-thick, 1-cm-wide PMMA slab", "Integral", 2, O, "75, 105, 94/91, 72/69, 63/61 (4.4, 8.0, 6.6/6.3, 4.0/3.7, 3.0/2.7)", "10, 17, 14, 10, 8", 20.1, 18.6,
     "self_extinguished", 8, A, "", "", False, "high",
     "Long burn, quick ignition, flame in seconds, kept it on 40 s + 2nd on for another 10 to 15 s when it was shrinking; multiple flows for steady spreading; flame big at 17, so only left it there 3 min; other flows longer; flame self-extinguished at 8 cm/s after almost 10 min; Alex saw it going out and locked shutter for the last few seconds; pictures start after ignition, about every 8 s",
     "Went out at a steady 8 cm/s after almost 10 min."),
    ("M11", 80, "7/11/14", "181m", "1-cm-wide PMMA 5 mm thick", "Integral", 2, O, "3.9, 6.5, 4.6, 3.3, 2.9, 2.8; 62.5, 93, 77, 66, 63, 62", "10, 20, 15, 12", 20.0, 18.5,
     "extinguished_unclear", 12, A, "", 1740, False, "medium", "29-min burn; extinguished at 12 cm/s., HCl 0.5 > 5.0",
     "Cause not stated. Burn time 29 min (stated)."),
    ("M12", 114, "7/31/14", "165m", "2-mm-thick PMMA, 2 cm wide", "Integral", 1, O, "41, 42, 41", "<1", 21.7, 20.4,
     "keeps_burning", 0.35, P, 0.35, "", False, "low",
     "Vigorous ignition led to trying to get flame under control; finally had about plateaus at pot = 0.35, 0.4, and again 0.35",
     "End not stated; burning at pot 0.35 when last described."),
    ("M13", 112, "7/31/14", "169m", "4-mm-thick PMMA, 2 cm wide", "Integral", 1, O, "52, 47, 43", "6, 5, 4", 20.8, 19.0,
     "quench", 0.3, P, 0.55, "", False, "high",
     "Mild ignition at 10 cm/s; decreased flow down holding constant for 6 min at pot settings of 1.7, 1.0, and 0.55; finally extinguished by turning pot down to 0.3", ""),
    ("M14", 16, "2/20/14", "223", "2-mm-thick PMMA, one-sided, 2 cm wide", "Integral", 2, O, "Pot 2.4, 1.87 (54)", "10, ~8", 22.2, 21.6,
     "self_extinguished", 9, A, "", "", False, "medium",
     "Prolonged ignition, followed by flow reduction after flame moved away from igniter region and spread steadily; flame self-extinguished at an air reading of 9 cm/s.",
     "Spread steadily after the flow reduction, then went out at 9 cm/s."),
    ("M15", 64, "7/7/2014", "225m", "2-cm, 4-mm, one-sided PMMA slab", "Integral", 2, O, "Ignited 10, adjusted down then up to 20, down in increments to 15", "10, 8, 7, 8, 10, 20, 18, 16, 15", 21.0, 20.0,
     "self_extinguished", 15, A, 15, "", False, "medium",
     "Ignited and turned flow down to control flame size during end burning, then turned flow up to 20 cm/s and got steady spreading there, turned down flow to 15 and got spreading and slow extinction there.",
     "Spread at 15 cm/s, then slow extinction at that steady flow."),
    ("M16", 99, "7/23/14", "164m", "1-mm-thick PMMA, 2 cm wide", "Integral", 2, O, "73, 57, 59, 48, 45, 43, 75 (4.2, 2.2, 2.4, 1.2, 0.8, 0.5, 4.4)", "10, 6, 3, 2, 1, 10", 19.2, 18.7,
     "keeps_burning", 0.5, P, 0.5, "", False, "high",
     "Burned at decreasing flow down to 1 cm/s or so, still fine, at end of sample, turned up flow to 10 cm/s and flame got really long; turned it down but Alex reported some soot on the door and some on the heat sink; dry wipe would not wipe off; try Monday with some other-water?",
     "Burned to the end of the sample at ~1 cm/s (pot 0.5)."),
    ("M17", 88, "7/15/14", "166m", "2-cm-wide PMMA, 2 mm thick", "Integral", 2, O, "Fan pot 3.7, 1.7, 1.5, 1.3, 0.8, 0.6, 0.5, 0.3 extinction", "10, 5, 3, 0, extinction", 18.8, 17.1,
     "quench", 0.3, P, 0.5, 1800, False, "medium",
     "30-min burn targeted constant flows of 10, 5, and 3; finally turned fan pot to 0 to extinguish. HCl 0.3 > 3.7",
     "Crew turned the flow down to extinguish. Text says pot 0, fan column says 0.3 extinction (0.3 used). Burn time 30 min (stated)."),
    ("M18", 87, "7/15/14", "168m", "2-cm-wide PMMA, 3 mm thick", "Integral", 2, O, "Fan pot 3.5, 5 (brief), 3.5, 2.2", "10, 15 (brief), 10, 8", 17.9, 16.8,
     "self_extinguished", 8, A, "", 1560, False, "medium",
     "26-min burn; flow briefly at 15 cm/s but flame was too strong so turned down; HCl 0 > 3.1, extinguished 8 cm/s",
     "Went out at 8 cm/s; burn time 26 min (stated)."),
    # ===== A.4 concluded, viewer p. 117 (printed 109)
    ("M19", 98, "7/23/14", "170m", "4-mm-thick, 2-cm, two-sided PMMA slab", "Integral", 2, O, "75, 105, 94, 75, 77, 79, 59, 61, 57, 55, 53 (4.4, 8.0, 6.6, 4.4, 4.6, 4.8, 2.5, 2.7, 2.2, 2.0, 1.8)", "10, 17, 14, 10, 7, 5", 19.0, 17.4,
     "quench", 5, A, 7, "", False, "medium", "Burned with decreasing flows until it went out on its own at 5 cm/s",
     "Went out during the flow decrease, at 5 cm/s."),
    ("M2", 17, "2/20/14", "224", "3-mm-thick PMMA one-sided, 2 cm wide", "Integral", 0, O, "", "20, 15, 13", 22.2, 21.2,
     "quench", 14, A, 15, "", False, "medium",
     "Ignite at 20 cm/s, turn down to 15 cm/s after spread away from igniter; seemed steady, so turned down to 13 cm/s; flame got very dim, so increased flow to 14 cm/s, but it self-extinguished",
     "Weakened after the turn-down to 13 cm/s and went out at 14 cm/s."),
    ("M20", 116, "8/1/14", "172m", "5-mm-thick PMMA, 2 cm wide", "Integral", 1, O, "67, 58", "10, 8", 18.0, 17.4,
     "self_extinguished", 8, A, 10, "", False, "medium",
     "Flame took some time to establish, initially only on bottom of fuel; ignition at 10 cm/s (left 8 min) then flow down to 8 cm/s (flame out after 3 more minutes)",
     "Went out 3 min after the flow was set to 8 cm/s."),
    ("M3", 82, "7/11/14", "226m", "2-cm-wide, 5-mm-thick, one-sided PMMA", "Integral", 2, O, "3.0, 3.1, 3.2, 6.4, 5.5, 5.4", "10, 20, 18", 20.8, 19.7,
     "extinguished_unclear", 18, A, "", "", False, "medium", "Extinguished at 18 cm/s; HCl 0.6 > 2.6", "Cause not stated."),
    ("M4", 113, "7/31/14", "171m", "5-mm-thick PMMA, 2 cm wide", "Integral", 1, O, "52, 47, 43", "5, 4, 3", 21.8, 19.8,
     "quench", 0.3, P, 0.55, "", False, "high",
     "Mild ignition at 10 cm/s; decreased flow down holding constant for 6 min at pot settings of 1.7, 1.0, and 0.55; finally extinguished by turning pot down to 0.3", ""),
    ("M5", 18, "2/20/14", "167", "3-mm-thick PMMA, two-sided, 2 cm thick", "Integral", 0, O, "", "20, 13, 10, 8, 5", 22.2, 19.0,
     "quench", 5, A, 8, "", False, "high",
     "Rick ignited while we were loss of signal and out of contact with ISS, unfortunately; ignition was ~3 min per his verbal call down when we came back; flame already burning ~1/3 of sample, both sides, long and sooty; more vapor jetting on bottom due to molten ball attached there, visible when lights on to change camera card; turned down to 10 cm/s, then further down in increments to 5 cm/s; extinguished at 5 cm/s after prolonged flashing; during soot cleaning, Rick noticed damage to front door corner by the switches; He sent pictures down for us to evaluate for damage; CO reading posttest was off-scale; came back during purge reading 500",
     ""),
    ("M6", 111, "7/31/14", "163m", "1-mm-thick PMMA, 2 cm wide", "Integral", 1, O, "68, 52, 47, 43, 42, 41", "10, 5, 3, 0", 21.8, 20.7,
     "keeps_burning", 0.36, P, 0.36, "", False, "high",
     "Aggressive ignition led to large flame initially; once flame settled down, we kept flow low and had two flow plateaus (pot 0.4 and 0.36); when flame reached end of sample it started backing up and spreading along the edges.",
     "Reached the end of the sample at pot 0.36."),
    ("M7", 81, "7/11/14", "177m", "1-cm-wide PMMA, 1 mm thick", "Integral", 2, O, "2.6, 1.3, 0.8, 0.7, 0.6, 0.5; 60, 49, 45, 44, 43, 42", "10, 6, 5, 4.5, 4, 3", 18.9, 18.4,
     "keeps_burning", 0.5, P, 0.5, 1080, False, "high", "18 min burn; burned entire sample; HCl 2.2 > 3.9", "Burn time 18 min (stated)."),
    ("M8", 79, "7/11/14", "178m", "1-cm-wide PMMA, 2 mm thick", "Integral", 2, O, "3.3, 1.6, 1.0, decrease", "10, 5 > 7, 5 decrease", 19.1, 18.2,
     "quench", 0.4, P, "", 1500, False, "high", "25-min burn; turned down flow to extinguish, went out at pot 0.4; HCl 0.4 > 4.6",
     "Burn time 25 min (stated)."),
    ("M9", 78, "7/11/14", "179m", "1-cm-wide PMMA, 3 mm thick", "Integral", 2, O, "3.3, 4.8; 66, 79", "10, 14", 18.0, 17.6,
     "self_extinguished", 14, A, "", 1020, False, "high",
     "Ignited at 10 cm/s, photographs every 5 s or so, turned up flow when flame looked weak; died after 15 min at 14 cm/s; 17-min burn; HCl 0 > 1.7",
     "Went out at a steady 14 cm/s. Burn time 17 min (stated)."),
]
PAGES = {
    "111 (printed 103)": {"B1", "B10", "B11", "B12", "B13", "B14", "B15", "B16", "B17"},
    "112 (printed 104)": {"B18", "B19", "B2", "B20", "B21", "B22", "B3", "B4", "B5", "B6", "B7", "B8", "B9"},
    "113 (printed 105)": {"F1", "F2", "F3", "F4"},
    "114 (printed 106)": {"P1", "P10", "P12", "P13a", "P13b", "P14", "P15", "P16", "P17", "P18", "P19", "P2", "P20", "P21a", "P21b"},
    "115 (printed 107)": {"P22a", "P22b", "P23", "P24", "P25", "P3a", "P3b", "P4", "P5", "P6", "P8", "P9"},
    "116 (printed 108)": {"M1", "M10", "M11", "M12", "M13", "M14", "M15", "M16", "M17", "M18"},
    "117 (printed 109)": {"M19", "M2", "M20", "M3", "M4", "M5", "M6", "M7", "M8", "M9"},
}
PI = {"B": ("Bhattacharjee", "A.1"), "F": ("Ferkul", "A.2"), "P": ("Fernandez-Pello", "A.3"), "M": ("Miller", "A.4")}


def page_of(tid):
    return next(p for p, ids in PAGES.items() if tid in ids)


def main():
    assert sum(len(v) for v in PAGES.values()) == len(R) == len({r[0] for r in R})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pi"] + F + ["source_doc", "source_page"])
        for r in R:
            assert len(r) == len(F), (r[0], len(r))
            pi, table = PI[r[0][0]]
            w.writerow([pi] + list(r) + [f"{DOC} (Table {table})", page_of(r[0])])
    print(len(R), "rows ->", OUT)
    for k in PI.values():
        print(f"  {k[0]:16s}", dict(collections.Counter(r[12] or "(blank)" for r in R if PI[r[0][0]] == k)))


if __name__ == "__main__":
    main()
