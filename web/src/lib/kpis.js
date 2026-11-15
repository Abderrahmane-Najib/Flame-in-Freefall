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
      T(`Only ${fmt(c.lunar_tests)} NASA fire tests used Moon-base air.`,
        `All by ${names(measured)}: ≥30% O₂ at ≤70.3 kPa.`,
        `O₂ and pressure recorded per test; ${withResults} with results.`),
      measured.length ? `NASA PSI · ${measured.map((r) => r.name).join(", ")}` : "NASA PSI test tables", measured[0]?.url || PSI_HOME],
    [fmt(c.near_lunar_tests), "tests just outside it",
      T(`${fmt(c.near_lunar_tests)} more came very close.`,
        `${nearNames.join(", ")}: just above 70.3 kPa.`,
        "Kept apart, never counted as Moon-base air."),
      nearPsi ? `NASA PSI · ${nearNames.join(", ")}` : "NASA PSI test tables", Object.values(nearTests?.tables || {})[0] || PSI_HOME],
    [rows.length ? `${selfOut} of ${rows.length}` : "–", "went out by themselves",
      T(selfOut === 0 ? "None put themselves out." : `${selfOut} put themselves out.`,
        `${endText || "Not recorded"}.`,
        `NASA's recorded test end, ${rows.length} tests.`),
      nearPsi ? `NASA PSI test table · ${nearNames.join(", ")}` : "NASA PSI test tables", Object.values(nearTests?.tables || {})[0], true],
    ["0", "tests at Moon gravity",
      T("Never tested at Moon gravity.", "All tests ran in microgravity.", "No partial-gravity data in PSI."),
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
      T(`${fmt(total)} NASA fire tests in air like the station's.`,
        `${range(box.o2_pct)}% O₂ at ${range(box.pressure_kpa)} kPa.`,
        `${measured.map((r) => `${r.name} ${r.measured}`).join(", ")}.`),
      "NASA PSI test tables", PSI_HOME],
    [String(measured.length), "experiments tested in this air",
      T(`${measured.length} experiments lit fires in this air.`,
        `${names(measured)}.`,
        noted.length ? `Not counted: ${names(noted)} (air in reports only).` : "O₂ and pressure recorded per test."),
      "NASA PSI test tables", PSI_HOME],
    ["13.5%", "lowest O₂ plastic burns in space",
      T("In space, plastic burns with less oxygen.", "Acrylic rods, microgravity.",
        micro?.label || "BASS-II Eq. 6.1 minimum."),
      micro?.cite || "BASS-II Summary Report, p. 84", micro?.url],
    ["15.4%", "the same limit on Earth",
      T("On Earth it needs more oxygen.", "Upward spread, Earth gravity.",
        earth?.label || "With an extra 4 cm/s forced flow."),
      earth?.cite || "BASS-II Summary Report, p. 84", earth?.url],
  ];
}
