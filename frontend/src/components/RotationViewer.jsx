import { useEffect, useState } from "react";
import { api } from "../api.js";
import Court from "./Court.jsx";

const PHASES = [
  { key: "serve", label: "Serving", help: "Your rotational spots. The zone-1 player serves; the rest hold position until contact." },
  { key: "receive", label: "Receiving", help: "Drag players into your serve-receive formation. They must stay overlap-legal until the other team contacts the serve. Changes are checked live and you can save them." },
  { key: "base", label: "Base (in play)", help: "Once the ball is live, players switch to base spots by role — setter right, middles middle, outsides left. Their rotational slot doesn't change; they just move." },
];

function buildPlacements(coords, positions, playersById, meta) {
  return Object.entries(positions).map(([zone, pid]) => {
    const p = playersById[pid] || {};
    const [x, y] = coords[zone];
    return {
      key: pid, playerId: pid, x, y,
      jersey: p.jersey_number, role: p.primary_role, name: p.name,
      isServer: pid === meta.server_id,
      isSetter: pid === meta.setter_id,
    };
  });
}

export default function RotationViewer({ lineupId }) {
  const [data, setData] = useState(null);
  const [idx, setIdx] = useState(0);
  const [phase, setPhase] = useState("serve");
  const [error, setError] = useState(null);

  // receive editing state (for the current rotation)
  const [receive, setReceive] = useState(null); // zone -> [x, y]
  const [overlap, setOverlap] = useState(null);  // {legal, faults}
  const [dirty, setDirty] = useState(false);
  const [savedMsg, setSavedMsg] = useState(null);

  useEffect(() => {
    if (!lineupId) return;
    setError(null); setIdx(0);
    api.getRotations(lineupId).then(setData).catch((e) => setError(e.message));
  }, [lineupId]);

  // (re)load the receive formation whenever the rotation or data changes
  useEffect(() => {
    if (!data) return;
    const rot = data.rotations[idx];
    setReceive({ ...rot.receive_positions });
    setOverlap(rot.receive_saved ? null : null);
    setDirty(false);
    setSavedMsg(null);
  }, [data, idx]);

  if (!lineupId) return <div className="screen"><p className="hint">Pick a lineup above to view its rotations.</p></div>;
  if (error) return <div className="screen"><p className="error">{error}</p></div>;
  if (!data || !receive) return <div className="screen"><p>Loading…</p></div>;

  const playersById = Object.fromEntries(data.players.map((p) => [p.id, p]));
  const rot = data.rotations[idx];
  const meta = rot.metadata;
  const zoneOfPlayer = Object.fromEntries(Object.entries(rot.positions).map(([z, pid]) => [pid, Number(z)]));

  const coordsForPhase =
    phase === "serve" ? rot.serve_positions :
    phase === "base" ? rot.base_positions :
    receive;
  const placements = buildPlacements(coordsForPhase, rot.positions, playersById, meta);

  function onDrag(playerId, nx, ny, committed) {
    const zone = zoneOfPlayer[playerId];
    const next = { ...receive, [zone]: [nx, ny] };
    setReceive(next);
    setDirty(true);
    setSavedMsg(null);
    if (committed) {
      api.overlapCheck(next).then(setOverlap).catch(() => {});
    }
  }

  function resetReceive() {
    setReceive({ ...rot.receive_positions });
    setOverlap(null); setDirty(false); setSavedMsg(null);
  }

  async function saveReceive() {
    const placementsByPlayer = {};
    for (const [zone, pid] of Object.entries(rot.positions)) {
      placementsByPlayer[pid] = receive[zone];
    }
    const res = await api.saveReceive(lineupId, idx, placementsByPlayer);
    setOverlap({ legal: res.legal, faults: res.faults });
    setDirty(false);
    setSavedMsg(res.legal ? "Saved — formation is legal." : "Saved (still has overlap faults).");
    // keep local state; refresh saved flag
    const fresh = await api.getRotations(lineupId);
    setData(fresh);
  }

  const phaseHelp = PHASES.find((p) => p.key === phase).help;

  return (
    <div className="screen">
      <h2>Rotations — {data.lineup.name} <span className="tag">{data.lineup.system}</span></h2>

      {/* Rotation stepper. rotation_index (0..5) is what Phase 2 tags events with. */}
      <div className="rotation-tabs">
        <span className="label-inline">Rotation:</span>
        {data.rotations.map((r) => (
          <button key={r.rotation_index} className={r.rotation_index === idx ? "active" : ""}
                  onClick={() => setIdx(r.rotation_index)}>
            R{r.rotation_index + 1}
          </button>
        ))}
        <span className="spacer" />
        <button className="ghost" onClick={() => setIdx((i) => (i + 5) % 6)}>‹ Prev</button>
        <button className="ghost" onClick={() => setIdx((i) => (i + 1) % 6)}>Next ›</button>
      </div>

      {/* Phase selector */}
      <div className="phase-tabs">
        <span className="label-inline">Situation:</span>
        {PHASES.map((p) => (
          <button key={p.key} className={p.key === phase ? "active" : ""} onClick={() => setPhase(p.key)}>
            {p.label}
          </button>
        ))}
      </div>
      <p className="hint phase-help">{phaseHelp}</p>

      <div className="viewer-grid">
        <div>
          <Court
            placements={placements}
            draggable={phase === "receive"}
            onDrag={onDrag}
            fault={phase === "receive" && overlap && !overlap.legal}
          />

          {phase === "receive" && (
            <div className="receive-controls">
              {overlap == null && <p className="hint">Drag a player, then release to check the formation.</p>}
              {overlap && overlap.legal && <p className="ok">✓ Legal formation — no overlap faults.</p>}
              {overlap && !overlap.legal && (
                <div className="error">
                  <strong>Overlap fault{overlap.faults.length > 1 ? "s" : ""}:</strong>
                  <ul>{overlap.faults.map((f, i) => <li key={i}>{f}</li>)}</ul>
                </div>
              )}
              <div className="form-row">
                <button onClick={saveReceive} disabled={!dirty && !!savedMsg}>Save this formation</button>
                <button className="ghost" onClick={resetReceive}>Reset</button>
                {dirty && <span className="dim">unsaved changes</span>}
                {savedMsg && <span className="ok">{savedMsg}</span>}
              </div>
            </div>
          )}
        </div>

        <aside className="meta-panel card">
          <h3>Rotation {idx + 1} <span className="dim">(index {rot.rotation_index})</span></h3>
          <dl>
            <dt>Serving</dt>
            <dd>{playersById[meta.server_id]?.name} <span className="dim">(zone 1)</span></dd>
            <dt>Setter</dt>
            <dd>
              {meta.setter_id != null ? playersById[meta.setter_id]?.name : "—"}
              {meta.setter_location && <span className={`pill ${meta.setter_location}`}>{meta.setter_location} row</span>}
            </dd>
            <dt>Front-row attackers</dt>
            <dd>
              <span className="big">{meta.front_row_attacker_count}</span>
              <span className="dim"> {meta.setter_location === "front" ? "(front-row setter — 2 hitters up)" : "(back-row setter — 3 hitters up)"}</span>
              <div className="attacker-names">{meta.front_row_attacker_ids.map((id) => playersById[id]?.name).join(", ")}</div>
            </dd>
          </dl>
        </aside>
      </div>
    </div>
  );
}
