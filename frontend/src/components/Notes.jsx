// Coach notes — one lightweight system, three attachment points:
//   <NotesScreen>  the team notebook (dated entries), its own tab
//   <QuickNotes>   pinned notes on a player card or a lineup viewer
// Same editor everywhere: type, save, edit in place, delete.

import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";

function fmtDate(ts) {
  if (!ts) return "";
  return ts.slice(0, 10);
}

function NoteItem({ note, onSaved, onDeleted }) {
  const [editing, setEditing] = useState(false);
  const [body, setBody] = useState(note.body);

  async function save() {
    const updated = await api.updateNote(note.id, body.trim());
    setEditing(false);
    onSaved(updated);
  }

  return (
    <div className="note-item">
      <span className="note-date">{fmtDate(note.created_at)}</span>
      {editing ? (
        <span className="note-edit">
          <input value={body} onChange={(e) => setBody(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && body.trim() && save()} autoFocus />
          <button className="ghost" disabled={!body.trim()} onClick={save}>Save</button>
        </span>
      ) : (
        <span className="note-body">{note.body}</span>
      )}
      <span className="note-actions">
        <button className="ghost" onClick={() => setEditing(!editing)}>{editing ? "Cancel" : "Edit"}</button>
        <button className="ghost danger" onClick={async () => { await api.deleteNote(note.id); onDeleted(note.id); }}>✕</button>
      </span>
    </div>
  );
}

function useNotes(teamId, params) {
  const [notes, setNotes] = useState([]);
  const key = JSON.stringify(params);
  const load = useCallback(() => {
    if (teamId == null) return;
    api.listNotes(teamId, JSON.parse(key)).then(setNotes).catch(() => setNotes([]));
  }, [teamId, key]);
  useEffect(() => { load(); }, [load]);
  return [notes, setNotes, load];
}

function AddNote({ teamId, attach, onAdded, placeholder }) {
  const [body, setBody] = useState("");
  async function add(e) {
    e?.preventDefault();
    if (!body.trim()) return;
    const note = await api.createNote(teamId, { body: body.trim(), ...attach });
    setBody("");
    onAdded(note);
  }
  return (
    <form className="note-add" onSubmit={add}>
      <input placeholder={placeholder} value={body} onChange={(e) => setBody(e.target.value)} />
      <button type="submit" disabled={!body.trim()}>Add note</button>
    </form>
  );
}

export function QuickNotes({ teamId, playerId = null, lineupId = null, title = "Notes" }) {
  const params = playerId != null ? { player_id: playerId } : { lineup_id: lineupId };
  const [notes, setNotes] = useNotes(teamId, params);
  const attach = playerId != null ? { player_id: playerId } : { lineup_id: lineupId };

  return (
    <div className="quick-notes">
      <span className="pz-card-title">📌 {title}</span>
      {notes.length > 0 && (
        <div className="note-list">
          {notes.map((n) => (
            <NoteItem key={n.id} note={n}
                      onSaved={(u) => setNotes((ns) => ns.map((x) => (x.id === u.id ? u : x)))}
                      onDeleted={(id) => setNotes((ns) => ns.filter((x) => x.id !== id))} />
          ))}
        </div>
      )}
      <AddNote teamId={teamId} attach={attach} placeholder="Jot something…"
               onAdded={(n) => setNotes((ns) => [n, ...ns])} />
    </div>
  );
}

export default function NotesScreen({ teamId, players, lineups }) {
  const [notes, setNotes] = useNotes(teamId, {});
  const playerName = (id) => players.find((p) => p.id === id)?.name ?? `player ${id}`;
  const lineupName = (id) => lineups.find((l) => l.id === id)?.name ?? `lineup ${id}`;

  const tagFor = (n) =>
    n.player_id != null ? `on ${playerName(n.player_id)}`
    : n.lineup_id != null ? `on ${lineupName(n.lineup_id)}`
    : null;

  return (
    <div className="screen">
      <h2>Team notebook</h2>
      <p className="hint">
        Everything you've jotted — team entries plus the notes pinned to players and lineups.
        Pin from a player's card (Roster) or a lineup (Rotations).
      </p>
      <div className="card notebook-page">
        <AddNote teamId={teamId} attach={{}} placeholder="New team note — practice focus, matchup plans, reminders…"
                 onAdded={(n) => setNotes((ns) => [n, ...ns])} />
        {notes.length === 0 ? (
          <p className="empty">No notes yet.</p>
        ) : (
          <div className="note-list">
            {notes.map((n) => (
              <div key={n.id} className="note-row">
                <NoteItem note={n}
                          onSaved={(u) => setNotes((ns) => ns.map((x) => (x.id === u.id ? u : x)))}
                          onDeleted={(id) => setNotes((ns) => ns.filter((x) => x.id !== id))} />
                {tagFor(n) && <span className="tag">{tagFor(n)}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
