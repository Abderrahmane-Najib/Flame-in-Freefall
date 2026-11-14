// Chart series colours by fuel family: the validated dataviz palette (CVD-safe in light and dark),
// always paired with a shape so colour is never the only cue. CSS variables live in styles.css.
export const FUEL_SERIES = [
  { id: "gas", label: "Gas flames", color: "var(--s-gas)", shape: "circle" },
  { id: "droplet", label: "Liquid droplets", color: "var(--s-droplet)", shape: "square" },
  { id: "solid", label: "Solid materials", color: "var(--s-solid)", shape: "triangle" },
];

export function Mark({ shape, x, y, r = 3.2, ...rest }) {
  if (shape === "square") return <rect x={x - r} y={y - r} width={r * 2} height={r * 2} rx={1} {...rest} />;
  if (shape === "triangle") return <path d={`M${x},${y - r * 1.2}L${x + r * 1.1},${y + r * 0.8}L${x - r * 1.1},${y + r * 0.8}Z`} {...rest} />;
  return <circle cx={x} cy={y} r={r} {...rest} />;
}
