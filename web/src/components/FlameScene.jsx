// Flame Lab 3D scene (three.js): a fuel droplet shrinking by the d² law with a glowing flame shell around it.
// Timing (K, extinction size, end state) comes from the API (nearest FLEX tests). Flame size, glow and the
// Earth 1 g teardrop are an illustration (not in the FLEX table); the page labels them as such.
import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

// Earth 1 g shape (uStretch = 1): a teardrop measured on NASA's photo of a burning n-heptane droplet in 1 g
// (Researcher's Guide to Combustion, 2015, Fig. 1, PDF p. 9): about 3.5x taller than wide, widest about a quarter of
// the way up, droplet near the base, blue only at the bottom. uShape = (half width, height, bottom), in mesh units.
const VS = `
uniform float uTime,uStretch,uFlicker;uniform vec3 uShape;
varying vec3 vN;varying vec3 vV;varying float vH;
float h(vec3 p){return fract(sin(dot(p,vec3(12.9898,78.233,37.719)))*43758.5453);}
float nz(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(mix(h(i),h(i+vec3(1,0,0)),f.x),mix(h(i+vec3(0,1,0)),h(i+vec3(1,1,0)),f.x),f.y),
  mix(mix(h(i+vec3(0,0,1)),h(i+vec3(1,0,1)),f.x),mix(h(i+vec3(0,1,1)),h(i+vec3(1,1,1)),f.x),f.y),f.z);}
void main(){
 float hy=(position.y+1.)*.5;                       // 0 bottom .. 1 top
 vec2 dir=length(position.xz)>1e-4?normalize(position.xz):vec2(0.);
 float prof=sin(3.14159*sqrt(hy));                  // widest at hy = 0.25, rounded base, pointed tip
 vec3 tear=vec3(dir.x*uShape.x*prof,uShape.z+hy*uShape.y,dir.y*uShape.x*prof);
 vec3 p=mix(position,tear,uStretch);
 float n=nz(normal*3.+vec3(0.,-uTime*(.5+2.5*uStretch),0.));
 p+=normal*(n-.5)*uFlicker*(.4+1.5*hy*uStretch);
 vH=hy;
 vec4 mv=modelViewMatrix*vec4(p,1.);
 vN=normalize(normalMatrix*normal);vV=normalize(-mv.xyz);
 gl_Position=projectionMatrix*mv;}`;
const FS = `
uniform vec3 uColor,uTop;uniform float uIntensity,uEdge,uStretch,uSootTop,uFill;
varying vec3 vN;varying vec3 vV;varying float vH;
void main(){
 float f=1.-abs(dot(normalize(vN),normalize(vV)));
 float a=mix(pow(f,uEdge),pow(1.-f,uEdge),uFill)*uIntensity;   // uFill 0 = bright rim, 1 = filled glow
 vec3 c=mix(uColor,uTop,smoothstep(.12,.25,vH)*uStretch*uSootTop);   // blue cap at the base in 1 g
 gl_FragColor=vec4(c*a,a);
 #include <colorspace_fragment>
}`;

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
// Per fuel. FLEX: methanol (clean, blue) and n-heptane (sooty); CFI: n-dodecane and its blends (sooty: "luminous
// yellow flame" in the CFI test notes). FSR = flame / droplet diameter in microgravity: illustration only.
const SOOTY = { methanol: false, heptane: true, dodecane: true, dodecane_iso25: true, dodecane_iso40: true };
const FSR = { methanol: 3.0, heptane: 6.0, dodecane: 6.0, dodecane_iso25: 6.0, dodecane_iso40: 6.0 };
// 1 g flame width / droplet diameter. Methanol: a 1.8 mm droplet in 1 g keeps its flame within about 2 droplet
// diameters (Saufi et al., Fuel, doi:10.1016/j.fuel.2020.119413, Fig. 7a), against 4-5 in microgravity. Sooty fuels:
// estimated from the NASA heptane photo (droplet hard to resolve). Height = 3.5 x width, droplet 10 % up (photo).
const w1g = (fuel) => (SOOTY[fuel] ? 3.5 : 2.0);
const COOL_FSR = 0.55;   // cool flame drawn inside the hot flame's size: illustration only

/** Illustration of brightness, soot and flame size from the air (not measured in the NASA tables). */
export function look(fuel, o2, p) {
  const o = o2 / 21, pr = p / 101.3;
  return {
    fsr: (FSR[fuel] || 4) * o ** -0.5 * pr ** -0.15,
    glow: clamp(o ** 1.2 * pr ** 0.3, 0.25, 2.2),
    soot: SOOTY[fuel] ? clamp((o2 - 14) / 20, 0, 1) * clamp(pr ** 0.7, 0, 1.6) : 0,
  };
}

/** Where the burn is at time t: droplet size, hot / cool flame strength (0..1), stage. */
export function phase(run, t) {
  const est = run.est;
  if (!est) return { d: run.d0, hot: 1, cool: 0, cloud: 0, burst: 0, out: false, stage: "none" };
  const dHot = est.end === "completion" ? 0 : est.d_ext_mm, kH = est.k_mm2_s;
  const tHot = Math.max(0, (run.d0 ** 2 - dHot ** 2) / kH);
  if (t < tHot) return { d: Math.sqrt(run.d0 ** 2 - kH * t), hot: 1, cool: 0, cloud: 0, burst: 0, out: false, stage: "hot" };
  const tA = t - tHot, c = est.cool;
  if (c) {   // CFI: the hot flame goes out and a cool flame keeps burning the droplet
    const tCool = Math.max(0, (dHot ** 2 - c.d_end_mm ** 2) / c.k_mm2_s), hot = clamp(1 - tA / 0.6, 0, 1);
    if (tA < tCool) {
      return { d: Math.sqrt(dHot ** 2 - c.k_mm2_s * tA), hot, cool: clamp(tA / 0.8, 0, 1), cloud: tA / tCool,
               burst: 0, out: false, stage: "cool" };
    }
    const cool = clamp(1 - (tA - tCool) / 0.8, 0, 1);
    return { d: c.d_end_mm, hot: 0, cool, cloud: cool, burst: 0, out: cool <= 0, stage: cool > 0 ? "cool" : "out" };
  }
  const fade = clamp(1 - tA / (est.end === "disruption" ? 0.25 : 0.6), 0, 1);
  const burst = est.end === "disruption" ? clamp(tA / 1.2, 0, 1) : 0;
  const out = fade <= 0 && (est.end !== "disruption" || burst >= 1);
  return { d: dHot, hot: fade, cool: 0, cloud: 0, burst, out, stage: out ? "out" : "hot" };
}

function shell(color, edge, fill = 0) {
  const m = new THREE.ShaderMaterial({
    vertexShader: VS, fragmentShader: FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: {
      uTime: { value: 0 }, uStretch: { value: 0 }, uFlicker: { value: 0.08 }, uColor: { value: new THREE.Color(color) },
      uTop: { value: new THREE.Color(0xffd9a0) }, uIntensity: { value: 1 }, uEdge: { value: edge },
      uShape: { value: new THREE.Vector3(1, 2, -1) }, uSootTop: { value: 1 }, uFill: { value: fill },
    },
  });
  return { mesh: new THREE.Mesh(new THREE.SphereGeometry(1, 96, 64), m), u: m.uniforms, m };
}

function makeFlame(scene) {
  const grp = new THREE.Group();
  const drop = new THREE.Mesh(new THREE.SphereGeometry(0.5, 48, 32),
    new THREE.MeshStandardMaterial({ color: 0xd8ecff, roughness: 0.1, transparent: true, opacity: 0.92, emissive: 0x0a1020 }));
  const outer = shell(0x2f6bff, 2.4), soot = shell(0xffc98a, 1.4, 1), halo = shell(0x3d6fe0, 1.6, 1);
  const cool = shell(0xcfe8ff, 1.6, 1);
  // vapour cloud seen around the droplet during the cool flame ("large vapor cloud" in the CFI test notes)
  const cloud = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32),
    new THREE.MeshBasicMaterial({ color: 0x9aa4ad, transparent: true, opacity: 0, depthWrite: false }));
  const light = new THREE.PointLight(0x7fa4ff, 1.6, 70, 0);
  // fragments for a "disruption" end: the droplet breaks apart
  const bits = new THREE.Group();
  const bitMat = new THREE.MeshBasicMaterial({ color: 0xffc27a, transparent: true });
  for (let i = 0; i < 18; i++) {
    const b = new THREE.Mesh(new THREE.SphereGeometry(0.12, 8, 6), bitMat);
    b.userData.dir = new THREE.Vector3().randomDirection();
    bits.add(b);
  }
  bits.visible = false;
  grp.add(drop, cloud, halo.mesh, outer.mesh, soot.mesh, cool.mesh, light, bits);
  scene.add(grp);
  return { grp, drop, outer, soot, halo, cool, cloud, light, bits, bitMat };
}

/**
 * props.run = { fuel, o2, p, d0, est: {k_mm2_s, d_ext_mm, burn_time_s, end, cool} | null } (GET /predict/droplet)
 * props.mode = "ug" | "1g" | "bounds";  props.playing, props.speed;  props.onTick({ t, d, done })
 */
export default function FlameScene({ run, mode, playing, speed, onTick }) {
  const host = useRef(null);
  const live = useRef({});
  live.current = { run, mode, playing, speed, onTick };
  const clock = useRef({ t: 0, hold: 0 });
  const labels = useRef([]);

  // restart the burn when the inputs change
  useEffect(() => { clock.current = { t: 0, hold: 0 }; }, [run, mode]);

  useEffect(() => {
    const el = host.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 500);
    camera.position.set(0, 6, 46);
    const controls = new OrbitControls(camera, renderer.domElement);
    Object.assign(controls, { enableDamping: true, autoRotate: true, autoRotateSpeed: 0.4, minDistance: 12, maxDistance: 120 });
    scene.add(new THREE.AmbientLight(0x6688aa, 0.6));

    { // stars
      const g = new THREE.BufferGeometry(), n = 1200, a = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) {
        const r = 150 + Math.random() * 100, t = Math.random() * Math.PI * 2, u = Math.acos(2 * Math.random() - 1);
        a.set([r * Math.sin(u) * Math.cos(t), r * Math.cos(u), r * Math.sin(u) * Math.sin(t)], i * 3);
      }
      g.setAttribute("position", new THREE.BufferAttribute(a, 3));
      scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0x9fb8d0, size: 0.6, transparent: true, opacity: 0.7 })));
    }
    { // chamber
      scene.add(new THREE.Mesh(new THREE.CylinderGeometry(30, 30, 44, 48, 6, true),
        new THREE.MeshBasicMaterial({ color: 0x2a5a66, wireframe: true, transparent: true, opacity: 0.12, side: THREE.BackSide })));
      for (const y of [22, -22]) {
        const r = new THREE.Mesh(new THREE.TorusGeometry(30, 0.12, 8, 96),
          new THREE.MeshBasicMaterial({ color: 0x3d8a96, transparent: true, opacity: 0.35 }));
        r.rotation.x = Math.PI / 2; r.position.y = y; scene.add(r);
      }
    }
    const world = new THREE.Group();   // holds the flames; scaled so the largest shape fits the chamber
    scene.add(world);
    const A = makeFlame(world), B = makeFlame(world);

    function draw(F, g, t, now) {
      const { run } = live.current;
      const lk = look(run.fuel, run.o2, run.p), est = run.est, ghost = !est;
      const ph = phase(run, t), d = ph.d;
      const r = (lk.fsr * Math.max(d, 0.2) / 2) * (1 + 0.3 * (est ? clamp(t / (est.burn_time_s || 1), 0, 1) : 0));
      F.drop.visible = !(ph.burst > 0) && d > 0.02;
      F.drop.scale.setScalar(Math.max(d, 0.001));
      const dd = Math.max(d, 0.2), wid = w1g(run.fuel) * dd, hgt = 3.5 * wid;
      for (const [s, k, wk, hk] of [[F.outer, 1, 1, 1], [F.soot, 0.5, 0.75, 0.85], [F.halo, 0.98, 0.98, 0.98],
                                    [F.cool, COOL_FSR, COOL_FSR, COOL_FSR]]) {
        const rs = r * k;   // the mesh is scaled by rs, so the 1 g shape is given in mesh units
        s.mesh.scale.setScalar(rs);
        s.u.uShape.value.set((wid / 2) * wk / rs, (hgt * hk) / rs, (-0.1 * hgt) / rs);
        s.u.uSootTop.value = SOOTY[run.fuel] ? 1 : 0.25;
        s.u.uStretch.value = g; s.u.uTime.value = now; s.m.wireframe = ghost;
      }
      const gk = ghost ? 0.35 : 1, hot = ph.hot * gk;
      F.outer.u.uIntensity.value = lk.glow * 0.95 * hot;
      F.halo.u.uIntensity.value = lk.glow * 0.22 * hot;
      F.soot.u.uIntensity.value = (lk.soot * 0.8 + g * 0.6 * (SOOTY[run.fuel] ? 1 : 0.25)) * hot;
      F.cool.u.uIntensity.value = 0.35 * ph.cool;   // brightened: a real cool flame is nearly invisible
      F.cloud.scale.setScalar(lk.fsr * run.d0 * 0.5 * (0.5 + 0.7 * ph.cloud));
      F.cloud.material.opacity = 0.1 * ph.cool * clamp(ph.cloud * 3, 0, 1);
      F.light.intensity = 1.4 * lk.glow * ph.hot + 0.4 * ph.cool;
      F.light.color.set(ph.hot < 0.5 && ph.cool > 0 ? 0xcfe8ff : lk.soot > 0.3 || g > 0 ? 0xffb070 : 0x7fa4ff);
      F.bits.visible = ph.burst > 0 && ph.burst < 1;
      F.bits.children.forEach((b) => b.position.copy(b.userData.dir).multiplyScalar(run.d0 * 0.5 + ph.burst * 9));
      F.bitMat.opacity = 1 - ph.burst;
      return { d, out: ph.out, stage: ph.stage };
    }

    let raf, last = performance.now(), lastTick = 0;
    const frame = (nowMs) => {
      const dt = Math.min(0.05, (nowMs - last) / 1000); last = nowMs;
      const { run, mode, playing, speed, onTick } = live.current;
      const c = clock.current;
      const w = el.clientWidth, h = el.clientHeight;
      const pr = renderer.getPixelRatio(); // resize on width or height changes (the stage can grow with the page)
      if (renderer.domElement.width !== Math.floor(w * pr) || renderer.domElement.height !== Math.floor(h * pr)) {
        renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
      }
      if (playing && run.est) {
        if (c.hold > 0) { c.hold -= dt; if (c.hold <= 0) { c.t = 0; c.hold = 0; } } else c.t += dt * speed;
      }
      const bounds = mode === "bounds", gA = mode === "1g" ? 1 : 0, now = nowMs / 1000;
      // fit: the microgravity sphere (at its largest) and the 1 g teardrop must fit in about 34 units of height
      const lk0 = look(run.fuel, run.o2, run.p), r0 = lk0.fsr * run.d0 * 0.65 * 1.18;
      const h1 = gA || bounds ? 3.5 * w1g(run.fuel) * run.d0 : 0;
      const fit = Math.min(1.4, 34 / Math.max(2 * r0, h1 * 1.05, 1));
      world.scale.setScalar(world.scale.x + (fit - world.scale.x) * 0.1);
      world.position.y += ((h1 ? -0.35 * h1 * fit : 0) - world.position.y) * 0.1;
      const gap = Math.max(r0, (w1g(run.fuel) * run.d0) / 2) * 1.3 + 2;
      A.grp.position.x = bounds ? -gap : 0; B.grp.position.x = gap; B.grp.visible = bounds;
      const ra = draw(A, gA, c.t, now);
      let done = ra.out;
      if (bounds) done = draw(B, 1, c.t, now).out && done;
      if (done && c.hold <= 0) c.hold = 1.5;
      controls.update();
      renderer.render(scene, camera);
      [[A, "Microgravity bound"], [B, "Earth 1 g bound"]].forEach(([F, text], i) => {
        const lb = labels.current[i];
        if (!lb) return;
        lb.style.display = bounds ? "block" : "none";
        if (!bounds) return;
        const v = new THREE.Vector3(0, -(r0 + 1.5), 0).applyMatrix4(F.grp.matrixWorld).project(camera);
        lb.textContent = text;
        lb.style.left = ((v.x + 1) / 2) * w + "px";
        lb.style.top = ((1 - v.y) / 2) * h + "px";
      });
      if (onTick && nowMs - lastTick > 100) { lastTick = nowMs; onTick({ t: c.t, d: ra.d, stage: ra.stage, done }); }
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      controls.dispose();
      scene.traverse((o) => { o.geometry?.dispose(); o.material?.dispose?.(); });
      renderer.dispose();
      el.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div className="lab-stage" ref={host}>
      <span className="lab-lbl" ref={(e) => { labels.current[0] = e; }} />
      <span className="lab-lbl" ref={(e) => { labels.current[1] = e; }} />
    </div>
  );
}
