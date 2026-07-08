import { useEffect, useState } from "react";
import RadarChart from "../components/RadarChart.jsx";
import { playerApi, SKILL_SHORT } from "./api.js";
import { AssessmentSliders } from "./Onboarding.jsx";

export default function ProgressScreen({ me, reloadMe }) {
  const [skills, setSkills] = useState([]);
  const [levelNames, setLevelNames] = useState({});
  const [prog, setProg] = useState(null);
  const [reassessing, setReassessing] = useState(false);
  const [ratings, setRatings] = useState({});
  const [error, setError] = useState(null);

  const load = () => playerApi.progress().then(setProg).catch((e) => setError(e.message));

  useEffect(() => {
    playerApi.skills().then((r) => { setSkills(r.skills); setLevelNames(r.level_names); }).catch(() => {});
    load();
  }, []);

  const color = "var(--accent)"; // the player's own progress reads in the brand pink
  const axes = skills.map((s) => ({ key: s.key, label: s.name, short: SKILL_SHORT[s.key] }));
  const values = Object.fromEntries(skills.map((s) => [s.key, prog?.levels?.[s.key]?.level ?? 0]));

  function startReassess() {
    setRatings(Object.fromEntries(skills.map((s) => [s.key, prog?.levels?.[s.key]?.level ?? 2])));
    setReassessing(true);
  }
  async function saveReassess() {
    setError(null);
    try {
      await playerApi.saveAssessment(ratings);
      setReassessing(false);
      await load();
      reloadMe();
    } catch (e) {
      setError(e.message);
    }
  }

  // group history rows by timestamp (one assessment session = one group)
  const groups = [];
  for (const h of prog?.history ?? []) {
    const last = groups[groups.length - 1];
    if (last && last.at === h.assessed_at) last.items.push(h);
    else groups.push({ at: h.assessed_at, items: [h] });
  }
  const skillName = (key) => skills.find((s) => s.key === key)?.name ?? key;

  return (
    <div className="screen">
      <h2>Progress</h2>
      {error && <p className="error">{error}</p>}

      <div className="pz-progress-grid">
        <div className="card pz-radar-card">
          <span className="pz-card-title">Skill radar</span>
          {skills.length > 0 && prog && (
            <RadarChart attrs={values} color={color} axes={axes} max={5} size={230} />
          )}
          <p className="hint pz-radar-caption">
            {Object.values(prog?.levels ?? {}).length} of {skills.length} skills assessed ·
            levels: Foundation → Mastery
          </p>
          <button className="ghost" onClick={startReassess} disabled={reassessing}>Re-assess my skills</button>
        </div>

        <div className="card">
          <span className="pz-card-title">Consistency</span>
          <div className="pz-stats-row">
            <div className="pz-stat"><span className="pz-stat-num">{prog?.week_streak ?? 0}</span><span className="pz-stat-label">week streak</span></div>
            <div className="pz-stat"><span className="pz-stat-num">{prog?.sessions_28d ?? 0}</span><span className="pz-stat-label">last 4 weeks</span></div>
            <div className="pz-stat"><span className="pz-stat-num">{prog?.sessions_total ?? 0}</span><span className="pz-stat-label">all-time sessions</span></div>
            <div className="pz-stat"><span className="pz-stat-num">{prog?.blocks_done ?? 0}</span><span className="pz-stat-label">blocks mastered</span></div>
          </div>
        </div>
      </div>

      {reassessing && (
        <div className="card">
          <h3>Re-assessment</h3>
          <p className="hint">Rate where you are NOW — comparing to your last assessment is the whole point.</p>
          <AssessmentSliders skills={skills} levelNames={levelNames} ratings={ratings} onChange={setRatings} />
          <div className="form-row">
            <button onClick={saveReassess}>Save assessment</button>
            <button className="ghost" onClick={() => setReassessing(false)}>Cancel</button>
          </div>
        </div>
      )}

      {groups.length > 0 && (
        <>
          <h3>Assessment history</h3>
          {groups.map((g) => (
            <div key={g.at} className="card pz-history">
              <span className="pz-log-date">{g.at}</span>
              <span>
                {g.items.map((h) => `${skillName(h.skill_key)} ${h.level}/5`).join(" · ")}
              </span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
