// SVG court rendered from NORMALIZED coordinates (x 0..1 left->right,
// y 0..1 net->baseline). The net is at the top. Works for every phase:
// serve and base are read-only; receive passes `draggable` + `onDrag` so the
// coach can slide players to passing spots.

import { useRef } from "react";

const W = 400;
const H = 300;
const OX = 24;     // court origin x
const OY = 44;     // court origin y (room for the net label on top)
const CW = W - OX * 2;
const CH = H - OY - 20;

// faint zone-cell guides (where each rotational zone nominally sits)
const ZONE_CELLS = {
  4: [0, 0], 3: [1, 0], 2: [2, 0],
  5: [0, 1], 6: [1, 1], 1: [2, 1],
};

const toSvg = (x, y) => [OX + x * CW, OY + y * CH];

export default function Court({ placements, draggable = false, onDrag, fault = false }) {
  const svgRef = useRef(null);
  const dragId = useRef(null);

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
    onDrag?.(id, nx, ny, true); // committed = true -> revalidate
  }

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
      <text x={W / 2} y={24} textAnchor="middle" className="net-label">NET</text>
      <line x1={OX} y1={OY - 8} x2={OX + CW} y2={OY - 8} className="net-line" />

      <rect x={OX} y={OY} width={CW} height={CH} className="court-outline" />
      <line x1={OX} y1={OY + CH / 2} x2={OX + CW} y2={OY + CH / 2} className="court-line" />

      {/* faint zone guides */}
      {Object.entries(ZONE_CELLS).map(([zone, [col, row]]) => (
        <text
          key={zone}
          x={OX + col * (CW / 3) + 8}
          y={OY + row * (CH / 2) + 18}
          className="zone-num"
        >
          {zone}
        </text>
      ))}

      {placements.map((p) => {
        const [cx, cy] = toSvg(p.x, p.y);
        return (
          <g
            key={p.key ?? p.playerId}
            className={`player ${p.isServer ? "is-server" : ""} ${p.isSetter ? "is-setter" : ""} ${draggable ? "grab" : ""}`}
            onPointerDown={(e) => onPointerDown(e, p.playerId)}
          >
            <circle cx={cx} cy={cy} r={24} className="player-circle" />
            <text x={cx} y={cy - 1} textAnchor="middle" className="player-jersey">
              {p.jersey ?? "–"}
            </text>
            <text x={cx} y={cy + 12} textAnchor="middle" className="player-role">{p.role}</text>
            <text x={cx} y={cy + 40} textAnchor="middle" className="player-name">{p.name}</text>
            {p.isServer && (
              <text x={cx} y={cy - 32} textAnchor="middle" className="badge-serve">SERVE</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
