// Tiny hash router: "#/predict" -> "predict". No dependency; works on any static host.
import { useEffect, useState } from "react";

export const ROUTES = ["home", "experiments", "coverage", "predict", "graph", "search", "uploads", "compare", "lab", "data"];

const read = () => {
  const r = location.hash.replace(/^#\/?/, "").split("?")[0];
  return ROUTES.includes(r) ? r : "home";
};

export function useRoute() {
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const on = () => { setRoute(read()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}

export const go = (route) => { location.hash = "/" + route; };
