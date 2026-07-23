// First page: Log in or Sign up, then who are you? Players go to the Player
// Zone (its own sign-in, opened in the right mode); coaches sign in / create
// an account right here, then set up their team.

import { useState } from "react";
import Volleyball from "./Volleyball.jsx";
import CoachAuth from "./CoachAuth.jsx";

// clipboard, in the same one-color outline style as the volleyball mark
function Clipboard({ size = 34 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none"
         stroke="currentColor" strokeWidth="5" strokeLinecap="round"
         strokeLinejoin="round" role="img" aria-label="Coach clipboard">
      <rect x="18" y="14" width="64" height="76" rx="8" />
      <rect x="36" y="6" width="28" height="16" rx="5" />
      <path d="M32 40 H 68" />
      <path d="M32 56 H 68" />
      <path d="M32 72 H 54" />
    </svg>
  );
}

// a volleyball net running across the bottom of the page — her accent idea
function NetBand() {
  return (
    <svg className="landing-net" viewBox="0 0 1200 96" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <pattern id="net-mesh" width="30" height="30" patternUnits="userSpaceOnUse">
          <path d="M0 0 H30 M0 0 V30" stroke="currentColor" strokeWidth="1.5" fill="none" />
        </pattern>
      </defs>
      <rect x="0" y="0" width="1200" height="10" rx="3" fill="currentColor" opacity="0.9" />
      <rect x="0" y="10" width="1200" height="86" fill="url(#net-mesh)" opacity="0.45" />
    </svg>
  );
}

export default function Landing({ onCoachAuthed }) {
  const [intent, setIntent] = useState(null); // null | "login" | "register"
  const [role, setRole] = useState(null);     // null | "coach"

  function pickRole(which) {
    if (which === "player") {
      // hand the chosen mode to the Player Zone so it opens the right form
      sessionStorage.setItem("pz_auth_intent", intent);
      location.hash = "#player";
    } else {
      setRole("coach");
    }
  }

  return (
    <div className="app landing">
      <header>
        <h1>Pepper Volleyball</h1>
      </header>

      {intent === null && (
        <div className="landing-choice">
          <div className="landing-hero">
            <span className="landing-hero-mark" aria-hidden="true"><Volleyball size={64} /></span>
            <h2>Practice · Progress · Thrive</h2>
            <p className="hint">Training plans, drills, film feedback, and a personal AI coach for players —
              rosters, rotations, and game simulations for coaches.</p>
          </div>
          <div className="landing-intent">
            <button className="pz-cta" onClick={() => setIntent("login")}>Log in</button>
            <button className="pz-cta ghost" onClick={() => setIntent("register")}>Sign up</button>
          </div>
        </div>
      )}

      {intent !== null && role === null && (
        <div className="landing-choice">
          <h2>Are you a coach or a player?</h2>
          <p className="hint">Coaches run rotations, lineups, and simulations. Players get their own training zone.</p>
          <div className="landing-cards">
            <button className="landing-card" onClick={() => pickRole("coach")}>
              <span className="landing-icon" aria-hidden="true"><Clipboard /></span>
              <span className="landing-title">I'm a coach</span>
              <span className="landing-sub">Roster, lineups, rotations, game simulations, notes</span>
            </button>
            <button className="landing-card" onClick={() => pickRole("player")}>
              <span className="landing-icon" aria-hidden="true"><Volleyball size={34} /></span>
              <span className="landing-title">I'm a player</span>
              <span className="landing-sub">Your training plan, drills, film room, and personal coach</span>
            </button>
          </div>
          <button className="link" onClick={() => setIntent(null)}>← Back</button>
        </div>
      )}

      {role === "coach" && (
        <CoachAuth onAuthed={onCoachAuthed} initialMode={intent} onBack={() => setRole(null)} />
      )}

      <NetBand />
    </div>
  );
}
