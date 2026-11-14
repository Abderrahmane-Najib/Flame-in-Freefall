// The four hero KPIs per habitat, built from API data. Each: [value, label, {explorer, student, researcher}, cite, url, warn].
import { fmt } from "./habitats.js";

const PSI_HOME = "https://psi.nasa.gov/physci/repo/data/investigations";
const T = (explorer, student, researcher) => ({ explorer, student, researcher });
const names = (list) => list.map((r) => r.name).join(", ") || "none";

export function moonKpis({ coverage, ranking, nearTests }) {
  const c = coverage?.counts || {};
  const measured = (ranking?.investigations || []).filter((r) => r.measured);
  const withResults = measured.reduce((s, r) => s + (r.measured_with_results || 0), 0);
  const nearNames = [...new Set((coverage?.points || []).filter((p) => p.zone === "near_lunar").map((p) => p.name))];

  const rows = nearTests?.rows || [];
  const ends = {};
  rows.forEach((r) => { const e = r.results?.test_end; if (e) ends[e] = (ends[e] || 0) + 1; });
  const selfOut = ends.extinction || 0;
  const END = { disruption: "broke apart", completion: "burned all their fuel", extinction: "went out" };
  const endText = Object.entries(ends).map(([k, v]) => `${v} ${END[k] || k}`).join(", ");
  const nearPsi = rows[0]?.psi_id;

  return [
    [fmt(c.lunar_tests), "fire tests in Moon-base air",
      T(`Only ${fmt(c.lunar_tests)} of NASA's fire tests used air like a Moon base's.`,
        `All by ${names(measured)}: 30% oxygen or more, at 70.3 kPa or less (about 70% of sea-level pressure).`,
        `Both oxygen and pressure recorded for each test; ${withResults} of them have a recorded result.`),
      measured.length ? `NASA PSI · ${measured.map((r) => r.name).join(", ")}` : "NASA PSI test tables", measured[0]?.url || PSI_HOME],
    [fmt(c.near_lunar_tests), "tests just outside it",
      T(`${fmt(c.near_lunar_tests)} more tests came very close.`,
        `${nearNames.join(", ")}: same oxygen, but pressure slightly above the Moon-base limit (70.3–72.5 kPa).`,
        "Shown apart and never counted as Moon-base air."),
      nearPsi ? `NASA PSI · ${nearNames.join(", ")}` : "NASA PSI test tables", Object.values(nearTests?.tables || {})[0] || PSI_HOME],
    [rows.length ? `${selfOut} of ${rows.length}` : "–", "went out by themselves",
      T(selfOut === 0 ? "None of those fires put themselves out." : `${selfOut} of those fires put themselves out.`,
        `How they ended: ${endText || "not recorded"}.`,
        `From the "test end" recorded by NASA for each of the ${rows.length} tests.`),
      nearPsi ? `NASA PSI test table · ${nearNames.join(", ")}` : "NASA PSI test tables", Object.values(nearTests?.tables || {})[0], true],
    ["0", "tests at Moon gravity",
      T("Nobody has tested fire at Moon gravity yet.", "Every test ran in microgravity (ISS, Cygnus).",
        "No partial-gravity data in PSI; future LUCI and FM2 experiments."),
      "PSI repository", "https://psi.nasa.gov/"],
  ];
}

export function issKpis({ habitat, ranking, pmma }) {
  const inv = ranking?.investigations || [];
  const measured = inv.filter((r) => r.measured);
  const total = measured.reduce((s, r) => s + r.measured, 0);
  const noted = inv.filter((r) => !r.measured && r.from_note);
  const box = habitat?.match || {};
  const refs = pmma?.references || [];
  const micro = refs.find((r) => r.o2_pct === 13.5);
  const earth = refs.find((r) => r.o2_pct === 15.4);
  const range = (v) => (v ? `${v[0]}–${v[1]}` : "?");

  return [
    [fmt(total), "fire tests in station-like air",
      T(`${fmt(total)} of NASA's fire tests were run in air like the space station's.`,
        `Air with ${range(box.o2_pct)}% oxygen at ${range(box.pressure_kpa)} kPa (about sea-level pressure), as recorded for each test.`,
        `Tests per experiment: ${measured.map((r) => `${r.name} ${r.measured}`).join(", ")}.`),
      "NASA PSI test tables", PSI_HOME],
    [String(measured.length), "experiments tested in this air",
      T(`${measured.length} experiments lit fires in this air: ${names(measured)}.`,
        `${names(measured)}.` + (noted.length ? ` ${names(noted)} probably did too, but NASA gives their air only in reports, not test by test.` : ""),
        `Counted only when both oxygen and pressure were recorded for the test.` + (noted.length ? ` Not counted: ${names(noted)} (air stated in reports only).` : "")),
      "NASA PSI test tables", PSI_HOME],
    ["13.5%", "lowest O₂ plastic burns in space",
      T("In space, plastic keeps burning with less oxygen.", "Acrylic (PMMA) rods, microgravity.",
        micro?.label || "BASS-II Eq. 6.1 minimum."),
      micro?.cite || "BASS-II Summary Report, p. 84", micro?.url],
    ["15.4%", "the same limit on Earth",
      T("On Earth it needs more oxygen to keep burning.", "Upward flame spread, normal gravity.",
        earth?.label || "With an extra 4 cm/s forced flow."),
      earth?.cite || "BASS-II Summary Report, p. 84", earth?.url],
  ];
}
