// Monarch butterflies for the Intense look — drawn, not emoji (her call).
// One reusable monarch (orange wings, black veins/body, white spots) and a
// decorative flock of three drifting near the top of the screen.

export function Monarch({ size = 24, className = "", style }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" className={className}
         style={style} aria-hidden="true" fill="none">
      {/* forewings */}
      <path d="M30 31 C 20 12, 6 8, 7 19 C 8 29, 19 34, 30 31 Z"
            fill="#ff7a1a" stroke="#17171a" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M34 31 C 44 12, 58 8, 57 19 C 56 29, 45 34, 34 31 Z"
            fill="#ff7a1a" stroke="#17171a" strokeWidth="2.5" strokeLinejoin="round" />
      {/* hindwings */}
      <path d="M30 34 C 18 36, 10 46, 16 52 C 22 57, 29 46, 30 34 Z"
            fill="#ff9b4d" stroke="#17171a" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M34 34 C 46 36, 54 46, 48 52 C 42 57, 35 46, 34 34 Z"
            fill="#ff9b4d" stroke="#17171a" strokeWidth="2.5" strokeLinejoin="round" />
      {/* wing veins */}
      <path d="M29 30 L15 19 M29 31 L12 25 M30 34 L19 47 M35 30 L49 19 M35 31 L52 25 M34 34 L45 47"
            stroke="#17171a" strokeWidth="1.4" />
      {/* body + antennae */}
      <ellipse cx="32" cy="34" rx="2.6" ry="10" fill="#17171a" />
      <path d="M31 25 C 29 19, 26 17, 23 16 M33 25 C 35 19, 38 17, 41 16"
            stroke="#17171a" strokeWidth="1.6" strokeLinecap="round" />
      {/* white edge spots */}
      <circle cx="11" cy="15" r="1.4" fill="#ffffff" />
      <circle cx="53" cy="15" r="1.4" fill="#ffffff" />
      <circle cx="8" cy="22" r="1.1" fill="#ffffff" />
      <circle cx="56" cy="22" r="1.1" fill="#ffffff" />
      <circle cx="17" cy="50" r="1.2" fill="#ffffff" />
      <circle cx="47" cy="50" r="1.2" fill="#ffffff" />
    </svg>
  );
}

// three monarchs "flying" along the top — pure decoration, never blocks taps
export function MonarchFlock() {
  return (
    <div className="monarch-flock" aria-hidden="true">
      <Monarch size={36} className="m1" />
      <Monarch size={27} className="m2" />
      <Monarch size={20} className="m3" />
    </div>
  );
}
