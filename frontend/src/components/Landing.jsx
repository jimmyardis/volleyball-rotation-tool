// First page: who are you? Players go to the Player Zone (its own sign-in);
// coaches sign in / create an account right here, then set up their team.

import { useState } from "react";
import Volleyball from "./Volleyball.jsx";
import CoachAuth from "./CoachAuth.jsx";

export default function Landing({ onCoachAuthed }) {
  const [mode, setMode] = useState(null); // null | "coach"

  return (
    <div className="app landing">
      <header>
        <h1 className="brand"><Volleyball size={26} /> Volleyball Team Tool</h1>
      </header>

      {mode === null && (
        <div className="landing-choice">
          <h2>Who are you?</h2>
          <p className="hint">Coaches run rotations, lineups, and simulations. Players get their own training zone.</p>
          <div className="landing-cards">
            <button className="landing-card" onClick={() => setMode("coach")}>
              <span className="landing-emoji" aria-hidden="true">📋</span>
              <span className="landing-title">I'm a coach</span>
              <span className="landing-sub">Roster, lineups, rotations, game simulations, notes</span>
            </button>
            <button className="landing-card" onClick={() => { location.hash = "#player"; }}>
              <span className="landing-emoji" aria-hidden="true">🏐</span>
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
