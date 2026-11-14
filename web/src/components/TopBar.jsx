export default function TopBar({ mode, setMode, onMenu, onSearch }) {
  return (
    <div className="top">
      <button className="menu" type="button" aria-label="Open menu" onClick={onMenu}>
        <svg width="18" height="18" viewBox="0 0 18 18"><path d="M2 4h14M2 9h14M2 14h14" stroke="currentColor" strokeWidth="1.8" /></svg>
      </button>
      <button className="search" aria-label="Search" type="button" onClick={onSearch}>
        <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" strokeWidth="1.6" /><path d="M11 11l3.5 3.5" stroke="currentColor" strokeWidth="1.6" /></svg>
        Search experiments, fuels, conditions<kbd>⌘K</kbd>
      </button>
      <div className="seg" role="group" aria-label="Colour mode">
        {["light", "dark"].map((m) => (
          <button key={m} type="button" aria-pressed={mode === m} onClick={() => setMode(m)}>{m === "light" ? "Light" : "Dark"}</button>
        ))}
      </div>
      <button className="pill" type="button">EN ▾</button>
    </div>
  );
}
