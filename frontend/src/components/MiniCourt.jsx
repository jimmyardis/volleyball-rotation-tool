// Tiny court thumbnail: six role-colored dots on the zone grid. Used as
// rotation navigation (which formation is this?) and in simulation results.

import { roleColor, zoneCenter } from "../roles.js";

const W = 84;
const H = 58;
const OX = 4, OY = 8;
const CW = W - OX * 2;
const CH = H - OY - 4;

export default function MiniCourt({ positions, playersById, serverId, setterId }) {
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="mini-court" aria-hidden="true">
      <line x1={OX - 3} y1={OY - 4} x2={OX + CW + 3} y2={OY - 4} className="mini-net" />
      <rect x={OX} y={OY} width={CW} height={CH} className="mini-surface" />
      <line x1={OX} y1={OY + CH / 2} x2={OX + CW} y2={OY + CH / 2} className="mini-line" />
      {Object.entries(positions).map(([zone, pid]) => {
        const [nx, ny] = zoneCenter(Number(zone));
        const p = playersById[pid];
        return (
          <g key={zone}>
            {pid === serverId && (
              <circle cx={OX + nx * CW} cy={OY + ny * CH} r={8} className="mini-server-halo" />
            )}
            <circle
              cx={OX + nx * CW}
              cy={OY + ny * CH}
              r={5.5}
              className={`mini-dot ${pid === setterId ? "is-setter" : ""}`}
              style={{ fill: roleColor(p?.primary_role) }}
            />
          </g>
        );
      })}
    </svg>
  );
}
