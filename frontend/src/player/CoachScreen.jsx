// The gotcha moment (her spec): ONE device that works like any modern AI
// chat — a conversation with Coach, plus a camera button in the input bar.
// Tap the camera, pick the skill, send a clip; the frame-by-frame breakdown
// lands right in the conversation. Shares its thread with the floating
// bubble (state lives in PlayerApp).

import { useEffect, useRef, useState } from "react";
import { playerApi } from "./api.js";
import { useCoachChat } from "./useCoachChat.js";
import { extractFrames, extractPose } from "./filmroom.js";
import { FeedbackCard } from "./FeedbackCard.jsx";

function CameraIcon({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 8 h3 l1.6 -2.4 h6.8 L17 8 h3 a1.5 1.5 0 0 1 1.5 1.5 v8 A1.5 1.5 0 0 1 20 19 H4 a1.5 1.5 0 0 1 -1.5 -1.5 v-8 A1.5 1.5 0 0 1 4 8 Z" />
      <circle cx="12" cy="13" r="3.4" />
    </svg>
  );
}

// one-line text version of a film review, kept in the thread so the chat
// API (and the coach's memory of the conversation) stays continuous
function filmSummaryText(a) {
  const f = a.feedback || {};
  let t = f.summary || "Clip reviewed.";
  if (f.focus?.issue) t += ` Main fix: ${f.focus.issue}.`;
  if (f.focus?.cue) t += ` Cue: “${f.focus.cue}”.`;
  return t;
}

export default function CoachScreen({ me, messages, setMessages }) {
  const [available, setAvailable] = useState(null);
  const [input, setInput] = useState("");
  const { busy, error, send } = useCoachChat(messages, setMessages);
  const bodyRef = useRef(null);
  const fileRef = useRef(null);

  // first-time spotlight on the camera button (her spec: highlight it and
  // explain with a chat bubble until they've tried it once)
  const [showCamTip, setShowCamTip] = useState(() => !localStorage.getItem("pz_cam_tip_seen"));

  // camera flow
  const [filmOpen, setFilmOpen] = useState(false);
  const [filmCfg, setFilmCfg] = useState(null);
  const [filmSkill, setFilmSkill] = useState("serve");
  const [filmStatus, setFilmStatus] = useState(null);
  const [filmError, setFilmError] = useState(null);

  useEffect(() => {
    playerApi.coachStatus().then((r) => setAvailable(r.available)).catch(() => setAvailable(false));
  }, []);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy, filmStatus]);

  async function submit(text) {
    const content = text ?? input;
    setInput("");
    const ok = await send(content);
    if (!ok) setInput(content);
  }

  function openCamera() {
    localStorage.setItem("pz_cam_tip_seen", "1");
    setShowCamTip(false);
    setFilmError(null);
    setFilmOpen((v) => !v);
    if (!filmCfg) playerApi.videoConfig().then(setFilmCfg).catch((e) => setFilmError(e.message));
  }

  const selectedSkill = filmCfg?.skills.find((s) => s.key === filmSkill);

  async function onFile(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setFilmError(null);
    try {
      setFilmStatus("Reading your clip…");
      const { frames, timestamps, duration_s } = await extractFrames(file, setFilmStatus);
      let pose_frames = null;
      if (selectedSkill?.pose_metrics) {
        try { pose_frames = await extractPose(file, setFilmStatus); } catch { pose_frames = null; }
      }
      setFilmStatus("Coach is watching your clip…");
      const out = await playerApi.submitVideo({ skill_key: filmSkill, frames, timestamps, duration_s, pose_frames });
      setMessages((m) => [
        ...m,
        { role: "user", content: `📹 Sent a ${out.skill_name} clip for review.` },
        { role: "assistant", content: filmSummaryText(out), film: out },
      ]);
      setFilmOpen(false);
    } catch (err) {
      setFilmError(err.message);
    } finally {
      setFilmStatus(null);
    }
  }

  return (
    <div className="screen pz-coach">
      <div className="card pz-chat pz-chat-hero">
        <div className="chat-body pz-chat-body" ref={bodyRef}>
          {messages.length === 0 && (
            <div className="pz-chat-empty">
              <p><strong>Hey {me.user.display_name.split(" ")[0]} — I'm your coach.</strong></p>
              <p className="hint">Ask me anything about your training, or tap the camera and send
                one rep of a serve, pass, set, attack, block, or dig — I'll break it down frame by frame.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role} ${m.film ? "has-film" : ""}`}>
              {m.film ? <FeedbackCard a={m.film} /> : m.content}
            </div>
          ))}
          {busy && <div className="bubble assistant dim">Coach is thinking…</div>}
          {filmStatus && <div className="bubble user dim">{filmStatus}</div>}
        </div>

        {filmOpen && (
          <div className="pz-film-panel">
            <span className="pz-card-title">What are you uploading?</span>
            {!filmCfg && !filmError && <p className="hint">One sec…</p>}
            {filmCfg && (
              <>
                <div className="pz-chip-row">
                  {filmCfg.skills.map((s) => (
                    <button type="button" key={s.key}
                            className={`chip pz-skill-chip ${s.key === filmSkill ? "active" : ""}`}
                            onClick={() => setFilmSkill(s.key)}>
                      {s.name}
                    </button>
                  ))}
                </div>
                {selectedSkill && (
                  <p className="pz-film-camera"><strong>How to film:</strong> {selectedSkill.camera}{" "}
                    One rep, a few seconds.</p>
                )}
                <div className="form-row">
                  <button type="button" disabled={!!filmStatus} onClick={() => fileRef.current?.click()}>
                    {filmStatus ? "Working…" : "Choose / record a clip"}
                  </button>
                  <button type="button" className="ghost" disabled={!!filmStatus}
                          onClick={() => setFilmOpen(false)}>Cancel</button>
                </div>
              </>
            )}
            {filmError && <p className="error">{filmError}</p>}
          </div>
        )}

        {showCamTip && !filmOpen && (
          <button type="button" className="pz-cam-callout" onClick={openCamera}>
            Send a video of any rep — I'll analyze it 📹
          </button>
        )}
        <form className="chat-input pz-chat-input" onSubmit={(e) => { e.preventDefault(); submit(); }}>
          <button type="button" className={`ghost pz-cam-btn ${filmOpen ? "active-ghost" : ""} ${showCamTip ? "spotlight" : ""}`}
                  title="Send a video for review" aria-label="Send a video for review"
                  disabled={available === false} onClick={openCamera}>
            <CameraIcon />
          </button>
          <input placeholder="Ask your coach…" value={input}
                 onChange={(e) => setInput(e.target.value)} disabled={busy || available === false} />
          <button type="submit" disabled={busy || available === false || !input.trim()}>Send</button>
        </form>
        <input ref={fileRef} type="file" accept="video/*" style={{ display: "none" }} onChange={onFile} />
      </div>

      {available === false && (
        <p className="warn">The coach isn't configured on this server (missing API key).</p>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
