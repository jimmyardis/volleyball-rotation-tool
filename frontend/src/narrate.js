// Turns rally-engine events into play-by-play lines. The backend sends
// compact structured events; all the personality lives here.
//
// Every line: { text, tone } — tone drives the color in the narration box:
//   "us" (we scored / did something good), "them", "neutral", "whistle".

const PASS_LINES = {
  3: (n) => `${n} passes a perfect ball — right on the setter's hands.`,
  2: (n) => `${n} gets a solid pass up.`,
  1: (n) => `${n} keeps it alive, but the pass pulls them off the net.`,
};

export function narrate(event, names) {
  const n = (pid) => names(pid);
  const we = event.tm === "us";
  switch (event.k) {
    case "rally_start":
      return {
        text: `— ${event.server === "us" ? "We serve" : "They serve"} at ${event.score[0]}–${event.score[1]} (R${event.us_rot + 1}) —`,
        tone: "neutral", divider: true,
      };
    case "serve":
      return { text: `${n(event.p)} steps back to serve…`, tone: "neutral" };
    case "serve_error":
      return {
        text: `${n(event.p)}'s serve ${event.how === "net" ? "catches the tape" : "sails long"}.` +
              (event.mk ? " That habit again." : ""),
        tone: we ? "them" : "us",
      };
    case "ace":
      return {
        text: we
          ? `ACE! ${n(event.p)} takes ${n(event.victim)} right off the platform!`
          : `Their serve aces ${n(event.victim)} — too hot to handle.`,
        tone: we ? "us" : "them",
      };
    case "pass":
      return { text: (PASS_LINES[event.q] || PASS_LINES[1])(n(event.p)), tone: "neutral" };
    case "set":
      return { text: `${n(event.p)} sets ${n(event.target)}…`, tone: "neutral" };
    case "attack":
      if (event.out === "kill")
        return { text: `KILL by ${n(event.p)}! 💥`, tone: we ? "us" : "them" };
      if (event.out === "error")
        return {
          text: `${n(event.p)} swings ${event.how === "net" ? "into the net" : "long"}.` +
                (event.mk ? " Coach has seen that one before." : ""),
          tone: we ? "them" : "us",
        };
      return { text: `${n(event.p)} swings —`, tone: "neutral" }; // dug, dig line follows
    case "block":
      return { text: `STUFFED! ${n(event.p)} roofs it at the net!`, tone: we ? "us" : "them" };
    case "dig":
      return { text: `${n(event.p)} digs it up — rally on…`, tone: "neutral" };
    case "net_touch":
      return {
        text: `Whistle — ${n(event.p)} touches the net on the block.`,
        tone: "whistle",
      };
    case "overlap":
      return {
        text: `Whistle — ${n(event.p)} lined up wrong before the serve. Overlap call.`,
        tone: "whistle",
      };
    case "scramble":
      return {
        text: `A wild scramble at the net… ${we ? "we" : "they"} come out with it!`,
        tone: we ? "us" : "them",
      };
    case "point":
      return {
        text: `Point ${event.winner === "us" ? "US" : "THEM"} · ${event.score[0]}–${event.score[1]}`,
        tone: event.winner, point: true,
      };
    case "rotate":
      return { text: `Sideout — we rotate to R${event.us_rot + 1}.`, tone: "neutral" };
    case "set_end":
      return {
        text: event.won
          ? `That's the set — WE WIN ${event.score[0]}–${event.score[1]}! 🎉`
          : `They take the set, ${event.score[1]}–${event.score[0]}. Back to work.`,
        tone: event.won ? "us" : "them", point: true,
      };
    default:
      return null;
  }
}

// how long each event stays on screen at 1x (ms)
export function eventDelay(event) {
  switch (event.k) {
    case "rally_start": return 650;
    case "serve": return 750;
    case "pass": case "set": return 600;
    case "attack": case "block": case "dig": return 800;
    case "ace": case "serve_error": case "net_touch": case "overlap": case "scramble": return 900;
    case "point": return 1100;
    case "rotate": return 850;
    default: return 600;
  }
}
