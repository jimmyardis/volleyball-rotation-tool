# iOS App Handoff — for Claude Code on the MacBook

Read this first. You are picking up the iOS phase of a working, deployed
full-stack volleyball training app. Your job on this machine: wrap the
existing React frontend in Capacitor, polish it into a genuinely great
iPhone experience, and ship it to teammates/coaches via TestFlight, then the
App Store. **Do not rewrite the frontend in React Native** — that decision
is made (single codebase, Capacitor wrap).

## Goal (the user's words)
"The best iPhone app with the best possible user experience" for a youth
volleyball training app, shipped to teammates and coaches. The primary user
is the builder's daughter (middle-school player); she's excited about
outreach and wants to see how far she can take it.

## What already exists (don't rebuild it)
- **Live app**: https://volleyball-api-production.up.railway.app — FastAPI +
  SQLite on Railway serves both the API and the built React SPA (`backend/webdist`).
- **Player Zone** (`frontend/src/player/`, hash-routed at `#player`): Home,
  AI Coach chat, Plan (mastery-gated goals + checklists), Train (79-drill
  library + training log), **Film Room** (video self-assessment), Progress
  (radar), Profile. Coach-side tools live at the root route.
- **Film Room** (`FilmScreen.jsx` + `filmroom.js`): player films one rep;
  the browser samples ~10 JPEG frames via canvas and (for serves) runs
  MediaPipe pose landmarking locally via CDN. Only frames + landmarks are
  uploaded — the raw video never leaves the device. Preserve this privacy
  property in everything you do; it is the app's App-Store-review story.
- **PWA**: manifest + icons already exist; the daughter has it installed.
- Backend tests: `cd backend && ./venv/bin/python -m pytest tests -q`
  (Mac: create a venv from `requirements.txt` if you need to run them —
  but backend work belongs on the WSL machine, see split below).

## Machine split — respect this
- **This Mac owns**: `frontend/`, the new `ios/` Capacitor project, Xcode,
  TestFlight/App Store Connect. Commit and push from here.
- **The WSL machine owns**: `backend/`, the knowledge base, and Railway
  deploys (`railway up` from `backend/` — a git push alone deploys nothing).
  The Railway token intentionally does not exist on this Mac.
- **Sync**: git only. Data syncs never — everything real is in the cloud DB.
- `backend/webdist/` is a build artifact committed by the WSL machine at
  deploy time. If it ever conflicts on merge, take either side and move on —
  it gets rebuilt at the next deploy.

## Known technical landmines (solve these first, in order)
1. **API base URL**: `frontend/src/player/api.js` and `frontend/src/api.js`
   use same-origin relative URLs (`import.meta.env.PROD ? "" : "/api"`).
   Inside Capacitor the origin is `capacitor://localhost`, so relative calls
   will fail. Detect the native shell (`window.Capacitor?.isNativePlatform?.()`)
   and use `https://volleyball-api-production.up.railway.app` as the base.
2. **CORS**: ~~needs allowlisting~~ DONE — verified 2026-07-21: production
   already serves `access-control-allow-origin: *` with all methods/headers
   and the auth gate skips OPTIONS preflights. Native API calls will work
   with no backend change.
3. **Camera permissions**: Film Room uses `<input type="file" accept="video/*">`.
   In the native shell this needs `NSCameraUsageDescription`,
   `NSMicrophoneUsageDescription`, and `NSPhotoLibraryUsageDescription` in
   Info.plist, with youth-appropriate, honest strings ("Your video is
   analyzed on your phone; only still frames are sent for coaching feedback").
4. **MediaPipe**: loads WASM + model from CDN at runtime (`filmroom.js`).
   Works in WKWebView but needs network. It already degrades gracefully
   (no pose → frames-only submission). Later optimization: bundle the model
   locally in the app package.
5. **Auth persistence**: bearer token in localStorage. WKWebView persists it,
   but verify after app restarts; if flaky, move token storage to the
   Capacitor Preferences plugin.
6. **Safe areas / viewport**: test notch/Dynamic Island overlap, the 7-tab
   scrolling nav, and keyboard-over-input behavior in the coach chat.

## Phase plan
**Phase A — wrap and run (first session):**
- `npm i @capacitor/core @capacitor/cli @capacitor/ios` in `frontend/`,
  `npx cap init` (app name is the daughter's call — ask, don't invent;
  bundle id from the family dev account, e.g. reverse-DNS they own),
  `npm run build && npx cap add ios && npx cap sync`.
- Fix landmine #1, open in Xcode, run on simulator + her real phone.
- Success: sign in, chat with the coach, film a serve end-to-end on device.

**Phase B — native-feel UX polish:**
- App icon + splash screen (existing brand: white/#f7f7f8, pink #d6336c,
  Inter font; icons in `frontend/dist/` are the starting point).
- Status bar style, launch experience, haptics on checklist ticks (Capacitor
  Haptics), pull-to-refresh where natural, keyboard handling in chat.
- Camera flow: consider `capture="environment"` so "Choose / record a clip"
  opens the camera directly.
- Real-device Film Room performance pass (MediaPipe on an iPhone).

**Phase C — TestFlight:**
- App Store Connect: create the app record under the existing dev account.
- Archive + upload from Xcode. Internal testers first (her + parents), then
  external TestFlight group for teammates/coaches (external needs a light
  beta review — have the privacy answers ready, see below).

**Phase D — App Store submission (the paperwork phase):**
- **Privacy policy URL** (required): must exist and truthfully describe the
  video-stays-on-device design, what IS stored (accounts, training logs,
  structured feedback), and the AI coach.
- **Account deletion** (required by Apple): DONE 2026-07-21 — `DELETE
  /player/account` (password re-entry as confirmation, cascades all player
  data in one transaction) + a "Delete account" card on the Profile screen.
  Nothing left to build for this requirement; just point at it in review
  notes. (Coach accounts have no deletion yet — fine for TestFlight; add
  before App Store if the coach tools stay in the shipped app.)
- **App Privacy questionnaire**: data linked to user = account info,
  training data. No tracking, no ads — say so.
- **Youth audience**: do NOT opt into the Kids Category (stricter rules);
  it's a sports training tool, rate 4+, but expect reviewer questions about
  AI chat + video in a youth app. The honest answers: chat is grounded in a
  curated coaching corpus with topic guardrails; video is processed
  on-device; nothing is shared between users.

## Working agreements for this Mac's Claude Code
- Follow the ATLAS.md protocol (root of repo): update it at the end of every
  session that changes anything; note iOS status so the WSL machine stays
  oriented. Log Mac-vs-WSL coordination items in ATLAS "Next Action".
- Never commit secrets, provisioning profiles with private keys, or
  `ios/App/Pods/` (gitignore them; commit `Podfile` + `Podfile.lock`).
- The daughter is the product owner: naming, icon, colors, copy are her
  calls — present options, let her pick.

## Mac setup checklist (human tasks, once)
- [ ] Xcode from the App Store (big download) + open once to accept license
      and install iOS platform. `xcode-select --install` for CLI tools.
- [ ] Homebrew, then: `brew install node git gh cocoapods`
- [ ] Claude Code: `npm install -g @anthropic-ai/claude-code` (or desktop app)
- [ ] `gh auth login` as jimmyardis (or add an SSH key to GitHub)
- [ ] `git clone https://github.com/jimmyardis/volleyball-rotation-tool.git`
- [ ] Xcode → Settings → Accounts → sign in with the family Apple
      Developer account
- [ ] In the clone: `cd frontend && npm install`
- [ ] Start Claude Code in the repo root and say: "read HANDOFF-IOS.md and
      start Phase A"
