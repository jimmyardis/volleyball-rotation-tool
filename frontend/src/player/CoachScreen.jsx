// The personal AI coach, full-pane. Shares its thread with the floating
// bubble (state lives in PlayerApp), so it's one continuous conversation.

import { useEffect, useRef, useState } from "react";
import { playerApi } from "./api.js";
import { COACH_STARTERS, useCoachChat } from "./useCoachChat.js";

export default function CoachScreen({ me, messages, setMessages }) {
  const [available, setAvailable] = useState(null);
  const [input, setInput] = useState("");
  const { busy, error, send } = useCoachChat(messages, setMessages);
  const bodyRef = useRef(null);

  useEffect(() => {
    playerApi.coachStatus().then((r) => setAvailable(r.available)).catch(() => setAvailable(false));
  }, []);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function submit(text) {
    const content = text ?? input;
    setInput("");
    const ok = await send(content);
    if (!ok) setInput(content);
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
              {COACH_STARTERS.map((s) => (
                <button key={s} className="chip" onClick={() => submit(s)}>{s}</button>
              ))}
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>{m.content}</div>
          ))}
          {busy && <div className="bubble assistant dim">Coach is thinking…</div>}
        </div>
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); submit(); }}>
          <input placeholder="Ask your coach…" value={input}
                 onChange={(e) => setInput(e.target.value)} disabled={busy || available === false} />
          <button type="submit" disabled={busy || available === false}>Send</button>
        </form>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
