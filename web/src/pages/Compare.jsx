// Compare up to three investigations side by side: what they burned, in which air and flow, which hardware,
// what they found. Rows where the picked investigations differ are marked. The choice lives in the address
// (#/compare?ids=PSI-25,PSI-26), so a comparison can be shared.
import { useEffect, useState } from "react";
import { PageHead } from "../components/InvCard.jsx";
import { apiUrl, get } from "../lib/api.js";
import { conditionRows } from "../lib/conditions.js";
import { fmt } from "../lib/habitats.js";

const MAX = 3;
const FUEL = { solid: "Solid materials", droplet: "Liquid droplets", gas: "Gas flames", smoke: "Smoke & detection", ground: "Ground study" };
const JOB = { prevention: "Prevention", detection: "Detection", suppression: "Suppression" };

function readIds() {
  const q = location.hash.split("?")[1] || "";
  return (new URLSearchParams(q).get("ids") || "").split(",").filter(Boolean).slice(0, MAX);
}

const cite = (f) => f && (f.url ? <a href={f.url} target="_blank" rel="noreferrer"><cite>{f.cite}</cite></a> : <cite>{f.cite}</cite>);

/** The compared rows: [label, card => {text, node?}]. text is what "same / differs" is judged on. */
const ROWS = [
  ["Fuel family", (c) => ({ text: FUEL[c.fuel_type] || c.fuel_type || "–" })],
  // Judged on the hardware group (MSG, CIR + MDCA…): the raw PSI wording varies ("Glovebox" vs "Glovebox (MSG)").
  ["Hardware", (c) => ({ text: c.hardware_group || c.hardware_raw || "–", node: c.hardware_raw || c.hardware_group || "–" })],
  ["Flown on", (c) => ({ text: c.in_space === false ? "Ground study" : c.flight_program || "–" })],
  ["Tests", (c) => ({ text: c.tests?.count == null ? "no test table" : fmt(c.tests.count) })],
  ["In Moon-base air", (c) => ({ text: c.tests?.count == null ? "–" : `${fmt(c.tests.lunar_air || 0)} tests` })],
  ...["Fuels and samples", "Oxygen (cabin air)", "Oxygen from the burner", "Pressure", "Airflow", "Gas mixed with the oxygen"].map((label) => [
    label, (c) => {
      const r = conditionRows(c, { maxFuels: 4 }).find((x) => x[0] === label || (label === "Oxygen (cabin air)" && x[0] === "Oxygen"));
      return { text: r ? r[1] : "–", node: r ? <>{r[1]}{r[2] && <small className="cond-note">{r[2]}{r[3] ? ` · ${r[3]}` : ""}</small>}</> : "–" };
    },
  ]),
  ["Fire-safety job", (c) => ({ text: (c.fire_safety?.jobs || []).map((j) => JOB[j] || j).join(", ") || "–" })],
  ["Key finding", (c) => {
    const f = c.findings?.[0];
    return { text: f?.text || "–", node: f ? <>{f.text}{cite(f)}</> : "No sourced finding yet." };
  }],
  ["Limitation", (c) => {
    const f = c.limitations?.[0];
    return { text: f?.text || "–", node: f ? <>{f.text}{cite(f)}</> : "–" };
  }],
  ["Data", (c) => ({
    text: c.id,
    node: c.tests?.count > 0
      ? <a href={apiUrl(`/tests.csv?psi_id=${encodeURIComponent(c.id)}`)} download>↓ CSV, {fmt(c.tests.count)} rows</a>
      : "–",
  })],
];

export default function Compare({ onOpen }) {
  const [ids, setIds] = useState(readIds);
  const [list, setList] = useState(null);
  const [cards, setCards] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => { get("/investigations").then(setList).catch((e) => setError(e.message)); }, []);
  useEffect(() => {
    const on = () => setIds(readIds());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  useEffect(() => {
    history.replaceState(null, "", "#/compare" + (ids.length ? `?ids=${ids.join(",")}` : ""));
    ids.filter((id) => !cards[id]).forEach((id) =>
      get(`/investigations/${id}`).then((c) => setCards((m) => ({ ...m, [id]: c }))).catch((e) => setError(e.message)));
  }, [ids]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id) => setIds((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : cur.length < MAX ? [...cur, id] : cur));
  const picked = ids.map((id) => cards[id]).filter(Boolean);
  const nasa = (list || []).filter((inv) => inv.origin !== "upload");

  return (
    <div className="page">
      <PageHead title="Compare experiments"
                sub={`Pick up to ${MAX} investigations to see how their tests were run and what they found, side by side. Rows where they differ are highlighted.`}>
        {error && <p className="cav">Could not load: {error}</p>}
        {!list && !error && <p className="loading">Loading…</p>}
        <div className="chips" role="group" aria-label="Investigations to compare">
          {nasa.map((inv) => {
            const on = ids.includes(inv.id);
            return <button key={inv.id} className="chip" type="button" aria-pressed={on} disabled={!on && ids.length >= MAX}
                           onClick={() => toggle(inv.id)}>{inv.name}</button>;
          })}
        </div>
        {ids.length > 0 && (
          <div className="sh-right" style={{ margin: "4px 0 16px" }}>
            <span className="tool">{ids.length} of {MAX} picked</span>
            <button type="button" className="btn2" onClick={() => setIds([])}>Clear</button>
          </div>
        )}
        {!ids.length && <p className="loading">Pick two or three investigations above. Good pairs to start: BASS vs BASS-II (solid materials, same flow duct), FLEX vs CFI (droplets in the same apparatus), SAME vs SAME-R (smoke).</p>}
        {picked.length > 0 && (
          <div className="cmp-wrap">
            <table className="table cmp">
              <thead>
                <tr>
                  <th scope="col"><span className="sr-only">Attribute</span></th>
                  {picked.map((c) => (
                    <th key={c.id} scope="col"><button type="button" onClick={() => onOpen(c.id)}>{c.name}</button><small>{c.id} · details →</small></th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map(([label, cell]) => {
                  const cells = picked.map((c) => cell(c));
                  const differs = picked.length > 1 && label !== "Data" && new Set(cells.map((x) => x.text)).size > 1;
                  const same = picked.length > 1 && label !== "Data" && !differs;
                  return (
                    <tr key={label} className={differs ? "diff" : ""}>
                      <th scope="row">{label}{(differs || same) && <span className="cmp-same">{differs ? "differs" : "same"}</span>}</th>
                      {cells.map((x, i) => <td key={picked[i].id}>{x.node ?? x.text}</td>)}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <p className="cav" style={{ marginTop: 16 }}>Every number comes from the NASA PSI test tables and reports; findings link to their page. All tests ran in microgravity.</p>
      </PageHead>
    </div>
  );
}
