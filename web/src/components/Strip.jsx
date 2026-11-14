import { fmt } from "../lib/habitats.js";

export default function Strip({ investigations, health }) {
  const psi = investigations.filter((i) => i.origin === "psi");
  const sum = (k) => (investigations.length ? psi.reduce((s, i) => s + (i[k] || 0), 0) : null);
  const db = health?.database || {};
  const cells = [
    [investigations.length ? psi.length : null, "NASA combustion experiments"],
    [sum("tests"), "fires recorded"],
    [sum("tests_with_results"), "with recorded results"],
    [db.documents, "reports and papers"],
    [db.pages, "report pages searchable"],
  ];
  return (
    <div className="strip">
      {cells.map(([n, label]) => <div key={label}><b>{fmt(n)}</b><small>{label}</small></div>)}
    </div>
  );
}
