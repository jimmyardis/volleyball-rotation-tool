// Clouds for the Sky look: soft white cumulus drawn from overlapping lobes,
// drifting slowly across the top of the screen. Decoration only.

export function Cloud({ size = 40, className = "", style }) {
  return (
    <svg width={size} height={size * 0.6} viewBox="0 0 100 60" className={className}
         style={style} aria-hidden="true" fill="none">
      <path d="M14 46
               C 4 46, 2 34, 11 31
               C 9 21, 21 15, 28 20
               C 31 9, 47 7, 52 16
               C 58 8, 72 11, 73 21
               C 84 19, 92 28, 88 37
               C 95 40, 93 46, 85 46 Z"
            fill="#ffffff" stroke="#cfe4f6" strokeWidth="2" strokeLinejoin="round" />
      <path d="M22 40 C 26 36, 34 36, 38 40 M52 38 C 56 34, 64 34, 68 38"
            stroke="#e4f0fa" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function CloudDrift() {
  return (
    <div className="cloud-drift" aria-hidden="true">
      <Cloud size={64} className="c1" />
      <Cloud size={44} className="c2" />
      <Cloud size={34} className="c3" />
    </div>
  );
}
