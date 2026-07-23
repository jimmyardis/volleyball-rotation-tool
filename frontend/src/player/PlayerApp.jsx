// Player Zone: the player-facing surface (spec: player-side-spec.md MVP).
// Lives behind #player in the same SPA and shares the app's brand accent;
// the player's position shows in labels and their token, not by recoloring.

import { useCallback, useEffect, useState } from "react";
import { playerApi, getToken, setToken } from "./api.js";
import AuthScreen from "./AuthScreen.jsx";
import Welcome from "./Welcome.jsx";
import WhoAreYou from "../components/WhoAreYou.jsx";
import Onboarding from "./Onboarding.jsx";
import HomeScreen from "./HomeScreen.jsx";
import CoachScreen from "./CoachScreen.jsx";
import PlayerCoachBubble from "./PlayerCoachBubble.jsx";
import PlanScreen from "./PlanScreen.jsx";
import TrainScreen from "./TrainScreen.jsx";
import FilmScreen from "./FilmScreen.jsx";
import ProgressScreen from "./ProgressScreen.jsx";
import ProfileScreen from "./ProfileScreen.jsx";

const TABS = ["Home", "Coach", "Plan", "Train", "Film", "Progress", "Profile"];

// The swipeable welcome tour shows once per device; after that, signed-out
// users go straight to sign-in (with a link back to the tour).
const WELCOME_SEEN = "pz_welcome_seen";
const THEME_KEY = "pz_theme";               // "classic" | "intense", per device

export default function PlayerApp() {
  const [me, setMe] = useState(null);        // null = loading/anon
  const [authed, setAuthed] = useState(!!getToken());
  const [authView, setAuthView] = useState(() => {
    // the web landing ("Log in" / "Sign up" → coach or player) hands its
    // intent over so we open the right form directly, skipping the tour
    const intent = sessionStorage.getItem("pz_auth_intent");
    if (!getToken() && (intent === "login" || intent === "register")) {
      sessionStorage.removeItem("pz_auth_intent");
      localStorage.setItem(WELCOME_SEEN, "1");
      return intent;
    }
    return getToken() || localStorage.getItem(WELCOME_SEEN) ? "login" : "welcome";
  });
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || "classic");
  useEffect(() => { localStorage.setItem(THEME_KEY, theme); }, [theme]);
  // the mode (login/register) chosen on the tour, carried through the
  // coach-or-player question that follows it
  const [pendingMode, setPendingMode] = useState("register");
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

  return (
    <div className="app player-zone" data-theme={theme}>
      {authed && (
        <header>
          <h1>Pepper{theme === "intense" && <span className="pz-butterfly" aria-hidden="true">🦋</span>}</h1>
          <div className="team-bar">
            {me && <span className="pz-whoami">{me.user.display_name}{me.profile?.position ? ` · ${me.profile.position}` : ""}</span>}
            {me && <button className="ghost" onClick={signOut}>Sign out</button>}
            <a className="pz-switch" href="#" onClick={(e) => { e.preventDefault(); location.hash = ""; }}>Coach tools</a>
          </div>
        </header>
      )}

      {error && <p className="error global">{error}</p>}

      {!authed && authView === "welcome" && (
        <Welcome onStart={(mode) => {
          localStorage.setItem(WELCOME_SEEN, "1");
          setPendingMode(mode);
          setAuthView("role");           // her flow: tour → coach or player? → sign-in
        }} />
      )}
      {!authed && authView === "role" && (
        <WhoAreYou
          onPick={(role) => {
            if (role === "player") setAuthView(pendingMode);
            else {
              // coach tools live on the web side of the SPA — carry the mode over
              sessionStorage.setItem("coach_auth_intent", pendingMode);
              location.hash = "";
            }
          }}
          onBack={() => setAuthView("welcome")}
        />
      )}
      {!authed && authView !== "welcome" && authView !== "role" && (
        <AuthScreen key={authView} initialMode={authView} onAuthed={loadMe}
                    onBack={() => setAuthView("welcome")} />
      )}

      {authed && me && (!me.profile?.position || !me.has_assessment) && (
        <Onboarding me={me} onDone={loadMe} theme={theme} setTheme={setTheme} />
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
          {tab === "Film" && <FilmScreen me={me} />}
          {tab === "Progress" && <ProgressScreen me={me} reloadMe={loadMe} />}
          {tab === "Profile" && <ProfileScreen me={me} reloadMe={loadMe} onSignOut={signOut} theme={theme} setTheme={setTheme} />}

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
