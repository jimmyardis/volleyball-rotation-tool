# ATLAS — Volleyball Rotation & Lineup Tool

## Meta
| Field | Value |
| Last Active | 2026-07-08 (session 12) |
| Status | shipping |
| Live URL | https://volleyball-api-production.up.railway.app |
| GitHub | https://github.com/jimmyardis/volleyball-rotation-tool (public) |
| Railway | project volleyball-tool (2491a7c7-6c6b-43ab-9a3a-b2dec5b5b8cd), service volleyball-api (e02e7646-e478-4976-b8d5-23df55bd6d1c) |
| Type | Full-stack learning project (3 phases) |

## Current State (jump to latest Session Log entry for detail)
Phase 3 SHIPPED (2026-07-08, session 12): touch-by-touch rally engine
(app/rally.py) replaces the coin-flip sim — watchable single set with live
court + narrated play-by-play, per-player mistake tags that causally affect
outcomes, and deterministic best/worst insights from 200-set batches. App
now opens with a coach-or-player landing page; COACH ACCOUNTS gate the whole
coach API (the old launch blocker is closed), with a 3-step team wizard and
a three-point notes system (team notebook / player pins / lineup notes).
Deployed to Railway + pushed to GitHub. 60 backend tests green.

## Next Action
USER MUST REGISTER THE FIRST COACH ACCOUNT on the live site ASAP — the
existing teams sit unclaimed until the first coach registration claims them,
and the URL is open. Then keep the daughter's week-long Player Zone trial
going. PINNED (user's call): camera serve-assessment v1 (MediaPipe).

## Blockers
None.

## Open Questions
- Stick with React/FastAPI/SQLite stack, or did she want the single-HTML-file
  faster start? (Built the recommended stack per spec.)
- Phase 2/3 timing — no date set.

## Session Log
### 2026-07-08 (session 12) — Phase 3 rally sim + coach accounts (deployed)
- Grilled the user's ask (deeper sims, watch-one-game, addable player
  mistakes, best/worst insights) via Q&A: full rally engine over cosmetic
  coin-flip; phantom-team opponent from slider; mistake catalog + severity +
  pressure amplification; auto-play watch mode; one set to 25; deterministic
  stat-based insights. Mid-session the user added: coach notes, coach
  sign-in, coach/player landing, team-setup questions — folded into design.
- ENGINE (app/rally.py, pure; 13 new tests + 7 API tests, 60 total green):
  serve→pass→set→attack→block/dig→transition chains; every touch a named
  player vs their ratings; rally scoring, sideouts rotate the effective
  (subs-applied) six; compact event stream for playback. New 7th attribute
  `serving` (ATTRS-driven column migration + presets). MISTAKE_CATALOG (8
  keys, each wired to its rally moment), severities sometimes/often,
  mistake_multiplier(stakes, pressure) makes low-pressure players choke
  late. simulate_batch aggregates rotations/players; generate_insights
  emits best/worst/go-to/serve-weapon/practice-focus/lineup sentences.
- BACKEND: coach.py auth (role='coach', same PBKDF2/session tables);
  middleware gates /teams /lineups /players /overlap-check /coach-chat
  /notes; teams.owner_user_id — FIRST coach registration claims ownerless
  teams (by design; single-coach history); /teams scoped per coach.
  player_mistakes + notes tables; mistakes + notes CRUD; POST
  /lineups/{id}/simulate-game (event stream) + rebuilt /simulate.
- FRONTEND: Landing (coach/player cards) → CoachAuth → TeamSetup wizard
  (name/season → grow-as-you-type roster rows → 5-1/6-2/not-sure, creates
  team+players+starter lineup). WatchGame.jsx: court rotates live on
  sideouts, scoreboard w/ serving highlight, narrate.js tone-colored
  play-by-play, ▶/⏸/1x/2x/4x/next-point/skip. SimulationScreen: watch |
  analyze modes; insights callout cards + ranked rotation cards
  (sideout%/serve% split). RosterScreen: mistake tag rows + severity chips,
  📌 Notes pin per card; serving slider (7-axis radar). Notes.jsx: notebook
  tab with source tags + QuickNotes pins (also on lineup in Rotations).
  api.js carries the coach bearer token; any 401 drops to the landing page.
- Verified: full Playwright journey on a DB copy (signup claimed 2 legacy
  teams → mistakes tagged → notes on player/lineup/team → watch mode at
  1x/4x → 200-set analysis with correct insights → wizard team). Deployed
  (asset hash flipped, /health + 401 gate + player zone confirmed live) +
  GitHub subtree pushed. Monorepo commit cd4e7b2.
- IMPORTANT handoff: live teams are UNCLAIMED until the user registers the
  first coach account. Emoji glyphs (💥🏐📋) show as tofu only in headless
  chromium (no emoji font) — fine on real devices.
- Deliberate scope cuts: cross-coach sub-resource ID probing not blocked
  (any authed coach could poke a known lineup id — fine at family scale,
  revisit if it goes multi-tenant); coach-chat lineup tool doesn't set
  owner… it inherits team ownership, fine.

### 2026-07-08 (session 11) — clean light retheme + wood court (deployed)
- User feedback: app "looks AI, almost like a database" — asked for a clean
  professional gray/pink/white/black look, better font, a court that looks
  like a real court, and phone-rotation adaptation. Design calls confirmed
  via Q&A: wood gym floor, monochrome+pink tokens, whole app (both surfaces).
- Theme: styles.css rewritten as a LIGHT theme — white cards on soft gray
  (#f7f7f8), near-black text, single pink accent (#d6336c), Inter typeface
  (Google Fonts + system fallback), subtle card shadows, uppercase micro-
  labels. Green/red still status-only; amber only for warning nudges.
- Court: SVG wood-plank pattern (defs/pattern in Court.jsx + CourtEditor.jsx,
  flat wood tone + seams in MiniCourt.jsx), painted white boundary/lines,
  pink attack line, dark net band. Fault red lines/white casing kept.
- Tokens: roles.js monochrome — charcoal ladder by role (OH darkest → DS
  lightest), LIBERO WHITE like the real contrasting jersey; pink = server
  halo + SERVE badge + setter ring (dashed). Roster cards/chips/mini-dots
  inherit automatically.
- Player Zone: removed per-position --accent injection (PlayerApp.jsx) —
  one brand accent everywhere; Progress skill radar now draws in pink.
- Orientation: new `(orientation: landscape) and (max-height: 540px)` block —
  viewer/lineup grids go two-column (court beside panel) even under the
  760px breakpoint, court capped at 72vh, stepper hidden for height; the
  portrait-only guard added to the old phone block. Manifest/theme-color →
  #f7f7f8; apple status bar black-translucent → default (light bg).
- Verified via Playwright on :8010 against a DB COPY (real db untouched):
  desktop/portrait/landscape shots of roster, lineups editor (bench drag UI),
  rotations serve+receive, simulate, and the full Player Zone (scratch
  account, plan generated). Frontend build clean; no backend changes.
- Deployed: `railway up` (live asset hash confirmed flipped, /health +
  /teams intact, live manifest theme #f7f7f8). GitHub subtree pushed
  (ff73c7b..85721fc). Monorepo commit 5c81006.

### 2026-07-06 (session 10d) — landscape rotation (deployed)
- Daughter request: app should rotate to landscape. Removed the manifest
  `orientation: portrait` lock; added landscape safe-area side insets (notch)
  and capped the coach chat pane to viewport height on short screens.
  Verified at 844x390 via Playwright. Deployed (c7ad8337 SUCCESS; live
  manifest confirmed lock-free) + GitHub pushed (c5082f5..ff73c7b).
- NOTE: iOS caches the manifest at install time — if the icon was already
  added to the home screen, remove + re-add it to pick up rotation.

### 2026-07-06 (session 10c) — installable web app + mobile fix (deployed)
- Add-to-Home-Screen packaging: manifest.webmanifest (standalone, start_url
  /#player — installed app launches into the Player Zone), icon set generated
  from the brand mark with PIL (512/192/apple-touch/favicon in
  frontend/public/), apple web-app metas + black-translucent status bar +
  viewport-fit=cover, safe-area insets for notch/home-indicator.
- Mobile bug found at iPhone viewport (390px): 6 tabs overflowed nav.tabs,
  Progress/Profile unreachable. Fixed: horizontal-scroll tab bar (no wrap,
  hidden scrollbar), tighter padding <480px. Verified via Playwright mobile
  emulation (login → Home → Plan → Progress).
- Deployed (6f55c092 SUCCESS; manifest + icons verified live) + GitHub
  subtree pushed (cd3f03b..c5082f5).
- Camera/pose feature PINNED by user for later.

### 2026-07-06 (session 10b) — Player Zone deployed + floating coach bubble
- Player Zone DEPLOYED (deployment 8b0fbd56 SUCCESS; new /player/* tables
  auto-created on startup; coach data intact) + GitHub subtree pushed.
- Added floating "My Coach" bubble on every Player Zone tab (except Coach
  tab): `PlayerCoachBubble.jsx` + `useCoachChat.js` hook; thread state lifted
  to PlayerApp so bubble + Coach tab are ONE conversation; Expand button
  jumps to the full pane. Verified via Playwright (fab on Home/Train, absent
  on Coach, Expand navigates). Deployed (49b0ff69 SUCCESS) + GitHub pushed
  (5339958..cd3f03b). NOTE: `git subtree split` must run from the repo
  toplevel (/home/wner), not a subdir.
- Decisions this session: web-first stays (camera feature works in Safari
  via MediaPipe WASM — no native app needed); iPhone path = Add to Home
  Screen now, Capacitor only if it outgrows family use. User wants the
  home-screen packaging LATER, not yet.

### 2026-07-06 (session 10) — Player Zone (player-side MVP)
- Built the MVP scope of `player-side-spec.md` (spec provided by user; key
  adjustments, documented here because the spec predates reality):
  SQLite not Postgres (matches actual stack); curated `knowledge.py` module
  instead of a vector store (corpus is small; swappable later); web surface in
  the SAME React SPA behind `#player` hash (no separate client, reuses the
  redesign's visual system); auth is player-side only (coach tool stays open
  as before); solo-first — CoachLink/parent/video all deferred per spec's
  own phasing.
- Backend: 10 new tables (users/sessions/player_profiles/skills/
  skill_assessments/plans/plan_blocks/plan_checkpoints/drills/training_logs),
  `player.py` router (~20 endpoints), `progression.py` (pure position-weighted
  plan builder: weakest primary skills first, blocks target current+1, mastery
  gating with unlock-next + reopen-on-uncheck), `knowledge.py` (8-skill
  taxonomy, cues + error→cause→correction tables per skill, position guides,
  24 seeded drills). Auth = PBKDF2-SHA256 (200k iters) + bearer session
  tokens; skills/drills seeded idempotently in db.init_db (upsert — knowledge
  module stays source of truth).
- Player AI coach: `/player/coach-chat` — encouragement-first / one-priority /
  always-a-next-action system prompt; context = profile + latest levels +
  active block + last 3 logs; grounded with knowledge snippets selected from
  the question text (alias matcher) + active block skill. Uses CHAT_MODEL env
  (default claude-sonnet-4-6). NO paid calls made in build/tests.
- Frontend: `src/player/` — PlayerApp (position color becomes the surface's
  --accent), AuthScreen, 2-step Onboarding (role-colored position picker +
  level-named sliders), Home (today's focus/streak/ask-coach), Plan (gated
  block cards), Train (drill library w/ filters + session log), Progress
  (8-axis radar via generalized RadarChart + history + streaks), Coach chat,
  Profile. RadarChart now takes axes/max props (roster cards unchanged).
- Tests: 5 new API tests incl. full mastery-gating walk + coach-context
  assembly (40 total pass). Playwright journey on a fresh scratch DB:
  register → onboard (Libero) → auto-generated plan led with Digging (weakest
  primary — correct) → checkpoints toggled → session logged → radar/streaks
  correct. Screenshots reviewed; fixed minutes-input truncation.
- NOT deployed yet (webdist has the build). No coach-side auth added — the
  coach tool is as open as before; revisit before any real launch.

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
- webdist refreshed with the new build. Committed (81bddc7 mid-session sweep
  by a concurrent agent + 401a270 finishing fixes), then user said "push":
  `railway up` deploy 03fb8812 SUCCESS, live site confirmed on the new asset
  hashes with /health + /teams intact; subtree split pushed to
  jimmyardis/volleyball-rotation-tool (5f8a8e8..3e6fc56).
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
