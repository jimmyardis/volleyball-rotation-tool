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
