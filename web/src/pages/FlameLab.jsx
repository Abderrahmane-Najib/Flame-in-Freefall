// Flame Lab: a burning fuel droplet in 3D (GET /predict/droplet). Timing comes from the nearest NASA droplet tests:
// FLEX (methanol, heptane) and CFI (dodecane and blends, with the cool-flame phase). Flame size and the Earth 1 g
// shape are an illustration. Habitat buttons set the air from GET /habitats.
import { useEffect, useMemo, useRef, useState } from "react";
import { PageHead } from "../components/InvCard.jsx";
import Explain from "../components/Explain.jsx";
import FlameScene from "../components/FlameScene.jsx";
import { fresh, get, post } from "../lib/api.js";

const HABS = [["iss", "ISS", "ug"], ["moon_base_rover", "Moon base", "bounds"], ["mars_base", "Mars base", "bounds"]];
// [id, label, experiment, a typical starting droplet in that experiment (mm)]
const FUELS = [["methanol", "Methanol", "FLEX", 2.5], ["heptane", "n-Heptane", "FLEX", 2.5],
  ["dodecane", "n-Dodecane", "CFI", 4.4], ["dodecane_iso25", "Dodecane + 25 % iso", "CFI", 4.4],
  ["dodecane_iso40", "Dodecane + 40 % iso", "CFI", 4.4]];
const D0_RANGE = { FLEX: [1.1, 4.7], CFI: [3.8, 6.4] };
const DILUENTS = [["N2", "Nitrogen (habitat air)"], ["CO2", "CO₂ added"], ["He", "Helium added"]];
const GRAVS = [["ug", "Microgravity"], ["1g", "Earth 1 g"], ["bounds", "Moon/Mars bounds"]];
const STATUS = {
  measured: ["burn", "Measured", "A NASA test was run at almost exactly this air and droplet size."],
  interpolated: ["burn", "Estimated from nearby tests", "Averaged from the 5 closest NASA tests (closer tests count more)."],
  outside: ["", "No test here", "No droplet of this fuel was burned at this air or size. The flame is drawn as a ghost, not a result."],
};
const ENDS = {
  extinction: "flame went out", disruption: "droplet burst", completion: "burned away",
  cool_flame: "cool flame", early_extinction: "cool flame went out", consumed_droplet: "burned away",
};
const STAGE = { hot: "Hot flame", cool: "Cool flame", out: "Out", none: "–" };
const TRUST = { tested_here: ["burn", "Tested here"], between: ["burn", "Between tests"], outside: ["", "Outside the tested range"] };

/** Trained predictors (POST /predict/models/{id}) that answer a question about this droplet: nitrogen air only,
 *  because the lab does not ask for the CO2 / helium percentage the models need. */
function modelQueries(res) {
  if (!res || res.diluent !== "N2") return [];
  const q = res.query, air = { o2_pct: q.o2_pct, pressure_kpa: q.pressure_kpa };
  if (res.experiment === "FLEX") return [["P1b", { ...air, fuel: res.table_fuel, co2_pct: 0, he_pct: 0 }]];
  return [["P7", { ...air, fuel: res.table_fuel, he_pct: 0, droplet_d0_mm: q.d0_mm }],
          ["P8", { ...air, he_pct: 0 }]];
}

export default function FlameLab({ level }) {
  const [habs, setHabs] = useState({});
  const [hab, setHab] = useState("iss");
  const [fuel, setFuel] = useState("methanol");
  const [diluent, setDiluent] = useState("N2");
  const [o2, setO2] = useState(21);
  const [p, setP] = useState(101.3);
  const [d0, setD0] = useState(2.5);
  const [grav, setGrav] = useState("ug");
  const [speed, setSpeed] = useState(1);
  const [playing, setPlaying] = useState(true);
  const [res, setRes] = useState(null);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState({ t: 0, d: 2.5, stage: "none" });
  const [preds, setPreds] = useState([]);     // [{ id, result }]

  useEffect(() => {
    get("/habitats").then((list) => setHabs(Object.fromEntries((list.habitats || list).map((h) => [h.id, h]))))
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      fresh(`/predict/droplet?fuel=${fuel}&o2_pct=${o2}&pressure_kpa=${p}&d0_mm=${d0}&diluent=${diluent}`)
        .then((r) => { setRes(r); setError(null); }).catch((e) => setError(e.message));
    }, 150);
    return () => clearTimeout(t);
  }, [fuel, o2, p, d0, diluent]);

  useEffect(() => {
    let live = true;
    Promise.all(modelQueries(res).map(([id, body]) => post(`/predict/models/${id}`, body).then((result) => ({ id, result }))))
      .then((r) => live && setPreds(r)).catch(() => live && setPreds([]));
    return () => { live = false; };
  }, [res]);

  // a diluent this fuel was never tested with (CFI had no CO2): fall back to nitrogen
  useEffect(() => {
    if (res?.fuel === fuel && res.diluents?.length && !res.diluents.includes(diluent)) setDiluent("N2");
  }, [res, fuel, diluent]);

  function pickHab(id, g) {
    const t = habs[id]?.target;
    setHab(id); setGrav(g);
    if (t) { setO2(t.o2_pct); setP(t.pressure_kpa); }
  }
  function pickFuel(id, exp, typical) {
    const [lo, hi] = D0_RANGE[exp];
    setFuel(id);
    if (d0 < lo || d0 > hi) setD0(typical);
  }

  // the scene restarts whenever this object changes, so build it only from the answer it belongs to
  const run = useMemo(() => res && {
    fuel: res.fuel, o2: res.query.o2_pct, p: res.query.pressure_kpa, d0: res.query.d0_mm, est: res.estimate,
  }, [res]);
  const est = res?.estimate, cool = est?.cool;
  const [cls, title, why] = STATUS[res?.status || "outside"];

  return (
    <div className="page">
      <PageHead title="Flame Lab: a burning fuel droplet"
                sub="Choose a habitat or your own air. The droplet shrinks at the speed NASA measured in the nearest ISS droplet tests (FLEX and CFI) and ends the way those tests ended, including the near-invisible cool flame. Drag to rotate, scroll to zoom."
                right={<Explain level={level} steps={[
                  { title: "A drop of fuel on fire", text: <>On the ISS, NASA lit floating drops of fuel a few millimetres wide. With no "up" in space, hot gas doesn't rise, so the flame wraps the drop like a <strong>glowing ball</strong> instead of a candle shape.</> },
                  { title: "Why the drop shrinks", text: <>The flame eats the fuel, so the drop gets smaller. NASA found it shrinks in a steady way: its <strong>diameter squared</strong> falls by the same amount every second. That amount is the <strong>burning rate K</strong>, the straight line in the chart under the 3D view.</> },
                  { title: "The ghost flame", text: <>With dodecane, a fuel like diesel, something strange happens: the bright flame goes out but the drop <strong>keeps shrinking</strong>. A <strong>cool flame</strong>, far too dim to see, is still burning it. It is a hidden fire risk: the fire looks out, but it is not.</> },
                  { title: "Three ways to end", text: <>A fire can <strong>go out</strong> before the fuel is gone, the drop can <strong>burst</strong>, or it can <strong>burn away completely</strong>. The lab shows the ending most nearby NASA tests had.</> },
                  { title: "Moon and Mars", text: <>Nobody has burned a drop in Moon or Mars gravity. So for those habitats you see <strong>two flames</strong>: the space one and an Earth one. The real flame would sit somewhere between them.</> },
                ]} />}>
        {/* Row 1: the 3D droplet | the controls (and the verdict they change) */}
        <div className="lab-top">
          <div className="panel lab-panel">
            <FlameScene run={run || { fuel, o2, p, d0, est: null }} mode={grav} playing={playing} speed={speed} onTick={setTick} />
            <div className="chips lab-play">
              <button type="button" className="chip" onClick={() => setPlaying(!playing)}>{playing ? "Pause" : "Play"}</button>
              {[0.5, 1, 2, 5].map((s) => <button key={s} type="button" className="chip" aria-pressed={speed === s} onClick={() => setSpeed(s)}>{s}×</button>)}
            </div>
          </div>
          <aside className="panel lab-controls">
            <h3>Habitat</h3>
            <div className="chips">
              {HABS.map(([id, label, g]) => <button key={id} type="button" className="chip" aria-pressed={hab === id} onClick={() => pickHab(id, g)}>{label}</button>)}
              <button type="button" className="chip" aria-pressed={hab === "custom"} onClick={() => setHab("custom")}>Custom</button>
            </div>
            {habs[hab]?.target && <p className="tool" style={{ marginBottom: 12 }}>{habs[hab].label}: {habs[hab].target.o2_pct} % O₂ at {habs[hab].target.pressure_kpa} kPa</p>}
            <div className="ctl"><label>Fuel</label>
              {["FLEX", "CFI"].map((exp) => (
                <div key={exp} className="chips" style={{ margin: 0 }}>
                  <span className="chip-label">{exp}</span>
                  {FUELS.filter((f) => f[2] === exp).map(([v, l, e, typ]) => <button key={v} type="button" className="chip" aria-pressed={fuel === v} onClick={() => pickFuel(v, e, typ)}>{l}</button>)}
                </div>))}
            </div>
            <div className="ctl"><label htmlFor="lab-o2">Oxygen <span>{o2} %</span></label>
              <input id="lab-o2" type="range" min="10" max="40" step="0.5" value={o2} onChange={(e) => { setO2(+e.target.value); setHab("custom"); }} />
            </div>
            <div className="ctl"><label htmlFor="lab-p">Pressure <span>{p} kPa</span></label>
              <input id="lab-p" type="range" min="40" max="510" step="0.5" value={p} onChange={(e) => { setP(+e.target.value); setHab("custom"); }} />
            </div>
            <div className="ctl"><label htmlFor="lab-d0">Starting droplet <span>{d0} mm</span></label>
              <input id="lab-d0" type="range" min="1.1" max="6.5" step="0.05" value={d0} onChange={(e) => setD0(+e.target.value)} />
            </div>
            <div className="ctl"><label>Gas mixed with the oxygen</label>
              <div className="chips" style={{ margin: 0 }}>{DILUENTS.map(([v, l]) => {
                const tested = !res?.diluents || res.fuel !== fuel || res.diluents.includes(v);
                return <button key={v} type="button" className="chip" aria-pressed={diluent === v} disabled={!tested}
                               title={tested ? undefined : "Never tested with this fuel"} onClick={() => setDiluent(v)}>{l}</button>;
              })}</div>
            </div>
            <div className="ctl"><label>Gravity</label>
              <div className="chips" style={{ margin: 0 }}>{GRAVS.map(([v, l]) => <button key={v} type="button" className="chip" aria-pressed={grav === v} onClick={() => setGrav(v)}>{l}</button>)}</div>
            </div>

            {error && <p className="cav">{error}</p>}
            {res && <div className={"verdict" + (cls ? " " + cls : "")}>
              <b>{title}</b>
              <div>{why}</div>
              {res.zone === "near_lunar" && <small>Near-lunar air (FLEX tested 71–72 kPa). This is not lunar air.</small>}
              {res.zone === "lunar" && <small>Lunar-air box: only CFI-G gas flames were tested here, never droplets.</small>}
              {res.status === "outside" && res.tested_range && <small> {res.experiment} tested {res.fuel_label} with {res.diluent} at {res.tested_range.o2_pct.join("–")} % O₂, {res.tested_range.pressure_kpa.join("–")} kPa and {res.tested_range.d0_mm.join("–")} mm droplets.</small>}
              {grav !== "ug" && <small> {grav === "1g" ? "The Earth shape is" : "The two shapes are"} an illustration from a NASA photo: the droplet tests have no 1 g runs and Moon or Mars gravity was never tested.</small>}
            </div>}
          </aside>
        </div>

        {/* Row 2: what happens to this droplet | second opinion + nearest NASA tests */}
        <div className="lab-results">
          <section className="panel">
            <h3>What happens to this droplet</h3>
            <DPlot res={res} t={tick.t} />
            <div className="lab-kv">
              <span>Time</span><b>{tick.t.toFixed(1)} s</b>
              <span>Droplet now</span><b>{tick.d.toFixed(2)} mm</b>
              <span>Burning now</span><b className={tick.stage === "cool" ? "lab-cool" : undefined}>{STAGE[tick.stage] || "–"}</b>
              <span>Hot flame K</span><b>{est ? `${est.k_mm2_s} mm²/s` : "–"}</b>
              <span>Hot flame out at</span><b title={est ? `From the ${est.ext_ratio_source}` : undefined}>{est ? `${est.end === "completion" ? 0 : est.d_ext_mm} mm${est.ext_ratio_source === "P6b model" ? " (P6b)" : ""}` : "–"}</b>
              <span>Hot flame time</span><b>{est ? `${est.burn_time_s} s` : "–"}</b>
              {cool && <>
                <span>Cool flame K</span><b className="lab-cool">{cool.k_mm2_s} mm²/s</b>
                <span>Cool flame ends at</span><b className="lab-cool">{cool.d_end_mm} mm</b>
                <span>Cool flame time</span><b className="lab-cool">{cool.burn_time_s} s</b>
              </>}
              <span>Ending</span><b>{est ? (cool ? `cool flame, then ${ENDS[cool.end] || "unknown"}` : ENDS[est.end] || est.end) : "–"}</b>
            </div>
            {cool?.extrapolated_share > 0 && <p className="tool" style={{ marginTop: 8 }}>{Math.round(cool.extrapolated_share * 100)} % of the weight comes from tests whose cool-flame end NASA extrapolated (the droplet left the camera view).</p>}
          </section>
          <div className="lab-side">
            {(preds.length > 0 || (res && res.diluent !== "N2")) && <section className="panel">
              {preds.length > 0 && <>
                <h3>Trained models: a second opinion</h3>
                <p className="tool" style={{ marginBottom: 8 }}>Fitted to all {res.experiment} tests, not just the 5 nearest. They can disagree with the lab.</p>
                {preds.map(({ id, result }) => <ModelAnswer key={id} result={result} />)}
              </>}
              {res && res.diluent !== "N2" && <p className="tool" style={{ marginTop: 12 }}>Trained models are shown for nitrogen air only.</p>}
            </section>}
            {res?.nearest?.length > 0 && <section className="panel">
              {res?.nearest?.length > 0 && <>
                <h3>Nearest NASA tests ({res.experiment})</h3>
                <table className="lab-near">
                  <thead><tr><th>O₂</th><th>kPa</th><th>d₀</th><th>K</th><th>Ending</th></tr></thead>
                  <tbody>{res.nearest.map((n) => (
                    <tr key={n.cite}>
                      <td>{n.o2_pct}</td><td>{n.pressure_kpa}</td><td>{n.d0_mm}</td><td>{n.k_mm2_s}</td>
                      <td><a href={n.url} target="_blank" rel="noreferrer" title={n.cite}>
                        {n.cool ? `cool flame${n.cool.end ? ", " + ENDS[n.cool.end] : ""}` : ENDS[n.end] || n.end} ↗</a></td>
                    </tr>))}
                  </tbody>
                </table>
                <p className="tool">d₀ in mm, K (hot flame) in mm²/s. Links open the {res.source.cite}.</p>
              </>}
            </section>}
          </div>
        </div>
        {res && <p className="cav lab-note">{res.check.text} {res.illustration.join(" ")}</p>}
      </PageHead>
    </div>
  );
}

/** One predictor's answer: most likely outcome with its probability and the trust badge. */
function ModelAnswer({ result }) {
  const [cls, label] = TRUST[result.trust] || TRUST.outside;
  const a = result.answer;
  return (
    <div className={"verdict lab-model" + (cls ? " " + cls : "")}>
      <small>{result.predictor} · {label}</small>
      <b>{result.title}</b>
      {a ? Object.entries(a.probabilities).map(([k, p]) => (
        <div key={k} className="lab-prob"><span>{k}</span><i style={{ width: `${Math.round(p * 100)}%` }} /><em>{Math.round(p * 100)} %</em></div>
      )) : <div>No model value here: see the nearest NASA tests below.</div>}
      {result.notes.map((n) => <small key={n}>{n}</small>)}
    </div>
  );
}

/** d² against time: the hot-flame line, then the cool-flame line (CFI), a dot for now, dashed lines at the end sizes. */
// The chart fills its box (.lab-plot, which grows to the card's free height): the viewBox height follows the
// box's shape, so text and marks keep their size instead of being stretched.
function DPlot({ res, t }) {
  const box = useRef(null);
  const [shape, setShape] = useState(150 / 640);
  useEffect(() => {
    const el = box.current;
    if (!el) return undefined;
    const ro = new ResizeObserver(([e]) => { const { width, height } = e.contentRect; if (width) setShape(height / width); });
    ro.observe(el);
    return () => ro.disconnect();
  }, [res]);
  const est = res?.estimate;
  if (!est) return null;
  const W = 640, H = Math.max(150, Math.round(W * shape)), L = 40, R = 10, T = 10, B = 24;
  const d0 = res.query.d0_mm, dHot = est.end === "completion" ? 0 : est.d_ext_mm, c = est.cool;
  const tHot = Math.max(0, (d0 ** 2 - dHot ** 2) / est.k_mm2_s);
  const tCool = c ? Math.max(0, (dHot ** 2 - c.d_end_mm ** 2) / c.k_mm2_s) : 0;
  const dEnd = c ? c.d_end_mm : dHot, tEnd = tHot + tCool, tMax = tEnd * 1.08 || 1, yMax = d0 ** 2 * 1.05;
  const X = (x) => L + ((W - L - R) * x) / tMax, Y = (y) => T + (H - T - B) * (1 - y / yMax);
  const tt = Math.min(t, tEnd);
  const yNow = tt <= tHot ? d0 ** 2 - est.k_mm2_s * tt : dHot ** 2 - c.k_mm2_s * (tt - tHot);
  return (
    <div className="lab-plot" ref={box}>
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Droplet diameter squared against time">
      <g className="grid"><line x1={L} x2={W - R} y1={Y(0)} y2={Y(0)} /><line x1={L} x2={L} y1={T} y2={Y(0)} /></g>
      <line x1={X(0)} y1={Y(dEnd ** 2)} x2={W - R} y2={Y(dEnd ** 2)} stroke="var(--faint)" strokeDasharray="3 3" />
      <line x1={X(0)} y1={Y(d0 ** 2)} x2={X(tHot)} y2={Y(dHot ** 2)} stroke="var(--ember)" strokeWidth="2" />
      {c && <line x1={X(tHot)} y1={Y(dHot ** 2)} x2={X(tEnd)} y2={Y(dEnd ** 2)} stroke="#8ec5ff" strokeWidth="2" strokeDasharray="6 3" />}
      <circle cx={X(tt)} cy={Y(yNow)} r="5" fill={tt > tHot && c ? "#8ec5ff" : "var(--ember)"} stroke="var(--card)" strokeWidth="2" />
      <g className="axis">
        <text x={L - 6} y={Y(d0 ** 2) + 4} textAnchor="end">{(d0 ** 2).toFixed(1)}</text>
        <text x={L - 6} y={Y(0) + 4} textAnchor="end">0</text>
        <text x={L} y={H - 6}>0 s</text>
        <text x={W - R} y={H - 6} textAnchor="end">{tMax.toFixed(1)} s</text>
        <text x={W - R} y={T + 10} textAnchor="end">d² (mm²): hot flame{c ? " ─, cool flame ╌" : ""}</text>
      </g>
    </svg>
    </div>
  );
}
