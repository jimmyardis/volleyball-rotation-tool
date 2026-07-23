// Onboarding: pick your position (role-colored buttons), rate yourself on the
// 8 skills (Foundation → Mastery), and the app builds your first plan.

import { useEffect, useState } from "react";
import { ROLES } from "../api.js";
import { roleMeta } from "../roles.js";
import { playerApi } from "./api.js";
import { tap, success } from "../haptics.js";

function StepDots({ step }) {
  return (
    <div className="pz-step-dots" aria-label={`Step ${step} of 3`}>
      {[1, 2, 3].map((n) => (
        <span key={n} className={step === n ? "active" : step > n ? "done" : ""} />
      ))}
    </div>
  );
}

// The two looks she designed: Classic (her logo's black/white/grey with
// little bits of pink) and Intense (black & orange, pink accents, butterfly).
export const THEMES = [
  { key: "classic", name: "Classic", desc: "Black, white & grey with a little pink",
    swatches: ["#17171a", "#ffffff", "#6f6f7a", "#d6336c"] },
  { key: "intense", name: "Intense 🦋", desc: "Black & orange, pink accents",
    swatches: ["#0e0e10", "#ff7a1a", "#d6336c", "#f4f4f6"] },
];

export function ThemeCards({ theme, setTheme }) {
  return (
    <div className="pz-theme-cards">
      {THEMES.map((t) => (
        <button key={t.key} type="button"
                className={`pz-theme-card ${theme === t.key ? "active" : ""}`}
                onClick={() => { tap(); setTheme(t.key); }}>
          <span className="pz-theme-swatches">
            {t.swatches.map((c, i) => <span key={i} style={{ background: c }} />)}
          </span>
          <span className="pz-theme-name">{t.name}</span>
          <span className="pz-theme-desc">{t.desc}</span>
        </button>
      ))}
    </div>
  );
}

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

export default function Onboarding({ me, onDone, theme, setTheme }) {
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
      success();
      onDone();
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  return (
    <div className="screen pz-onb">
      <StepDots step={step} />
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
                        onClick={() => { tap(); setPosition(r.code); }}>
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
            <button disabled={!skills.length} onClick={() => { tap(); setStep(3); }}>
              Next: pick your look
            </button>
          </div>
          {error && <p className="error">{error}</p>}
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <h2>Pick your look</h2>
          <p className="hint">The whole app wears it. Change it any time from Profile.</p>
          <ThemeCards theme={theme} setTheme={setTheme} />
          <div className="form-row">
            <button className="ghost" onClick={() => setStep(2)}>Back</button>
            <button onClick={finish} disabled={busy}>
              {busy ? "Building your plan…" : "Finish — build my plan"}
            </button>
          </div>
          {error && <p className="error">{error}</p>}
        </div>
      )}
    </div>
  );
}
