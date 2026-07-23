// Coach sign-in / account creation. Mirrors the Player Zone's AuthScreen;
// same users table server-side, role='coach'. The first coach account
// claims any teams created before accounts existed.

import { useState } from "react";
import { api, setCoachToken } from "../api.js";

export default function CoachAuth({ onAuthed, onBack, initialMode = "login" }) {
  const [creating, setCreating] = useState(initialMode === "register");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = { username, password, display_name: displayName };
      const res = creating ? await api.coachRegister(body) : await api.coachLogin(body);
      setCoachToken(res.token);
      onAuthed(res);
    } catch (err) {
      setError(err.message.replace(/^\d+: /, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="pz-auth">
      <div className="card pz-auth-card">
        <h2>{creating ? "Create your coach account" : "Coach sign in"}</h2>
        <p className="hint">
          {creating
            ? "Your teams live under your account — only you can see and edit them."
            : "Sign in to get to your teams."}
        </p>
        <form className="pz-auth-form" onSubmit={submit}>
          <input placeholder="Username" value={username} autoComplete="username"
                 onChange={(e) => setUsername(e.target.value)} />
          {creating && (
            <input placeholder="Your name (shown in the app)" value={displayName}
                   onChange={(e) => setDisplayName(e.target.value)} />
          )}
          <input type="password" placeholder="Password (6+ characters)" value={password}
                 autoComplete={creating ? "new-password" : "current-password"}
                 onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="error">{error}</p>}
          <button className="primary" disabled={busy || !username || password.length < 6}>
            {creating ? "Create account" : "Sign in"}
          </button>
        </form>
        <button className="link" onClick={() => { setCreating(!creating); setError(null); }}>
          {creating ? "Have an account? Sign in" : "New here? Create a coach account"}
        </button>
        {onBack && <button className="link" onClick={onBack}>← Back</button>}
      </div>
    </div>
  );
}
