// A single clean, flat volleyball mark — the one symbol allowed in the UI.
// Real-volleyball panel layout: three seams swirling out of the center
// (like the ball's three panel groups), each with a companion panel line
// hugging the rim. Pure line art, inherits currentColor.
export default function Volleyball({ size = 26, className = "", style }) {
  return (
    <svg
      className={`vb-mark ${className}`}
      style={style}
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      stroke="currentColor"
      strokeWidth="5"
      strokeLinecap="round"
      strokeLinejoin="round"
      role="img"
      aria-label="Volleyball"
    >
      <circle cx="50" cy="50" r="44" />
      {/* three seams meeting at the center, curling the same direction */}
      <path d="M50 50 C 46 33, 49 18, 60 7" />
      <path d="M50 50 C 36 60, 22 62, 7 56" />
      <path d="M50 50 C 64 57, 72 70, 72 89" />
      {/* companion panel lines, one per third, following the rim */}
      <path d="M85 21 C 72 27, 60 38, 53 49" />
      <path d="M16 78 C 27 69, 39 59, 48 53" />
      <path d="M52 93 C 51 79, 51 64, 50 53" />
    </svg>
  );
}
