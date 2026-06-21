# Volleyball Rotation & Lineup Tool — Phase 1

A rotation & lineup visualizer. Define a roster, set a starting lineup, see all
6 rotations on a court diagram, and read off who serves, where the setter is,
and how many front-row attackers you have.

Built **engine-first**: the rotation logic is pure, deterministic Python with a
full test suite, and the data model is designed from day one to carry into
Phase 2 (stat tracking) and Phase 3 (rally simulator). Every on-court thing
references a permanent `players.id`.

## Architecture

```
backend/   FastAPI + SQLite. The rotation engine + persistence.
  app/engine.py   pure rotation math + metadata + overlap checker  (no I/O)
  app/db.py       SQLite repository functions
  app/schema.sql  the simulator-ready schema
  app/main.py     REST API; computes rotations on the fly
  tests/          20 tests — engine properties + DB invariants
frontend/  React + Vite. SVG court + roster/lineup/rotation screens.
```

The rotation engine is the single source of truth: only the **starting** lineup
is stored; the other 5 rotations are always computed.

## Run it

**Backend** (terminal 1):

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000  (docs at /docs)
```

Optional — load a sample team to click around immediately:

```bash
python seed.py
```

**Frontend** (terminal 2):

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173  (proxies /api -> :8000)
```

## Run the tests

```bash
cd backend && source venv/bin/activate && pytest -q
```

The three engine properties from the spec are covered:
- rotating 6× returns to start,
- every rotation holds all 6 players exactly once,
- zone 2 of rotation N becomes the server of rotation N+1.

## What's deliberately *not* here (later phases)

No scoring, stat logging, charts, simulator, or auth. The hooks that keep those
cheap to add later are in place: stable player IDs, a `rotation_index` (0–5)
surfaced everywhere, an unused `dominant_hand` column the simulator will want,
and no assumption that the roster is exactly 6 players.
