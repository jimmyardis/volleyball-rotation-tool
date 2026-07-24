-- Volleyball Rotation & Lineup Tool — Phase 1 schema.
-- Designed so Phase 2 (stat tracking) and Phase 3 (rally simulator) attach
-- cleanly: every on-court thing references a permanent players.id.

PRAGMA foreign_keys = ON;

-- A team for a given season.
CREATE TABLE IF NOT EXISTS teams (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    season        TEXT,
    -- The coach account that owns this team. NULL only for rows that predate
    -- coach accounts; the first coach to register claims them (db._migrate
    -- adds the column on old databases, coach.register does the claim).
    owner_user_id INTEGER REFERENCES users(id),
    -- Level of play (rally.LEVEL_PROFILES key) — scales unforced errors in
    -- the simulator for BOTH sides. NULL = high_school baseline.
    level         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coach-tagged mistake tendencies, one row per (player, mistake). Keys come
-- from rally.MISTAKE_CATALOG; severity scales how often it bites in sims.
CREATE TABLE IF NOT EXISTS player_mistakes (
    id          INTEGER PRIMARY KEY,
    player_id   INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    mistake_key TEXT NOT NULL,
    severity    TEXT NOT NULL CHECK (severity IN ('sometimes', 'often')),
    UNIQUE (player_id, mistake_key)
);

-- Coach notes: one system, three attachment points. team_id is always set;
-- player_id pins the note to a player card, lineup_id to a lineup. Both NULL
-- means it's a team-notebook entry.
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY,
    team_id    INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id  INTEGER REFERENCES players(id) ON DELETE CASCADE,
    lineup_id  INTEGER REFERENCES lineups(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- The roster. Every player gets a permanent id — this is the anchor that ALL
-- future stats and simulations reference. Never reuse ids.
CREATE TABLE IF NOT EXISTS players (
    id             INTEGER PRIMARY KEY,
    team_id        INTEGER NOT NULL REFERENCES teams(id),
    name           TEXT NOT NULL,
    jersey_number  INTEGER,
    primary_role   TEXT NOT NULL,     -- S, OH, MB, OPP, L, DS
    secondary_role TEXT,              -- optional
    is_libero      INTEGER DEFAULT 0, -- 0/1 boolean
    dominant_hand  TEXT,              -- 'L' / 'R' / NULL. Unused in P1, but the
                                      -- simulator will want it.
    -- Simulation attributes (0-100). Seeded from position presets, editable.
    serving        INTEGER,
    setting        INTEGER,
    defense        INTEGER,
    attacking      INTEGER,
    blocking       INTEGER,
    confidence     INTEGER,           -- chance to go for a ball
    pressure       INTEGER,           -- performance under high-stakes games
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- A named starting configuration (e.g. "5-1 vs tall teams").
CREATE TABLE IF NOT EXISTS lineups (
    id          INTEGER PRIMARY KEY,
    team_id     INTEGER NOT NULL REFERENCES teams(id),
    name        TEXT NOT NULL,
    system      TEXT NOT NULL DEFAULT '5-1',  -- '5-1', '6-2', '4-2'
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- The seed of a lineup: which player STARTS in which zone (1-6).
-- The 6 rotations are COMPUTED from this, not stored.
CREATE TABLE IF NOT EXISTS lineup_positions (
    id          INTEGER PRIMARY KEY,
    lineup_id   INTEGER NOT NULL REFERENCES lineups(id),
    player_id   INTEGER NOT NULL REFERENCES players(id),
    start_zone  INTEGER NOT NULL CHECK (start_zone BETWEEN 1 AND 6),
    UNIQUE (lineup_id, start_zone),   -- one player per zone
    UNIQUE (lineup_id, player_id)     -- a player can't be in two zones
);

-- A saved formation: one (x, y) per player, per rotation, per phase, per
-- lineup. Coordinates are normalized (x left->right, y net->baseline).
--   phase 'receive' — the serve-receive formation (overlap rules apply).
--   phase 'base'    — where players switch to after the serve (free; no overlap).
-- This is where the coach's draggable layouts persist.
CREATE TABLE IF NOT EXISTS formations (
    id              INTEGER PRIMARY KEY,
    lineup_id       INTEGER NOT NULL REFERENCES lineups(id),
    rotation_index  INTEGER NOT NULL CHECK (rotation_index BETWEEN 0 AND 5),
    phase           TEXT NOT NULL CHECK (phase IN ('receive', 'base')),
    player_id       INTEGER NOT NULL REFERENCES players(id),
    x               REAL NOT NULL,
    y               REAL NOT NULL,
    UNIQUE (lineup_id, rotation_index, phase, player_id)
);

-- Per-rotation substitutions: for a given rotation, a starter's slot can be
-- played by someone off the bench (or the libero). starter_id is the rostered
-- starter whose zone it is; on_court_id is who actually plays it this rotation.
CREATE TABLE IF NOT EXISTS substitutions (
    id              INTEGER PRIMARY KEY,
    lineup_id       INTEGER NOT NULL REFERENCES lineups(id),
    rotation_index  INTEGER NOT NULL CHECK (rotation_index BETWEEN 0 AND 5),
    starter_id      INTEGER NOT NULL REFERENCES players(id),
    on_court_id     INTEGER NOT NULL REFERENCES players(id),
    UNIQUE (lineup_id, rotation_index, starter_id)
);

-- Per-lineup court-coverage type for a player: how much of the court they play.
--   'all'   — all-around, plays all 6 rotations (never auto-subbed).
--   'front' — front-row specialist, on only when in the front row.
--   'back'  — back-row specialist (DS / libero), on only when in the back row.
-- Coverage is per-lineup because the same player can be used differently.
CREATE TABLE IF NOT EXISTS lineup_player_meta (
    id          INTEGER PRIMARY KEY,
    lineup_id   INTEGER NOT NULL REFERENCES lineups(id),
    player_id   INTEGER NOT NULL REFERENCES players(id),
    coverage    TEXT NOT NULL DEFAULT 'all' CHECK (coverage IN ('all', 'front', 'back')),
    UNIQUE (lineup_id, player_id)
);

-- Per-lineup substitution pairing: a front-row specialist and a back-row
-- partner who SHARE one rotational slot. Whoever matches the slot's current
-- row is on court. One of the pair must be a starter (the slot owner).
CREATE TABLE IF NOT EXISTS sub_pairs (
    id              INTEGER PRIMARY KEY,
    lineup_id       INTEGER NOT NULL REFERENCES lineups(id),
    front_player_id INTEGER NOT NULL REFERENCES players(id),
    back_player_id  INTEGER NOT NULL REFERENCES players(id),
    UNIQUE (lineup_id, front_player_id),
    UNIQUE (lineup_id, back_player_id)
);

-- Optional in P1: records a libero swapping in for a back-row player.
CREATE TABLE IF NOT EXISTS libero_replacements (
    id              INTEGER PRIMARY KEY,
    lineup_id       INTEGER NOT NULL REFERENCES lineups(id),
    libero_id       INTEGER NOT NULL REFERENCES players(id),
    replaces_id     INTEGER NOT NULL REFERENCES players(id)
);

-- ============================================================ player side
-- The player-facing companion app (spec: player-side-spec.md). One backend,
-- one database; players are USER accounts, optionally linkable to a roster
-- players.id later (CoachLink deferred past MVP).

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name  TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'player' CHECK (role IN ('player', 'coach')),
    password_hash TEXT NOT NULL,     -- pbkdf2-sha256, format: salt$hexdigest
    theme         TEXT NOT NULL DEFAULT 'classic',  -- coach-side look (players use player_profiles.theme)
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    token       TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_profiles (
    id                 INTEGER PRIMARY KEY,
    user_id            INTEGER NOT NULL UNIQUE REFERENCES users(id),
    position           TEXT CHECK (position IN ('S','OH','MB','OPP','L','DS')),
    secondary_position TEXT,
    level_band         TEXT DEFAULT 'high_school',  -- rec|club|middle_school|high_school
    theme              TEXT NOT NULL DEFAULT 'classic',  -- app look: classic|intense|sky (per account)
    coach_memory       TEXT,                             -- what the player told Coach about themselves
    roster_player_id   INTEGER REFERENCES players(id),  -- optional coach-app link
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- The 8-skill taxonomy (6 fundamentals + movement + game IQ). Seeded in code.
CREATE TABLE IF NOT EXISTS skills (
    id    INTEGER PRIMARY KEY,
    key   TEXT NOT NULL UNIQUE,
    name  TEXT NOT NULL,
    sort  INTEGER NOT NULL DEFAULT 0
);

-- Timestamped, re-takeable assessments: levels 1-5
-- (Foundation / Developing / Proficient / Advanced / Mastery).
CREATE TABLE IF NOT EXISTS skill_assessments (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    skill_key   TEXT NOT NULL,
    level       INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5),
    source      TEXT NOT NULL DEFAULT 'self' CHECK (source IN ('self','coach','video')),
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plans (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    position    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived')),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mastery-gated blocks: 'locked' -> 'active' -> 'done'. One active at a time.
CREATE TABLE IF NOT EXISTS plan_blocks (
    id               INTEGER PRIMARY KEY,
    plan_id          INTEGER NOT NULL REFERENCES plans(id),
    block_order      INTEGER NOT NULL,
    skill_key        TEXT NOT NULL,
    title            TEXT NOT NULL,
    level_target     INTEGER NOT NULL,
    success_criteria TEXT NOT NULL,
    drill_keys       TEXT NOT NULL DEFAULT '[]',   -- JSON list of drills.key
    status           TEXT NOT NULL DEFAULT 'locked' CHECK (status IN ('locked','active','done'))
);

CREATE TABLE IF NOT EXISTS plan_checkpoints (
    id           INTEGER PRIMARY KEY,
    block_id     INTEGER NOT NULL REFERENCES plan_blocks(id),
    cp_order     INTEGER NOT NULL,
    text         TEXT NOT NULL,
    done         INTEGER NOT NULL DEFAULT 0
);

-- Drill library (seeded from knowledge.py; coach-pushed drills come later).
CREATE TABLE IF NOT EXISTS drills (
    id         INTEGER PRIMARY KEY,
    key        TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    skill_key  TEXT NOT NULL,
    positions  TEXT NOT NULL DEFAULT 'all',  -- 'all' or CSV of position codes
    level      INTEGER NOT NULL DEFAULT 1,   -- 1-5 entry level
    equipment  TEXT NOT NULL DEFAULT 'ball',
    solo       INTEGER NOT NULL DEFAULT 1,   -- 1 = can do alone
    how_to     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS training_logs (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    log_date    TEXT NOT NULL,               -- YYYY-MM-DD
    skills      TEXT NOT NULL DEFAULT '[]',  -- JSON list of skill keys
    drill_keys  TEXT NOT NULL DEFAULT '[]',  -- JSON list of drills.key
    quality     INTEGER CHECK (quality BETWEEN 1 AND 5),
    minutes     INTEGER,
    notes       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Film Room: one row per submitted video assessment. No video or frames are
-- ever stored — only the structured feedback (and, for serves, the pose
-- metrics computed from browser-side MediaPipe landmarks).
CREATE TABLE IF NOT EXISTS video_assessments (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    skill_key   TEXT NOT NULL,
    metrics     TEXT,                        -- JSON pose metrics (serve) or NULL
    feedback    TEXT NOT NULL,               -- JSON structured coach feedback
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
