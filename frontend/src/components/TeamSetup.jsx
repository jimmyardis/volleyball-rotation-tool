// Quick 3-step team setup for a fresh coach account:
//   1) team name + season  2) rapid roster entry  3) offense system.
// Under two minutes; ratings and mistake tags come later on player cards.

import { useState } from "react";
import { api, ROLES } from "../api.js";

const EMPTY_ROW = { name: "", jersey: "", role: "OH" };

export default function TeamSetup({ onDone, onCancel }) {
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [season, setSeason] = useState("");
  const [rows, setRows] = useState([{ ...EMPTY_ROW }]);
  const [system, setSystem] = useState("unsure");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const filled = rows.filter((r) => r.name.trim());

  function setRow(i, field, value) {
    setRows((rs) => {
      const next = rs.map((r, j) => (j === i ? { ...r, [field]: value } : r));
      // typing in the last row grows a fresh one below it
      if (i === rs.length - 1 && field === "name" && value.trim()) next.push({ ...EMPTY_ROW });
      return next;
    });
  }

  async function finish() {
    setBusy(true);
    setError(null);
    try {
      const team = await api.createTeam({ name: name.trim(), season: season.trim() || null });
      for (const r of filled) {
        await api.createPlayer(team.id, {
          name: r.name.trim(),
          jersey_number: r.jersey === "" ? null : Number(r.jersey),
          primary_role: r.role,
          is_libero: r.role === "L",
        });
      }
      const sys = system === "unsure" ? "5-1" : system;
      await api.createLineup(team.id, { name: `Base ${sys}`, system: sys });
      onDone(team.id, { system, playerCount: filled.length });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="card setup-wizard">
      <div className="setup-head">
        <h2>Set up your team</h2>
        <span className="dim">step {step} of 3</span>
      </div>

      {step === 1 && (
        <>
          <div className="pz-auth-form">
            <input placeholder="Team name (e.g. Lakeside 14U)" value={name}
                   onChange={(e) => setName(e.target.value)} autoFocus />
            <input placeholder="Season (optional, e.g. 2026 club)" value={season}
                   onChange={(e) => setSeason(e.target.value)} />
          </div>
          <div className="setup-nav">
            {onCancel && <button className="ghost" onClick={onCancel}>Cancel</button>}
            <button className="primary" disabled={!name.trim()} onClick={() => setStep(2)}>Next</button>
          </div>
        </>
      )}

      {step === 2 && (
        <>
          <p className="hint">Add your players — one line each. You need 6 to fill a lineup; you can always add more later.</p>
          <div className="setup-roster">
            {rows.map((r, i) => (
              <div className="setup-row" key={i}>
                <input className="setup-jersey" placeholder="#" inputMode="numeric" value={r.jersey}
                       onChange={(e) => setRow(i, "jersey", e.target.value.replace(/\D/g, ""))} />
                <input className="setup-name" placeholder={i === 0 ? "Player name" : "Another player…"}
                       value={r.name} onChange={(e) => setRow(i, "name", e.target.value)} />
                <select value={r.role} onChange={(e) => setRow(i, "role", e.target.value)}>
                  {ROLES.map((role) => <option key={role.code} value={role.code}>{role.code}</option>)}
                </select>
              </div>
            ))}
          </div>
          <p className="dim">{filled.length} player{filled.length === 1 ? "" : "s"} so far{filled.length < 6 ? ` — ${6 - filled.length} more to fill a court` : " — that's a full court ✓"}</p>
          <div className="setup-nav">
            <button className="ghost" onClick={() => setStep(1)}>Back</button>
            <button className="primary" onClick={() => setStep(3)}>Next</button>
          </div>
        </>
      )}

      {step === 3 && (
        <>
          <p className="hint">How do you run your offense? This names your first lineup — nothing is locked in.</p>
          <div className="setup-systems">
            {[
              { code: "5-1", label: "5-1", sub: "One setter runs every rotation" },
              { code: "6-2", label: "6-2", sub: "Two setters, always setting from the back row" },
              { code: "unsure", label: "Not sure yet", sub: "We'll start you on a 5-1 — the most common" },
            ].map((s) => (
              <button key={s.code} className={`setup-system ${system === s.code ? "active" : ""}`}
                      onClick={() => setSystem(s.code)}>
                <span className="landing-title">{s.label}</span>
                <span className="landing-sub">{s.sub}</span>
              </button>
            ))}
          </div>
          {error && <p className="error">{error}</p>}
          <div className="setup-nav">
            <button className="ghost" onClick={() => setStep(2)}>Back</button>
            <button className="primary" disabled={busy} onClick={finish}>
              {busy ? "Setting up…" : "Finish setup"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
