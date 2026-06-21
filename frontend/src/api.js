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
  saveReceive: (lineupId, rotationIndex, placements) =>
    request(`/lineups/${lineupId}/rotations/${rotationIndex}/receive`, {
      method: "PUT",
      body: JSON.stringify({ placements }),
    }),
  overlapCheck: (coords) =>
    request("/overlap-check", { method: "POST", body: JSON.stringify({ coords }) }),
};

export const ROLES = [
  { code: "S", label: "Setter" },
  { code: "OH", label: "Outside Hitter" },
  { code: "MB", label: "Middle Blocker" },
  { code: "OPP", label: "Opposite / Right Side" },
  { code: "L", label: "Libero" },
  { code: "DS", label: "Defensive Specialist" },
];
