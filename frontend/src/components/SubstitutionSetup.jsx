import { useCallback, useEffect, useState } from "react";
import { api, COVERAGE } from "../api.js";

// Per-lineup substitution setup: classify each player's court coverage, pair
// front/back specialists, then generate the per-rotation subs as a starting
// point. "Generate, then edit" — the rotation viewer is where you fine-tune.

const defaultCoverage = (p) => (p.is_libero ? "back" : "all");

export default function SubstitutionSetup({ lineupId, onGenerated }) {
  const [setup, setSetup] = useState(null);
  const [coverage, setCoverage] = useState({});   // pid -> 'all'|'front'|'back'
  const [pairs, setPairs] = useState([]);         // [[frontId, backId], ...]
  const [pendFront, setPendFront] = useState("");
  const [pendBack, setPendBack] = useState("");
  const [msg, setMsg] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    const s = await api.getSetup(lineupId);
    setSetup(s);
    const cov = {};
    for (const p of s.players) cov[p.id] = s.coverage[p.id] || defaultCoverage(p);
    setCoverage(cov);
    setPairs(s.pairs.map((pr) => [pr.front_player_id, pr.back_player_id]));
  }, [lineupId]);

  useEffect(() => { load(); }, [load]);

  if (!setup) return <p className="hint">Loading substitution setup…</p>;

  const byId = Object.fromEntries(setup.players.map((p) => [p.id, p]));
  const starterIds = new Set(Object.values(setup.starter_positions));
  const pairedIds = new Set(pairs.flat());
  const name = (id) => `#${byId[id]?.jersey_number ?? "–"} ${byId[id]?.name}`;

  async function changeCoverage(pid, cov) {
    const next = { ...coverage, [pid]: cov };
    setCoverage(next);
    setError(null); setMsg(null);
    try { await api.saveCoverage(lineupId, next); } catch (e) { setError(e.message); }
  }

  async function persistPairs(next) {
    setError(null); setMsg(null);
    try { await api.savePairs(lineupId, next); setPairs(next); }
    catch (e) { setError(e.message); }
  }
  function addPair() {
    if (!pendFront || !pendBack) return;
    persistPairs([...pairs, [Number(pendFront), Number(pendBack)]]);
    setPendFront(""); setPendBack("");
  }
  function removePair(i) { persistPairs(pairs.filter((_, idx) => idx !== i)); }

  async function generate() {
    setError(null);
    try {
      const res = await api.generateSubs(lineupId);
      setMsg(`Generated subs for ${res.rotations_with_subs} rotation(s) (${res.total_swaps} swaps). Open Rotations to review and tweak.`);
      onGenerated?.();
    } catch (e) { setError(e.message); }
  }

  // dropdown candidates: front specialists (not libero) / back specialists, not already paired
  const frontChoices = setup.players.filter((p) => coverage[p.id] === "front" && !p.is_libero && !pairedIds.has(p.id));
  const backChoices = setup.players.filter((p) => coverage[p.id] === "back" && !pairedIds.has(p.id));

  // warn about specialists with no pairing
  const unpaired = setup.players.filter(
    (p) => (coverage[p.id] === "front" || coverage[p.id] === "back") && !pairedIds.has(p.id) && starterIds.has(p.id)
  );

  return (
    <div className="card subs-setup">
      <h3>Substitution setup</h3>
      <p className="hint">
        Mark each player's court coverage. A front- or back-only player should be
        paired with an opposite partner — they share one slot and swap as it
        rotates between front and back row. All-around players play all six. The
        libero is locked to back-row (can never play the front row).
      </p>

      <div className="coverage-grid">
        {setup.players.map((p) => (
          <div key={p.id} className="coverage-row">
            <span className="cov-name">
              #{p.jersey_number ?? "–"} {p.name} <span className="dim">({p.primary_role})</span>
              {starterIds.has(p.id) && <span className="tag">starter</span>}
              {p.is_libero && <span className="pill back">libero</span>}
            </span>
            <select
              value={coverage[p.id]}
              disabled={p.is_libero}
              onChange={(e) => changeCoverage(p.id, e.target.value)}
              title={p.is_libero ? "Libero is back-row by rule" : ""}
            >
              {COVERAGE.map((c) => <option key={c.code} value={c.code}>{c.label}</option>)}
            </select>
          </div>
        ))}
      </div>

      <h4>Pairings</h4>
      {pairs.length === 0 && <p className="hint">No pairings yet.</p>}
      <ul className="pair-list">
        {pairs.map(([f, b], i) => (
          <li key={i}>
            <span>{name(f)} <span className="dim">(front)</span> ⇄ {name(b)} <span className="dim">(back)</span></span>
            <button className="ghost danger" onClick={() => removePair(i)}>×</button>
          </li>
        ))}
      </ul>
      <div className="form-row">
        <select value={pendFront} onChange={(e) => setPendFront(e.target.value)}>
          <option value="">front-row player…</option>
          {frontChoices.map((p) => <option key={p.id} value={p.id}>{name(p.id)}</option>)}
        </select>
        <span>⇄</span>
        <select value={pendBack} onChange={(e) => setPendBack(e.target.value)}>
          <option value="">back-row partner…</option>
          {backChoices.map((p) => <option key={p.id} value={p.id}>{name(p.id)}</option>)}
        </select>
        <button onClick={addPair} disabled={!pendFront || !pendBack}>Add pairing</button>
      </div>
      {frontChoices.length === 0 && backChoices.length === 0 && pairs.length === 0 && (
        <p className="hint">Set some players to “Front-row only” / “Back-row only” above to pair them.</p>
      )}

      {unpaired.length > 0 && (
        <p className="warn">
          ⚠ Unpaired specialist{unpaired.length > 1 ? "s" : ""}: {unpaired.map((p) => p.name).join(", ")} — they’ll stay on all 6 rotations until paired.
        </p>
      )}

      <div className="form-row generate-row">
        <button className="primary" onClick={generate}>⚙ Generate subs from pairings</button>
        <span className="dim">Overwrites the subs in all 6 rotations, then you hand-edit.</span>
      </div>
      {msg && <p className="ok">{msg}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
