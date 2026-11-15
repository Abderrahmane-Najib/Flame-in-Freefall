// "Did you know?": one fact at a time, two groups of topics. Nothing is written by AI here.
//  - From the experiments: the curated NASA card findings, word for word, with their report page
//    (GET /investigations/findings).
//  - Space → Earth: the discovery prototype's facts (lib/spinoffs.js), word for word, NASA Spinoff / nasa.gov.
// Only for the Explorer and Student levels (App.jsx).
import { useEffect, useRef, useState } from "react";
import { ILL } from "./Art.jsx";
import { get } from "../lib/api.js";
import { OBJECTS, SOURCES } from "../lib/spinoffs.js";

const FAMILIES = [
  ["gas", "Gas flames"], ["droplet", "Liquid droplets"], ["solid", "Solid materials"],
  ["smoke", "Smoke"], ["ground", "Ground studies"],
];

// The prototype's object drawings (static strings from our own code, not user content).
const Icon = ({ o }) => (
  <svg viewBox="0 0 88 88" aria-hidden="true" fill={`${o.color}22`} stroke={o.color} strokeWidth="3"
       strokeLinecap="round" strokeLinejoin="round" dangerouslySetInnerHTML={{ __html: o.shape }} />
);

const EARTH = OBJECTS.map((o) => ({
  id: "earth-" + o.name, name: o.name, group: "earth", art: <Icon o={o} />, color: o.color,
  facts: o.facts.map(([title, text, why, src, label]) => ({ title, text, why, cite: label, url: SOURCES[src] })),
}));

function psiTopics(findings) {
  return FAMILIES.map(([t, name]) => ({
    id: t, name, group: "psi", art: ILL[t],
    facts: findings.filter((f) => f.fuel_type === t).map((f) => ({
      title: f.name, text: f.text, psi_id: f.psi_id, cite: f.cite, url: f.url,
      why: (f.safety_jobs || []).map((j) => j[0].toUpperCase() + j.slice(1)).join(" · "),
    })),
  })).filter((t) => t.facts.length);
}

// Each topic deals its facts in a shuffled order and only repeats once all were seen.
const bags = {};
function next(t) {
  if (!bags[t.id]?.length) {
    const b = t.facts.map((_, i) => i);
    for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; }
    bags[t.id] = b;
  }
  return bags[t.id].shift();
}

function Tray({ label, topics, active, onPick }) {
  return (
    <>
      <span className="df-eyebrow df-group">{label}</span>
      <div className="df-tray" role="group" aria-label={label}>
        {topics.map((t) => (
          <button key={t.id} type="button" aria-pressed={t.id === active} onClick={() => onPick(t)}>
            <span className={"df-thumb" + (t.group === "earth" ? " icon" : "")}>{t.art}</span><span>{t.name}</span>
          </button>
        ))}
      </div>
    </>
  );
}

export default function DidYouKnow({ onOpen }) {
  const dialog = useRef(null);
  const [psi, setPsi] = useState([]);
  const [topic, setTopic] = useState(null);
  const [shown, setShown] = useState(0);

  useEffect(() => { get("/investigations/findings").then((f) => setPsi(psiTopics(f))).catch(() => {}); }, []);
  const topics = [...psi, ...EARTH];

  function pick(t) { setTopic(t); setShown(next(t)); }

  function open() {
    pick(topics[Math.floor(Math.random() * topics.length)]);
    dialog.current.showModal();
  }

  const f = topic?.facts[shown];
  const earth = topic?.group === "earth";

  return (
    <>
      <button type="button" className="df-discover" onClick={open} title="Fire safety facts from NASA"
              aria-label="Did you know? Fire safety facts from NASA">
        <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
          {/* lightbulb: a fact, not AI */}
          <path d="M8 1.5a4.5 4.5 0 0 0-2.6 8.2c.4.3.6.7.6 1.1v.7h4v-.7c0-.4.2-.8.6-1.1A4.5 4.5 0 0 0 8 1.5z"
                fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
          <path d="M6.2 13.6h3.6M6.8 15h2.4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
        <span className="df-label">Did you know?</span>
      </button>
      <dialog ref={dialog} className="df-dialog" aria-labelledby="df-title"
              onClick={(e) => { if (e.target === dialog.current) dialog.current.close(); }}>
        <button type="button" className="df-close" aria-label="Close" onClick={() => dialog.current.close()}>×</button>
        <div className="df-heading">
          <span className="df-eyebrow">Etna / Did you know?</span>
          <h2 id="df-title">Small discoveries.<br />Earth-sized possibilities.</h2>
          <p>Pick a topic. Every fact links to the NASA page it comes from.</p>
        </div>
        {psi.length > 0 && <Tray label="From the experiments · NASA reports" topics={psi} active={topic?.id} onPick={pick} />}
        <Tray label="Space → Earth · NASA Spinoff" topics={EARTH} active={topic?.id} onPick={pick} />
        {f && (
          <article className="df-card" aria-live="polite">
            <div className={"df-art" + (earth ? " icon" : "")} style={earth ? { "--object-color": topic.color } : undefined}>{topic.art}</div>
            <div className="df-copy">
              <span className="df-eyebrow">{topic.name} · Fact {shown + 1} of {topic.facts.length}</span>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
              {f.why && <div className="df-why"><b>{earth ? "Why it matters" : "Helps with fire"}</b><p>{f.why}</p></div>}
              <a href={f.url} target="_blank" rel="noreferrer">{f.cite} ↗</a>
              <div className="df-actions">
                <button type="button" className="df-next" onClick={() => pick(topic)}>Another one →</button>
                {f.psi_id && (
                  <button type="button" className="df-more" onClick={() => { dialog.current.close(); onOpen(f.psi_id); }}>
                    Open the {f.title} card
                  </button>
                )}
              </div>
            </div>
          </article>
        )}
        <footer>Experiment facts: NASA PSI reports and test tables, as written on the cards (microgravity only) ·
          Space → Earth: NASA Spinoff and nasa.gov, historical items dated · Educational, not emergency instructions</footer>
      </dialog>
    </>
  );
}
