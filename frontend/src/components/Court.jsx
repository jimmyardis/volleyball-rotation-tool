// SVG court rendered from NORMALIZED coordinates (x 0..1 left->right,
// y 0..1 net->baseline). The net is at the top. Works for every phase:
// serve and base are read-only; receive passes `draggable` + `onDrag` so the
// coach can slide players to passing spots.
//
// Players are role-colored tokens that ANIMATE between positions (CSS
// transform transition), so switching rotation or phase slides everyone to
// their new spot instead of teleporting. `faultPairs` draws the overlap
// violations as red lines between the two offending players.

import { useRef, useState } from "react";
import { roleColor, roleInk, ZONE_CELLS } from "../roles.js";

const W = 400;
const H = 310;
const OX = 24;     // court origin x
const OY = 52;     // court origin y (room for the net band on top)
const CW = W - OX * 2;
const CH = H - OY - 26;

const toSvg = (x, y) => [OX + x * CW, OY + y * CH];

export default function Court({ placements, draggable = false, onDrag, fault = false, faultPairs = [] }) {
  const svgRef = useRef(null);
  const dragId = useRef(null);
  const [draggingId, setDraggingId] = useState(null); // transition off while dragging

  function clientToNorm(e) {
    const pt = svgRef.current.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const loc = pt.matrixTransform(svgRef.current.getScreenCTM().inverse());
    const nx = Math.min(1, Math.max(0, (loc.x - OX) / CW));
    const ny = Math.min(1, Math.max(0, (loc.y - OY) / CH));
    return [nx, ny];
  }

  function onPointerDown(e, playerId) {
    if (!draggable) return;
    dragId.current = playerId;
    setDraggingId(playerId);
    e.target.setPointerCapture?.(e.pointerId);
  }
  function onPointerMove(e) {
    if (dragId.current == null) return;
    const [nx, ny] = clientToNorm(e);
    onDrag?.(dragId.current, nx, ny, false);
  }
  function onPointerUp(e) {
    if (dragId.current == null) return;
    const [nx, ny] = clientToNorm(e);
    const id = dragId.current;
    dragId.current = null;
    setDraggingId(null);
    onDrag?.(id, nx, ny, true); // committed = true -> revalidate
  }

  const byZone = Object.fromEntries(placements.filter((p) => p.zone != null).map((p) => [p.zone, p]));

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${W} ${H}`}
      className={`court ${draggable ? "draggable" : ""} ${fault ? "fault" : ""}`}
      role="img"
      aria-label="Volleyball court diagram"
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerUp}
    >
      {/* net band */}
      <rect x={OX - 6} y={OY - 14} width={CW + 12} height={8} className="net-band" />
      <text x={W / 2} y={OY - 22} textAnchor="middle" className="net-label">NET</text>

      {/* playing surface: FIVB-style orange court on a teal free zone */}
      <rect x={OX} y={OY} width={CW} height={CH} className="court-outline" />
      {/* attack (3 m) line */}
      <line x1={OX} y1={OY + CH / 2} x2={OX + CW} y2={OY + CH / 2} className="court-line" />

      {/* faint zone guides */}
      {Object.entries(ZONE_CELLS).map(([zone, [col, row]]) => (
        <text
          key={zone}
          x={OX + col * (CW / 3) + 9}
          y={OY + row * (CH / 2) + 18}
          className="zone-num"
        >
          {zone}
        </text>
      ))}

      {/* overlap fault lines — drawn under the players */}
      {faultPairs.map((f, i) => {
        const a = byZone[f.zone_a], b = byZone[f.zone_b];
        if (!a || !b) return null;
        const [ax, ay] = toSvg(a.x, a.y);
        const [bx, by] = toSvg(b.x, b.y);
        return (
          <g key={i} className="fault-pair">
            <line x1={ax} y1={ay} x2={bx} y2={by} className="fault-line" />
            <circle cx={ax} cy={ay} r={29} className="fault-ring" />
            <circle cx={bx} cy={by} r={29} className="fault-ring" />
          </g>
        );
      })}

      {placements.map((p) => {
        const [cx, cy] = toSvg(p.x, p.y);
        const color = roleColor(p.role);
        const ink = roleInk(p.role);
        return (
          <g
            key={p.key ?? p.playerId}
            className={`player ${draggable ? "grab" : ""} ${p.playerId === draggingId ? "dragging" : ""}`}
            style={{ transform: `translate(${cx}px, ${cy}px)` }}
            onPointerDown={(e) => onPointerDown(e, p.playerId)}
          >
            {p.isServer && <circle r={30} className="server-halo" />}
            <circle r={24} className="player-circle" style={{ fill: color }} />
            {p.isSetter && <circle r={27} className="setter-ring" />}
            <text y={-1} textAnchor="middle" className="player-jersey" style={{ fill: ink }}>
              {p.jersey ?? "–"}
            </text>
            <text y={12} textAnchor="middle" className="player-role" style={{ fill: ink }}>{p.role}</text>
            <text y={40} textAnchor="middle" className="player-name">{p.name}</text>
            {p.isServer && (
              <text y={-36} textAnchor="middle" className="badge-serve">SERVE</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
