import { useEffect, useState } from "react";
import { playerApi } from "./api.js";

export default function TrainScreen({ me }) {
  const [skills, setSkills] = useState([]);
  const [drills, setDrills] = useState([]);
  const [filterSkill, setFilterSkill] = useState("");
  const [soloOnly, setSoloOnly] = useState(false);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [savedMsg, setSavedMsg] = useState(null);

  const emptyLog = { skills: [], drill_keys: [], quality: 3, minutes: "", notes: "" };
  const [log, setLog] = useState(emptyLog);

  useEffect(() => {
    playerApi.skills().then((r) => setSkills(r.skills)).catch(() => {});
    playerApi.logs(10).then((r) => setLogs(r.logs)).catch(() => {});
  }, []);

  useEffect(() => {
    playerApi.drills({ skill_key: filterSkill || undefined, solo_only: soloOnly })
      .then((r) => setDrills(r.drills)).catch((e) => setError(e.message));
  }, [filterSkill, soloOnly]);

  const skillName = (key) => skills.find((s) => s.key === key)?.name ?? key;

  function toggleLogSkill(key) {
    setLog((l) => ({
      ...l,
      skills: l.skills.includes(key) ? l.skills.filter((k) => k !== key) : [...l.skills, key],
    }));
  }
  function toggleLogDrill(key) {
    setLog((l) => ({
      ...l,
      drill_keys: l.drill_keys.includes(key) ? l.drill_keys.filter((k) => k !== key) : [...l.drill_keys, key],
    }));
  }

  async function saveLog(e) {
    e.preventDefault();
    setError(null); setSavedMsg(null);
    if (log.skills.length === 0) return setError("Pick at least one skill you worked on.");
    try {
      const saved = await playerApi.createLog({
        skills: log.skills, drill_keys: log.drill_keys,
        quality: log.quality, minutes: log.minutes === "" ? null : Number(log.minutes),
        notes: log.notes,
      });
      setLogs((ls) => [saved, ...ls]);
      setLog(emptyLog);
      setSavedMsg("Session logged — nice work showing up.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="screen">
      <h2>Train</h2>

      <form className="card pz-log-form" onSubmit={saveLog}>
        <span className="pz-card-title">Log a session</span>
        <div className="pz-chip-row">
          {skills.map((s) => (
            <button type="button" key={s.key}
                    className={`chip pz-skill-chip ${log.skills.includes(s.key) ? "active" : ""}`}
                    onClick={() => toggleLogSkill(s.key)}>
              {s.name}
            </button>
          ))}
        </div>
        <div className="form-row">
          <label className="slider-field">How did it go? <strong>{log.quality}/5</strong>
            <input type="range" min="1" max="5" value={log.quality}
                   onChange={(e) => setLog({ ...log, quality: Number(e.target.value) })} />
          </label>
          <input type="number" className="pz-minutes" placeholder="minutes" title="minutes"
                 value={log.minutes} onChange={(e) => setLog({ ...log, minutes: e.target.value })} />
          <input className="pz-notes" placeholder="Notes — what clicked, what didn't? (Coach reads this)"
                 value={log.notes} onChange={(e) => setLog({ ...log, notes: e.target.value })} />
          <button type="submit">Log it</button>
        </div>
        {log.drill_keys.length > 0 && (
          <p className="hint">Drills in this session: {log.drill_keys.map((k) => drills.find((d) => d.key === k)?.name ?? k).join(", ")}</p>
        )}
        {savedMsg && <p className="ok">{savedMsg}</p>}
        {error && <p className="error">{error}</p>}
      </form>

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
              <button type="button" className={`ghost ${log.drill_keys.includes(d.key) ? "active-ghost" : ""}`}
                      onClick={() => toggleLogDrill(d.key)}>
                {log.drill_keys.includes(d.key) ? "In session — remove" : "Add to session"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {logs.length > 0 && (
        <>
          <h3>Recent sessions</h3>
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
    </div>
  );
}
