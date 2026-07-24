// The coach side's gotcha moment (her spec): a dynamic sphere you can spin,
// with a dot for every player — tap a dot to pull up their card. Pure SVG
// 3D projection: no libraries, themes for free, works with touch.

import { useEffect, useMemo, useRef, useState } from "react";
import { roleMeta } from "../roles.js";

const R = 120;          // sphere radius in viewBox units
const F = 3.2;          // perspective strength
const IDLE_SPIN = 0.0035;

// evenly distribute n points on a unit sphere (Fibonacci lattice)
function fibonacci(n) {
  const pts = [];
  const ga = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < n; i++) {
    const y = n === 1 ? 0 : 1 - (2 * i) / (n - 1);
    const r = Math.sqrt(Math.max(0, 1 - y * y));
    pts.push([Math.cos(ga * i) * r, y, Math.sin(ga * i) * r]);
  }
  return pts;
}

// wireframe: latitude + longitude rings as point loops on the unit sphere
function rings() {
  const out = [];
  for (const lat of [-60, -30, 0, 30, 60]) {
    const phi = (lat * Math.PI) / 180, y = Math.sin(phi), r = Math.cos(phi), ring = [];
    for (let i = 0; i <= 48; i++) {
      const t = (i / 48) * 2 * Math.PI;
      ring.push([Math.cos(t) * r, y, Math.sin(t) * r]);
    }
    out.push(ring);
  }
  for (let lon = 0; lon < 180; lon += 30) {
    const lam = (lon * Math.PI) / 180, ring = [];
    for (let i = 0; i <= 48; i++) {
      const t = (i / 48) * 2 * Math.PI;
      const x = Math.cos(t), y = Math.sin(t);
      ring.push([x * Math.cos(lam), y, x * Math.sin(lam)]);
    }
    out.push(ring);
  }
  return out;
}
const RINGS = rings();

function project([x, y, z], yaw, pitch) {
  const x1 = x * Math.cos(yaw) + z * Math.sin(yaw);
  const z1 = -x * Math.sin(yaw) + z * Math.cos(yaw);
  const y1 = y * Math.cos(pitch) - z1 * Math.sin(pitch);
  const z2 = y * Math.sin(pitch) + z1 * Math.cos(pitch);
  const s = F / (F + z2);
  return { px: x1 * s * R, py: y1 * s * R, z: z2, s };
}

export default function RosterSphere({ players, onPick }) {
  const rot = useRef({ yaw: 0.6, pitch: -0.25 });
  const drag = useRef(null);           // {x, y, moved}
  const idleAt = useRef(0);
  const [, setFrame] = useState(0);

  const unit = useMemo(() => fibonacci(players.length), [players.length]);

  useEffect(() => {
    let raf;
    const tick = (t) => {
      if (!drag.current && t > idleAt.current) rot.current.yaw += IDLE_SPIN;
      setFrame((f) => f + 1);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  function down(e) {
    drag.current = { x: e.clientX, y: e.clientY, moved: 0 };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function move(e) {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x, dy = e.clientY - drag.current.y;
    drag.current.x = e.clientX; drag.current.y = e.clientY;
    drag.current.moved += Math.abs(dx) + Math.abs(dy);
    rot.current.yaw += dx * 0.006;
    rot.current.pitch = Math.max(-1.2, Math.min(1.2, rot.current.pitch + dy * 0.006));
  }
  function up(e) {
    // pointer capture retargets click events to the svg, so taps are
    // resolved by hand: small movement + a dot under the finger = a pick
    const wasTap = drag.current && drag.current.moved < 6;
    idleAt.current = performance.now() + 2500;
    drag.current = null;
    if (wasTap) {
      const g = document.elementFromPoint(e.clientX, e.clientY)?.closest?.(".sphere-dot");
      if (g) {
        const player = players.find((p) => p.id === Number(g.dataset.pid));
        if (player) onPick(player);
      }
    }
  }

  const { yaw, pitch } = rot.current;
  const dots = players
    .map((p, i) => ({ p, ...project(unit[i], yaw, pitch) }))
    .sort((a, b) => b.z - a.z);        // back first, front last

  return (
    <svg className="roster-sphere" viewBox="-165 -155 330 310"
         onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}>
      {RINGS.map((ring, ri) => (
        <polyline key={ri} className="sphere-ring"
          points={ring.map((v) => { const q = project(v, yaw, pitch); return `${q.px.toFixed(1)},${q.py.toFixed(1)}`; }).join(" ")} />
      ))}
      {dots.map(({ p, px, py, z, s }) => {
        const meta = roleMeta(p.primary_role);
        const front = z < 0.15;
        const r = 15 * s;
        return (
          <g key={p.id} transform={`translate(${px} ${py})`} data-pid={p.id}
             className={`sphere-dot ${front ? "front" : "back"}`}>
            <circle r={r} fill={meta.color} />
            <text y={r * 0.32} textAnchor="middle" fontSize={r * 0.95} fill={meta.ink} fontWeight="700">
              {p.jersey_number ?? p.name[0]}
            </text>
            {front && (
              <text y={r + 11} textAnchor="middle" fontSize="9.5" className="sphere-name">
                {p.name.split(" ")[0]}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
