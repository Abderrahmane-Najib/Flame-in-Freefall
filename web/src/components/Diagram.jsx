// A Mermaid diagram the assistant wrote in its answer (```mermaid block). It is an illustration of a process
// or of relations, never measured data: the caption says so. Mermaid (large) loads only when a diagram appears;
// securityLevel "strict" sanitises labels and blocks scripts and clicks.
import { useEffect, useRef, useState } from "react";

let mermaidReady = null;
let count = 0;

function loadMermaid() {
  mermaidReady ??= import("mermaid").then((m) => m.default);
  return mermaidReady;
}

export default function Diagram({ code }) {
  const box = useRef(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let live = true;
    loadMermaid().then(async (mermaid) => {
      const dark = document.documentElement.dataset.mode !== "light";
      mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: dark ? "dark" : "neutral",
                           fontFamily: "inherit" });
      try {
        const { svg } = await mermaid.render(`gf-diagram-${++count}`, code);
        if (live && box.current) box.current.innerHTML = svg;  // sanitised by Mermaid (strict)
      } catch {
        if (live) setFailed(true);
      }
    });
    return () => { live = false; };
  }, [code]);

  return (
    <figure className="diagram">
      {failed ? <pre className="diagram-code">{code}</pre> : <div ref={box} className="diagram-svg" />}
      <figcaption>{failed ? "This diagram could not be drawn; its text is shown instead." : "Illustration by the assistant, not measured data."}</figcaption>
    </figure>
  );
}
