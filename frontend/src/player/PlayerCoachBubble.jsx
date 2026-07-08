// Floating coach bubble for the Player Zone — same personal coach as the
// Coach tab (shared thread), reachable from any screen.

import { useEffect, useRef, useState } from "react";
import { useCoachChat } from "./useCoachChat.js";

export default function PlayerCoachBubble({ messages, setMessages, onExpand }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const { busy, error, send } = useCoachChat(messages, setMessages);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [messages, busy, open]);

  async function submit(text) {
    const content = text ?? input;
    setInput("");
    const ok = await send(content);
    if (!ok) setInput(content);
  }

  if (!open) {
    return (
      <button className="chat-fab" onClick={() => setOpen(true)} title="Ask your coach">
        My Coach
      </button>
    );
  }

  return (
    <div className="chat-panel">
      <header className="chat-head">
        <span>My Coach</span>
        <span className="pz-bubble-actions">
          <button className="ghost" onClick={() => { setOpen(false); onExpand?.(); }} title="Open the full Coach tab">Expand</button>
          <button className="ghost" onClick={() => setOpen(false)}>Close</button>
        </span>
      </header>

      <div className="chat-body" ref={bodyRef}>
        {messages.length === 0 && (
          <p className="hint">Ask coach anything about your training.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>{m.content}</div>
        ))}
        {busy && <div className="bubble assistant dim">Coach is thinking…</div>}
        {error && <p className="error">{error}</p>}
      </div>

      <form className="chat-input" onSubmit={(e) => { e.preventDefault(); submit(); }}>
        <input placeholder="Ask your coach…" value={input} onChange={(e) => setInput(e.target.value)} />
        <button type="submit" disabled={busy}>Send</button>
      </form>
    </div>
  );
}
