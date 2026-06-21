"""FastAPI server — the seam between the React UI and the engine + DB.

The interesting endpoint is GET /lineups/{id}/rotations: it loads the stored
STARTING lineup and computes all 6 rotations + metadata on the fly. Rotations
are never persisted — the engine is the single source of truth.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import db, engine
from .models import (
    CoverageSave,
    FormationSave,
    LineupCreate,
    LineupPositions,
    OverlapCheck,
    PairsSave,
    PlayerCreate,
    PlayerUpdate,
    SubsSave,
    TeamCreate,
)

FRONT_ROW_ZONES = {2, 3, 4}

DB_PATH = Path(__file__).resolve().parent.parent / "volleyball.db"

app = FastAPI(title="Volleyball Rotation & Lineup Tool", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase 1 is single-user/offline; lock down later.
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    conn = db.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


@app.on_event("startup")
def _startup() -> None:
    conn = db.connect(DB_PATH)
    db.init_db(conn)
    conn.close()


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------- teams

@app.get("/teams")
def list_teams(conn=Depends(get_conn)):
    return db.list_teams(conn)


@app.post("/teams", status_code=201)
def create_team(body: TeamCreate, conn=Depends(get_conn)):
    return db.create_team(conn, body.name, body.season)


# ---------------------------------------------------------------- players

@app.get("/teams/{team_id}/players")
def list_players(team_id: int, conn=Depends(get_conn)):
    return db.list_players(conn, team_id)


@app.post("/teams/{team_id}/players", status_code=201)
def create_player(team_id: int, body: PlayerCreate, conn=Depends(get_conn)):
    if not db.get_team(conn, team_id):
        raise HTTPException(404, "team not found")
    try:
        return db.create_player(
            conn, team_id, body.name, body.primary_role,
            jersey_number=body.jersey_number,
            secondary_role=body.secondary_role,
            is_libero=body.is_libero,
            dominant_hand=body.dominant_hand,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.patch("/players/{player_id}")
def update_player(player_id: int, body: PlayerUpdate, conn=Depends(get_conn)):
    if not db.get_player(conn, player_id):
        raise HTTPException(404, "player not found")
    try:
        return db.update_player(conn, player_id, **body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.delete("/players/{player_id}", status_code=204)
def delete_player(player_id: int, conn=Depends(get_conn)):
    db.delete_player(conn, player_id)


# ---------------------------------------------------------------- lineups

@app.get("/teams/{team_id}/lineups")
def list_lineups(team_id: int, conn=Depends(get_conn)):
    return db.list_lineups(conn, team_id)


@app.post("/teams/{team_id}/lineups", status_code=201)
def create_lineup(team_id: int, body: LineupCreate, conn=Depends(get_conn)):
    if not db.get_team(conn, team_id):
        raise HTTPException(404, "team not found")
    try:
        return db.create_lineup(conn, team_id, body.name, body.system, body.notes)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.delete("/lineups/{lineup_id}", status_code=204)
def delete_lineup(lineup_id: int, conn=Depends(get_conn)):
    db.delete_lineup(conn, lineup_id)


@app.put("/lineups/{lineup_id}/positions")
def set_positions(lineup_id: int, body: LineupPositions, conn=Depends(get_conn)):
    if not db.get_lineup(conn, lineup_id):
        raise HTTPException(404, "lineup not found")
    try:
        db.set_lineup_positions(conn, lineup_id, body.positions)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return db.get_lineup_positions(conn, lineup_id)


@app.get("/lineups/{lineup_id}/rotations")
def get_rotations(lineup_id: int, conn=Depends(get_conn)):
    """Compute all 6 rotations + metadata from the stored starting lineup."""
    lineup = db.get_lineup(conn, lineup_id)
    if not lineup:
        raise HTTPException(404, "lineup not found")
    start = db.get_lineup_positions(conn, lineup_id)
    if set(start.keys()) != set(range(1, 7)):
        raise HTTPException(409, "lineup has no complete 6-zone starting positions yet")

    players = {p["id"]: p for p in db.list_players(conn, lineup["team_id"])}
    states = engine.all_rotations(start)

    rotations = []
    for idx, starter_state in enumerate(states):
        # Apply this rotation's substitutions to get who's actually on court.
        swaps = db.get_substitutions(conn, lineup_id, idx)
        state = engine.apply_substitutions(starter_state, swaps)

        # Each rotation has three phase layouts (serve / receive / base).
        # Receive + base use the saved formation if the coach built one, else a
        # default; saved spots are keyed by player, remapped to the on-court zone.
        saved_recv = db.get_formation(conn, lineup_id, idx, "receive")
        receive = {
            zone: list(saved_recv[pid]) if pid in saved_recv else list(engine.ZONE_COORDS[zone])
            for zone, pid in state.items()
        }
        base_default = engine.base_positions(state, players)
        saved_base = db.get_formation(conn, lineup_id, idx, "base")
        base = {
            zone: list(saved_base[pid]) if pid in saved_base else list(base_default[zone])
            for zone, pid in state.items()
        }
        rotations.append({
            "rotation_index": idx,  # 0..5 — Phase 2 will tag events with this.
            "positions": state,                 # effective on-court (subs applied)
            "starter_positions": starter_state, # the rostered starters, pre-sub
            "subs": swaps,                      # starter_id -> on_court_id
            "metadata": engine.rotation_metadata(state, players, lineup["system"]),
            "serve_positions": {z: list(xy) for z, xy in engine.serve_positions(state).items()},
            "base_positions": base,
            "receive_positions": receive,
            "receive_saved": bool(saved_recv),
            "base_saved": bool(saved_base),
        })
    return {
        "lineup": lineup,
        "players": list(players.values()),
        "rotations": rotations,
    }


@app.put("/lineups/{lineup_id}/rotations/{rotation_index}/formation/{phase}")
def save_formation(
    lineup_id: int, rotation_index: int, phase: str, body: FormationSave, conn=Depends(get_conn)
):
    """Save a draggable formation (phase 'receive' or 'base') for one rotation.

    For 'receive' the response reports overlap legality (saving is allowed even
    when illegal, so WIP can be kept). 'base' is free — no overlap rule applies
    once the ball is in play.
    """
    if phase not in db.VALID_PHASES:
        raise HTTPException(422, f"phase must be one of {sorted(db.VALID_PHASES)}")
    if not db.get_lineup(conn, lineup_id):
        raise HTTPException(404, "lineup not found")
    start = db.get_lineup_positions(conn, lineup_id)
    if set(start.keys()) != set(range(1, 7)):
        raise HTTPException(409, "lineup has no complete starting positions yet")

    swaps = db.get_substitutions(conn, lineup_id, rotation_index)
    state = engine.apply_substitutions(engine.all_rotations(start)[rotation_index], swaps)
    placements = {pid: tuple(xy) for pid, xy in body.placements.items()}
    try:
        db.set_formation(conn, lineup_id, rotation_index, phase, placements)
    except ValueError as e:
        raise HTTPException(422, str(e))

    if phase == "receive":
        coords = {zone: placements[pid] for zone, pid in state.items() if pid in placements}
        faults = engine.check_overlap(coords)
        return {"saved": True, "legal": not faults, "faults": faults}
    return {"saved": True, "legal": True, "faults": []}


@app.put("/lineups/{lineup_id}/rotations/{rotation_index}/subs")
def save_subs(lineup_id: int, rotation_index: int, body: SubsSave, conn=Depends(get_conn)):
    """Set who's on court for one rotation. Validates the result is still 6
    distinct players occupying the 6 zones."""
    if not db.get_lineup(conn, lineup_id):
        raise HTTPException(404, "lineup not found")
    start = db.get_lineup_positions(conn, lineup_id)
    if set(start.keys()) != set(range(1, 7)):
        raise HTTPException(409, "lineup has no complete starting positions yet")

    starter_state = engine.all_rotations(start)[rotation_index]
    effective = engine.apply_substitutions(starter_state, body.swaps)
    if len(set(effective.values())) != 6:
        raise HTTPException(422, "substitutions would put a player in two zones at once")

    players = {p["id"]: p for p in db.list_players(conn, db.get_lineup(conn, lineup_id)["team_id"])}
    if not set(effective.values()) <= set(players):
        raise HTTPException(422, "on-court player not on this team")

    # Hard rule: a libero can never be in a front-row zone.
    for zone in FRONT_ROW_ZONES:
        if players.get(effective[zone], {}).get("is_libero"):
            raise HTTPException(422, f"the libero cannot play a front-row zone (zone {zone})")

    try:
        db.set_substitutions(conn, lineup_id, rotation_index, body.swaps)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"saved": True, "on_court": effective}


@app.get("/lineups/{lineup_id}/setup")
def get_setup(lineup_id: int, conn=Depends(get_conn)):
    """Coverage types + pairings + roster for the lineup's substitution setup."""
    lineup = db.get_lineup(conn, lineup_id)
    if not lineup:
        raise HTTPException(404, "lineup not found")
    return {
        "players": db.list_players(conn, lineup["team_id"]),
        "starter_positions": db.get_lineup_positions(conn, lineup_id),
        "coverage": db.get_coverage(conn, lineup_id),
        "pairs": db.get_pairs(conn, lineup_id),
    }


@app.put("/lineups/{lineup_id}/coverage")
def put_coverage(lineup_id: int, body: CoverageSave, conn=Depends(get_conn)):
    if not db.get_lineup(conn, lineup_id):
        raise HTTPException(404, "lineup not found")
    try:
        db.set_coverage(conn, lineup_id, body.coverage)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return db.get_coverage(conn, lineup_id)


@app.put("/lineups/{lineup_id}/pairs")
def put_pairs(lineup_id: int, body: PairsSave, conn=Depends(get_conn)):
    if not db.get_lineup(conn, lineup_id):
        raise HTTPException(404, "lineup not found")
    players = {p["id"]: p for p in db.list_players(conn, db.get_lineup(conn, lineup_id)["team_id"])}
    # The libero is a back-row player by rule — they can only be the back of a pair.
    for front_id, back_id in body.pairs:
        if players.get(front_id, {}).get("is_libero"):
            raise HTTPException(422, "the libero can't be the front-row player in a pairing")
    try:
        db.set_pairs(conn, lineup_id, [tuple(p) for p in body.pairs])
    except ValueError as e:
        raise HTTPException(422, str(e))
    return db.get_pairs(conn, lineup_id)


@app.post("/lineups/{lineup_id}/generate-subs")
def generate_subs(lineup_id: int, conn=Depends(get_conn)):
    """Fill in per-rotation substitutions from the pairings (overwrites existing
    subs for all 6 rotations). The starting point the coach then hand-edits."""
    if not db.get_lineup(conn, lineup_id):
        raise HTTPException(404, "lineup not found")
    start = db.get_lineup_positions(conn, lineup_id)
    if set(start.keys()) != set(range(1, 7)):
        raise HTTPException(409, "lineup has no complete starting positions yet")

    pairs = [(p["front_player_id"], p["back_player_id"]) for p in db.get_pairs(conn, lineup_id)]
    plan = engine.generate_substitutions(start, pairs)
    total = 0
    for r in range(6):
        db.set_substitutions(conn, lineup_id, r, plan[r])
        total += len(plan[r])
    return {"generated": True, "rotations_with_subs": sum(1 for r in range(6) if plan[r]), "total_swaps": total}


# ---------------------------------------------------------------- overlap (stretch)

@app.post("/overlap-check")
def overlap_check(body: OverlapCheck):
    faults = engine.check_overlap({z: tuple(xy) for z, xy in body.coords.items()})
    return {"legal": not faults, "faults": faults}
