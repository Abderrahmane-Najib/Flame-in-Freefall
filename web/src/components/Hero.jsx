const BUTTONS = [
  ["iss", "ISS · spacecraft", "21% O₂ · 101 kPa"],
  ["moon", "Moon base", "≥30% O₂ · ≤70 kPa"],
  ["rover", "Pressurized rover", "≥30% O₂ · ≤70 kPa"],
  ["mars", "Mars habitat", "air not defined yet"],
];
const PHOTOS = [
  ["iss", { backgroundImage: "url(/img/iss.jpg)" }],
  ["moon", { backgroundImage: "url(/img/moon.jpg)", backgroundPosition: "center 70%" }],
  ["mars", { backgroundImage: "url(/img/mars.jpg)", backgroundSize: "60%", backgroundPosition: "110% 40%", backgroundRepeat: "no-repeat", backgroundColor: "#000" }],
];

export default function Hero({ hab, habitat, setHab, kpis, level, children }) {
  return (
    <header className="hero">
      {PHOTOS.map(([id, style]) => <div key={id} className={"photo" + (habitat.photo === id ? " on" : "")} style={style} />)}
      <h1>Where will your crew live?</h1>
      <p className="q">Pick a habitat. Etna shows what NASA's fire experiments say about its air.</p>
      <div className="habs" role="group" aria-label="Habitat">
        {BUTTONS.map(([id, b, span]) => (
          <button key={id} className="hab" type="button" aria-pressed={hab === id} onClick={() => setHab(id)}>
            <b>{b}</b><span>{span}</span>
          </button>
        ))}
      </div>
      <div className={"mars" + (hab === "mars" ? " on" : "")}>Mars habitat air isn't defined yet, so Etna shows it as Moon-like air.</div>
      <div className="kpis">
        {kpis.map(([value, label, text, cite, url, warn]) => (
          <div key={label} className={"kpi" + (warn ? " warn" : "")}>
            <b>{value}</b><span className="l">{label}</span><p>{text[level]}</p>
            {url ? <a href={url} target="_blank" rel="noreferrer">{cite} ↗</a> : <a>{cite}</a>}
          </div>
        ))}
      </div>
      {children /* the totals strip (Strip.jsx), inside the photo */}
      <span className="photocred">Photo: {habitat.cred}</span>
    </header>
  );
}
