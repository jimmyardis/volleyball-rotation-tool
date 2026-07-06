import { useState } from "react";
import { playerApi, setToken } from "./api.js";

export default function AuthScreen({ onAuthed }) {
  const [mode, setMode] = useState("login");
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
      onAuthed();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen pz-auth">
      <div className="card pz-auth-card">
        <h2>{mode === "login" ? "Welcome back" : "Create your player account"}</h2>
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
          <button type="submit" disabled={busy}>
            {busy ? "One sec…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        <button className="link inline-link" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}>
          {mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
