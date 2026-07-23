"""Coach accounts — auth for the coach-facing tool.

Same machinery as the player side (PBKDF2 password hashes, bearer session
tokens in the shared users/sessions tables), but role='coach'. Coaches OWN
teams: the whole coach API is gated (see the middleware in main.py) and
/teams is scoped to the signed-in coach.

Claiming: teams created before coach accounts existed have owner_user_id
NULL. The FIRST coach to register claims them all — right for the app's
actual history (one coach, existing data); later registrations never claim.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from .player import _hash_password, _issue_token, _verify_password, get_conn

router = APIRouter(prefix="/coach", tags=["coach"])


class CoachRegister(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6, max_length=100)
    display_name: str = Field(default="", max_length=60)


class CoachLogin(BaseModel):
    username: str
    password: str


def verify_coach_token(conn, token: str) -> dict | None:
    """Token -> coach user row, or None. Used by main.py's API gate."""
    row = conn.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token = ? AND u.role = 'coach'",
        (token,),
    ).fetchone()
    return dict(row) if row else None


def current_coach(authorization: str | None = Header(None), conn=Depends(get_conn)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "not signed in")
    user = verify_coach_token(conn, authorization.removeprefix("Bearer ").strip())
    if not user:
        raise HTTPException(401, "coach session expired — sign in again")
    return user


@router.post("/register")
def register(body: CoachRegister, conn=Depends(get_conn)):
    username = body.username.strip()
    if not username.replace("_", "").isalnum():
        raise HTTPException(422, "username: letters, numbers, and _ only")
    display = body.display_name.strip() or username
    try:
        cur = conn.execute(
            "INSERT INTO users (username, display_name, role, password_hash) VALUES (?, ?, 'coach', ?)",
            (username, display, _hash_password(body.password)),
        )
    except Exception:
        raise HTTPException(409, "that username is taken")
    user_id = cur.lastrowid

    # first coach in the door claims the pre-auth teams
    others = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'coach' AND id != ?", (user_id,)
    ).fetchone()[0]
    claimed = 0
    if others == 0:
        claimed = conn.execute(
            "UPDATE teams SET owner_user_id = ? WHERE owner_user_id IS NULL", (user_id,)
        ).rowcount

    token = _issue_token(conn, user_id)
    return {"token": token, "claimed_teams": claimed,
            "user": {"id": user_id, "username": username, "display_name": display}}


@router.post("/login")
def login(body: CoachLogin, conn=Depends(get_conn)):
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND role = 'coach'",
        (body.username.strip(),),
    ).fetchone()
    if not row or not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "wrong username or password")
    token = _issue_token(conn, row["id"])
    return {"token": token, "user": {"id": row["id"], "username": row["username"],
                                     "display_name": row["display_name"]}}


@router.post("/logout")
def logout(authorization: str | None = Header(None), conn=Depends(get_conn)):
    if authorization and authorization.startswith("Bearer "):
        conn.execute("DELETE FROM sessions WHERE token = ?",
                     (authorization.removeprefix("Bearer ").strip(),))
        conn.commit()
    return {"ok": True}


@router.get("/me")
def me(user=Depends(current_coach)):
    return {"user": {"id": user["id"], "username": user["username"],
                     "display_name": user["display_name"],
                     "theme": user.get("theme", "classic")}}


class CoachTheme(BaseModel):
    theme: str


@router.put("/theme")
def update_theme(body: CoachTheme, user=Depends(current_coach), conn=Depends(get_conn)):
    """The coach-side look follows the coach account (mirrors the player
    side's per-account theme)."""
    if body.theme not in {"classic", "intense", "sky"}:
        raise HTTPException(422, "theme must be one of ['classic', 'intense', 'sky']")
    conn.execute("UPDATE users SET theme = ? WHERE id = ?", (body.theme, user["id"]))
    conn.commit()
    return {"theme": body.theme}
