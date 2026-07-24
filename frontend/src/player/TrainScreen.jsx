// Train (her spec): "Log an activity" leads — a button that opens the form
// (skill dropdown, duration, drills from the library), with recent sessions
// and the drill library below. No plan, no checklists.

import { useEffect, useState } from "react";
import { playerApi } from "./api.js";

const EMPTY = { skill: "", minutes: "", drill_keys: [], quality: 3, notes: "" };

export default function TrainScreen({ me }) {
  const [skills, setSkills] = useState([]);
  const [drills, setDrills] = useState([]);
  const [filterSkill, setFilterSkill] = useState("");
  const [soloOnly, setSoloOnly] = useState(false);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [savedMsg, setSavedMsg] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [log, setLog] = useState(EMPTY);

  useEffect(() => {
    playerApi.skills().then((r) => setSkills(r.skills)).catch(() => {});
    playerApi.logs(10).then((r) => setLogs(r.logs)).catch(() => {});
  }, []);

  useEffect(() => {
    playerApi.drills({ skill_key: filterSkill || undefined, solo_only: soloOnly })
      .then((r) => setDrills(r.drills)).catch((e) => setError(e.message));
  }, [filterSkill, soloOnly]);

  const skillName = (key) => skills.find((s) => s.key === key)?.name ?? key;
  // drills offered inside the form follow the chosen skill
  const formDrills = drills.filter((d) => !log.skill || d.skill_key === log.skill);

  function toggleLogDrill(key) {
    setLog((l) => ({
      ...l,
      drill_keys: l.drill_keys.includes(key) ? l.drill_keys.filter((k) => k !== key) : [...l.drill_keys, key],
    }));
  }

  async function saveLog(e) {
    e.preventDefault();
    setError(null); setSavedMsg(null);
    if (!log.skill) return setError("Pick the skill you worked on.");
    try {
      const saved = await playerApi.createLog({
        skills: [log.skill], drill_keys: log.drill_keys,
        quality: log.quality, minutes: log.minutes === "" ? null : Number(log.minutes),
        notes: log.notes,
      });
      setLogs((ls) => [saved, ...ls]);
      setLog(EMPTY);
      setFormOpen(false);
      setSavedMsg("Activity logged — nice work showing up.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="screen">
      <div className="screen-head">
        <div>
          <h2>Train</h2>
          <p className="hint">Log what you worked on — Coach sees it and your streak grows.</p>
        </div>
        {!formOpen && (
          <button onClick={() => { setFormOpen(true); setSavedMsg(null); }}>+ Log an activity</button>
        )}
      </div>
      {savedMsg && !formOpen && <p className="ok">{savedMsg}</p>}

      {formOpen && (
        <form className="card pz-log-form" onSubmit={saveLog}>
          <span className="pz-card-title">Log an activity</span>
          <div className="form-row">
            <label>Skill{" "}
              <select value={log.skill}
                      onChange={(e) => setLog({ ...log, skill: e.target.value, drill_keys: [] })}>
                <option value="" disabled>Pick a skill…</option>
                {skills.map((s) => <option key={s.key} value={s.key}>{s.name}</option>)}
              </select>
            </label>
            <label>Minutes{" "}
              <input type="number" className="pz-minutes" min="1" max="600" placeholder="30"
                     value={log.minutes} onChange={(e) => setLog({ ...log, minutes: e.target.value })} />
            </label>
          </div>

          {log.skill && (
            <>
              <span className="label-inline">Drills you did (optional):</span>
              <div className="pz-chip-row">
                {formDrills.map((d) => (
                  <button type="button" key={d.key}
                          className={`chip pz-skill-chip ${log.drill_keys.includes(d.key) ? "active" : ""}`}
                          onClick={() => toggleLogDrill(d.key)}>
                    {d.name}
                  </button>
                ))}
                {formDrills.length === 0 && <span className="dim">No drills for this skill yet.</span>}
              </div>
            </>
          )}

          <div className="form-row">
            <label className="slider-field">How did it go? <strong>{log.quality}/5</strong>
              <input type="range" min="1" max="5" value={log.quality}
                     onChange={(e) => setLog({ ...log, quality: Number(e.target.value) })} />
            </label>
            <input className="pz-notes" placeholder="Notes — what clicked, what didn't? (Coach reads this)"
                   value={log.notes} onChange={(e) => setLog({ ...log, notes: e.target.value })} />
          </div>
          <div className="form-row">
            <button type="submit">Log it</button>
            <button type="button" className="ghost"
                    onClick={() => { setFormOpen(false); setLog(EMPTY); setError(null); }}>Cancel</button>
          </div>
          {error && <p className="error">{error}</p>}
        </form>
      )}
      {error && !formOpen && <p className="error">{error}</p>}

      {logs.length > 0 && (
        <>
          <h3>Recent activities</h3>
          <ul className="pz-log-list">
            {logs.map((l) => (
              <li key={l.id} className="card pz-log-item">
                <span className="pz-log-date">{l.log_date}</span>
                <span>{l.skills.map(skillName).join(", ") || "general"}</span>
                {l.quality && <span className="tag">{l.quality}/5</span>}
                {l.minutes && <span className="dim">{l.minutes} min</span>}
                {l.notes && <span className="pz-log-notes">“{l.notes}”</span>}
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="pz-drill-filter form-row">
        <h3>Drill library</h3>
        <select value={filterSkill} onChange={(e) => setFilterSkill(e.target.value)}>
          <option value="">All skills</option>
          {skills.map((s) => <option key={s.key} value={s.key}>{s.name}</option>)}
        </select>
        <label className="checkbox">
          <input type="checkbox" checked={soloOnly} onChange={(e) => setSoloOnly(e.target.checked)} />
          I'm training alone
        </label>
      </div>

      <div className="pz-drills">
        {drills.map((d) => (
          <div key={d.key} className={`card pz-drill ${d.position_fit ? "" : "off-position"}`}>
            <div className="pz-drill-head">
              <strong>{d.name}</strong>
              <span className="tag">{skillName(d.skill_key)}</span>
              <span className="pz-drill-lvl">{"●".repeat(d.level)}{"○".repeat(Math.max(0, 5 - d.level))}</span>
            </div>
            <p className="pz-drill-how">{d.how_to}</p>
            <div className="pz-drill-meta">
              <span className="dim">{d.solo ? "solo-friendly" : "needs a partner"} · {d.equipment}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
