// Chat with the assistant. ChatThread streams one endpoint (NDJSON: session, tool, text, chart, error, done)
// and keeps its session for follow-ups; used by the floating "Ask Ghostflame" and by each uploaded report.
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import Markdown from "./Markdown.jsx";
import ChartView from "./ChartView.jsx";
import Avatar, { GUIDES } from "./Avatar.jsx";
import Character from "./Character.jsx";
import { streamChat } from "../lib/api.js";

const TOOL_LABEL = {
  search_reports: "searching NASA reports", search_report: "searching the report",
  get_investigation: "reading an investigation card", list_investigations: "listing investigations",
  rank_for_habitat: "ranking for a habitat", query_tests: "querying test tables", make_chart: "drawing a chart",
  get_card: "reading the card", search_card_reports: "searching its reports", query_card_tests: "querying its tests",
};

export const ChatThread = forwardRef(function ChatThread(
  { endpoint, persona, level, intro, suggestions = [], placeholder, onLink, draft, setDraft, autoFocus, onStatus }, ref) {
  const [msgs, setMsgs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [own, setOwn] = useState("");
  const value = draft ?? own;
  const setValue = setDraft ?? setOwn;
  const session = useRef(null);
  const abort = useRef(null);
  const input = useRef(null);
  const end = useRef(null);

  useEffect(() => { end.current?.scrollIntoView({ block: "nearest" }); }, [msgs]);
  useEffect(() => { if (autoFocus) input.current?.focus(); }, [autoFocus, draft]);
  // What the guide character shows: thinking (looking things up), talking (answer streaming), idle.
  const status = !busy ? "idle" : msgs.at(-1)?.text ? "talking" : "thinking";
  useEffect(() => { onStatus?.(status); }, [status]); // eslint-disable-line react-hooks/exhaustive-deps

  const update = (fn) => setMsgs((m) => { const c = [...m]; c[c.length - 1] = fn({ ...c[c.length - 1] }); return c; });

  async function ask(q) {
    q = q.trim();
    if (!q || busy) return;
    setValue("");
    setBusy(true);
    setMsgs((m) => [...m, { role: "me", text: q }, { role: "bot", text: "", tools: [], charts: [] }]);
    abort.current = new AbortController();
    try {
      for await (const ev of streamChat(endpoint, { message: q, session_id: session.current, persona }, abort.current.signal)) {
        if (ev.type === "session") session.current = ev.session_id;
        else if (ev.type === "tool") update((b) => ({ ...b, tools: [...b.tools, TOOL_LABEL[ev.name] || ev.name] }));
        else if (ev.type === "chart") update((b) => ({ ...b, charts: [...b.charts, ev.spec] }));
        else if (ev.type === "text") update((b) => ({ ...b, text: b.text + ev.content }));
        else if (ev.type === "error") update((b) => ({ ...b, error: ev.message }));
      }
    } catch (e) {
      if (e.name !== "AbortError") update((b) => ({ ...b, error: e.message }));
    }
    setBusy(false);
  }

  useImperativeHandle(ref, () => ({
    reset() { abort.current?.abort(); session.current = null; setMsgs([]); setBusy(false); },
  }));

  return (
    <>
      <div className="msgs" aria-live="polite">
        <div className="bot-row"><Avatar level={level} size={28} state={msgs.length ? "still" : "idle"} /><div className="bub">{intro || GUIDES[level]?.greet}</div></div>
        {!msgs.length && suggestions.length > 0 && (
          <div className="sugg">{suggestions.map((s) => <button key={s} type="button" onClick={() => ask(s)}>{s}</button>)}</div>
        )}
        {msgs.map((m, i) => m.role === "me"
          ? <div key={i} className="bub me">{m.text}</div>
          : <div key={i} className="bot-row">
              <Avatar level={level} size={28}
                      state={i < msgs.length - 1 ? "still" : !busy ? "idle" : m.text ? "talking" : "thinking"} />
              <div className={"bub" + (m.error ? " err" : "")}>
                {m.tools.length > 0 && <div className="tool">{[...new Set(m.tools)].join(" · ")}…</div>}
                {m.text ? <Markdown text={m.text} onLink={onLink} /> : !m.error && <span className="tool">thinking…</span>}
                {m.charts.map((c, j) => <ChartView key={j} spec={c} />)}
                {m.error && <p className="tool">Something went wrong: {m.error}</p>}
              </div>
            </div>)}
        <div ref={end} />
      </div>
      <form onSubmit={(e) => { e.preventDefault(); ask(value); }}>
        <input ref={input} value={value} onChange={(e) => setValue(e.target.value)} placeholder={placeholder}
               aria-label="Your question" maxLength={2000} autoComplete="off" />
        <button type="submit" disabled={busy}>{busy ? "…" : "Send"}</button>
      </form>
    </>
  );
});

export default function Chat({ open, setOpen, context, suggestions, persona, level, draft, setDraft }) {
  const thread = useRef(null);
  const [big, setBig] = useState(false);
  const [status, setStatus] = useState("idle");
  // The guide steps aside while the page scrolls (content passes under it), and comes back once scrolling stops.
  const [away, setAway] = useState(false);
  useEffect(() => {
    let t;
    const onScroll = () => { setAway(true); clearTimeout(t); t = setTimeout(() => setAway(false), 900); };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => { window.removeEventListener("scroll", onScroll); clearTimeout(t); };
  }, []);
  const guide = GUIDES[level] || GUIDES.student;
  return (
    <>
      {/* The guide is the chat button: "Ask me!" appears on hover / keyboard focus (and peeks out now and then) */}
      <button className={"mascot" + (away ? " away" : "")} type="button" aria-label={`Ask Ghostflame: ${guide.role.toLowerCase()}`}
              aria-expanded={open} aria-controls="chat" onClick={() => setOpen(!open)}>
        <span className="mascot-say" aria-hidden="true">Ask me!</span>
        <Character level={level} height={88} title="" />
      </button>
      <div className={"chat" + (big ? " big" : "")} id="chat" role="dialog" aria-label="Ask Ghostflame">
        <header>
          <div className="chat-who"><span className="chat-char"><Character level={level} state={status} height={62} /></span><div><b>Ask Ghostflame</b><br /><span>{guide.role} · {context}</span></div></div>
          <div className="chat-actions">
            <button className="pill" type="button" title="New conversation" aria-label="New conversation" onClick={() => thread.current?.reset()}>↺</button>
            <button className="pill" type="button" title={big ? "Make smaller" : "Expand"} aria-label={big ? "Make smaller" : "Expand"}
                    aria-pressed={big} onClick={() => setBig(!big)}>{big ? "⤡" : "⤢"}</button>
            <button className="pill" type="button" title="Close" aria-label="Close chat" onClick={() => setOpen(false)}>✕</button>
          </div>
        </header>
        <ChatThread ref={thread} endpoint="/chat" persona={persona} level={level} suggestions={suggestions} draft={draft} setDraft={setDraft}
                    autoFocus={open} onStatus={setStatus} placeholder="Ask about any experiment or habitat…" />
      </div>
    </>
  );
}
