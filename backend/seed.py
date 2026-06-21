"""Load one sample team + a full 5-1 lineup so you can click around immediately.

Run from the backend/ dir:  python seed.py
Idempotent-ish: it always appends a fresh team, so re-running just adds another.
"""

from pathlib import Path

from app import db

DB_PATH = Path(__file__).resolve().parent / "volleyball.db"

# (name, jersey, role, start_zone) for a textbook 5-1 with the setter in zone 1.
ROSTER = [
    ("Avery", 1, "S", 1),    # setter, back row -> 3 front attackers in R1
    ("Blake", 8, "OPP", 2),
    ("Casey", 12, "MB", 3),
    ("Devon", 5, "OH", 4),
    ("Emery", 9, "OH", 5),
    ("Frankie", 15, "MB", 6),
]


def main() -> None:
    conn = db.connect(DB_PATH)
    db.init_db(conn)

    team = db.create_team(conn, "Sample HS Varsity", "2026")
    positions = {}
    for name, num, role, zone in ROSTER:
        p = db.create_player(conn, team["id"], name, role, jersey_number=num)
        positions[zone] = p["id"]

    # a libero on the bench, to exercise the roster > 6 case
    db.create_player(conn, team["id"], "Gray", "L", jersey_number=2, is_libero=True)

    lineup = db.create_lineup(conn, team["id"], "Base 5-1", "5-1")
    db.set_lineup_positions(conn, lineup["id"], positions)

    print(f"Seeded team {team['id']} '{team['name']}' with lineup {lineup['id']} 'Base 5-1'.")
    print("Start the API and open the frontend to view rotations.")
    conn.close()


if __name__ == "__main__":
    main()
