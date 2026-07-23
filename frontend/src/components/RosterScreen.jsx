import { useEffect, useRef, useState } from "react";
import { api, ROLES, ATTRS } from "../api.js";
import { roleMeta, overallRating } from "../roles.js";
import RadarChart from "./RadarChart.jsx";
import { QuickNotes } from "./Notes.jsx";

// ---- roster file import (SportsEngine CSV export, or any spreadsheet) ----

// minimal quote-aware CSV parser: returns rows of cells, blank lines dropped
function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; }
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.some((x) => x.trim() !== "")) rows.push(row);
      row = [];
    } else cell += c;
  }
  row.push(cell);
  if (row.some((x) => x.trim() !== "")) rows.push(row);
  return rows;
}

function findCol(headers, ...names) {
  return headers.findIndex((h) => names.includes(h));
}

// "Setter" / "OH" / "Middle Blocker" / "Right Side" / … -> role code
function guessRole(text) {
  const t = (text || "").toLowerCase();
  if (/\bsetter\b|^s$/.test(t)) return "S";
  if (/libero|^l$|^lib$/.test(t)) return "L";
  if (/middle|^mb$/.test(t)) return "MB";
  if (/opposite|right side|^opp$|^rs$/.test(t)) return "OPP";
  if (/defensive|^ds$/.test(t)) return "DS";
  if (/outside|^oh$|left side/.test(t)) return "OH";
  return null;
}

// rows -> [{name, jersey, role, roleGuessed}]; understands SportsEngine's
// First/Last Name + Jersey Number + Position headers and common variants
function rosterFromCsv(text) {
  const rows = parseCsv(text);
  if (rows.length < 2) throw new Error("that file has no player rows");
  const headers = rows[0].map((h) => h.trim().toLowerCase());
  const first = findCol(headers, "first name", "first", "firstname");
  const last = findCol(headers, "last name", "last", "lastname", "surname");
  const full = findCol(headers, "name", "full name", "player name", "player", "athlete name", "athlete");
  const jersey = findCol(headers, "jersey number", "jersey", "number", "#", "uniform number", "uniform", "no.", "no");
  const pos = findCol(headers, "position", "positions", "pos", "primary position");
  if (first === -1 && full === -1) {
    throw new Error("couldn't find a name column — expected a 'Name' or 'First Name'/'Last Name' header");
  }
  return rows.slice(1).map((r) => {
    const name = (full !== -1 ? r[full] : `${r[first] ?? ""} ${last !== -1 ? r[last] ?? "" : ""}`).trim();
    const num = jersey !== -1 ? String(r[jersey] ?? "").replace(/[^0-9]/g, "") : "";
    const guessed = pos !== -1 ? guessRole(r[pos]) : null;
    return { name, jersey: num, role: guessed ?? "OH", roleGuessed: guessed != null };
  }).filter((p) => p.name);
}

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
  const [formOpen, setFormOpen] = useState(false); // collapsed by default — the roster is the screen
  const [error, setError] = useState(null);
  const [presets, setPresets] = useState({});
  const [catalog, setCatalog] = useState([]);
  const [notesFor, setNotesFor] = useState(null); // player id with the notes pin open
  const [importRows, setImportRows] = useState(null); // parsed CSV preview, null = closed
  const [importBusy, setImportBusy] = useState(false);
  const fileRef = useRef(null);

  useEffect(() => {
    setForm(EMPTY);
    setEditingId(null);
    setFormOpen(false);
    setNotesFor(null);
    setImportRows(null);
  }, [teamId]);

  async function onImportFile(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setError(null);
    try {
      setImportRows(rosterFromCsv(await file.text()));
    } catch (err) {
      setError(`Import: ${err.message}`);
    }
  }

  function setImportRow(i, patch) {
    setImportRows((rows) => rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  }

  async function runImport() {
    setImportBusy(true);
    setError(null);
    try {
      for (const p of importRows) {
        await api.createPlayer(teamId, {
          name: p.name,
          primary_role: p.role,
          jersey_number: p.jersey === "" ? null : Number(p.jersey),
        });
      }
      setImportRows(null);
      reload();
    } catch (err) {
      setError(`Import stopped: ${err.message} — players added so far are on the roster below.`);
      reload();
    } finally {
      setImportBusy(false);
    }
  }

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
      setFormOpen(false);
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
    setFormOpen(true);
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
      <div className="screen-head">
        <div>
          <h2>Roster</h2>
          <p className="hint">
            Every player gets a card. The skill radar drives the game simulator.
          </p>
        </div>
        {!formOpen && !editingId && (
          <span className="inline">
            <button className="ghost" onClick={() => fileRef.current?.click()}>Import CSV</button>
            <button onClick={() => setFormOpen(true)}>+ New player</button>
          </span>
        )}
        <input ref={fileRef} type="file" accept=".csv,text/csv" style={{ display: "none" }} onChange={onImportFile} />
      </div>

      {importRows && (
        <div className="card">
          <h4 className="form-title">Import roster — {importRows.length} player{importRows.length === 1 ? "" : "s"} found</h4>
          <p className="hint">Works with the SportsEngine roster export (Roster → Export → CSV) or any
            spreadsheet saved as CSV with name / number / position columns. Check positions before adding —
            rows marked ⚠ had no recognizable position and defaulted to OH.</p>
          <div className="import-rows">
            {importRows.map((p, i) => (
              <div key={i} className="form-row import-row">
                <input value={p.name} onChange={(e) => setImportRow(i, { name: e.target.value })} />
                <input type="number" className="narrow" placeholder="#" value={p.jersey}
                       onChange={(e) => setImportRow(i, { jersey: e.target.value })} />
                <select value={p.role} onChange={(e) => setImportRow(i, { role: e.target.value, roleGuessed: true })}>
                  {ROLES.map((r) => <option key={r.code} value={r.code}>{r.code} — {r.label}</option>)}
                </select>
                {!p.roleGuessed && <span title="No position found in the file — defaulted to OH">⚠</span>}
                <button type="button" className="ghost danger"
                        onClick={() => setImportRows((rows) => rows.filter((_, j) => j !== i))}>Remove</button>
              </div>
            ))}
          </div>
          <div className="form-row">
            <button disabled={importBusy || importRows.length === 0} onClick={runImport}>
              {importBusy ? "Adding…" : `Add ${importRows.length} player${importRows.length === 1 ? "" : "s"}`}
            </button>
            <button className="ghost" disabled={importBusy} onClick={() => setImportRows(null)}>Cancel</button>
          </div>
        </div>
      )}

      {(formOpen || editingId) && (
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
          <button type="button" className="ghost"
                  onClick={() => { setEditingId(null); setForm(EMPTY); setFormOpen(false); }}>Cancel</button>
        </div>
      </form>
      )}
      {error && <p className="error">{error}</p>}

      {players.length === 0 && !formOpen && <p className="empty">No players yet — tap “+ New player” to add your first.</p>}

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
