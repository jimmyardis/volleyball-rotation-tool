// Monarch butterflies for the Intense look — drawn, not emoji (her call).
// Real-monarch anatomy, simplified: orange wing cells separated by black
// veins, wide black wing margins dotted white, black-tipped forewings,
// slender black body. One reusable monarch + a flock of three drifting
// near the top of the screen.

export function Monarch({ size = 24, className = "", style }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" className={className}
         style={style} aria-hidden="true" fill="none">
      {/* wing silhouettes first — the black layer IS the margin band */}
      <path d="M31 30 C 25 14, 13 4, 6 8 C 0 12, 6 26, 16 32 C 22 35, 28 34, 31 30 Z" fill="#151515" />
      <path d="M33 30 C 39 14, 51 4, 58 8 C 64 12, 58 26, 48 32 C 42 35, 36 34, 33 30 Z" fill="#151515" />
      <path d="M31 34 C 24 35, 13 42, 13 49 C 13 56, 23 57, 28 51 C 31 47, 32 40, 31 34 Z" fill="#151515" />
      <path d="M33 34 C 40 35, 51 42, 51 49 C 51 56, 41 57, 36 51 C 33 47, 32 40, 33 34 Z" fill="#151515" />
      {/* orange cells inset inside the black margins */}
      <path d="M30 29 C 26 17, 17 9, 11 12 C 7 15, 12 25, 19 30 C 23 32.5, 27 32, 30 29 Z" fill="#f97316" />
      <path d="M34 29 C 38 17, 47 9, 53 12 C 57 15, 52 25, 45 30 C 41 32.5, 37 32, 34 29 Z" fill="#f97316" />
      <path d="M30 35 C 25 36, 17 42, 17 48 C 17 53, 24 54, 27 49 C 29.5 45, 30.5 40, 30 35 Z" fill="#fb923c" />
      <path d="M34 35 C 39 36, 47 42, 47 48 C 47 53, 40 54, 37 49 C 34.5 45, 33.5 40, 34 35 Z" fill="#fb923c" />
      {/* black forewing tips (monarchs' dark apex) */}
      <path d="M13 10 C 9 10, 6 12, 7 16 C 10 17, 14 15, 16 12 Z" fill="#151515" />
      <path d="M51 10 C 55 10, 58 12, 57 16 C 54 17, 50 15, 48 12 Z" fill="#151515" />
      {/* veins radiating through the orange cells */}
      <path d="M30 29 L14 13 M30 29 L11 20 M30 29 L17 27 M34 29 L50 13 M34 29 L53 20 M34 29 L47 27"
            stroke="#151515" strokeWidth="1.3" />
      <path d="M30 35 L19 43 M30 35 L22 50 M34 35 L45 43 M34 35 L42 50"
            stroke="#151515" strokeWidth="1.3" />
      {/* white spots along the black margins (the monarch signature) */}
      <circle cx="9" cy="13" r="1.1" fill="#fff" /><circle cx="12" cy="9.5" r="0.9" fill="#fff" />
      <circle cx="55" cy="13" r="1.1" fill="#fff" /><circle cx="52" cy="9.5" r="0.9" fill="#fff" />
      <circle cx="7" cy="20" r="0.9" fill="#fff" /><circle cx="57" cy="20" r="0.9" fill="#fff" />
      <circle cx="15" cy="52" r="1" fill="#fff" /><circle cx="49" cy="52" r="1" fill="#fff" />
      <circle cx="20" cy="55" r="0.8" fill="#fff" /><circle cx="44" cy="55" r="0.8" fill="#fff" />
      {/* body: slender, black, white-dotted thorax + head */}
      <ellipse cx="32" cy="34" rx="2.2" ry="10.5" fill="#151515" />
      <circle cx="32" cy="23.5" r="2.4" fill="#151515" />
      <circle cx="31" cy="23" r="0.5" fill="#fff" /><circle cx="33" cy="23" r="0.5" fill="#fff" />
      <circle cx="32" cy="27" r="0.45" fill="#fff" /><circle cx="32" cy="30" r="0.45" fill="#fff" />
      {/* antennae with clubbed tips */}
      <path d="M31 22 C 28 17, 25 15, 22 14 M33 22 C 36 17, 39 15, 42 14"
            stroke="#151515" strokeWidth="1.4" strokeLinecap="round" />
      <circle cx="22" cy="14" r="1" fill="#151515" /><circle cx="42" cy="14" r="1" fill="#151515" />
    </svg>
  );
}

// ONE monarch perched at the top edge of the page (her call: sitting, not
// flying — and anchored to the page, so it scrolls away with the content).
export function MonarchPerch() {
  return (
    <div className="monarch-perch" aria-hidden="true">
      <Monarch size={44} />
    </div>
  );
}
