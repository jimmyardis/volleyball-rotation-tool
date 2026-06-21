import { useEffect, useState } from "react";
import { api } from "../api.js";
import Court from "./Court.jsx";

const PHASES = [
  { key: "serve", label: "Serving", editable: false,
    help: "Your rotational spots. The zone-1 player serves; the rest hold position until contact." },
  { key: "receive", label: "Receiving", editable: true,
    help: "Drag players into your serve-receive formation. They must stay overlap-legal until the other team contacts the serve — checked live. Save it to keep it." },
  { key: "base", label: "Base (after serve)", editable: true,
    help: "Drag each player to where they switch to once the ball is in play (e.g. a middle who hid outside slides to the middle). No overlap rule here — put them anywhere. Save it to keep it." },
];

const jersey = (p) => `#${p?.jersey_number ?? "–"}`;

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

  const [editCoords, setEditCoords] = useState(null); // zone -> [x, y] for the editable phase
  const [overlap, setOverlap] = useState(null);
  const [dirty, setDirty] = useState(false);
  const [savedMsg, setSavedMsg] = useState(null);
  const [showSubs, setShowSubs] = useState(false);
  const [subError, setSubError] = useState(null);

  useEffect(() => {
    if (!lineupId) return;
    setError(null); setIdx(0);
    api.getRotations(lineupId).then(setData).catch((e) => setError(e.message));
  }, [lineupId]);

  // load the editable formation whenever rotation / phase / data changes
  useEffect(() => {
    if (!data) return;
    const rot = data.rotations[idx];
    const src = phase === "base" ? rot.base_positions : rot.receive_positions;
    setEditCoords({ ...src });
    setOverlap(null); setDirty(false); setSavedMsg(null);
  }, [data, idx, phase]);

  if (!lineupId) return <div className="screen"><p className="hint">Pick a lineup above to view its rotations.</p></div>;
  if (error) return <div className="screen"><p className="error">{error}</p></div>;
  if (!data || !editCoords) return <div className="screen"><p>Loading…</p></div>;

  const playersById = Object.fromEntries(data.players.map((p) => [p.id, p]));
  const rot = data.rotations[idx];
  const meta = rot.metadata;
  const phaseDef = PHASES.find((p) => p.key === phase);
  const editable = phaseDef.editable;
  const zoneOfPlayer = Object.fromEntries(Object.entries(rot.positions).map(([z, pid]) => [pid, Number(z)]));

  const coords = phase === "serve" ? rot.serve_positions : editCoords;
  const placements = buildPlacements(coords, rot.positions, playersById, meta);

  // ---- editable formation (drag) ----
  function onDrag(playerId, nx, ny, committed) {
    const zone = zoneOfPlayer[playerId];
    const next = { ...editCoords, [zone]: [nx, ny] };
    setEditCoords(next); setDirty(true); setSavedMsg(null);
    if (committed && phase === "receive") api.overlapCheck(next).then(setOverlap).catch(() => {});
  }
  function resetFormation() {
    const src = phase === "base" ? rot.base_positions : rot.receive_positions;
    setEditCoords({ ...src }); setOverlap(null); setDirty(false); setSavedMsg(null);
  }
  async function saveFormation() {
    const byPlayer = {};
    for (const [zone, pid] of Object.entries(rot.positions)) byPlayer[pid] = editCoords[zone];
    const res = await api.saveFormation(lineupId, idx, phase, byPlayer);
    setOverlap(phase === "receive" ? { legal: res.legal, faults: res.faults } : null);
    setDirty(false);
    setSavedMsg(phase === "receive" && !res.legal ? "Saved (still has overlap faults)." : "Saved.");
    setData(await api.getRotations(lineupId));
  }

  // ---- substitutions ----
  const onCourtIds = new Set(Object.values(rot.positions));
  const bench = data.players.filter((p) => !onCourtIds.has(p.id));
  function candidatesFor(zone) {
    const ids = new Set([rot.starter_positions[zone], rot.positions[zone], ...bench.map((p) => p.id)]);
    return data.players.filter((p) => ids.has(p.id));
  }
  async function changeOnCourt(zone, newId) {
    setSubError(null);
    const newOnCourt = { ...rot.positions, [zone]: Number(newId) };
    const swaps = {};
    for (const z of Object.keys(rot.starter_positions)) {
      const starter = rot.starter_positions[z];
      if (newOnCourt[z] !== starter) swaps[starter] = newOnCourt[z];
    }
    try {
      await api.saveSubs(lineupId, idx, swaps);
      setData(await api.getRotations(lineupId));
    } catch (e) {
      setSubError(e.message);
    }
  }
  async function clearSubs() {
    setSubError(null);
    try { await api.saveSubs(lineupId, idx, {}); setData(await api.getRotations(lineupId)); }
    catch (e) { setSubError(e.message); }
  }

  // ---- narration ----
  const narration = [];
  narration.push(`Rotation ${idx + 1} of 6 — ${phaseDef.label}.`);
  const srv = playersById[meta.server_id];
  narration.push(`🏐 Serving: ${srv?.name} (${jersey(srv)}) from zone 1.`);
  if (meta.setter_id != null) {
    const s = playersById[meta.setter_id];
    narration.push(
      `Setter ${s?.name} is in the ${meta.setter_location} row → ${meta.front_row_attacker_count} front-row attacker${meta.front_row_attacker_count === 1 ? "" : "s"} (${meta.front_row_attacker_ids.map((id) => playersById[id]?.name).join(", ")}).`
    );
  }
  const subEntries = Object.entries(rot.subs || {});
  if (subEntries.length === 0) {
    narration.push("No substitutions — your starting six is on the floor.");
  } else {
    for (const [starterId, oncId] of subEntries) {
      const inP = playersById[oncId], outP = playersById[Number(starterId)];
      narration.push(`🔁 ${inP?.name} (${jersey(inP)})${inP?.is_libero ? " [libero]" : ""} in for ${outP?.name} (${jersey(outP)}).`);
    }
  }

  return (
    <div className="screen">
      <h2>Rotations — {data.lineup.name} <span className="tag">{data.lineup.system}</span></h2>

      <div className="rotation-tabs">
        <span className="label-inline">Rotation:</span>
        {data.rotations.map((r) => (
          <button key={r.rotation_index} className={r.rotation_index === idx ? "active" : ""} onClick={() => setIdx(r.rotation_index)}>
            R{r.rotation_index + 1}
          </button>
        ))}
        <span className="spacer" />
        <button className="ghost" onClick={() => setIdx((i) => (i + 5) % 6)}>‹ Prev</button>
        <button className="ghost" onClick={() => setIdx((i) => (i + 1) % 6)}>Next ›</button>
      </div>

      <div className="phase-tabs">
        <span className="label-inline">Situation:</span>
        {PHASES.map((p) => (
          <button key={p.key} className={p.key === phase ? "active" : ""} onClick={() => setPhase(p.key)}>{p.label}</button>
        ))}
        <span className="spacer" />
        <button className={`ghost ${showSubs ? "active-ghost" : ""}`} onClick={() => setShowSubs((s) => !s)}>
          Substitutions {showSubs ? "▾" : "▸"}{subEntries.length ? ` (${subEntries.length})` : ""}
        </button>
      </div>
      <p className="hint phase-help">{phaseDef.help}</p>

      {showSubs && (
        <div className="card subs-editor">
          <h4>Who's on court — Rotation {idx + 1}</h4>
          <p className="hint">Pick the player for each zone. Bench players (and the libero) can come in for a starter; leave the starter selected to keep them in.</p>
          <div className="zone-grid">
            {[4, 3, 2, 5, 6, 1].map((zone) => (
              <label key={zone} className="zone-assign">
                <span className="zone-tag">Zone {zone}{zone === 1 ? " (server)" : ""}</span>
                <select value={rot.positions[zone]} onChange={(e) => changeOnCourt(zone, e.target.value)}>
                  {candidatesFor(zone).map((p) => (
                    <option key={p.id} value={p.id}>
                      {jersey(p)} {p.name} ({p.primary_role}){p.id === rot.starter_positions[zone] ? " — starter" : ""}{p.is_libero ? " ⓛ" : ""}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <div className="form-row">
            {subEntries.length > 0 && <button className="ghost" onClick={clearSubs}>Clear all subs this rotation</button>}
            {subError && <span className="error">{subError}</span>}
          </div>
        </div>
      )}

      <div className="viewer-grid">
        <div>
          <Court placements={placements} draggable={editable} onDrag={onDrag}
                 fault={phase === "receive" && overlap && !overlap.legal} />

          {editable && (
            <div className="receive-controls">
              {phase === "receive" && overlap == null && <p className="hint">Drag a player, then release to check the formation.</p>}
              {phase === "receive" && overlap?.legal && <p className="ok">✓ Legal formation — no overlap faults.</p>}
              {phase === "receive" && overlap && !overlap.legal && (
                <div className="error"><strong>Overlap fault{overlap.faults.length > 1 ? "s" : ""}:</strong>
                  <ul>{overlap.faults.map((f, i) => <li key={i}>{f}</li>)}</ul>
                </div>
              )}
              <div className="form-row">
                <button onClick={saveFormation} disabled={!dirty}>Save this formation</button>
                <button className="ghost" onClick={resetFormation}>Reset</button>
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
            <dd>{meta.setter_id != null ? playersById[meta.setter_id]?.name : "—"}
              {meta.setter_location && <span className={`pill ${meta.setter_location}`}>{meta.setter_location} row</span>}</dd>
            <dt>Front-row attackers</dt>
            <dd><span className="big">{meta.front_row_attacker_count}</span>
              <span className="dim"> {meta.setter_location === "front" ? "(front-row setter — 2 up)" : "(back-row setter — 3 up)"}</span>
              <div className="attacker-names">{meta.front_row_attacker_ids.map((id) => playersById[id]?.name).join(", ")}</div></dd>
          </dl>
        </aside>
      </div>

      {/* play-by-play narration */}
      <div className="narration">
        <span className="narration-title">📣 On this rotation</span>
        <ul>{narration.map((line, i) => <li key={i}>{line}</li>)}</ul>
      </div>
    </div>
  );
}
