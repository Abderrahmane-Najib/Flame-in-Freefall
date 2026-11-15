// Etna API client. Empty base = same address (FastAPI serves the UI; Vite proxies in development).
// On etna.web.app (Firebase Hosting in front of Cloud Run) the API is called on Cloud Run directly:
// Firebase buffers streamed chat answers and cuts requests off after 60 s.
const CLOUD_RUN = "https://ghostflame-ryhaqcvtmq-ey.a.run.app";
const ON_FIREBASE = /\.(web\.app|firebaseapp\.com)$/.test(location.hostname);
const BASE = import.meta.env.VITE_API_URL || (ON_FIREBASE ? CLOUD_RUN : "");

/** Full address of an API path, for plain links (CSV downloads) that do not go through fetch. */
export const apiUrl = (path) => BASE + path;

const cache = new Map();

/** GET a JSON endpoint; the same path is fetched once per page load. */
export function get(path) {
  if (!cache.has(path)) {
    const p = fetch(BASE + path).then((r) => {
      if (!r.ok) throw new Error(`${r.status} on ${path}`);
      return r.json();
    });
    p.catch(() => cache.delete(path)); // a failed call can be retried
    cache.set(path, p);
  }
  return cache.get(path);
}

/** Forget cached GETs whose path starts with prefix (after an upload is approved, for example). */
export function forget(prefix) {
  for (const k of [...cache.keys()]) if (k.startsWith(prefix)) cache.delete(k);
}

/** GET without the cache (status polling). */
export async function fresh(path) {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${r.status} on ${path}`);
  return r.json();
}

async function send(path, init) {
  const r = await fetch(BASE + path, { method: "POST", ...init });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail ? (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)) : `${r.status} on ${path}`);
  return body;
}

export const post = (path, json) => send(path, json === undefined ? {} : {
  headers: { "Content-Type": "application/json" }, body: JSON.stringify(json),
});

export const del = (path) => send(path, { method: "DELETE" });

export function upload(path, file) {
  const form = new FormData();
  form.append("file", file);
  return send(path, { body: form });
}

/** POST to a chat endpoint and yield its NDJSON events: session, tool, text, chart, error, done (app/services/chat.py). */
export async function* streamChat(path, body, signal) {
  const r = await fetch(BASE + path, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal,
  });
  if (!r.ok) {
    yield { type: "error", message: `${r.status}: ${(await r.text()).slice(0, 200)}` };
    return;
  }
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (line) yield JSON.parse(line);
    }
  }
}
