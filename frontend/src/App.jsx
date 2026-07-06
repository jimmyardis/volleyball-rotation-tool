import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import RosterScreen from "./components/RosterScreen.jsx";
import LineupBuilder from "./components/LineupBuilder.jsx";
import RotationViewer from "./components/RotationViewer.jsx";
import HelpPanel from "./components/HelpPanel.jsx";
import CoachChat from "./components/CoachChat.jsx";
import SimulationScreen from "./components/SimulationScreen.jsx";
import Volleyball from "./components/Volleyball.jsx";

const TABS = ["Roster", "Lineups", "Rotations", "Simulate"];

// The guided path. Each step knows when it's complete and which tab it lives on.
function steps({ teamId, players, lineups }) {
  return [
    { n: 1, label: "Create a team", tab: null, done: teamId != null },
    { n: 2, label: "Add 6+ players", tab: "Roster", done: players.length >= 6 },
    { n: 3, label: "Build a lineup", tab: "Lineups", done: lineups.length >= 1 },
    { n: 4, label: "View rotations", tab: "Rotations", done: false },
  ];
}

function Stepper({ items, onJump }) {
  return (
    <ol className="stepper">
      {items.map((s) => (
        <li key={s.n} className={s.done ? "done" : ""}>
          <button className="step" disabled={!s.tab} onClick={() => s.tab && onJump(s.tab)}>
            <span className="step-dot">{s.n}</span>
            <span className="step-label">{s.label}</span>
          </button>
        </li>
      ))}
    </ol>
  );
}

export default function App() {
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState(null);
  const [players, setPlayers] = useState([]);
  const [lineups, setLineups] = useState([]);
  const [tab, setTab] = useState("Roster");
  const [viewLineupId, setViewLineupId] = useState(null);
  const [newTeamName, setNewTeamName] = useState("");
  const [error, setError] = useState(null);
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    api.listTeams()
      .then((t) => { setTeams(t); if (t.length && teamId == null) setTeamId(t[0].id); })
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const reloadTeam = useCallback(async () => {
    if (teamId == null) return;
    const [ps, ls] = await Promise.all([api.listPlayers(teamId), api.listLineups(teamId)]);
    setPlayers(ps); setLineups(ls);
  }, [teamId]);

  useEffect(() => { reloadTeam(); }, [reloadTeam]);

  async function createTeam(e) {
    e.preventDefault();
    if (!newTeamName.trim()) return;
    const team = await api.createTeam({ name: newTeamName.trim() });
    setNewTeamName("");
    setTeams(await api.listTeams());
    setTeamId(team.id);
    setTab("Roster");
  }

  function goToRotations(lineupId) { setViewLineupId(lineupId); setTab("Rotations"); }

  const stepItems = steps({ teamId, players, lineups });
  const nextStep = stepItems.find((s) => !s.done);

  // a friendly nudge toward the next thing to do
  const nudge =
    teamId == null ? "Start by creating a team below."
    : players.length < 6 ? `Add ${6 - players.length} more player${6 - players.length === 1 ? "" : "s"} on the Roster tab (you need 6 to fill a lineup).`
    : lineups.length === 0 ? "Now build a lineup: name it, pick a system, and assign your six to the zones."
    : "You're set — open Rotations to step through all six and try the Serving / Receiving / Base views.";

  return (
    <div className="app">
      <header>
        <h1 className="brand"><Volleyball size={26} /> Rotation &amp; Lineup Tool</h1>
        <div className="team-bar">
          <a className="pz-switch" href="#player">Player Zone</a>
          <button className="ghost help-btn" onClick={() => setShowHelp(true)} title="How this app works">Guide</button>
          <select value={teamId ?? ""} onChange={(e) => setTeamId(Number(e.target.value))}>
            <option value="" disabled>Select a team</option>
            {teams.map((t) => <option key={t.id} value={t.id}>{t.name}{t.season ? ` (${t.season})` : ""}</option>)}
          </select>
          <form className="inline" onSubmit={createTeam}>
            <input placeholder="New team name" value={newTeamName} onChange={(e) => setNewTeamName(e.target.value)} />
            <button type="submit">Add team</button>
          </form>
        </div>
      </header>

      {showHelp && <HelpPanel onClose={() => setShowHelp(false)} />}
      <CoachChat
        teamId={teamId}
        lineupId={viewLineupId}
        onLineupCreated={() => reloadTeam()}
        onViewLineup={(id) => { setViewLineupId(id); setTab("Rotations"); }}
      />

      <Stepper items={stepItems} onJump={setTab} />
      {nextStep && (
        <p className="nudge">{nudge} <button className="link inline-link" onClick={() => setShowHelp(true)}>New here? Open the guide.</button></p>
      )}

      {error && <p className="error global">{error}</p>}

      {teamId == null ? (
        <p className="hint big-hint">Create a team above to get started.</p>
      ) : (
        <>
          <nav className="tabs">
            {TABS.map((t) => (
              <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>{t}</button>
            ))}
          </nav>

          {tab === "Roster" && <RosterScreen teamId={teamId} players={players} reload={reloadTeam} />}
          {tab === "Lineups" && (
            <LineupBuilder teamId={teamId} players={players} lineups={lineups} reload={reloadTeam} onView={goToRotations} />
          )}
          {tab === "Rotations" && (
            <>
              <div className="screen lineup-picker">
                {lineups.length === 0 ? (
                  <p className="hint">No lineups yet — build one on the <button className="link inline-link" onClick={() => setTab("Lineups")}>Lineups</button> tab first.</p>
                ) : (
                  <label>Lineup:{" "}
                    <select value={viewLineupId ?? ""} onChange={(e) => setViewLineupId(Number(e.target.value))}>
                      <option value="" disabled>pick a lineup</option>
                      {lineups.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.system})</option>)}
                    </select>
                  </label>
                )}
              </div>
              <RotationViewer lineupId={viewLineupId} />
            </>
          )}
          {tab === "Simulate" && (
            lineups.length === 0
              ? <p className="hint big-hint">Build a lineup first, then come back to simulate it.</p>
              : <SimulationScreen lineups={lineups} />
          )}
        </>
      )}
    </div>
  );
}
