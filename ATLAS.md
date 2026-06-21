# ATLAS — Volleyball Rotation & Lineup Tool

## Meta
| Field | Value |
| Last Active | 2026-06-21 |
| Status | building |
| Type | Full-stack learning project (3 phases) |

## Current State
Phase 1 built + extended. Engine-first: pure Python rotation engine
(`backend/app/engine.py`) with 24 passing tests, simulator-ready SQLite model
(permanent `players.id`, `rotation_index`, `dominant_hand` hook), FastAPI
server, React/Vite/SVG frontend. NEW (2026-06-21 session 2): each rotation now
has three on-court PHASES — Serve / Receive / Base. Receive is a draggable
serve-receive formation with live overlap-legality checking and per-rotation
SAVE (new `receive_formations` table). Base shows role-based switch positions.
UI reworked into a guided flow (progress stepper + contextual nudges). Verified
end-to-end through the user's own running WSL stack (backend :8000 --reload,
frontend :5173); all 24 tests pass; frontend builds clean.

## Next Action
Commit the new work (untracked changes in `volleyball-app/`). Optional next:
libero swap-in for receive/base views; or begin Phase 2 (stat tracking) against
the stable player IDs + rotation_index.

## Blockers
None.

## Open Questions
- Stick with React/FastAPI/SQLite stack, or did she want the single-HTML-file
  faster start? (Built the recommended stack per spec.)
- Phase 2/3 timing — no date set.

## Session Log
### 2026-06-21 (session 2)
- Added on-court PHASES to each rotation: Serve / Receive / Base. Decision
  (user grilled): Receive formations are SAVED per rotation (new
  `receive_formations` table), not just a scratchpad; UI reworked as a guided
  flow (not a full wizard).
- Engine: added normalized court coords (x left→right, y net→baseline) +
  `serve_positions`, `receive_default`, `base_positions`. Base assigns role
  lanes (OH=left, MB/L/DS=middle, S/OPP=right) and de-conflicts per row.
- Receive view is draggable (SVG pointer events) with live overlap checking via
  the existing `check_overlap`; saving allowed even when illegal (returns
  legality so a coach can keep WIP).
- 4 new engine tests (24 total pass). Verified the new endpoints through the
  user's own --reload backend — schema table auto-created on reload, no data
  migration needed (CREATE TABLE IF NOT EXISTS).
- Note: user runs the app from Windows via WSL; localhost:5173 forwards to the
  Windows browser. Their --reload backend + Vite HMR picked up all changes live.

### 2026-06-21
- Built Phase 1 from the design spec: backend (engine + db + FastAPI + tests)
  and frontend (React/Vite/SVG).
- Decision: followed the spec's recommended stack (Python/SQLite engine-first +
  React/SVG) rather than the single-HTML-file alternative, because Phase 2/3
  need real persisted player IDs and the SQLite schema.
- Engine metadata computes front-row attackers from who is actually up front
  (role != S, not libero) rather than hardcoding 2/3 — stays correct for 6-2
  and libero edge cases. Verified via tests + live API.
- 20 tests pass; frontend `npm run build` clean.
- Left mid-stream: overlap checker exists in engine/API but isn't surfaced in
  the UI yet; base-positions stretch feature not started.
