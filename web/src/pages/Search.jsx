// Report search (GET /search): hybrid full-text + meaning search over every report page, with its source.
import { useEffect, useRef, useState } from "react";
import { PageHead } from "../components/InvCard.jsx";
import Explain from "../components/Explain.jsx";
import { fresh } from "../lib/api.js";

const EXAMPLES = ["PMMA extinction oxygen limit", "cool flame re-ignition", "smoke particle size Kapton", "flame spread over fabric"];

export default function Search({ level }) {
  const [q, setQ] = useState("");
  const [uploads, setUploads] = useState(false);
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const input = useRef(null);

  useEffect(() => { input.current?.focus(); }, []);

  async function run(query = q) {
    if (query.trim().length < 2) return;
    setQ(query); setBusy(true); setError(null);
    try {
      setRes(await fresh(`/search?k=10&include_unreviewed=${uploads}&q=${encodeURIComponent(query.trim())}`));
    } catch (e) { setError(e.message); }
    setBusy(false);
  }

  return (
    <div className="page">
      <PageHead title="Search the reports" sub="Finds the passages that answer your words or their meaning, in NASA's reports (and your uploads, if you tick the box). Every hit links to its page."
                right={<Explain level={level} steps={[
                  { title: "Ask in your own words", text: <>Type a question the way you'd ask a person, like <em>"why do fires burn differently in space?"</em>. No special keywords needed.</> },
                  { title: "Words and meaning", text: <>We search <strong>NASA's reports</strong> two ways: passages that use <strong>your words</strong>, and passages that <strong>mean the same thing</strong> in different words. Each result is tagged with how it matched.</> },
                  { title: "Check it yourself", text: <>Every result shows the <strong>report and page</strong> it comes from. Click it to open the real NASA document at that page.</> },
                ]} />}>
        <form className="field" onSubmit={(e) => { e.preventDefault(); run(); }}>
          <input ref={input} type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. lowest oxygen for acrylic in microgravity" aria-label="Search the reports" />
          <button className="btn" type="submit" disabled={busy}>{busy ? "Searching…" : "Search"}</button>
          <label className="chip" style={{ cursor: "pointer" }}><input type="checkbox" checked={uploads} onChange={(e) => setUploads(e.target.checked)} style={{ accentColor: "var(--ember)" }} /> include my unreviewed uploads</label>
        </form>
        {!res && <div className="chips">{EXAMPLES.map((x) => <button key={x} type="button" className="chip" onClick={() => run(x)}>{x}</button>)}</div>}
        {error && <p className="cav">Search failed: {error}</p>}
        {res && <p className="tool" style={{ marginBottom: 10 }}>{res.results.length} passages · {res.mode === "hybrid" ? "words + meaning" : res.mode}</p>}
        <div className="list">
          {res?.results.map((h, i) => (
            <article key={i} className="result">
              {h.url && !h.url.startsWith("/uploads/")
                ? <a href={h.url} target="_blank" rel="noreferrer"><cite>{h.cite} ↗</cite></a>
                : <a href="#/uploads"><cite>{h.cite}</cite></a>}
              <p>{h.text.length > 600 ? h.text.slice(0, 600) + "…" : h.text}</p>
              <div className="tags">
                {h.by_words && <span className="tag">matches words</span>}
                {h.by_meaning && <span className="tag">matches meaning</span>}
                {h.origin === "upload" && <span className="tag">your upload · {h.status}</span>}
              </div>
            </article>
          ))}
        </div>
      </PageHead>
    </div>
  );
}
