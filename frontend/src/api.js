// Tiny fetch wrapper. All calls go through Vite's /api proxy -> FastAPI.
// The whole coach API is gated: every request carries the coach's bearer
// token (localStorage), and a 401 anywhere means "sign in again".

// Dev: Vite proxies /api -> backend. Prod: same-origin (FastAPI serves both).
const BASE = import.meta.env.PROD ? "" : "/api";

const TOKEN_KEY = "vb_coach_token";
export const getCoachToken = () => localStorage.getItem(TOKEN_KEY);
export const setCoachToken = (t) =>
  t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);

async function request(path, options = {}) {
  const token = getCoachToken();
  const res = await fetch(BASE + path, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* no body */
    }
    const err = new Error(`${res.status}: ${detail}`);
    err.status = res.status;
    throw err;
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  // coach auth
  coachRegister: (body) => request("/coach/register", { method: "POST", body: JSON.stringify(body) }),
  coachLogin: (body) => request("/coach/login", { method: "POST", body: JSON.stringify(body) }),
  coachLogout: () => request("/coach/logout", { method: "POST" }),
  coachMe: () => request("/coach/me"),

  // teams
  listTeams: () => request("/teams"),
  createTeam: (body) => request("/teams", { method: "POST", body: JSON.stringify(body) }),
  setTeamLevel: (teamId, level) =>
    request(`/teams/${teamId}/level`, { method: "PUT", body: JSON.stringify({ level }) }),

  // players
  listPlayers: (teamId) => request(`/teams/${teamId}/players`),
  createPlayer: (teamId, body) =>
    request(`/teams/${teamId}/players`, { method: "POST", body: JSON.stringify(body) }),
  updatePlayer: (playerId, body) =>
    request(`/players/${playerId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deletePlayer: (playerId) => request(`/players/${playerId}`, { method: "DELETE" }),

  // mistakes (per player, keys from /mistake-catalog)
  mistakeCatalog: () => request("/mistake-catalog"),
  getMistakes: (playerId) => request(`/players/${playerId}/mistakes`),
  saveMistakes: (playerId, mistakes) =>
    request(`/players/${playerId}/mistakes`, { method: "PUT", body: JSON.stringify({ mistakes }) }),

  // notes (team notebook + pins on players/lineups)
  listNotes: (teamId, params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null && v !== false)
    ).toString();
    return request(`/teams/${teamId}/notes${qs ? `?${qs}` : ""}`);
  },
  createNote: (teamId, body) =>
    request(`/teams/${teamId}/notes`, { method: "POST", body: JSON.stringify(body) }),
  updateNote: (noteId, body) =>
    request(`/notes/${noteId}`, { method: "PUT", body: JSON.stringify({ body }) }),
  deleteNote: (noteId) => request(`/notes/${noteId}`, { method: "DELETE" }),

  // lineups
  listLineups: (teamId) => request(`/teams/${teamId}/lineups`),
  createLineup: (teamId, body) =>
    request(`/teams/${teamId}/lineups`, { method: "POST", body: JSON.stringify(body) }),
  deleteLineup: (lineupId) => request(`/lineups/${lineupId}`, { method: "DELETE" }),
  setPositions: (lineupId, positions) =>
    request(`/lineups/${lineupId}/positions`, {
      method: "PUT",
      body: JSON.stringify({ positions }),
    }),
  getRotations: (lineupId) => request(`/lineups/${lineupId}/rotations`),
  saveFormation: (lineupId, rotationIndex, phase, placements) =>
    request(`/lineups/${lineupId}/rotations/${rotationIndex}/formation/${phase}`, {
      method: "PUT",
      body: JSON.stringify({ placements }),
    }),
  saveSubs: (lineupId, rotationIndex, swaps) =>
    request(`/lineups/${lineupId}/rotations/${rotationIndex}/subs`, {
      method: "PUT",
      body: JSON.stringify({ swaps }),
    }),
  overlapCheck: (coords) =>
    request("/overlap-check", { method: "POST", body: JSON.stringify({ coords }) }),

  // substitution setup (per lineup)
  getSetup: (lineupId) => request(`/lineups/${lineupId}/setup`),
  saveCoverage: (lineupId, coverage) =>
    request(`/lineups/${lineupId}/coverage`, { method: "PUT", body: JSON.stringify({ coverage }) }),
  savePairs: (lineupId, pairs) =>
    request(`/lineups/${lineupId}/pairs`, { method: "PUT", body: JSON.stringify({ pairs }) }),
  generateSubs: (lineupId) =>
    request(`/lineups/${lineupId}/generate-subs`, { method: "POST" }),

  // simulation — batch analysis + single watchable set
  rolePresets: () => request("/role-presets"),
  simulate: (lineupId, body) =>
    request(`/lineups/${lineupId}/simulate`, { method: "POST", body: JSON.stringify(body) }),
  simulateGame: (lineupId, body) =>
    request(`/lineups/${lineupId}/simulate-game`, { method: "POST", body: JSON.stringify(body) }),

  // coach assistant
  coachStatus: () => request("/coach-chat/status"),
  coachChat: (messages, ctx = {}) =>
    request("/coach-chat", {
      method: "POST",
      body: JSON.stringify({ messages, team_id: ctx.teamId ?? null, lineup_id: ctx.lineupId ?? null }),
    }),
};

export const ATTRS = [
  { key: "serving", label: "Serving" },
  { key: "setting", label: "Setting" },
  { key: "attacking", label: "Attacking" },
  { key: "blocking", label: "Blocking" },
  { key: "defense", label: "Defense" },
  { key: "confidence", label: "Confidence" },
  { key: "pressure", label: "Pressure" },
];

export const COVERAGE = [
  { code: "all", label: "All-around (all 6)" },
  { code: "front", label: "Front-row only" },
  { code: "back", label: "Back-row only" },
];

// Level of play — scales unforced errors in the simulator (both sides).
export const LEVELS = [
  { code: "rec", label: "Recreational", sub: "Fun first — rallies end on mistakes" },
  { code: "middle_school", label: "Middle school", sub: "Learning the game" },
  { code: "high_school", label: "High school", sub: "The baseline" },
  { code: "club", label: "Club", sub: "Cleaner ball, tougher serves" },
  { code: "college", label: "College", sub: "Long rallies, points are earned" },
];

export const ROLES = [
  { code: "S", label: "Setter" },
  { code: "OH", label: "Outside Hitter" },
  { code: "MB", label: "Middle Blocker" },
  { code: "OPP", label: "Opposite / Right Side" },
  { code: "L", label: "Libero" },
  { code: "DS", label: "Defensive Specialist" },
];
