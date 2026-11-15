// The details drawer: one full card from GET /investigations/{id}, with every finding linked to its source.
import { useEffect, useRef, useState } from "react";
import Art from "./Art.jsx";
import { ChatThread } from "./Chat.jsx";
import { GUIDES } from "./Avatar.jsx";
import { apiUrl, get } from "../lib/api.js";
import { firstSentence, fmt } from "../lib/habitats.js";

const JOB = { prevention: "prevention", detection: "detection", suppression: "suppression" };

function Source({ item }) {
  const cite = <cite>{item.cite}</cite>;
  return item.url ? <a href={item.url} target="_blank" rel="noreferrer">{cite}</a> : cite;
}

/** Download the investigation's cleaned test rows as CSV (GET /tests.csv). */
function Export({ card }) {
  if (!(card.tests?.count > 0) || card.origin === "upload") return null;
  return (
    <div className="dl">
      <a className="btn2" href={apiUrl(`/tests.csv?psi_id=${encodeURIComponent(card.id)}`)} download>↓ Download test data (CSV, {fmt(card.tests.count)} rows)</a>
    </div>
  );
}

export default function Detail({ id, ev, onClose, persona, level }) {
  const guide = (GUIDES[level] || GUIDES.student).name; // the selected persona: space guide / teacher / research colleague
  const [card, setCard] = useState(null);
  const [error, setError] = useState(null);
  const [asking, setAsking] = useState(false);
  const closeRef = useRef(null);
  const chatRef = useRef(null);

  useEffect(() => { if (asking) chatRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [asking]);
  useEffect(() => {
    setAsking(false);
    if (!id) return;
    setCard(null); setError(null);
    get(`/investigations/${id}`).then(setCard).catch((e) => setError(e.message));
  }, [id]);
  useEffect(() => { if (id) closeRef.current?.focus(); }, [id]);

  if (!id) return <aside className="detail" role="dialog" aria-modal="true" />;
  const inv = card || { id, fuel_type: null };
  const jobs = card?.fire_safety?.jobs || [];
  const psiPage = card?.links?.psi_page;

  return (
    <aside className="detail" role="dialog" aria-modal="true" aria-labelledby="dTitle">
      <div className="d-art"><Art inv={inv} /><button ref={closeRef} className="x" type="button" aria-label="Close" onClick={onClose}>×</button></div>
      <div className="d-body">
        {error && <p className="cav">Could not load this card ({error}).</p>}
        {!card && !error && <p className="loading">Loading…</p>}
        {card && <>
          <div>
            <h2 id="dTitle">{card.name}</h2>
            <div style={{ color: "var(--dim)" }}>{card.title} · {card.origin === "upload" ? "your upload" : card.id}</div>
          </div>
          <div className="kv">
            <div><b>{fmt(card.tests?.count)}</b><small>tests</small></div>
            <div><b>{ev?.n == null ? "–" : fmt(ev.n)}</b><small>{ev?.kind === "near" ? "just outside this air" : "in this air"}</small></div>
            <div><b>{(card.findings || []).length}</b><small>sourced findings</small></div>
          </div>
          {card.summary?.text && <p>{card.summary.text}</p>}
          <div><h4>What was found</h4>
            {(card.findings || []).map((f, i) => <div key={i} className="find">{f.text}<Source item={f} /></div>)}
            {!card.findings?.length && <p className="cav">No sourced findings on this card yet.</p>}
          </div>
          {jobs.length > 0 && <div><h4>Why it matters for fire safety</h4>
            <div className="teach">
              Informs fire {jobs.map((j) => JOB[j] || j).join(" and ")}{card.fire_safety?.psi_label ? ` (NASA PSI category: ${card.fire_safety.psi_label})` : ""}.
              {card.findings?.[0] && <> Key finding: {firstSentence(card.findings[0].text)}<Source item={card.findings[0]} /></>}
            </div>
          </div>}
          <Export card={card} />
          <div className="acts">
            <button type="button" className="p" aria-expanded={asking} onClick={() => setAsking(!asking)}>✦ {asking ? `Hide your ${guide}` : `Ask your ${guide} about this card`}</button>
            {psiPage && <a href={psiPage} target="_blank" rel="noreferrer" style={{ padding: "10px 14px", borderRadius: 10, border: "1px solid var(--seam)" }}>Open NASA page ↗</a>}
          </div>
          {asking && (
            <div className="inline-chat" ref={chatRef}>
              <ChatThread key={card.id} endpoint={`/investigations/${card.id}/chat`} persona={persona} level={level} autoFocus
                          placeholder={`Ask about ${card.name}…`}
                          intro={`I answer only about ${card.name}, from its card, its reports and its test tables, and link every claim to its source.`}
                          suggestions={[`What did ${card.name} find?`, "Under which oxygen and pressure was it tested?", "Which fuels or materials were burned?"]} />
            </div>
          )}
          <p className="cav">{card.origin === "upload"
            ? "From a report you uploaded and approved: not NASA PSI data."
            : "All tests ran in microgravity. Moon and Mars gravity were never tested."}</p>
        </>}
      </div>
    </aside>
  );
}
