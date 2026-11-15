// Test conditions of one card (card.conditions, built by scripts/build_cards.py), as display rows.
// Shared by the details drawer and the Compare page, so both say exactly the same thing.
import { fmt } from "./habitats.js";

const KPA_PER_PSI = 6.894757;
const PSI_FILE_URL = "https://psi.nasa.gov/geode-py/ws/studies/{psi}/download?file={file}";

const num = (v) => (v == null ? "" : Number.isInteger(v) ? String(v) : String(+v.toFixed(2)));

/** "15.9–22.7" or "22.2" for a {min, max} range; null if missing. */
function span(r, unit) {
  if (!r || r.min == null) return null;
  return (r.min === r.max ? num(r.min) : `${num(r.min)}–${num(r.max)}`) + (unit ? ` ${unit}` : "");
}

/** "varied" when the tests used several values, "held fixed" when all used one, null if unknown. */
const varied = (r) => (!r || r.min == null ? null : r.min === r.max ? "held fixed" : "varied");

/** The rows of the conditions table: [label, value, varied-tag, note]. Empty when the card has no test table. */
export function conditionRows(card, { maxFuels = 6 } = {}) {
  const c = card?.conditions;
  if (!c || c.available === false) return [];
  const rows = [];

  const fuels = c.fuels || [];
  if (fuels.length) {
    const shown = fuels.slice(0, maxFuels).map((f) => `${f.name}${f.tests ? ` (${fmt(f.tests)})` : ""}`).join(", ");
    rows.push(["Fuels and samples", shown + (fuels.length > maxFuels ? `, +${fuels.length - maxFuels} more` : ""),
      fuels.length > 1 ? "varied" : "held fixed", null]);
  }

  const o2 = c.o2_pct || {};
  if (o2.chamber) rows.push(["Oxygen (cabin air)", span(o2.chamber, "%"), varied(o2.chamber), o2.chamber.assumed ? "assumed, not measured" : null]);
  if (o2.burner_stream) rows.push(["Oxygen from the burner", span(o2.burner_stream, "%"), varied(o2.burner_stream), "blown out of the burner: not cabin air"]);
  if (!o2.chamber && !o2.burner_stream) rows.push(["Oxygen", "not recorded", null, null]);

  const p = c.pressure_kpa;
  rows.push(["Pressure", p ? `${span(p, "kPa")} (${span({ min: p.min / KPA_PER_PSI, max: p.max / KPA_PER_PSI }, "psi")})` : "not recorded",
    varied(p), p?.assumed ? "assumed, not measured" : null]);
  rows.push(["Airflow", c.flow_cm_s ? span(c.flow_cm_s, "cm/s") : "not recorded", varied(c.flow_cm_s), null]);
  if (c.diluents?.length) rows.push(["Gas mixed with the oxygen", c.diluents.join(", "), c.diluents.length > 1 ? "varied" : "held fixed", null]);
  if (c.gravity?.length) rows.push(["Gravity", c.gravity.join(", "), null, null]);
  return rows;
}

/** The NASA PSI source tables of a card: [{name, url}]. */
export function sourceTables(card) {
  return (card?.tests?.tables || []).filter((t) => t.source_file).map((t) => {
    const name = t.source_file.split("/").pop();
    return { name, url: PSI_FILE_URL.replace("{psi}", card.id).replace("{file}", encodeURIComponent(name)) };
  });
}
