import { useEffect, useMemo, useState } from "react";
import Nav from "./components/Nav.jsx";
import TopBar from "./components/TopBar.jsx";
import Detail from "./components/Detail.jsx";
import DidYouKnow from "./components/DidYouKnow.jsx";
import Chat from "./components/Chat.jsx";
import Home from "./pages/Home.jsx";
import Experiments from "./pages/Experiments.jsx";
import Coverage from "./pages/Coverage.jsx";
import Predict from "./pages/Predict.jsx";
import FlameLab from "./pages/FlameLab.jsx";
import Graph from "./pages/Graph.jsx";
import Search from "./pages/Search.jsx";
import Uploads from "./pages/Uploads.jsx";
import DataMethod from "./pages/DataMethod.jsx";
import Placeholder from "./pages/Placeholder.jsx";
import Mir from "./pages/Mir.jsx";
import { get } from "./lib/api.js";
import { go, useRoute } from "./lib/router.js";
import { HABITATS, PERSONA, evidence, nearLunarByPsi, score } from "./lib/habitats.js";

// Near-lunar band (app/services/coverage.py): chamber O2 >= 30% at 70.3-72.5 kPa.
const NEAR_LUNAR_TESTS = "/tests?o2_min=30&pressure_min_kpa=70.31&pressure_max_kpa=72.5&limit=100";

function readMode() {
  try {
    return new URLSearchParams(location.search).get("mode") || localStorage.getItem("gf-mode") || "light";
  } catch { return "light"; }
}

export default function App() {
  const route = useRoute();
  const [hab, setHab] = useState("moon");
  const [level, setLevel] = useState("student");
  const [mode, setMode] = useState(readMode);
  const [detailId, setDetailId] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [data, setData] = useState({ investigations: [], rankings: {} });
  const [apiDown, setApiDown] = useState(false); // the core list failed: show a banner instead of empty pages

  const habitat = HABITATS[hab];

  // Home data: loaded once; investigations again when the route changes (an approved upload adds a card).
  useEffect(() => {
    const load = (key, path) => get(path).then((v) => setData((d) => ({ ...d, [key]: v }))).catch((e) => console.error(e));
    load("coverage", "/coverage");
    load("health", "/health");
    load("habitats", "/habitats");
    load("nearTests", NEAR_LUNAR_TESTS);
    load("pmma", "/predict/pmma?rod_diameter_mm=9.53");
  }, []);
  useEffect(() => {
    get("/investigations").then((v) => { setApiDown(false); setData((d) => ({ ...d, investigations: v })); })
      .catch((e) => { console.error(e); setApiDown(true); });
  }, [route]);
  useEffect(() => {
    get(`/habitats/${habitat.apiId}/ranking`)
      .then((r) => setData((d) => ({ ...d, rankings: { ...d.rankings, [habitat.apiId]: r } })))
      .catch((e) => console.error(e));
  }, [habitat.apiId]);

  // Page-level state the design's CSS reads from <html> and <body>.
  useEffect(() => {
    document.documentElement.dataset.mode = mode;
    try { localStorage.setItem("gf-mode", mode); } catch { /* private mode */ }
  }, [mode]);
  useEffect(() => { document.documentElement.dataset.level = level; }, [level]);
  useEffect(() => {
    const b = document.body.classList;
    b.toggle("show-detail", !!detailId);
    b.toggle("show-chat", chatOpen);
    b.toggle("show-nav", navOpen);
  }, [detailId, chatOpen, navOpen]);
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") { setDetailId(null); setChatOpen(false); setNavOpen(false); }
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); go("search"); }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const ranking = data.rankings[habitat.apiId];
  const nearByPsi = useMemo(() => nearLunarByPsi(data.coverage), [data.coverage]);
  const ranked = useMemo(() => data.investigations
    .map((inv) => ({ inv, ev: evidence(inv, ranking, nearByPsi, habitat.moonLike) }))
    .sort((a, b) => score(b.inv, b.ev) - score(a.inv, a.ev)), [data.investigations, ranking, nearByPsi, habitat.moonLike]);

  const persona = PERSONA[level];

  const page = {
    home: <Home hab={hab} habitat={habitat} setHab={setHab} level={level} data={data} ranking={ranking} ranked={ranked} onOpen={setDetailId} />,
    experiments: <Experiments onOpen={setDetailId} />,
    coverage: <Coverage onOpen={setDetailId} level={level} />,
    predict: <Predict level={level} />,
    graph: <Graph onOpen={setDetailId} level={level} />,
    search: <Search level={level} />,
    uploads: <Uploads persona={persona} level={level} />,
    data: <DataMethod />,
    mir: <Mir />,
    lab: <FlameLab level={level} />,
  }[route];

  return (
    <>
      <div className="stars" aria-hidden="true" />
      <Nav route={route} level={level} setLevel={setLevel} onNavigate={() => setNavOpen(false)} />
      <div className="main">
        <TopBar mode={mode} setMode={setMode} onMenu={() => setNavOpen(true)} onSearch={() => go("search")}>
          {(level === "explorer" || level === "student") && <DidYouKnow onOpen={setDetailId} />}
        </TopBar>
        {apiDown && (
          <div className="api-down" role="alert">
            <b>Can't reach the NASA data right now.</b> The Ghostflame server is not answering; pages fill in once it is back.
            <button type="button" className="chip" onClick={() => window.location.reload()}>Try again</button>
          </div>
        )}
        {page}
        <p className="foot">All evidence was measured in microgravity. Moon and Mars gravity were never tested. Ghostflame is a NASA Space Apps 2026 project and is not affiliated with NASA.</p>
      </div>
      <div className="scrim" onClick={() => { setDetailId(null); setNavOpen(false); }} />
      <Detail id={detailId} ev={ranked.find((r) => r.inv.id === detailId)?.ev} onClose={() => setDetailId(null)} persona={persona} level={level} />
      <Chat open={chatOpen} setOpen={setChatOpen} context={route === "home" ? habitat.label : "all experiments"}
            suggestions={habitat.sugg} persona={persona} level={level} draft={draft} setDraft={setDraft} />
    </>
  );
}
