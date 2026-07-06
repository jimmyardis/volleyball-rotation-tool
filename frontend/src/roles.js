// One visual identity per ROLE, used everywhere a player appears: roster
// cards, the bench, the court, mini-courts, and the substitution panel.
// Palette validated for CVD separation + contrast on the app's dark surface
// (dataviz six-checks validator). Amber stays the brand/UI accent and red
// stays reserved for faults — neither is a role color. Every colored mark
// always carries its role code + jersey number as a direct label, so color
// never works alone.

export const ROLE_META = {
  OH:  { label: "Outside Hitter",        color: "#3987e5", ink: "#ffffff" },
  S:   { label: "Setter",                color: "#199e70", ink: "#ffffff" },
  MB:  { label: "Middle Blocker",        color: "#008300", ink: "#ffffff" },
  OPP: { label: "Opposite / Right Side", color: "#9085e9", ink: "#10131a" },
  L:   { label: "Libero",                color: "#c98500", ink: "#10131a" },
  DS:  { label: "Defensive Specialist",  color: "#d55181", ink: "#10131a" },
};

const FALLBACK = { label: "Player", color: "#969cab", ink: "#10131a" };

export const roleMeta = (code) => ROLE_META[code] || FALLBACK;
export const roleColor = (code) => roleMeta(code).color;
export const roleInk = (code) => roleMeta(code).ink;

// The zone grid every court view shares: 3 columns x 2 rows, net on top.
// front row: 4 | 3 | 2      back row: 5 | 6 | 1
export const ZONE_CELLS = {
  4: [0, 0], 3: [1, 0], 2: [2, 0],
  5: [0, 1], 6: [1, 1], 1: [2, 1],
};

// Nominal center of a zone cell in normalized court coords (x 0..1, y 0..1).
export const zoneCenter = (zone) => {
  const [col, row] = ZONE_CELLS[zone];
  return [(col + 0.5) / 3, (row + 0.5) / 2];
};

export const overallRating = (p) => {
  const keys = ["setting", "attacking", "blocking", "defense", "confidence", "pressure"];
  const vals = keys.map((k) => p?.[k]).filter((v) => v != null);
  if (!vals.length) return null;
  return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
};
