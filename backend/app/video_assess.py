"""Film Room: video assessment for the player side.

Privacy-first pipeline — the raw clip NEVER reaches the server. The browser
samples ~10 JPEG frames from the player's video (and, for serves, runs
MediaPipe pose landmarking locally); this router receives frames + landmarks,
computes deterministic serve metrics (serve_metrics.py), and asks a vision
model for coaching feedback grounded in the Film Room rubric + knowledge
base + the player's real data. Only the structured feedback row is stored.
"""

from __future__ import annotations

import base64
import json
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import knowledge, serve_metrics
from .player import _mentioned_skills  # noqa: F401  (re-exported context helpers)
from .player import _player_context, current_user, get_conn

router = APIRouter(prefix="/player/video-assessments", tags=["player"])

VIDEO_SKILLS = ["serve", "passing", "setting", "attacking", "blocking", "digging"]
POSE_METRIC_SKILLS = ["serve"]        # skills with deterministic landmark metrics
MAX_FRAMES = 16
MAX_FRAME_BYTES = 400_000             # per decoded frame (~downscaled JPEG)
MAX_TOTAL_BYTES = 3_000_000


VIDEO_REVIEW_SYSTEM = """You are a volleyball coach reviewing a short video of \
a youth player (middle school to high school age) performing one skill rep. \
You are looking at frames sampled evenly across their clip, in time order.

How to review:
- Work through the rubric checkpoints below phase by phase against what you \
can actually SEE in the frames. Never invent details the frames don't show; \
if a checkpoint isn't visible (camera angle, cropping, blur), mark it \
"cant_tell" rather than guessing.
- Youth-appropriate tone: warm, specific, honest. Name what's genuinely good \
before what needs work. No empty praise.
- Pick exactly ONE primary fix — the highest-leverage correction, the thing a \
coach would fix first because other faults flow from it. One cue, not five.
- When measured pose metrics are provided, treat them as approximate \
supporting evidence; if they contradict what you see, trust your eyes and \
say so briefly.
- Recommend drills ONLY from the drill library entries provided, by their \
exact key. 1-3 drills that target the primary fix.

Respond with ONLY a JSON object (no markdown fences, no prose outside it):
{
  "summary": "2-3 sentences, spoken like a coach, covering the overall rep",
  "strengths": ["specific thing done well", "another (1-3 items)"],
  "focus": {
    "issue": "the ONE primary fix, named plainly",
    "why": "what in the frames shows it, and what it costs them",
    "fix": "how to correct it, concretely",
    "cue": "the one short cue to think about next rep"
  },
  "checkpoints": [
    {"name": "rubric checkpoint name", "verdict": "good" | "needs_work" | "cant_tell", "note": "one short sentence"}
  ],
  "drill_keys": ["exact-drill-key"],
  "confidence_note": "one sentence on camera angle / visibility limits, or empty string"
}"""


class PoseFrame(BaseModel):
    t: float = Field(ge=0)
    lm: list[list[float]]


class VideoSubmit(BaseModel):
    skill_key: str
    frames: list[str] = Field(min_length=3, max_length=MAX_FRAMES)  # base64 JPEG
    timestamps: list[float] = []          # seconds, parallel to frames (optional)
    duration_s: float | None = Field(default=None, ge=0, le=120)
    pose_frames: list[PoseFrame] | None = None
    note: str = Field(default="", max_length=300)  # optional player context


@router.get("/config")
def config():
    """What the Film Room UI needs: reviewable skills + filming guidance."""
    return {
        "available": bool(os.getenv("ANTHROPIC_API_KEY")),
        "skills": [
            {
                "key": k,
                "name": next(s["name"] for s in knowledge.SKILLS if s["key"] == k),
                "camera": knowledge.VIDEO_RUBRICS[k]["camera"],
                "pose_metrics": k in POSE_METRIC_SKILLS,
            }
            for k in VIDEO_SKILLS
        ],
        "max_frames": MAX_FRAMES,
    }


def _decode_frames(frames: list[str]) -> list[str]:
    """Validate base64 JPEG payloads (tolerating data: URLs); return clean b64."""
    out, total = [], 0
    for i, f in enumerate(frames):
        b64 = f.split(",", 1)[1] if f.startswith("data:") else f
        try:
            raw = base64.b64decode(b64, validate=True)
        except Exception:
            raise HTTPException(422, f"frame {i + 1} is not valid base64")
        if not raw.startswith(b"\xff\xd8"):
            raise HTTPException(422, f"frame {i + 1} is not a JPEG")
        if len(raw) > MAX_FRAME_BYTES:
            raise HTTPException(422, f"frame {i + 1} is too large — downscale before upload")
        total += len(raw)
        out.append(b64)
    if total > MAX_TOTAL_BYTES:
        raise HTTPException(422, "clip frames too large in total — use a shorter clip")
    return out


def _call_model(system: str, content: list[dict]) -> str:
    """One vision call; separated so tests can stub it."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(503, "Film Room unavailable: ANTHROPIC_API_KEY not set")
    try:
        from anthropic import Anthropic
    except ImportError:
        raise HTTPException(503, "Film Room unavailable: anthropic package not installed")
    model = os.getenv("VIDEO_MODEL") or os.getenv("CHAT_MODEL", "claude-sonnet-4-6")
    client = Anthropic(api_key=key)
    resp = client.messages.create(
        model=model, max_tokens=1500, system=system,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def _parse_feedback(text: str) -> dict:
    """Parse the model's JSON, tolerating stray fences/prose around it."""
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        s = s.split("\n", 1)[1] if "\n" in s else s
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model reply")
    fb = json.loads(s[start:end + 1])
    for field in ("summary", "focus", "checkpoints"):
        if field not in fb:
            raise ValueError(f"feedback missing {field!r}")
    return fb


@router.post("")
def create(body: VideoSubmit, user=Depends(current_user), conn=Depends(get_conn)):
    if body.skill_key not in VIDEO_SKILLS:
        raise HTTPException(422, f"skill_key must be one of {VIDEO_SKILLS}")
    frames = _decode_frames(body.frames)

    # Deterministic pose metrics (serve only, when the browser sent landmarks).
    metrics = None
    if body.skill_key in POSE_METRIC_SKILLS and body.pose_frames:
        metrics = serve_metrics.compute_serve_metrics(
            [{"t": p.t, "lm": p.lm} for p in body.pose_frames]
        )

    profile_row = conn.execute(
        "SELECT position FROM player_profiles WHERE user_id = ?", (user["id"],)
    ).fetchone()
    position = profile_row["position"] if profile_row else None

    skill_name = next(s["name"] for s in knowledge.SKILLS if s["key"] == body.skill_key)
    system = (
        VIDEO_REVIEW_SYSTEM
        + "\n\n" + knowledge.practice_principles_text()
        + f"\n\nSkill under review: {skill_name}."
        + "\n\n" + knowledge.video_rubric_text(body.skill_key)
        + "\n\nCoaching knowledge (ground your diagnosis in this):\n"
        + knowledge.knowledge_snippets([body.skill_key], position)
        + "\n\nDrill library for recommendations (recommend by exact key in quotes):\n"
        + _drill_catalog(body.skill_key, position)
        + "\n\nThis player's data:\n" + _player_context(conn, user)
    )

    content: list[dict] = [{
        "type": "text",
        "text": f"{len(frames)} frames sampled in time order from a "
                f"{body.duration_s or 'short'}{'s' if body.duration_s else ''} clip"
                + (f". Player's note: {body.note.strip()}" if body.note.strip() else "."),
    }]
    for i, b64 in enumerate(frames):
        t = body.timestamps[i] if i < len(body.timestamps) else None
        content.append({"type": "text",
                        "text": f"Frame {i + 1}/{len(frames)}" + (f" (t={t:.1f}s)" if t is not None else "")})
        content.append({"type": "image",
                        "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}})
    if metrics:
        content.append({"type": "text", "text": serve_metrics.summarize_for_prompt(metrics)})

    try:
        reply = _call_model(system, content)
        feedback = _parse_feedback(reply)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Film Room error: {e}")

    # Only recommend drills that actually exist in the library.
    valid_keys = {d["key"] for d in knowledge.DRILLS}
    feedback["drill_keys"] = [k for k in feedback.get("drill_keys", []) if k in valid_keys]

    cur = conn.execute(
        "INSERT INTO video_assessments (user_id, skill_key, metrics, feedback) VALUES (?, ?, ?, ?)",
        (user["id"], body.skill_key,
         json.dumps(metrics) if metrics else None, json.dumps(feedback)),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM video_assessments WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _out(row, conn)


def _drill_catalog(skill_key: str, position: str | None) -> str:
    text = knowledge.drill_snippets([skill_key], position, max_drills=8)
    keys = [d["key"] for d in knowledge.DRILLS if d["skill_key"] == skill_key]
    return text + "\n(Their exact keys, in library order: " + ", ".join(f'"{k}"' for k in keys) + ")"


def _out(row, conn) -> dict:
    d = dict(row)
    d["metrics"] = json.loads(d["metrics"]) if d["metrics"] else None
    d["feedback"] = json.loads(d["feedback"])
    # resolve recommended drills to full entries for the UI
    keys = d["feedback"].get("drill_keys", [])
    if keys:
        marks = ",".join("?" for _ in keys)
        d["drills"] = [dict(r) for r in conn.execute(
            f"SELECT * FROM drills WHERE key IN ({marks})", keys).fetchall()]
    else:
        d["drills"] = []
    d["skill_name"] = next((s["name"] for s in knowledge.SKILLS if s["key"] == d["skill_key"]), d["skill_key"])
    return d


@router.get("")
def history(limit: int = 10, user=Depends(current_user), conn=Depends(get_conn)):
    rows = conn.execute(
        "SELECT * FROM video_assessments WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user["id"], min(max(limit, 1), 50)),
    ).fetchall()
    return {"assessments": [_out(r, conn) for r in rows]}
