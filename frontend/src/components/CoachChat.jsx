import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

// Floating coaching assistant: ask for drills or player help. Backed by Claude
// on the server. Closed by default; opens as a panel in the corner.

const SUGGESTIONS = [
  "Which of my rotations looks weakest, and why?",
  "Who should sub in for the back row in each rotation?",
  "Give me 3 passing drills for a beginner team.",
  "How do I teach a middle blocker to close the block?",
];

export default function CoachChat({ teamId, lineupId, onLineupCreated, onViewLineup }) {
  const [open, setOpen] = useState(false);
  const [available, setAvailable] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const bodyRef = useRef(null);

  useEffect(() => { api.coachStatus().then((s) => setAvailable(s.available)).catch(() => setAvailable(false)); }, []);
  useEffect(() => { if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight; }, [messages, busy]);

  async function send(text) {
    const content = (text ?? input).trim();
    if (!content || busy) return;
    setError(null); setInput("");
    const next = [...messages, { role: "user", content }];
    setMessages(next);
    setBusy(true);
    try {
      // only real user/assistant turns go to the API — the green "added" bubbles
      // are UI-only annotations (role 'system' is not a valid chat role).
      const apiMessages = next.filter((m) => m.role === "user" || m.role === "assistant");
      const res = await api.coachChat(apiMessages, { teamId, lineupId });
      const added = [...next, { role: "assistant", content: res.reply }];
      if (res.created_lineups?.length) {
        onLineupCreated?.(res.created_lineups);
        for (const l of res.created_lineups) {
          added.push({ role: "system", content: `✅ Added “${l.name}” (${l.system}) to your lineups.`, lineupId: l.id });
        }
      }
      setMessages(added);
    } catch (e) {
      setError(e.message);
      setMessages(next);
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button className="chat-fab" onClick={() => setOpen(true)} title="Ask the coaching assistant">
        💬 Coach Assistant
      </button>
    );
  }

  return (
    <div className="chat-panel">
      <header className="chat-head">
        <span>💬 Coach Assistant <span className="dim">drills & player help</span></span>
        <button className="ghost" onClick={() => setOpen(false)}>×</button>
      </header>

      <div className="chat-body" ref={bodyRef}>
        {available === false && (
          <p className="error">Assistant unavailable — set <code>ANTHROPIC_API_KEY</code> in <code>~/.env</code> and restart the backend.</p>
        )}
        {messages.length === 0 && available !== false && (
          <div className="chat-intro">
            <p className="hint">Ask for drills or player help. Try:</p>
            {SUGGESTIONS.map((s) => (
              <button key={s} className="chip" onClick={() => send(s)}>{s}</button>
            ))}
          </div>
        )}
        {messages.map((m, i) =>
          m.role === "system" ? (
            <div key={i} className="bubble system">
              {m.content}
              {m.lineupId != null && onViewLineup && (
                <button className="link inline-link" onClick={() => onViewLineup(m.lineupId)}>View in Rotations →</button>
              )}
            </div>
          ) : (
            <div key={i} className={`bubble ${m.role}`}>{m.content}</div>
          )
        )}
        {busy && <div className="bubble assistant dim">thinking…</div>}
        {error && <p className="error">{error}</p>}
      </div>

      <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
        <input
          placeholder="Ask about drills or a player…"
          value={input}
          disabled={available === false}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={busy || available === false}>Send</button>
      </form>
    </div>
  );
}
