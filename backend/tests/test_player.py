"""Player-side API tests: auth, assessment, plan gating, logs, progress,
coach-context assembly. NO paid Claude calls — the chat endpoint itself is
never exercised against the API; only its context builder is tested.
"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VB_DB_PATH", str(tmp_path / "test.db"))
    # import late so main.py resolves DB_PATH from the env var
    from app import db, main
    monkeypatch.setattr(main, "DB_PATH", db.resolve_db_path())
    conn = db.connect(db.resolve_db_path())
    db.init_db(conn)
    conn.close()
    return TestClient(main.app)


@pytest.fixture()
def auth(client):
    r = client.post("/player/register", json={"username": "celia", "password": "spike123", "display_name": "Celia"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_login_me(client, auth):
    # duplicate username rejected (case-insensitive)
    dup = client.post("/player/register", json={"username": "CELIA", "password": "whatever"})
    assert dup.status_code == 409

    ok = client.post("/player/login", json={"username": "celia", "password": "spike123"})
    assert ok.status_code == 200
    bad = client.post("/player/login", json={"username": "celia", "password": "nope123"})
    assert bad.status_code == 401

    me = client.get("/player/me", headers=auth).json()
    assert me["user"]["username"] == "celia"
    assert me["has_assessment"] is False
    assert client.get("/player/me").status_code == 401  # no token


def test_assessment_and_progress(client, auth):
    r = client.post("/player/assessment", headers=auth,
                    json={"ratings": {"serve": 2, "passing": 3, "setting": 1}})
    assert r.status_code == 200
    assert r.json()["levels"]["serve"]["level"] == 2

    bad = client.post("/player/assessment", headers=auth, json={"ratings": {"juggling": 3}})
    assert bad.status_code == 422

    prog = client.get("/player/progress", headers=auth).json()
    assert prog["levels"]["passing"]["level"] == 3
    assert len(prog["history"]) == 3


def test_plan_generation_and_mastery_gating(client, auth):
    # plan requires position + assessment
    assert client.post("/player/plan/generate", headers=auth).status_code == 409
    client.put("/player/profile", headers=auth,
               json={"position": "L", "level_band": "club"})
    assert client.post("/player/plan/generate", headers=auth).status_code == 409
    client.post("/player/assessment", headers=auth,
                json={"ratings": {"passing": 2, "digging": 1, "movement": 3, "serve": 2}})

    plan = client.post("/player/plan/generate", headers=auth).json()
    blocks = plan["blocks"]
    assert 1 <= len(blocks) <= 5
    # libero emphasis: weakest primary first -> digging (1) before passing (2)
    assert blocks[0]["skill_key"] == "digging"
    assert blocks[0]["status"] == "active"
    assert all(b["status"] == "locked" for b in blocks[1:])
    assert blocks[0]["level_target"] == 2
    assert blocks[0]["drills"], "block should carry drill details"

    # locked block's checkpoints can't be toggled
    locked_cp = blocks[1]["checkpoints"][0]["id"]
    assert client.put(f"/player/checkpoints/{locked_cp}", headers=auth, json={"done": True}).status_code == 409

    # completing every checkpoint in block 0 unlocks block 1
    for cp in blocks[0]["checkpoints"]:
        r = client.put(f"/player/checkpoints/{cp['id']}", headers=auth, json={"done": True})
        assert r.status_code == 200
    updated = r.json()
    assert updated["unlocked_next"] is True
    assert updated["plan"]["blocks"][0]["status"] == "done"
    assert updated["plan"]["blocks"][1]["status"] == "active"

    # un-checking reopens the block
    cp0 = updated["plan"]["blocks"][0]["checkpoints"][0]["id"]
    reopened = client.put(f"/player/checkpoints/{cp0}", headers=auth, json={"done": False}).json()
    assert reopened["plan"]["blocks"][0]["status"] == "active"


def test_all_fives_assessment_still_gets_a_plan(client, auth):
    """A kid who maxes every slider must NOT dead-end (the live
    'Building your plan… and then never does it' bug): they get
    prove-it blocks holding Mastery under the hardest criteria."""
    client.put("/player/profile", headers=auth,
               json={"position": "OH", "level_band": "high_school"})
    all5 = {k: 5 for k in ["serve", "passing", "setting", "attacking",
                           "blocking", "digging", "movement", "game_iq"]}
    assert client.post("/player/assessment", headers=auth,
                       json={"ratings": all5}).status_code == 200
    r = client.post("/player/plan/generate", headers=auth)
    assert r.status_code == 200, r.text
    blocks = r.json()["blocks"]
    assert blocks, "plan must never be empty"
    assert all(b["level_target"] == 5 for b in blocks)
    # OH prove-it blocks lead with the position's primary skills
    assert blocks[0]["skill_key"] in {"attacking", "passing", "serve"}


def test_drills_and_logs(client, auth):
    client.put("/player/profile", headers=auth, json={"position": "S"})
    drills = client.get("/player/drills?skill_key=setting", headers=auth).json()["drills"]
    assert drills and all(d["skill_key"] == "setting" for d in drills)
    solo = client.get("/player/drills?solo_only=true", headers=auth).json()["drills"]
    assert solo and all(d["solo"] for d in solo)

    r = client.post("/player/logs", headers=auth, json={
        "skills": ["setting"], "drill_keys": ["wall-sets"], "quality": 4,
        "minutes": 30, "notes": "hands felt way more even today",
    })
    assert r.status_code == 200
    assert r.json()["skills"] == ["setting"]

    logs = client.get("/player/logs", headers=auth).json()["logs"]
    assert len(logs) == 1
    prog = client.get("/player/progress", headers=auth).json()
    assert prog["sessions_total"] == 1 and prog["sessions_28d"] == 1
    assert prog["week_streak"] == 1


def test_coach_context_assembly(client, auth, monkeypatch):
    """The chat context builder pulls profile + levels + block + logs, and the
    knowledge selector finds skills in free text. No API call is made."""
    from app import db, player, knowledge

    client.put("/player/profile", headers=auth, json={"position": "OH"})
    client.post("/player/assessment", headers=auth, json={"ratings": {"attacking": 2, "passing": 3}})
    client.post("/player/plan/generate", headers=auth)
    client.post("/player/logs", headers=auth, json={"skills": ["attacking"], "quality": 3, "notes": "kept hitting the net"})

    conn = db.connect(db.resolve_db_path())
    user = dict(conn.execute("SELECT * FROM users").fetchone())
    ctx = player._player_context(conn, user)
    conn.close()

    assert "Position: OH" in ctx
    assert "Attacking / Spiking" in ctx and "2/5" in ctx
    assert "Active goal" in ctx
    assert "kept hitting the net" in ctx

    keys = player._mentioned_skills("why do my serves keep going into the net when I spike?")
    assert "serve" in keys and "attacking" in keys

    snip = knowledge.knowledge_snippets(["serve"], "OH")
    assert "serve into the net" in snip and "Position guide (OH)" in snip


def test_delete_account_removes_everything(client, auth):
    client.put("/player/profile", headers=auth, json={"position": "OH"})
    client.post("/player/assessment", headers=auth, json={"ratings": {"attacking": 2}})
    client.post("/player/plan/generate", headers=auth)
    client.post("/player/logs", headers=auth, json={"skills": ["attacking"]})

    # wrong password refused; account still works
    bad = client.request("DELETE", "/player/account", headers=auth, json={"password": "nope999"})
    assert bad.status_code == 403
    assert client.get("/player/me", headers=auth).status_code == 200

    ok = client.request("DELETE", "/player/account", headers=auth, json={"password": "spike123"})
    assert ok.status_code == 200 and ok.json()["deleted"] is True

    # token dead, login dead, and no orphan rows anywhere
    assert client.get("/player/me", headers=auth).status_code == 401
    assert client.post("/player/login", json={"username": "celia", "password": "spike123"}).status_code == 401
    from app import db
    conn = db.connect(db.resolve_db_path())
    for table in ("users", "sessions", "player_profiles", "skill_assessments",
                  "plans", "plan_blocks", "plan_checkpoints", "training_logs",
                  "video_assessments"):
        n = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        assert n == 0, f"{table} still has {n} rows"
    conn.close()


def test_theme_is_per_account(client, auth):
    # set at onboarding (profile PUT), read back from /me
    client.put("/player/profile", headers=auth,
               json={"position": "OH", "theme": "intense"})
    assert client.get("/player/me", headers=auth).json()["profile"]["theme"] == "intense"

    # settable alone via the header button endpoint; invalid rejected
    r = client.put("/player/profile/theme", headers=auth, json={"theme": "classic"})
    assert r.status_code == 200 and r.json()["theme"] == "classic"
    assert client.put("/player/profile/theme", headers=auth,
                      json={"theme": "neon"}).status_code == 422

    # a second sign-in (new "device") sees the account's theme
    tok2 = client.post("/player/login", json={"username": "celia", "password": "spike123"}).json()["token"]
    me2 = client.get("/player/me", headers={"Authorization": f"Bearer {tok2}"}).json()
    assert me2["profile"]["theme"] == "classic"
