// The level's guide as a full character (head from Avatar.jsx + arms, legs and a prop), animated in CSS
// (styles.css, "Guide characters"). Purely visual: it never says anything the page or the assistant didn't.
//   state: "idle"     floats, blinks, waves now and then
//          "thinking" hand on chin, eyes look around (the assistant is looking things up)
//          "talking"  mouth moves, hands gesture (an answer or a tour step is being shown)
// Explorer: astronaut helmet + jetpack (floats higher). Student: cap + book. Researcher: lab glasses + clipboard.
import { FLAME, GUIDES, Head } from "./Avatar.jsx";

const SKIN = "#F2A65A";

export default function Character({ level = "student", state = "idle", height = 120, title }) {
  const g = GUIDES[level] || GUIDES.student;
  return (
    <svg viewBox="0 0 120 160" height={height} width={height * 0.75} role="img" aria-label={title || g.role}
         className={`character ch-${level} av-${state}`}>
      <ellipse className="ch-shadow" cx="60" cy="153" rx="22" ry="4" fill="#000" opacity=".18" />
      <g className="ch-body">
        {level === "explorer" && (
          // jetpack behind the body, with two jets
          <g>
            <rect x="26" y="76" width="10" height="32" rx="5" fill="#AEB5D6" />
            <rect x="84" y="76" width="10" height="32" rx="5" fill="#AEB5D6" />
            <path className="ch-jet" d="M27 108q4 14 8 0z M85 108q4 14 8 0z" fill="#FFB347" />
          </g>
        )}
        <g className="ch-legs" stroke={SKIN} strokeWidth="5" strokeLinecap="round" fill="none">
          <path className="ch-leg-l" d="M51 110l-3 26" />
          <path className="ch-leg-r" d="M69 110l3 26" />
          <ellipse cx="46" cy="138" rx="6" ry="3.5" fill="#1B1E2E" stroke="none" />
          <ellipse cx="74" cy="138" rx="6" ry="3.5" fill="#1B1E2E" stroke="none" />
        </g>
        <g transform="translate(-2.4 10) scale(2.6)">
          <path d={FLAME} fill="none" stroke={SKIN} strokeWidth="2.2" />{/* outline: visible on light backgrounds */}
          <Head level={level} state={state} />
        </g>
        <g className="ch-arm-l">
          <path d="M33 90q-9 6-11 20" stroke={SKIN} strokeWidth="5" strokeLinecap="round" fill="none" />
          {level === "student" && (
            // a book
            <g transform="rotate(-12 20 112)">
              <rect x="10" y="104" width="20" height="15" rx="2" fill="#3a62ff" />
              <rect x="12" y="106" width="16" height="11" rx="1" fill="#F4F6FB" />
              <path d="M20 106v11" stroke="#3a62ff" strokeWidth="1.2" />
            </g>
          )}
          {level === "researcher" && (
            // a clipboard
            <g transform="rotate(-8 20 110)">
              <rect x="12" y="98" width="16" height="21" rx="2" fill="#B98A5E" />
              <rect x="14" y="102" width="12" height="15" rx="1" fill="#F4F6FB" />
              <rect x="16.5" y="96.5" width="7" height="4" rx="1.5" fill="#7A8199" />
              <path d="M16 106h8M16 109.5h8M16 113h5" stroke="#9AA3B8" strokeWidth="1" />
            </g>
          )}
          <circle cx="22" cy="110" r="4.5" fill="#FFF3D6" stroke={SKIN} strokeWidth="2" />
        </g>
        <g className="ch-arm-r">
          <path d="M87 90q9 6 11 20" stroke={SKIN} strokeWidth="5" strokeLinecap="round" fill="none" />
          <circle cx="98" cy="110" r="4.5" fill="#FFF3D6" stroke={SKIN} strokeWidth="2" />
        </g>
      </g>
    </svg>
  );
}
