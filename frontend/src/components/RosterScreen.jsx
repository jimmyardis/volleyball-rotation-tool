import { useEffect, useState } from "react";
import { api, ROLES } from "../api.js";

const EMPTY = {
  name: "",
  jersey_number: "",
  primary_role: "OH",
  secondary_role: "",
  is_libero: false,
};

export default function RosterScreen({ teamId, players, reload }) {
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setForm(EMPTY);
    setEditingId(null);
  }, [teamId]);

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
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
    };
    if (!payload.name) return setError("Name is required.");
    try {
      if (editingId) await api.updatePlayer(editingId, payload);
      else await api.createPlayer(teamId, payload);
      setForm(EMPTY);
      setEditingId(null);
      reload();
    } catch (err) {
      setError(err.message);
    }
  }

  function startEdit(p) {
    setEditingId(p.id);
    setForm({
      name: p.name,
      jersey_number: p.jersey_number ?? "",
      primary_role: p.primary_role,
      secondary_role: p.secondary_role ?? "",
      is_libero: !!p.is_libero,
    });
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
        Every player gets a permanent ID. Stats (Phase 2) and the simulator
        (Phase 3) will all hang off these IDs.
      </p>

      <form className="card form-row" onSubmit={submit}>
        <input
          placeholder="Name"
          value={form.name}
          onChange={(e) => set("name", e.target.value)}
        />
        <input
          type="number"
          placeholder="#"
          className="narrow"
          value={form.jersey_number}
          onChange={(e) => set("jersey_number", e.target.value)}
        />
        <select value={form.primary_role} onChange={(e) => set("primary_role", e.target.value)}>
          {ROLES.map((r) => (
            <option key={r.code} value={r.code}>{r.code} — {r.label}</option>
          ))}
        </select>
        <select value={form.secondary_role} onChange={(e) => set("secondary_role", e.target.value)}>
          <option value="">(no 2nd role)</option>
          {ROLES.map((r) => (
            <option key={r.code} value={r.code}>{r.code}</option>
          ))}
        </select>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={form.is_libero}
            onChange={(e) => set("is_libero", e.target.checked)}
          />
          Libero
        </label>
        <button type="submit">{editingId ? "Save" : "Add"}</button>
        {editingId && (
          <button type="button" className="ghost" onClick={() => { setEditingId(null); setForm(EMPTY); }}>
            Cancel
          </button>
        )}
      </form>
      {error && <p className="error">{error}</p>}

      <table className="roster-table">
        <thead>
          <tr><th>#</th><th>Name</th><th>Role</th><th>2nd</th><th>Libero</th><th></th></tr>
        </thead>
        <tbody>
          {players.length === 0 && (
            <tr><td colSpan={6} className="empty">No players yet — add some above.</td></tr>
          )}
          {players.map((p) => (
            <tr key={p.id}>
              <td>{p.jersey_number ?? "–"}</td>
              <td>{p.name}</td>
              <td>{p.primary_role}</td>
              <td>{p.secondary_role ?? "–"}</td>
              <td>{p.is_libero ? "✓" : ""}</td>
              <td className="actions">
                <button className="ghost" onClick={() => startEdit(p)}>Edit</button>
                <button className="ghost danger" onClick={() => remove(p.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
