import { useEffect, useState } from "react";
import { playerApi } from "./api.js";

const STATUS_LABEL = { locked: "LOCKED", active: "IN PROGRESS", done: "MASTERED" };

export default function PlanScreen({ me, goTo }) {
  const [plan, setPlan] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [celebrate, setCelebrate] = useState(false);

  useEffect(() => {
    playerApi.plan().then((r) => { setPlan(r.plan); setLoaded(true); }).catch((e) => { setError(e.message); setLoaded(true); });
  }, []);

  async function regenerate() {
    if (plan && !confirm("Rebuild your plan from your latest self-assessment? Your current block progress resets.")) return;
    setError(null);
    try {
      setPlan(await playerApi.generatePlan());
    } catch (e) {
      setError(e.message);
    }
  }

  async function toggle(cp, done) {
    setError(null);
    try {
      const res = await playerApi.toggleCheckpoint(cp.id, done);
      setPlan(res.plan);
      if (res.unlocked_next) {
        setCelebrate(true);
        setTimeout(() => setCelebrate(false), 4000);
      }
    } catch (e) {
      setError(e.message);
    }
  }

  if (!loaded) return <div className="screen"><p>Loading…</p></div>;

  return (
    <div className="screen">
      <div className="pz-plan-head">
        <h2>My Plan</h2>
        <button className="ghost" onClick={regenerate}>{plan ? "Rebuild plan" : "Build my plan"}</button>
      </div>
      {error && <p className="error">{error}</p>}
      {celebrate && <p className="pz-celebrate">Block mastered — the next one just unlocked. Keep rolling!</p>}
      {!plan && <p className="hint">No plan yet — build one from your position + self-assessment.</p>}

      {plan && (
        <p className="hint">
          One block at a time: finish every checkpoint to unlock the next block.
          Each block's test tells you when you've truly got it.
        </p>
      )}

      {plan?.blocks.map((b, i) => (
        <div key={b.id} className={`card pz-block ${b.status}`}>
          <div className="pz-block-head">
            <span className="pz-block-num">{i + 1}</span>
            <h3>{b.title}</h3>
            <span className={`pz-block-status ${b.status}`}>{STATUS_LABEL[b.status]}</span>
          </div>

          {b.status !== "locked" && (
            <>
              <ul className="pz-checkpoints">
                {b.checkpoints.map((c) => (
                  <li key={c.id}>
                    <label className="checkbox">
                      <input type="checkbox" checked={!!c.done} onChange={(e) => toggle(c, e.target.checked)} />
                      <span className={c.done ? "pz-cp-done" : ""}>{c.text}</span>
                    </label>
                  </li>
                ))}
              </ul>
              {b.drills.length > 0 && (
                <p className="pz-block-drills">
                  Drills for this block:{" "}
                  {b.drills.map((d) => <span key={d.key} className="tag" title={d.how_to}>{d.name}</span>)}
                  <button className="link inline-link" onClick={() => goTo("Train")}>open Train</button>
                </p>
              )}
            </>
          )}
          {b.status === "locked" && (
            <p className="hint">Unlocks after block {i} — {b.success_criteria}</p>
          )}
        </div>
      ))}
    </div>
  );
}
