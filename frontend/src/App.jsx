import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import RosterScreen from "./components/RosterScreen.jsx";
import LineupBuilder from "./components/LineupBuilder.jsx";
import RotationViewer from "./components/RotationViewer.jsx";

const TABS = ["Roster", "Lineups", "Rotations"];

export default function App() {
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState(null);
  const [players, setPlayers] = useState([]);
  const [lineups, setLineups] = useState([]);
  const [tab, setTab] = useState("Roster");
  const [viewLineupId, setViewLineupId] = useState(null);
  const [newTeamName, setNewTeamName] = useState("");
  const [error, setError] = useState(null);

  // load teams once
  useEffect(() => {
    api.listTeams()
      .then((t) => {
        setTeams(t);
        if (t.length && teamId == null) setTeamId(t[0].id);
      })
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const reloadTeam = useCallback(async () => {
    if (teamId == null) return;
    const [ps, ls] = await Promise.all([api.listPlayers(teamId), api.listLineups(teamId)]);
    setPlayers(ps);
    setLineups(ls);
  }, [teamId]);

  useEffect(() => { reloadTeam(); }, [reloadTeam]);

  async function createTeam(e) {
    e.preventDefault();
    if (!newTeamName.trim()) return;
    const team = await api.createTeam({ name: newTeamName.trim() });
    setNewTeamName("");
    const t = await api.listTeams();
    setTeams(t);
    setTeamId(team.id);
  }

  function goToRotations(lineupId) {
    setViewLineupId(lineupId);
    setTab("Rotations");
  }

  return (
    <div className="app">
      <header>
        <h1>🏐 Rotation &amp; Lineup Tool</h1>
        <div className="team-bar">
          <select value={teamId ?? ""} onChange={(e) => setTeamId(Number(e.target.value))}>
            <option value="" disabled>Select a team</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>{t.name}{t.season ? ` (${t.season})` : ""}</option>
            ))}
          </select>
          <form className="inline" onSubmit={createTeam}>
            <input
              placeholder="New team name"
              value={newTeamName}
              onChange={(e) => setNewTeamName(e.target.value)}
            />
            <button type="submit">+ Team</button>
          </form>
        </div>
      </header>

      {error && <p className="error global">{error}</p>}

      {teamId == null ? (
        <p className="hint big-hint">Create a team to get started.</p>
      ) : (
        <>
          <nav className="tabs">
            {TABS.map((t) => (
              <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>
                {t}
              </button>
            ))}
          </nav>

          {tab === "Roster" && (
            <RosterScreen teamId={teamId} players={players} reload={reloadTeam} />
          )}
          {tab === "Lineups" && (
            <LineupBuilder
              teamId={teamId}
              players={players}
              lineups={lineups}
              reload={reloadTeam}
              onView={goToRotations}
            />
          )}
          {tab === "Rotations" && (
            <>
              <div className="screen lineup-picker">
                <label>
                  Lineup:{" "}
                  <select value={viewLineupId ?? ""} onChange={(e) => setViewLineupId(Number(e.target.value))}>
                    <option value="" disabled>pick a lineup</option>
                    {lineups.map((l) => (
                      <option key={l.id} value={l.id}>{l.name} ({l.system})</option>
                    ))}
                  </select>
                </label>
              </div>
              <RotationViewer lineupId={viewLineupId} />
            </>
          )}
        </>
      )}
    </div>
  );
}
