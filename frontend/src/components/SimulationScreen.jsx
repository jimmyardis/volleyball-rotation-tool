import { useState } from "react";
import { api } from "../api.js";
import MiniCourt from "./MiniCourt.jsx";

const STAKES = [
  { label: "Low (scrimmage)", value: 0.2 },
  { label: "Medium (regular match)", value: 0.5 },
  { label: "High (playoffs)", value: 0.85 },
];

export default function SimulationScreen({ lineups }) {
  const [lineupId, setLineupId] = useState(lineups[0]?.id ?? null);
  const [stakes, setStakes] = useState(0.5);
  const [opponent, setOpponent] = useState(60);
  const [result, setResult] = useState(null);
  const [rotations, setRotations] = useState(null); // for the mini-court per rank card
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function run() {
    if (!lineupId) return;
    setBusy(true); setError(null); setResult(null);
    try {
      const [res, rots] = await Promise.all([
        api.simulate(lineupId, { stakes, opponent_skill: opponent, games: 10000 }),
        api.getRotations(lineupId),
      ]);
      setResult(res);
      setRotations(rots);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const playersById = result ? Object.fromEntries(result.players.map((p) => [p.id, p])) : {};
  const ranked = result ? [...result.per_rotation].sort((a, b) => b.win_pct - a.win_pct) : [];
  const maxWin = ranked.length ? ranked[0].win_pct : 100;
  const rotByIndex = rotations
    ? Object.fromEntries(rotations.rotations.map((r) => [r.rotation_index, r]))
    : {};

  return (
    <div className="screen">
      <h2>Game Simulation</h2>
      <p className="hint">
        Runs ~10,000 simulated games and ranks which rotation performs best,
        using each on-court player's skill ratings (edit those on the Roster
        tab). Stakes amplify the cost of low “pressure”; opponent skill is the
        other team's overall strength.
      </p>

      <div className="card sim-controls">
        <label>Lineup:{" "}
          <select value={lineupId ?? ""} onChange={(e) => setLineupId(Number(e.target.value))}>
            <option value="" disabled>pick a lineup</option>
            {lineups.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.system})</option>)}
          </select>
        </label>
        <label>Stakes:{" "}
          <select value={stakes} onChange={(e) => setStakes(Number(e.target.value))}>
            {STAKES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </label>
        <label className="slider-field">
          Opponent skill: <strong>{opponent}</strong>
          <input type="range" min="1" max="100" value={opponent} onChange={(e) => setOpponent(Number(e.target.value))} />
        </label>
        <button onClick={run} disabled={busy || !lineupId}>{busy ? "Simulating…" : "Run 10,000 games"}</button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          <div className="sim-best card">
            Best rotation: <strong>Rotation {result.best_rotation + 1}</strong>
            {" "}— weakest is Rotation {result.worst_rotation + 1}.
            <span className="dim"> ({result.games_per_rotation.toLocaleString()} games each)</span>
          </div>

          <div className="sim-cards">
            {ranked.map((r, i) => {
              const rot = rotByIndex[r.rotation_index];
              const isBest = r.rotation_index === result.best_rotation;
              const isWorst = r.rotation_index === result.worst_rotation;
              return (
                <div key={r.rotation_index} className={`sim-card ${isBest ? "best" : ""} ${isWorst ? "worst" : ""}`}>
                  <div className="sim-card-head">
                    <span className="sim-rank">#{i + 1}</span>
                    <strong>Rotation {r.rotation_index + 1}</strong>
                    {isBest && <span className="sim-flag good-flag">BEST</span>}
                    {isWorst && <span className="sim-flag bad-flag">WORK ON THIS</span>}
                  </div>
                  {rot && (
                    <MiniCourt
                      positions={rot.positions}
                      playersById={playersById}
                      serverId={rot.metadata.server_id}
                      setterId={rot.metadata.setter_id}
                    />
                  )}
                  <div className="winbar-wrap">
                    <div className="winbar-track">
                      <div className="winbar" style={{ width: `${(r.win_pct / maxWin) * 100}%` }} />
                    </div>
                    <span className="win-pct">{r.win_pct}%</span>
                  </div>
                  <div className="sim-card-meta">
                    <span>{playersById[r.server_id]?.name ?? "—"} serving</span>
                    <span>{r.setter_location}-row setter · {r.attacker_count} attackers</span>
                  </div>
                </div>
              );
            })}
          </div>
          <p className="hint">
            Tip: a back-row setter (3 attackers) usually rates higher than a
            front-row setter (2 attackers). Ask the Coach Assistant why a
            rotation is weak and how to drill it.
          </p>
        </>
      )}
    </div>
  );
}
