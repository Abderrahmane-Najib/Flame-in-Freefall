import Hero from "../components/Hero.jsx";
import Strip from "../components/Strip.jsx";
import Ranked from "../components/Ranked.jsx";
import { Equipment, FlameLab } from "../components/Static.jsx";
import { issKpis, moonKpis } from "../lib/kpis.js";

export default function Home({ hab, habitat, setHab, level, data, ranking, ranked, onOpen }) {
  const kpis = habitat.moonLike
    ? moonKpis({ coverage: data.coverage, ranking, nearTests: data.nearTests })
    : issKpis({ habitat: data.habitats?.find((h) => h.id === "iss"), ranking, pmma: data.pmma });
  return (
    <>
      <Hero hab={hab} habitat={habitat} setHab={setHab} kpis={kpis} level={level} />
      <Strip investigations={data.investigations} health={data.health} />
      <Ranked title={habitat.rank} ranked={ranked} coverage={data.coverage} onOpen={onOpen} level={level} />
      <Equipment />
      <FlameLab />
    </>
  );
}
