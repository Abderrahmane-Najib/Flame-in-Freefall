// O2 x pressure map of every test row with both values measured (GET /coverage).
// x: pressure on a log scale (most tests sit near 101 kPa), y: chamber O2. Hovering a card highlights its rows.
import { memo } from "react";

const P = [40, 500];   // kPa, log scale
const O2 = [10, 42];   // %

const clamp = (v) => Math.min(1, Math.max(0, v));
const x = (p) => clamp(Math.log(p / P[0]) / Math.log(P[1] / P[0])) * 100;
const y = (o) => clamp((O2[1] - o) / (O2[1] - O2[0])) * 100;

function box(o2, p) { // [o2 range, pressure range] -> css position
  const left = x(p[0]), right = x(p[1]), top = y(o2[1]), bottom = y(o2[0]);
  return { left: left + "%", top: top + "%", width: Math.max(right - left, 0.8) + "%", height: bottom - top + "%" };
}

// The dots never change: drawn once, highlighted by a CSS rule on the hovered investigation id.
const Dots = memo(function Dots({ points }) {
  return points.map((p, i) => (
    <i key={i} className="dot" data-psi={p.psi_id} style={{ left: x(p.pressure_kpa) + "%", top: y(p.o2_pct) + "%" }}
       title={`${p.name} · ${p.fuel || ""} · ${p.o2_pct}% O₂ · ${p.pressure_kpa} kPa`} />
  ));
});

export default function CoverageMap({ coverage, focus }) {
  const zones = coverage?.zones;
  const moon = zones?.habitats.find((h) => h.id === "moon_base_rover")?.box;
  const iss = zones?.habitats.find((h) => h.id === "iss")?.box;
  const near = zones?.near_lunar;
  return (
    <aside className="mapbox space" id="mapbox">
      <h3>All tests · oxygen × pressure <span>{coverage ? `${coverage.counts.points.toLocaleString("en")} rows · log kPa` : "loading"}</span></h3>
      {focus && <style>{`.space .map.focus .dot[data-psi="${focus}"]{opacity:1;background:var(--ember);transform:scale(1.9);box-shadow:0 0 6px var(--ember)}`}</style>}
      <div className={"map" + (focus ? " focus" : "")}>
        {near && <div className="zone z-near" style={box([near.o2_pct[0], O2[1]], near.pressure_kpa)} title={near.label} />}
        {moon && <div className="zone z-moon" style={box([moon.o2_pct[0], O2[1]], moon.pressure_kpa)} title="Moon habitat & rover air" />}
        {iss && <div className="zone z-iss" style={box(iss.o2_pct, iss.pressure_kpa)} title="ISS air" />}
        {coverage && <Dots points={coverage.points} />}
        <span className="ax" style={{ left: -28, top: -4 }}>{O2[1]}%</span>
        <span className="ax" style={{ left: -28, bottom: -4 }}>{O2[0]}%</span>
        <span className="ax" style={{ left: 0, bottom: -18 }}>{P[0]} kPa</span>
        <span className="ax" style={{ left: x(101.3) + "%", bottom: -18, transform: "translateX(-50%)" }}>101</span>
        <span className="ax" style={{ right: 0, bottom: -18 }}>{P[1]} kPa</span>
      </div>
      <div className="legend">
        <span><i style={{ background: "var(--ember)" }} />Moon-habitat air</span>
        <span><i style={{ border: "1px dashed var(--cyan)" }} />Near-lunar</span>
        <span><i style={{ background: "var(--lime)" }} />ISS air</span>
      </div>
    </aside>
  );
}
