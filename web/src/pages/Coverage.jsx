// Full coverage map (GET /coverage): every test row with chamber O2 and pressure, the habitat boxes and the
// near-lunar band. Colour + shape = fuel family; hover for the row, click to open its investigation.
import { useEffect, useMemo, useRef, useState } from "react";
import { PageHead } from "../components/InvCard.jsx";
import Explain from "../components/Explain.jsx";
import { get } from "../lib/api.js";
import { FUEL_SERIES, Mark } from "../lib/series.jsx";
import { fmt } from "../lib/habitats.js";

const W = 820, H = 470, M = { l: 48, r: 16, t: 14, b: 40 };
const P = [40, 520], O2 = [10, 42];
const sx = (p) => M.l + (Math.log(Math.min(Math.max(p, P[0]), P[1]) / P[0]) / Math.log(P[1] / P[0])) * (W - M.l - M.r);
const sy = (o) => M.t + ((O2[1] - Math.min(Math.max(o, O2[0]), O2[1])) / (O2[1] - O2[0])) * (H - M.t - M.b);
const X_TICKS = [50, 70.3, 101.3, 200, 300, 500];
const Y_TICKS = [10, 15, 21, 25, 30, 35, 40];
const SERIES = Object.fromEntries(FUEL_SERIES.map((s) => [s.id, s]));

function zoneRect(o2, p) {
  const x0 = sx(Math.max(p[0], P[0])), x1 = sx(p[1]), y0 = sy(Math.min(o2[1], O2[1])), y1 = sy(o2[0]);
  return { x: x0, y: y0, width: Math.max(x1 - x0, 2), height: y1 - y0 };
}

export default function Coverage({ onOpen, level }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [off, setOff] = useState({});
  const [hover, setHover] = useState(null);
  const [focus, setFocus] = useState(null); // the part the "Explain it simply" step points at
  const svg = useRef(null);

  useEffect(() => { get("/coverage").then(setData).catch((e) => setError(e.message)); }, []);

  const points = useMemo(() => (data?.points || [])
    .filter((p) => !off[p.fuel_type])
    .map((p) => ({ ...p, x: sx(p.pressure_kpa), y: sy(p.o2_pct) })), [data, off]);

  const byInv = useMemo(() => {
    const t = {};
    const iss = data?.zones.habitats.find((h) => h.id === "iss")?.box;
    for (const p of data?.points || []) {
      const r = (t[p.psi_id] ||= { psi_id: p.psi_id, name: p.name, rows: 0, lunar: 0, near: 0, iss: 0 });
      r.rows++;
      if (p.zone === "lunar") r.lunar++;
      if (p.zone === "near_lunar") r.near++;
      if (iss && p.o2_pct >= iss.o2_pct[0] && p.o2_pct <= iss.o2_pct[1] && p.pressure_kpa >= iss.pressure_kpa[0] && p.pressure_kpa <= iss.pressure_kpa[1]) r.iss++;
    }
    return Object.values(t).sort((a, b) => b.lunar - a.lunar || b.near - a.near || b.rows - a.rows);
  }, [data]);

  function move(e) {
    const r = svg.current.getBoundingClientRect();
    const mx = ((e.clientX - r.left) / r.width) * W, my = ((e.clientY - r.top) / r.height) * H;
    let best = null, bd = 144; // within 12 px
    for (const p of points) {
      const d = (p.x - mx) ** 2 + (p.y - my) ** 2;
      if (d < bd) { bd = d; best = p; }
    }
    setHover(best && { p: best, left: (best.x / W) * r.width, top: (best.y / H) * r.height });
  }

  const moon = data?.zones.habitats.find((h) => h.id === "moon_base_rover")?.box;
  const iss = data?.zones.habitats.find((h) => h.id === "iss")?.box;
  const near = data?.zones.near_lunar;
  const c = data?.counts;

  return (
    <div className="page">
      <PageHead title="Coverage map: oxygen × pressure"
                sub="Every NASA test row with both chamber oxygen and pressure measured. The boxes are the habitats' air: see how few fires were tested in Moon-habitat air."
                right={<Explain level={level} onStep={setFocus} steps={[
                  { title: "Every dot is a fire", focus: "dots", text: <>Each dot is <strong>one fire NASA lit in space</strong>. The shape and colour tell you what burned: a gas, a liquid droplet or a solid material. Hover a dot to see which experiment it came from.</> },
                  { title: "Reading the map", text: <>Going <strong>up</strong> means more oxygen in the air (normal air has 21%). Going <strong>right</strong> means thicker air, measured as pressure: 101 kPa is the air at sea level.</> },
                  { title: "Space-station air", focus: "iss", text: <>The blue box is <strong>space-station air</strong>, almost like Earth's. That's where most of NASA's fires were tested, so we know it well.</> },
                  { title: "Moon-habitat air", focus: "moon", text: <>The green box is the air planned for a <strong>Moon habitat</strong>: thinner, but richer in oxygen. Very few dots land in it{data ? <>: only <strong>{data.counts.lunar_tests} fires</strong></> : ""}. The dashed strip next to it is <em>almost</em> Moon-habitat air, kept apart because "almost" is not the same.</> },
                  { title: "The big gap", focus: "moon", text: <>So the map shows what is missing: we know a lot about fire in station air, and <strong>very little about fire in Moon-habitat air</strong>. That's the gap future experiments need to fill.</> },
                ]} />}>
        {error && <p className="cav">Could not load: {error}</p>}
        <div className="cols">
          <div className="panel space">
            <div className="chips" role="group" aria-label="Fuel families shown">
              {FUEL_SERIES.map((s) => (
                <button key={s.id} className="chip" type="button" aria-pressed={!off[s.id]} onClick={() => setOff({ ...off, [s.id]: !off[s.id] })}>
                  <svg width="12" height="12"><Mark shape={s.shape} x={6} y={6} r={4} fill={s.color} /></svg>{s.label}
                </button>
              ))}
            </div>
            <div className="chart-wrap">
              <svg ref={svg} className="chart" viewBox={`0 0 ${W} ${H}`} onMouseMove={move} onMouseLeave={() => setHover(null)}
                   onClick={() => hover && onOpen(hover.p.psi_id)} style={{ cursor: hover ? "pointer" : "default" }}
                   role="img" aria-label="Scatter plot of test rows: pressure in kPa (log scale) against chamber oxygen in percent">
                <defs>
                  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="2.2" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
                  </filter>
                </defs>
                <g className="grid">
                  {Y_TICKS.map((t) => <line key={t} x1={M.l} x2={W - M.r} y1={sy(t)} y2={sy(t)} />)}
                  {X_TICKS.map((t) => <line key={t} y1={M.t} y2={H - M.b} x1={sx(t)} x2={sx(t)} />)}
                </g>
                {moon && <g className={focus === "moon" ? "pulse focus-glow" : undefined}><rect {...zoneRect(moon.o2_pct, moon.pressure_kpa)} fill="color-mix(in srgb,var(--ember) 10%,transparent)" stroke="var(--ember)" strokeWidth="1.5" rx="4" />
                  <text className="lbl" x={sx(moon.pressure_kpa[0] < P[0] ? P[0] : moon.pressure_kpa[0]) + 6} y={sy(41) + 4}>☾ Moon habitat / rover air</text></g>}
                {near && <rect {...zoneRect([near.o2_pct[0], O2[1]], near.pressure_kpa)} fill="none" stroke="var(--cyan)" strokeDasharray="4 3" strokeWidth="1.5" />}
                {near && <text className="lbl" x={sx(near.pressure_kpa[1]) + 5} y={sy(31.5)}>near-lunar</text>}
                {iss && <g className={focus === "iss" ? "pulse" : undefined} style={focus === "iss" ? { filter: "drop-shadow(0 0 6px var(--lime))" } : undefined}><rect {...zoneRect(iss.o2_pct, iss.pressure_kpa)} fill="color-mix(in srgb,var(--lime) 10%,transparent)" stroke="var(--lime)" strokeWidth="1.5" rx="4" />
                  <text className="lbl" x={sx(iss.pressure_kpa[1]) + 5} y={sy(iss.o2_pct[1]) + 10}>✦ ISS air</text></g>}
                <g filter="url(#glow)" className={focus === "dots" ? "pulse" : undefined}>
                  {points.map((p, i) => {
                    const s = SERIES[p.fuel_type];
                    return <Mark key={i} shape={s?.shape || "circle"} x={p.x} y={p.y} r={3} fill={s?.color || "var(--faint)"} fillOpacity={0.75}
                                 stroke="rgba(3,5,13,.6)" strokeWidth={0.6} />;
                  })}
                </g>
                {hover && <Mark shape={SERIES[hover.p.fuel_type]?.shape || "circle"} x={hover.p.x} y={hover.p.y} r={5.5}
                                fill={SERIES[hover.p.fuel_type]?.color || "var(--faint)"} stroke="var(--card)" strokeWidth={2} />}
                <g className="axis">
                  {Y_TICKS.map((t) => <text key={t} x={M.l - 8} y={sy(t) + 3.5} textAnchor="end">{t}%</text>)}
                  {X_TICKS.map((t) => <text key={t} x={sx(t)} y={H - M.b + 16} textAnchor="middle">{t}</text>)}
                  <text x={W - M.r} y={H - 6} textAnchor="end">pressure, kPa (log scale) →</text>
                  <text x={M.l} y={M.t - 2}>chamber O₂</text>
                </g>
              </svg>
              {hover && (
                <div className="tip" style={{ left: hover.left, top: hover.top }}>
                  <b>{hover.p.name} · {hover.p.psi_id}</b>
                  {hover.p.fuel && <div>{hover.p.fuel}</div>}
                  <span>{hover.p.o2_pct}% O₂ · {hover.p.pressure_kpa} kPa{hover.p.assumed ? " · assumed air" : ""}</span><br />
                  <span>{hover.p.zone === "lunar" ? "lunar air" : hover.p.zone === "near_lunar" ? "near-lunar (not lunar)" : ""} {hover.p.table}, row {hover.p.row}</span>
                </div>
              )}
            </div>
          </div>
          <aside className="panel space">
            <h3>What the map holds</h3>
            {c ? <table className="table"><tbody>
              <tr><td>Rows drawn</td><td className="n">{fmt(c.points)}</td></tr>
              <tr><td>Fires in Moon-habitat air</td><td className="n">{fmt(c.lunar_tests)}</td></tr>
              <tr><td>Fires just outside it (near-lunar)</td><td className="n">{fmt(c.near_lunar_tests)}</td></tr>
              <tr><td>Burner-stream rows left out</td><td className="n">{fmt(c.burner_stream_rows)}</td></tr>
              <tr><td>Rows without a single O₂ / pressure</td><td className="n">{fmt(c.rows_without_single_value)}</td></tr>
            </tbody></table> : <p className="loading">Loading…</p>}
            <div style={{ marginTop: 14 }}>{data?.notes.map((n) => <p key={n} className="cav" style={{ border: 0, paddingTop: 6 }}>{n}</p>)}</div>
          </aside>
        </div>
      </PageHead>
      <PageHead title="By experiment" sub="The same rows as a table: which experiments tested which air. Click a row to open it.">
        <div className="panel">
          <table className="table">
            <thead><tr><th>Experiment</th><th className="n">Rows on the map</th><th className="n">…in Moon-habitat air</th><th className="n">…near-lunar</th><th className="n">…in ISS air</th></tr></thead>
            <tbody>{byInv.map((r) => (
              <tr key={r.psi_id} onClick={() => onOpen(r.psi_id)} style={{ cursor: "pointer" }}>
                <td><b>{r.name}</b> <span className="mono" style={{ color: "var(--faint)" }}>{r.psi_id}</span></td>
                <td className="n">{fmt(r.rows)}</td><td className="n">{fmt(r.lunar)}</td><td className="n">{fmt(r.near)}</td><td className="n">{fmt(r.iss)}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
      </PageHead>
    </div>
  );
}
