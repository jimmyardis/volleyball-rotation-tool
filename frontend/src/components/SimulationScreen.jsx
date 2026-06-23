import { useState } from "react";
import { api } from "../api.js";

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
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function run() {
    if (!lineupId) return;
    setBusy(true); setError(null); setResult(null);
    try {
      const res = await api.simulate(lineupId, { stakes, opponent_skill: opponent, games: 10000 });
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const playersById = result ? Object.fromEntries(result.players.map((p) => [p.id, p])) : {};
  const ranked = result ? [...result.per_rotation].sort((a, b) => b.win_pct - a.win_pct) : [];
  const maxWin = ranked.length ? ranked[0].win_pct : 100;

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

          <table className="sim-table">
            <thead>
              <tr><th>Rank</th><th>Rotation</th><th>Serving</th><th>Setter</th><th>Attackers</th><th>Win %</th></tr>
            </thead>
            <tbody>
              {ranked.map((r, i) => (
                <tr key={r.rotation_index} className={r.rotation_index === result.best_rotation ? "best" : ""}>
                  <td>{i + 1}</td>
                  <td>R{r.rotation_index + 1}</td>
                  <td>{playersById[r.server_id]?.name ?? "—"}</td>
                  <td>{r.setter_location} row</td>
                  <td>{r.attacker_count}</td>
                  <td>
                    <div className="winbar-wrap">
                      <div className="winbar" style={{ width: `${(r.win_pct / maxWin) * 100}%` }} />
                      <span>{r.win_pct}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
