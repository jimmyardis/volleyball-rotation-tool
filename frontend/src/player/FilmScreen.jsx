// Film Room: film one rep (serve, pass, set, attack, block, dig), get
// frame-by-frame coach feedback. The clip is processed on-device — only
// sampled frames (and pose landmarks for serves) are uploaded.

import { useEffect, useRef, useState } from "react";
import { playerApi } from "./api.js";
import { extractFrames, extractPose } from "./filmroom.js";

const VERDICT_ICON = { good: "✓", needs_work: "△", cant_tell: "?" };

export default function FilmScreen({ me }) {
  const [config, setConfig] = useState(null);
  const [skill, setSkill] = useState("serve");
  const [status, setStatus] = useState(null);      // progress text while working
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  useEffect(() => {
    playerApi.videoConfig().then(setConfig).catch((e) => setError(e.message));
    playerApi.videoHistory().then((r) => setHistory(r.assessments)).catch(() => {});
  }, []);

  const selected = config?.skills.find((s) => s.key === skill);

  async function onFile(e) {
    const file = e.target.files?.[0];
    e.target.value = "";                            // allow re-picking the same file
    if (!file) return;
    setError(null); setResult(null);
    try {
      setStatus("Reading your clip…");
      const { frames, timestamps, duration_s } = await extractFrames(file, setStatus);

      let pose_frames = null;
      if (selected?.pose_metrics) {
        try {
          pose_frames = await extractPose(file, setStatus);
        } catch {
          pose_frames = null;                       // pose is a bonus, never a blocker
        }
      }

      setStatus("Coach is watching your clip…");
      const out = await playerApi.submitVideo({ skill_key: skill, frames, timestamps, duration_s, pose_frames });
      setResult(out);
      setHistory((h) => [out, ...h]);
    } catch (err) {
      setError(err.message);
    } finally {
      setStatus(null);
    }
  }

  return (
    <div className="screen">
      <h2>Film Room</h2>
      <p className="hint">Film ONE rep, send it in, and get real coach feedback on your form.
        Your video stays on your phone — the app only sends a few still frames.</p>

      {config && !config.available && (
        <p className="error">The Film Room coach isn't available right now — try again later.</p>
      )}

      {config && (
        <div className="card pz-film-setup">
          <span className="pz-card-title">1 · What are you filming?</span>
          <div className="pz-chip-row">
            {config.skills.map((s) => (
              <button type="button" key={s.key}
                      className={`chip pz-skill-chip ${s.key === skill ? "active" : ""}`}
                      onClick={() => { setSkill(s.key); setResult(null); }}>
                {s.name}
              </button>
            ))}
          </div>
          {selected && (
            <p className="pz-film-camera"><strong>How to film:</strong> {selected.camera}{" "}
              Keep the clip short — one rep, a few seconds.</p>
          )}
          <span className="pz-card-title">2 · Record or pick your clip</span>
          <div className="form-row">
            <button type="button" disabled={!!status || !config.available}
                    onClick={() => fileRef.current?.click()}>
              {status ? "Working…" : "Choose / record a clip"}
            </button>
            <input ref={fileRef} type="file" accept="video/*" style={{ display: "none" }} onChange={onFile} />
          </div>
          {status && <p className="hint pz-film-status">{status}</p>}
          {error && <p className="error">{error}</p>}
        </div>
      )}

      {result && <FeedbackCard a={result} big />}

      {history.length > 0 && (
        <>
          <h3>Past reviews</h3>
          <ul className="pz-log-list">
            {history.filter((a) => a.id !== result?.id).map((a) => (
              <li key={a.id} className="card pz-film-past">
                <button type="button" className="pz-film-past-head"
                        onClick={() => setOpenId(openId === a.id ? null : a.id)}>
                  <span className="pz-log-date">{String(a.created_at).slice(0, 10)}</span>
                  <span className="tag">{a.skill_name}</span>
                  <span className="pz-film-past-issue">{a.feedback?.focus?.issue}</span>
                  <span className="dim">{openId === a.id ? "▴" : "▾"}</span>
                </button>
                {openId === a.id && <FeedbackCard a={a} />}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

export function FeedbackCard({ a, big = false }) {
  const fb = a.feedback || {};
  const m = a.metrics;
  return (
    <div className={`pz-film-feedback ${big ? "card" : ""}`}>
      {big && <span className="pz-card-title">Coach's review — {a.skill_name}</span>}
      <p className="pz-film-summary">{fb.summary}</p>

      {fb.strengths?.length > 0 && (
        <ul className="pz-film-strengths">
          {fb.strengths.map((s, i) => <li key={i}>✓ {s}</li>)}
        </ul>
      )}

      {fb.focus && (
        <div className="pz-film-focus">
          <strong>Work on this one thing: {fb.focus.issue}</strong>
          {fb.focus.why && <p>{fb.focus.why}</p>}
          {fb.focus.fix && <p>{fb.focus.fix}</p>}
          {fb.focus.cue && <p className="pz-film-cue">Next rep, think: “{fb.focus.cue}”</p>}
        </div>
      )}

      {fb.checkpoints?.length > 0 && (
        <ul className="pz-film-checks">
          {fb.checkpoints.map((c, i) => (
            <li key={i} className={`pz-film-check ${c.verdict}`}>
              <span className="pz-film-check-icon">{VERDICT_ICON[c.verdict] ?? "?"}</span>
              <span><strong>{c.name}</strong>{c.note ? ` — ${c.note}` : ""}</span>
            </li>
          ))}
        </ul>
      )}

      {m?.ok && (
        <div className="pz-film-metrics">
          <span className="pz-card-title">Motion tracker (beta)</span>
          <ul>
            <li>{m.elbow_label} ({m.elbow_extension_deg}°)</li>
            <li>{m.contact_height_label}</li>
            {m.knee_label && <li>{m.knee_label}</li>}
            {m.step_label && <li>{m.step_label}</li>}
          </ul>
        </div>
      )}

      {a.drills?.length > 0 && (
        <div className="pz-film-drills">
          <span className="pz-card-title">Drills for this</span>
          {a.drills.map((d) => (
            <div key={d.key} className="pz-film-drill">
              <strong>{d.name}</strong> <span className="dim">({d.equipment}{d.solo ? ", solo-friendly" : ""})</span>
              <p className="pz-drill-how">{d.how_to}</p>
            </div>
          ))}
        </div>
      )}

      {fb.confidence_note && <p className="dim pz-film-conf">{fb.confidence_note}</p>}
    </div>
  );
}
