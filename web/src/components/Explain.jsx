// "Explain it simply": a small button next to the page title (Explorer and Student levels only). It opens a short
// step-by-step tour in a speech bubble from the level's guide; a step can highlight part of the page (onStep).
// Written by the team (not generated), so it never adds new facts: it explains what the page already shows.
import { useEffect, useRef, useState } from "react";
import Avatar, { GUIDES } from "./Avatar.jsx";

export const SIMPLE_LEVELS = new Set(["explorer", "student"]);

/** steps: [{ title, text, focus }] — focus is passed to onStep so the page can highlight that part. */
export default function Explain({ level, steps, onStep }) {
  const [open, setOpen] = useState(false);
  const [i, setI] = useState(0);
  const box = useRef(null);

  useEffect(() => { onStep?.(open ? steps[i]?.focus ?? null : null); }, [open, i]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!open) return;
    const away = (e) => { if (!box.current?.contains(e.target)) setOpen(false); };
    const esc = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", away);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("mousedown", away); document.removeEventListener("keydown", esc); };
  }, [open]);

  if (!SIMPLE_LEVELS.has(level) || !steps?.length) return null;
  const step = steps[i];
  const last = i === steps.length - 1;

  return (
    <div className="xp" ref={box}>
      <button type="button" className="xp-btn" aria-expanded={open} onClick={() => { setOpen(!open); setI(0); }}>
        <Avatar level={level} size={26} /><span>{open ? "Close" : "Explain it simply"}</span>
      </button>
      {open && (
        <div className="xp-pop" role="dialog" aria-label="Simple explanation">
          <div className="xp-head">
            <Avatar level={level} size={34} />
            <div><b>{step.title}</b><small>{GUIDES[level].role} · step {i + 1} of {steps.length}</small></div>
          </div>
          <div className="xp-text">{step.text}</div>
          <div className="xp-foot">
            <div className="xp-dots">{steps.map((_, k) => (
              <button key={k} type="button" aria-label={`Step ${k + 1}`} aria-current={k === i} onClick={() => setI(k)} />
            ))}</div>
            <div className="xp-nav">
              {i > 0 && <button type="button" onClick={() => setI(i - 1)}>Back</button>}
              <button type="button" className="p" onClick={() => (last ? setOpen(false) : setI(i + 1))}>{last ? "Got it" : "Next"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
