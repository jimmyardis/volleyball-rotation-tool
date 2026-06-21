import { useEffect, useState } from "react";
import { api } from "../api.js";
import Court from "./Court.jsx";

export default function RotationViewer({ lineupId }) {
  const [data, setData] = useState(null);
  const [idx, setIdx] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!lineupId) return;
    setError(null);
    setIdx(0);
    api.getRotations(lineupId).then(setData).catch((e) => setError(e.message));
  }, [lineupId]);

  if (!lineupId) return <div className="screen"><p className="hint">Pick a lineup to view its rotations.</p></div>;
  if (error) return <div className="screen"><p className="error">{error}</p></div>;
  if (!data) return <div className="screen"><p>Loading…</p></div>;

  const playersById = Object.fromEntries(data.players.map((p) => [p.id, p]));
  const rot = data.rotations[idx];
  const meta = rot.metadata;
  const setterName = meta.setter_id != null ? playersById[meta.setter_id]?.name : "—";
  const serverName = playersById[meta.server_id]?.name;

  return (
    <div className="screen">
      <h2>
        Rotations — {data.lineup.name} <span className="tag">{data.lineup.system}</span>
      </h2>

      {/* Rotation 1..6 stepper. rotation_index (0..5) is what Phase 2 tags events with. */}
      <div className="rotation-tabs">
        {data.rotations.map((r) => (
          <button
            key={r.rotation_index}
            className={r.rotation_index === idx ? "active" : ""}
            onClick={() => setIdx(r.rotation_index)}
          >
            R{r.rotation_index + 1}
          </button>
        ))}
        <span className="spacer" />
        <button className="ghost" onClick={() => setIdx((i) => (i + 5) % 6)}>‹ Prev</button>
        <button className="ghost" onClick={() => setIdx((i) => (i + 1) % 6)}>Next ›</button>
      </div>

      <div className="viewer-grid">
        <Court
          positions={rot.positions}
          playersById={playersById}
          serverId={meta.server_id}
          setterId={meta.setter_id}
        />

        <aside className="meta-panel card">
          <h3>Rotation {idx + 1} <span className="dim">(index {rot.rotation_index})</span></h3>
          <dl>
            <dt>Serving</dt>
            <dd>{serverName} <span className="dim">(zone 1)</span></dd>

            <dt>Setter</dt>
            <dd>
              {setterName}
              {meta.setter_location && (
                <span className={`pill ${meta.setter_location}`}>
                  {meta.setter_location} row
                </span>
              )}
            </dd>

            <dt>Front-row attackers</dt>
            <dd>
              <span className="big">{meta.front_row_attacker_count}</span>
              <span className="dim">
                {" "}
                {meta.setter_location === "front"
                  ? "(front-row setter — only 2 hitters up)"
                  : "(back-row setter penetrates — 3 hitters up)"}
              </span>
              <div className="attacker-names">
                {meta.front_row_attacker_ids.map((id) => playersById[id]?.name).join(", ")}
              </div>
            </dd>
          </dl>
        </aside>
      </div>
    </div>
  );
}
