// Data & method: what is in the database (GET /health) and how the numbers are made.
import { useEffect, useState } from "react";
import { PageHead } from "../components/InvCard.jsx";
import { fresh } from "../lib/api.js";
import { fmt } from "../lib/habitats.js";

const ROWS = [
  ["investigations", "Investigation cards (NASA PSI + approved uploads)"],
  ["test_rows", "Cleaned test rows"],
  ["habitats", "Habitat atmospheres"],
  ["documents", "Reports and papers"],
  ["pages", "Report pages"],
  ["chunks", "Searchable passages"],
  ["chunks_embedded", "Passages with a meaning vector (BGE-M3)"],
];

const METHOD = [
  ["Source", "NASA Physical Sciences Informatics (PSI): 24 combustion investigations, their test tables and reports. Public domain."],
  ["Habitat air", "A test counts for a habitat only when both chamber O₂ and pressure were measured inside its box. Moon base: O₂ ≥ 30% at ≤ 70.3 kPa. Mars uses the Moon air (team assumption)."],
  ["Near-lunar", "O₂ ≥ 30% at 70.3–72.5 kPa (17 FLEX tests): shown apart, never counted as lunar."],
  ["Burner stream", "O₂ blown out of a burner (inverse flames) is not cabin air and is never compared with it."],
  ["Gravity", "Every test ran in microgravity. Nothing here is a Moon- or Mars-gravity result."],
  ["Assistant", "Answers only from tool results (report search, cards, test tables) and cites each claim. Model: gpt-oss-120b on Groq."],
  ["Search", "Full-text and meaning (BGE-M3 embeddings) merged with Reciprocal Rank Fusion; every passage keeps its PDF page."],
  ["Predictor", "PMMA boundary = NASA's own fitted equation (BASS-II Eq. 6.1); not trained by us."],
];

export default function DataMethod() {
  const [h, setH] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { fresh("/health").then(setH).catch((e) => setError(e.message)); }, []);
  return (
    <div className="page">
      <PageHead title="Data & method" sub="What Etna holds, and the rules every number follows."
                right={<a href="/docs" target="_blank" rel="noreferrer">API docs ↗</a>}>
        <div className="cols">
          <div className="list">
            {METHOD.map(([k, v]) => <div key={k} className="result"><b>{k}</b><p>{v}</p></div>)}
          </div>
          <aside className="panel">
            <h3>In the database now</h3>
            {error && <p className="cav">API unreachable: {error}</p>}
            {!h && !error && <p className="loading">Loading…</p>}
            {h && <table className="table"><tbody>
              {ROWS.map(([k, l]) => <tr key={k}><td>{l}</td><td className="n">{fmt(h.database[k])}</td></tr>)}
            </tbody></table>}
          </aside>
        </div>
      </PageHead>
    </div>
  );
}
