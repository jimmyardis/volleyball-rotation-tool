// The front door on the web: the same dynamic welcome tour the app opens
// with (logo, three slides, Get started), then the coach-or-player question,
// then the right sign-in in the right mode. Her spec, session 15c.

import { useState } from "react";
import Welcome from "../player/Welcome.jsx";
import WhoAreYou from "./WhoAreYou.jsx";
import CoachAuth from "./CoachAuth.jsx";
import Volleyball from "./Volleyball.jsx";

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
  // someone in the Player Zone (or native app) who answered "coach" arrives
  // here with the mode they already chose
  const [mode, setMode] = useState(() => sessionStorage.getItem("coach_auth_intent") || "login");
  const [step, setStep] = useState(() => {
    if (sessionStorage.getItem("coach_auth_intent")) {
      sessionStorage.removeItem("coach_auth_intent");
      return "coach-auth";
    }
    return "welcome";
  });

  function pickRole(role) {
    if (role === "player") {
      // hand the chosen mode to the Player Zone so it opens the right form
      // (and doesn't replay the tour they just watched)
      sessionStorage.setItem("pz_auth_intent", mode);
      localStorage.setItem("pz_welcome_seen", "1");
      location.hash = "#player";
    } else {
      setStep("coach-auth");
    }
  }

  return (
    <div className="app landing">
      <header>
        <h1>Pepper<Volleyball size={20} style={{ verticalAlign: "-3px", marginLeft: "0.45rem" }} /></h1>
      </header>

      {step === "welcome" && (
        <Welcome onStart={(m) => { setMode(m); setStep("role"); }} />
      )}

      {step === "role" && (
        <WhoAreYou onPick={pickRole} onBack={() => setStep("welcome")} />
      )}

      {step === "coach-auth" && (
        <CoachAuth onAuthed={onCoachAuthed} initialMode={mode} onBack={() => setStep("role")} />
      )}

      <NetBand />
    </div>
  );
}
