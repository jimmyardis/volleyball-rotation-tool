"""SQLite persistence layer.

Thin repository functions over the schema in schema.sql. Returns plain dicts
so the API layer can hand them straight to Pydantic / JSON. Standard SQL only,
so the eventual swap to Postgres is mechanical.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from . import engine

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "volleyball.db"

VALID_ROLES = {"S", "OH", "MB", "OPP", "L", "DS"}
VALID_SYSTEMS = {"5-1", "6-2", "4-2"}


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection with foreign keys on and row access by column name.

    check_same_thread=False: FastAPI may run a sync dependency's setup and
    teardown in different threadpool threads, which intermittently 500'd every
    endpoint. Each request still gets its own connection, so there is no
    concurrent cross-thread use.
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def resolve_db_path() -> Path:
    """The one place the DB location is decided (env override for Railway)."""
    import os
    return Path(os.getenv("VB_DB_PATH") or DEFAULT_DB_PATH)


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables (idempotent) and run lightweight migrations."""
    conn.executescript(SCHEMA_PATH.read_text())
    _migrate(conn)
    _seed_player_content(conn)
    conn.commit()


def _seed_player_content(conn: sqlite3.Connection) -> None:
    """Seed the player-side skill taxonomy + drill library (idempotent).
    Re-running updates drill text in place so knowledge.py stays the source
    of truth."""
    from . import knowledge

    for i, s in enumerate(knowledge.SKILLS):
        conn.execute(
            "INSERT INTO skills (key, name, sort) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET name = excluded.name, sort = excluded.sort",
            (s["key"], s["name"], i),
        )
    for d in knowledge.DRILLS:
        conn.execute(
            "INSERT INTO drills (key, name, skill_key, positions, level, equipment, solo, how_to) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET name = excluded.name, skill_key = excluded.skill_key, "
            "positions = excluded.positions, level = excluded.level, equipment = excluded.equipment, "
            "solo = excluded.solo, how_to = excluded.how_to",
            (d["key"], d["name"], d["skill_key"], d["positions"], d["level"], d["equipment"], d["solo"], d["how_to"]),
        )


def _migrate(conn: sqlite3.Connection) -> None:
    """Fold legacy tables into the current shape, preserving data."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    # receive_formations -> formations(phase='receive')
    if "receive_formations" in tables:
        conn.execute(
            "INSERT OR IGNORE INTO formations "
            "(lineup_id, rotation_index, phase, player_id, x, y) "
            "SELECT lineup_id, rotation_index, 'receive', player_id, x, y "
            "FROM receive_formations"
        )
        conn.execute("DROP TABLE receive_formations")

    # player accounts gained a per-account look (theme follows the login,
    # not the device).
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "player_profiles" in tables:
        pp_cols = {r[1] for r in conn.execute("PRAGMA table_info(player_profiles)")}
        if "theme" not in pp_cols:
            conn.execute("ALTER TABLE player_profiles ADD COLUMN theme TEXT NOT NULL DEFAULT 'classic'")
        if "coach_memory" not in pp_cols:
            conn.execute("ALTER TABLE player_profiles ADD COLUMN coach_memory TEXT")
    if "users" in tables:
        u_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        if "theme" not in u_cols:
            conn.execute("ALTER TABLE users ADD COLUMN theme TEXT NOT NULL DEFAULT 'classic'")

    # teams gained an owning coach account (NULL = pre-auth row, claimed by
    # the first coach to register — see coach.register).
    team_cols = {r[1] for r in conn.execute("PRAGMA table_info(teams)")}
    if "owner_user_id" not in team_cols:
        conn.execute("ALTER TABLE teams ADD COLUMN owner_user_id INTEGER REFERENCES users(id)")
    if "level" not in team_cols:
        conn.execute("ALTER TABLE teams ADD COLUMN level TEXT")

    # add simulation attribute columns to older players tables, backfilling
    # existing rows from their position preset.
    cols = {r[1] for r in conn.execute("PRAGMA table_info(players)")}
    added = [a for a in engine.ATTRS if a not in cols]
    for a in added:
        conn.execute(f"ALTER TABLE players ADD COLUMN {a} INTEGER")
    # backfill any NULL attributes (covers both new columns and fresh inserts)
    sel = ", ".join(engine.ATTRS)
    for row in conn.execute(f"SELECT id, primary_role, {sel} FROM players").fetchall():
        preset = engine.preset_for(row["primary_role"])
        updates = {a: preset[a] for a in engine.ATTRS if row[a] is None}
        if updates:
            conn.execute(
                "UPDATE players SET " + ", ".join(f"{a} = ?" for a in updates) + " WHERE id = ?",
                (*updates.values(), row["id"]),
            )


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


# ---------------------------------------------------------------- teams

def create_team(conn: sqlite3.Connection, name: str, season: str | None = None,
                owner_user_id: int | None = None, level: str | None = None) -> dict:
    cur = conn.execute(
        "INSERT INTO teams (name, season, owner_user_id, level) VALUES (?, ?, ?, ?)",
        (name, season, owner_user_id, level),
    )
    conn.commit()
    return get_team(conn, cur.lastrowid)


def set_team_level(conn: sqlite3.Connection, team_id: int, level: str | None) -> dict | None:
    conn.execute("UPDATE teams SET level = ? WHERE id = ?", (level, team_id))
    conn.commit()
    return get_team(conn, team_id)


def get_team(conn: sqlite3.Connection, team_id: int) -> dict | None:
    return _row_to_dict(conn.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone())


def list_teams(conn: sqlite3.Connection, owner_user_id: int | None = None) -> list[dict]:
    if owner_user_id is not None:
        rows = conn.execute(
            "SELECT * FROM teams WHERE owner_user_id = ? ORDER BY created_at DESC, id DESC",
            (owner_user_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM teams ORDER BY created_at DESC, id DESC").fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- players

def create_player(
    conn: sqlite3.Connection,
    team_id: int,
    name: str,
    primary_role: str,
    jersey_number: int | None = None,
    secondary_role: str | None = None,
    is_libero: bool = False,
    dominant_hand: str | None = None,
    attributes: dict | None = None,
) -> dict:
    if primary_role not in VALID_ROLES:
        raise ValueError(f"Invalid primary_role {primary_role!r}; must be one of {sorted(VALID_ROLES)}")
    # seed attributes from the position preset, overridden by any provided
    attrs = engine.preset_for(primary_role)
    if attributes:
        attrs.update({a: attributes[a] for a in engine.ATTRS if a in attributes and attributes[a] is not None})
    cur = conn.execute(
        f"""INSERT INTO players
           (team_id, name, jersey_number, primary_role, secondary_role, is_libero,
            dominant_hand, {", ".join(engine.ATTRS)})
           VALUES (?, ?, ?, ?, ?, ?, ?, {", ".join("?" for _ in engine.ATTRS)})""",
        (team_id, name, jersey_number, primary_role, secondary_role, int(is_libero),
         dominant_hand, *(attrs[a] for a in engine.ATTRS)),
    )
    conn.commit()
    return get_player(conn, cur.lastrowid)


def get_player(conn: sqlite3.Connection, player_id: int) -> dict | None:
    return _row_to_dict(conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone())


def list_players(conn: sqlite3.Connection, team_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM players WHERE team_id = ? ORDER BY jersey_number IS NULL, jersey_number, id",
        (team_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_player(conn: sqlite3.Connection, player_id: int, **fields) -> dict | None:
    allowed = {
        "name", "jersey_number", "primary_role", "secondary_role",
        "is_libero", "dominant_hand", *engine.ATTRS,
    }
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if "primary_role" in updates and updates["primary_role"] not in VALID_ROLES:
        raise ValueError(f"Invalid primary_role {updates['primary_role']!r}")
    if "is_libero" in updates:
        updates["is_libero"] = int(bool(updates["is_libero"]))
    if not updates:
        return get_player(conn, player_id)
    cols = ", ".join(f"{k} = ?" for k in updates)
    conn.execute(f"UPDATE players SET {cols} WHERE id = ?", (*updates.values(), player_id))
    conn.commit()
    return get_player(conn, player_id)


def delete_player(conn: sqlite3.Connection, player_id: int) -> None:
    conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
    conn.commit()


# ---------------------------------------------------------------- lineups

def create_lineup(
    conn: sqlite3.Connection,
    team_id: int,
    name: str,
    system: str = "5-1",
    notes: str | None = None,
) -> dict:
    if system not in VALID_SYSTEMS:
        raise ValueError(f"Invalid system {system!r}; must be one of {sorted(VALID_SYSTEMS)}")
    cur = conn.execute(
        "INSERT INTO lineups (team_id, name, system, notes) VALUES (?, ?, ?, ?)",
        (team_id, name, system, notes),
    )
    conn.commit()
    return get_lineup(conn, cur.lastrowid)


def get_lineup(conn: sqlite3.Connection, lineup_id: int) -> dict | None:
    return _row_to_dict(conn.execute("SELECT * FROM lineups WHERE id = ?", (lineup_id,)).fetchone())


def list_lineups(conn: sqlite3.Connection, team_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM lineups WHERE team_id = ? ORDER BY created_at DESC, id DESC",
        (team_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def delete_lineup(conn: sqlite3.Connection, lineup_id: int) -> None:
    conn.execute("DELETE FROM lineup_positions WHERE lineup_id = ?", (lineup_id,))
    conn.execute("DELETE FROM libero_replacements WHERE lineup_id = ?", (lineup_id,))
    conn.execute("DELETE FROM lineups WHERE id = ?", (lineup_id,))
    conn.commit()


def set_lineup_positions(
    conn: sqlite3.Connection,
    lineup_id: int,
    positions: dict[int, int],
) -> None:
    """Replace the starting positions for a lineup.

    `positions` maps start_zone (1..6) -> player_id. Validated to be a full,
    distinct 6-zone assignment, then written atomically.
    """
    zones = set(positions.keys())
    if zones != set(range(1, 7)):
        raise ValueError(f"positions must cover zones 1..6 exactly; got {sorted(zones)}")
    if len(set(positions.values())) != 6:
        raise ValueError("each zone must hold a distinct player")
    with conn:  # transaction
        conn.execute("DELETE FROM lineup_positions WHERE lineup_id = ?", (lineup_id,))
        conn.executemany(
            "INSERT INTO lineup_positions (lineup_id, player_id, start_zone) VALUES (?, ?, ?)",
            [(lineup_id, pid, zone) for zone, pid in positions.items()],
        )


def get_lineup_positions(conn: sqlite3.Connection, lineup_id: int) -> dict[int, int]:
    """Return {start_zone: player_id} for a lineup (may be empty if unset)."""
    rows = conn.execute(
        "SELECT start_zone, player_id FROM lineup_positions WHERE lineup_id = ?",
        (lineup_id,),
    ).fetchall()
    return {r["start_zone"]: r["player_id"] for r in rows}


# ---------------------------------------------------------------- formations

VALID_PHASES = {"receive", "base"}


def get_formation(
    conn: sqlite3.Connection, lineup_id: int, rotation_index: int, phase: str
) -> dict[int, tuple[float, float]]:
    """Return {player_id: (x, y)} for a saved formation (empty if none)."""
    rows = conn.execute(
        "SELECT player_id, x, y FROM formations "
        "WHERE lineup_id = ? AND rotation_index = ? AND phase = ?",
        (lineup_id, rotation_index, phase),
    ).fetchall()
    return {r["player_id"]: (r["x"], r["y"]) for r in rows}


def set_formation(
    conn: sqlite3.Connection,
    lineup_id: int,
    rotation_index: int,
    phase: str,
    placements: dict[int, tuple[float, float]],
) -> None:
    """Replace the saved formation for one rotation + phase with `placements`."""
    if not 0 <= rotation_index <= 5:
        raise ValueError("rotation_index must be 0..5")
    if phase not in VALID_PHASES:
        raise ValueError(f"phase must be one of {sorted(VALID_PHASES)}")
    with conn:  # transaction
        conn.execute(
            "DELETE FROM formations WHERE lineup_id = ? AND rotation_index = ? AND phase = ?",
            (lineup_id, rotation_index, phase),
        )
        conn.executemany(
            "INSERT INTO formations (lineup_id, rotation_index, phase, player_id, x, y) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(lineup_id, rotation_index, phase, pid, xy[0], xy[1]) for pid, xy in placements.items()],
        )


# ---------------------------------------------------------------- substitutions

def get_substitutions(
    conn: sqlite3.Connection, lineup_id: int, rotation_index: int
) -> dict[int, int]:
    """Return {starter_id: on_court_id} swaps for one rotation (empty if none)."""
    rows = conn.execute(
        "SELECT starter_id, on_court_id FROM substitutions "
        "WHERE lineup_id = ? AND rotation_index = ?",
        (lineup_id, rotation_index),
    ).fetchall()
    return {r["starter_id"]: r["on_court_id"] for r in rows}


def set_substitutions(
    conn: sqlite3.Connection,
    lineup_id: int,
    rotation_index: int,
    swaps: dict[int, int],
) -> None:
    """Replace all swaps for one rotation. No-op swaps (starter==on_court) are
    dropped so the table only holds real substitutions."""
    if not 0 <= rotation_index <= 5:
        raise ValueError("rotation_index must be 0..5")
    real = {s: o for s, o in swaps.items() if s != o}
    with conn:  # transaction
        conn.execute(
            "DELETE FROM substitutions WHERE lineup_id = ? AND rotation_index = ?",
            (lineup_id, rotation_index),
        )
        conn.executemany(
            "INSERT INTO substitutions (lineup_id, rotation_index, starter_id, on_court_id) "
            "VALUES (?, ?, ?, ?)",
            [(lineup_id, rotation_index, s, o) for s, o in real.items()],
        )


# ---------------------------------------------------------------- coverage & pairs

VALID_COVERAGE = {"all", "front", "back"}


def get_coverage(conn: sqlite3.Connection, lineup_id: int) -> dict[int, str]:
    """Return {player_id: coverage} for a lineup (only explicitly-set rows)."""
    rows = conn.execute(
        "SELECT player_id, coverage FROM lineup_player_meta WHERE lineup_id = ?",
        (lineup_id,),
    ).fetchall()
    return {r["player_id"]: r["coverage"] for r in rows}


def set_coverage(conn: sqlite3.Connection, lineup_id: int, coverage: dict[int, str]) -> None:
    """Upsert coverage types for players in a lineup."""
    for cov in coverage.values():
        if cov not in VALID_COVERAGE:
            raise ValueError(f"coverage must be one of {sorted(VALID_COVERAGE)}")
    with conn:
        for pid, cov in coverage.items():
            conn.execute(
                "INSERT INTO lineup_player_meta (lineup_id, player_id, coverage) VALUES (?, ?, ?) "
                "ON CONFLICT (lineup_id, player_id) DO UPDATE SET coverage = excluded.coverage",
                (lineup_id, pid, cov),
            )


def get_pairs(conn: sqlite3.Connection, lineup_id: int) -> list[dict]:
    """Return [{id, front_player_id, back_player_id}] for a lineup."""
    rows = conn.execute(
        "SELECT id, front_player_id, back_player_id FROM sub_pairs WHERE lineup_id = ?",
        (lineup_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def set_pairs(conn: sqlite3.Connection, lineup_id: int, pairs: list[tuple[int, int]]) -> None:
    """Replace all pairings for a lineup with `pairs` (front_id, back_id)."""
    seen: set[int] = set()
    for front_id, back_id in pairs:
        if front_id == back_id:
            raise ValueError("a player cannot be paired with themselves")
        if front_id in seen or back_id in seen:
            raise ValueError("each player can be in at most one pairing")
        seen.update((front_id, back_id))
    with conn:
        conn.execute("DELETE FROM sub_pairs WHERE lineup_id = ?", (lineup_id,))
        conn.executemany(
            "INSERT INTO sub_pairs (lineup_id, front_player_id, back_player_id) VALUES (?, ?, ?)",
            [(lineup_id, f, b) for f, b in pairs],
        )


# ---------------------------------------------------------------- libero swaps

def set_libero_replacement(
    conn: sqlite3.Connection, lineup_id: int, libero_id: int, replaces_id: int
) -> dict:
    cur = conn.execute(
        "INSERT INTO libero_replacements (lineup_id, libero_id, replaces_id) VALUES (?, ?, ?)",
        (lineup_id, libero_id, replaces_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM libero_replacements WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return dict(row)


def list_libero_replacements(conn: sqlite3.Connection, lineup_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM libero_replacements WHERE lineup_id = ?", (lineup_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def clear_libero_replacements(conn: sqlite3.Connection, lineup_id: int) -> None:
    conn.execute("DELETE FROM libero_replacements WHERE lineup_id = ?", (lineup_id,))
    conn.commit()


# ---------------------------------------------------------------- mistakes

def get_player_mistakes(conn: sqlite3.Connection, player_id: int) -> dict[str, str]:
    rows = conn.execute(
        "SELECT mistake_key, severity FROM player_mistakes WHERE player_id = ?",
        (player_id,),
    ).fetchall()
    return {r["mistake_key"]: r["severity"] for r in rows}


def set_player_mistakes(conn: sqlite3.Connection, player_id: int,
                        mistakes: dict[str, str]) -> None:
    """Replace the player's full mistake set (empty dict clears it)."""
    conn.execute("DELETE FROM player_mistakes WHERE player_id = ?", (player_id,))
    for key, severity in mistakes.items():
        conn.execute(
            "INSERT INTO player_mistakes (player_id, mistake_key, severity) VALUES (?, ?, ?)",
            (player_id, key, severity),
        )
    conn.commit()


def team_mistakes(conn: sqlite3.Connection, team_id: int) -> dict[int, dict[str, str]]:
    """{player_id: {mistake_key: severity}} for a whole roster — sim input."""
    rows = conn.execute(
        "SELECT pm.player_id, pm.mistake_key, pm.severity FROM player_mistakes pm "
        "JOIN players p ON p.id = pm.player_id WHERE p.team_id = ?",
        (team_id,),
    ).fetchall()
    out: dict[int, dict[str, str]] = {}
    for r in rows:
        out.setdefault(r["player_id"], {})[r["mistake_key"]] = r["severity"]
    return out


# ---------------------------------------------------------------- notes

def list_notes(conn: sqlite3.Connection, team_id: int,
               player_id: int | None = None, lineup_id: int | None = None,
               notebook_only: bool = False) -> list[dict]:
    q = "SELECT * FROM notes WHERE team_id = ?"
    args: list = [team_id]
    if player_id is not None:
        q += " AND player_id = ?"
        args.append(player_id)
    if lineup_id is not None:
        q += " AND lineup_id = ?"
        args.append(lineup_id)
    if notebook_only:
        q += " AND player_id IS NULL AND lineup_id IS NULL"
    q += " ORDER BY created_at DESC, id DESC"
    return [dict(r) for r in conn.execute(q, args).fetchall()]


def create_note(conn: sqlite3.Connection, team_id: int, body: str,
                player_id: int | None = None, lineup_id: int | None = None) -> dict:
    cur = conn.execute(
        "INSERT INTO notes (team_id, player_id, lineup_id, body) VALUES (?, ?, ?, ?)",
        (team_id, player_id, lineup_id, body),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone())


def update_note(conn: sqlite3.Connection, note_id: int, body: str) -> dict | None:
    conn.execute("UPDATE notes SET body = ? WHERE id = ?", (body, note_id))
    conn.commit()
    return _row_to_dict(conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone())


def delete_note(conn: sqlite3.Connection, note_id: int) -> None:
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
