// The personal AI coach: full-pane chat grounded in the player's own data.

import { useEffect, useRef, useState } from "react";
import { playerApi } from "./api.js";

const STARTERS = [
  "What should I work on this week?",
  "Why do my serves keep going into the net?",
  "Give me a 20-minute solo practice for today.",
  "How do I know if I passed my current block?",
];

export default function CoachScreen({ me }) {
  const [available, setAvailable] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const bodyRef = useRef(null);

  useEffect(() => {
    playerApi.coachStatus().then((r) => setAvailable(r.available)).catch(() => setAvailable(false));
  }, []);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function send(text) {
    const content = (text ?? input).trim();
    if (!content || busy) return;
    setError(null);
    const next = [...messages, { role: "user", content }];
    setMessages(next);
    setInput("");
    setBusy(true);
    try {
      const res = await playerApi.coachChat(next);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    } catch (e) {
      setError(e.message);
      setMessages(messages); // roll back the optimistic user turn
      setInput(content);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen pz-coach">
      <h2>My Coach</h2>
      <p className="hint">
        Coach knows your position, your levels, your plan, and your recent
        sessions — ask anything about your training.
      </p>
      {available === false && (
        <p className="warn">The coach isn't configured on this server (missing API key).</p>
      )}

      <div className="card pz-chat">
        <div className="chat-body pz-chat-body" ref={bodyRef}>
          {messages.length === 0 && (
            <div className="chat-intro">
              <p className="hint">Try one of these:</p>
              {STARTERS.map((s) => (
                <button key={s} className="chip" onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>{m.content}</div>
          ))}
          {busy && <div className="bubble assistant dim">Coach is thinking…</div>}
        </div>
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input placeholder="Ask your coach…" value={input}
                 onChange={(e) => setInput(e.target.value)} disabled={busy || available === false} />
          <button type="submit" disabled={busy || available === false}>Send</button>
        </form>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
