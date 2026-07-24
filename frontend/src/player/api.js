// Player Zone API client: base URL from apiBase.js (same-origin in web prod,
// /api proxy in dev, Railway directly inside the iOS app), with the bearer
// token from localStorage on every call.

import { API_BASE as BASE } from "../apiBase.js";
const TOKEN_KEY = "vb_player_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY));

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(BASE + path, { ...options, headers });
  if (res.status === 401) {
    setToken(null);
    const err = new Error("signed out");
    err.signedOut = true;
    throw err;
  }
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch { /* no body */ }
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

export const playerApi = {
  register: (body) => request("/player/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body) => request("/player/login", { method: "POST", body: JSON.stringify(body) }),
  logout: () => request("/player/logout", { method: "POST" }),
  me: () => request("/player/me"),
  updateProfile: (body) => request("/player/profile", { method: "PUT", body: JSON.stringify(body) }),
  skills: () => request("/player/skills"),
  saveAssessment: (ratings) => request("/player/assessment", { method: "POST", body: JSON.stringify({ ratings }) }),
  generatePlan: () => request("/player/plan/generate", { method: "POST" }),
  plan: () => request("/player/plan"),
  toggleCheckpoint: (id, done) => request(`/player/checkpoints/${id}`, { method: "PUT", body: JSON.stringify({ done }) }),
  drills: (params = {}) => {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== "" && v !== false));
    const qs = q.toString();
    return request(`/player/drills${qs ? `?${qs}` : ""}`);
  },
  createLog: (body) => request("/player/logs", { method: "POST", body: JSON.stringify(body) }),
  logs: (limit = 20) => request(`/player/logs?limit=${limit}`),
  progress: () => request("/player/progress"),
  coachStatus: () => request("/player/coach-chat/status"),
  coachChat: (messages) => request("/player/coach-chat", { method: "POST", body: JSON.stringify({ messages }) }),
  deleteAccount: (password) => request("/player/account", { method: "DELETE", body: JSON.stringify({ password }) }),
  saveTheme: (theme) => request("/player/profile/theme", { method: "PUT", body: JSON.stringify({ theme }) }),
  saveCoachMemory: (content) => request("/player/coach-memory", { method: "PUT", body: JSON.stringify({ content }) }),
  videoConfig: () => request("/player/video-assessments/config"),
  submitVideo: (body) => request("/player/video-assessments", { method: "POST", body: JSON.stringify(body) }),
  videoHistory: (limit = 10) => request(`/player/video-assessments?limit=${limit}`),
};

// Short labels for the 8-skill radar.
export const SKILL_SHORT = {
  serve: "SRV", passing: "PAS", setting: "SET", attacking: "ATK",
  blocking: "BLK", digging: "DIG", movement: "MOV", game_iq: "IQ",
};
