// The equipment cards and the Flame Lab teaser: editorial content (not live). Each claim was checked
// against its source on 14 Nov 2026 (the SAME table in the PDF, the FLEX counts in data/psi/clean/flex.csv).
const PSI = "https://psi.nasa.gov/geode-py/ws/studies/";
const SAME = PSI + "PSI-102/download?file=PSI-102_Reports_SAME_Final%20Science%20Report.pdf";
const BASS2 = PSI + "PSI-25/download?file=PSI-25_Reports_BASS-II%20Summary%20Report.pdf";
const FLEX_TABLE = PSI + "PSI-69/download?file=PSI-69_Experimental%20table_FLEX.csv";
const GUIDE = "https://www.nasa.gov/wp-content/uploads/2016/05/np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf";

export function Equipment() {
  const ic = { width: 22, height: 22, viewBox: "0 0 22 22", style: { color: "var(--accent-text)" } };
  const items = [
    [<><circle cx="8" cy="12" r="3" fill="#FF7A45" /><circle cx="14" cy="8" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.8" /></>,
      "Smoke detectors", "Smoke from Kapton and Teflon averages 105–205 nm, which the report says makes it challenging for light-scattering detectors.",
      [["SAME Final Science Report, Table 1, PDF p. 27", SAME + "#page=27"]]],
    [<><rect x="7" y="6" width="8" height="13" rx="3" fill="none" stroke="currentColor" strokeWidth="1.8" /><path d="M11 6V3h4" stroke="currentColor" strokeWidth="1.8" fill="none" /></>,
      "Extinguishers", "In near-lunar air, none of the 17 droplet fires went out by itself: 15 broke apart, 2 burned all their fuel.",
      [["FLEX test table · PSI-69", FLEX_TABLE]]],
    [<path d="M4 6h14M4 11h14M4 16h14" stroke="currentColor" strokeWidth="1.8" />,
      "Materials", "Acrylic plastic keeps burning down to 13.5% O₂ in microgravity, versus 15.4% on Earth.",
      [["BASS-II Summary Report, PDF p. 84", BASS2 + "#page=84"]]],
    [<path d="M3 8c4-3 8 3 12 0s4-1 4-1M3 14c4-3 8 3 12 0s4-1 4-1" stroke="currentColor" strokeWidth="1.8" fill="none" />,
      "Ventilation", "Materials burn at the lowest oxygen at about 10 cm/s airflow, typical of spacecraft ventilation.",
      [["BASS-II Summary Report, PDF p. 84", BASS2 + "#page=84"], ["NASA Researcher's Guide to Combustion, p. 31", GUIDE + "#page=31"]]],
  ];
  return (
    <section>
      <div className="sh"><div><h2>What it means for fire-safety equipment</h2><p>What the experiments teach the people designing detectors, extinguishers and habitats.</p></div></div>
      <div className="equip">
        {items.map(([icon, h, p, cites]) => (
          <article key={h} className="eq"><div className="ic"><svg {...ic}>{icon}</svg></div><h3>{h}</h3><p>{p}</p>
            <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 4 }}>
              {cites.map(([label, url]) => <a key={url} href={url} target="_blank" rel="noreferrer"><cite>{label} ↗</cite></a>)}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function FlameLab() {
  return (
    <section>
      <div className="lab">
        <div className="pic" role="img" aria-label="NASA photo: candle flame on Earth (left) and in microgravity (right)">
          <span style={{ left: 12 }}>Earth · 1 g</span><span style={{ right: 12 }}>Space · microgravity</span>
        </div>
        <div className="txt">
          <h2>The same candle, two different fires</h2>
          <p>On Earth hot air rises and stretches a flame into a teardrop. In space nothing rises, so the flame becomes a dim blue sphere. In the Flame Lab, watch real NASA test videos next to reconstructions built from their measurements, including the near-invisible cool flame.</p>
          <a className="btn" href="#/lab">Open the Flame Lab →</a>
          <small className="mono" style={{ color: "var(--faint)" }}>Photo: NASA Glenn (Lewis) Research Center, C-1998-485</small>
        </div>
      </div>
    </section>
  );
}
