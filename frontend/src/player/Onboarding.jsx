// Onboarding: pick your position (role-colored buttons), rate yourself on the
// 8 skills (Foundation → Mastery), and the app builds your first plan.

import { useEffect, useState } from "react";
import { ROLES } from "../api.js";
import { roleMeta } from "../roles.js";
import { playerApi } from "./api.js";

export function AssessmentSliders({ skills, levelNames, ratings, onChange }) {
  return (
    <div className="pz-assess">
      {skills.map((s) => (
        <label key={s.key} className="pz-assess-row">
          <span className="pz-assess-name">{s.name}</span>
          <input type="range" min="1" max="5" value={ratings[s.key] ?? 2}
                 onChange={(e) => onChange({ ...ratings, [s.key]: Number(e.target.value) })} />
          <span className="pz-assess-level">{levelNames[ratings[s.key] ?? 2]}</span>
        </label>
      ))}
    </div>
  );
}

export default function Onboarding({ me, onDone }) {
  const [skills, setSkills] = useState([]);
  const [levelNames, setLevelNames] = useState({});
  const [position, setPosition] = useState(me.profile?.position ?? null);
  const [levelBand, setLevelBand] = useState(me.profile?.level_band ?? "high_school");
  const [ratings, setRatings] = useState({});
  const [step, setStep] = useState(me.profile?.position ? 2 : 1);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    playerApi.skills().then((r) => {
      setSkills(r.skills);
      setLevelNames(r.level_names);
      setRatings(Object.fromEntries(r.skills.map((s) => [s.key, 2])));
    }).catch((e) => setError(e.message));
  }, []);

  async function finish() {
    setError(null); setBusy(true);
    try {
      await playerApi.updateProfile({ position, level_band: levelBand });
      await playerApi.saveAssessment(ratings);
      try { await playerApi.generatePlan(); } catch { /* plan can be generated later */ }
      onDone();
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  return (
    <div className="screen">
      {step === 1 && (
        <div className="card">
          <h2>What do you play?</h2>
          <p className="hint">Your position shapes your plan — a libero trains passing and digging, a setter trains hands and tempo.</p>
          <div className="pz-positions">
            {ROLES.map((r) => {
              const m = roleMeta(r.code);
              const active = position === r.code;
              return (
                <button key={r.code} className={`pz-pos ${active ? "active" : ""}`}
                        style={{ "--pos-color": m.color, "--pos-ink": m.ink }}
                        onClick={() => setPosition(r.code)}>
                  <span className="pz-pos-code">{r.code}</span>
                  <span className="pz-pos-label">{r.label}</span>
                </button>
              );
            })}
          </div>
          <div className="form-row">
            <label>Where do you play?{" "}
              <select value={levelBand} onChange={(e) => setLevelBand(e.target.value)}>
                <option value="rec">Rec league</option>
                <option value="middle_school">Middle school</option>
                <option value="high_school">High school</option>
                <option value="club">Club</option>
                <option value="college">College</option>
              </select>
            </label>
            <button disabled={!position} onClick={() => setStep(2)}>Next: rate your skills</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h2>How's your game right now?</h2>
          <p className="hint">
            Be honest — this is just your starting point, and nobody else sees it.
            You can re-assess any time from the Progress tab.
          </p>
          <AssessmentSliders skills={skills} levelNames={levelNames} ratings={ratings} onChange={setRatings} />
          <div className="form-row">
            <button className="ghost" onClick={() => setStep(1)}>Back</button>
            <button onClick={finish} disabled={busy || !skills.length}>
              {busy ? "Building your plan…" : "Finish — build my plan"}
            </button>
          </div>
          {error && <p className="error">{error}</p>}
        </div>
      )}
    </div>
  );
}
