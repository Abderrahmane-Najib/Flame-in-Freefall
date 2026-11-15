// The assistant's look for each explanation level: the Ghostflame flame dressed as a guide, a teacher or a
// scientist. Purely visual (the answer rules are the same for everyone).
export const GUIDES = {
  explorer: { name: "space guide", role: "Your space guide", bg: "var(--lime)", greet: "Hi! I'm your space guide. Ask me anything about fire in space, I'll keep it simple and show where every fact comes from." },
  student: { name: "teacher", role: "Your teacher", bg: "var(--ember)", greet: "Hello! I'm your teacher for today. Ask me about NASA's fire experiments and I'll explain step by step, with the source of every fact." },
  researcher: { name: "research colleague", role: "Your research colleague", bg: "var(--cyan)", greet: "Hi. I answer from NASA's combustion reports and test tables, with conditions, counts and a source for every claim." },
};

// Animated parts carry av-* classes (styles.css): eyes blink, flame flickers, mouth talks.
function Face({ talking }) {
  return (
    <>
      <g className="av-eyes">
        <circle cx="20.6" cy="29.5" r="1.7" fill="#1B1E2E" />
        <circle cx="27.4" cy="29.5" r="1.7" fill="#1B1E2E" />
      </g>
      <circle cx="18.3" cy="32.6" r="1.6" fill="#FF9B7A" opacity=".55" />
      <circle cx="29.7" cy="32.6" r="1.6" fill="#FF9B7A" opacity=".55" />
      {talking
        ? <ellipse className="av-mouth" cx="24" cy="34.2" rx="1.8" ry="1.4" fill="#1B1E2E" />
        : <path d="M22 33.3q2 1.8 4 0" fill="none" stroke="#1B1E2E" strokeWidth="1.3" strokeLinecap="round" />}
    </>
  );
}

export const FLAME = "M24 9c7 8 11.5 13 11.5 19.5a11.5 11.5 0 0 1-23 0C12.5 22 17 17 24 9z";

// state: "idle" (blinks, flame flickers), "thinking" (looks up, brighter flame), "talking" (mouth moves),
// "still" (no animation: older chat messages).
export default function Avatar({ level = "student", size = 32, title, state = "idle" }) {
  const g = GUIDES[level] || GUIDES.student;
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" role="img" aria-label={title || g.role} className={`avatar av-${state}`}>
      <circle cx="24" cy="24" r="24" fill={g.bg} />
      {level === "researcher" && (
        // lab coat collar
        <path d="M10 48l7-11 7 6 7-6 7 11z" fill="#F4F6FB" stroke="#C9D0E0" strokeWidth=".8" />
      )}
      <Head level={level} state={state} />
    </svg>
  );
}

/** The flame guide's head and face with the level's accessories, in a 48 x 48 frame (also used by Character.jsx). */
export function Head({ level, state }) {
  return (
    <>
      <g className="av-flame">
        <path d={FLAME} fill="#FFF3D6" />
        <path className="av-glow" d="M24 19c3.5 4 5.5 6.6 5.5 9.4a5.5 5.5 0 0 1-11 0c0-2.8 2-5.4 5.5-9.4z" fill="#FFC27A" opacity=".45" />
        <Face talking={state === "talking"} />
      </g>
      {level === "explorer" && (
        // astronaut helmet + antenna light
        <>
          <circle cx="24" cy="27" r="15.5" fill="rgba(255,255,255,.14)" stroke="#fff" strokeWidth="1.8" />
          <path d="M14.5 21.5a11 11 0 0 1 6-6.5" fill="none" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" opacity=".8" />
          <path d="M33 13.5l3-4" stroke="#fff" strokeWidth="1.5" /><circle className="av-light" cx="36.5" cy="8.8" r="1.8" fill="#FFD166" />
        </>
      )}
      {level === "student" && (
        // round glasses + graduation cap with tassel
        <>
          <circle cx="20.6" cy="29.5" r="3.2" fill="none" stroke="#1B1E2E" strokeWidth="1.2" />
          <circle cx="27.4" cy="29.5" r="3.2" fill="none" stroke="#1B1E2E" strokeWidth="1.2" />
          <path d="M23.8 29.3h0.4" stroke="#1B1E2E" strokeWidth="1.2" />
          <path d="M12 12.5L24 7l12 5.5-12 5.5z" fill="#1B1E2E" />
          <path d="M17 15v3.5c0 1.6 3.1 2.8 7 2.8s7-1.2 7-2.8V15" fill="#1B1E2E" />
          <g className="av-tassel"><path d="M34 13.5v6" stroke="#FFD166" strokeWidth="1.2" /><circle cx="34" cy="20.3" r="1.2" fill="#FFD166" /></g>
        </>
      )}
      {level === "researcher" && (
        // rectangular lab glasses
        <>
          <rect x="16.8" y="26.8" width="7" height="5.2" rx="1.6" fill="rgba(200,230,255,.35)" stroke="#1B1E2E" strokeWidth="1.2" />
          <rect x="24.2" y="26.8" width="7" height="5.2" rx="1.6" fill="rgba(200,230,255,.35)" stroke="#1B1E2E" strokeWidth="1.2" />
        </>
      )}
    </>
  );
}
