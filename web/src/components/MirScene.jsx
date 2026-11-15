// Mir 1997 scene (pages/Mir.jsx): an illustrated cutaway of the Kvant-1 cabin, the escape-route map and the
// lessons board. Every decision changes what is drawn, so the consequence of a choice is visible:
//   breathing  wait / ignore smoke -> haze fills the cabin, figures fade  | masks -> masks + hoses
//   teamwork   coordinated -> held responder + chain passing extinguishers | alone -> spray recoil pushes him away
//              "one spray ends it" -> spraying stops, the flame keeps burning
//   escape     map: one Soyuz for six -> 3 without a seat | "two exits" -> blocked path | reassess -> open vs blocked
//   recovery   haze clears + health checks (documented) | haze stays (imagined branches)
//   learning   checklist: which lessons each plan covers
// Illustration only: positions, sizes and timing are schematic (story text and sources: lib/mirStory.js).
import { useEffect, useRef } from "react";

const W = 960, H = 540;
export const CREW = [ // symbolic figures: clothing colour identifies the person, not a uniform
  { name: "Korzun", c: "#e4572e" }, { name: "Kaleri", c: "#f2a541" }, { name: "Linenger", c: "#3fa7d6" },
  { name: "Tsibliyev", c: "#9b5de5" }, { name: "Lazutkin", c: "#59cd90" }, { name: "Ewald", c: "#f15bb5" },
];
const NOZZLE = { x: 790, y: 300 };

// Where the six figures float, per situation (x, y, rotation in degrees)
const POSES = {
  calm:   [[260, 250, -8], [340, 330, 10], [430, 230, 4], [520, 320, -12], [610, 250, 6], [190, 350, 14]],
  alarm:  [[330, 230, -20], [250, 330, 18], [420, 300, -6], [170, 240, 12], [500, 350, 25], [110, 330, -16]],
  // Korzun (0) at the fire, Linenger (2) holding him, the others pass extinguishers: Ewald → Lazutkin → Tsibliyev → Kaleri
  chain:  [[565, 300, 80], [450, 262, 10], [522, 318, 72], [390, 318, -12], [330, 250, 14], [260, 310, -8]],
  alone:  [[565, 300, 80], [150, 250, 10], [200, 340, -14], [110, 330, 18], [240, 220, -6], [90, 240, 12]],
  after:  [[300, 250, -6], [380, 330, 10], [460, 240, 6], [540, 320, -10], [620, 250, 4], [220, 340, 12]],
};

function scenario(stage, choice) {
  const s = { view: "cabin", pose: "calm", fire: 0, haze: 0, masks: false, spray: false, label: "", warn: false };
  if (stage === -1) return { ...s, label: "Kvant-1 · an ordinary evening" };
  if (stage === 0) {
    Object.assign(s, { pose: "alarm", fire: 1, haze: 0.28, label: "A canister erupts: a jet of flame, sparks and smoke" });
    if (choice === 1) Object.assign(s, { masks: true, haze: 0.4, label: "Masks on: the crew can breathe and act" });
    if (choice === 0) Object.assign(s, { haze: 0.82, warn: true, label: "Imagined: waiting — smoke fills the cabin, no fresh air to reach" });
    if (choice === 2) Object.assign(s, { haze: 0.72, warn: true, pose: "chain", label: "Imagined: fighting the fire without breathing protection" });
  } else if (stage === 1) {
    Object.assign(s, { pose: "alarm", fire: 1, haze: 0.45, masks: true, label: "Masks on. Now the fire itself" });
    if (choice === 0) Object.assign(s, { pose: "chain", spray: "team", fire: 0.75, label: "Korzun sprays, Linenger holds him steady, the others pass extinguishers" });
    if (choice === 1) Object.assign(s, { pose: "alone", spray: "alone", warn: true, label: "Imagined: nobody holds him — the spray's push sends him drifting away" });
    if (choice === 2) Object.assign(s, { pose: "chain", spray: "once", warn: true, label: "Imagined: one short spray, then waiting — the flame keeps burning" });
  } else if (stage === 2) {
    Object.assign(s, { view: "map", label: "Two Soyuz, three seats each. The fire is in Kvant-1" });
    if (choice === 0) Object.assign(s, { warn: true, label: "Imagined plan: all six head for one Soyuz — three seats are missing" });
    if (choice === 1) Object.assign(s, { warn: true, label: "Imagined plan: counting two exits — but one route runs through the fire" });
    if (choice === 2) Object.assign(s, { label: "Documented hazard: one Soyuz cut off. The crew reassessed and stayed aboard" });
  } else if (stage === 3) {
    Object.assign(s, { pose: "after", haze: 0.38, masks: true, label: "The flame is out. Smoke is still in the air" });
    if (choice === 1) Object.assign(s, { recover: true, label: "Life support cleans the air over hours; the crew's health is checked" });
    if (choice === 0) Object.assign(s, { haze: 0.38, masks: false, warn: true, label: "Imagined: masks off because it looks clearer — the smoke is still there" });
    if (choice === 2) Object.assign(s, { clock: true, warn: true, label: "Imagined: a fixed wait, no checks — nobody knows if the air is clean" });
  } else if (stage === 4) {
    Object.assign(s, { view: "board", label: "Back on Earth: which plan covers the lessons?" });
  }
  return s;
}

/** What the scene shows for this decision and choice (the page prints it as the caption under the screen). */
export function sceneInfo(stage, choice) { const s = scenario(stage, choice); return { label: s.label, warn: s.warn, view: s.view }; }

const BOARD = [ // lessons checklist per choice of the last decision: 1 covered, 0 missing, null not addressed
  { label: "Equipment easy to reach and use", v: [0, 0, 1] },
  { label: "Hands-on drills, as a team", v: [0, 1, 1] },
  { label: "Cause still under investigation", v: [null, 0, 1] },
];

// compact (phones): the caption is shown by the page as text, and crew names are drawn larger.
export default function MirScene({ stage, choice, paused, compact = false }) {
  const ref = useRef(null);
  const st = useRef({ stage, choice, paused, t0: performance.now() });
  useEffect(() => { Object.assign(st.current, { stage, choice, t0: performance.now() }); }, [stage, choice]);
  useEffect(() => { st.current.paused = paused; }, [paused]);
  useEffect(() => { st.current.compact = compact; }, [compact]);

  useEffect(() => {
    const cv = ref.current, ctx = cv.getContext("2d");
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    cv.width = 640; cv.height = 360; ctx.setTransform(640 / W, 0, 0, 640 / W, 0, 0); // low resolution: pixel-art look
    const smoke = [], sparks = [], foam = [];
    const pos = POSES.calm.map((p) => [...p]);
    let haze = 0, fire = 0, raf, last = performance.now(), clock = 0, drift = 0;

    const draw = (now) => {
      const S = st.current, dt = S.paused ? 0 : Math.min(0.05, (now - last) / 1000);
      last = now; clock += dt;
      const sc = scenario(S.stage, S.choice), age = (now - S.t0) / 1000;
      ctx.clearRect(0, 0, W, H);
      if (sc.view === "map") drawMap(ctx, S.choice, age, reduced);
      else if (sc.view === "board") drawBoard(ctx, S.choice, age);
      else {
        // ease the fire, haze and figures toward this situation
        let fireTarget = sc.fire;
        if (sc.spray === "team") fireTarget = Math.max(0.15, 1 - age / 9);   // shrinks slowly; it never vanishes at once
        const k = reduced ? 1 : Math.min(1, dt * 1.6);
        fire += (fireTarget - fire) * k;
        let hazeTarget = sc.haze;
        if (sc.recover) hazeTarget = Math.max(0.05, 0.38 - age * 0.05);
        haze += (hazeTarget - haze) * (reduced ? 1 : Math.min(1, dt * 0.8));
        POSES[sc.pose].forEach((p, i) => {
          let tx = p[0], ty = p[1];
          if (sc.spray === "alone" && i === 0) { drift = Math.min(1, age / 4); tx = 565 - 300 * drift; ty = 300 - 60 * drift; }
          const f = reduced ? 1 : Math.min(1, dt * 1.8);
          pos[i][0] += (tx - pos[i][0]) * f; pos[i][1] += (ty - pos[i][1]) * f;
          const rot = sc.spray === "alone" && i === 0 ? 80 + 220 * drift : p[2];
          pos[i][2] += (rot - pos[i][2]) * f;
        });
        const spraying = sc.spray === "team" || (sc.spray === "alone" && age < 3) || (sc.spray === "once" && age < 1.6);
        step(dt, fire, spraying, sc.spray === "alone" ? 1 : 0);
        drawCabin(ctx, clock);
        drawSmoke(ctx);
        drawFire(ctx, fire, clock);
        drawCrew(ctx, pos, sc, clock, haze, spraying, S.compact);
        drawFoam(ctx);
        // overall haze: the cabin fades behind smoke
        if (haze > 0.01) { ctx.fillStyle = `rgba(120,118,112,${haze * 0.75})`; ctx.fillRect(0, 0, W, H); }
        if (sc.recover) drawChecks(ctx, pos, age);
        if (sc.clock) drawClock(ctx, age);
        if (sc.spray === "team") drawHandoff(ctx, pos, clock);
      }
      if (!S.compact) caption(ctx, sc.label, sc.warn);
      raf = requestAnimationFrame(draw);
    };

    function step(dt, f, spraying, alone) {
      if (!dt) return;
      if (f > 0.05) {
        for (let i = 0; i < 3 * f; i++) smoke.push({ x: NOZZLE.x - 80 * f - Math.random() * 120 * f, y: NOZZLE.y + (Math.random() - 0.5) * 30,
          vx: -20 - Math.random() * 40, vy: (Math.random() - 0.5) * 30, r: 10 + Math.random() * 12, a: 0.35 });
        for (let i = 0; i < 4 * f; i++) sparks.push({ x: NOZZLE.x - 10, y: NOZZLE.y, vx: -150 - Math.random() * 220, vy: (Math.random() - 0.5) * 160, life: 0.6 + Math.random() * 0.6 });
      }
      if (spraying) {
        const k = pos[0], ang = alone ? Math.PI * (0.05 + Math.random() * 0.4) - Math.PI * 0.2 * (1 - Math.min(1, drift * 2)) : (Math.random() - 0.5) * 0.25;
        for (let i = 0; i < 5; i++) foam.push({ x: k[0] + 24, y: k[1] - 6, vx: Math.cos(ang) * (260 + Math.random() * 80), vy: Math.sin(ang) * 260 + (Math.random() - 0.5) * 40, life: 0.9 });
      }
      for (const p of smoke) { p.x += p.vx * dt; p.y += p.vy * dt; p.r += 14 * dt; p.vx *= 0.99; p.a -= dt * 0.035; }
      for (const p of sparks) { p.x += p.vx * dt; p.y += p.vy * dt; p.life -= dt; }
      for (const p of foam) { p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= 0.97; p.vy *= 0.97; p.life -= dt; }
      prune(smoke, (p) => p.a > 0 && p.x > 30); prune(sparks, (p) => p.life > 0); prune(foam, (p) => p.life > 0 && p.x < NOZZLE.x + 20);
      if (smoke.length > 420) smoke.splice(0, smoke.length - 420);
    }
    function drawSmoke(c) { for (const p of smoke) { c.fillStyle = `rgba(150,146,140,${Math.max(0, p.a)})`; c.beginPath(); c.arc(p.x, p.y, p.r, 0, 7); c.fill(); } }
    function drawFoam(c) { for (const p of foam) { c.fillStyle = `rgba(240,248,255,${p.life})`; c.beginPath(); c.arc(p.x, p.y, 3.5, 0, 7); c.fill(); } }
    function drawFire(c, f, t) {
      for (const p of sparks) { c.fillStyle = `rgba(255,${180 + Math.random() * 60},90,${Math.min(1, p.life * 1.5)})`; c.fillRect(p.x, p.y, 2.5, 2.5); }
      if (f < 0.03) return;
      const len = 200 * f * (0.92 + 0.08 * Math.sin(t * 23) + 0.05 * Math.sin(t * 41));
      for (const [w, col] of [[34, "rgba(255,90,30,.55)"], [22, "rgba(255,160,40,.85)"], [10, "rgba(255,245,200,.95)"]]) {
        c.fillStyle = col; c.beginPath(); c.moveTo(NOZZLE.x, NOZZLE.y - w * 0.35 * f);
        c.quadraticCurveTo(NOZZLE.x - len * 0.55, NOZZLE.y - w * f, NOZZLE.x - len * (w === 10 ? 0.75 : 1), NOZZLE.y + Math.sin(t * 9) * 4);
        c.quadraticCurveTo(NOZZLE.x - len * 0.55, NOZZLE.y + w * f, NOZZLE.x, NOZZLE.y + w * 0.35 * f); c.fill();
      }
      const g = c.createRadialGradient(NOZZLE.x - 60, NOZZLE.y, 10, NOZZLE.x - 60, NOZZLE.y, 260);
      g.addColorStop(0, `rgba(255,140,40,${0.25 * f})`); g.addColorStop(1, "rgba(255,140,40,0)");
      c.fillStyle = g; c.fillRect(0, 0, W, H);
    }

    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  return <canvas ref={ref} className="mir-canvas" role="img"
                 aria-label="Illustrated Mir scene that changes with each decision (illustration, not to scale)" />;
}

export function prune(a, keep) { let j = 0; for (const p of a) if (keep(p)) a[j++] = p; a.length = j; }

export function roundRect(c, x, y, w, h, r) { c.beginPath(); c.roundRect(x, y, w, h, r); }

function drawCabin(c, t) {
  const g = c.createLinearGradient(0, 60, 0, 480);
  g.addColorStop(0, "#1b2a36"); g.addColorStop(0.5, "#22384a"); g.addColorStop(1, "#16222c");
  c.fillStyle = "#070d12"; c.fillRect(0, 0, W, H);
  c.fillStyle = g; roundRect(c, 30, 60, 900, 420, 60); c.fill();
  // ceiling and floor bands of the cylinder
  c.fillStyle = "#2c4558"; roundRect(c, 30, 60, 900, 52, [60, 60, 0, 0]); c.fill();
  c.fillStyle = "#132029"; roundRect(c, 30, 428, 900, 52, [0, 0, 60, 60]); c.fill();
  // wall panels with small lights
  for (let i = 0; i < 9; i++) {
    const x = 70 + i * 92;
    c.fillStyle = "#2a4254"; roundRect(c, x, 128, 78, 70, 6); c.fill();
    c.fillStyle = i % 3 === 0 ? "#6ee7b7" : "#94a3b8"; c.fillRect(x + 8, 140, 6, 6);
    c.fillStyle = "#3b5a70"; c.fillRect(x + 22, 140, 46, 4); c.fillRect(x + 22, 152, 34, 4);
  }
  // porthole with Earth
  c.fillStyle = "#0b1620"; c.beginPath(); c.arc(140, 300, 42, 0, 7); c.fill();
  const e = c.createRadialGradient(150, 330, 5, 150, 330, 60); e.addColorStop(0, "#5fb3e8"); e.addColorStop(1, "#16406b");
  c.fillStyle = e; c.beginPath(); c.arc(140, 300, 34, 0, 7); c.fill();
  c.strokeStyle = "#4a6a82"; c.lineWidth = 5; c.beginPath(); c.arc(140, 300, 40, 0, 7); c.stroke();
  // handrails
  c.strokeStyle = "#c9a227"; c.lineWidth = 4;
  for (const x of [230, 470, 700]) { c.beginPath(); c.moveTo(x, 412); c.lineTo(x + 70, 412); c.stroke(); }
  // the oxygen generator (SFOG) at the right
  c.fillStyle = "#4b5563"; roundRect(c, 800, 262, 70, 80, 8); c.fill();
  c.fillStyle = "#9ca3af"; c.fillRect(790, 292, 14, 16);
  c.fillStyle = "#cbd5e1"; c.font = "700 15px monospace"; c.fillText("O₂ GENERATOR", 790, 362);
  c.fillStyle = `rgba(239,68,68,${0.5 + 0.5 * Math.sin(t * 6)})`; c.beginPath(); c.arc(855, 276, 4, 0, 7); c.fill();
  c.fillStyle = "#94a3b8"; c.font = "15px monospace"; c.fillText("KVANT-1 · CUTAWAY · SI-GENERATED", 56, 96);
}

// A crew member as a pixel-art sprite (the team prototype's style): blocks of U px on a grid, drawn at low
// resolution and scaled up with sharp pixels. Clothing colour identifies the person, not a uniform.
const U = 6;
// mask: true = breathing mask and hose (Mir); "surgical" = surgical mask, goggles and gloves (ISS 2006).
export function figure(c, x, y, rot, col, mask, alpha, bob) {
  const px = (cx, cy, w, h, color) => { c.fillStyle = color; c.fillRect(cx * U, cy * U, w * U, h * U); };
  c.save(); c.globalAlpha = alpha; c.translate(Math.round(x), Math.round(y + bob)); c.rotate((rot * Math.PI) / 180);
  const dark = "rgba(0,0,0,.28)", skin = "#f1d3b3", hair = "#2b2b2b";
  px(-2, 1, 1, 4, col); px(1, 1, 1, 4, col); px(-2, 4, 1, 1, dark); px(1, 4, 1, 1, dark);   // legs
  px(-3, 5, 2, 1, "#111827"); px(1, 5, 2, 1, "#111827");                                      // boots
  px(-2, -4, 4, 5, col); px(1, -4, 1, 5, dark); px(-2, 0, 4, 1, dark);                        // body, shading, belt
  px(-3, -4, 1, 1, col); px(-4, -3, 1, 2, col); px(-4, -1, 1, 1, skin);                       // left arm, hand
  px(2, -4, 1, 1, col); px(3, -3, 1, 2, col); px(3, -1, 1, 1, skin);                          // right arm, hand
  px(-2, -8, 4, 4, skin); px(-2, -8, 4, 1, hair); px(-2, -7, 1, 1, hair);                     // head, hair
  c.fillStyle = "#1b1e2e"; c.fillRect(-1 * U + 1, -6 * U, 2, 3); c.fillRect(0.5 * U, -6 * U, 2, 3); // eyes
  if (mask === "surgical") {
    px(-2, -5.2, 4, 1.4, "#f8fafc"); px(-2, -5.2, 4, 0.3, "#cbd5e1");                           // surgical mask
    px(-2.2, -6.4, 4.4, 1, "#1e293b"); px(-1.8, -6.25, 1.5, 0.7, "#7dd3fc"); px(0.3, -6.25, 1.5, 0.7, "#7dd3fc"); // goggles
    px(-4, -1, 1, 1, "#a5f3fc"); px(3, -1, 1, 1, "#a5f3fc");                                     // gloves
  } else if (mask) { // breathing mask over nose and mouth, hose to a canister on the chest
    px(-2, -6, 4, 2, "#7dd3fc"); px(-2, -6, 4, 0.34, "#0c4a6e");
    px(2, -4, 1, 1, "#e2e8f0"); px(2, -3, 1, 1, "#e2e8f0"); px(0, -3, 2, 2, "#e2e8f0");
  }
  c.restore();
}

function drawCrew(c, pos, sc, t, haze, spraying, big) {
  pos.forEach(([x, y, r], i) => {
    const fade = sc.warn && haze > 0.6 ? 0.55 : 1;
    figure(c, x, y, r, CREW[i].c, sc.masks && !(sc.pose === "chain" && sc.warn && i === 0), fade, Math.sin(t * 1.3 + i) * 3);
    c.fillStyle = "rgba(226,232,240,.95)"; c.font = big ? "700 26px monospace" : "15px monospace"; c.textAlign = "center";
    c.fillText(CREW[i].name, x, y + (big ? 72 : 64)); c.textAlign = "left";
  });
  if (sc.pose === "chain" && !sc.warn) { // Linenger's hold on Korzun
    c.strokeStyle = "#3fa7d6"; c.lineWidth = 3; c.setLineDash([4, 4]);
    c.beginPath(); c.moveTo(pos[2][0] + 12, pos[2][1] - 4); c.lineTo(pos[0][0] - 10, pos[0][1] + 4); c.stroke(); c.setLineDash([]);
  }
  if (spraying) { // extinguisher in Korzun's hands
    const [x, y] = pos[0]; c.fillStyle = "#dc2626"; roundRect(c, x + 6, y - 14, 18, 10, 3); c.fill();
  }
  if (sc.spray === "alone") {
    c.fillStyle = "#fbbf24"; c.font = "700 16px monospace"; c.fillText("← push from the spray", pos[0][0] + 20, pos[0][1] - 40);
  }
}

function drawHandoff(c, pos, t) { // an extinguisher travels along the chain to Korzun
  const chain = [5, 4, 3, 1, 0].map((i) => pos[i]);
  const u = (t * 0.35) % 1, seg = Math.min(chain.length - 2, Math.floor(u * (chain.length - 1))), f = u * (chain.length - 1) - seg;
  const a = chain[seg], b = chain[seg + 1];
  c.fillStyle = "#dc2626"; roundRect(c, a[0] + (b[0] - a[0]) * f - 6, a[1] + (b[1] - a[1]) * f - 30, 12, 20, 3); c.fill();
}

function drawChecks(c, pos, age) {
  pos.forEach(([x, y], i) => {
    if (age < 0.6 + i * 0.5) return;
    c.fillStyle = "#22c55e"; c.beginPath(); c.arc(x + 18, y - 44, 9, 0, 7); c.fill();
    c.strokeStyle = "#fff"; c.lineWidth = 2.5; c.beginPath(); c.moveTo(x + 14, y - 44); c.lineTo(x + 17, y - 40); c.lineTo(x + 23, y - 48); c.stroke();
  });
  c.fillStyle = "#bbf7d0"; c.font = "700 16px monospace"; c.fillText("health checks · air cleaning", 760, 110);
}

function drawClock(c, age) {
  c.strokeStyle = "#fbbf24"; c.lineWidth = 3; c.beginPath(); c.arc(860, 120, 22, 0, 7); c.stroke();
  const a = age * 2; c.beginPath(); c.moveTo(860, 120); c.lineTo(860 + Math.sin(a) * 15, 120 - Math.cos(a) * 15); c.stroke();
  c.fillStyle = "#fde68a"; c.font = "700 16px monospace"; c.textAlign = "right"; c.fillText("waiting… air never checked", 828, 125); c.textAlign = "left";
}


// Escape-route map: Soyuz (aft of Kvant-1) — Kvant-1 (fire) — Core — node — Soyuz (forward)
function drawMap(c, choice, age, reduced) {
  c.fillStyle = "#06121a"; c.fillRect(0, 0, W, H);
  c.strokeStyle = "rgba(94,234,212,.08)"; c.lineWidth = 1;
  for (let x = 0; x < W; x += 30) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, H); c.stroke(); }
  for (let y = 0; y < H; y += 30) { c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
  const mod = (x, y, w, h, label, col = "#1f3b4d") => {
    c.fillStyle = col; roundRect(c, x, y, w, h, 12); c.fill(); c.strokeStyle = "#5eead4"; c.lineWidth = 1.5; c.stroke();
    c.fillStyle = "#cbd5e1"; c.font = "700 16px monospace"; c.textAlign = "center"; c.fillText(label, x + w / 2, y - 8); c.textAlign = "left";
  };
  mod(60, 230, 110, 70, "Soyuz (aft)", "#2a3340"); mod(200, 220, 170, 90, "Kvant-1"); mod(400, 205, 250, 120, "Core module");
  mod(680, 235, 60, 60, "Node"); mod(770, 230, 110, 70, "Soyuz (forward)", "#2a3340");
  for (const [x, y, h] of [[690, 120, 100], [690, 310, 100]]) { c.fillStyle = "#16303f"; roundRect(c, x, y, 40, h, 8); c.fill(); }
  // fire in Kvant-1
  const fl = 1 + 0.15 * Math.sin(age * 12);
  c.fillStyle = "rgba(255,120,30,.9)"; c.beginPath(); c.ellipse(285, 265, 34 * fl, 22 * fl, 0, 0, 7); c.fill();
  c.fillStyle = "rgba(255,235,170,.95)"; c.beginPath(); c.ellipse(285, 265, 14, 9, 0, 0, 7); c.fill();
  // seats: 3 per Soyuz
  const seats = (x) => [0, 1, 2].map((i) => [x + 20 + i * 30, 265]);
  const aft = seats(60), fwd = seats(770);
  for (const [x, y] of [...aft, ...fwd]) { c.strokeStyle = "#94a3b8"; c.lineWidth = 2; c.strokeRect(x - 9, y - 9, 18, 18); }
  // crew: six dots in the core
  const home = [0, 1, 2, 3, 4, 5].map((i) => [450 + (i % 3) * 50, 245 + Math.floor(i / 3) * 40]);
  const ease = reduced ? 1 : Math.min(1, age / 2.5);
  const path = (pts, col, dash) => { c.strokeStyle = col; c.lineWidth = 4; c.setLineDash(dash || []); c.beginPath(); pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y))); c.stroke(); c.setLineDash([]); };
  let dots = home, notes = [];
  if (choice === 0) {
    dots = home.map((p, i) => { const tgt = i < 3 ? fwd[i] : [740, 200 + (i - 3) * 22]; return [p[0] + (tgt[0] - p[0]) * ease, p[1] + (tgt[1] - p[1]) * ease]; });
    if (ease >= 1) notes.push([700, 180, "3 people: no seat", "#f87171"]);
  }
  if (choice === 1 || choice === 2) {
    path([[525, 265], [710, 265], [800, 265]], "#22c55e", choice === 1 ? [8, 6] : null);
    path([[450, 265], [320, 265], [170, 265]], choice === 2 ? "#ef4444" : "#22c55e", choice === 1 ? [8, 6] : null);
    if (choice === 1 || ease > 0.5) {
      c.strokeStyle = "#ef4444"; c.lineWidth = 6;
      c.beginPath(); c.moveTo(270, 245); c.lineTo(300, 285); c.moveTo(300, 245); c.lineTo(270, 285); c.stroke();
      notes.push([200, 360, "route blocked by the fire", "#f87171"]);
    }
    if (choice === 2) { notes.push([700, 360, "open: 3 seats for 6 people", "#86efac"]);
      c.strokeStyle = "rgba(250,204,21,.8)"; c.lineWidth = 2; c.setLineDash([5, 5]); c.beginPath(); c.arc(500, 265, 70 + Math.sin(age * 3) * 4, 0, 7); c.stroke(); c.setLineDash([]); }
  }
  dots.forEach(([x, y], i) => { c.fillStyle = CREW[i].c; c.beginPath(); c.arc(x, y, 10, 0, 7); c.fill(); c.strokeStyle = "#0b1620"; c.lineWidth = 2; c.stroke(); });
  for (const [x, y, t, col] of notes) { c.fillStyle = col; c.font = "700 17px monospace"; c.fillText(t, x, y); }
  c.fillStyle = "#94a3b8"; c.font = "15px monospace"; c.fillText("MIR · ESCAPE ROUTES · SCHEMATIC, NOT TO SCALE", 56, 60);
}

function drawBoard(c, choice, age) {
  c.fillStyle = "#0b2239"; c.fillRect(0, 0, W, H);
  c.strokeStyle = "rgba(147,197,253,.12)"; c.lineWidth = 1;
  for (let x = 0; x < W; x += 24) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, H); c.stroke(); }
  for (let y = 0; y < H; y += 24) { c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
  c.fillStyle = "#bfdbfe"; c.font = "700 28px monospace"; c.fillText("Next mission: lessons from the fire", 80, 110);
  BOARD.forEach((row, i) => {
    const y = 180 + i * 90, v = choice == null ? undefined : row.v[choice], shown = choice != null && age > 0.4 + i * 0.5;
    c.strokeStyle = "#93c5fd"; c.lineWidth = 2; roundRect(c, 80, y - 26, 800, 64, 12); c.stroke();
    c.fillStyle = "#e0f2fe"; c.font = "700 22px monospace"; c.fillText(row.label, 150, y + 12);
    c.strokeStyle = "#93c5fd"; c.strokeRect(100, y - 6, 28, 28);
    if (!shown) return;
    if (v === 1) { c.strokeStyle = "#4ade80"; c.lineWidth = 5; c.beginPath(); c.moveTo(104, y + 8); c.lineTo(112, y + 18); c.lineTo(126, y - 2); c.stroke(); }
    else if (v === 0) { c.strokeStyle = "#f87171"; c.lineWidth = 5; c.beginPath(); c.moveTo(104, y - 2); c.lineTo(124, y + 18); c.moveTo(124, y - 2); c.lineTo(104, y + 18); c.stroke(); }
    else { c.fillStyle = "#94a3b8"; c.fillRect(104, y + 6, 20, 4); }
    c.fillStyle = v === 1 ? "#86efac" : v === 0 ? "#fca5a5" : "#94a3b8"; c.font = "700 18px monospace"; c.textAlign = "right";
    c.fillText(v === 1 ? "covered" : v === 0 ? "gap" : "not addressed", 860, y + 12); c.textAlign = "left";
  });
}

export function caption(c, text, warn) {
  if (!text) return;
  c.font = "700 17px monospace";
  const w = c.measureText(text).width + 28;
  c.fillStyle = warn ? "rgba(120,53,15,.92)" : "rgba(6,14,20,.85)"; c.fillRect(30, 488, w, 36);
  c.fillStyle = warn ? "#fde68a" : "#e2e8f0"; c.fillText(text, 44, 512);
}
