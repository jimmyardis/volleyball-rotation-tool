import { useEffect, useState } from "react";
import { api } from "../api.js";
import SubstitutionSetup from "./SubstitutionSetup.jsx";

const SYSTEMS = ["5-1", "6-2", "4-2"];
const ZONE_LABELS = {
  1: "Zone 1 — right back (server)",
  2: "Zone 2 — right front",
  3: "Zone 3 — center front",
  4: "Zone 4 — left front",
  5: "Zone 5 — left back",
  6: "Zone 6 — center back",
};

export default function LineupBuilder({ teamId, players, lineups, reload, onView }) {
  const [newLineup, setNewLineup] = useState({ name: "", system: "5-1", notes: "" });
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
      await reload();
      setSelectedId(lineup.id);
      setAssign({});
    } catch (err) {
      setError(err.message);
    }
  }

  function setZone(zone, playerId) {
    setAssign((a) => ({ ...a, [zone]: playerId ? Number(playerId) : undefined }));
    setSaved(false);
  }

  // a player already placed in another zone (to grey out duplicates)
  function placedElsewhere(zone, playerId) {
    return Object.entries(assign).some(([z, pid]) => Number(z) !== zone && pid === playerId);
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
      <h2>Lineups</h2>

      <div className="two-col">
        <div>
          <h3>Your lineups</h3>
          <ul className="lineup-list">
            {lineups.length === 0 && <li className="empty">No lineups yet.</li>}
            {lineups.map((l) => (
              <li key={l.id} className={l.id === selectedId ? "active" : ""}>
                <button className="link" onClick={() => setSelectedId(l.id)}>
                  {l.name} <span className="tag">{l.system}</span>
                </button>
                <button className="ghost danger" onClick={() => remove(l.id)}>Delete</button>
              </li>
            ))}
          </ul>

          <form className="card" onSubmit={createLineup}>
            <h4>New lineup</h4>
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
          </form>
        </div>

        <div>
          {!selected && <p className="hint">Select or create a lineup to set its starting six.</p>}
          {selected && (
            <>
              <h3>
                Starting six — {selected.name} <span className="tag">{selected.system}</span>
              </h3>
              <p className="hint">
                Assign one player per zone. The other 5 rotations are computed from this.
              </p>
              <div className="zone-grid">
                {[4, 3, 2, 5, 6, 1].map((zone) => (
                  <label key={zone} className="zone-assign">
                    <span className="zone-tag">{ZONE_LABELS[zone]}</span>
                    <select
                      value={assign[zone] ?? ""}
                      onChange={(e) => setZone(zone, e.target.value)}
                    >
                      <option value="">— pick —</option>
                      {players.map((p) => (
                        <option key={p.id} value={p.id} disabled={placedElsewhere(zone, p.id)}>
                          #{p.jersey_number ?? "–"} {p.name} ({p.primary_role})
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
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
    </div>
  );
}
