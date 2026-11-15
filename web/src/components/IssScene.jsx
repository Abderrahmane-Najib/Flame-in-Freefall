// ISS 2006 scene (pages/Mir.jsx, story lib/issStory.js): an illustrated cutaway of the Zvezda module with the
// Elektron oxygen generator, and a communications diagram. Every decision changes what is drawn:
//   alarm     no alarm / fans up -> fumes ride the airflow out of the hatch | alarm -> fans stop, fumes stay local
//   protect   bare hands -> skin warning | gear -> goggles, gloves, surgical masks | ignore -> droplets drift
//   source    keep running / restart -> hot, more leaking | shut down -> Elektron off, spill wiped and bagged
//   ground    diagram: priority satellite link (documented) | evacuate to Soyuz | silence
//   air       charcoal filter clears the fumes, checks, then fans restart | unchecked | all fans on -> spread
// Illustration only: positions, sizes and timing are schematic. Pixel-art figures come from MirScene.jsx.
import { useEffect, useRef } from "react";
import { caption, figure, prune, roundRect } from "./MirScene.jsx";

const W = 960, H = 540;
const CREW = [{ name: "Vinogradov", c: "#e4572e" }, { name: "Williams", c: "#3fa7d6" }, { name: "Reiter", c: "#f2a541" }];
const EL = { x: 800, y: 300 };     // the Elektron's outlet
const HATCH = { x: 70, y: 280 };   // hatch to the rest of the station
const FILTER = { x: 470, y: 150 }; // charcoal filter (last decision)

const POSES = {
  calm:  [[300, 260, -6], [420, 340, 10], [540, 250, 4]],
  turn:  [[560, 270, 18], [450, 330, -8], [380, 240, 10]],
  close: [[690, 300, 70], [600, 250, 20], [520, 340, -10]],
  wipe:  [[730, 330, 85], [650, 270, 30], [540, 330, -12]],
};

function scenario(stage, choice) {
  const s = { view: "cabin", pose: "calm", fans: 1, alarm: false, odor: 0, spread: 0, drops: 0, hot: false, on: true,
              gear: false, label: "", warn: false };
  if (stage === -1) return { ...s, label: "Zvezda · morning: the Elektron is switched back on" };
  if (stage === 0) {
    Object.assign(s, { pose: "turn", hot: true, odor: 0.6, label: "The Elektron overheats: a bad smell spreads" });
    if (choice === 0) Object.assign(s, { spread: 1, warn: true, label: "Imagined: no alarm — the fans carry the fumes to other modules" });
    if (choice === 1) Object.assign(s, { alarm: true, fans: 0, label: "Alarm pulled by hand: the fans stop, the fumes stay in Zvezda" });
    if (choice === 2) Object.assign(s, { spread: 2, fans: 2, warn: true, label: "Imagined: fans turned up — the fumes spread through the station" });
  } else if (stage === 1) {
    Object.assign(s, { pose: "turn", fans: 0, hot: true, odor: 0.45, drops: 1, label: "Clear droplets float out of the Elektron" });
    if (choice === 0) Object.assign(s, { pose: "close", skin: true, warn: true, label: "Imagined: bare hands on a corrosive liquid" });
    if (choice === 1) Object.assign(s, { pose: "close", gear: true, label: "Gloves, goggles, surgical masks: skin, eyes and breathing protected" });
    if (choice === 2) Object.assign(s, { drift: true, warn: true, label: "Imagined: the liquid is ignored — droplets drift through the cabin" });
  } else if (stage === 2) {
    Object.assign(s, { pose: "close", fans: 0, hot: true, odor: 0.4, drops: 0.7, gear: true, label: "The Elektron is still hot and leaking" });
    if (choice === 0) Object.assign(s, { drops: 1.4, odor: 0.6, warn: true, label: "Imagined: kept running — more heat, more liquid" });
    if (choice === 1) Object.assign(s, { pose: "wipe", on: false, hot: false, drops: 0, towels: true, label: "Elektron off: the spill is wiped up and sealed in two bags" });
    if (choice === 2) Object.assign(s, { drops: 1.2, restart: true, warn: true, label: "Imagined: restarted to test it — the leak begins again" });
  } else if (stage === 3) {
    Object.assign(s, { view: "link", label: "Houston and Moscow can declare a spacecraft emergency" });
    if (choice === 0) Object.assign(s, { warn: true, label: "Imagined: evacuation — the crew leaves a station whose problem is contained" });
    if (choice === 1) Object.assign(s, { label: "Spacecraft emergency: priority on the relay satellites, constant contact" });
    if (choice === 2) Object.assign(s, { warn: true, label: "Imagined: no call — the experts on the ground know nothing" });
  } else if (stage === 4) {
    Object.assign(s, { fans: 0, on: false, odor: 0.45, gear: true, label: "The Elektron is off. The smell lingers in Zvezda" });
    if (choice === 0) Object.assign(s, { gear: false, unchecked: true, warn: true, label: "Imagined: no smell, so no check — the air is never measured" });
    if (choice === 1) Object.assign(s, { scrub: true, label: "A charcoal filter scrubs the air; checked, then the fans restart" });
    if (choice === 2) Object.assign(s, { fans: 1, spread: 1, warn: true, label: "Imagined: all fans on — the fumes reach every module" });
  }
  return s;
}

/** What the scene shows for this decision and choice (the page prints it as the caption under the screen). */
export function sceneInfo(stage, choice) { const s = scenario(stage, choice); return { label: s.label, warn: s.warn, view: s.view }; }

export default function IssScene({ stage, choice, compact = false }) {
  const ref = useRef(null);
  const st = useRef({ stage, choice, t0: performance.now() });
  useEffect(() => { Object.assign(st.current, { stage, choice, t0: performance.now() }); }, [stage, choice]);
  useEffect(() => { st.current.compact = compact; }, [compact]);

  useEffect(() => {
    const cv = ref.current, ctx = cv.getContext("2d");
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    cv.width = 640; cv.height = 360; ctx.setTransform(640 / W, 0, 0, 640 / W, 0, 0); // low resolution: pixel-art look
    const fumes = [], drops = [];
    const pos = POSES.calm.map((p) => [...p]);
    let raf, last = performance.now(), clock = 0, haze = 0;

    const draw = (now) => {
      const S = st.current, dt = Math.min(0.05, (now - last) / 1000);
      last = now; clock += dt;
      const sc = scenario(S.stage, S.choice), age = (now - S.t0) / 1000;
      ctx.clearRect(0, 0, W, H);
      if (sc.view === "link") drawLink(ctx, S.choice, age, reduced);
      else {
        const fansOn = sc.scrub ? (age > 6 ? 1 : 0) : sc.fans;   // documented: ventilation back on after cleaning
        let odor = sc.odor;
        if (sc.scrub) odor = Math.max(0.03, 0.45 - age * 0.07);
        haze += (odor * 0.35 - haze) * (reduced ? 1 : Math.min(1, dt));
        POSES[sc.pose].forEach((p, i) => {
          const f = reduced ? 1 : Math.min(1, dt * 1.8);
          for (const k of [0, 1, 2]) pos[i][k] += (p[k] - pos[i][k]) * f;
        });
        step(dt, sc, odor, fansOn, age);
        drawCabin(ctx, clock, sc, fansOn, age);
        drawFumes(ctx);
        drawDrops(ctx);
        drawCrew(ctx, sc, clock, S.compact);
        if (haze > 0.01) { ctx.fillStyle = `rgba(170,180,150,${haze})`; ctx.fillRect(0, 0, W, H); }
        if (sc.scrub) drawFilter(ctx, age);
        if (sc.unchecked) note(ctx, "? air not measured", 610, 120, "#fde68a");
        if (sc.spread) note(ctx, "← fumes to the rest of the station", 110, 200, "#fde68a");
        if (sc.skin) note(ctx, "KOH: corrosive on skin", pos[0][0] - 60, pos[0][1] - 70, "#fca5a5");
      }
      if (!S.compact) caption(ctx, sc.label, sc.warn);
      raf = requestAnimationFrame(draw);
    };

    function step(dt, sc, odor, fansOn, age) {
      if (!dt) return;
      const leaking = sc.drops > 0 && (!sc.restart || age > 1.2);
      if (odor > 0.05 && Math.random() < odor * 0.6) fumes.push({ x: EL.x - 20 - Math.random() * 30, y: EL.y + (Math.random() - 0.5) * 70,
        vx: -6 - Math.random() * 24, vy: (Math.random() - 0.5) * 40, r: 6 + Math.random() * 10, a: 0.2 });
      if (leaking && Math.random() < 0.08 * sc.drops) drops.push({ x: EL.x - 20, y: EL.y + 30, vx: -8 - Math.random() * 14, vy: (Math.random() - 0.5) * 10,
        r: 3 + Math.random() * 4, life: 1 });
      const pull = sc.spread === 2 ? 90 : sc.spread ? 50 : fansOn ? 20 : 0;
      for (const p of fumes) {
        if (sc.scrub && age > 0.5) { p.vx += (FILTER.x - p.x) * 0.6 * dt; p.vy += (FILTER.y - p.y) * 0.6 * dt; if (Math.hypot(p.x - FILTER.x, p.y - FILTER.y) < 40) p.a -= dt * 1.5; }
        else if (pull) { p.vx += (HATCH.x - p.x) * pull * 0.0006 * dt * 60; p.vy += (HATCH.y - p.y) * pull * 0.0006 * dt * 60; }
        else { p.vx = p.vx * 0.96 + (Math.random() - 0.5) * 40 * dt; p.vy = p.vy * 0.96 + (Math.random() - 0.5) * 40 * dt; } // fans off: slow spread
        p.x += p.vx * dt; p.y += p.vy * dt; p.r += 6 * dt; p.a -= dt * 0.03;
      }
      for (const p of drops) {
        if (sc.drift) p.vx -= 6 * dt;
        if (sc.towels && age > 0.5) { p.vx += (740 - p.x) * dt; p.vy += (360 - p.y) * dt; p.life -= dt * 0.7; }
        p.x += p.vx * dt; p.y += p.vy * dt;
      }
      if (!sc.drops && !sc.towels) drops.length = 0;
      prune(fumes, (p) => p.a > 0 && p.x > HATCH.x - 10); prune(drops, (p) => p.life > 0 && p.x > 60);
      if (fumes.length > 300) fumes.splice(0, fumes.length - 300);
      if (drops.length > 40) drops.splice(0, drops.length - 40);
    }
    function drawFumes(c) { for (const p of fumes) { c.fillStyle = `rgba(190,198,160,${Math.max(0, p.a)})`; c.beginPath(); c.arc(p.x, p.y, p.r, 0, 7); c.fill(); } }
    function drawDrops(c) { // liquid in microgravity: floating spheres, not drips
      for (const p of drops) {
        c.globalAlpha = Math.max(0, Math.min(1, p.life));
        c.fillStyle = "rgba(186,230,253,.75)"; c.beginPath(); c.arc(p.x, p.y, p.r, 0, 7); c.fill();
        c.fillStyle = "rgba(255,255,255,.9)"; c.fillRect(p.x - p.r * 0.4, p.y - p.r * 0.5, 2, 2);
        c.globalAlpha = 1;
      }
    }
    function drawCrew(c, sc, t, big) {
      pos.forEach(([x, y, r], i) => {
        figure(c, x, y, r, CREW[i].c, sc.gear ? "surgical" : false, 1, Math.sin(t * 1.3 + i) * 3);
        c.fillStyle = "rgba(226,232,240,.95)"; c.font = big ? "700 26px monospace" : "15px monospace"; c.textAlign = "center";
        c.fillText(CREW[i].name, x, y + (big ? 72 : 64)); c.textAlign = "left";
      });
      if (sc.towels) { // towels and the two sealed bags
        c.fillStyle = "#f1f5f9"; roundRect(c, pos[0][0] + 14, pos[0][1] - 20, 22, 14, 3); c.fill();
        for (const [x, y] of [[700, 150], [736, 158]]) { c.fillStyle = "#cbd5e1"; roundRect(c, x, y, 28, 34, 7); c.fill(); c.fillStyle = "#475569"; c.fillRect(x + 4, y + 5, 20, 3); }
        c.fillStyle = "#e2e8f0"; c.font = "700 13px monospace"; c.fillText("sealed bags", 694, 212);
      }
    }

    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  return <canvas ref={ref} className="mir-canvas" role="img"
                 aria-label="Illustrated ISS Zvezda scene that changes with each decision (illustration, not to scale)" />;
}

function note(c, text, x, y, col) { c.fillStyle = col; c.font = "700 16px monospace"; c.fillText(text, x, y); }

function fan(c, x, y, on, t) {
  c.fillStyle = "#16222c"; c.beginPath(); c.arc(x, y, 20, 0, 7); c.fill();
  c.strokeStyle = "#4a6a82"; c.lineWidth = 3; c.stroke();
  const a = on ? t * 9 * on : 0.4;
  c.fillStyle = on ? "#94a3b8" : "#475569";
  for (let k = 0; k < 3; k++) { const b = a + (k * 2 * Math.PI) / 3; c.beginPath(); c.ellipse(x + Math.cos(b) * 9, y + Math.sin(b) * 9, 9, 4, b, 0, 7); c.fill(); }
  if (!on) { c.strokeStyle = "#f87171"; c.lineWidth = 3; c.beginPath(); c.moveTo(x - 14, y - 14); c.lineTo(x + 14, y + 14); c.stroke(); }
}

function drawCabin(c, t, sc, fansOn, age) {
  const g = c.createLinearGradient(0, 60, 0, 480);
  g.addColorStop(0, "#1d2b3a"); g.addColorStop(0.5, "#243a4e"); g.addColorStop(1, "#17232e");
  c.fillStyle = "#070d12"; c.fillRect(0, 0, W, H);
  c.fillStyle = g; roundRect(c, 30, 60, 900, 420, 60); c.fill();
  c.fillStyle = "#2e4a5f"; roundRect(c, 30, 60, 900, 52, [60, 60, 0, 0]); c.fill();
  c.fillStyle = "#132029"; roundRect(c, 30, 428, 900, 52, [0, 0, 60, 60]); c.fill();
  for (let i = 0; i < 9; i++) { // racks with small lights
    const x = 110 + i * 84;
    c.fillStyle = "#2b4356"; roundRect(c, x, 128, 70, 64, 6); c.fill();
    c.fillStyle = i % 3 === 1 ? "#7dd3fc" : "#94a3b8"; c.fillRect(x + 8, 140, 6, 6);
    c.fillStyle = "#3b5a70"; c.fillRect(x + 22, 140, 40, 4); c.fillRect(x + 22, 152, 30, 4);
  }
  // hatch to the rest of the station (left)
  c.fillStyle = "#0b1620"; c.beginPath(); c.ellipse(HATCH.x + 10, HATCH.y, 26, 70, 0, 0, 7); c.fill();
  c.strokeStyle = "#4a6a82"; c.lineWidth = 6; c.stroke();
  c.fillStyle = "#94a3b8"; c.font = "13px monospace"; c.fillText("to the rest", 44, 372); c.fillText("of the ISS", 48, 388);
  // ventilation fans (top)
  fan(c, 330, 88, fansOn, t); fan(c, 630, 88, fansOn, t);
  c.fillStyle = "#94a3b8"; c.font = "13px monospace"; c.fillText(fansOn ? "fans on" : "fans off", 360, 93);
  // the Elektron (right)
  const glow = sc.hot ? (sc.restart ? (age > 1.2 ? 1 : 0) : 1) : 0;
  if (glow) {
    const r = c.createRadialGradient(EL.x + 35, EL.y, 10, EL.x + 35, EL.y, 140);
    r.addColorStop(0, `rgba(255,120,40,${0.35 + 0.1 * Math.sin(t * 5)})`); r.addColorStop(1, "rgba(255,120,40,0)");
    c.fillStyle = r; c.fillRect(EL.x - 120, EL.y - 150, 300, 300);
  }
  c.fillStyle = "#4b5563"; roundRect(c, EL.x, EL.y - 60, 90, 130, 8); c.fill();
  c.fillStyle = "#374151"; c.fillRect(EL.x + 12, EL.y - 44, 66, 30);
  c.fillStyle = "#9ca3af"; c.fillRect(EL.x - 12, EL.y + 24, 14, 14);
  c.fillStyle = sc.on ? (glow ? "#f97316" : "#22c55e") : "#475569"; c.beginPath(); c.arc(EL.x + 72, EL.y + 50, 6, 0, 7); c.fill();
  c.fillStyle = "#cbd5e1"; c.font = "700 15px monospace"; c.fillText("ELEKTRON O₂", EL.x - 4, EL.y + 96);
  c.fillStyle = sc.on ? "#e2e8f0" : "#94a3b8"; c.font = "13px monospace"; c.fillText(sc.on ? "on" : "off", EL.x + 34, EL.y + 54);
  if (sc.alarm) { c.fillStyle = `rgba(239,68,68,${0.5 + 0.5 * Math.sin(t * 8)})`; roundRect(c, 760, 128, 150, 30, 6); c.fill();
    c.fillStyle = "#fff"; c.font = "700 15px monospace"; c.fillText("FIRE ALARM", 788, 149); }
  c.fillStyle = "#94a3b8"; c.font = "15px monospace"; c.fillText("ZVEZDA · CUTAWAY · ILLUSTRATION", 120, 96 + 330);
}

function drawFilter(c, age) {
  c.fillStyle = "#334155"; roundRect(c, FILTER.x - 40, FILTER.y - 26, 80, 52, 8); c.fill();
  c.fillStyle = "#0f172a"; for (let i = 0; i < 5; i++) c.fillRect(FILTER.x - 30 + i * 13, FILTER.y - 16, 7, 32);
  c.fillStyle = "#e2e8f0"; c.font = "700 13px monospace"; c.textAlign = "center"; c.fillText("CHARCOAL FILTER", FILTER.x, FILTER.y + 44); c.textAlign = "left";
  if (age > 4) note(c, "✓ air checked", 760, 130, "#86efac");
}

// Communications: the station, a relay satellite, and the two control centers on the ground.
function drawLink(c, choice, age, reduced) {
  c.fillStyle = "#050b16"; c.fillRect(0, 0, W, H);
  for (let i = 0; i < 60; i++) { c.fillStyle = "rgba(226,232,240,.5)"; c.fillRect((i * 151) % W, (i * 89) % 300, 2, 2); }
  const e = c.createRadialGradient(480, 1050, 500, 480, 1050, 700); e.addColorStop(0, "#1e5a8a"); e.addColorStop(1, "#0b2440");
  c.fillStyle = e; c.beginPath(); c.arc(480, 1050, 680, 0, 7); c.fill();
  const iss = [200, 170], sat = [520, 80], hou = [380, 405], mos = [650, 392], soy = [120, 260];
  const box = (x, y, w, h, col, label) => { c.fillStyle = col; roundRect(c, x - w / 2, y - h / 2, w, h, 6); c.fill(); c.fillStyle = "#e2e8f0"; c.font = "700 15px monospace"; c.textAlign = "center"; c.fillText(label, x, y + h / 2 + 20); c.textAlign = "left"; };
  // station: truss + modules
  c.fillStyle = "#94a3b8"; c.fillRect(iss[0] - 70, iss[1] - 3, 140, 6);
  for (const dx of [-70, 50]) { c.fillStyle = "#1d4ed8"; c.fillRect(iss[0] + dx, iss[1] - 30, 20, 60); }
  box(iss[0], iss[1] + 22, 60, 18, "#cbd5e1", ""); c.fillStyle = "#e2e8f0"; c.font = "700 15px monospace"; c.fillText("ISS", iss[0] - 14, iss[1] - 40);
  box(sat[0], sat[1], 40, 24, "#a3a3a3", "relay satellite");
  box(hou[0], hou[1], 26, 26, "#f97316", "Houston"); box(mos[0], mos[1], 26, 26, "#f97316", "Moscow");
  const ln = (a, b, col, w, dash) => { c.strokeStyle = col; c.lineWidth = w; c.setLineDash(dash || []); c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke(); c.setLineDash([]); };
  if (choice === 1) {
    const pulse = reduced ? 1 : 0.6 + 0.4 * Math.sin(age * 5);
    ln(iss, sat, `rgba(56,189,248,${pulse})`, 5); ln(sat, hou, `rgba(56,189,248,${pulse})`, 5); ln(iss, mos, "rgba(56,189,248,.6)", 3, [8, 6]);
    note(c, "PRIORITY LINK", 560, 150, "#7dd3fc");
  } else if (choice === 2) {
    ln(iss, sat, "rgba(148,163,184,.35)", 2, [4, 8]); ln(sat, hou, "rgba(148,163,184,.35)", 2, [4, 8]);
    note(c, "no call: the ground is unaware", 560, 150, "#fde68a");
  } else if (choice === 0) {
    box(soy[0], soy[1], 40, 22, "#2a3340", "Soyuz");
    const k = reduced ? 1 : Math.min(1, age / 2.5);
    [0, 1, 2].forEach((i) => { c.fillStyle = ["#e4572e", "#3fa7d6", "#f2a541"][i]; c.beginPath();
      c.arc(iss[0] + (soy[0] - iss[0]) * k + i * 10 - 10, iss[1] + 22 + (soy[1] - iss[1] - 22) * k, 7, 0, 7); c.fill(); });
    if (k >= 1) note(c, "leaving a contained problem", 40, 330, "#fde68a");
  } else {
    ln(iss, sat, "rgba(148,163,184,.6)", 2); ln(sat, hou, "rgba(148,163,184,.6)", 2);
  }
  c.fillStyle = "#94a3b8"; c.font = "15px monospace"; c.fillText("COMMUNICATIONS · SCHEMATIC, NOT TO SCALE", 56, 40);
}
