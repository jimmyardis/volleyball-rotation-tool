"""Rally engine tests — the touch-by-touch set simulator (Phase 3).

Everything is seeded: same seed -> same set, statistical assertions use wide
tolerances so tuning the probability constants doesn't break the suite.
"""

import random

import pytest

from app import engine, rally


def make_players():
    """A plausible starting six + libero, ids 1..7."""
    def p(pid, name, role, jersey, libero=False, **over):
        base = engine.preset_for(role)
        base.update(over)
        return {"id": pid, "name": name, "jersey_number": jersey,
                "primary_role": role, "is_libero": libero, **base}
    return {
        1: p(1, "Avery", "S", 1),
        2: p(2, "Gray", "L", 2, libero=True),
        5: p(5, "Devon", "OH", 5),
        8: p(8, "Blake", "OPP", 8),
        9: p(9, "Emery", "OH", 9),
        12: p(12, "Casey", "MB", 12),
        15: p(15, "Frankie", "MB", 15),
    }


START = {1: 1, 2: 8, 3: 12, 4: 5, 5: 9, 6: 15}  # setter serving first


def run_set(mistakes=None, opponent=50, seed=7, target=25):
    return rally.simulate_set(
        START, make_players(), mistakes or {}, opponent,
        random.Random(seed), target=target,
    )


# ---------------------------------------------------------------- attributes

def test_serving_is_a_real_attribute():
    assert "serving" in engine.ATTRS
    assert all("serving" in preset for preset in engine.ROLE_PRESETS.values())


# ---------------------------------------------------------------- one set

def test_set_reaches_a_legal_score():
    result = run_set()
    us, them = result["score"]["us"], result["score"]["them"]
    assert max(us, them) >= 25
    assert abs(us - them) >= 2 or max(us, them) >= rally.SCORE_CAP
    assert result["won"] == (us > them)


def test_set_is_deterministic_for_a_seed():
    a, b = run_set(seed=42), run_set(seed=42)
    assert a["score"] == b["score"]
    assert len(a["events"]) == len(b["events"])


def test_events_tell_a_playable_story():
    result = run_set()
    events = result["events"]
    kinds = [e["k"] for e in events]
    assert kinds[0] == "rally_start"
    assert "serve" in kinds and "point" in kinds
    assert kinds[-1] == "set_end"
    # every point event carries the running score and our rotation
    points = [e for e in events if e["k"] == "point"]
    assert all("score" in e and "us_rot" in e for e in points)
    final = points[-1]["score"]
    assert final == [result["score"]["us"], result["score"]["them"]]


def test_rotation_advances_only_on_receive_wins():
    result = run_set()
    rot = 0
    serving = True  # we serve first in simulate_set when serve_first="us"
    for e in result["events"]:
        if e["k"] == "point":
            if e["winner"] == "us" and not serving:
                rot = (rot + 1) % 6  # sideout -> we rotate
            serving = e["winner"] == "us"
            assert e["us_rot"] in range(6)
    assert result["rotation_stats"] is not None


def test_rotation_stats_cover_all_points():
    result = run_set()
    played = sum(r["serve_points"] + r["recv_points"] for r in result["rotation_stats"])
    assert played == result["score"]["us"] + result["score"]["them"]


# ---------------------------------------------------------------- balance

def wins(n, opponent, seed=0, mistakes=None):
    won = 0
    rng = random.Random(seed)
    for _ in range(n):
        r = rally.simulate_set(START, make_players(), mistakes or {}, opponent, rng)
        won += r["won"]
    return won / n


def test_stronger_team_usually_wins():
    assert wins(60, opponent=30) > 0.72
    assert wins(60, opponent=92) < 0.35


def test_even_matchup_is_roughly_even():
    rate = wins(120, opponent=62)  # presets average out near the low 60s
    assert 0.25 < rate < 0.75


# ---------------------------------------------------------------- mistakes

def test_mistake_catalog_shape():
    assert set(rally.SEVERITIES) == {"sometimes", "often"}
    for key, m in rally.MISTAKE_CATALOG.items():
        assert m["label"] and m["moment"]


def test_serve_mistake_costs_serve_errors():
    def serve_errors(mistakes):
        rng = random.Random(3)
        errs = 0
        for _ in range(40):
            r = rally.simulate_set(START, make_players(), mistakes, 55, rng)
            errs += r["player_stats"][1].get("serve_errors", 0)  # Avery serves in R1
        return errs
    clean = serve_errors({})
    sloppy = serve_errors({1: {"serve_net": "often"}})
    assert sloppy > clean * 1.5


def test_pressure_amplifies_mistakes():
    calm = rally.mistake_multiplier(stakes=1.0, pressure=90)
    nervous = rally.mistake_multiplier(stakes=1.0, pressure=25)
    no_stakes = rally.mistake_multiplier(stakes=0.0, pressure=25)
    assert nervous > calm
    assert no_stakes == pytest.approx(1.0)


def test_phantom_team_is_complete():
    opp = rally.phantom_team(65, random.Random(1))
    assert len(opp) == 6
    assert all(pid < 0 for pid in opp)          # negative ids never collide
    assert any(p["primary_role"] == "S" for p in opp.values())


# ---------------------------------------------------------------- batch

def test_batch_aggregates_and_insights():
    batch = rally.simulate_batch(START, make_players(), {}, 60, sets=30, seed=5)
    assert batch["sets"] == 30
    assert len(batch["rotations"]) == 6
    for r in batch["rotations"]:
        assert 0.0 <= r["sideout_pct"] <= 1.0
        assert 0.0 <= r["point_win_pct"] <= 1.0
    assert batch["player_stats"]
    insights = rally.generate_insights(batch, make_players())
    assert insights, "insights should never be empty"
    text = " ".join(i["text"] for i in insights)
    assert "Rotation" in text
    kinds = {i["kind"] for i in insights}
    assert "best" in kinds and "worst" in kinds
