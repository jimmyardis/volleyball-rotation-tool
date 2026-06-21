"""DB layer tests — uses an in-memory SQLite so nothing touches disk."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402


@pytest.fixture()
def conn():
    c = db.connect(":memory:")
    db.init_db(c)
    yield c
    c.close()


def _full_roster(conn, team_id):
    roles = ["S", "OPP", "MB", "OH", "OH", "MB"]
    return [
        db.create_player(conn, team_id, f"P{i}", role, jersey_number=i)
        for i, role in enumerate(roles, start=1)
    ]


def test_create_team_and_player_get_stable_ids(conn):
    team = db.create_team(conn, "Eagles", "2026")
    p = db.create_player(conn, team["id"], "Avery", "S", jersey_number=7)
    assert p["id"] >= 1
    assert p["team_id"] == team["id"]
    assert p["primary_role"] == "S"
    # id is stable across reads
    assert db.get_player(conn, p["id"])["id"] == p["id"]


def test_invalid_role_rejected(conn):
    team = db.create_team(conn, "Eagles")
    with pytest.raises(ValueError):
        db.create_player(conn, team["id"], "X", "QB")


def test_set_and_get_lineup_positions(conn):
    team = db.create_team(conn, "Eagles")
    players = _full_roster(conn, team["id"])
    lineup = db.create_lineup(conn, team["id"], "Base 5-1", "5-1")
    positions = {zone: players[zone - 1]["id"] for zone in range(1, 7)}
    db.set_lineup_positions(conn, lineup["id"], positions)
    assert db.get_lineup_positions(conn, lineup["id"]) == positions


def test_lineup_positions_require_all_six_zones(conn):
    team = db.create_team(conn, "Eagles")
    players = _full_roster(conn, team["id"])
    lineup = db.create_lineup(conn, team["id"], "Partial", "5-1")
    with pytest.raises(ValueError):
        db.set_lineup_positions(conn, lineup["id"], {1: players[0]["id"]})


def test_lineup_positions_reject_duplicate_player(conn):
    team = db.create_team(conn, "Eagles")
    players = _full_roster(conn, team["id"])
    lineup = db.create_lineup(conn, team["id"], "Dup", "5-1")
    positions = {zone: players[0]["id"] for zone in range(1, 7)}  # same player everywhere
    with pytest.raises(ValueError):
        db.set_lineup_positions(conn, lineup["id"], positions)


def test_set_positions_is_idempotent_replace(conn):
    team = db.create_team(conn, "Eagles")
    players = _full_roster(conn, team["id"])
    lineup = db.create_lineup(conn, team["id"], "Base", "5-1")
    p1 = {zone: players[zone - 1]["id"] for zone in range(1, 7)}
    db.set_lineup_positions(conn, lineup["id"], p1)
    # reversed assignment
    p2 = {zone: players[6 - zone]["id"] for zone in range(1, 7)}
    db.set_lineup_positions(conn, lineup["id"], p2)
    assert db.get_lineup_positions(conn, lineup["id"]) == p2


def test_update_and_delete_player(conn):
    team = db.create_team(conn, "Eagles")
    p = db.create_player(conn, team["id"], "Sam", "OH", jersey_number=3)
    updated = db.update_player(conn, p["id"], jersey_number=12, is_libero=True)
    assert updated["jersey_number"] == 12
    assert updated["is_libero"] == 1
    db.delete_player(conn, p["id"])
    assert db.get_player(conn, p["id"]) is None


def test_libero_replacement_roundtrip(conn):
    team = db.create_team(conn, "Eagles")
    players = _full_roster(conn, team["id"])
    libero = db.create_player(conn, team["id"], "Libby", "L", is_libero=True)
    lineup = db.create_lineup(conn, team["id"], "Base", "5-1")
    rep = db.set_libero_replacement(conn, lineup["id"], libero["id"], players[2]["id"])
    assert rep["libero_id"] == libero["id"]
    assert len(db.list_libero_replacements(conn, lineup["id"])) == 1
