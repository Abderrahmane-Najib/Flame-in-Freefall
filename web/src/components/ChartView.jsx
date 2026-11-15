// A chart drawn by the assistant's make_chart tool (app/services/charts.py). Every number comes from the
// NASA test tables, not from the model. Scatter: one mark per test row, colour + shape per group (validated
// fuel palette). Bar: fires per group, one colour. Hover a mark for its table and row; sources link below.
import { useState } from "react";
import { Mark } from "../lib/series.jsx";

const FAMILY = { gas: 0, droplet: 1, solid: 2 };
const SLOTS = [
  { color: "var(--s-gas)", shape: "circle" },
  { color: "var(--s-droplet)", shape: "square" },
  { color: "var(--s-solid)", shape: "triangle" },
];
const OTHER = { color: "var(--faint)", shape: "circle" };

// ~5 round ticks between lo and hi
function ticks(lo, hi) {
  if (lo === hi) { lo -= 1; hi += 1; }
  const raw = (hi - lo) / 5, mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * mag).find((s) => s >= raw);
  const out = [];
  for (let v = Math.floor(lo / step) * step; v <= hi + step / 2; v += step) out.push(+v.toPrecision(10));
  return out;
}

const fmt = (v) => (Math.abs(v) >= 100 ? Math.round(v) : +v.toPrecision(3)).toLocaleString();

function Scatter({ spec }) {
  const [hover, setHover] = useState(null);
  const W = 360, H = 230, L = 44, R = 10, T = 10, B = 36;
  const style = Object.fromEntries(spec.groups.map((g, i) => [g.id,
    g.id === "other" ? OTHER : SLOTS[FAMILY[g.id] ?? i]]));
  const xt = ticks(Math.min(...spec.points.map((p) => p.x)), Math.max(...spec.points.map((p) => p.x)));
  const yt = ticks(Math.min(...spec.points.map((p) => p.y)), Math.max(...spec.points.map((p) => p.y)));
  const sx = (v) => L + ((v - xt[0]) / (xt.at(-1) - xt[0])) * (W - L - R);
  const sy = (v) => H - B - ((v - yt[0]) / (yt.at(-1) - yt[0])) * (H - T - B);
  return (
    <>
      {spec.groups.length > 1 && (
        <div className="chart-legend">
          {spec.groups.map((g) => (
            <span key={g.id}><svg width="12" height="12" aria-hidden="true">
              <Mark shape={style[g.id].shape} x={6} y={6} r={4} fill={style[g.id].color} /></svg>{g.label}</span>
          ))}
        </div>
      )}
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label={`${spec.title}: ${spec.points.length} test rows`} onMouseLeave={() => setHover(null)}>
        {yt.map((v) => <g key={"y" + v}>
          <line x1={L} x2={W - R} y1={sy(v)} y2={sy(v)} className="chart-grid" />
          <text x={L - 6} y={sy(v) + 3} textAnchor="end" className="chart-tick">{fmt(v)}</text></g>)}
        {xt.map((v) => <text key={"x" + v} x={sx(v)} y={H - B + 14} textAnchor="middle" className="chart-tick">{fmt(v)}</text>)}
        <text x={(L + W - R) / 2} y={H - 4} textAnchor="middle" className="chart-axis">{spec.x.label}</text>
        <text x={10} y={(T + H - B) / 2} textAnchor="middle" className="chart-axis"
              transform={`rotate(-90 10 ${(T + H - B) / 2})`}>{spec.y.label}</text>
        {spec.points.map((p, i) => {
          const s = style[p.g] || OTHER;
          return <Mark key={i} shape={s.shape} x={sx(p.x)} y={sy(p.y)} r={hover === p ? 5 : 3.5} fill={s.color}
                       className="chart-mark" onMouseEnter={() => setHover(p)} onClick={() => setHover(p)} />;
        })}
      </svg>
      <p className="chart-hover">{hover
        ? <>{spec.x.label} <b>{fmt(hover.x)}</b> · {spec.y.label} <b>{fmt(hover.y)}</b> · {hover.psi}, table row {hover.row}</>
        : <>Hover or tap a mark to see its test row.</>}</p>
    </>
  );
}

function Bars({ spec }) {
  const max = Math.max(...spec.bars.map((b) => b.value), 1);
  return (
    <div className="chart-bars" role="list" aria-label={spec.title}>
      {spec.bars.map((b) => (
        <div key={b.id} className="chart-bar" role="listitem" title={`${b.label}: ${b.value} fires`}>
          <span className="chart-bar-label">{b.label}</span>
          <span className="chart-bar-track"><span style={{ width: `${(b.value / max) * 100}%` }} /></span>
          <span className="chart-bar-value">{b.value.toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
}

const FILTER = {
  psi_id: (v) => v, fuel: (v) => `fuel "${v}"`, fuel_type: (v) => v, o2_min: (v) => `O₂ ≥ ${v} %`, o2_max: (v) => `O₂ ≤ ${v} %`,
  pressure_min_kpa: (v) => `≥ ${v} kPa`, pressure_max_kpa: (v) => `≤ ${v} kPa`,
  lunar_air: (v) => (v ? "lunar air only" : "not lunar air"), has_result: (v) => (v ? "tests with a result only" : "tests without a result"),
};

export default function ChartView({ spec }) {
  const tables = Object.entries(spec.tables || {});
  const filters = Object.entries(spec.filters || {}).map(([k, v]) => (FILTER[k] ? FILTER[k](v) : `${k} ${v}`));
  return (
    <figure className="chart">
      <figcaption>{spec.title}</figcaption>
      {filters.length > 0 && <p className="chart-src">Filters: {filters.join(" · ")}</p>}
      {spec.kind === "bar" ? <Bars spec={spec} /> : <Scatter spec={spec} />}
      <p className="chart-src">
        {spec.kind === "bar" ? spec.x.label : `${spec.points.length} test rows`}
        {spec.skipped > 0 && ` (${spec.skipped} without a value not drawn)`}
        {spec.unknown_rows > 0 && ` (${spec.unknown_rows} rows without a test count)`}
        . Source: {tables.map(([name, url], i) => (
          <span key={name}>{i > 0 && ", "}<a href={url} target="_blank" rel="noreferrer">NASA PSI table {name.replace(/^PSI-\d+_/, "").replace(/\.\w+$/, "")}</a></span>
        ))}
      </p>
    </figure>
  );
}
