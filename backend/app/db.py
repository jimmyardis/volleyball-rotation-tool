"""SQLite persistence layer.

Thin repository functions over the schema in schema.sql. Returns plain dicts
so the API layer can hand them straight to Pydantic / JSON. Standard SQL only,
so the eventual swap to Postgres is mechanical.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "volleyball.db"

VALID_ROLES = {"S", "OH", "MB", "OPP", "L", "DS"}
VALID_SYSTEMS = {"5-1", "6-2", "4-2"}


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection with foreign keys on and row access by column name."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables (idempotent)."""
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


# ---------------------------------------------------------------- teams

def create_team(conn: sqlite3.Connection, name: str, season: str | None = None) -> dict:
    cur = conn.execute(
        "INSERT INTO teams (name, season) VALUES (?, ?)", (name, season)
    )
    conn.commit()
    return get_team(conn, cur.lastrowid)


def get_team(conn: sqlite3.Connection, team_id: int) -> dict | None:
    return _row_to_dict(conn.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone())


def list_teams(conn: sqlite3.Connection) -> list[dict]:
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
) -> dict:
    if primary_role not in VALID_ROLES:
        raise ValueError(f"Invalid primary_role {primary_role!r}; must be one of {sorted(VALID_ROLES)}")
    cur = conn.execute(
        """INSERT INTO players
           (team_id, name, jersey_number, primary_role, secondary_role, is_libero, dominant_hand)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (team_id, name, jersey_number, primary_role, secondary_role, int(is_libero), dominant_hand),
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
        "is_libero", "dominant_hand",
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


# ---------------------------------------------------------------- receive formations

def get_receive_formation(
    conn: sqlite3.Connection, lineup_id: int, rotation_index: int
) -> dict[int, tuple[float, float]]:
    """Return {player_id: (x, y)} for a saved formation (empty if none)."""
    rows = conn.execute(
        "SELECT player_id, x, y FROM receive_formations "
        "WHERE lineup_id = ? AND rotation_index = ?",
        (lineup_id, rotation_index),
    ).fetchall()
    return {r["player_id"]: (r["x"], r["y"]) for r in rows}


def set_receive_formation(
    conn: sqlite3.Connection,
    lineup_id: int,
    rotation_index: int,
    placements: dict[int, tuple[float, float]],
) -> None:
    """Replace the saved formation for one rotation with `placements`."""
    if not 0 <= rotation_index <= 5:
        raise ValueError("rotation_index must be 0..5")
    with conn:  # transaction
        conn.execute(
            "DELETE FROM receive_formations WHERE lineup_id = ? AND rotation_index = ?",
            (lineup_id, rotation_index),
        )
        conn.executemany(
            "INSERT INTO receive_formations (lineup_id, rotation_index, player_id, x, y) "
            "VALUES (?, ?, ?, ?, ?)",
            [(lineup_id, rotation_index, pid, xy[0], xy[1]) for pid, xy in placements.items()],
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
