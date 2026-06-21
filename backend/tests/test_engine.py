"""Engine acceptance tests. These are the bar from the spec, Section 6 & 7."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import engine  # noqa: E402

# A canonical 5-1 start: setter (player 1) in zone 1 (back row).
# zone -> player_id
START = {1: 101, 2: 102, 3: 103, 4: 104, 5: 105, 6: 106}

PLAYERS = {
    101: {"primary_role": "S", "is_libero": 0},    # setter
    102: {"primary_role": "OPP", "is_libero": 0},
    103: {"primary_role": "MB", "is_libero": 0},
    104: {"primary_role": "OH", "is_libero": 0},
    105: {"primary_role": "OH", "is_libero": 0},
    106: {"primary_role": "MB", "is_libero": 0},
}


# ---- Section 6: the three required engine properties --------------------

def test_six_rotations_returns_to_start():
    rotations = engine.all_rotations(START)
    current = rotations[-1]
    after_sixth = engine.rotate_once(current)
    assert after_sixth == START


def test_all_rotations_has_six_states_index_zero_is_start():
    rotations = engine.all_rotations(START)
    assert len(rotations) == 6
    assert rotations[0] == START


def test_every_rotation_has_all_six_players_once():
    for state in engine.all_rotations(START):
        assert set(state.keys()) == {1, 2, 3, 4, 5, 6}
        assert sorted(state.values()) == sorted(START.values())


def test_zone2_of_rotation_n_becomes_server_of_rotation_n_plus_1():
    rotations = engine.all_rotations(START)
    for n in range(5):
        assert rotations[n][2] == rotations[n + 1][engine.SERVER_ZONE]


def test_rotate_once_does_not_mutate_input():
    snapshot = dict(START)
    engine.rotate_once(START)
    assert START == snapshot


# ---- Section 7: rotation metadata --------------------------------------

def test_server_is_zone_one_player():
    meta = engine.rotation_metadata(START, PLAYERS)
    assert meta["server_id"] == START[1]


def test_back_row_setter_means_three_front_attackers():
    # Setter (101) starts in zone 1 (back row) -> 3 attackers up front.
    meta = engine.rotation_metadata(START, PLAYERS)
    assert meta["setter_location"] == "back"
    assert meta["front_row_attacker_count"] == 3


def test_front_row_setter_means_two_front_attackers():
    # Rotate until the setter is in the front row, then it must drop to 2.
    for state in engine.all_rotations(START):
        meta = engine.rotation_metadata(state, PLAYERS)
        if meta["setter_zone"] in engine.FRONT_ROW:
            assert meta["setter_location"] == "front"
            assert meta["front_row_attacker_count"] == 2


def test_libero_in_front_is_not_counted_as_attacker():
    players = dict(PLAYERS)
    players[103] = {"primary_role": "MB", "is_libero": 1}  # a (nonsensical) front libero
    meta = engine.rotation_metadata(START, players)
    assert 103 not in meta["front_row_attacker_ids"]


# ---- Stretch: overlap checker ------------------------------------------

def _legal_coords():
    # x left->right, y away from net. Front row near net (small y).
    return {
        4: (1.0, 1.0), 3: (2.0, 1.0), 2: (3.0, 1.0),
        5: (1.0, 2.0), 6: (2.0, 2.0), 1: (3.0, 2.0),
    }


def test_legal_formation_has_no_faults():
    assert engine.check_overlap(_legal_coords()) == []


def test_back_player_ahead_of_front_is_a_fault():
    coords = _legal_coords()
    coords[1] = (3.0, 0.5)  # right back creeps ahead of right front (zone 2)
    faults = engine.check_overlap(coords)
    assert any("zone 2" in f and "zone 1" in f for f in faults)


def test_left_right_order_violation_is_a_fault():
    coords = _legal_coords()
    coords[4] = (5.0, 1.0)  # left front shoved right of center/right front
    faults = engine.check_overlap(coords)
    assert any("front row" in f for f in faults)


# ---- Phases: serve / receive / base ------------------------------------

def test_serve_positions_cover_all_six_and_server_is_deep():
    coords = engine.serve_positions(START)
    assert set(coords.keys()) == {1, 2, 3, 4, 5, 6}
    # server (zone 1) is pulled back to the line: largest y of all players.
    assert coords[1][1] == max(xy[1] for xy in coords.values())


def test_receive_default_is_overlap_legal():
    coords = engine.receive_default(START)
    assert engine.check_overlap(coords) == []


def test_base_positions_put_front_row_near_net():
    coords = engine.base_positions(START, PLAYERS)
    front_y = max(coords[z][1] for z in (2, 3, 4))
    back_y = min(coords[z][1] for z in (1, 5, 6))
    assert front_y < back_y  # every front-row body nearer the net than back row


def test_base_positions_give_each_row_distinct_lanes():
    coords = engine.base_positions(START, PLAYERS)
    front_x = sorted(coords[z][0] for z in (2, 3, 4))
    assert len(set(front_x)) == 3  # no two front-row players share a lane


# ---- Substitutions ------------------------------------------------------

def test_apply_substitutions_swaps_the_right_slot():
    # Sub bench player 201 in for starter 105 (who is in zone 5).
    effective = engine.apply_substitutions(START, {105: 201})
    assert effective[5] == 201
    # everyone else unchanged
    assert {z: effective[z] for z in (1, 2, 3, 4, 6)} == {z: START[z] for z in (1, 2, 3, 4, 6)}


def test_apply_substitutions_no_swaps_is_identity():
    assert engine.apply_substitutions(START, {}) == START


def test_metadata_reflects_substituted_player():
    # Sub a libero (no-attack) into the front-row zone holding attacker 102.
    players = dict(PLAYERS)
    players[201] = {"primary_role": "L", "is_libero": 1}
    effective = engine.apply_substitutions(START, {102: 201})
    meta = engine.rotation_metadata(effective, players)
    assert 201 not in meta["front_row_attacker_ids"]  # libero isn't an attacker
    assert 102 not in meta["front_row_attacker_ids"]


# ---- Pairing-driven substitution generation -----------------------------

def test_pairing_subs_back_partner_in_for_back_row_rotations():
    # Starter 103 (a middle, starts zone 3 = front) paired with bench 201 (back).
    # 201 should be on court exactly in the rotations where 103 sits in the back
    # row, and 103 on for the front-row rotations.
    pairs = [(103, 201)]
    plan = engine.generate_substitutions(START, pairs)
    rotations = engine.all_rotations(START)
    for r in range(6):
        zone_of_103 = next(z for z, pid in rotations[r].items() if pid == 103)
        if zone_of_103 in engine.BACK_ROW:
            assert plan[r].get(103) == 201   # DS subs in for the back row
        else:
            assert 103 not in plan[r]        # middle stays in up front


def test_pairing_subs_total_three_back_row_rotations():
    plan = engine.generate_substitutions(START, [(103, 201)])
    swaps = sum(1 for r in range(6) if plan[r].get(103) == 201)
    assert swaps == 3  # every player is back row in exactly 3 of 6 rotations


def test_no_pairs_means_no_generated_subs():
    plan = engine.generate_substitutions(START, [])
    assert all(plan[r] == {} for r in range(6))


# ---- Simulation ---------------------------------------------------------

def _sim_players(attacking=70, defense=60):
    base = {pid: {"primary_role": PLAYERS[pid]["primary_role"], "is_libero": 0} for pid in PLAYERS}
    for pid, p in base.items():
        p.update({"setting": 60, "defense": defense, "attacking": attacking,
                  "blocking": 60, "confidence": 65, "pressure": 65})
    base[101]["setting"] = 85  # the setter sets well
    return base


def test_stronger_team_beats_weak_opponent():
    players = _sim_players(attacking=85, defense=80)
    out = engine.simulate_rotations(engine.all_rotations(START), players, stakes=0.3,
                                    opponent_skill=30, games=600)
    assert all(r["win_pct"] > 60 for r in out["per_rotation"])


def test_simulation_ranks_all_six_rotations():
    players = _sim_players()
    out = engine.simulate_rotations(engine.all_rotations(START), players, stakes=0.5,
                                    opponent_skill=60, games=600)
    assert len(out["per_rotation"]) == 6
    assert sorted(out["ranking"]) == [0, 1, 2, 3, 4, 5]
    assert out["best_rotation"] == out["ranking"][0]


def test_high_stakes_hurts_low_pressure_team():
    players = _sim_players()
    for p in players.values():
        p["pressure"] = 20  # cracks under pressure
    low = engine.rotation_rating(START, players)
    p_low_stakes, eff_low = engine.rally_win_prob(low, stakes=0.1, opponent_skill=60)
    p_high_stakes, eff_high = engine.rally_win_prob(low, stakes=1.0, opponent_skill=60)
    assert eff_high < eff_low  # high stakes drags a low-pressure team down


def test_back_row_setter_rotation_has_three_attackers_in_sim():
    players = _sim_players()
    rating = engine.rotation_rating(START, players)  # setter in zone 1 (back)
    assert rating["attacker_count"] == 3
