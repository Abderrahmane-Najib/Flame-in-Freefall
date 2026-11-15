// My reports: upload a PDF -> it is chunked and embedded -> chat with it -> the card agent drafts a card ->
// approve (it becomes an experiment card everywhere) or reject. API: /uploads (app/routes/uploads.py).
import { useCallback, useEffect, useRef, useState } from "react";
import { PageHead } from "../components/InvCard.jsx";
import { ChatThread } from "../components/Chat.jsx";
import { forget, fresh, post, upload } from "../lib/api.js";

const STATUS = { processing: "embedding…", unreviewed: "ready · not reviewed", approved: "approved", rejected: "rejected", failed: "failed" };
const FUELS = ["solid", "droplet", "gas", "smoke", "ground"];

function Status({ s }) { return <span className={"status " + s}>{STATUS[s] || s}</span>; }

function Point({ p, onPage }) {
  return (
    <div className="find">{p.text}
      <a href={p.url} onClick={(e) => { e.preventDefault(); onPage(p.url); }}><cite>{p.cite}</cite></a>
    </div>
  );
}

function CardDraft({ u, onChanged, onPage }) {
  const [card, setCard] = useState(u.card);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => setCard(u.card), [u.id, u.card]);

  async function act(name, fn) {
    setBusy(name); setError(null);
    try { await fn(); await onChanged(); } catch (e) { setError(e.message); }
    setBusy(null);
  }
  const draft = () => act("draft", async () => setCard(await post(`/uploads/${u.id}/card`)));
  const approve = () => act("approve", async () => { await post(`/uploads/${u.id}/approve`, { card }); forget("/investigations"); forget("/graph"); });
  const reject = () => act("reject", () => post(`/uploads/${u.id}/reject`));
  const set = (k, v) => setCard({ ...card, [k]: v });

  return (
    <div className="panel">
      <h3>Experiment card</h3>
      {!card && <p style={{ color: "var(--tx2)", marginBottom: 12 }}>A second agent reads the report's key passages and drafts a card in the same shape as the NASA ones. Every point keeps the page it comes from.</p>}
      {card && <>
        <div className="ctl"><label htmlFor="cn">Name</label><input id="cn" className="inp" value={card.name || ""} onChange={(e) => set("name", e.target.value)} disabled={u.status !== "unreviewed"} /></div>
        <div className="ctl"><label htmlFor="ct">Title</label><input id="ct" className="inp" value={card.title || ""} onChange={(e) => set("title", e.target.value)} disabled={u.status !== "unreviewed"} /></div>
        <div className="ctl"><label>Fuel family</label>
          <div className="chips" style={{ margin: 0 }}>{FUELS.map((f) => <button key={f} type="button" className="chip" aria-pressed={card.fuel_type === f} disabled={u.status !== "unreviewed"} onClick={() => set("fuel_type", f)}>{f}</button>)}</div>
        </div>
        {card.summary && <><h4 style={{ fontSize: 12, color: "var(--dim)", margin: "8px 0" }}>Summary</h4><Point p={card.summary.sources[0]} onPage={onPage} /></>}
        <h4 style={{ fontSize: 12, color: "var(--dim)", margin: "8px 0" }}>Findings ({card.findings.length})</h4>
        {card.findings.map((f, i) => <Point key={i} p={f} onPage={onPage} />)}
        {card.limitations?.length > 0 && <><h4 style={{ fontSize: 12, color: "var(--dim)", margin: "8px 0" }}>Limitations</h4>
          {card.limitations.map((f, i) => <Point key={i} p={f} onPage={onPage} />)}</>}
        {card.conditions?.fuels?.length > 0 && <p className="tool" style={{ margin: "8px 0" }}>Materials: {card.conditions.fuels.map((f) => f.name).join(", ")}</p>}
        <p className="cav">{card.review?.note}{card.review?.points_dropped ? ` ${card.review.points_dropped} point(s) dropped: their page was not among the passages read.` : ""}</p>
      </>}
      {error && <p className="cav" style={{ color: "var(--tx)" }}>⚠ {error}</p>}
      <div className="acts" style={{ marginTop: 14, flexWrap: "wrap" }}>
        {u.status === "unreviewed" && <button type="button" className={card ? "" : "p"} onClick={draft} disabled={!!busy}>{busy === "draft" ? "Drafting…" : card ? "Draft again" : "Draft a card"}</button>}
        {u.status === "unreviewed" && card && <button type="button" className="p" onClick={approve} disabled={!!busy}>{busy === "approve" ? "Approving…" : "Approve: add to experiments"}</button>}
        {u.status !== "rejected" && u.status !== "processing" && <button type="button" onClick={reject} disabled={!!busy}>{busy === "reject" ? "…" : "Reject"}</button>}
        {u.status === "approved" && <a className="btn" href="#/experiments">See it in Experiments →</a>}
      </div>
    </div>
  );
}

export default function Uploads({ persona, level }) {
  const [list, setList] = useState(null);
  const [selId, setSelId] = useState(null);
  const [u, setU] = useState(null);
  const [drag, setDrag] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(null);
  const fileInput = useRef(null);

  const refreshList = useCallback(() => fresh("/uploads").then(setList).catch((e) => setError(e.message)), []);
  const refreshOne = useCallback(async () => { if (selId) setU(await fresh(`/uploads/${selId}`)); await refreshList(); }, [selId, refreshList]);

  useEffect(() => { refreshList(); }, [refreshList]);
  useEffect(() => { setU(null); setPage(null); if (selId) fresh(`/uploads/${selId}`).then(setU).catch((e) => setError(e.message)); }, [selId]);
  useEffect(() => { // poll while embedding
    if (u?.status !== "processing") return;
    const t = setInterval(() => fresh(`/uploads/${u.id}`).then((x) => { setU(x); if (x.status !== "processing") refreshList(); }), 2000);
    return () => clearInterval(t);
  }, [u?.id, u?.status, refreshList]);

  async function send(file) {
    if (!file) return;
    setSending(true); setError(null);
    try {
      const r = await upload("/uploads", file);
      await refreshList();
      setSelId(r.id);
    } catch (e) { setError(e.message); }
    setSending(false);
  }

  async function openPage(url) {
    try { setPage(await fresh(url)); } catch (e) { setError(e.message); }
  }

  const pct = u?.chunks ? Math.round((u.chunks_embedded / u.chunks) * 100) : 0;

  return (
    <div className="page">
      <PageHead title="My reports" sub="Upload a combustion report (PDF). Etna reads it, lets you chat with it alone, and drafts an experiment card for you to approve. Uploads are never mixed with NASA data until you approve them.">
        <div className="cols" style={{ gridTemplateColumns: "320px minmax(0,1fr)" }}>
          <div className="list">
            <div className={"drop" + (drag ? " on" : "")}
                 onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
                 onDrop={(e) => { e.preventDefault(); setDrag(false); send(e.dataTransfer.files[0]); }}>
              <b>{sending ? "Uploading…" : "Drop a PDF here"}</b>
              <span>up to 20 MB · text PDFs (not scans)</span>
              <div style={{ marginTop: 12 }}><button type="button" className="btn2" onClick={() => fileInput.current.click()} disabled={sending}>Choose a file</button></div>
              <input ref={fileInput} type="file" accept="application/pdf,.pdf" hidden onChange={(e) => { send(e.target.files[0]); e.target.value = ""; }} />
            </div>
            {error && <p className="cav" style={{ color: "var(--tx)" }}>⚠ {error}</p>}
            {list?.length === 0 && <p className="loading">No uploads yet.</p>}
            {list?.map((x) => (
              <button key={x.id} type="button" className="up-row" aria-pressed={selId === x.id} onClick={() => setSelId(x.id)}>
                <b title={x.file}>{x.file}</b><Status s={x.status} />
              </button>
            ))}
          </div>

          <div className="list">
            {!u && <div className="soon"><p>{selId ? "Loading…" : "Upload a report or pick one on the left."}</p></div>}
            {u && <>
              <div className="panel">
                <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                  <h3 style={{ margin: 0, flex: 1, overflowWrap: "anywhere" }}>{u.file}</h3><Status s={u.status} />
                </div>
                <p className="tool">{u.n_pages} pages · {u.chunks} passages · {u.chunks_embedded} embedded{u.psi_id ? ` · card ${u.psi_id}` : ""}</p>
                {u.status === "processing" && <div className="bar" style={{ marginTop: 10 }}><i style={{ width: pct + "%" }} /></div>}
                {u.status === "failed" && <p className="cav">Embedding failed. Delete-and-retry is not built yet: check the server log.</p>}
              </div>
              {(u.status === "unreviewed" || u.status === "approved") && (
                <div className="inline-chat">
                  <ChatThread key={u.id} endpoint={`/uploads/${u.id}/chat`} persona={persona} level={level} onLink={openPage}
                              placeholder={`Ask about ${u.file}…`}
                              intro="I answer only from this report, and link every claim to its page."
                              suggestions={["What is this report about?", "What fuels and conditions were tested?", "What are the main findings?"]} />
                </div>
              )}
              {page && (
                <div className="panel">
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <h3 style={{ margin: 0 }}>{page.file}, PDF p. {page.page}</h3>
                    <button type="button" className="pill" onClick={() => setPage(null)} aria-label="Close page">×</button>
                  </div>
                  <div className="pagetext">{page.text}</div>
                </div>
              )}
              {u.status !== "processing" && u.status !== "failed" && <CardDraft u={u} onChanged={refreshOne} onPage={openPage} />}
            </>}
          </div>
        </div>
      </PageHead>
    </div>
  );
}
