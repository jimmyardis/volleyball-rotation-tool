// Shared send logic for the player's AI coach. The MESSAGE THREAD lives in
// PlayerApp so the floating bubble and the Coach tab are one conversation —
// ask from the bubble on Train, continue on the Coach tab.

import { useState } from "react";
import { playerApi } from "./api.js";

export function useCoachChat(messages, setMessages) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  /** Returns true on success; false if the turn was rolled back. */
  async function send(content) {
    content = content.trim();
    if (!content || busy) return false;
    setError(null);
    const next = [...messages, { role: "user", content }];
    setMessages(next);
    setBusy(true);
    try {
      const res = await playerApi.coachChat(next);
      setMessages([...next, { role: "assistant", content: res.reply }]);
      return true;
    } catch (e) {
      setError(e.message);
      setMessages(messages); // roll back the optimistic user turn
      return false;
    } finally {
      setBusy(false);
    }
  }

  return { busy, error, send };
}
