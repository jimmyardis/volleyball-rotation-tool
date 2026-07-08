"""FastAPI server — the seam between the React UI and the engine + DB.

The interesting endpoint is GET /lineups/{id}/rotations: it loads the stored
STARTING lineup and computes all 6 rotations + metadata on the fly. Rotations
are never persisted — the engine is the single source of truth.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import coach, db, engine, rally
from .models import (
    ChatRequest,
    CoverageSave,
    FormationSave,
    LineupCreate,
    LineupPositions,
    MistakesSave,
    NoteCreate,
    NoteUpdate,
    OverlapCheck,
    PairsSave,
    PlayerCreate,
    PlayerUpdate,
    SimGameRequest,
    SimRequest,
    SubsSave,
    TeamCreate,
)

# Pull ANTHROPIC_API_KEY from the user's ~/.env (and any local .env) for the
# coaching chatbot. The key is never committed; the feature degrades gracefully
# if it's absent.
load_dotenv()
load_dotenv(os.path.expanduser("~/.env"))

FRONT_ROW_ZONES = {2, 3, 4}

COACH_SYSTEM = """You are an assistant volleyball coach built into a rotation & \
lineup app. Your job is to help the coach with two things: (1) practice DRILLS \
and (2) PLAYER development/help (skills, positioning, fixing common mistakes).

Guidelines:
- Be concrete and practical. Prefer named drills with a one-line setup, the \
reps/goal, and what to coach (the key cue). Keep answers tight.
- Tailor advice to the position when relevant (setter, outside, middle, \
opposite, libero, DS) and to age/level if the coach mentions it.
- Use short paragraphs and simple dashes for lists. No long essays.
- You understand the app's concepts: zones 1-6, the 6 rotations, serve / \
receive / base situations, overlap rules, diagonal opposite pairings \
(setter-opposite, the two outsides, the two middles), front/back substitution \
pairings, and that the libero can't play the front row.
- If asked something unrelated to volleyball coaching, briefly say that's \
outside what you help with and steer back to drills or player help.
- You can BUILD a lineup and save it into the app with the create_lineup tool. \
Use the player IDs from the team context. Build a sensible lineup from the \
roster's roles and ratings (a 5-1 places the setter and opposite diagonally, \
the two outsides diagonally, the two middles diagonally). If the coach's request \
is vague, make reasonable choices and tell them what you built; they can edit or \
delete it. Only create a lineup when the coach asks you to build/make/insert one."""

# DB lives on the persistent volume in production (set VB_DB_PATH), else local.
DB_PATH = Path(os.getenv("VB_DB_PATH") or (Path(__file__).resolve().parent.parent / "volleyball.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

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


# The coach-facing API is gated: every request to these prefixes needs a
# signed-in COACH's bearer token (player endpoints have their own auth under
# /player, and /coach handles sign-in itself). This closed the "anyone with
# the URL can edit the roster / burn chat credits" launch blocker.
_COACH_API_PREFIXES = ("/teams", "/lineups", "/players", "/overlap-check",
                       "/coach-chat", "/notes")


@app.middleware("http")
async def _coach_gate(request: Request, call_next):
    path = request.url.path
    if request.method != "OPTIONS" and path.startswith(_COACH_API_PREFIXES):
        auth = request.headers.get("authorization") or ""
        user = None
        if auth.startswith("Bearer "):
            conn = db.connect(DB_PATH)
            try:
                user = coach.verify_coach_token(conn, auth.removeprefix("Bearer ").strip())
            finally:
                conn.close()
        if not user:
            return JSONResponse({"detail": "coach sign-in required"}, status_code=401)
        request.state.coach = user
    return await call_next(request)


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
def list_teams(request: Request, conn=Depends(get_conn)):
    # request.state.coach is set by the auth gate middleware
    return db.list_teams(conn, owner_user_id=request.state.coach["id"])


@app.post("/teams", status_code=201)
def create_team(body: TeamCreate, request: Request, conn=Depends(get_conn)):
    return db.create_team(conn, body.name, body.season,
                          owner_user_id=request.state.coach["id"])


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
            attributes={a: getattr(body, a) for a in engine.ATTRS},
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
        detail = engine.check_overlap_detail(coords)
        return {
            "saved": True, "legal": not detail,
            "faults": [f["text"] for f in detail], "fault_pairs": detail,
        }
    return {"saved": True, "legal": True, "faults": [], "fault_pairs": []}


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
    detail = engine.check_overlap_detail({z: tuple(xy) for z, xy in body.coords.items()})
    return {
        "legal": not detail,
        "faults": [f["text"] for f in detail],
        "fault_pairs": detail,
    }


# ---------------------------------------------------------------- simulation

@app.get("/role-presets")
def role_presets():
    """Default attribute presets per position (for the roster editor)."""
    return engine.ROLE_PRESETS


def _sim_inputs(conn, lineup_id: int):
    """Shared loader for both sim endpoints: lineup, players, effective
    rotations (subs applied), and the roster's tagged mistakes."""
    lineup = db.get_lineup(conn, lineup_id)
    if not lineup:
        raise HTTPException(404, "lineup not found")
    start = db.get_lineup_positions(conn, lineup_id)
    if set(start.keys()) != set(range(1, 7)):
        raise HTTPException(409, "lineup has no complete starting positions yet")
    players = {p["id"]: p for p in db.list_players(conn, lineup["team_id"])}
    effective = [
        engine.apply_substitutions(state, db.get_substitutions(conn, lineup_id, idx))
        for idx, state in enumerate(engine.all_rotations(start))
    ]
    mistakes = db.team_mistakes(conn, lineup["team_id"])
    return lineup, start, players, effective, mistakes


@app.post("/lineups/{lineup_id}/simulate")
def simulate(lineup_id: int, body: SimRequest, conn=Depends(get_conn)):
    """Rally-engine batch: many simulated sets, aggregated per rotation and
    per player, with plain-English best/worst insights."""
    lineup, start, players, effective, mistakes = _sim_inputs(conn, lineup_id)
    opponent = max(1, min(100, body.opponent_skill))
    sets = max(20, min(500, body.sets))
    batch = rally.simulate_batch(start, players, mistakes, opponent,
                                 sets=sets, rotations=effective)
    batch["insights"] = rally.generate_insights(batch, players)
    for r in batch["rotations"]:
        meta = engine.rotation_metadata(effective[r["rot"]], players, lineup["system"])
        r["setter_location"] = meta["setter_location"]
        r["positions"] = effective[r["rot"]]
    batch["lineup"] = lineup
    batch["players"] = list(players.values())
    return batch


@app.post("/lineups/{lineup_id}/simulate-game")
def simulate_game(lineup_id: int, body: SimGameRequest, conn=Depends(get_conn)):
    """Play ONE full set touch-by-touch and return the whole event stream —
    the frontend plays it back like a broadcast (court + narration box)."""
    import random as _random
    lineup, start, players, effective, mistakes = _sim_inputs(conn, lineup_id)
    opponent = max(1, min(100, body.opponent_skill))
    rng = _random.Random(body.seed)
    result = rally.simulate_set(start, players, mistakes, opponent, rng,
                                rotations=effective)
    return {
        "lineup": lineup,
        "players": list(players.values()),
        "opp_players": list(result["opp_players"].values()),
        "rotations": effective,
        "score": result["score"],
        "won": result["won"],
        "events": result["events"],
        "player_stats": result["player_stats"],
        "rotation_stats": result["rotation_stats"],
    }


# ---------------------------------------------------------------- mistakes

@app.get("/mistake-catalog")
def mistake_catalog():
    """The tag list for the roster editor, grouped by moment."""
    return {"catalog": [{"key": k, **v} for k, v in rally.MISTAKE_CATALOG.items()],
            "severities": list(rally.SEVERITIES)}


@app.get("/players/{player_id}/mistakes")
def get_mistakes(player_id: int, conn=Depends(get_conn)):
    if not db.get_player(conn, player_id):
        raise HTTPException(404, "player not found")
    return {"mistakes": db.get_player_mistakes(conn, player_id)}


@app.put("/players/{player_id}/mistakes")
def put_mistakes(player_id: int, body: MistakesSave, conn=Depends(get_conn)):
    if not db.get_player(conn, player_id):
        raise HTTPException(404, "player not found")
    for key, sev in body.mistakes.items():
        if key not in rally.MISTAKE_CATALOG:
            raise HTTPException(422, f"unknown mistake '{key}'")
        if sev not in rally.SEVERITIES:
            raise HTTPException(422, f"severity must be one of {list(rally.SEVERITIES)}")
    db.set_player_mistakes(conn, player_id, body.mistakes)
    return {"mistakes": db.get_player_mistakes(conn, player_id)}


# ---------------------------------------------------------------- notes

@app.get("/teams/{team_id}/notes")
def list_notes(team_id: int, player_id: int | None = None,
               lineup_id: int | None = None, notebook: bool = False,
               conn=Depends(get_conn)):
    if not db.get_team(conn, team_id):
        raise HTTPException(404, "team not found")
    return db.list_notes(conn, team_id, player_id=player_id,
                         lineup_id=lineup_id, notebook_only=notebook)


@app.post("/teams/{team_id}/notes", status_code=201)
def create_note(team_id: int, body: NoteCreate, conn=Depends(get_conn)):
    if not db.get_team(conn, team_id):
        raise HTTPException(404, "team not found")
    return db.create_note(conn, team_id, body.body.strip(),
                          player_id=body.player_id, lineup_id=body.lineup_id)


@app.put("/notes/{note_id}")
def update_note(note_id: int, body: NoteUpdate, conn=Depends(get_conn)):
    note = db.update_note(conn, note_id, body.body.strip())
    if not note:
        raise HTTPException(404, "note not found")
    return note


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, conn=Depends(get_conn)):
    db.delete_note(conn, note_id)


# ---------------------------------------------------------------- coach assistant

@app.get("/coach-chat/status")
def coach_chat_status():
    """Tell the UI whether the assistant is configured (API key present)."""
    return {"available": bool(os.getenv("ANTHROPIC_API_KEY"))}


def _coach_context(conn, team_id: int | None, lineup_id: int | None) -> str:
    """Build a compact text snapshot of the roster + a lineup's rotations so the
    assistant can answer questions about the actual team."""
    parts: list[str] = []
    team = db.get_team(conn, team_id) if team_id else None
    if team:
        parts.append(f"Team: {team['name']}" + (f" ({team['season']})" if team.get("season") else ""))
        roster = db.list_players(conn, team_id)
        if roster:
            parts.append("Roster (use the id= value when building a lineup; attributes are 0-100):")
            for p in roster:
                lib = " [libero]" if p.get("is_libero") else ""
                attrs = " ".join(f"{a[:3]}{p.get(a)}" for a in engine.ATTRS)
                parts.append(f"- id={p['id']} #{p.get('jersey_number','?')} {p['name']} — {p['primary_role']}{lib} ({attrs})")

    lineup = db.get_lineup(conn, lineup_id) if lineup_id else None
    if lineup:
        start = db.get_lineup_positions(conn, lineup_id)
        if set(start.keys()) == set(range(1, 7)):
            players = {p["id"]: p for p in db.list_players(conn, lineup["team_id"])}
            nm = lambda pid: players.get(pid, {}).get("name", f"#{pid}")
            parts.append(f'\nLineup "{lineup["name"]}" ({lineup["system"]}) — rotations:')
            for idx, state in enumerate(engine.all_rotations(start)):
                swaps = db.get_substitutions(conn, lineup_id, idx)
                eff = engine.apply_substitutions(state, swaps)
                meta = engine.rotation_metadata(eff, players, lineup["system"])
                subtxt = "; ".join(f"{nm(o)} in for {nm(s)}" for s, o in swaps.items()) or "none"
                parts.append(
                    f"  R{idx+1}: serving {nm(meta['server_id'])}; setter {meta['setter_location']} row, "
                    f"{meta['front_row_attacker_count']} front attackers; subs: {subtxt}"
                )
    return "\n".join(parts)


CREATE_LINEUP_TOOL = {
    "name": "create_lineup",
    "description": (
        "Create a new lineup (a starting six) for the coach's current team and "
        "save it into the app. Use player IDs from the team context. The 6 "
        "rotations are computed automatically from the starting six."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "a short descriptive name"},
            "system": {"type": "string", "enum": ["5-1", "6-2", "4-2"]},
            "positions": {
                "type": "object",
                "description": "map of zone ('1'..'6') to player id. Exactly 6 distinct players.",
                "additionalProperties": {"type": "integer"},
            },
            "notes": {"type": "string"},
        },
        "required": ["name", "system", "positions"],
    },
}


def _exec_create_lineup(conn, team_id: int | None, args: dict) -> dict:
    """Execute the create_lineup tool. Returns a result dict for the model."""
    if not team_id:
        return {"error": "No team is selected in the app, so I can't save a lineup."}
    team_players = {p["id"]: p for p in db.list_players(conn, team_id)}
    by_name = {p["name"].lower(): p["id"] for p in team_players.values()}

    raw = args.get("positions") or {}
    positions: dict[int, int] = {}
    for z, v in raw.items():
        try:
            zone = int(z)
        except (TypeError, ValueError):
            return {"error": f"invalid zone {z!r}"}
        pid = v if isinstance(v, int) and v in team_players else by_name.get(str(v).lower())
        if pid is None:
            return {"error": f"player {v!r} (zone {z}) is not on this team"}
        positions[zone] = pid

    if set(positions) != set(range(1, 7)):
        return {"error": "positions must assign exactly zones 1-6"}
    if len(set(positions.values())) != 6:
        return {"error": "each zone needs a different player"}

    try:
        lineup = db.create_lineup(conn, team_id, args.get("name", "New lineup"),
                                  args.get("system", "5-1"), args.get("notes"))
        db.set_lineup_positions(conn, lineup["id"], positions)
    except ValueError as e:
        return {"error": str(e)}
    return {"ok": True, "lineup_id": lineup["id"], "name": lineup["name"], "system": lineup["system"]}


@app.post("/coach-chat")
def coach_chat(body: ChatRequest, conn=Depends(get_conn)):
    """A volleyball coaching assistant (drills + player help) backed by Claude.

    Given team_id / lineup_id, the assistant sees the roster + the lineup's
    rotations, and can build & save a new lineup via the create_lineup tool.
    """
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(503, "Coach assistant unavailable: set ANTHROPIC_API_KEY in ~/.env")
    try:
        from anthropic import Anthropic
    except ImportError:
        raise HTTPException(503, "Coach assistant unavailable: run pip install -r requirements.txt")

    # only user/assistant turns are valid chat roles (system is a separate param)
    messages = [
        {"role": m.role, "content": m.content}
        for m in body.messages
        if m.content.strip() and m.role in ("user", "assistant")
    ][-12:]
    if not messages:
        raise HTTPException(422, "no message to send")

    system = COACH_SYSTEM
    context = _coach_context(conn, body.team_id, body.lineup_id)
    if context:
        system += (
            "\n\nThe coach is working with this team in the app. Use it to answer "
            "questions about their roster and rotations, and as the source of "
            "player IDs when building a lineup:\n" + context
        )

    client = Anthropic(api_key=key)
    created: list[dict] = []
    try:
        for _ in range(4):  # bounded tool loop
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=1024, system=system,
                messages=messages, tools=[CREATE_LINEUP_TOOL],
            )
            if resp.stop_reason != "tool_use":
                text = "".join(b.text for b in resp.content if b.type == "text")
                return {"reply": text, "created_lineups": created}

            # replay the assistant's tool_use turn, then return tool results
            assistant_content, tool_results = [], []
            for b in resp.content:
                if b.type == "text":
                    assistant_content.append({"type": "text", "text": b.text})
                elif b.type == "tool_use":
                    assistant_content.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
                    out = _exec_create_lineup(conn, body.team_id, b.input) if b.name == "create_lineup" else {"error": "unknown tool"}
                    if out.get("ok"):
                        created.append({"id": out["lineup_id"], "name": out["name"], "system": out["system"]})
                    tool_results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out)})
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
    except Exception as e:
        raise HTTPException(502, f"Coach assistant error: {e}")
    return {"reply": "(I made several changes — check your lineups.)", "created_lineups": created}


# ---------------------------------------------------------------- player side
# The player-facing companion surface (accounts, plans, logs, personal coach).
from . import player as player_side  # noqa: E402

app.include_router(player_side.router)
app.include_router(coach.router)


# ---------------------------------------------------------------- static frontend
# Serve the built React app (if present) from the same service, so the whole app
# lives at one URL. Mounted LAST so it never shadows the API routes above.
_WEBDIST = Path(__file__).resolve().parent.parent / "webdist"
if _WEBDIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_WEBDIST), html=True), name="web")
