// SVG court. Net at the top, 6 zones laid out exactly as the domain diagram:
//
//        NET
//   +----+----+----+
//   | 4  | 3  | 2  |   front row
//   +----+----+----+
//   | 5  | 6  | 1  |   back row
//   +----+----+----+
//
// Pure presentational component: give it {zone: player_id} + a player lookup.

const W = 360;
const H = 240;
const ORIGIN_X = 20;
const ORIGIN_Y = 40; // leave room for the net label/line on top
const CELL_W = W / 3;
const CELL_H = H / 2;

// zone -> grid column (0..2) and row (0 = front/near net, 1 = back)
const ZONE_GRID = {
  4: [0, 0], 3: [1, 0], 2: [2, 0],
  5: [0, 1], 6: [1, 1], 1: [2, 1],
};

function cellCenter(zone) {
  const [col, row] = ZONE_GRID[zone];
  return {
    cx: ORIGIN_X + col * CELL_W + CELL_W / 2,
    cy: ORIGIN_Y + row * CELL_H + CELL_H / 2,
    x: ORIGIN_X + col * CELL_W,
    y: ORIGIN_Y + row * CELL_H,
  };
}

export default function Court({ positions, playersById, serverId, setterId }) {
  return (
    <svg viewBox={`0 0 ${W + 40} ${H + 60}`} className="court" role="img"
         aria-label="Volleyball court rotation diagram">
      {/* Net */}
      <text x={ORIGIN_X + W / 2} y={22} textAnchor="middle" className="net-label">
        NET
      </text>
      <line x1={ORIGIN_X} y1={ORIGIN_Y - 6} x2={ORIGIN_X + W} y2={ORIGIN_Y - 6}
            className="net-line" />

      {/* Court outline */}
      <rect x={ORIGIN_X} y={ORIGIN_Y} width={W} height={H} className="court-outline" />
      {/* center (10-foot) line between rows */}
      <line x1={ORIGIN_X} y1={ORIGIN_Y + CELL_H} x2={ORIGIN_X + W} y2={ORIGIN_Y + CELL_H}
            className="court-line" />

      {[1, 2, 3, 4, 5, 6].map((zone) => {
        const { cx, cy, x, y } = cellCenter(zone);
        const pid = positions?.[zone];
        const player = pid != null ? playersById[pid] : null;
        const isServer = pid != null && pid === serverId;
        const isSetter = pid != null && pid === setterId;
        return (
          <g key={zone}>
            {/* zone number, faint, in the corner */}
            <text x={x + 8} y={y + 18} className="zone-num">{zone}</text>

            {player && (
              <g className={`player ${isServer ? "is-server" : ""} ${isSetter ? "is-setter" : ""}`}>
                <circle cx={cx} cy={cy} r={30} className="player-circle" />
                <text x={cx} y={cy - 2} textAnchor="middle" className="player-jersey">
                  {player.jersey_number ?? "–"}
                </text>
                <text x={cx} y={cy + 14} textAnchor="middle" className="player-role">
                  {player.primary_role}
                </text>
                <text x={cx} y={cy + 48} textAnchor="middle" className="player-name">
                  {player.name}
                </text>
                {isServer && (
                  <text x={cx} y={cy - 40} textAnchor="middle" className="badge-serve">
                    ★ SERVE
                  </text>
                )}
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
}
