// Six-axis radar (spider) chart for a player's skill ratings, drawn in the
// player's role color. Labels stay in text ink (never the series color).

import { ATTRS } from "../api.js";

const SHORT = { setting: "SET", attacking: "ATK", blocking: "BLK", defense: "DEF", confidence: "CON", pressure: "PRS" };

export default function RadarChart({ attrs, color, size = 150 }) {
  const cx = size / 2, cy = size / 2;
  const R = size / 2 - 20; // room for labels
  const N = ATTRS.length;

  // axis i points straight up for i=0, then clockwise
  const point = (i, r) => {
    const a = (Math.PI * 2 * i) / N - Math.PI / 2;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };
  const ringPath = (r) =>
    ATTRS.map((_, i) => point(i, r).join(",")).join(" ");
  const valuePath = ATTRS.map((a, i) =>
    point(i, (Math.max(0, Math.min(100, attrs?.[a.key] ?? 0)) / 100) * R).join(",")
  ).join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="radar" aria-label="Skill ratings radar chart">
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <polygon key={f} points={ringPath(R * f)} className="radar-ring" />
      ))}
      {ATTRS.map((_, i) => {
        const [x, y] = point(i, R);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} className="radar-axis" />;
      })}
      <polygon points={valuePath} className="radar-value" style={{ fill: color, stroke: color }} />
      {ATTRS.map((a, i) => {
        const [x, y] = point(i, R + 11);
        return (
          <text key={a.key} x={x} y={y + 3} textAnchor="middle" className="radar-label">
            {SHORT[a.key]}
          </text>
        );
      })}
    </svg>
  );
}
