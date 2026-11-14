import { useState } from "react";
import CoverageMap from "./CoverageMap.jsx";
import InvCard from "./InvCard.jsx";
import Explain from "./Explain.jsx";
import { fmt } from "../lib/habitats.js";

function Badge({ ev }) {
  if (ev.kind === "in") return <span className="badge b-in">{fmt(ev.n)} in this air</span>;
  if (ev.kind === "near") return <span className="badge b-near">{fmt(ev.n)} just outside</span>;
  if (ev.kind === "note") return <span className="badge b-in" title="Air values taken from NASA documents, not the test table">~{fmt(ev.n)} · assumed air</span>;
  if (ev.kind === "na") return <span className="badge b-none">{ev.note}</span>;
  return <span className="badge b-none">0 in this air{ev.note ? " · " + ev.note : ""}</span>;
}

export default function Ranked({ title, ranked, coverage, onOpen, level }) {
  const [focus, setFocus] = useState(null);
  const [all, setAll] = useState(false);
  const shown = all ? ranked : ranked.slice(0, 6);
  return (
    <section id="ranked">
      <div className="sh">
        <div><h2>{title}</h2><p>Ordered by how many of each experiment's tests were run in this habitat's air. Hover a card to see its tests on the map.</p></div>
        <div className="sh-right">
          <Explain level={level} onStep={(f) => setFocus(f === "first" ? ranked[0]?.inv.id ?? null : null)} steps={[
            { title: "Best clues first", focus: "first", text: <>Not every experiment tells us about this place. The ones that lit the <strong>most fires in air like this habitat's</strong> come first, because they're the best clues for what a fire would do here. Its fires light up on the map.</> },
            { title: "What the badges mean", text: <><strong>"in this air"</strong>: fires tested in this habitat's air. <strong>"just outside"</strong>: almost the same air, but not quite. <strong>"0 in this air"</strong>: the experiment still taught NASA something, just in different air.</> },
            { title: "Try it", text: <>Hover any card to see <strong>where its fires were</strong> on the map, and click it for what was found, with the NASA source.</> },
          ]} />
          <a href="#/" onClick={(e) => { e.preventDefault(); setAll(!all); }}>{all ? "Show top 6 ↑" : `See all ${ranked.length} →`}</a>
        </div>
      </div>
      <div className="ranked">
        <div className="grid">
          {!ranked.length && <p className="loading">Loading experiments…</p>}
          {shown.map(({ inv, ev }, i) => (
            <InvCard key={inv.id} inv={inv} badge={<Badge ev={ev} />} corner={`#${i + 1}`} onOpen={onOpen} onFocusChange={setFocus} />
          ))}
        </div>
        <CoverageMap coverage={coverage} focus={focus} />
      </div>
    </section>
  );
}
