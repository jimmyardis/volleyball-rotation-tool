// The coach's film review, rendered as a card — lives inside chat bubbles
// (and anywhere else a review needs showing).

const VERDICT_ICON = { good: "✓", needs_work: "△", cant_tell: "?" };

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
