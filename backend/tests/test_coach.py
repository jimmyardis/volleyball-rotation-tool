"""Coach accounts, the API gate, mistakes, notes, and the sim endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VB_DB_PATH", str(tmp_path / "test.db"))
    from app import db, main
    monkeypatch.setattr(main, "DB_PATH", db.resolve_db_path())
    conn = db.connect(db.resolve_db_path())
    db.init_db(conn)
    # a pre-auth team, as if it predates coach accounts
    db.create_team(conn, "Legacy HS", "2026")
    conn.close()
    return TestClient(main.app)


@pytest.fixture()
def coach(client):
    r = client.post("/coach/register", json={
        "username": "coachjay", "password": "sideout1", "display_name": "Coach Jay"})
    assert r.status_code == 200, r.text
    data = r.json()
    return {"Authorization": f"Bearer {data['token']}"}, data


def seed_team(client, hdrs):
    team = client.post("/teams", json={"name": "Test 14U"}, headers=hdrs).json()
    roster = [("Ava", "S", 1), ("Bee", "OH", 2), ("Cat", "MB", 3),
              ("Dee", "OPP", 4), ("Eve", "OH", 5), ("Fay", "MB", 6)]
    ids = {}
    for name, role, jersey in roster:
        p = client.post(f"/teams/{team['id']}/players", headers=hdrs,
                        json={"name": name, "primary_role": role, "jersey_number": jersey}).json()
        ids[name] = p["id"]
    lu = client.post(f"/teams/{team['id']}/lineups", headers=hdrs,
                     json={"name": "Base", "system": "5-1"}).json()
    positions = {str(z): ids[n] for z, n in
                 zip(range(1, 7), ["Ava", "Bee", "Cat", "Dee", "Eve", "Fay"])}
    r = client.put(f"/lineups/{lu['id']}/positions", headers=hdrs,
                   json={"positions": positions})
    assert r.status_code == 200, r.text
    return team, ids, lu


def test_gate_blocks_anonymous_and_players(client):
    assert client.get("/teams").status_code == 401
    # a PLAYER token must not open the coach tool
    p = client.post("/player/register", json={"username": "kid", "password": "spike123"})
    ph = {"Authorization": f"Bearer {p.json()['token']}"}
    assert client.get("/teams", headers=ph).status_code == 401
    # health + player + coach auth endpoints stay open
    assert client.get("/health").status_code == 200


def test_first_coach_claims_legacy_teams(client, coach):
    hdrs, data = coach
    assert data["claimed_teams"] == 1
    teams = client.get("/teams", headers=hdrs).json()
    assert any(t["name"] == "Legacy HS" for t in teams)
    # a SECOND coach claims nothing and sees no one else's teams
    r2 = client.post("/coach/register", json={"username": "rival", "password": "blocked1"})
    assert r2.json()["claimed_teams"] == 0
    h2 = {"Authorization": f"Bearer {r2.json()['token']}"}
    assert client.get("/teams", headers=h2).json() == []


def test_coach_login_rejects_player_creds(client):
    client.post("/player/register", json={"username": "justakid", "password": "spike123"})
    r = client.post("/coach/login", json={"username": "justakid", "password": "spike123"})
    assert r.status_code == 401


def test_mistakes_roundtrip(client, coach):
    hdrs, _ = coach
    team, ids, _ = seed_team(client, hdrs)
    cat = client.get("/mistake-catalog", headers=hdrs).json()
    assert any(m["key"] == "serve_net" for m in cat["catalog"])

    pid = ids["Bee"]
    r = client.put(f"/players/{pid}/mistakes", headers=hdrs,
                   json={"mistakes": {"serve_net": "often", "shank_pass": "sometimes"}})
    assert r.status_code == 200
    assert client.get(f"/players/{pid}/mistakes", headers=hdrs).json()["mistakes"] == {
        "serve_net": "often", "shank_pass": "sometimes"}
    # unknown keys / severities are rejected
    bad = client.put(f"/players/{pid}/mistakes", headers=hdrs,
                     json={"mistakes": {"nope": "often"}})
    assert bad.status_code == 422


def test_notes_three_attachment_points(client, coach):
    hdrs, _ = coach
    team, ids, lu = seed_team(client, hdrs)
    tid = team["id"]
    nb = client.post(f"/teams/{tid}/notes", headers=hdrs,
                     json={"body": "work serve receive"}).json()
    client.post(f"/teams/{tid}/notes", headers=hdrs,
                json={"body": "toss drifts left", "player_id": ids["Bee"]})
    client.post(f"/teams/{tid}/notes", headers=hdrs,
                json={"body": "use vs zone serving", "lineup_id": lu["id"]})

    assert len(client.get(f"/teams/{tid}/notes", headers=hdrs).json()) == 3
    assert len(client.get(f"/teams/{tid}/notes?notebook=true", headers=hdrs).json()) == 1
    pins = client.get(f"/teams/{tid}/notes?player_id={ids['Bee']}", headers=hdrs).json()
    assert pins[0]["body"] == "toss drifts left"

    upd = client.put(f"/notes/{nb['id']}", headers=hdrs, json={"body": "edited"})
    assert upd.json()["body"] == "edited"
    assert client.delete(f"/notes/{nb['id']}", headers=hdrs).status_code == 204
    assert len(client.get(f"/teams/{tid}/notes", headers=hdrs).json()) == 2


def test_simulate_batch_endpoint(client, coach):
    hdrs, _ = coach
    _, _, lu = seed_team(client, hdrs)
    r = client.post(f"/lineups/{lu['id']}/simulate", headers=hdrs,
                    json={"opponent_skill": 60, "sets": 25})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sets"] == 25
    assert len(body["rotations"]) == 6
    assert body["insights"]
    kinds = {i["kind"] for i in body["insights"]}
    assert {"best", "worst"} <= kinds


def test_simulate_game_endpoint_is_replayable(client, coach):
    hdrs, _ = coach
    _, _, lu = seed_team(client, hdrs)
    a = client.post(f"/lineups/{lu['id']}/simulate-game", headers=hdrs,
                    json={"opponent_skill": 55, "seed": 11}).json()
    b = client.post(f"/lineups/{lu['id']}/simulate-game", headers=hdrs,
                    json={"opponent_skill": 55, "seed": 11}).json()
    assert a["score"] == b["score"]
    kinds = [e["k"] for e in a["events"]]
    assert kinds[0] == "rally_start" and kinds[-1] == "set_end"
    assert a["opp_players"] and all(p["id"] < 0 for p in a["opp_players"])
