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
    LineupCreate,
    LineupPositions,
    OverlapCheck,
    PlayerCreate,
    PlayerUpdate,
    TeamCreate,
)

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
    for idx, state in enumerate(states):
        rotations.append({
            "rotation_index": idx,  # 0..5 — Phase 2 will tag events with this.
            "positions": state,
            "metadata": engine.rotation_metadata(state, players, lineup["system"]),
        })
    return {
        "lineup": lineup,
        "players": list(players.values()),
        "rotations": rotations,
    }


# ---------------------------------------------------------------- overlap (stretch)

@app.post("/overlap-check")
def overlap_check(body: OverlapCheck):
    faults = engine.check_overlap({z: tuple(xy) for z, xy in body.coords.items()})
    return {"legal": not faults, "faults": faults}
