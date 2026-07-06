import { useState } from "react";
import { ROLES } from "../api.js";
import { playerApi } from "./api.js";

const BANDS = [
  { code: "rec", label: "Rec league" },
  { code: "middle_school", label: "Middle school" },
  { code: "high_school", label: "High school" },
  { code: "club", label: "Club" },
];

export default function ProfileScreen({ me, reloadMe, onSignOut }) {
  const p = me.profile ?? {};
  const [form, setForm] = useState({
    position: p.position ?? "OH",
    secondary_position: p.secondary_position ?? "",
    level_band: p.level_band ?? "high_school",
  });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  const changedPosition = form.position !== p.position;

  async function save(e) {
    e.preventDefault();
    setError(null); setSaved(false);
    try {
      await playerApi.updateProfile({
        position: form.position,
        secondary_position: form.secondary_position || null,
        level_band: form.level_band,
      });
      setSaved(true);
      reloadMe();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="screen">
      <h2>Profile</h2>
      <form className="card" onSubmit={save}>
        <p><strong>{me.user.display_name}</strong> <span className="dim">@{me.user.username}</span></p>
        <div className="form-row">
          <label>Position{" "}
            <select value={form.position} onChange={(e) => setForm({ ...form, position: e.target.value })}>
              {ROLES.map((r) => <option key={r.code} value={r.code}>{r.code} — {r.label}</option>)}
            </select>
          </label>
          <label>Second position{" "}
            <select value={form.secondary_position} onChange={(e) => setForm({ ...form, secondary_position: e.target.value })}>
              <option value="">(none)</option>
              {ROLES.map((r) => <option key={r.code} value={r.code}>{r.code}</option>)}
            </select>
          </label>
          <label>Level{" "}
            <select value={form.level_band} onChange={(e) => setForm({ ...form, level_band: e.target.value })}>
              {BANDS.map((b) => <option key={b.code} value={b.code}>{b.label}</option>)}
            </select>
          </label>
        </div>
        <div className="form-row">
          <button type="submit">Save</button>
          {saved && <span className="ok">Saved.{changedPosition ? "" : ""}</span>}
          {error && <span className="error">{error}</span>}
        </div>
        {changedPosition && (
          <p className="hint">Changing position? Rebuild your plan from the Plan tab so it trains the right skills.</p>
        )}
      </form>

      <div className="card">
        <span className="pz-card-title">Account</span>
        <p className="hint">Your data is private to you on this server. Video features come later — nothing is recorded today.</p>
        <button className="ghost danger" onClick={onSignOut}>Sign out</button>
      </div>
    </div>
  );
}
