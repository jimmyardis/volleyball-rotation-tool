import { useEffect, useState } from "react";
import { playerApi } from "./api.js";

export default function HomeScreen({ me, goTo }) {
  const [plan, setPlan] = useState(null);
  const [prog, setProg] = useState(null);

  useEffect(() => {
    playerApi.plan().then((r) => setPlan(r.plan)).catch(() => {});
    playerApi.progress().then(setProg).catch(() => {});
  }, []);

  const active = plan?.blocks?.find((b) => b.status === "active");
  const nextCp = active?.checkpoints?.find((c) => !c.done);
  const doneCount = active ? active.checkpoints.filter((c) => c.done).length : 0;

  return (
    <div className="screen">
      <h2>Hey {me.user.display_name} — let's get better today.</h2>

      <div className="pz-home-grid">
        <div className="card pz-today">
          <span className="pz-card-title">Today's focus</span>
          {active ? (
            <>
              <h3>{active.title}</h3>
              <p className="hint">{doneCount}/{active.checkpoints.length} checkpoints done</p>
              {nextCp && <p className="pz-next-cp">Next up: {nextCp.text}</p>}
              <button onClick={() => goTo("Plan")}>Open my plan</button>
            </>
          ) : plan ? (
            <>
              <h3>Plan complete!</h3>
              <p className="hint">Every block is done. Re-assess and build the next one.</p>
              <button onClick={() => goTo("Progress")}>Re-assess my skills</button>
            </>
          ) : (
            <>
              <h3>No plan yet</h3>
              <button onClick={() => goTo("Plan")}>Build my plan</button>
            </>
          )}
        </div>

        <div className="card pz-streak">
          <span className="pz-card-title">Consistency</span>
          <div className="pz-stats-row">
            <div className="pz-stat"><span className="pz-stat-num">{prog?.week_streak ?? "–"}</span><span className="pz-stat-label">week streak</span></div>
            <div className="pz-stat"><span className="pz-stat-num">{prog?.sessions_28d ?? "–"}</span><span className="pz-stat-label">sessions, last 4 wks</span></div>
            <div className="pz-stat"><span className="pz-stat-num">{prog?.blocks_done ?? "–"}</span><span className="pz-stat-label">blocks mastered</span></div>
          </div>
          <button className="ghost" onClick={() => goTo("Train")}>Log a session</button>
        </div>

        <div className="card pz-ask">
          <span className="pz-card-title">Ask Coach</span>
          <p className="hint">Stuck on something? Your coach knows your plan, your levels, and your last few sessions.</p>
          <button onClick={() => goTo("Coach")}>Talk to Coach</button>
        </div>
      </div>
    </div>
  );
}
