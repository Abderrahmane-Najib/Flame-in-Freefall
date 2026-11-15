// All investigations, filtered by the API (GET /investigations?fuel_type=&safety_job=).
import { useEffect, useState } from "react";
import InvCard, { PageHead } from "../components/InvCard.jsx";
import { get } from "../lib/api.js";

const FUELS = [[null, "All"], ["solid", "Solid materials"], ["droplet", "Liquid droplets"], ["gas", "Gas flames"],
  ["smoke", "Smoke & detection"], ["ground", "Ground studies"]];
const JOBS = [[null, "Any job"], ["prevention", "Prevention"], ["detection", "Detection"], ["suppression", "Suppression"]];
const FUEL_BADGE = Object.fromEntries(FUELS.slice(1));

export default function Experiments({ onOpen }) {
  const [fuel, setFuel] = useState(null);
  const [job, setJob] = useState(null);
  const [list, setList] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const q = new URLSearchParams();
    if (fuel) q.set("fuel_type", fuel);
    if (job) q.set("safety_job", job);
    setError(null);
    get("/investigations" + (q.size ? "?" + q : "")).then(setList).catch((e) => setError(e.message));
  }, [fuel, job]);

  return (
    <div className="page">
      <PageHead title="Experiments" sub="Every NASA PSI combustion investigation, plus the reports you uploaded and approved. Open one for its sourced findings and test data.">
        <div className="chips" role="group" aria-label="Fuel family">
          {FUELS.map(([id, label]) => <button key={label} className="chip" type="button" aria-pressed={fuel === id} onClick={() => setFuel(id)}>{label}</button>)}
        </div>
        <div className="chips" role="group" aria-label="Fire-safety job">
          {JOBS.map(([id, label]) => <button key={label} className="chip" type="button" aria-pressed={job === id} onClick={() => setJob(id)}>{label}</button>)}
        </div>
        {error && <p className="cav">Could not load: {error}</p>}
        {!list && !error && <p className="loading">Loading…</p>}
        {list && !list.length && <p className="loading">No experiment matches these filters.</p>}
        <div className="grid">
          {list?.map((inv) => (
            <InvCard key={inv.id} inv={inv} onOpen={onOpen}
                     badge={<span className="badge b-none">{FUEL_BADGE[inv.fuel_type] || inv.fuel_type}</span>}
                     corner={inv.lunar_air_tests ? `${inv.lunar_air_tests} lunar-air tests` : null} />
          ))}
        </div>
      </PageHead>
    </div>
  );
}
