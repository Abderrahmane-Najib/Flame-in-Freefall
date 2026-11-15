// Card artwork: a real NASA photo when we have one, otherwise an illustration of the fuel family.
const PHOTOS = {
  "PSI-25": ["/img/PSI-25.jpg", "real flame · ISS 2014"],
  "PSI-101": ["/img/PSI-101.jpg", "SAME-R on the ISS · 2010"],
  "PSI-99": ["/img/PSI-99.jpg", "Saffire-IV fabric burn · 2023"],
  "PSI-26": ["/img/PSI-26.jpg", "BASS session · ISS 2013"],
};

export const ILL = {
  gas: (
    <svg viewBox="0 0 300 150" preserveAspectRatio="xMidYMid slice"><defs><radialGradient id="g-gas" cx="50%" cy="55%" r="50%"><stop offset="0" stopColor="#fff3d6" /><stop offset=".35" stopColor="#FF9B5A" /><stop offset=".62" stopColor="#3a62ff" stopOpacity=".85" /><stop offset="1" stopColor="#3a62ff" stopOpacity="0" /></radialGradient></defs><rect width="300" height="150" fill="#06080F" /><circle cx="150" cy="80" r="62" fill="url(#g-gas)" /><circle cx="150" cy="80" r="16" fill="#2a2d36" /></svg>
  ),
  droplet: (
    <svg viewBox="0 0 300 150" preserveAspectRatio="xMidYMid slice"><defs><radialGradient id="g-drop" cx="50%" cy="50%" r="50%"><stop offset=".3" stopColor="#5CC8FF" stopOpacity="0" /><stop offset=".55" stopColor="#5CC8FF" stopOpacity=".9" /><stop offset=".7" stopColor="#2a4bff" stopOpacity=".5" /><stop offset="1" stopColor="#2a4bff" stopOpacity="0" /></radialGradient></defs><rect width="300" height="150" fill="#06080F" /><circle cx="150" cy="75" r="58" fill="url(#g-drop)" /><circle cx="150" cy="75" r="11" fill="#d9dbe6" /><line x1="150" y1="0" x2="150" y2="64" stroke="#6b7088" /></svg>
  ),
  solid: (
    <svg viewBox="0 0 300 150" preserveAspectRatio="xMidYMid slice"><defs><radialGradient id="g-solid" cx="62%" cy="50%" r="50%"><stop offset="0" stopColor="#FF9B5A" stopOpacity=".9" /><stop offset=".45" stopColor="#3a62ff" stopOpacity=".7" /><stop offset="1" stopColor="#3a62ff" stopOpacity="0" /></radialGradient></defs><rect width="300" height="150" fill="#06080F" /><ellipse cx="190" cy="75" rx="58" ry="40" fill="url(#g-solid)" /><rect x="60" y="68" width="150" height="14" rx="7" fill="#2a2d36" /></svg>
  ),
  smoke: (
    <svg viewBox="0 0 300 150" preserveAspectRatio="xMidYMid slice"><rect width="300" height="150" fill="#06080F" />{[[110, 70, 9], [140, 52, 6], [165, 80, 11], [190, 58, 5], [128, 96, 5], [205, 92, 7], [150, 30, 4], [178, 112, 4]].map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r} fill="#AEB5D6" opacity={0.25 + (i % 3) * 0.2} />)}</svg>
  ),
  ground: (
    <svg viewBox="0 0 300 150" preserveAspectRatio="xMidYMid slice"><rect width="300" height="150" fill="#06080F" />{Array.from({ length: 9 }, (_, i) => <line key={i} x1={30 + i * 30} y1="20" x2={30 + i * 30} y2="130" stroke="#1d2433" />)}<path d="M30 110 C 90 105, 120 40, 170 50 S 250 95, 270 30" fill="none" stroke="#5CC8FF" strokeWidth="2" /></svg>
  ),
};

export default function Art({ inv }) {
  const photo = PHOTOS[inv.id];
  if (photo) return <><img src={photo[0]} alt="" loading="lazy" /><span className="src">{photo[1]}</span></>;
  return <>{ILL[inv.fuel_type] || ILL.ground}<span className="src">illustration</span></>;
}
