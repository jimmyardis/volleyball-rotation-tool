import { useState } from "react";
import { playerApi, setToken } from "./api.js";
import Volleyball from "../components/Volleyball.jsx";
import { success } from "../haptics.js";

export default function AuthScreen({ onAuthed, initialMode = "login", onBack }) {
  const [mode, setMode] = useState(initialMode);
  const [form, setForm] = useState({ username: "", password: "", display_name: "" });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setError(null); setBusy(true);
    try {
      const res = mode === "login"
        ? await playerApi.login({ username: form.username, password: form.password })
        : await playerApi.register(form);
      setToken(res.token);
      success();
      onAuthed();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen pz-auth">
      <div className="pz-auth-card">
        <div className="pz-auth-brand">
          <Volleyball size={54} />
          <span className="pz-auth-wordmark">Pepper</span>
        </div>
        <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
        <p className="hint">
          Your own coach, plan, and progress — no coach account needed.
        </p>
        <form onSubmit={submit} className="pz-auth-form">
          <input placeholder="Username" autoComplete="username" value={form.username} onChange={set("username")} />
          {mode === "register" && (
            <input placeholder="What should Coach call you? (optional)" value={form.display_name} onChange={set("display_name")} />
          )}
          <input type="password" placeholder="Password (6+ characters)" autoComplete={mode === "login" ? "current-password" : "new-password"}
                 value={form.password} onChange={set("password")} />
          <button type="submit" className="pz-cta" disabled={busy}>
            {busy ? "One sec…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        <button className="link inline-link" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}>
          {mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>
        {onBack && (
          <button className="link inline-link pz-auth-back" onClick={onBack}>‹ Back to the tour</button>
        )}
      </div>
    </div>
  );
}
