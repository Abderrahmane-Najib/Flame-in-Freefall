import { PageHead } from "../components/InvCard.jsx";

const PAGES = {
  compare: ["Compare", "Put two experiments or two habitats side by side: their tested air, fuels, results and gaps."],
  lab: ["Flame Lab", "Real NASA test videos next to reconstructions built from their measurements, including the near-invisible cool flame."],
};

export default function Placeholder({ id }) {
  const [title, text] = PAGES[id];
  return (
    <div className="page">
      <PageHead title={title}>
        <div className="soon">
          <span className="tag mono">coming soon</span>
          <h2>{title} is being built</h2>
          <p>{text}</p>
          <p><a href="#/" style={{ color: "var(--accent-text)" }}>← Back home</a></p>
        </div>
      </PageHead>
    </div>
  );
}
