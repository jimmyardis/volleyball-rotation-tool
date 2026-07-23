"""Player-side API: accounts, self-assessment, progression plan, training
log, drill library, progress, and the personalized AI coach.

Design (player-side-spec.md, adjusted to the real stack):
- Same SQLite database as the coach app; players are `users` rows with
  bearer-token sessions. Coach-link is deferred past MVP (solo-first).
- Plans are mastery-gated: one active block; completing all of a block's
  checkpoints marks it done and unlocks the next.
- The AI coach = player context (profile, levels, active block, recent logs)
  + curated knowledge (knowledge.py) + encouragement-first tone layer.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from . import db, knowledge, progression

router = APIRouter(prefix="/player", tags=["player"])

POSITIONS = {"S", "OH", "MB", "OPP", "L", "DS"}
LEVEL_BANDS = {"rec", "club", "middle_school", "high_school", "college"}
_PBKDF2_ITERATIONS = 200_000


# ---------------------------------------------------------------- plumbing

def get_conn():
    conn = db.connect(db.resolve_db_path())
    try:
        yield conn
    finally:
        conn.close()


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    salt, _ = stored.split("$", 1)
    return secrets.compare_digest(_hash_password(password, salt), stored)


def current_user(authorization: str | None = Header(None), conn=Depends(get_conn)) -> dict:
    """Resolve the bearer token to a user row (dependency for all
    authenticated endpoints)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "not signed in")
    token = authorization.removeprefix("Bearer ").strip()
    row = conn.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?",
        (token,),
    ).fetchone()
    if not row:
        raise HTTPException(401, "session expired — sign in again")
    return dict(row)


def _profile(conn, user_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM player_profiles WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def _latest_levels(conn, user_id: int) -> dict[str, dict]:
    """Latest assessment per skill: {skill_key: {level, assessed_at, source}}."""
    rows = conn.execute(
        "SELECT skill_key, level, source, assessed_at FROM skill_assessments "
        "WHERE user_id = ? ORDER BY assessed_at, id", (user_id,),
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        out[r["skill_key"]] = {"level": r["level"], "source": r["source"], "assessed_at": r["assessed_at"]}
    return out


# ---------------------------------------------------------------- auth

class Register(BaseModel):
    username: str = Field(min_length=3, max_length=24)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(default="", max_length=40)


class Login(BaseModel):
    username: str
    password: str


def _issue_token(conn, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sessions (user_id, token) VALUES (?, ?)", (user_id, token))
    conn.commit()
    return token


@router.post("/register")
def register(body: Register, conn=Depends(get_conn)):
    username = body.username.strip()
    if not username.replace("_", "").isalnum():
        raise HTTPException(422, "username: letters, numbers, and _ only")
    display = body.display_name.strip() or username
    try:
        cur = conn.execute(
            "INSERT INTO users (username, display_name, role, password_hash) VALUES (?, ?, 'player', ?)",
            (username, display, _hash_password(body.password)),
        )
    except Exception:
        raise HTTPException(409, "that username is taken")
    user_id = cur.lastrowid
    conn.execute("INSERT INTO player_profiles (user_id) VALUES (?)", (user_id,))
    token = _issue_token(conn, user_id)
    return {"token": token, "user": {"id": user_id, "username": username, "display_name": display}}


@router.post("/login")
def login(body: Login, conn=Depends(get_conn)):
    row = conn.execute("SELECT * FROM users WHERE username = ?", (body.username.strip(),)).fetchone()
    if not row or not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "wrong username or password")
    token = _issue_token(conn, row["id"])
    return {"token": token, "user": {"id": row["id"], "username": row["username"], "display_name": row["display_name"]}}


@router.post("/logout")
def logout(authorization: str | None = Header(None), conn=Depends(get_conn)):
    if authorization and authorization.startswith("Bearer "):
        conn.execute("DELETE FROM sessions WHERE token = ?", (authorization.removeprefix("Bearer ").strip(),))
        conn.commit()
    return {"ok": True}


class DeleteAccount(BaseModel):
    password: str


@router.delete("/account")
def delete_account(body: DeleteAccount, user=Depends(current_user), conn=Depends(get_conn)):
    """Permanently delete this player account and every row it owns (an App
    Store requirement — apps with accounts must offer in-app deletion).
    Password re-entry is the confirmation."""
    if user["role"] != "player":
        raise HTTPException(403, "only player accounts can be deleted here")
    if not _verify_password(body.password, user["password_hash"]):
        raise HTTPException(403, "wrong password")
    uid = user["id"]
    with conn:  # one transaction, children first (no ON DELETE CASCADE in schema)
        conn.execute("DELETE FROM video_assessments WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM training_logs WHERE user_id = ?", (uid,))
        conn.execute(
            "DELETE FROM plan_checkpoints WHERE block_id IN "
            "(SELECT b.id FROM plan_blocks b JOIN plans p ON p.id = b.plan_id WHERE p.user_id = ?)",
            (uid,))
        conn.execute(
            "DELETE FROM plan_blocks WHERE plan_id IN (SELECT id FROM plans WHERE user_id = ?)",
            (uid,))
        conn.execute("DELETE FROM plans WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM skill_assessments WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM player_profiles WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM users WHERE id = ?", (uid,))
    return {"deleted": True}


# ---------------------------------------------------------------- profile

THEMES = {"classic", "intense", "sky"}


class ProfileUpdate(BaseModel):
    position: str
    secondary_position: str | None = None
    level_band: str = "high_school"
    theme: str | None = None            # optional here; also settable alone below


@router.get("/me")
def me(user=Depends(current_user), conn=Depends(get_conn)):
    profile = _profile(conn, user["id"])
    levels = _latest_levels(conn, user["id"])
    plan = conn.execute(
        "SELECT id FROM plans WHERE user_id = ? AND status = 'active'", (user["id"],)
    ).fetchone()
    return {
        "user": {"id": user["id"], "username": user["username"], "display_name": user["display_name"]},
        "profile": profile,
        "has_assessment": bool(levels),
        "active_plan_id": plan["id"] if plan else None,
    }


@router.put("/profile")
def update_profile(body: ProfileUpdate, user=Depends(current_user), conn=Depends(get_conn)):
    if body.position not in POSITIONS:
        raise HTTPException(422, f"position must be one of {sorted(POSITIONS)}")
    if body.secondary_position and body.secondary_position not in POSITIONS:
        raise HTTPException(422, "bad secondary position")
    if body.level_band not in LEVEL_BANDS:
        raise HTTPException(422, f"level_band must be one of {sorted(LEVEL_BANDS)}")
    if body.theme is not None and body.theme not in THEMES:
        raise HTTPException(422, f"theme must be one of {sorted(THEMES)}")
    conn.execute(
        "UPDATE player_profiles SET position = ?, secondary_position = ?, level_band = ?, "
        "theme = COALESCE(?, theme) WHERE user_id = ?",
        (body.position, body.secondary_position, body.level_band, body.theme, user["id"]),
    )
    conn.commit()
    return _profile(conn, user["id"])


class ThemeUpdate(BaseModel):
    theme: str


@router.put("/profile/theme")
def update_theme(body: ThemeUpdate, user=Depends(current_user), conn=Depends(get_conn)):
    """The look follows the account: settable on its own from the header
    button / Profile without touching position or level."""
    if body.theme not in THEMES:
        raise HTTPException(422, f"theme must be one of {sorted(THEMES)}")
    conn.execute("UPDATE player_profiles SET theme = ? WHERE user_id = ?", (body.theme, user["id"]))
    conn.commit()
    return _profile(conn, user["id"])


# ---------------------------------------------------------------- skills & assessment

@router.get("/skills")
def skills():
    return {"skills": knowledge.SKILLS, "level_names": knowledge.LEVEL_NAMES}


class Assessment(BaseModel):
    ratings: dict[str, int]


@router.post("/assessment")
def save_assessment(body: Assessment, user=Depends(current_user), conn=Depends(get_conn)):
    valid = {s["key"] for s in knowledge.SKILLS}
    if not body.ratings:
        raise HTTPException(422, "no ratings given")
    for key, level in body.ratings.items():
        if key not in valid:
            raise HTTPException(422, f"unknown skill {key!r}")
        if not 1 <= level <= 5:
            raise HTTPException(422, f"{key}: level must be 1-5")
    now = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")
    for key, level in body.ratings.items():
        conn.execute(
            "INSERT INTO skill_assessments (user_id, skill_key, level, source, assessed_at) "
            "VALUES (?, ?, ?, 'self', ?)", (user["id"], key, level, now),
        )
    conn.commit()
    return {"levels": _latest_levels(conn, user["id"])}


# ---------------------------------------------------------------- plan

def _plan_payload(conn, plan_id: int) -> dict:
    plan = dict(conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone())
    blocks = [dict(r) for r in conn.execute(
        "SELECT * FROM plan_blocks WHERE plan_id = ? ORDER BY block_order", (plan_id,)
    ).fetchall()]
    drills_by_key = {d["key"]: d for d in (dict(r) for r in conn.execute("SELECT * FROM drills").fetchall())}
    for b in blocks:
        b["checkpoints"] = [dict(r) for r in conn.execute(
            "SELECT id, cp_order, text, done FROM plan_checkpoints WHERE block_id = ? ORDER BY cp_order",
            (b["id"],),
        ).fetchall()]
        b["drills"] = [drills_by_key[k] for k in json.loads(b["drill_keys"]) if k in drills_by_key]
        b["level_target_name"] = knowledge.LEVEL_NAMES.get(b["level_target"])
    plan["blocks"] = blocks
    return plan


@router.post("/plan/generate")
def generate_plan(user=Depends(current_user), conn=Depends(get_conn)):
    profile = _profile(conn, user["id"])
    if not profile or not profile.get("position"):
        raise HTTPException(409, "set your position first (Profile)")
    levels = _latest_levels(conn, user["id"])
    if not levels:
        raise HTTPException(409, "take the self-assessment first")

    blocks = progression.build_plan(profile["position"], {k: v["level"] for k, v in levels.items()})
    if not blocks:
        raise HTTPException(409, "every skill is already at Mastery — set new goals with your coach!")

    conn.execute("UPDATE plans SET status = 'archived' WHERE user_id = ? AND status = 'active'", (user["id"],))
    cur = conn.execute("INSERT INTO plans (user_id, position) VALUES (?, ?)", (user["id"], profile["position"]))
    plan_id = cur.lastrowid
    for i, blk in enumerate(blocks):
        bcur = conn.execute(
            "INSERT INTO plan_blocks (plan_id, block_order, skill_key, title, level_target, "
            "success_criteria, drill_keys, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (plan_id, i, blk["skill_key"], blk["title"], blk["level_target"],
             blk["success_criteria"], json.dumps(blk["drill_keys"]),
             "active" if i == 0 else "locked"),
        )
        for j, text in enumerate(blk["checkpoints"]):
            conn.execute(
                "INSERT INTO plan_checkpoints (block_id, cp_order, text) VALUES (?, ?, ?)",
                (bcur.lastrowid, j, text),
            )
    conn.commit()
    return _plan_payload(conn, plan_id)


@router.get("/plan")
def get_plan(user=Depends(current_user), conn=Depends(get_conn)):
    row = conn.execute(
        "SELECT id FROM plans WHERE user_id = ? AND status = 'active'", (user["id"],)
    ).fetchone()
    if not row:
        return {"plan": None}
    return {"plan": _plan_payload(conn, row["id"])}


class CheckpointToggle(BaseModel):
    done: bool


@router.put("/checkpoints/{cp_id}")
def toggle_checkpoint(cp_id: int, body: CheckpointToggle, user=Depends(current_user), conn=Depends(get_conn)):
    row = conn.execute(
        "SELECT c.id, c.block_id, b.plan_id, b.status AS block_status, p.user_id "
        "FROM plan_checkpoints c JOIN plan_blocks b ON b.id = c.block_id "
        "JOIN plans p ON p.id = b.plan_id WHERE c.id = ?", (cp_id,),
    ).fetchone()
    if not row or row["user_id"] != user["id"]:
        raise HTTPException(404, "checkpoint not found")
    if row["block_status"] == "locked":
        raise HTTPException(409, "finish the earlier block to unlock this one")

    conn.execute("UPDATE plan_checkpoints SET done = ? WHERE id = ?", (int(body.done), cp_id))

    # mastery gate: all checkpoints done -> block done, next block unlocks.
    block_id, plan_id = row["block_id"], row["plan_id"]
    remaining = conn.execute(
        "SELECT COUNT(*) AS n FROM plan_checkpoints WHERE block_id = ? AND done = 0", (block_id,)
    ).fetchone()["n"]
    unlocked_next = False
    if remaining == 0:
        conn.execute("UPDATE plan_blocks SET status = 'done' WHERE id = ?", (block_id,))
        nxt = conn.execute(
            "SELECT id FROM plan_blocks WHERE plan_id = ? AND status = 'locked' ORDER BY block_order",
            (plan_id,),
        ).fetchone()
        if nxt:
            conn.execute("UPDATE plan_blocks SET status = 'active' WHERE id = ?", (nxt["id"],))
            unlocked_next = True
    else:
        # un-checking re-opens a done block
        conn.execute(
            "UPDATE plan_blocks SET status = 'active' WHERE id = ? AND status = 'done'", (block_id,)
        )
    conn.commit()
    return {"plan": _plan_payload(conn, plan_id), "unlocked_next": unlocked_next}


# ---------------------------------------------------------------- drills & training log

@router.get("/drills")
def list_drills(skill_key: str | None = None, solo_only: bool = False,
                user=Depends(current_user), conn=Depends(get_conn)):
    profile = _profile(conn, user["id"]) or {}
    rows = [dict(r) for r in conn.execute("SELECT * FROM drills ORDER BY skill_key, level").fetchall()]
    pos = profile.get("position")
    out = []
    for d in rows:
        if skill_key and d["skill_key"] != skill_key:
            continue
        if solo_only and not d["solo"]:
            continue
        d["position_fit"] = d["positions"] == "all" or (pos in d["positions"].split(",") if pos else True)
        out.append(d)
    return {"drills": out}


class LogCreate(BaseModel):
    log_date: str | None = None            # YYYY-MM-DD, default today
    skills: list[str] = []
    drill_keys: list[str] = []
    quality: int | None = Field(default=None, ge=1, le=5)
    minutes: int | None = Field(default=None, ge=1, le=600)
    notes: str = Field(default="", max_length=2000)


@router.post("/logs")
def create_log(body: LogCreate, user=Depends(current_user), conn=Depends(get_conn)):
    when = body.log_date or date.today().isoformat()
    try:
        date.fromisoformat(when)
    except ValueError:
        raise HTTPException(422, "log_date must be YYYY-MM-DD")
    valid = {s["key"] for s in knowledge.SKILLS}
    if any(k not in valid for k in body.skills):
        raise HTTPException(422, "unknown skill in skills[]")
    cur = conn.execute(
        "INSERT INTO training_logs (user_id, log_date, skills, drill_keys, quality, minutes, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user["id"], when, json.dumps(body.skills), json.dumps(body.drill_keys),
         body.quality, body.minutes, body.notes.strip()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM training_logs WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _log_out(row)


def _log_out(row) -> dict:
    d = dict(row)
    d["skills"] = json.loads(d["skills"])
    d["drill_keys"] = json.loads(d["drill_keys"])
    return d


@router.get("/logs")
def list_logs(limit: int = 20, user=Depends(current_user), conn=Depends(get_conn)):
    rows = conn.execute(
        "SELECT * FROM training_logs WHERE user_id = ? ORDER BY log_date DESC, id DESC LIMIT ?",
        (user["id"], min(max(limit, 1), 100)),
    ).fetchall()
    return {"logs": [_log_out(r) for r in rows]}


# ---------------------------------------------------------------- progress

def _week_streak(log_dates: list[str]) -> int:
    """Consecutive ISO weeks with >= 1 session, counting back from this week
    (or last week, so a Monday doesn't read as a broken streak)."""
    weeks = set()
    for s in log_dates:
        try:
            d = date.fromisoformat(s)
        except ValueError:
            continue
        weeks.add((d.isocalendar().year, d.isocalendar().week))
    if not weeks:
        return 0
    cur = date.today()
    this_week = (cur.isocalendar().year, cur.isocalendar().week)
    if this_week not in weeks:
        cur = cur - timedelta(days=7)  # allow the streak to include only completed weeks
    streak = 0
    while (cur.isocalendar().year, cur.isocalendar().week) in weeks:
        streak += 1
        cur = cur - timedelta(days=7)
    return streak


@router.get("/progress")
def progress(user=Depends(current_user), conn=Depends(get_conn)):
    levels = _latest_levels(conn, user["id"])
    history = [dict(r) for r in conn.execute(
        "SELECT skill_key, level, source, assessed_at FROM skill_assessments "
        "WHERE user_id = ? ORDER BY assessed_at DESC, id DESC LIMIT 80", (user["id"],),
    ).fetchall()]
    log_rows = conn.execute(
        "SELECT log_date FROM training_logs WHERE user_id = ?", (user["id"],)
    ).fetchall()
    dates = [r["log_date"] for r in log_rows]
    cutoff = (date.today() - timedelta(days=28)).isoformat()
    blocks_done = conn.execute(
        "SELECT COUNT(*) AS n FROM plan_blocks b JOIN plans p ON p.id = b.plan_id "
        "WHERE p.user_id = ? AND b.status = 'done'", (user["id"],),
    ).fetchone()["n"]
    return {
        "levels": levels,
        "history": history,
        "sessions_total": len(dates),
        "sessions_28d": sum(1 for s in dates if s >= cutoff),
        "week_streak": _week_streak(dates),
        "blocks_done": blocks_done,
    }


# ---------------------------------------------------------------- AI coach

PLAYER_COACH_SYSTEM = """You are a personal volleyball coach inside a training \
app, texting directly with a youth player (middle school to high school age).

How to talk:
- NATURAL CONVERSATION. Answer what they actually asked, directly. No fixed \
formula: do NOT open every reply with praise and do NOT tack a call-to-action, \
assignment, or "your next step is…" onto every message. Only suggest something \
to do when they ask for it or it genuinely answers their question.
- Warm, specific, honest — like a coach who knows them (their real data is \
below). Encourage when there's something real to encourage.
- One idea at a time; keep it short. Ask at most one clarifying question, and \
only when you truly can't answer without it.
- DRILLS: when a drill comes up, explain it properly — what it trains, the \
setup, exactly how to do it step by step, how many reps or minutes, the ONE \
cue to think about while doing it, and what doing it well looks like. Use the \
drill library entries provided below when they match; otherwise teach the \
drill fully yourself.
- Diagnose with the error -> cause -> correction tables provided.
- THE APP has exactly these features: a plan made of skill GOALS, each with a \
short CHECKLIST to tick off, a drill library, a training log, a progress \
radar, the FILM ROOM (film a short clip of a serve, pass, set, attack, block, \
or dig and get frame-by-frame coach feedback on it), and this chat. There are \
NO quizzes, tests, badges, levels to unlock by answering questions, or any \
other features — NEVER mention or invent app features beyond that list. Call a plan unit a "goal," never a \
"block" (that word means the blocking skill). A goal's "test" is a real-court \
challenge written as the last item on its checklist, not something in the app.
- Stay on volleyball training. No medical/injury advice beyond "rest and tell \
a parent/coach or doctor". If asked something unrelated, steer back kindly.
"""


@router.get("/coach-chat/status")
def player_coach_status():
    return {"available": bool(os.getenv("ANTHROPIC_API_KEY"))}


class PlayerChatMessage(BaseModel):
    role: str
    content: str


class PlayerChat(BaseModel):
    messages: list[PlayerChatMessage]


def _mentioned_skills(text: str) -> list[str]:
    """Skills referenced in free text, by key or common words."""
    aliases = {
        "serve": ["serve", "serving", "ace", "float"],
        "passing": ["pass", "passing", "receive", "shank", "platform"],
        "setting": ["set", "setting", "setter", "hands", "double"],
        "attacking": ["hit", "hitting", "spike", "attack", "swing", "approach", "kill"],
        "blocking": ["block", "blocking", "tool"],
        "digging": ["dig", "digging", "defense", "tip"],
        "movement": ["footwork", "movement", "slow", "late"],
        "game_iq": ["rotation", "position", "read", "iq", "talk", "communicat"],
    }
    low = text.lower()
    return [k for k, words in aliases.items() if any(w in low for w in words)]


def _player_context(conn, user: dict) -> str:
    profile = _profile(conn, user["id"]) or {}
    levels = _latest_levels(conn, user["id"])
    parts = [f"Player: {user['display_name']}"]
    if profile.get("position"):
        parts.append(f"Position: {profile['position']}"
                     + (f" (secondary {profile['secondary_position']})" if profile.get("secondary_position") else "")
                     + f", level band: {profile.get('level_band', 'high_school')}")
    if levels:
        lvl = ", ".join(
            f"{next(s['name'] for s in knowledge.SKILLS if s['key'] == k)}: "
            f"{knowledge.LEVEL_NAMES[v['level']]} ({v['level']}/5)"
            for k, v in levels.items()
        )
        parts.append(f"Current self-assessed skill levels: {lvl}")

    block = conn.execute(
        "SELECT b.* FROM plan_blocks b JOIN plans p ON p.id = b.plan_id "
        "WHERE p.user_id = ? AND p.status = 'active' AND b.status = 'active' "
        "ORDER BY b.block_order LIMIT 1", (user["id"],),
    ).fetchone()
    if block:
        todo = [r["text"] for r in conn.execute(
            "SELECT text FROM plan_checkpoints WHERE block_id = ? AND done = 0 ORDER BY cp_order",
            (block["id"],),
        ).fetchall()]
        parts.append(f"Active goal: {block['title']} — done when: {block['success_criteria']}")
        if todo:
            parts.append("Still to check off: " + " | ".join(todo))

    videos = conn.execute(
        "SELECT skill_key, feedback, created_at FROM video_assessments "
        "WHERE user_id = ? ORDER BY id DESC LIMIT 2",
        (user["id"],),
    ).fetchall()
    if videos:
        parts.append("Recent Film Room video reviews (newest first):")
        for r in videos:
            fb = json.loads(r["feedback"])
            skill = next((s["name"] for s in knowledge.SKILLS if s["key"] == r["skill_key"]), r["skill_key"])
            focus = fb.get("focus") or {}
            line = f"- {str(r['created_at'])[:10]} {skill}: working on {focus.get('issue', 'form')}"
            if focus.get("cue"):
                line += f" (cue: “{focus['cue']}”)"
            parts.append(line)

    logs = conn.execute(
        "SELECT * FROM training_logs WHERE user_id = ? ORDER BY log_date DESC, id DESC LIMIT 3",
        (user["id"],),
    ).fetchall()
    if logs:
        parts.append("Recent training logs (newest first):")
        for r in logs:
            skills_txt = ", ".join(json.loads(r["skills"])) or "general"
            note = (r["notes"] or "").strip()
            note = (note[:160] + "…") if len(note) > 160 else note
            q = f", quality {r['quality']}/5" if r["quality"] else ""
            parts.append(f"- {r['log_date']}: {skills_txt}{q}" + (f" — “{note}”" if note else ""))
    return "\n".join(parts)


@router.post("/coach-chat")
def player_coach_chat(body: PlayerChat, user=Depends(current_user), conn=Depends(get_conn)):
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(503, "Coach unavailable: ANTHROPIC_API_KEY not set")
    try:
        from anthropic import Anthropic
    except ImportError:
        raise HTTPException(503, "Coach unavailable: anthropic package not installed")

    messages = [
        {"role": m.role, "content": m.content}
        for m in body.messages
        if m.content.strip() and m.role in ("user", "assistant")
    ][-12:]
    if not messages:
        raise HTTPException(422, "no message to send")

    profile = _profile(conn, user["id"]) or {}
    # ground the answer: skills from the latest question + the active block
    skill_keys = _mentioned_skills(messages[-1]["content"])
    block = conn.execute(
        "SELECT b.skill_key FROM plan_blocks b JOIN plans p ON p.id = b.plan_id "
        "WHERE p.user_id = ? AND p.status = 'active' AND b.status = 'active' LIMIT 1",
        (user["id"],),
    ).fetchone()
    if block and block["skill_key"] not in skill_keys:
        skill_keys.append(block["skill_key"])
    skill_keys = skill_keys[:3]

    system = (
        PLAYER_COACH_SYSTEM
        + "\n\n" + knowledge.practice_principles_text()
        + "\n\nThis player's data (use it — reference their real levels, plan, and logs):\n"
        + _player_context(conn, user)
    )
    snippets = knowledge.knowledge_snippets(skill_keys, profile.get("position"))
    if snippets:
        system += "\n\nCoaching knowledge to ground your advice (do not contradict it):\n" + snippets
    drills = knowledge.drill_snippets(skill_keys, profile.get("position"))
    if drills:
        system += ("\n\nDrill library entries for these skills (use these exact "
                   "drills when they fit, and expand the how-to when explaining):\n" + drills)

    model = os.getenv("CHAT_MODEL", "claude-sonnet-4-6")
    try:
        client = Anthropic(api_key=key)
        resp = client.messages.create(model=model, max_tokens=700, system=system, messages=messages)
        text = "".join(b.text for b in resp.content if b.type == "text")
    except Exception as e:
        raise HTTPException(502, f"Coach error: {e}")
    return {"reply": text}
