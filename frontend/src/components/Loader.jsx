// Loading animation: a volleyball being set — the ball floats up off a pair
// of setter's hands and drops back in, on repeat. Pure CSS keyframes; the
// ball is the same one-color line-art mark used on the landing page.

import Volleyball from "./Volleyball.jsx";

export default function Loader({ label = "Loading…" }) {
  return (
    <div className="loader" role="status" aria-label={label}>
      <div className="loader-scene" aria-hidden="true">
        <div className="loader-ball"><Volleyball size={30} /></div>
        {/* setter's hands: two cupped strokes that flick as the ball leaves */}
        <svg className="loader-hands" width="44" height="18" viewBox="0 0 44 18"
             fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round">
          <path d="M4 16 C 8 6, 16 4, 20 10" />
          <path d="M40 16 C 36 6, 28 4, 24 10" />
        </svg>
      </div>
      <span className="loader-label">{label}</span>
    </div>
  );
}
