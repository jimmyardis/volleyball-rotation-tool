# ATLAS — Volleyball Rotation & Lineup Tool

## Meta
| Field | Value |
| Last Active | 2026-07-23 (session 17b, WSL) |
| Status | shipping |
| Live URL | https://volleyball-api-production.up.railway.app |
| GitHub | https://github.com/jimmyardis/volleyball-rotation-tool (public) |
| Railway | project volleyball-tool (2491a7c7-6c6b-43ab-9a3a-b2dec5b5b8cd), service volleyball-api (e02e7646-e478-4976-b8d5-23df55bd6d1c) |
| Type | Full-stack learning project (3 phases) |

## Current State (jump to latest Session Log entry for detail)
Session 14 (2026-07-22, Mac): iOS PHASE A DONE — Capacitor 8 wrap ("Player
Zone", com.jimmyardis.PlayerZone) builds and runs on the iPhone 17 Pro
simulator: landing screen renders, safe areas respected, native API base +
haptics + Info.plist permission strings in place. Committed + pushed from
the Mac (312529c). Not yet verified: sign-in/chat/Film-Room on a real
device (needs credentials + her phone). Session 13 (2026-07-20): FILM ROOM
shipped — video self-assessment for all
six ball skills (browser samples ~10 frames + runs MediaPipe pose locally,
raw video never uploaded; backend computes deterministic serve metrics and
gets rubric-grounded structured feedback from Claude vision; new Film tab +
coach-chat integration). Coach KNOWLEDGE BASE v2: audited against USAV /
AVCA / Gold Medal Squared / Art of Coaching, cues 25→67, error rows 24→63,
drills 29→79 (56 solo-friendly), VIDEO_RUBRICS + PRACTICE_PRINCIPLES wired
into both AI prompts. 72 backend tests green. Repo's .git was found MISSING
(WSL-crash fallout; sessions 12b-12e had been shadow-committed to the home
repo) — restored from a GitHub clone, everything pushed properly.

## Next Action
iOS: install on the DAUGHTER'S iPhone from Xcode (family Apple Developer
account in Xcode → Signing & Capabilities → pick team; her phone on the
cable, Developer Mode on, ⌘R). She verifies: welcome tour → create account
→ coach chat → film a serve. She reviews the design page (link in session
14b) and rules on icon B vs A/C. Then Phase C: TestFlight upload + internal
group (external group fallback for her account if ASC team invite won't
work for a minor). Mac↔WSL note: nothing here needs a Railway deploy.
Also still open from session 13: have the daughter film one real serve in
the Film Room on the live site and
sanity-check feedback quality (the smoke test only verified format + honest
cant_tell behavior on junk frames — no real clip has been reviewed yet).
Still open: USER MUST REGISTER THE FIRST COACH ACCOUNT on the live site —
existing teams sit unclaimed and the URL is open.

## Blockers
None.

## Open Questions
- Stick with React/FastAPI/SQLite stack, or did she want the single-HTML-file
  faster start? (Built the recommended stack per spec.)
- Phase 2/3 timing — no date set.

## Session Log
### 2026-07-23 (session 17b, WSL) — coach-side layout pass (deployed)
- Her list, all shipped: ROSTER — sphere IS the roster; card grid behind a
  "Show all player cards (N)" toggle (auto-shows while editing). LINEUPS —
  "+ Lineup" button opens the create form; lineups listed full-width below
  (tap to open the starting-six editor; two-col layout retired). SIMULATE —
  de-clunked into a "Match setup" card: labeled field grid (lineup /
  opponent slider / level) + two big Watch/Analyze mode buttons. NOTES —
  spiral-binder accent down the notebook's left edge (CSS repeating
  radial-gradient rings, .notebook-page). NET TABS extended to the coach
  side (selectors generalized .player-zone->.app).
- Verify note: Simulate needs a lineup to show setup (scratch team got one
  seeded via API).
### 2026-07-23 (session 17, WSL) — coach gotcha: the roster sphere (deployed)
- HER SPEC for the coach side's hook: a dynamic sphere you can move around,
  a dot per player, tap a dot -> their card (skills + position). Built as
  components/RosterSphere.jsx: PURE SVG 3D (no deps) — Fibonacci-lattice
  point distribution, yaw/pitch drag rotation w/ pointer capture, idle
  auto-spin (resumes 2.5s after interaction), perspective projection,
  lat/long wireframe rings, depth-sorted dots (back ones dimmed), jersey
  numbers in role-colored dots, first names under front-facing dots.
- Hero card at the top of Roster (hidden while add/edit form is open);
  tap -> floating player card (band + radar + overall + Edit/Close),
  static-stacked on phones.
- TRAP: setPointerCapture retargets click events to the svg — per-dot
  onClick never fires. Taps are resolved manually on pointerup (<6px
  movement + document.elementFromPoint -> .closest('.sphere-dot') ->
  data-pid). Playwright note: use mouse.click at dot coords, not
  locator.click (dots move with the idle spin).
### 2026-07-23 (session 16c, WSL) — coach intro interview + net monarch (deployed)
- HER SPEC: after the skill self-assessment, Coach pops up in the chat:
  "Hi (name), I'm Pepper, your AI coach — mind if we get started with a
  few questions?" Yes/No. Yes -> 3 free-form questions (strengths /
  struggles / season goal) answered in the normal chat input, scripted
  client-side (zero API calls), then saved via new PUT /player/coach-memory
  into player_profiles.coach_memory (migration + schema). _player_context
  now injects it ("what the player told Coach about themselves") so every
  chat + film review is personalized. Trigger = empty coach_memory + empty
  thread, so EXISTING accounts get the intro once too. "Maybe later"
  dismisses politely. 75 backend tests.
- Intense: the corner monarch now SITS ON THE NET — bigger (60px), absolute
  atop the tab bar's right side inside new .pz-net-wrap (nav's overflow
  clipping avoided by wrapping, not nesting). Wordmark monarch unchanged.
- Gotcha during verify: local uvicorn predated the new endpoint (no
  --reload) — silent 404 swallowed by the retry-later catch; restart fixed.
### 2026-07-23 (session 16b, WSL) — player revamp: 4 tabs, activity-first Train (deployed)
- Her layout pass: PLAN TAB (and Home + Film tabs) RETIRED — player nav is
  now Coach / Train / Progress / Profile. Plan endpoints + progression.py
  remain server-side but are unsurfaced; onboarding no longer generates a
  plan ("Finish — let's train"); PLAYER_COACH_SYSTEM feature list + chat
  context rewritten with NO plan/goal/checklist references (context test
  now asserts their absence); Progress stat "blocks mastered" ->
  "sessions logged". HomeScreen/PlanScreen/FilmScreen deleted;
  FeedbackCard extracted to player/FeedbackCard.jsx (chat renders it).
- TRAIN = "+ Log an activity" button opening a form (her spec): skill
  DROPDOWN, minutes, drill chips filtered to the chosen skill, quality
  slider + notes. Recent activities + drill library below.
- Player tab bar drawn as a NET across the screen (mesh background via
  repeating-linear-gradients + accent-2 top tape; tabs sit as panels on
  the net). Loading is now her volleyball SPINNING (BallSpinner; coach
  Loader delegates to it too).
- Verified: 4 tabs render, log flow saves + lists, 74 backend tests.
### 2026-07-23 (session 16, WSL) — the gotcha moment: chat+film ONE device (deployed)
- Her spec (daughter driving; she flagged that most messages are her):
  player-side revamp starts with the hook — the AI coach + film upload
  combined like any modern AI chat. Built: CoachScreen is now a full
  chat device (bubbles, pinned input bar) with a CAMERA BUTTON in the
  input row; tapping it opens skill chips + how-to-film + choose/record,
  and the review lands IN the conversation (user "sent a clip" turn +
  assistant turn rendering FeedbackCard, now exported from FilmScreen).
  Thread text summary of each film review keeps chat-API context
  continuous (useCoachChat strips non-{role,content} keys before POST).
- Coach is the FIRST tab and default view after sign-in (tabs reordered).
- First-time spotlight (her mid-turn add): pulsing ring on the camera
  button + bobbing callout bubble "Send a video of any rep — I'll analyze
  it"; retires permanently on first camera tap (localStorage
  pz_cam_tip_seen). NOTE: infinite bob animation makes playwright deem the
  element unstable — click(force=True) in tests.
- Verified live: empty-state hook copy, camera panel (6 skills + tips),
  real chat round-trip (reply referenced her actual checklist), tip
  persistence across reload. Film tab kept as the history/detail view.
### 2026-07-23 (session 15c, WSL) — her flow spec: ONE front door (deployed)
- ROUND 6: her own icon art is in — she dropped a side-view orange/black
  butterfly + a proper volleyball line-icon in Downloads (white-bg PNGs).
  Ink extracted onto transparent alpha (PIL white-unmix: a=255-min(rgb),
  un-premultiply), trimmed, 160px, saved to frontend/src/assets/
  {monarch,volleyball}.png. Volleyball.jsx and Monarch now render her art
  (SVG drawings retired); .pz-mark-img gets a white drop-shadow on Intense
  so black linework reads on dark panels. All existing usages (ThemeMark,
  Look buttons, perch, picker cards, WhoAreYou, Welcome lens) inherit.
- ROUND 5b: absolute-corner decor STILL collided with coach header buttons
  at desktop widths (h1 + team-bar share one row there). Final fix: decor
  is a real in-flow strip at the very top (flex, right-aligned, no
  negative margins) — overlap impossible at any width, verified
  geometrically (bounding-box intersection checks vs Sign out / + New
  team) and visually. Lesson logged: corner-floated decor around a
  flex-wrapping header is a loser; reserve space in flow instead.
- HER ROUND 5: decor now ANCHORED TO THE PAGE (position: absolute in the
  .app, which gained position: relative) — she reported the fixed-position
  butterflies/clouds "moving with me" on scroll. Intense decor is ONE
  monarch perched still at the top-right edge (MonarchPerch replaces the
  flock). Wordmark is just "Pepper" everywhere (coach header + landing
  dropped "Volleyball") with a per-look mark beside it (ThemeMark):
  volleyball on Classic, monarch on Intense, cloud on Sky. Volleyball.jsx
  REDRAWN as a real ball (three seams swirling from center + rim panel
  lines) — the old mark read as a network/globe icon, her catch.
- HER ROUND 4: monarchs redrawn realistic (layered SVG: black margin
  bands w/ white spots, black wingtips, veined orange cells, clubbed
  antennae). Phone overlap fixed — decor now sits beside the short title
  row on <=640px, scaled 0.72; NOTE the mobile overrides must stay LAST
  in styles.css (cascade bug: appended sky block was beating a mid-file
  media query). NEW third scheme "sky": sky/light blue + white, 3 drawn
  clouds drifting top-right (Clouds.jsx), backend theme sets updated,
  Look button now cycles classic->intense->sky.
- HER ROUND 3: themes extended to the COACH side (users.theme column +
  migration, PUT /coach/theme, /coach/me returns it; Look button in the
  coach header, data-theme generalized to .app scope). Butterfly emoji
  REPLACED with drawn monarch SVGs (components/Monarchs.jsx): three
  monarchs drifting top-right on Intense (both surfaces, prefers-reduced-
  motion respected), small monarch inline on the Look button + picker
  card. Intense rebalanced MORE ORANGE (--pop orange; the one pink wink
  left = streak stat numbers). Dark-mode fixes: radar polygons forced
  orange (inline style needed !important), nudge banner dark-amber,
  flock dropped below wrapped header on phones.
- FOLLOW-UP (her ask): the look is now PER ACCOUNT — player_profiles.theme
  column (migration + schema), settable in signup step 3 (profile PUT
  carries theme), alone via PUT /player/profile/theme, and from a new
  always-visible header button ("Look: Classic" / "Look: Intense 🦋") that
  toggles + saves. /me returns it; the client adopts the account theme
  over any stale device preference (verified across two fresh browser
  contexts). 74 backend tests.
- Her report (as product owner, directly): web "/" showed a static hero ->
  Log in/Sign up while Get Started in the tour jumped straight to player
  sign-in; coach path was hidden behind a corner link. Her spec: the
  DYNAMIC tour page is the homepage, and Get started leads to the
  coach-or-player question.
- Implemented everywhere: web "/" now opens the Welcome tour itself; tour
  actions (Get started=register / I-already-have-an-account=login) -> NEW
  shared WhoAreYou step (components/WhoAreYou.jsx) -> right auth form in
  the right mode. Same flow at #player and in the native shell (PlayerApp
  welcome -> role step; picking coach carries mode via sessionStorage
  coach_auth_intent to the coach side). Old static landing hero deleted.
- Also: coach-signup "broken" report = silently disabled button on short
  passwords (fixed earlier today); verified coach signup live twice.
- NOTE for Mac session: native bundle predates themes + this flow — run
  git pull, npm run build, npx cap sync before her next sim/device test.
  Her "no color schemes" report is that stale native bundle (Look card
  verified live on prod web Profile).
### 2026-07-23 (session 15b, WSL) — her UI batch 2 + roster import (deployed)
- POST-SHIP: "can't sign up as coach" report — flow verified working on
  prod (browser-automated, twice). Root-cause suspect fixed: the Create-
  account button silently disabled on <6-char passwords (reads as broken).
  Now always clickable w/ plain-language messages. Deployed + re-verified.
- LANDING reworked to her spec: name "Pepper Volleyball", flow is now
  Log in / Sign up FIRST -> "coach or player?" page -> the right auth form
  in the right mode (player intent rides sessionStorage pz_auth_intent;
  CoachAuth gained initialMode). Net accent (SVG mesh band) fixed across
  the bottom of the landing. Coach in-app header renamed Pepper Volleyball.
- Green guided-stepper chips REMOVED from the coach side per her call
  ("looks weird"); the one-sentence nudge + Guide button remain.
- PLAYER LOOKS: two schemes, picked at onboarding step 3 (new) and
  switchable in Profile. "Classic" = black/white/grey + little bits of
  pink (--pop: active tab underline, stat numbers, dots). "Intense" =
  black & orange w/ pink pops + butterfly next to the header wordmark.
  Stored per-device (localStorage pz_theme), applied via
  .player-zone[data-theme]. This resolves the Mac session's open
  "does pink return" question: yes, as pop accents in both schemes.
- SPORTSENGINE ROSTER IMPORT (coach ask, via user): no public SE API, so
  v1 = "Import CSV" on Roster — quote-aware parser, SportsEngine export
  headers (First/Last Name, Jersey Number, Position) + variants, position
  words -> role codes (Right Side->OPP etc.), editable preview with ⚠ on
  defaulted rows, then bulk-create. Verified end-to-end with a synthetic
  SE export (6 players). AWAITING a real SportsEngine export from the
  requesting coach to confirm exact headers.
- Verified by screenshot: landing intent+role pages, theme step, Intense
  home, import preview. Butterfly = emoji (renders on devices; tofu in
  headless shots). Deployed to Railway + pushed.
### 2026-07-23 (session 15, WSL) — daughter's UI feedback round 1 (deployed)
- "Building your plan… forever" report: NOT reproducible on current build —
  full UI onboarding on prod resolves in ~1s (playwright). Diagnosis: her
  installed home-screen app is a STALE CACHED BUNDLE from before the 12c
  fix. One-time fix: delete + re-add the home-screen icon. Permanent fix
  shipped: _html_no_cache middleware (Cache-Control: no-cache on HTML only;
  hashed assets still cache) so installed apps always pick up new builds.
- Coach Roster de-bulked per her request: add-player form now collapsed
  behind a "+ New player" button (screen-head layout), auto-opens on Edit,
  closes on save/cancel; empty-state copy points at the button. Fixed a
  self-inflicted CSS regression (button.danger rule made ghost Delete
  buttons red-on-red; now :not(.ghost)).
- More UI feedback from her coming next session (aesthetics + copy for
  Home/Onboarding — screenshots of current state in Windows Downloads).
### 2026-07-23 (session 14d, Mac) — her logo, everywhere (307c4f1)
- She delivered a logo (B&W athletic: swoosh ball w/ "pepper" panel, net,
  italic wordmark, tagline "Practice · Progress · Thrive") — integrated as
  the whole brand: accent token pink→ink #17171a (all buttons/tabs/ticks
  follow), icon = ball crop on white (black inverse = alternate), splash =
  full lockup, welcome hero = transparent-ink ball + tagline headline,
  wordmarks italic 800. PWA icons/favicon updated too. Source logo lives at
  frontend/brand/pepper-logo.png.
- Gotcha logged: WebKit ignores mix-blend-mode when the element has a
  filter AND across composited scroll layers — transparent-alpha asset
  (canvas ink-extraction via headless Chrome) is the reliable pattern.
- Verified on sim; review artifact updated in place (same URL). Pending
  her call: white vs black icon; whether pink returns as a small accent.
### 2026-07-23 (session 14c, Mac) — the app is PEPPER (61d009a)
- The daughter named it: **Pepper** (the warmup drill). Renamed everywhere
  user-visible: bundle id com.jimmyardis.Pepper (changed BEFORE the ASC
  record exists — it is permanent after), display name, splash wordmark,
  welcome tour title, auth wordmark, in-app header, PWA manifest. Verified
  on sim (home screen says Pepper). Review artifact updated in place.
- ASC note for Phase C: app record must use bundle id com.jimmyardis.Pepper
  and the store name "Pepper" (may be taken — have a fallback like "Pepper
  Volleyball" ready).
### 2026-07-22 (session 14b, Mac) — Phase B: icon, splash, app-like onboarding (90dd6c0)
- Product owner (the daughter) asked for: our stab at icon + splash + a more
  intuitive, "app"-like onboarding (disliked the Who-are-you chooser).
- Native now launches straight into #player (chooser is web-only; Coach
  tools still linked in-app). NEW Welcome.jsx: full-screen 3-slide swipe
  tour (scroll-snap, haptic per slide, animated dots) → Get started /
  sign-in; shows once per device. AuthScreen restyled full-screen w/ brand
  mark + big inputs; Onboarding got step dots, haptics, phone-width slider
  layout. All shared with the web #player route.
- Icon (shipped): white line-volleyball on brand pink, generated from the
  app's own Volleyball.jsx mark via headless Chrome; 2 alternates (pink-on-
  cream; cropped "serve") kept in scratch + review page. Splash: mark +
  wordmark on cream, all 3 slots. Verified: build + fresh install on the
  iPhone 17 Pro sim — welcome tour + home-screen icon look right.
- Review artifact for her (icons A/B/C, splash, screens):
  https://claude.ai/code/artifact/432f3b46-3fdc-45a9-a3cd-a9c0bcd45124
- DECISION pending her review: icon B vs A/C; tour copy tweaks welcome.
- Next: install on HER phone (not Dad's) via Xcode; then TestFlight.
### 2026-07-22 (session 14, Mac) — Capacitor wrap: Phase A verified on simulator
- First session on the MacBook (per HANDOFF-IOS.md). The previous Mac
  session CRASHED mid-wrap before committing or verifying anything; this
  session recovered it. Root cause of the machine-wide failures: an
  orphaned 14-day-old claude process holding 985 zombie children had
  exhausted the per-user process table (every fork() failed — git push,
  clang, everything). Killed it; system healthy.
- Recovered work, all intact and now committed (312529c): Capacitor 8
  project in frontend/ios (SPM, no Pods), appId com.jimmyardis.PlayerZone,
  app name "Player Zone"; apiBase.js (native shell → Railway directly, web
  unchanged); haptics.js + PlanScreen ticks; html.is-native safe-area CSS
  (WKWebView reports display-mode "browser", not standalone); Info.plist
  camera/mic/photo strings with the on-device-video privacy story; splash
  + keyboard config in capacitor.config.json.
- Verified: xcodebuild succeeds; app installs, launches, and renders
  correctly on the iPhone 17 Pro simulator (landing chooser, safe areas,
  brand styles). NOT yet verified: sign-in / coach chat / Film Room —
  needs credentials and a real phone (UI automation on the sim needs
  accessibility permissions this environment doesn't have).
- Machine split respected: no backend, no webdist, no Railway.
### 2026-07-21 (session 13b) — iOS prep: handoff spec, account deletion (deployed)
- Decision: iPhone app = CAPACITOR WRAP of the existing frontend (not an RN
  rewrite), built on the wife's MacBook under the user's Apple Developer
  account (Apple requires 18+ holders; App Transfer keeps this reversible).
- HANDOFF-IOS.md committed to repo root: goal, machine split (Mac owns
  frontend/+ios/+TestFlight; WSL owns backend/+Railway deploys+token),
  phased plan A-D, technical landmines, Apple compliance list, Mac setup
  checklist. MacBook flow: clone → Claude Code → "read HANDOFF-IOS.md".
- CORS for capacitor://localhost: verified ALREADY OPEN on prod (allow-
  origin *, gate skips OPTIONS) — no change needed, handoff updated.
- DELETE /player/account shipped (Apple hard requirement): password
  re-entry confirms; one transaction wipes video_assessments, logs,
  checkpoints, blocks, plans, assessments, profile, sessions, user row.
  Profile screen: Delete-account card + fixed stale "video features come
  later" copy (now describes Film Room on-device privacy). 73 tests green.
  Deployed to Railway (a878451d) + pushed; live endpoint verified 401
  unauthenticated. Coach-account deletion still TODO before App Store.
### 2026-07-20 (session 13) — Film Room + knowledge base v2 (deployed)
- FILM ROOM (both engines, per user's call): Claude-vision review for
  serve/pass/set/attack/block/dig PLUS MediaPipe serve metrics. Privacy-first
  pipeline: browser extracts 10 JPEG frames (canvas) and runs the pose
  landmarker via CDN (@mediapipe/tasks-vision 0.10.14, lite model) locally;
  only frames + landmarks upload, nothing binary stored (video_assessments
  table keeps structured feedback + metrics JSON only).
- Backend: app/video_assess.py (config/create/history endpoints, strict-JSON
  feedback with checkpoint verdicts good/needs_work/cant_tell, drill recs
  validated against the library), app/serve_metrics.py (pure-Python landmark
  math: elbow extension at contact ≥160°=full per Reeser et al. bands,
  contact height in torso units, knee load, step detection reported only as
  detected/not). Coach chat context now includes the last 2 Film Room
  reviews; PLAYER_COACH_SYSTEM feature list updated (it previously said the
  app has NO videos — would have contradicted the new feature).
- Real-API smoke test: submitted non-volleyball frames; model correctly
  returned all-cant_tell + "no footage to review" (no hallucinated feedback).
  MediaPipe CDN load verified headless. UI screenshot verified (7th tab
  "Film"; tab bar scrolls on phones).
- KNOWLEDGE BASE v2 from 4 parallel research agents (USAV, AVCA, GMS, AoC,
  JVA, motor-learning lit). Corrected existing content: float toss = low
  straight-arm LIFT (never "raise the toss"); approach = long-low penultimate
  + SHORT-quick last step; wrist snap de-emphasized (GMS: it's a result, not
  a cause); passing target 4-5 ft off net (was 2-3); crossover default for
  long block trips; setters square to left antenna every set. Added: seam
  serving/rules, topspin + jump-float progressions, overhead floater takes,
  knee-drop short balls, out-of-system defaults, split step, pancake
  progression, setter-row scouting. Drills 29→79. PRACTICE_PRINCIPLES
  (game-like>blocked, one cue at a time, external focus, faded feedback,
  jump-volume + shoulder safety) now ground both AI prompts.
- REPO SURGERY: /home/wner/volleyball-app/.git was gone — git commands were
  falling through to the HOME repo (remote jane-jacobs-bot; 14 volleyball
  commits stranded there unpushed, incl. an automated "preserved at session
  end" snapshot from a concurrent carolina-redesign session). GitHub's
  volleyball-rotation-tool actually HAD 12e already (ATLAS note was stale).
  Restored .git from a fresh clone; committed today's work as 9b6532f +
  4c48dc4; pushed. Home-repo strays left alone (local only, harmless).
- Deployed via railway up (service deploys by CLI, NOT GitHub webhook —
  the push alone would have shipped nothing). 72 backend tests green.
### 2026-07-08 (session 12e) — Player Zone de-jargon + solo drills (LOCAL only)
- Live player-side feedback (daughter): "watch for one thing" meant nothing;
  coach bot showed "how do I know if I passed my block?" (nonsense); wanted
  more drills with no net/partner. Train area otherwise liked.
- Root cause of "passed my block": terminology collision — a plan unit was a
  "block" and its items "checkpoints", but block/pass are volleyball SKILLS.
  Fix: player-facing wording is now GOAL + CHECKLIST everywhere (HomeScreen,
  PlanScreen, styles pz-checklist-label), incl. the AI coach system prompt +
  context builder, which is now explicitly told never to call a unit a
  "block". DB table/column names (plan_blocks, plan_checkpoints) unchanged —
  internal only. User picked "Goals + checklist" wording via a preview Q.
- Renamed drill film-one-thing "Watch For One Thing" → "Watch a Match, Track
  One Thing" + plain-language how-to.
- Added 6 no-net/no-partner solo drills (toss-pass-self, straight-set-ladder,
  shadow-approach-arms, shadow-block-press, sprawl-recover, line-hops-base).
  Solo library 16 → 22; blocking gained its first no-NET solo drill. Verified
  via full API flow on the local db: fresh OH player, mixed assessment →
  plan's active goal (Passing) auto-pulled "Toss & Pass to Yourself".
- 63 backend tests pass (updated one context-assembly assertion). Committed
  LOCALLY 16d9ae2 — NOT deployed to Railway, NOT pushed to GitHub yet (waiting
  on user's deploy call). Old plans keep old checklist text until "Rebuild
  plan"; the Home/Plan labels update immediately regardless.
- NOTE on the "prompt" she saw: current code has NO player-side suggestion
  chips (removed in 12d) — if her installed PWA still shows them she's on a
  cached old build; remove + re-add the home-screen icon after deploy.

### 2026-07-08 (session 12d) — player coach chat + My Plan simplification (deployed)
- Live feedback: coach bot referenced a nonexistent "quiz", pushed prompts
  every message; My Plan "confusing"; drills under-explained. (User likes
  Train as-is.)
- PLAYER_COACH_SYSTEM rewritten: natural conversation (no forced praise-
  open / call-to-action close — those formulas were making the model
  invent next-step app features); hard feature list with "NO quizzes,
  tests, videos, badges" so it can't hallucinate app features; DRILLS rule
  (purpose, setup, steps, reps, one cue, done-well). Chat context now
  includes full drill-library entries via new knowledge.drill_snippets
  (matched to mentioned skills + active block, position-fit, ≤6).
- Removed COACH_STARTERS chips from CoachScreen + PlayerCoachBubble —
  plain "ask anything" empty state (user: "no nonsense prompts").
- PlanScreen rebuilt simple: WORKING ON NOW card (big skill + goal chip +
  checklist + drill tags), UP NEXT numbered names only, FINISHED ✓ rows.
  No LOCKED badges/criteria dumps. Gating engine + endpoints unchanged.
  progression checkpoint wording friendlier ("Beat the challenge: …") —
  old plans keep old text until rebuilt.
- 63 tests pass; verified phone-size via Playwright (seeded plan w/ one
  finished block). Deployed (asset flip confirmed) + pushed. Commit 8bdbe13.
- NOTE: chat behavior change verified by prompt/grounding content only —
  no paid model call made; user should sanity-check one real chat.

### 2026-07-08 (session 12c) — BUGFIX: all-5s self-assessment dead-ended with no plan
- Live report: Player Zone "says building your plan.. and then never does
  it". Railway logs showed POST /player/plan/generate → 409 right after a
  200 assessment. Root cause: player self-rated EVERY skill 5/5 (kids max
  the sliders) → progression.build_plan skipped all at-Mastery skills →
  empty → 409 "every skill is already at Mastery" — silently swallowed by
  Onboarding's try/except, so no plan ever appeared and Plan tab's "Build
  my plan" hit the same wall.
- Fix: build_plan never returns empty — with nothing below level 5 it
  builds PROVE-IT blocks (the position's primary skills held at Mastery
  under the hardest success criteria, e.g. "Attacking / Spiking →
  Mastery"). Regression test added (63 pass). Backend-only change.
- Deployed + verified LIVE with a scratch player account `plan_smoketest`
  (left in the prod users table; harmless, invisible to other players):
  all-5s OH assessment → 200 with 3 prove-it blocks. The daughter's stuck
  account self-heals: Home/Plan → "Build my plan" now generates.
- Also in logs: two /player/register 422s before her login — probably a
  username with spaces or short password; client shows those errors, no
  action taken. Commit 771d287.

### 2026-07-08 (session 12b) — level of play + loader + icon polish (deployed)
- Level of play per TEAM (rec | middle_school | high_school | club |
  college): rally.LEVEL_PROFILES — `err` multiplies every unforced-error
  probability for BOTH sides, `dig` shifts kill/dig balance, so rec ball is
  mistake-decided and college ball earned. teams.level column + migration;
  wizard now 4 steps (level cards are step 3); Level select on Simulate
  controls (PUT /teams/{id}/level; GET /levels is public). Player side:
  level_band accepts 'college' (backend LEVEL_BANDS + onboarding/profile
  selects) — level_band already feeds the player coach-chat context.
- Loader.jsx: "volleyball being set" animation (line-art ball floats off
  cupped hands, CSS keyframes vb-set/vb-flick) — used on app load, watch
  setup, batch analysis, wizard finish.
- Branding: volleyball mark removed from all three headers (Volleyball.jsx
  survives — it's the loader ball + landing icon); landing card emoji →
  brand-pink outline SVGs (new inline Clipboard + Volleyball).
- 62 backend tests green (level scaling test + level endpoints test).
  Verified via Playwright on a FRESH db: signup flowed straight into the
  wizard (already automatic for teamless coaches), level step, sim level
  select showed team's level, loader photographed via a stalled /simulate
  route. Deployed (asset flip + /levels live) + GitHub pushed. Commit 3d85208.

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
