import Art from "./Art.jsx";
import { firstSentence, fmt } from "../lib/habitats.js";

export const JOB = { prevention: "Prevention", detection: "Detection", suppression: "Suppression" };

/** One investigation card (the design's .card). badge and corner are optional overlays on the artwork. */
export default function InvCard({ inv, badge, corner, onOpen, onFocusChange }) {
  const focus = (on) => onFocusChange?.(on ? inv.id : null);
  return (
    <button className="card" type="button" onClick={() => onOpen(inv.id)}
            onMouseEnter={() => focus(true)} onMouseLeave={() => focus(false)}
            onFocus={() => focus(true)} onBlur={() => focus(false)}>
      <div className="art"><Art inv={inv} />{badge}{corner && <span className="rank">{corner}</span>}</div>
      <div className="body">
        <div className="ttl"><b>{inv.name}</b><span>{inv.origin === "upload" ? "your upload" : inv.id}</span></div>
        <p>{firstSentence(inv.summary)}</p>
        <div className="meta">
          <span className="tag mono">{inv.tests == null ? "no test table" : `${fmt(inv.tests)} tests`}</span>
          {(inv.safety_jobs || []).map((j) => <span key={j} className="tag">{JOB[j] || j}</span>)}
          <span className="more">Details →</span>
        </div>
      </div>
    </button>
  );
}

export function PageHead({ title, sub, right, children, id }) {
  return (
    <section id={id}>
      <div className="sh"><div><h2>{title}</h2>{sub && <p>{sub}</p>}</div>{right}</div>
      {children}
    </section>
  );
}
