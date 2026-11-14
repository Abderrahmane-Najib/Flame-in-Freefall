// The habitat buttons of the hero. apiId = the habitat id in the API (/habitats/{id}/ranking).
export const HABITATS = {
  iss: {
    apiId: "iss", moonLike: false, photo: "iss", label: "ISS",
    cred: "Earth's limb and aurora from the ISS · NASA", rank: "Experiments ranked for ISS air",
    sugg: ["Why does plastic burn at lower oxygen in space?", "Which smoke is hardest for ISS detectors to see?",
      "What is a cool flame?"],
  },
  moon: {
    apiId: "moon_base_rover", moonLike: true, photo: "moon", label: "Moon base",
    cred: "Apollo 17, Taurus-Littrow valley · NASA", rank: "Experiments ranked for Moon-base air",
    sugg: ["What happens to a fuel-droplet fire in Moon-base air?", "Which experiments used air close to a Moon base?",
      "Why was Moon gravity never tested?"],
  },
  rover: {
    apiId: "moon_base_rover", moonLike: true, photo: "moon", label: "Rover",
    cred: "Apollo 17, Taurus-Littrow valley · NASA", rank: "Experiments ranked for rover air",
    sugg: ["What happens to a fuel-droplet fire in Moon-base air?", "Which experiments used air close to a Moon base?",
      "Why was Moon gravity never tested?"],
  },
  mars: {
    apiId: "mars_base", moonLike: true, photo: "mars", label: "Mars",
    cred: "Mars, Viking orbiter mosaic · NASA/JPL", rank: "Experiments ranked for Mars habitat air (Moon-like)",
    sugg: ["Which experiments used air close to a Mars habitat?", "What happens to a fuel-droplet fire in Moon-base air?",
      "Why was Mars gravity never tested?"],
  },
};

// Explanation level -> assistant persona (app/services/assistant.py PERSONAS).
export const PERSONA = { explorer: "student", student: "researcher", researcher: "researcher" };

/** How an investigation's tests relate to the habitat's air (for the badge and the order). */
export function evidence(inv, ranking, nearByPsi, moonLike) {
  const r = ranking?.investigations?.find((x) => x.psi_id === inv.id);
  if (r?.measured) return { kind: "in", n: r.measured };
  if (moonLike && nearByPsi[inv.id]) return { kind: "near", n: nearByPsi[inv.id] };
  if (r?.from_note) return { kind: "note", n: r.from_note };
  if (inv.fuel_type === "ground" || inv.tests == null) return { kind: "na", n: null, note: "no test table" };
  if (r?.o2_only) return { kind: "none", n: 0, note: "O₂ only" };
  return { kind: "none", n: 0 };
}

export function score(inv, ev) {
  const base = { in: 3000, near: 2000, note: 1000, none: 0, na: -1000 }[ev.kind];
  return base + (ev.n || 0) + (inv.tests || 0) / 10000;
}

/** Tests per investigation in the near-lunar band (from /coverage points). */
export function nearLunarByPsi(coverage) {
  const out = {};
  for (const p of coverage?.points || []) {
    if (p.zone === "near_lunar") out[p.psi_id] = (out[p.psi_id] || 0) + (p.n_tests ?? 1);
  }
  return out;
}

export const fmt = (n) => (n == null ? "–" : Number(n).toLocaleString("en"));

/** First sentence of a summary, for the card line. */
export function firstSentence(text) {
  if (!text) return "";
  const m = text.match(/^.+?[.!?](\s|$)/);
  return (m ? m[0] : text).trim();
}
