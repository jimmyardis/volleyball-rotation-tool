// N-axis radar (spider) chart, drawn in a given color. Used for the roster
// trading cards (6 sim attributes, 0-100) and the Player Zone skill radar
// (8 skills, 1-5). Labels stay in text ink (never the series color).

import { ATTRS } from "../api.js";

const SHORT = { setting: "SET", attacking: "ATK", blocking: "BLK", defense: "DEF", confidence: "CON", pressure: "PRS" };

const shortLabel = (axis) =>
  axis.short ?? SHORT[axis.key] ?? (axis.label || axis.key).slice(0, 3).toUpperCase();

export default function RadarChart({ attrs, color, size = 150, axes = ATTRS, max = 100 }) {
  const cx = size / 2, cy = size / 2;
  const R = size / 2 - 20; // room for labels
  const N = axes.length;

  // axis i points straight up for i=0, then clockwise
  const point = (i, r) => {
    const a = (Math.PI * 2 * i) / N - Math.PI / 2;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };
  const ringPath = (r) =>
    axes.map((_, i) => point(i, r).join(",")).join(" ");
  const valuePath = axes.map((a, i) =>
    point(i, (Math.max(0, Math.min(max, attrs?.[a.key] ?? 0)) / max) * R).join(",")
  ).join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="radar" aria-label="Skill ratings radar chart">
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <polygon key={f} points={ringPath(R * f)} className="radar-ring" />
      ))}
      {axes.map((_, i) => {
        const [x, y] = point(i, R);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} className="radar-axis" />;
      })}
      <polygon points={valuePath} className="radar-value" style={{ fill: color, stroke: color }} />
      {axes.map((a, i) => {
        const [x, y] = point(i, R + 11);
        return (
          <text key={a.key} x={x} y={y + 3} textAnchor="middle" className="radar-label">
            {shortLabel(a)}
          </text>
        );
      })}
    </svg>
  );
}
