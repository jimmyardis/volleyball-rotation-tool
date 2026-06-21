// Guided "How it works" overlay: a step-by-step walkthrough of the whole app
// plus coaching recommendations. Pure content, no backend.

const STEPS = [
  {
    n: 1, title: "Create your team",
    body: "Use “+ Team” in the top bar. Everything (players, lineups) hangs off the team you have selected.",
    tip: "You can keep several teams/seasons — switch with the dropdown.",
  },
  {
    n: 2, title: "Build the roster",
    body: "On the Roster tab, add every player with their jersey #, primary role (S, OH, MB, OPP, L, DS) and a libero flag. Add your whole bench, not just six — subs and the libero live here too.",
    tip: "Each player gets a permanent ID, so later stat-tracking and analysis stay attached to the right person.",
  },
  {
    n: 3, title: "Set a starting lineup",
    body: "On the Lineups tab, name a lineup, pick the system (5-1 / 6-2 / 4-2), then assign six players to zones 1–6. Zone 1 is right-back and serves first; the other five rotations are computed from this.",
    tip: "Tip: build the lineup from your three diagonal pairs — setter/opposite, your two outsides, your two middles — placed across from each other (see “Pairs” below).",
  },
  {
    n: 4, title: "Classify players & pair specialists",
    body: "In the Substitution setup (under the lineup), mark each player All-around, Front-only, or Back-only. Pair a front specialist with a back partner (e.g. a middle with a DS/libero), then hit “Generate subs from pairings.”",
    tip: "The libero is locked to the back row — it can never play a front-row zone.",
  },
  {
    n: 5, title: "Walk the rotations",
    body: "On the Rotations tab, step through R1–R6. For each, switch the situation: Serving (rotational spots), Receiving (drag your serve-receive formation — it’s overlap-checked), and Base (drag where players switch to after the serve). Open Substitutions to fine-tune who’s on court per rotation.",
    tip: "The narration box at the bottom reads out who serves, where the setter is, and who subbed in for whom.",
  },
  {
    n: 6, title: "Ask the assistant",
    body: "Use the 💬 Coach Assistant (bottom-right) any time for practice drills or player-development help — by position, level, or skill.",
    tip: "Try: “3 serve-receive drills for 12-year-olds” or “help my middle close the block.”",
  },
];

const CONCEPTS = [
  ["The 6 zones", "Front row (left→right): 4, 3, 2. Back row: 5, 6, 1. Zone 1 serves. The net is at the top of the court diagram."],
  ["Rotation", "You rotate one spot clockwise only when you win serve back (a side-out). There are exactly 6 rotations, then it repeats."],
  ["The 3 situations", "Serving = your base rotational spots. Receiving = your serve-receive formation (must obey overlap until the ball is served). Base = where players move once the ball’s in play."],
  ["Overlap rule", "At the moment of serve, each front-row player must be nearer the net than the back-row player behind them, and left-right order must hold within each row. The Receiving view flags violations."],
  ["Diagonal “opposite” pairs", "The structure of a lineup: setter↔opposite, the two outsides, the two middles — each placed 3 spots apart, so one of each pair is always front row and the other back. (Your middle’s pair is the player behind/across from her.)"],
  ["Front/back sub pairs", "A different kind of pair: a front-only and back-only specialist who share one slot and swap as it crosses the front/back line — like you (middle) and your DS."],
  ["Libero", "A back-row defensive specialist who can never play the front row and (usually) doesn’t serve. Swaps in for a back-row player without counting as a sub."],
];

const RECS = [
  "Start every lineup from your three diagonal pairs (S/OPP, OH/OH, MB/MB) placed across from each other — it guarantees one of each pair is always up front.",
  "In a 5-1, remember: setter in the back row = 3 front-row attackers; setter in the front row = only 2. Plan your strongest scoring rotations around that.",
  "Pair each middle with a back-row specialist so your weaker back-row passers come off and your best defenders come on.",
  "Use the Receiving view to make sure every rotation’s serve-receive is legal before game day — overlap calls are free points for the other team.",
  "Use the Base view to set each player’s switch (e.g. a middle who hides outside slides back to the middle after serve).",
];

export default function HelpPanel({ onClose }) {
  return (
    <div className="help-overlay" onClick={onClose}>
      <div className="help-modal" onClick={(e) => e.stopPropagation()}>
        <header className="help-head">
          <h2>How this app works</h2>
          <button className="ghost" onClick={onClose}>Close ×</button>
        </header>

        <p className="hint">A quick tour, then key concepts and a few coaching recommendations. You can reopen this any time with the “?” button.</p>

        <h3>Step by step</h3>
        <ol className="help-steps">
          {STEPS.map((s) => (
            <li key={s.n}>
              <span className="help-num">{s.n}</span>
              <div>
                <strong>{s.title}</strong>
                <p>{s.body}</p>
                <p className="help-tip">💡 {s.tip}</p>
              </div>
            </li>
          ))}
        </ol>

        <h3>Key concepts</h3>
        <dl className="help-concepts">
          {CONCEPTS.map(([term, def]) => (
            <div key={term}><dt>{term}</dt><dd>{def}</dd></div>
          ))}
        </dl>

        <h3>Coach recommendations</h3>
        <ul className="help-recs">
          {RECS.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      </div>
    </div>
  );
}
