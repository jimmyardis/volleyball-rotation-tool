// Drag-and-drop lineup builder: the roster sits on a BENCH below the court;
// drag a player into a zone to place them, between zones to swap, or off the
// court to send them back to the bench. Replaces the six per-zone dropdowns.

import { useRef, useState } from "react";
import { roleColor, roleInk, ZONE_CELLS, zoneCenter } from "../roles.js";

const W = 400;
const OX = 24, OY = 40;
const CW = W - OX * 2;
const CH = 200;

const BENCH_TOP = OY + CH + 40;
const BENCH_COLS = 5;
const BENCH_DX = CW / (BENCH_COLS - 1);
const ROW_H = 66;

const ZONE_SHORT = {
  4: "left front", 3: "center front", 2: "right front",
  5: "left back", 6: "center back", 1: "right back",
};

const zoneSvgCenter = (zone) => {
  const [nx, ny] = zoneCenter(zone);
  return [OX + nx * CW, OY + ny * CH];
};

export default function CourtEditor({ players, assign, onChange }) {
  const svgRef = useRef(null);
  const [drag, setDrag] = useState(null); // { pid, x, y } in svg coords

  const placedIds = new Set(Object.values(assign).filter(Boolean));
  const bench = players.filter((p) => !placedIds.has(p.id));
  const benchRows = Math.max(1, Math.ceil(bench.length / BENCH_COLS));
  const H = BENCH_TOP + benchRows * ROW_H + 6;

  const benchPos = (i) => [
    OX + (i % BENCH_COLS) * BENCH_DX,
    BENCH_TOP + Math.floor(i / BENCH_COLS) * ROW_H + 14,
  ];

  function clientToSvg(e) {
    const pt = svgRef.current.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const loc = pt.matrixTransform(svgRef.current.getScreenCTM().inverse());
    return [loc.x, loc.y];
  }

  const zoneAt = (x, y) => {
    if (x < OX || x > OX + CW || y < OY || y > OY + CH) return null;
    const col = Math.min(2, Math.floor(((x - OX) / CW) * 3));
    const row = Math.min(1, Math.floor(((y - OY) / CH) * 2));
    return Number(Object.keys(ZONE_CELLS).find(
      (z) => ZONE_CELLS[z][0] === col && ZONE_CELLS[z][1] === row
    ));
  };

  function onPointerDown(e, pid) {
    const [x, y] = clientToSvg(e);
    setDrag({ pid, x, y });
    e.target.setPointerCapture?.(e.pointerId);
  }
  function onPointerMove(e) {
    if (!drag) return;
    const [x, y] = clientToSvg(e);
    setDrag((d) => ({ ...d, x, y }));
  }
  function onPointerUp(e) {
    if (!drag) return;
    const [x, y] = clientToSvg(e);
    const pid = drag.pid;
    setDrag(null);

    const target = zoneAt(x, y);
    const next = { ...assign };
    const fromZone = Object.keys(next).find((z) => next[z] === pid);

    if (target == null) {
      // dropped off-court -> back to the bench
      if (fromZone) delete next[fromZone];
    } else {
      const occupant = next[target];
      if (occupant && occupant !== pid && fromZone) next[fromZone] = occupant; // swap
      else if (fromZone) delete next[fromZone];
      next[target] = pid;
    }
    onChange(next);
  }

  const playersById = Object.fromEntries(players.map((p) => [p.id, p]));

  function Token({ p, x, y, small = false }) {
    const r = small ? 19 : 22;
    return (
      <g
        className={`player grab ${drag?.pid === p.id ? "dragging" : ""}`}
        style={{ transform: `translate(${x}px, ${y}px)` }}
        onPointerDown={(e) => onPointerDown(e, p.id)}
      >
        <circle r={r} className="player-circle" style={{ fill: roleColor(p.primary_role) }} />
        <text y={-1} textAnchor="middle" className="player-jersey" style={{ fill: roleInk(p.primary_role) }}>
          {p.jersey_number ?? "–"}
        </text>
        <text y={11} textAnchor="middle" className="player-role" style={{ fill: roleInk(p.primary_role) }}>
          {p.primary_role}
        </text>
        <text y={r + 14} textAnchor="middle" className="player-name">{p.name}</text>
      </g>
    );
  }

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${W} ${H}`}
      className="court editor"
      role="application"
      aria-label="Drag players from the bench onto the court"
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerUp}
    >
      <defs>
        <pattern id="wood-editor" width="96" height="36" patternUnits="userSpaceOnUse">
          <rect width="96" height="12" fill="#e6bd86" />
          <rect y="12" width="96" height="12" fill="#ddad72" />
          <rect y="24" width="96" height="12" fill="#e2b67e" />
          <g stroke="#c79a5d" strokeWidth="0.8">
            <line x1="0" y1="12" x2="96" y2="12" />
            <line x1="0" y1="24" x2="96" y2="24" />
            <line x1="30" y1="0" x2="30" y2="12" />
            <line x1="78" y1="12" x2="78" y2="24" />
            <line x1="14" y1="24" x2="14" y2="36" />
            <line x1="60" y1="24" x2="60" y2="36" />
          </g>
        </pattern>
      </defs>
      <rect x={OX - 6} y={OY - 14} width={CW + 12} height={8} className="net-band" />
      <text x={W / 2} y={OY - 22} textAnchor="middle" className="net-label">NET</text>
      <rect x={OX} y={OY} width={CW} height={CH} fill="url(#wood-editor)" className="court-outline" />
      <line x1={OX} y1={OY + CH / 2} x2={OX + CW} y2={OY + CH / 2} className="attack-line" />

      {/* zone slots (empty targets) */}
      {Object.keys(ZONE_CELLS).map((z) => {
        const zone = Number(z);
        const [cx, cy] = zoneSvgCenter(zone);
        const highlight = drag && zoneAt(drag.x, drag.y) === zone;
        if (assign[zone]) {
          return highlight ? <circle key={z} cx={cx} cy={cy} r={28} className="slot-highlight" /> : null;
        }
        return (
          <g key={z} className={`zone-slot ${highlight ? "over" : ""}`}>
            <circle cx={cx} cy={cy} r={22} className="slot-circle" />
            <text x={cx} y={cy + 4} textAnchor="middle" className="slot-num">{zone}</text>
            <text x={cx} y={cy + 34} textAnchor="middle" className="slot-label">
              {ZONE_SHORT[zone]}{zone === 1 ? " · serves" : ""}
            </text>
          </g>
        );
      })}

      {/* placed players (skip the one being dragged — drawn on top later) */}
      {Object.entries(assign).map(([zone, pid]) => {
        if (!pid || drag?.pid === pid) return null;
        const p = playersById[pid];
        if (!p) return null;
        const [cx, cy] = zoneSvgCenter(Number(zone));
        return <Token key={pid} p={p} x={cx} y={cy} />;
      })}

      {/* bench */}
      <text x={OX} y={BENCH_TOP - 18} className="bench-title">
        BENCH — drag a player onto the court
      </text>
      {bench.map((p, i) => {
        if (drag?.pid === p.id) return null;
        const [x, y] = benchPos(i);
        return <Token key={p.id} p={p} x={x} y={y} small />;
      })}

      {/* dragged token rides the pointer, always on top */}
      {drag && playersById[drag.pid] && (
        <Token p={playersById[drag.pid]} x={drag.x} y={drag.y} />
      )}
    </svg>
  );
}
