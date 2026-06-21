-- Volleyball Rotation & Lineup Tool — Phase 1 schema.
-- Designed so Phase 2 (stat tracking) and Phase 3 (rally simulator) attach
-- cleanly: every on-court thing references a permanent players.id.

PRAGMA foreign_keys = ON;

-- A team for a given season.
CREATE TABLE IF NOT EXISTS teams (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    season      TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
