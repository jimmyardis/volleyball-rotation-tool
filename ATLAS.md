# ATLAS — Volleyball Rotation & Lineup Tool

## Meta
| Field | Value |
| Last Active | 2026-06-21 |
| Status | building |
| Type | Full-stack learning project (3 phases) |

## Current State
Phase 1 built and verified end-to-end. Engine-first architecture: pure Python
rotation engine (`backend/app/engine.py`) with 20 passing tests, SQLite data
model designed simulator-ready (permanent `players.id`, `rotation_index`,
unused `dominant_hand` hook), FastAPI server computing all 6 rotations + coach
metadata on the fly, and a React/Vite/SVG frontend (roster CRUD, lineup
builder, rotation viewer with court diagram). Frontend builds clean; live API
returns correct rotation metadata (back-row setter → 3 attackers, front-row
setter → 2). Overlap checker (stretch) implemented in engine + exposed via API,
not yet wired into UI.

## Next Action
`git add` the new `volleyball-app/` dir and commit (currently untracked); then
optionally wire the overlap checker / base-positions stretch features into the
frontend.

## Blockers
None.

## Open Questions
- Stick with React/FastAPI/SQLite stack, or did she want the single-HTML-file
  faster start? (Built the recommended stack per spec.)
- Phase 2/3 timing — no date set.

## Session Log
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
