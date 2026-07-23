import { useCallback, useEffect, useState } from "react";
import { api, getCoachToken, setCoachToken } from "./api.js";
import RosterScreen from "./components/RosterScreen.jsx";
import LineupBuilder from "./components/LineupBuilder.jsx";
import RotationViewer from "./components/RotationViewer.jsx";
import HelpPanel from "./components/HelpPanel.jsx";
import CoachChat from "./components/CoachChat.jsx";
import SimulationScreen from "./components/SimulationScreen.jsx";
import NotesScreen, { QuickNotes } from "./components/Notes.jsx";
import Landing from "./components/Landing.jsx";
import TeamSetup from "./components/TeamSetup.jsx";
import Loader from "./components/Loader.jsx";

const TABS = ["Roster", "Lineups", "Rotations", "Simulate", "Notes"];

export default function App() {
  const [authed, setAuthed] = useState(() => !!getCoachToken());
  const [me, setMe] = useState(null);
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState(null);
  const [players, setPlayers] = useState([]);
  const [lineups, setLineups] = useState([]);
  const [tab, setTab] = useState("Roster");
  const [viewLineupId, setViewLineupId] = useState(null);
  const [showWizard, setShowWizard] = useState(false);
  const [error, setError] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // a 401 anywhere means the coach session died — back to the landing page
  const handleError = useCallback((e) => {
    if (e.status === 401) {
      setCoachToken(null);
      setAuthed(false);
      setMe(null);
    } else {
      setError(e.message);
    }
  }, []);

  const loadTeams = useCallback(async () => {
    try {
      const [meRes, t] = await Promise.all([api.coachMe(), api.listTeams()]);
      setMe(meRes.user);
      setTeams(t);
      setTeamId((cur) => (cur != null && t.some((x) => x.id === cur) ? cur : t[0]?.id ?? null));
      setShowWizard(t.length === 0);
      setLoaded(true);
    } catch (e) {
      handleError(e);
    }
  }, [handleError]);

  useEffect(() => {
    if (authed) loadTeams();
  }, [authed, loadTeams]);

  const reloadTeam = useCallback(async () => {
    if (teamId == null) return;
    try {
      const [ps, ls] = await Promise.all([api.listPlayers(teamId), api.listLineups(teamId)]);
      setPlayers(ps); setLineups(ls);
    } catch (e) {
      handleError(e);
    }
  }, [teamId, handleError]);

  useEffect(() => { reloadTeam(); }, [reloadTeam]);

  async function signOut() {
    try { await api.coachLogout(); } catch { /* token already dead */ }
    setCoachToken(null);
    setAuthed(false);
    setMe(null);
    setTeams([]); setTeamId(null); setPlayers([]); setLineups([]);
    setLoaded(false);
  }

  if (!authed) {
    return <Landing onCoachAuthed={() => { setAuthed(true); setTab("Roster"); }} />;
  }

  function goToRotations(lineupId) { setViewLineupId(lineupId); setTab("Rotations"); }

  // a friendly nudge toward the next thing to do (the numbered stepper is
  // gone — the product owner found it visually noisy; one sentence suffices)
  const setupDone = teamId != null && players.length >= 6 && lineups.length >= 1;
  const nudge =
    teamId == null ? "Start by setting up a team."
    : players.length < 6 ? `Add ${6 - players.length} more player${6 - players.length === 1 ? "" : "s"} on the Roster tab (you need 6 to fill a lineup).`
    : lineups.length === 0 ? "Now build a lineup: name it, pick a system, and assign your six to the zones."
    : "You're set — open Rotations to step through all six and try the Serving / Receiving / Base views.";

  return (
    <div className="app">
      <header>
        <h1>Pepper Volleyball</h1>
        <div className="team-bar">
          {me && <span className="pz-whoami">{me.display_name}</span>}
          <button className="ghost help-btn" onClick={() => setShowHelp(true)} title="How this app works">Guide</button>
          {teams.length > 0 && (
            <select value={teamId ?? ""} onChange={(e) => setTeamId(Number(e.target.value))}>
              <option value="" disabled>Select a team</option>
              {teams.map((t) => <option key={t.id} value={t.id}>{t.name}{t.season ? ` (${t.season})` : ""}</option>)}
            </select>
          )}
          <button className="ghost" onClick={() => setShowWizard(true)}>+ New team</button>
          <button className="ghost" onClick={signOut}>Sign out</button>
        </div>
      </header>

      {showHelp && <HelpPanel onClose={() => setShowHelp(false)} />}
      <CoachChat
        teamId={teamId}
        lineupId={viewLineupId}
        onLineupCreated={() => reloadTeam()}
        onViewLineup={(id) => { setViewLineupId(id); setTab("Rotations"); }}
      />

      {error && <p className="error global">{error}</p>}

      {showWizard ? (
        <TeamSetup
          onCancel={teams.length ? () => setShowWizard(false) : null}
          onDone={async (newTeamId) => {
            setShowWizard(false);
            const t = await api.listTeams();
            setTeams(t);
            setTeamId(newTeamId);
            setTab("Roster");
          }}
        />
      ) : !loaded ? (
        <Loader label="Loading your teams…" />
      ) : teamId == null ? (
        <p className="hint big-hint">Set up a team to get started.</p>
      ) : (
        <>
          {!setupDone && (
            <p className="nudge">{nudge} <button className="link inline-link" onClick={() => setShowHelp(true)}>New here? Open the guide.</button></p>
          )}

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
              {viewLineupId != null && (
                <div className="card">
                  <QuickNotes teamId={teamId} lineupId={viewLineupId}
                              title={`Notes on ${lineups.find((l) => l.id === viewLineupId)?.name ?? "this lineup"}`} />
                </div>
              )}
            </>
          )}
          {tab === "Simulate" && (
            lineups.length === 0
              ? <p className="hint big-hint">Build a lineup first, then come back to simulate it.</p>
              : <SimulationScreen lineups={lineups}
                                  team={teams.find((t) => t.id === teamId)}
                                  onTeamChanged={loadTeams} />
          )}
          {tab === "Notes" && <NotesScreen teamId={teamId} players={players} lineups={lineups} />}
        </>
      )}
    </div>
  );
}
