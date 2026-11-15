// P10 PMMA predictor (GET /predict/pmma): NASA's fitted flammability boundary for acrylic rods in microgravity
// (BASS-II Eq. 6.1). Sliders place a flow and an oxygen level against the curve.
import { useEffect, useMemo, useRef, useState } from "react";
import { PageHead } from "../components/InvCard.jsx";
import Explain from "../components/Explain.jsx";
import { fresh } from "../lib/api.js";

const RODS = [6.35, 9.53, 12.7];
const RODS_IN = { 6.35: '1/4"', 9.53: '3/8"', 12.7: '1/2"' };
const PRESETS = [["ISS air", 21], ["Moon habitat", 34]];
const W = 760, H = 420, M = { l: 48, r: 110, t: 16, b: 40 };
const Y = [12, 36];
const FLOW = [0.5, 60];                        // slider range, cm/s (log)
const toFlow = (v) => +(FLOW[0] * (FLOW[1] / FLOW[0]) ** (v / 1000)).toFixed(2);
const toSlider = (f) => Math.round((Math.log(f / FLOW[0]) / Math.log(FLOW[1] / FLOW[0])) * 1000);

export default function Predict({ level }) {
  const [rod, setRod] = useState(9.53);
  const [flow, setFlow] = useState(5);
  const [o2, setO2] = useState(21);
  const [res, setRes] = useState(null);
  const [error, setError] = useState(null);
  const [hover, setHover] = useState(null);
  const [focus, setFocus] = useState(null); // the part of the chart the "Explain it simply" step points at
  const svg = useRef(null);

  useEffect(() => {
    const t = setTimeout(() => {
      fresh(`/predict/pmma?rod_diameter_mm=${rod}&flow_cm_s=${flow}&o2_pct=${o2}`)
        .then((r) => { setRes(r); setError(null); }).catch((e) => setError(e.message));
    }, 120);
    return () => clearTimeout(t);
  }, [rod, flow, o2]);

  const curve = useMemo(() => (res?.curve || []).filter((c) => c.flow_cm_s > 0), [res]);
  const X = curve.length ? [Math.max(curve[0].flow_cm_s, 0.05), curve[curve.length - 1].flow_cm_s] : [0.05, 100];
  const sx = (f) => M.l + (Math.log(f / X[0]) / Math.log(X[1] / X[0])) * (W - M.l - M.r);
  const sy = (o) => M.t + ((Y[1] - Math.min(Math.max(o, Y[0]), Y[1])) / (Y[1] - Y[0])) * (H - M.t - M.b);
  const line = curve.map((c, i) => `${i ? "L" : "M"}${sx(c.flow_cm_s).toFixed(1)},${sy(c.o2_min_pct).toFixed(1)}`).join("");
  const below = curve.length ? `${line}L${sx(X[1])},${sy(Y[0])}L${sx(X[0])},${sy(Y[0])}Z` : "";
  const xTicks = [0.1, 0.3, 1, 3, 10, 30, 100].filter((t) => t >= X[0] && t <= X[1]);
  const p = res?.point;
  const burns = p && p.margin_pct > 0;
  const refs = res?.references || [];

  function move(e) {
    if (!curve.length) return;
    const r = svg.current.getBoundingClientRect();
    const mx = ((e.clientX - r.left) / r.width) * W;
    const c = curve.reduce((a, b) => (Math.abs(sx(b.flow_cm_s) - mx) < Math.abs(sx(a.flow_cm_s) - mx) ? b : a));
    setHover({ c, left: (sx(c.flow_cm_s) / W) * r.width, top: (sy(c.o2_min_pct) / H) * r.height });
  }

  return (
    <div className="page">
      <PageHead title="Predict: will an acrylic rod keep burning?"
                sub="NASA's own fitted boundary from the BASS-II rods in microgravity (Eq. 6.1). Below the curve the flame cannot survive: on the left it loses too much heat, on the right the flow blows it off."
                right={<Explain level={level} onStep={setFocus} steps={[
                  { title: "Meet the burning stick", text: <>Picture a stick of <strong>acrylic</strong> (the clear plastic of a plexiglass window) on fire inside a spacecraft. A flame needs two things: enough <strong>oxygen</strong>, and a little <strong>moving air</strong> to bring the oxygen in. In space hot air doesn't rise, so the only moving air is what the fans blow.</> },
                  { title: "The green line", focus: "curve", text: <>The green line is the <strong>least oxygen</strong> the flame needs to survive, for each airflow. <strong>Above</strong> the line it keeps burning. <strong>Below</strong> it, it dies.</> },
                  { title: "Too little or too much air", focus: "below", text: <>The grey area is where the flame can't survive. On the <strong>left</strong> the air barely moves, so the flame starves and cools down. On the <strong>right</strong> the air rushes so fast it blows the flame out, like a candle in the wind. The lowest point, a gentle breeze of about 10 cm/s, is where fire survives with the least oxygen.</> },
                  { title: "Space, Earth and the Moon", focus: "refs", text: <>The dashed lines compare: <strong>13.5%</strong> is the least oxygen an acrylic rod burned with in space, <strong>15.4%</strong> the limit measured on Earth, <strong>21%</strong> is normal air, and a Moon habitat may have <strong>30% or more</strong>. At 30% the rod can keep burning at every airflow on this chart.</> },
                  { title: "Your setting", focus: "you", text: p ? <>At <strong>{p.flow_cm_s} cm/s</strong> of airflow the rod needs at least <strong>{p.o2_min_pct}%</strong> oxygen. You chose {p.o2_pct}%, so {burns
                    ? <>it <strong>can keep burning</strong>, with {p.margin_pct} points to spare.</>
                    : <>it <strong>goes out</strong>: {Math.abs(p.margin_pct)} points short.</>} Move the sliders and watch the dot.</> : "Move the sliders on the right to place your own rod."},
                ]} />}>
        <div className="cols">
          <div className="panel">
            <div className="chart-wrap">
              <svg ref={svg} className="chart" viewBox={`0 0 ${W} ${H}`} onMouseMove={move} onMouseLeave={() => setHover(null)}
                   role="img" aria-label="Minimum oxygen for a burning PMMA rod against airflow speed">
                <g className="grid">
                  {[12, 15, 18, 21, 24, 27, 30, 33, 36].map((t) => <line key={t} x1={M.l} x2={W - M.r} y1={sy(t)} y2={sy(t)} />)}
                  {xTicks.map((t) => <line key={t} y1={M.t} y2={H - M.b} x1={sx(t)} x2={sx(t)} />)}
                </g>
                {below && <path d={below} className={focus === "below" ? "pulse" : undefined} fill={`color-mix(in srgb,var(--faint) ${focus === "below" ? 40 : 16}%,transparent)`} />}
                {res?.moon_range && <rect x={M.l} width={W - M.l - M.r} y={sy(res.moon_range.o2_min_pct[1])}
                  height={sy(res.moon_range.o2_min_pct[0]) - sy(res.moon_range.o2_min_pct[1])}
                  fill="color-mix(in srgb,var(--cyan) 12%,transparent)" />}
                {refs.map((r) => (
                  <g key={r.o2_pct} className={focus === "refs" ? "pulse" : undefined}>
                    <line className="ref" x1={M.l} x2={W - M.r} y1={sy(r.o2_pct)} y2={sy(r.o2_pct)} />
                    <text className="lbl" x={W - M.r + 6} y={sy(r.o2_pct) + 4}>{r.o2_pct}% {{ 13.5: "µg lowest", 15.4: "Earth limit", 21: "ISS air", 30: "Moon habitat" }[r.o2_pct] || ""}</text>
                  </g>
                ))}
                <path d={line} fill="none" stroke="var(--ember)" strokeWidth={focus === "curve" ? 4 : 2} className={focus === "curve" ? "focus-glow" : undefined} />
                {p && <g>
                  <line x1={sx(Math.min(Math.max(p.flow_cm_s, X[0]), X[1]))} x2={sx(Math.min(Math.max(p.flow_cm_s, X[0]), X[1]))} y1={sy(p.o2_pct)} y2={sy(p.o2_min_pct)}
                        stroke="var(--tx2)" strokeDasharray="2 3" />
                  <circle className={focus === "you" ? "pulse focus-glow" : undefined} cx={sx(Math.min(Math.max(p.flow_cm_s, X[0]), X[1]))} cy={sy(p.o2_pct)} r={focus === "you" ? 10 : 7} fill={burns ? "var(--ember)" : "var(--panel)"} stroke={burns ? "var(--card)" : "var(--tx)"} strokeWidth="2" />
                </g>}
                {hover && <circle cx={sx(hover.c.flow_cm_s)} cy={sy(hover.c.o2_min_pct)} r="4.5" fill="var(--ember)" stroke="var(--card)" strokeWidth="2" />}
                <g className="axis">
                  {[12, 15, 18, 21, 24, 27, 30, 33, 36].map((t) => <text key={t} x={M.l - 8} y={sy(t) + 3.5} textAnchor="end">{t}%</text>)}
                  {xTicks.map((t) => <text key={t} x={sx(t)} y={H - M.b + 16} textAnchor="middle">{t}</text>)}
                  <text x={W - M.r} y={H - 6} textAnchor="end">airflow, cm/s (log scale) →</text>
                  <text x={M.l} y={M.t - 4}>O₂ needed</text>
                </g>
              </svg>
              {hover && <div className="tip" style={{ left: hover.left, top: hover.top }}>
                <b>{hover.c.o2_min_pct.toFixed(1)}% O₂ needed</b><span>at {hover.c.flow_cm_s} cm/s · stretch rate {hover.c.a}/s</span>
              </div>}
            </div>
            <div className="legend" style={{ marginTop: 10 }}>
              <span><i style={{ background: "var(--ember)" }} />Boundary (NASA fit)</span>
              <span><i style={{ background: "color-mix(in srgb,var(--faint) 30%,transparent)" }} />Cannot keep burning</span>
              <span><i style={{ background: "color-mix(in srgb,var(--cyan) 30%,transparent)" }} />{res?.moon_range.label.split(":")[0] || "Moon range"}</span>
            </div>
          </div>

          <aside className="panel">
            <h3>Your rod and air</h3>
            <div className="ctl"><label>Rod diameter</label>
              <div className="chips" style={{ margin: 0 }}>{RODS.map((d) => <button key={d} type="button" className="chip" aria-pressed={rod === d} onClick={() => setRod(d)}>{d} mm · {RODS_IN[d]}</button>)}</div>
            </div>
            <div className="ctl"><label htmlFor="flow">Airflow <span>{flow} cm/s</span></label>
              <input id="flow" type="range" min="0" max="1000" value={toSlider(flow)} onChange={(e) => setFlow(toFlow(+e.target.value))} />
            </div>
            <div className="ctl"><label htmlFor="o2">Oxygen <span>{o2}%</span></label>
              <input id="o2" type="range" min="12" max="40" step="0.1" value={o2} onChange={(e) => setO2(+e.target.value)} />
              <div className="chips" style={{ margin: 0 }}>{PRESETS.map(([l, v]) => <button key={l} type="button" className="chip" aria-pressed={o2 === v} onClick={() => setO2(v)}>{l} · {v}%</button>)}</div>
            </div>
            {error && <p className="cav">{error}</p>}
            {p && <div className={"verdict" + (burns ? " burn" : "")}>
              <b>{burns ? "It can keep burning" : "It cannot keep burning"}</b>
              <div>Needs {p.o2_min_pct}% O₂ at this flow; you set {p.o2_pct}% ({p.margin_pct > 0 ? "+" : ""}{p.margin_pct} points).</div>
              <small>Limit set by {p.branch}. Stretch rate {p.a}/s.</small>
              {p.warnings.map((w) => <p key={w} className="tool" style={{ marginTop: 6 }}>⚠ {w}</p>)}
            </div>}
            {res && <>
              <p className="cav" style={{ marginTop: 14 }}><a href={res.url} target="_blank" rel="noreferrer" style={{ color: "var(--accent-text)" }}>{res.cite} ↗</a></p>
              {res.caveats.map((c) => <p key={c} className="cav" style={{ border: 0, paddingTop: 4 }}>{c}</p>)}
            </>}
          </aside>
        </div>
      </PageHead>
    </div>
  );
}
