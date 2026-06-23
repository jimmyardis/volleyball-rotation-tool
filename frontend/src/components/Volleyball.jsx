// A single clean, flat volleyball mark — the one symbol allowed in the UI.
// Pure line art, one color (inherits currentColor), no fill, no shading.
export default function Volleyball({ size = 26 }) {
  return (
    <svg
      className="vb-mark"
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
      <path d="M50 6 C 32 30 30 64 46 94" />
      <path d="M50 6 C 68 30 70 64 54 94" />
      <path d="M9 38 C 36 53 64 53 91 38" />
      <path d="M15 73 C 35 59 65 59 85 73" />
    </svg>
  );
}
