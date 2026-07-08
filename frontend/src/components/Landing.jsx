// First page: who are you? Players go to the Player Zone (its own sign-in);
// coaches sign in / create an account right here, then set up their team.

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

export default function Landing({ onCoachAuthed }) {
  const [mode, setMode] = useState(null); // null | "coach"

  return (
    <div className="app landing">
      <header>
        <h1>Volleyball Team Tool</h1>
      </header>

      {mode === null && (
        <div className="landing-choice">
          <h2>Who are you?</h2>
          <p className="hint">Coaches run rotations, lineups, and simulations. Players get their own training zone.</p>
          <div className="landing-cards">
            <button className="landing-card" onClick={() => setMode("coach")}>
              <span className="landing-icon" aria-hidden="true"><Clipboard /></span>
              <span className="landing-title">I'm a coach</span>
              <span className="landing-sub">Roster, lineups, rotations, game simulations, notes</span>
            </button>
            <button className="landing-card" onClick={() => { location.hash = "#player"; }}>
              <span className="landing-icon" aria-hidden="true"><Volleyball size={34} /></span>
              <span className="landing-title">I'm a player</span>
              <span className="landing-sub">Your training plan, drills, progress, and personal coach</span>
            </button>
          </div>
        </div>
      )}

      {mode === "coach" && (
        <CoachAuth onAuthed={onCoachAuthed} onBack={() => setMode(null)} />
      )}
    </div>
  );
}
