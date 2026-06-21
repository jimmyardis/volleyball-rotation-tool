// Tiny fetch wrapper. All calls go through Vite's /api proxy -> FastAPI.

const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* no body */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  // teams
  listTeams: () => request("/teams"),
  createTeam: (body) => request("/teams", { method: "POST", body: JSON.stringify(body) }),

  // players
  listPlayers: (teamId) => request(`/teams/${teamId}/players`),
  createPlayer: (teamId, body) =>
    request(`/teams/${teamId}/players`, { method: "POST", body: JSON.stringify(body) }),
  updatePlayer: (playerId, body) =>
    request(`/players/${playerId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deletePlayer: (playerId) => request(`/players/${playerId}`, { method: "DELETE" }),

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
};

export const COVERAGE = [
  { code: "all", label: "All-around (all 6)" },
  { code: "front", label: "Front-row only" },
  { code: "back", label: "Back-row only" },
];

export const ROLES = [
  { code: "S", label: "Setter" },
  { code: "OH", label: "Outside Hitter" },
  { code: "MB", label: "Middle Blocker" },
  { code: "OPP", label: "Opposite / Right Side" },
  { code: "L", label: "Libero" },
  { code: "DS", label: "Defensive Specialist" },
];
