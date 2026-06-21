"""Rotation engine — the deterministic brain.

Pure functions only. No database, no UI, no I/O. Everything here is a
referentially-transparent transform over plain dicts, which is exactly what
makes it trivial to unit-test (see tests/test_engine.py) and reusable by the
Phase 3 simulator later.

Vocabulary (keep these exact terms everywhere — code, API, UI):
    zone            an integer 1..6, a fixed spot on the court (see diagram).
    positions       {zone: player_id} — who stands where, right now.
    rotation_index  0..5 — how many clockwise rotation steps from the start.
    rotation state  the `positions` dict for a given rotation_index.

Court layout, net at the top, viewed from above:

            NET
      +-----+-----+-----+
      |  4  |  3  |  2  |   front row (left -> right)
      +-----+-----+-----+
      |  5  |  6  |  1  |   back row (left -> right)
      +-----+-----+-----+

    Zone 1 = right back  -> THE SERVER serves from here.
    Zone 2 = right front, 3 = center front, 4 = left front.
    Zone 5 = left back, 6 = center back.
"""

from __future__ import annotations

ZONES: list[int] = [1, 2, 3, 4, 5, 6]
FRONT_ROW: frozenset[int] = frozenset({2, 3, 4})
BACK_ROW: frozenset[int] = frozenset({1, 5, 6})
SERVER_ZONE: int = 1

# Clockwise rotation: each zone RECEIVES the player from the next zone up the
# cycle. The physical cycle a single player walks is 1 -> 6 -> 5 -> 4 -> 3 -> 2 -> 1.
ROTATE_MAP: dict[int, int] = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 1}

# Left-to-right ordering used by the overlap rules.
FRONT_LEFT_TO_RIGHT: list[int] = [4, 3, 2]
BACK_LEFT_TO_RIGHT: list[int] = [5, 6, 1]
# Each front-row zone and the back-row zone directly behind it.
FRONT_BEHIND_PAIRS: list[tuple[int, int]] = [(2, 1), (3, 6), (4, 5)]


def rotate_once(positions: dict[int, int]) -> dict[int, int]:
    """positions = {zone: player_id}. Returns the next rotation (one step CW)."""
    return {zone: positions[ROTATE_MAP[zone]] for zone in ZONES}


def all_rotations(start: dict[int, int]) -> list[dict[int, int]]:
    """Return the 6 rotation states. Index 0 is the starting lineup."""
    rotations = [dict(start)]
    current = start
    for _ in range(5):
        current = rotate_once(current)
        rotations.append(current)
    return rotations


def _active_setter_zone(positions: dict[int, int], players: dict[int, dict]) -> int | None:
    """Zone of the setter who is actually running the offense.

    In a 5-1 there is one setter. In a 6-2 there are two, and the one in the
    BACK row is the one setting (the front-row setter is hitting as an
    opposite). So: prefer a back-row setter, else any setter, else None.
    """
    setter_zones = [z for z, pid in positions.items() if players.get(pid, {}).get("primary_role") == "S"]
    if not setter_zones:
        return None
    back = [z for z in setter_zones if z in BACK_ROW]
    return back[0] if back else setter_zones[0]


def _is_attacker(player: dict) -> bool:
    """A front-row body that can legally attack above the net.

    Setters (running offense) and liberos (can't attack above the net) don't
    count as front-row attackers.
    """
    return player.get("primary_role") != "S" and not player.get("is_libero")


def rotation_metadata(
    positions: dict[int, int],
    players: dict[int, dict],
    system: str = "5-1",
) -> dict:
    """Compute the coach-readable facts about a single rotation state.

    `players` maps player_id -> a dict with at least 'primary_role' and
    'is_libero'. Returns a JSON-serializable dict.

    Front-row attackers: the genuinely useful number. A front-row setter means
    one of the three front spots is spent setting, so only 2 attackers; a
    back-row setter penetrates from behind and leaves all 3 front bodies free
    to hit. We compute it directly from who is actually up front rather than
    hardcoding 2/3, so it stays correct for 6-2 and for libero edge cases.
    """
    setter_zone = _active_setter_zone(positions, players)
    setter_location: str | None
    if setter_zone is None:
        setter_location = None
    elif setter_zone in FRONT_ROW:
        setter_location = "front"
    else:
        setter_location = "back"

    front_attackers = [
        positions[z]
        for z in (2, 3, 4)
        if _is_attacker(players.get(positions[z], {}))
    ]

    return {
        "system": system,
        "server_id": positions[SERVER_ZONE],
        "setter_id": positions[setter_zone] if setter_zone is not None else None,
        "setter_zone": setter_zone,
        "setter_location": setter_location,
        "front_row_attacker_ids": front_attackers,
        "front_row_attacker_count": len(front_attackers),
    }


# ---------------------------------------------------------------------------
# Court geometry & the three on-court PHASES of a single rotation.
#
# A rotation is a fixed rotational ORDER (who is overlap-legal relative to whom).
# But where the six players physically STAND changes by phase:
#   serve   — your rotational spots, the server back at the line.
#   receive — a serve-receive formation; players slide to passing spots but must
#             stay overlap-legal until the opponent contacts the serve. Editable.
#   base    — once the ball is in play they switch to base spots by role
#             (setter right, middles middle, outsides left). The rotational slot
#             is unchanged; they just move.
#
# Coordinates are NORMALIZED: x in [0,1] left->right, y in [0,1] from the net
# (y=0) to the baseline (y=1). This matches check_overlap's convention (smaller
# y == nearer the net), so a formation can be validated directly.
# ---------------------------------------------------------------------------

ZONE_COORDS: dict[int, tuple[float, float]] = {
    4: (0.18, 0.30), 3: (0.50, 0.30), 2: (0.82, 0.30),  # front row
    5: (0.18, 0.74), 6: (0.50, 0.74), 1: (0.82, 0.74),  # back row
}


def serve_positions(positions: dict[int, int]) -> dict[int, tuple[float, float]]:
    """Where players stand when YOUR team is serving: rotational spots, with
    the zone-1 server pulled back behind the baseline."""
    coords = dict(ZONE_COORDS)
    coords[SERVER_ZONE] = (0.82, 0.96)  # server at the service line
    return {zone: coords[zone] for zone in positions}


def receive_default(positions: dict[int, int]) -> dict[int, tuple[float, float]]:
    """A sane, overlap-legal starting formation for serve-receive: everyone at
    their rotational spot, on court, ready to pass. The coach drags from here."""
    return {zone: ZONE_COORDS[zone] for zone in positions}


def _role_lane(role: str | None) -> int:
    """Preferred left/middle/right lane (0/1/2) for a role's base position."""
    if role == "OH":
        return 0  # outsides play the left
    if role in ("S", "OPP"):
        return 2  # setter / right side play the right
    return 1      # middles, libero, DS play the middle


def base_positions(
    positions: dict[int, int], players: dict[int, dict]
) -> dict[int, tuple[float, float]]:
    """Base ("switch") spots after the serve, by role.

    Front-row players line up at the net in left/middle/right lanes; back-row
    players spread deep in the same three lanes. Lanes are assigned by role
    preference, then de-conflicted so no two players share a lane in a row.
    """
    coords: dict[int, tuple[float, float]] = {}
    lane_x = [0.18, 0.50, 0.82]
    for zones_in_row, y in (([2, 3, 4], 0.13), ([1, 5, 6], 0.86)):
        members = [
            (z, _role_lane(players.get(positions[z], {}).get("primary_role")))
            for z in zones_in_row
            if z in positions
        ]
        # Sort by desired lane, tie-break by current left->right spot for
        # stability, then drop into distinct left/middle/right slots.
        members.sort(key=lambda m: (m[1], ZONE_COORDS[m[0]][0]))
        for slot, (zone, _) in enumerate(members):
            coords[zone] = (lane_x[slot], y)
    return coords


def check_overlap(coords: dict[int, tuple[float, float]]) -> list[str]:
    """Validate serve-receive positional (overlap) rules for custom spots.

    `coords` maps zone -> (x, y) where x increases left->right and y increases
    AWAY from the net (net at y = 0, so a smaller y is "nearer the net").

    Two rule families:
      1. Front/back: each front-row player must be nearer the net than the
         back-row player directly behind them  (2 ahead of 1, 3 ahead of 6,
         4 ahead of 5).
      2. Left/right: within each row the left-to-right order must hold
         (front: 4 < 3 < 2, back: 5 < 6 < 1, by x).

    Returns a list of human-readable fault strings; empty list == legal.
    Only checks zones present in `coords`, so it degrades gracefully.
    """
    faults: list[str] = []

    for front_z, back_z in FRONT_BEHIND_PAIRS:
        if front_z in coords and back_z in coords:
            if coords[front_z][1] >= coords[back_z][1]:
                faults.append(
                    f"Overlap: front-row zone {front_z} must be nearer the net "
                    f"than back-row zone {back_z}."
                )

    for row_name, order in (("front", FRONT_LEFT_TO_RIGHT), ("back", BACK_LEFT_TO_RIGHT)):
        present = [z for z in order if z in coords]
        for left_z, right_z in zip(present, present[1:]):
            if coords[left_z][0] >= coords[right_z][0]:
                faults.append(
                    f"Overlap: in the {row_name} row, zone {left_z} must be to "
                    f"the left of zone {right_z}."
                )

    return faults
