// Player Zone: the player-facing surface (spec: player-side-spec.md MVP).
// Lives behind #player in the same SPA; the player's position color becomes
// their personal accent throughout.

import { useCallback, useEffect, useState } from "react";
import { roleColor, roleMeta } from "../roles.js";
import Volleyball from "../components/Volleyball.jsx";
import { playerApi, getToken, setToken } from "./api.js";
import AuthScreen from "./AuthScreen.jsx";
import Onboarding from "./Onboarding.jsx";
import HomeScreen from "./HomeScreen.jsx";
import CoachScreen from "./CoachScreen.jsx";
import PlayerCoachBubble from "./PlayerCoachBubble.jsx";
import PlanScreen from "./PlanScreen.jsx";
import TrainScreen from "./TrainScreen.jsx";
import ProgressScreen from "./ProgressScreen.jsx";
import ProfileScreen from "./ProfileScreen.jsx";

const TABS = ["Home", "Coach", "Plan", "Train", "Progress", "Profile"];

export default function PlayerApp() {
  const [me, setMe] = useState(null);        // null = loading/anon
  const [authed, setAuthed] = useState(!!getToken());
  const [tab, setTab] = useState("Home");
  const [error, setError] = useState(null);
  // ONE coach conversation, shared by the floating bubble and the Coach tab
  const [coachThread, setCoachThread] = useState([]);

  const loadMe = useCallback(async () => {
    if (!getToken()) { setMe(null); setAuthed(false); return; }
    try {
      setMe(await playerApi.me());
      setAuthed(true);
    } catch (e) {
      setMe(null);
      if (e.signedOut) setAuthed(false);
      else setError(e.message);
    }
  }, []);

  useEffect(() => { loadMe(); }, [loadMe]);

  async function signOut() {
    try { await playerApi.logout(); } catch { /* token already dead */ }
    setToken(null);
    setMe(null);
    setAuthed(false);
    setTab("Home");
  }

  const accent = me?.profile?.position ? roleColor(me.profile.position) : null;
  const posMeta = me?.profile?.position ? roleMeta(me.profile.position) : null;

  return (
    <div className="app player-zone" style={accent ? { "--accent": accent, "--accent-ink": posMeta.ink } : undefined}>
      <header>
        <h1 className="brand"><Volleyball size={26} /> Player Zone</h1>
        <div className="team-bar">
          {me && <span className="pz-whoami">{me.user.display_name}{me.profile?.position ? ` · ${me.profile.position}` : ""}</span>}
          {me && <button className="ghost" onClick={signOut}>Sign out</button>}
          <a className="pz-switch" href="#" onClick={(e) => { e.preventDefault(); location.hash = ""; }}>Coach tools</a>
        </div>
      </header>

      {error && <p className="error global">{error}</p>}

      {!authed && <AuthScreen onAuthed={loadMe} />}

      {authed && me && (!me.profile?.position || !me.has_assessment) && (
        <Onboarding me={me} onDone={loadMe} />
      )}

      {authed && me && me.profile?.position && me.has_assessment && (
        <>
          <nav className="tabs">
            {TABS.map((t) => (
              <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>{t}</button>
            ))}
          </nav>
          {tab === "Home" && <HomeScreen me={me} goTo={setTab} />}
          {tab === "Coach" && <CoachScreen me={me} messages={coachThread} setMessages={setCoachThread} />}
          {tab === "Plan" && <PlanScreen me={me} goTo={setTab} />}
          {tab === "Train" && <TrainScreen me={me} />}
          {tab === "Progress" && <ProgressScreen me={me} reloadMe={loadMe} />}
          {tab === "Profile" && <ProfileScreen me={me} reloadMe={loadMe} onSignOut={signOut} />}

          {/* the coach travels with you — hidden on the Coach tab itself */}
          {tab !== "Coach" && (
            <PlayerCoachBubble
              messages={coachThread}
              setMessages={setCoachThread}
              onExpand={() => setTab("Coach")}
            />
          )}
        </>
      )}

      {authed && !me && !error && <p className="hint big-hint">Loading…</p>}
    </div>
  );
}
