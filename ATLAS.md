# ATLAS — Volleyball Rotation & Lineup Tool

## Meta
| Field | Value |
| Last Active | 2026-06-21 |
| Status | building |
| Type | Full-stack learning project (3 phases) |

## Current State
Phase 1 built + extended. Engine-first: pure Python rotation engine
(`backend/app/engine.py`) with 27 passing tests, simulator-ready SQLite model
(permanent `players.id`, `rotation_index`, `dominant_hand` hook), FastAPI
server, React/Vite/SVG frontend with a guided flow. Each rotation has three
draggable/savable on-court PHASES — Serve (read-only) / Receive (overlap-checked)
/ Base (free after-serve sandbox) — stored in a generalized `formations` table.
Per-rotation SUBSTITUTIONS (`substitutions` table + `engine.apply_substitutions`):
the coach picks who's on court each rotation; the court, metadata, and a
play-by-play narration box all reflect the effective six. Verified live through
the user's running WSL stack (backend :8000 --reload, frontend :5173).

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
### 2026-06-21 (session 5)
- Researched the volleyball "pairs" the user described: confirmed they're the
  diagonal OPPOSITE pairings (setter↔opposite, OH↔OH, MB↔MB), always 3 zones
  apart, one front / one back. Distinct from the front/back SUB pairing built in
  session 4. Sources: NCAA, GoldMedalSquared, coachingvb. Formulated 3 ideas
  (presented to user, not yet built): pair-based lineup builder, opposite
  highlighter in viewer, lineup legality/structure validator.
- Built the explicit asks:
  1. Guided "? Guide" explainer (`HelpPanel.jsx`): step-by-step workflow + key
     concepts glossary (incl. both kinds of pairs) + coach recommendations.
  2. Coaching chatbot (`CoachChat.jsx` + backend `/coach-chat` + `/coach-chat/
     status`): floating assistant for drills + player help, backed by Claude
     (claude-sonnet-4-6). Reads ANTHROPIC_API_KEY from ~/.env via python-dotenv;
     degrades gracefully if absent. Added anthropic + python-dotenv to reqs.
- Did NOT make a paid Claude call in testing (cost guideline) — verified routing
  + status (key present) only; user exercises live chat. 30 tests pass.

### 2026-06-21 (session 4)
- Substitution roles + pairings (all per-lineup, user's choice). New tables:
  `lineup_player_meta` (coverage: all/front/back) + `sub_pairs`
  (front_player_id ⇄ back_player_id). `engine.generate_substitutions(start,
  pairs)` derives the per-rotation plan: the slot owner (the starter) plays when
  their slot is front row, the partner subs in for back-row rotations.
- "Generate, then edit" model (user's choice): POST `/generate-subs` overwrites
  all 6 rotations' subs from pairings; coach then hand-edits in the viewer.
- Libero hard rule enforced everywhere: can't be the front of a pair, blocked
  from front-row zones in save_subs (422) and filtered out of front-zone
  dropdowns in the UI.
- New endpoints: GET `/lineups/{id}/setup`, PUT `/coverage`, PUT `/pairs`,
  POST `/generate-subs`. New `SubstitutionSetup.jsx` lives in the lineup builder
  (coverage dropdowns + pairing editor + generate). 30 tests pass; verified the
  full middle/DS(libero) pairing flow live (libero on only in back-row
  rotations, never front), then reset sample to pristine.

### 2026-06-21 (session 3)
- Base view is now a draggable + savable sandbox (after-serve switch positions),
  no overlap check. Generalized storage: `receive_formations` → `formations`
  (phase 'receive'|'base'); added an idempotent `_migrate()` in db.init_db that
  copies legacy rows and drops the old table (ran live on the user's --reload db).
- Substitutions: per-rotation on-court control (user's choice). New
  `substitutions` table (starter_id→on_court_id per rotation);
  `engine.apply_substitutions`; rotations endpoint returns effective `positions`
  (subs applied) + `starter_positions` + `subs`; metadata computed from the
  effective six (so a subbed-in libero correctly isn't an attacker). New
  endpoints: `PUT .../formation/{phase}` and `PUT .../subs` (validates 6 distinct
  on-court players). Removed old `/receive` endpoint.
- Added a play-by-play narration box at the bottom of the rotation viewer
  (server, setter/attackers, who's in for whom) — per user request mid-build.
- Sub editor UI: collapsible "Substitutions" panel, per-zone dropdowns of
  starter + bench/libero. 27 backend tests pass; frontend builds clean. Verified
  all new endpoints live through the user's running backend, then reset the
  sample db to pristine.

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
