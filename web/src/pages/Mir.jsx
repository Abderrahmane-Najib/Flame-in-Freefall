// Mir 1997: an interactive story of the fire aboard the Mir space station (replaces the Compare placeholder).
// 1. Intro "video": NASA public-domain photos with slow zoom/pan and captions (facts from the NASA 2022
//    retrospective and the photos' own NASA captions). Autoplays; pause, previous/next, skip.
// 2. Five decisions (story text word for word from the team prototype, lib/mirStory.js), each changing the
//    illustrated scene (components/MirScene.jsx, pixel-art crew in the prototype's style). Documented choices
//    follow the record; others show labelled, imagined consequences. 3. Debrief with every source.
import { useEffect, useState } from "react";
import { PageHead } from "../components/InvCard.jsx";
import MirScene from "../components/MirScene.jsx";
import STORY from "../lib/mirStory.js";

const RETRO = "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/";
const img = (id) => `https://images-assets.nasa.gov/image/${id}/${id}~large.jpg`;
const page = (id) => `https://images.nasa.gov/details/${id}`;

const SLIDES = [
  { id: "9702655", kicker: "Earth orbit · early 1997",
    text: "This is Mir, Russia's space station, photographed from Space Shuttle Atlantis in January 1997, a month before the fire.",
    credit: "NASA · STS-81 crew, January 1997" },
  { id: "sts081-369-003", kicker: "The people",
    text: "NASA astronaut Jerry Linenger (back row, left) arrived on Atlantis in January to live aboard with Mir commander Valeri Korzun and engineer Aleksandr Kaleri (both shown here).",
    credit: "NASA · Mir-22 and STS-81 crews in Mir's base block, January 1997" },
  { id: "NM23-48-003", kicker: "Six aboard",
    text: "In February, Vasili Tsibliyev and Aleksandr Lazutkin came up to take over, with Germany's Reinhold Ewald on a short visit. During a handover, six people lived aboard for a few weeks.",
    credit: "NASA · Tsibliyev outside Mir, April 1997. The Kvant-1 module is at lower left" },
  { id: "sts084-305-018", kicker: "Air for six",
    text: "Machines made oxygen by splitting water. With extra people aboard, the crew also burned canisters of a solid chemical: one canister gave one person's oxygen for a day. Mir had used them over 2,500 times without trouble.",
    credit: "NASA · inside a Mir node, May 1997" },
  { id: "s79e5216", kicker: "The lifeboats",
    text: "If they had to leave, two Soyuz capsules were docked, each with three seats. One of them was parked at the far end of the Kvant-1 module.",
    credit: "NASA · a Soyuz docked to Mir, September 1996" },
  { id: null, kicker: "Late February 1997 · after dinner",
    text: "Lazutkin lights an oxygen canister in Kvant-1. Something is wrong. Now you guide the crew.",
    credit: "" },
];
const SLIDE_S = 8;

function Intro({ onDone }) {
  const [i, setI] = useState(0);
  const [paused, setPaused] = useState(false);
  const [t, setT] = useState(0); // seconds into this slide
  const reduced = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (paused) return undefined;
    const id = setInterval(() => setT((x) => x + 0.1), 100);
    return () => clearInterval(id);
  }, [paused]);
  useEffect(() => {
    if (t < SLIDE_S) return;
    if (i < SLIDES.length - 1) { setI(i + 1); setT(0); } else setPaused(true);
  }, [t, i]);
  const go = (k) => { setI(Math.max(0, Math.min(SLIDES.length - 1, k))); setT(0); };
  const s = SLIDES[i], last = i === SLIDES.length - 1;

  return (
    <div className="mir-video" role="region" aria-label="Introduction: Mir in 1997">
      {SLIDES.map((x, k) => x.id && (
        <img key={x.id} src={img(x.id)} alt="" className={"mir-photo" + (k === i ? " on" : "") + (k % 2 ? " pan-l" : " pan-r")}
             style={{ animationPlayState: paused || reduced ? "paused" : "running" }} />
      ))}
      {!s.id && <div className="mir-ember" aria-hidden="true" />}
      <div className="mir-bars" aria-hidden="true">
        {SLIDES.map((_, k) => <span key={k}><i style={{ width: `${k < i ? 100 : k > i ? 0 : Math.min(100, (t / SLIDE_S) * 100)}%` }} /></span>)}
      </div>
      <div className="mir-cap" aria-live="polite">
        <span className="mir-kick">{s.kicker}</span>
        <p>{s.text}</p>
        {s.id && <a href={page(s.id)} target="_blank" rel="noreferrer">Photo: {s.credit} ↗</a>}
        <a href={RETRO} target="_blank" rel="noreferrer">Facts: NASA, "25 years ago: fire aboard Mir" (2022) ↗</a>
      </div>
      <div className="mir-vctl">
        <button type="button" onClick={() => go(i - 1)} disabled={!i} aria-label="Previous">‹</button>
        <button type="button" onClick={() => setPaused(!paused)} aria-label={paused ? "Play" : "Pause"}>{paused ? "▶" : "❚❚"}</button>
        <button type="button" onClick={() => go(i + 1)} disabled={last} aria-label="Next">›</button>
        <button type="button" className={last ? "mir-go" : "mir-skip"} onClick={onDone}>{last ? "Start the story →" : "Skip intro"}</button>
      </div>
    </div>
  );
}

function Source({ id }) {
  const s = STORY.sources[id];
  return s ? <a className="mir-src" href={s.url} target="_blank" rel="noreferrer" title={s.note}>{s.title} ↗</a> : null;
}

export default function Mir() {
  const [phase, setPhase] = useState("intro"); // intro | story | debrief
  const [stage, setStage] = useState(-1);      // -1 = briefing
  const [choice, setChoice] = useState(null);
  const [record, setRecord] = useState(false);
  const [trail, setTrail] = useState([]);      // first choice made at each stage
  const [page_, setPage] = useState(0);

  const st = STORY.stages[stage];
  const picked = st && choice != null ? st.choices[choice] : null;
  const goodIdx = st ? st.choices.findIndex((c) => c.good) : -1;

  function choose(k) {
    setChoice(k); setRecord(false);
    setTrail((tr) => { const n = [...tr]; if (n[stage] == null) n[stage] = k; return n; });
  }
  function next() {
    setChoice(null); setRecord(false);
    if (stage < STORY.stages.length - 1) setStage(stage + 1); else { setPhase("debrief"); setPage(0); }
  }
  function restart() { setPhase("story"); setStage(-1); setChoice(null); setTrail([]); setRecord(false); }

  useEffect(() => { // number keys choose while a decision is open
    if (phase !== "story" || !st || choice != null) return undefined;
    const h = (e) => { const n = +e.key; if (n >= 1 && n <= st.choices.length && !e.target.closest?.("input,textarea")) choose(n - 1); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }); // eslint-disable-line react-hooks/exhaustive-deps

  const pages = [...STORY.debrief, { title: "Sources", sources: true }];

  return (
    <div className="page">
      <PageHead title="Mir 1997: fire on a space station"
                sub="A real fire in orbit, told in five decisions. Choices that match the record follow what happened; others show clearly labelled, imagined consequences. Every step links to its NASA or ESA source.">
        {phase === "intro" && <Intro onDone={() => setPhase("story")} />}

        {phase !== "intro" && (
          <div className="mir-game">
            <div className="mir-stage">
              <MirScene stage={phase === "debrief" ? 3 : stage} choice={phase === "debrief" ? 1 : choice != null ? choice : null} />
              <div className="mir-steps" aria-label="Progress">
                {STORY.stages.map((s, k) => (
                  <span key={s.id} className={k < stage || phase === "debrief" ? "done" : k === stage ? "now" : ""}>{k + 1}. {s.label}</span>
                ))}
              </div>
            </div>

            <div className="panel mir-panel">
              {phase === "story" && stage === -1 && <>
                <span className="mir-kick">Prologue · a real event, illustrated</span>
                <h2>An ordinary evening changes.</h2>
                <p>{STORY.briefing}</p>
                <p className="tool">You guide the story, not a named astronaut. The scene is an illustration; the sequence is simplified.</p>
                <Source id="history" />
                <div className="mir-actions"><button type="button" className="mir-go" onClick={() => setStage(0)}>Begin the incident →</button>
                  <button type="button" onClick={() => setPhase("intro")}>Watch the intro again</button></div>
              </>}

              {phase === "story" && st && <>
                <span className="mir-kick">Decision {stage + 1} of {STORY.stages.length} · {st.label}</span>
                <h2>{st.title}</h2>
                <p>{st.body}</p>
                <div className="mir-choices" role="group" aria-label="Choices">
                  {st.choices.map((c, k) => (
                    <button key={k} type="button" aria-pressed={choice === k} disabled={choice != null && choice !== k}
                            className={choice === k ? (c.good ? "good" : "bad") : ""} onClick={() => choose(k)}>
                      <b>{k + 1}</b>{c.label}
                    </button>
                  ))}
                </div>

                {picked && (picked.good ? (
                  <div className="mir-out good">
                    <span className="mir-kick">Matches the record</span>
                    <p>{picked.result}</p>
                    <p><strong>What happened:</strong> {st.record}</p>
                    <p className="mir-lesson">{st.lesson}</p>
                    <Source id={st.source} />
                    <div className="mir-actions"><button type="button" className="mir-go" onClick={next}>
                      {stage < STORY.stages.length - 1 ? "Next decision →" : "See the debrief →"}</button></div>
                  </div>
                ) : (
                  <div className="mir-out bad">
                    <span className="mir-kick">Imagined · not what happened</span>
                    <p>{picked.result}</p>
                    {record && <p><strong>What happened:</strong> {st.record} <Source id={st.source} /></p>}
                    <div className="mir-actions">
                      <button type="button" onClick={() => setChoice(null)}>↶ Try another choice</button>
                      {!record && <button type="button" onClick={() => setRecord(true)}>Read what really happened</button>}
                      <button type="button" className="mir-go" onClick={() => choose(goodIdx)}>Follow the record →</button>
                    </div>
                  </div>
                ))}
              </>}

              {phase === "debrief" && <>
                <span className="mir-kick">Debrief · {page_ + 1} of {pages.length}</span>
                <h2>{pages[page_].title}</h2>
                {pages[page_].sources ? (
                  <ul className="mir-srcs">{Object.entries(STORY.sources).map(([id, s]) => (
                    <li key={id}><a href={s.url} target="_blank" rel="noreferrer">{s.title} ↗</a><small>{s.note}</small></li>))}
                    <li><a href="https://images.nasa.gov/" target="_blank" rel="noreferrer">Intro photos: NASA Image and Video Library (public domain) ↗</a></li>
                  </ul>
                ) : <><p>{pages[page_].text}</p><Source id={pages[page_].source} /></>}
                {page_ === 0 && trail.length > 0 && (
                  <p className="tool">Your first choices: {trail.map((k, s) => (STORY.stages[s].choices[k]?.good ? "✓" : "✗")).join(" ")} (✓ = matched the record on the first try)</p>
                )}
                <div className="mir-actions">
                  {page_ > 0 && <button type="button" onClick={() => setPage(page_ - 1)}>← Back</button>}
                  {page_ < pages.length - 1
                    ? <button type="button" className="mir-go" onClick={() => setPage(page_ + 1)}>Next →</button>
                    : <button type="button" className="mir-go" onClick={restart}>Replay the story</button>}
                </div>
              </>}
            </div>
          </div>
        )}
        <p className="cav" style={{ marginTop: 18 }}>A historical learning story, not a fire simulation or an emergency procedure. Figures, positions and timing are illustrations; dialogue and choices are original paraphrases of the NASA and ESA sources.</p>
      </PageHead>
    </div>
  );
}
