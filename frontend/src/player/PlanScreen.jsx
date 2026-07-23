// My Plan, kept SIMPLE: one big "working on now" card with a checklist,
// a plain "up next" list, and finished skills as one-line ✓ rows. All the
// engine (mastery gating, unlock-next, reopen) is unchanged underneath.

import { useEffect, useState } from "react";
import { playerApi } from "./api.js";
import { tap, success } from "../haptics.js";

const skillOf = (title) => title.split("→")[0].trim();
const goalOf = (title) => (title.split("→")[1] || "").trim();

export default function PlanScreen({ me, goTo }) {
  const [plan, setPlan] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [celebrate, setCelebrate] = useState(false);

  useEffect(() => {
    playerApi.plan().then((r) => { setPlan(r.plan); setLoaded(true); }).catch((e) => { setError(e.message); setLoaded(true); });
  }, []);

  async function regenerate() {
    if (plan && !confirm("Rebuild your plan from your latest self-assessment? Your current progress resets.")) return;
    setError(null);
    try {
      setPlan(await playerApi.generatePlan());
    } catch (e) {
      setError(e.message);
    }
  }

  async function toggle(cp, done) {
    setError(null);
    if (done) tap();
    try {
      const res = await playerApi.toggleCheckpoint(cp.id, done);
      setPlan(res.plan);
      if (res.unlocked_next) {
        success();
        setCelebrate(true);
        setTimeout(() => setCelebrate(false), 4000);
      }
    } catch (e) {
      setError(e.message);
    }
  }

  if (!loaded) return <div className="screen"><p>Loading…</p></div>;

  const blocks = plan?.blocks ?? [];
  const active = blocks.find((b) => b.status === "active");
  const done = blocks.filter((b) => b.status === "done");
  const upNext = blocks.filter((b) => b.status === "locked");
  const allDone = plan && !active && upNext.length === 0;

  return (
    <div className="screen">
      <div className="pz-plan-head">
        <h2>My Plan</h2>
        <button className="ghost" onClick={regenerate}>{plan ? "Rebuild plan" : "Build my plan"}</button>
      </div>
      {error && <p className="error">{error}</p>}
      {celebrate && <p className="pz-celebrate">You finished it — the next skill just unlocked! 🎉</p>}
      {!plan && <p className="hint">No plan yet — tap “Build my plan”.</p>}
      {plan && !allDone && (
        <p className="hint">One goal at a time. Check off the list as you do it — finish the checklist and your next goal unlocks.</p>
      )}
      {allDone && <p className="pz-celebrate">Whole plan finished! Re-assess your skills on Progress, then rebuild for new goals.</p>}

      {active && (
        <div className="card pz-block active pz-now">
          <span className="pz-card-title">Working on now</span>
          <div className="pz-now-head">
            <h3 className="pz-now-skill">{skillOf(active.title)}</h3>
            {goalOf(active.title) && <span className="pz-goal">({goalOf(active.title)})</span>}
          </div>
          <span className="pz-checklist-label">Checklist</span>
          <ul className="pz-checkpoints">
            {active.checkpoints.map((c) => (
              <li key={c.id}>
                <label className="checkbox">
                  <input type="checkbox" checked={!!c.done} onChange={(e) => toggle(c, e.target.checked)} />
                  <span className={c.done ? "pz-cp-done" : ""}>{c.text}</span>
                </label>
              </li>
            ))}
          </ul>
          {active.drills.length > 0 && (
            <p className="pz-block-drills">
              Drills:{" "}
              {active.drills.map((d) => <span key={d.key} className="tag" title={d.how_to}>{d.name}</span>)}
              <button className="link inline-link" onClick={() => goTo("Train")}>open Train</button>
            </p>
          )}
        </div>
      )}

      {upNext.length > 0 && (
        <div className="card pz-upnext">
          <span className="pz-card-title">Next goals</span>
          <ol className="pz-next-list">
            {upNext.map((b) => <li key={b.id}>{skillOf(b.title)}</li>)}
          </ol>
        </div>
      )}

      {done.length > 0 && (
        <div className="card pz-doneblocks">
          <span className="pz-card-title">Finished</span>
          {done.map((b) => (
            <p key={b.id} className="pz-done-row">✓ {skillOf(b.title)}</p>
          ))}
        </div>
      )}
    </div>
  );
}
