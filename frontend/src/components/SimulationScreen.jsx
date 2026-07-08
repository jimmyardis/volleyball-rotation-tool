// Simulate: two modes on one screen.
//   WATCH — one set, touch by touch, on the court with narration (WatchGame).
//   ANALYZE — hundreds of simulated sets aggregated per rotation, with
//   plain-English insights (computed from the event logs, never invented).

import { useMemo, useState } from "react";
import { api } from "../api.js";
import MiniCourt from "./MiniCourt.jsx";
import WatchGame from "./WatchGame.jsx";

const INSIGHT_META = {
  best:    { icon: "🏆", label: "Best rotation" },
  worst:   { icon: "🧱", label: "Needs work" },
  player:  { icon: "💥", label: "Go-to attacker" },
  serve:   { icon: "🎯", label: "Serving weapon" },
  mistake: { icon: "📌", label: "Practice focus" },
  lineup:  { icon: "🧠", label: "Lineup note" },
};

export default function SimulationScreen({ lineups }) {
  const [lineupId, setLineupId] = useState(lineups[0]?.id ?? null);
  const [opponent, setOpponent] = useState(60);
  const [mode, setMode] = useState("watch"); // watch | analyze
  const [batch, setBatch] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function runBatch() {
    setBusy(true);
    setError(null);
    try {
      setBatch(await api.simulate(lineupId, { opponent_skill: opponent, sets: 200 }));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const playersById = useMemo(
    () => Object.fromEntries((batch?.players ?? []).map((p) => [p.id, p])),
    [batch]
  );

  const ranked = useMemo(
    () => (batch ? [...batch.rotations].sort((a, b) => b.point_win_pct - a.point_win_pct) : []),
    [batch]
  );

  const pct = (x) => `${Math.round(x * 100)}%`;

  return (
    <div className="screen">
      <h2>Simulate</h2>

      <div className="card sim-controls">
        <label>
          Lineup:{" "}
          <select value={lineupId ?? ""} onChange={(e) => { setLineupId(Number(e.target.value)); setBatch(null); }}>
            {lineups.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.system})</option>)}
          </select>
        </label>
        <div className="slider-field">
          <span>Opponent strength: <strong>{opponent}</strong></span>
          <input type="range" min="20" max="95" value={opponent}
                 onChange={(e) => { setOpponent(Number(e.target.value)); setBatch(null); }} />
        </div>
        <div className="phase-tabs">
          <button className={mode === "watch" ? "active" : ""} onClick={() => setMode("watch")}>Watch a game</button>
          <button className={mode === "analyze" ? "active" : ""} onClick={() => setMode("analyze")}>Analyze rotations</button>
        </div>
      </div>

      {mode === "watch" && (
        <div className="card">
          <WatchGame key={`${lineupId}-${opponent}`} lineupId={lineupId} opponent={opponent} />
        </div>
      )}

      {mode === "analyze" && (
        <>
          {!batch && (
            <div className="card watch-empty">
              <p className="hint">Runs 200 full simulated sets with this lineup — every serve, pass,
              and tagged mistake — then reports what actually worked and what didn't.</p>
              {error && <p className="error">{error}</p>}
              <button className="primary" disabled={busy || lineupId == null} onClick={runBatch}>
                {busy ? "Playing 200 sets…" : "Run the analysis"}
              </button>
            </div>
          )}

          {batch && (
            <>
              <div className="card sim-summary">
                <span className="pz-card-title">After {batch.sets} simulated sets</span>
                <p className="sim-winrate">
                  You win <strong>{pct(batch.win_rate)}</strong> of sets against a level-{opponent} opponent.
                </p>
                <div className="insight-list">
                  {batch.insights.map((ins, i) => {
                    const meta = INSIGHT_META[ins.kind] ?? { icon: "•", label: ins.kind };
                    return (
                      <div key={i} className={`insight insight-${ins.kind}`}>
                        <span className="insight-icon" aria-hidden="true">{meta.icon}</span>
                        <span>
                          <span className="insight-label">{meta.label}</span>
                          <span className="insight-text">{ins.text}</span>
                        </span>
                      </div>
                    );
                  })}
                </div>
                <button className="ghost" disabled={busy} onClick={runBatch}>Run again</button>
              </div>

              <div className="sim-cards">
                {ranked.map((r, i) => {
                  const setterId = Object.values(r.positions ?? {})
                    .find((pid) => playersById[pid]?.primary_role === "S");
                  return (
                    <div key={r.rot}
                         className={`sim-card ${i === 0 ? "best" : ""} ${i === ranked.length - 1 ? "worst" : ""}`}>
                      <div className="sim-card-head">
                        <span className="sim-rank">#{i + 1}</span>
                        <strong>R{r.rot + 1}</strong>
                        {i === 0 && <span className="sim-flag good-flag">BEST</span>}
                        {i === ranked.length - 1 && <span className="sim-flag bad-flag">WORK ON THIS</span>}
                      </div>
                      {r.positions && (
                        <MiniCourt positions={r.positions} playersById={playersById}
                                   serverId={r.server_id} setterId={setterId} />
                      )}
                      <div className="winbar-wrap">
                        <div className="winbar-track"><div className="winbar" style={{ width: `${r.point_win_pct * 100}%` }} /></div>
                        <span className="win-pct">{pct(r.point_win_pct)}</span>
                      </div>
                      <div className="sim-card-meta">
                        <span>Sideout: {pct(r.sideout_pct)} · Serving: {pct(r.serve_win_pct)}</span>
                        <span>Server: {playersById[r.server_id]?.name ?? "—"}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
