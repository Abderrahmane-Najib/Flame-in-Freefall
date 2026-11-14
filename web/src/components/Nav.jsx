import Avatar, { GUIDES } from "./Avatar.jsx";

const LEVELS = [
  ["explorer", "Explorer", "Plain language"],
  ["student", "Student", "Exact numbers"],
  ["researcher", "Researcher", "Full detail"],
];

const S = { width: 18, height: 18, viewBox: "0 0 18 18" };
const sw = { stroke: "currentColor", strokeWidth: 1.6, fill: "none" };
const LINKS = [
  ["home", "Home", <path d="M2 8l7-6 7 6v8H2z" {...sw} />],
  ["experiments", "Experiments", <>{[[2, 2], [10, 2], [2, 10], [10, 10]].map(([x, y]) => <rect key={x + "" + y} x={x} y={y} width="6" height="6" rx="1.5" {...sw} />)}</>],
  ["coverage", "Coverage map", <><path d="M2 16V2M2 16h14" {...sw} /><circle cx="6" cy="10" r="1.5" fill="currentColor" /><circle cx="10" cy="6" r="1.5" fill="currentColor" /><circle cx="13" cy="11" r="1.5" fill="currentColor" /></>],
  ["graph", "Knowledge graph", <><circle cx="4" cy="4" r="2" {...sw} /><circle cx="14" cy="6" r="2" {...sw} /><circle cx="8" cy="14" r="2" {...sw} /><path d="M6 5l6 1M5 6l2 6M13 8l-4 5" {...sw} /></>],
  ["compare", "Compare", <path d="M5 3v12M13 3v12M2 6h6M10 12h6" {...sw} />],
  ["predict", "Predict", <path d="M2 14l4-5 3 3 6-8" {...sw} />],
  ["lab", "Flame Lab", <path d="M9 2c3 4 5 6 5 9a5 5 0 0 1-10 0c0-3 2-5 5-9z" {...sw} />],
  ["uploads", "My reports", <><path d="M4 2h7l3 3v11H4z" {...sw} /><path d="M9 13V7M6.5 9.5L9 7l2.5 2.5" {...sw} /></>],
  ["data", "Data & method", <><ellipse cx="9" cy="4" rx="6" ry="2.2" {...sw} /><path d="M3 4v10c0 1.2 2.7 2.2 6 2.2s6-1 6-2.2V4" {...sw} /></>],
];

export default function Nav({ route, level, setLevel, onNavigate }) {
  return (
    <nav className="nav" aria-label="Main" onClick={(e) => e.target.closest("a") && onNavigate()}>
      <div className="logo">
        <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><path d="M13 2c5 6 8 10 8 14a8 8 0 0 1-16 0c0-4 3-8 8-14z" fill="var(--ember)" /><circle cx="13" cy="16" r="3.6" fill="var(--panel)" /></svg>
        Ghostflame
      </div>
      {LINKS.map(([id, label, icon]) => (
        <a key={id} href={"#/" + id} className={route === id ? "on" : undefined} aria-current={route === id ? "page" : undefined}>
          <svg {...S}>{icon}</svg>{label}
        </a>
      ))}
      <div className="lvl" role="radiogroup" aria-label="Explanation level">
        <h5>Explain it at</h5>
        {LEVELS.map(([value, b, small]) => (
          <label key={value}>
            <input type="radio" name="lvl" value={value} checked={level === value} onChange={() => setLevel(value)} />
            <Avatar level={value} size={28} title={GUIDES[value].role} />
            <span><b>{b}</b><small>{small}</small></span>
          </label>
        ))}
        <p className="credit">Data and photos: NASA PSI and NASA Image Library, public domain. Not affiliated with or endorsed by NASA.</p>
      </div>
    </nav>
  );
}
