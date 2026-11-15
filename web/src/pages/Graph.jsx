// Knowledge graph (GET /graph): investigations linked to fuel families, materials, safety jobs, hardware and
// the habitat airs they were tested in. Choosing a habitat redraws the graph with only the experiments tested
// in that air (and what they burned / flew on). Layout: d3-force, computed once per view; drawn by React.
import { useEffect, useMemo, useRef, useState } from "react";
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation, forceX, forceY } from "d3-force";
import { select } from "d3-selection";
import { zoom, zoomIdentity } from "d3-zoom";
import { PageHead } from "../components/InvCard.jsx";
import Explain from "../components/Explain.jsx";
import { get } from "../lib/api.js";

const TYPES = {
  investigation: { label: "Experiments", color: "var(--s-gas)", shape: "circle" },
  material: { label: "Materials", color: "var(--s-droplet)", shape: "circle" },
  habitat: { label: "Habitat air", color: "var(--s-solid)", shape: "planet" },
  family: { label: "Fuel families", color: "var(--dim)", shape: "square" },
  job: { label: "Safety jobs", color: "var(--dim)", shape: "diamond" },
  hardware: { label: "Hardware", color: "var(--dim)", shape: "triangle" },
};
const HABITATS = [
  [null, "All habitats"],
  ["hab:iss", "ISS air"],
  ["hab:moon_base_rover", "Moon base & rover"],
  ["hab:mars_base", "Mars base"],
  ["hab:near_lunar", "Near-lunar (not lunar)"],
];
const W = 1000, H = 680;

function radius(n) {
  if (n.type === "investigation") return 7 + Math.sqrt(n.tests || 0) / 2;
  if (n.type === "habitat") return 14;
  return n.type === "material" ? 5 : 8;
}

function Shape({ n, r, ...rest }) {
  const s = TYPES[n.type].shape;
  if (s === "square") return <rect x={n.x - r} y={n.y - r} width={r * 2} height={r * 2} rx={3} {...rest} />;
  if (s === "diamond") return <path d={`M${n.x},${n.y - r * 1.3}L${n.x + r * 1.3},${n.y}L${n.x},${n.y + r * 1.3}L${n.x - r * 1.3},${n.y}Z`} {...rest} />;
  if (s === "triangle") return <path d={`M${n.x},${n.y - r * 1.3}L${n.x + r * 1.2},${n.y + r * 0.9}L${n.x - r * 1.2},${n.y + r * 0.9}Z`} {...rest} />;
  if (s === "planet") return <g><circle cx={n.x} cy={n.y} r={r} {...rest} /><ellipse cx={n.x} cy={n.y} rx={r * 1.7} ry={r * 0.45} fill="none" stroke={rest.fill} strokeOpacity=".7" strokeWidth="1.5" transform={`rotate(-20 ${n.x} ${n.y})`} /></g>;
  return <circle cx={n.x} cy={n.y} r={r} {...rest} />;
}

/** The nodes and links of one view: everything, or one habitat's experiments and what they connect to. */
function subgraph(data, habitat) {
  if (!habitat) return data;
  const exps = new Set(data.edges.filter((e) => e.target === habitat).map((e) => e.source));
  const keep = new Set([habitat, ...exps]);
  data.edges.forEach((e) => { if (exps.has(e.source) && !e.target.startsWith("hab:")) keep.add(e.target); });
  return {
    nodes: data.nodes.filter((n) => keep.has(n.id)),
    edges: data.edges.filter((e) => keep.has(e.source) && keep.has(e.target)),
  };
}

function layout(view, habitat) {
  const nodes = view.nodes.map((n) => ({ ...n, ...(n.id === habitat ? { fx: W / 2, fy: H / 2 } : {}) }));
  const links = view.edges.map((e) => ({ ...e }));
  const small = nodes.length < 30;
  forceSimulation(nodes)
    .force("link", forceLink(links).id((d) => d.id)
      .distance((l) => (l.target.type === "habitat" ? 150 : l.target.type === "material" ? 45 : 95)).strength(0.45))
    .force("charge", forceManyBody().strength(small ? -420 : -200))
    .force("collide", forceCollide().radius((d) => radius(d) + 14))
    .force("x", forceX(W / 2).strength(0.04))
    .force("y", forceY(H / 2).strength(0.06))
    .force("center", forceCenter(W / 2, H / 2))
    .stop()
    .tick(450);
  return { nodes, links };
}

/** The zoom that fits all nodes in the box. */
function fit(nodes) {
  if (!nodes.length) return zoomIdentity;
  const xs = nodes.map((n) => n.x), ys = nodes.map((n) => n.y);
  const [x0, x1, y0, y1] = [Math.min(...xs) - 60, Math.max(...xs) + 60, Math.min(...ys) - 50, Math.max(...ys) + 50];
  const k = Math.min(W / (x1 - x0), H / (y1 - y0), 2.2);
  return zoomIdentity.translate(W / 2 - (k * (x0 + x1)) / 2, H / 2 - (k * (y0 + y1)) / 2).scale(k);
}

// A gentle curve between two nodes (straight lines cross into a hairball).
const curve = (a, b) => {
  const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y;
  return `M${a.x},${a.y}Q${mx - dy * 0.12},${my + dx * 0.12} ${b.x},${b.y}`;
};

export default function Graph({ onOpen, level }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [habitat, setHabitat] = useState(null);
  const [sel, setSel] = useState(null);
  const [hover, setHover] = useState(null);
  const [hidden, setHidden] = useState({});
  const [t, setT] = useState(zoomIdentity);
  const svg = useRef(null);
  const zoomer = useRef(null);
  // Phones: the wide graph fills the tall box (sides cropped, drag to see them) instead of a thin strip.
  const phone = typeof matchMedia !== "undefined" && matchMedia("(max-width:640px)").matches;

  useEffect(() => { get("/graph").then(setData).catch((e) => setError(e.message)); }, []);
  const g = useMemo(() => (data ? layout(subgraph(data, habitat), habitat) : null), [data, habitat]);

  useEffect(() => { setSel(habitat || "hab:moon_base_rover"); }, [habitat]);
  useEffect(() => {
    if (!g) return;
    const el = select(svg.current);
    zoomer.current = zoom().scaleExtent([0.3, 5]).on("zoom", (e) => setT(e.transform));
    el.call(zoomer.current).call(zoomer.current.transform, fit(g.nodes));
    return () => el.on(".zoom", null);
  }, [g]);

  const visible = (n) => !hidden[n.type];
  const focus = hover || sel;
  const near = useMemo(() => {
    const s = new Set([focus]);
    g?.links.forEach((l) => { if (l.source.id === focus) s.add(l.target.id); if (l.target.id === focus) s.add(l.source.id); });
    return s;
  }, [g, focus]);
  const node = g?.nodes.find((n) => n.id === sel) || data?.nodes.find((n) => n.id === sel);
  const rels = (g?.links || []).filter((l) => l.source.id === sel || l.target.id === sel)
    .map((l) => ({ other: l.source.id === sel ? l.target : l.source, rel: l.rel, tests: l.tests }))
    .sort((a, b) => (b.other.type === "investigation") - (a.other.type === "investigation") || (b.tests || 0) - (a.tests || 0));
  const habLabel = HABITATS.find(([id]) => id === habitat)?.[1];
  const expCount = g?.nodes.filter((n) => n.type === "investigation").length || 0;

  return (
    <div className="page">
      <PageHead title="Knowledge graph" sub="How the experiments connect: what they burned, which air they were tested in, what they flew on and which fire-safety job they inform. Pick a habitat to see only the experiments tested in its air."
                right={<Explain level={level} onStep={(f) => { if (f === "all") setHabitat(null); if (f === "moon") setHabitat("hab:moon_base_rover"); if (f === "iss") setHabitat("hab:iss"); }} steps={[
                  { title: "A map of connections", focus: "all", text: <>Think of it as a <strong>map of who is connected to what</strong>. <strong>Blue</strong> dots are NASA's fire experiments (bigger means more fires). <strong>Orange</strong> dots are the things they burned. The <strong>green planets</strong> are the kinds of air astronauts breathe.</> },
                  { title: "What a line means", text: <>A line means "this experiment <strong>burned</strong> that material" or "was <strong>tested in</strong> that air". Hover any dot to light up its lines, or click it to read about it on the right.</> },
                  { title: "Space-station air", focus: "iss", text: <>Here are only the experiments that lit fires in <strong>space-station air</strong>. Several experiments, many materials: this air is well studied.</> },
                  { title: "Moon-base air", focus: "moon", text: <>And here is <strong>Moon-base air</strong>: just <strong>one experiment</strong>, burning only gases. No solid material (like fabric or plastic) has been tested in this air. That's how little we know about fire on a Moon base.</> },
                  { title: "Your turn", focus: "all", text: <>Use the <strong>Habitat</strong> buttons to switch between airs, and the <strong>Show</strong> buttons to hide what you don't need.</> },
                ]} />}>
        {error && <p className="cav">Could not load: {error}</p>}
        <div className="chips" role="group" aria-label="Habitat">
          <span className="chip-label">Habitat</span>
          {HABITATS.map(([id, label]) => (
            <button key={label} type="button" className="chip" aria-pressed={habitat === id} onClick={() => setHabitat(id)}>
              {id && <svg width="16" height="12"><Shape n={{ type: "habitat", x: 8, y: 6 }} r={3.5} fill="var(--s-solid)" /></svg>}{label}
            </button>
          ))}
        </div>
        <div className="chips" role="group" aria-label="What to show">
          <span className="chip-label">Show</span>
          {Object.entries(TYPES).map(([k, v]) => (
            <button key={k} type="button" className="chip" aria-pressed={!hidden[k]} onClick={() => setHidden({ ...hidden, [k]: !hidden[k] })}>
              <svg width="14" height="12"><Shape n={{ type: k, x: 7, y: 6 }} r={3.5} fill={v.color} /></svg>{v.label}
            </button>
          ))}
        </div>
        <div className="cols">
          <div className="graph-box space">
            <div className="g-status">{habitat ? `${expCount} experiment${expCount === 1 ? "" : "s"} tested in ${habLabel}` : `${expCount} experiments · ${g?.nodes.length || 0} nodes`}</div>
            {habitat && expCount === 0 && <div className="g-empty">No experiment was tested in this air.</div>}
            <svg ref={svg} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio={phone ? "xMidYMid slice" : "xMidYMid meet"} role="img" aria-label="Network of experiments and what they connect to">
              <defs>
                <filter id="g-glow" x="-80%" y="-80%" width="260%" height="260%">
                  <feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
              </defs>
              <g transform={t.toString()}>
                {g?.links.filter((l) => visible(l.source) && visible(l.target)).map((l, i) => {
                  const on = near.has(l.source.id) && near.has(l.target.id) && (l.source.id === focus || l.target.id === focus);
                  const air = l.target.type === "habitat";
                  return <path key={i} d={curve(l.source, l.target)} className={"glink" + (on ? " hi" : focus ? " dim" : "") + (air ? " air" : "")}
                               strokeWidth={air && l.tests ? Math.min(1.2 + Math.sqrt(l.tests) / 3, 5) : undefined} />;
                })}
                {g?.nodes.filter(visible).map((n) => {
                  const r = radius(n), on = near.has(n.id), big = n.type === "investigation" || n.type === "habitat";
                  return (
                    <g key={n.id} className={"gnode" + (on || !focus ? "" : " dim")} onClick={() => setSel(n.id)}
                       onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)}>
                      {big && <circle cx={n.x} cy={n.y} r={r + 6} fill={TYPES[n.type].color} opacity={n.id === sel ? 0.35 : 0.14} filter="url(#g-glow)" />}
                      <Shape n={n} r={r} fill={TYPES[n.type].color} stroke={n.id === sel ? "#fff" : "rgba(3,5,13,.8)"} strokeWidth={n.id === sel ? 2.5 : 1.2} />
                      {(big || on) && <text x={n.x} y={n.y + r + (n.type === "habitat" ? 16 : 13)} textAnchor="middle" className={big ? "big" : ""}>{n.label}</text>}
                    </g>
                  );
                })}
              </g>
            </svg>
            <div className="g-hint">drag to move · scroll to zoom · click a node</div>
          </div>

          <aside className="panel">
            {!node ? <p className="loading">{g ? "Click a node." : "Loading…"}</p> : <>
              <span className="tag">{TYPES[node.type].label.replace(/s$/, "")}</span>
              <h3 style={{ fontSize: 20, margin: "8px 0 4px" }}>{node.label}</h3>
              {node.title && <p style={{ color: "var(--dim)", marginBottom: 8 }}>{node.title}</p>}
              {node.summary && <p style={{ color: "var(--tx2)", marginBottom: 12 }}>{node.summary}</p>}
              <div className="acts" style={{ marginBottom: 14, flexWrap: "wrap" }}>
                {node.type === "investigation" && <button type="button" className="p" onClick={() => onOpen(node.id)}>Open details</button>}
                {node.type === "habitat" && habitat !== node.id && <button type="button" className="p" onClick={() => setHabitat(node.id)}>Show only its experiments</button>}
                {habitat && <button type="button" onClick={() => setHabitat(null)}>Show all habitats</button>}
              </div>
              {node.type === "habitat" && !rels.length && <p className="teach">No experiment was tested in this air.</p>}
              <h4 style={{ fontSize: 12, color: "var(--dim)", margin: "6px 0 8px" }}>Linked to ({rels.length})</h4>
              <div className="list">
                {rels.map((r) => (
                  <button key={r.other.id + r.rel} type="button" className="up-row" onClick={() => setSel(r.other.id)}>
                    <svg width="14" height="12"><Shape n={{ ...r.other, x: 7, y: 6 }} r={3.5} fill={TYPES[r.other.type].color} /></svg>
                    <b>{r.other.label}</b><small style={{ color: "var(--dim)" }}>{r.rel}{r.tests ? ` · ${r.tests} tests` : ""}</small>
                  </button>
                ))}
              </div>
              {node.findings?.length > 0 && <>
                <h4 style={{ fontSize: 12, color: "var(--dim)", margin: "16px 0 8px" }}>Findings</h4>
                {node.findings.slice(0, 4).map((f, i) => (
                  <div key={i} className="find">{f.text}{f.url ? <a href={f.url} target="_blank" rel="noreferrer"><cite>{f.cite}</cite></a> : <cite>{f.cite}</cite>}</div>
                ))}
              </>}
            </>}
            <p className="cav" style={{ marginTop: 14 }}>"Tested in this air" = chamber O₂ and pressure both measured inside the habitat's range. Near-lunar is never lunar. Microgravity only.</p>
          </aside>
        </div>
      </PageHead>
    </div>
  );
}
