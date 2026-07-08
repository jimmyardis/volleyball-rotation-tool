import { useEffect, useState } from "react";
import { api, ROLES, ATTRS } from "../api.js";
import { roleMeta, overallRating } from "../roles.js";
import RadarChart from "./RadarChart.jsx";
import { QuickNotes } from "./Notes.jsx";

const EMPTY_ATTRS = Object.fromEntries(ATTRS.map((a) => [a.key, 50]));
const EMPTY = {
  name: "",
  jersey_number: "",
  primary_role: "OH",
  secondary_role: "",
  is_libero: false,
  attrs: { ...EMPTY_ATTRS },
  mistakes: {},
};

export default function RosterScreen({ teamId, players, reload }) {
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState(null);
  const [presets, setPresets] = useState({});
  const [catalog, setCatalog] = useState([]);
  const [notesFor, setNotesFor] = useState(null); // player id with the notes pin open

  useEffect(() => {
    setForm(EMPTY);
    setEditingId(null);
    setNotesFor(null);
  }, [teamId]);

  useEffect(() => { api.rolePresets().then(setPresets).catch(() => {}); }, []);
  useEffect(() => {
    api.mistakeCatalog().then((c) => setCatalog(c.catalog)).catch(() => {});
  }, []);

  // tag on/off + severity cycle for the mistakes editor
  function toggleMistake(key) {
    setForm((f) => {
      const m = { ...f.mistakes };
      if (m[key]) delete m[key];
      else m[key] = "sometimes";
      return { ...f, mistakes: m };
    });
  }
  function setMistakeSeverity(key, sev) {
    setForm((f) => ({ ...f, mistakes: { ...f.mistakes, [key]: sev } }));
  }

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }
  function setAttr(key, value) {
    const v = value === "" ? "" : Math.max(0, Math.min(100, Number(value)));
    setForm((f) => ({ ...f, attrs: { ...f.attrs, [key]: v } }));
  }
  function applyPreset() {
    const p = presets[form.primary_role];
    if (p) setForm((f) => ({ ...f, attrs: { ...p } }));
  }

  async function submit(e) {
    e.preventDefault();
    setError(null);
    const payload = {
      name: form.name.trim(),
      primary_role: form.primary_role,
      jersey_number: form.jersey_number === "" ? null : Number(form.jersey_number),
      secondary_role: form.secondary_role || null,
      is_libero: !!form.is_libero,
      ...Object.fromEntries(ATTRS.map((a) => [a.key, form.attrs[a.key] === "" ? null : Number(form.attrs[a.key])])),
    };
    if (!payload.name) return setError("Name is required.");
    try {
      const saved = editingId
        ? await api.updatePlayer(editingId, payload)
        : await api.createPlayer(teamId, payload);
      await api.saveMistakes(saved?.id ?? editingId, form.mistakes);
      setForm(EMPTY);
      setEditingId(null);
      reload();
    } catch (err) {
      setError(err.message);
    }
  }

  // when picking a role for a NEW player, prefill attributes from the preset
  function changeRole(role) {
    setForm((f) => ({
      ...f,
      primary_role: role,
      attrs: !editingId && presets[role] ? { ...presets[role] } : f.attrs,
    }));
  }

  function startEdit(p) {
    setEditingId(p.id);
    setForm({
      name: p.name,
      jersey_number: p.jersey_number ?? "",
      primary_role: p.primary_role,
      secondary_role: p.secondary_role ?? "",
      is_libero: !!p.is_libero,
      attrs: Object.fromEntries(ATTRS.map((a) => [a.key, p[a.key] ?? 50])),
      mistakes: {},
    });
    api.getMistakes(p.id)
      .then((r) => setForm((f) => ({ ...f, mistakes: r.mistakes })))
      .catch(() => {});
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function remove(id) {
    if (!confirm("Remove this player?")) return;
    await api.deletePlayer(id);
    if (editingId === id) {
      setEditingId(null);
      setForm(EMPTY);
    }
    reload();
  }

  return (
    <div className="screen">
      <h2>Roster</h2>
      <p className="hint">
        Every player gets a card. The skill radar drives the game simulator.
      </p>

      <form className="card" onSubmit={submit}>
        <h4 className="form-title">{editingId ? "Edit player" : "Add a player"}</h4>
        <div className="form-row">
          <input placeholder="Name" value={form.name} onChange={(e) => set("name", e.target.value)} />
          <input type="number" placeholder="#" className="narrow"
                 value={form.jersey_number} onChange={(e) => set("jersey_number", e.target.value)} />
          <select value={form.primary_role} onChange={(e) => changeRole(e.target.value)}>
            {ROLES.map((r) => <option key={r.code} value={r.code}>{r.code} — {r.label}</option>)}
          </select>
          <select value={form.secondary_role} onChange={(e) => set("secondary_role", e.target.value)}>
            <option value="">(no 2nd role)</option>
            {ROLES.map((r) => <option key={r.code} value={r.code}>{r.code}</option>)}
          </select>
          <label className="checkbox">
            <input type="checkbox" checked={form.is_libero} onChange={(e) => set("is_libero", e.target.checked)} />
            Libero
          </label>
        </div>

        <div className="attrs-editor">
          <span className="label-inline">Skill ratings (0–100, used by the simulator):</span>
          <button type="button" className="ghost" onClick={applyPreset}>Use {form.primary_role} preset</button>
          <div className="attrs-grid">
            {ATTRS.map((a) => (
              <label key={a.key} className="attr-field">
                <span>{a.label} <strong className="attr-val">{form.attrs[a.key]}</strong></span>
                <input type="range" min="0" max="100" value={form.attrs[a.key] || 0}
                       onChange={(e) => setAttr(a.key, e.target.value)} />
              </label>
            ))}
          </div>
        </div>

        <div className="attrs-editor">
          <span className="label-inline">
            Common mistakes (tag what this player actually does — the simulator makes them happen,
            more often in big moments if their Pressure is low):
          </span>
          <div className="mistake-list">
            {catalog.map((m) => {
              const on = !!form.mistakes[m.key];
              return (
                <div key={m.key} className={`mistake-row ${on ? "on" : ""}`}>
                  <label className="checkbox">
                    <input type="checkbox" checked={on} onChange={() => toggleMistake(m.key)} />
                    <span>{m.label} <span className="dim">({m.moment})</span></span>
                  </label>
                  {on && (
                    <span className="mistake-sev">
                      {["sometimes", "often"].map((sev) => (
                        <button key={sev} type="button"
                                className={`ghost sev-btn ${form.mistakes[m.key] === sev ? "active-ghost" : ""}`}
                                onClick={() => setMistakeSeverity(m.key, sev)}>
                          {sev}
                        </button>
                      ))}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="form-row">
          <button type="submit">{editingId ? "Save player" : "Add player"}</button>
          {editingId && (
            <button type="button" className="ghost" onClick={() => { setEditingId(null); setForm(EMPTY); }}>Cancel</button>
          )}
        </div>
      </form>
      {error && <p className="error">{error}</p>}

      {players.length === 0 && <p className="empty">No players yet — add some above.</p>}

      <div className="player-cards">
        {players.map((p) => {
          const meta = roleMeta(p.primary_role);
          const overall = overallRating(p);
          return (
            <div key={p.id} className={`player-card ${editingId === p.id ? "editing" : ""}`}>
              <div className="pc-band" style={{ background: meta.color, color: meta.ink }}>
                <span className="pc-jersey">{p.jersey_number ?? "–"}</span>
                <span className="pc-nameblock">
                  <span className="pc-name">{p.name}</span>
                  <span className="pc-role">
                    {meta.label}
                    {p.secondary_role ? ` · ${p.secondary_role}` : ""}
                  </span>
                </span>
                {overall != null && <span className="pc-overall" title="Overall (average of skills)">{overall}</span>}
              </div>
              {!!p.is_libero && <span className="pc-libero">LIBERO</span>}
              <RadarChart attrs={p} color={meta.color} />
              <div className="pc-actions">
                <button className="ghost" onClick={() => startEdit(p)}>Edit</button>
                <button className="ghost" onClick={() => setNotesFor(notesFor === p.id ? null : p.id)}>📌 Notes</button>
                <button className="ghost danger" onClick={() => remove(p.id)}>Delete</button>
              </div>
              {notesFor === p.id && (
                <div className="pc-notes">
                  <QuickNotes teamId={teamId} playerId={p.id} title={`Notes on ${p.name}`} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
