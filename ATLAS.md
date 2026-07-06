# ATLAS — Volleyball Rotation & Lineup Tool

## Meta
| Field | Value |
| Last Active | 2026-07-06 |
| Status | shipping |
| Live URL | https://volleyball-api-production.up.railway.app |
| GitHub | https://github.com/jimmyardis/volleyball-rotation-tool (public) |
| Railway | project volleyball-tool (2491a7c7-6c6b-43ab-9a3a-b2dec5b5b8cd), service volleyball-api (e02e7646-e478-4976-b8d5-23df55bd6d1c) |
| Type | Full-stack learning project (3 phases) |

## Current State (jump to latest Session Log entry for detail)
Full visual redesign shipped locally (2026-07-06, for the user's daughter):
role-colored player tokens everywhere, FIVB-style orange/teal court, animated
rotation/phase transitions, drag-and-drop lineup builder (bench → court),
trading-card roster with radar charts, mini-court thumbnails as rotation tabs,
tap-a-chip substitution panel, geometric overlap-fault lines (backend now
returns structured `fault_pairs`), and ranked simulation cards. 35 backend
tests pass; every screen verified via Playwright screenshots. NOT yet
committed or deployed to Railway.

## Next Action
Commit + push the redesign, then redeploy (rebuild frontend → copy dist to
backend/webdist → `railway up` from backend). webdist already has the new build.

## Blockers
None.

## Open Questions
- Stick with React/FastAPI/SQLite stack, or did she want the single-HTML-file
  faster start? (Built the recommended stack per spec.)
- Phase 2/3 timing — no date set.

## Session Log
### 2026-07-06 (session 9) — visual redesign ("less database, more shapes & colors")
- Built the full visual package the user's daughter asked for:
  1. Role color system (`frontend/src/roles.js`) — one CVD-validated hue per
     role (OH blue, S aqua, MB green, OPP violet, L gold, DS magenta; amber
     stays UI accent, red reserved for faults). Palette validated with the
     dataviz six-checks script against the app surface.
  2. Court.jsx: FIVB-style orange court on teal free zone, role-colored
     tokens, CSS-transform transitions so rotation/phase switches SLIDE
     players (drag disables transition), server halo + SERVE badge, dashed
     white setter ring.
  3. Overlap faults drawn geometrically: engine got `check_overlap_detail()`
     (structured zone pairs; string version derived from it), endpoints return
     `fault_pairs`, Court draws white-cased red dashed lines + rings between
     offending players. New engine test (35 total pass).
  4. CourtEditor.jsx: drag-and-drop lineup builder (bench strip under the
     court; drop to place, drop on occupant to swap, drag off to bench) —
     replaced the six zone dropdowns in LineupBuilder.
  5. RosterScreen: trading-card grid (role-color band, jersey, overall
     rating, RadarChart.jsx spider chart) + slider attribute editor.
  6. RotationViewer: MiniCourt.jsx thumbnails replace R1–R6 buttons; subs
     panel is now tap-a-chip (role-dot chips, starter dot, amber outline for
     on-court player).
  7. SimulationScreen: ranked cards with mini-courts + win bars; best/worst
     get status flags (green BEST / red WORK ON THIS).
- BUGFIX (backend, latent): sqlite connections created with default
  check_same_thread=True intermittently 500'd ALL endpoints — FastAPI runs
  sync dependency setup/teardown on different threadpool threads. Fixed in
  db.connect (check_same_thread=False; still one connection per request).
  This likely explains any past sporadic blank screens.
- BUGFIX (React): `{p.is_libero && ...}` rendered a stray "0" (SQLite ints,
  not bools) on roster cards + SubstitutionSetup — now `!!p.is_libero`.
- Verified end-to-end with Playwright (headless chromium; needed a locally
  extracted libasound2 — no sudo): screenshots of all screens, real drag on
  receive (fault lines render), bench→court swap drag in the editor, sim run.
  Test server ran on :8010 against a COPY of the db; real db untouched.
- webdist refreshed with the new build. Left NOT committed / NOT deployed.
- DEPLOYED to Railway as a single service. Live:
  https://volleyball-api-production.up.railway.app
- Prep: FastAPI serves the built frontend from `backend/webdist` (mounted last so
  it doesn't shadow API routes); `VB_DB_PATH` env points the SQLite file at the
  persistent volume `/data`; frontend calls API same-origin in prod
  (`import.meta.env.PROD ? "" : "/api"`); `backend/railway.json` (Nixpacks +
  uvicorn) + `backend/.railwayignore`.
- Railway: project `volleyball-tool`, service `volleyball-api`, volume at /data,
  env VB_DB_PATH=/data/volleyball.db + ANTHROPIC_API_KEY (piped via stdin, not
  echoed). Deployed with `railway up` (account token from ~/.env: export
  `$(grep RAILWAY_..._TOKEN ~/.env)`). Domain generated. Seeded sample team via
  the live API. Verified health, root app, simulate, chatbot status, persistence.
- GitHub: pushed to public standalone repo
  jimmyardis/volleyball-rotation-tool (subtree split from the monorepo).
- Redeploy: rebuild frontend → copy dist to backend/webdist → `railway up` from
  backend (linked to project). No auth on the app yet (add before real launch).

### 2026-06-21 (session 7)
- Chatbot can now BUILD & SAVE lineups via Anthropic tool use. Added
  `CREATE_LINEUP_TOOL` + `_exec_create_lineup` (resolves player id or name,
  validates 6 distinct zones, no orphan lineup on error) and a bounded (4-iter)
  tool-use loop in `coach_chat`. Context now includes `id=` per player so the
  model references players reliably. Response returns `created_lineups`; the
  chat UI shows a green "Added …" bubble with a "View in Rotations →" button
  (App reloads lineups + jumps via onLineupCreated/onViewLineup).
- Executor unit-verified directly on a temp db (valid by-id + by-name, plus dup
  / missing-zone / unknown-player / no-team errors) — NO paid Claude call made.
  Live tool loop reviewed, not executed (paid).
- 34 tests pass; frontend builds clean.
- BUGFIX (same session): the UI-only "✅ Added" bubbles had role 'system' and
  were being sent back to the API on the next turn → Anthropic 400 ("role
  'system' must follow a user/assistant message"). Now filtered out client-side
  before sending, and the backend ignores any non-user/assistant role.

### 2026-06-21 (session 6)
- Game simulation (Phase 3, simplified Monte Carlo) — new "Simulate" tab.
  Players got 6 editable 0-100 attributes (setting, defense, attacking,
  blocking, confidence, pressure) seeded from position presets
  (`engine.ROLE_PRESETS`); added via schema cols + a backfilling migration.
  `engine.rotation_rating` → `rally_win_prob` (Bradley-Terry, stakes penalize
  low pressure) → `simulate_rotations` (Monte Carlo, ranks the 6 rotations).
  Endpoints: POST `/lineups/{id}/simulate`, GET `/role-presets`. UI:
  attribute editor in RosterScreen (+ "use preset" button), SimulationScreen
  (stakes select, opponent slider, ranked win% table, best/worst callout).
- Chatbot now context-aware: ChatRequest takes optional team_id/lineup_id;
  `main._coach_context` builds a roster + per-rotation snapshot injected into the
  system prompt, so the coach can ask about their actual team/rotations.
- BUG fixed: `from __future__ import annotations` + a missing `SimRequest`
  import made FastAPI treat the body as a query param (422 "Field required").
  Lesson: with lazy annotations, an unimported model fails silently as a query
  param rather than NameError — always verify the import.
- 34 tests pass; verified simulate + context live (no paid Claude call made).
- STILL PENDING from session 5: the diagonal opposite-pairing feature (3 ideas
  proposed: pair-based lineup builder / opposite highlighter / structure
  validator) — user pivoted to simulation; revisit.

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
