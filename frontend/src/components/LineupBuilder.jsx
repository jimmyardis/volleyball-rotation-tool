import { useEffect, useState } from "react";
import { api } from "../api.js";
import SubstitutionSetup from "./SubstitutionSetup.jsx";
import CourtEditor from "./CourtEditor.jsx";

const SYSTEMS = ["5-1", "6-2", "4-2"];

export default function LineupBuilder({ teamId, players, lineups, reload, onView }) {
  const [newLineup, setNewLineup] = useState({ name: "", system: "5-1", notes: "" });
  const [creating, setCreating] = useState(false);   // "+ Lineup" opens the form
  const [selectedId, setSelectedId] = useState(null);
  const [assign, setAssign] = useState({}); // zone -> player_id
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  const selected = lineups.find((l) => l.id === selectedId) || null;

  useEffect(() => {
    if (!selectedId) return;
    setSaved(false);
    api
      .getRotations(selectedId)
      .then((data) => setAssign(data.rotations[0].starter_positions || data.rotations[0].positions))
      .catch(() => setAssign({})); // no positions set yet
  }, [selectedId]);

  async function createLineup(e) {
    e.preventDefault();
    setError(null);
    if (!newLineup.name.trim()) return setError("Lineup needs a name.");
    try {
      const lineup = await api.createLineup(teamId, {
        name: newLineup.name.trim(),
        system: newLineup.system,
        notes: newLineup.notes || null,
      });
      setNewLineup({ name: "", system: "5-1", notes: "" });
      setCreating(false);
      await reload();
      setSelectedId(lineup.id);
      setAssign({});
    } catch (err) {
      setError(err.message);
    }
  }

  async function savePositions() {
    setError(null);
    const zones = [1, 2, 3, 4, 5, 6];
    const positions = {};
    for (const z of zones) {
      if (!assign[z]) return setError(`Assign a player to every zone (missing zone ${z}).`);
      positions[z] = assign[z];
    }
    if (new Set(Object.values(positions)).size !== 6)
      return setError("Each player can only be in one zone.");
    try {
      await api.setPositions(selectedId, positions);
      setSaved(true);
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(id) {
    if (!confirm("Delete this lineup?")) return;
    await api.deleteLineup(id);
    if (selectedId === id) setSelectedId(null);
    reload();
  }

  return (
    <div className="screen">
      <div className="screen-head">
        <div>
          <h2>Lineups</h2>
          <p className="hint">Name it, pick a system, drag your six onto the court.</p>
        </div>
        {!creating && <button onClick={() => setCreating(true)}>+ Lineup</button>}
      </div>

      {creating && (
        <form className="card" onSubmit={createLineup}>
          <h4 className="form-title">New lineup</h4>
          <div className="form-row">
            <input
              placeholder="Name (e.g. 5-1 vs tall teams)"
              value={newLineup.name}
              onChange={(e) => setNewLineup({ ...newLineup, name: e.target.value })}
            />
            <select
              value={newLineup.system}
              onChange={(e) => setNewLineup({ ...newLineup, system: e.target.value })}
            >
              {SYSTEMS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <button type="submit">Create</button>
            <button type="button" className="ghost" onClick={() => setCreating(false)}>Cancel</button>
          </div>
        </form>
      )}

      <ul className="lineup-list">
        {lineups.length === 0 && !creating && <li className="empty">No lineups yet — tap “+ Lineup”.</li>}
        {lineups.map((l) => (
          <li key={l.id} className={l.id === selectedId ? "active" : ""}>
            <button className="link" onClick={() => setSelectedId(l.id === selectedId ? null : l.id)}>
              {l.name} <span className="tag">{l.system}</span>
            </button>
            <button className="ghost danger" onClick={() => remove(l.id)}>Delete</button>
          </li>
        ))}
      </ul>

      <div>
          {!selected && lineups.length > 0 && <p className="hint">Tap a lineup to set its starting six.</p>}
          {selected && (
            <>
              <h3>
                Starting six — {selected.name} <span className="tag">{selected.system}</span>
              </h3>
              <p className="hint">
                Drag each player from the bench into a zone — drop one player on
                another to swap them, or drag them off the court to bench them.
                The other 5 rotations are computed from this.
              </p>
              <CourtEditor
                players={players}
                assign={assign}
                onChange={(next) => { setAssign(next); setSaved(false); }}
              />
              <div className="form-row">
                <button onClick={savePositions}>Save starting six</button>
                {saved && (
                  <button className="primary" onClick={() => onView(selected.id)}>
                    View rotations
                  </button>
                )}
              </div>
              {saved && <p className="ok">Saved. Player IDs persisted.</p>}

              {[1, 2, 3, 4, 5, 6].every((z) => assign[z]) ? (
                <SubstitutionSetup lineupId={selected.id} onGenerated={() => onView(selected.id)} />
              ) : (
                <p className="hint">Save a full starting six to set up coverage types and substitutions.</p>
              )}
            </>
          )}
          {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
