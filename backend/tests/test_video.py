"""Film Room tests: deterministic serve metrics from synthetic landmarks, and
the video-assessment endpoints with the vision call stubbed out. NO paid
Claude calls anywhere.
"""

import base64
import json

import pytest
from fastapi.testclient import TestClient

from app import serve_metrics


# ---------------------------------------------------------------- fixtures

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VB_DB_PATH", str(tmp_path / "test.db"))
    from app import db, main
    monkeypatch.setattr(main, "DB_PATH", db.resolve_db_path())
    conn = db.connect(db.resolve_db_path())
    db.init_db(conn)
    conn.close()
    return TestClient(main.app)


@pytest.fixture()
def auth(client):
    r = client.post("/player/register", json={"username": "vidkid", "password": "spike123"})
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.put("/player/profile", headers=headers, json={"position": "OH"})
    return headers


# ---------------------------------------------------------------- landmark builders

def _blank_lm():
    """33 landmarks, all visible, at a neutral standing pose."""
    lm = [[0.5, 0.5, 0.0, 0.9] for _ in range(33)]
    lm[serve_metrics.NOSE] = [0.5, 0.30, 0, 0.9]
    lm[serve_metrics.L_SHOULDER] = [0.45, 0.40, 0, 0.9]
    lm[serve_metrics.R_SHOULDER] = [0.55, 0.40, 0, 0.9]
    lm[serve_metrics.L_ELBOW] = [0.43, 0.50, 0, 0.9]
    lm[serve_metrics.R_ELBOW] = [0.57, 0.50, 0, 0.9]
    lm[serve_metrics.L_WRIST] = [0.42, 0.58, 0, 0.9]
    lm[serve_metrics.R_WRIST] = [0.58, 0.58, 0, 0.9]
    lm[serve_metrics.L_HIP] = [0.46, 0.60, 0, 0.9]
    lm[serve_metrics.R_HIP] = [0.54, 0.60, 0, 0.9]
    lm[serve_metrics.L_KNEE] = [0.46, 0.75, 0, 0.9]
    lm[serve_metrics.R_KNEE] = [0.54, 0.75, 0, 0.9]
    lm[serve_metrics.L_ANKLE] = [0.46, 0.90, 0, 0.9]
    lm[serve_metrics.R_ANKLE] = [0.54, 0.90, 0, 0.9]
    return lm


def _serve_clip(contact_elbow_bend=0.0, hips_step=0.0):
    """10-frame synthetic right-handed serve: wrist rises to full extension
    above the head at the final frame. contact_elbow_bend shifts the elbow
    x-position at contact to bend the measured angle; hips_step drifts the
    hip midpoint across the windup (weight transfer)."""
    frames = []
    for i in range(10):
        lm = _blank_lm()
        f = i / 9.0
        # right arm rises: wrist from 0.58 down to well above the nose
        lm[serve_metrics.R_WRIST] = [0.55, 0.58 - 0.44 * f, 0, 0.9]
        lm[serve_metrics.R_ELBOW] = [0.55 + contact_elbow_bend * f, 0.50 - 0.21 * f, 0, 0.9]
        lm[serve_metrics.R_SHOULDER] = [0.55, 0.40, 0, 0.9]
        if hips_step:
            for idx in (serve_metrics.L_HIP, serve_metrics.R_HIP):
                lm[idx][0] += hips_step * f
        frames.append({"t": i * 0.1, "lm": lm})
    return frames


# ---------------------------------------------------------------- metric tests

def test_straight_arm_serve_metrics():
    m = serve_metrics.compute_serve_metrics(_serve_clip(hips_step=0.06))
    assert m["ok"] is True
    assert m["hitting_side"] == "right"
    assert m["contact_t"] == 0.9
    assert m["elbow_extension_deg"] >= 160          # collinear arm
    assert "full arm extension" in m["elbow_label"]
    assert m["contact_height_ratio"] > 0.6          # wrist well above the nose
    assert "high above your head" in m["contact_height_label"]
    assert m["step_detected"] is True


def test_bent_arm_and_no_step_flagged():
    m = serve_metrics.compute_serve_metrics(_serve_clip(contact_elbow_bend=0.12))
    assert m["ok"] is True
    assert m["elbow_extension_deg"] < 140
    assert "clearly bent" in m["elbow_label"]
    assert m["step_detected"] is False
    # straight legs in the synthetic clip -> flagged
    assert "legs mostly straight" in m["knee_label"]


def test_too_few_frames_refuses():
    m = serve_metrics.compute_serve_metrics(_serve_clip()[:4])
    assert m["ok"] is False
    assert "whole body" in m["reason"]


def test_low_visibility_frames_ignored():
    frames = _serve_clip()
    for fr in frames:
        for p in fr["lm"]:
            p[3] = 0.1                              # nothing trustworthy
    m = serve_metrics.compute_serve_metrics(frames)
    assert m["ok"] is False


def test_prompt_summary_mentions_all_metrics():
    m = serve_metrics.compute_serve_metrics(_serve_clip(hips_step=0.06))
    text = serve_metrics.summarize_for_prompt(m)
    assert "Elbow angle" in text and "Contact height" in text and "weight transfer" in text


# ---------------------------------------------------------------- endpoint tests

FAKE_JPEG = base64.b64encode(b"\xff\xd8\xff\xe0" + b"x" * 400).decode()

CANNED_FEEDBACK = {
    "summary": "Nice rhythm overall — your toss is steady and you finish balanced.",
    "strengths": ["Consistent low toss", "Balanced finish"],
    "focus": {"issue": "Bent elbow at contact", "why": "Frames 6-8 show contact below full reach",
              "fix": "Reach tall — contact at full extension", "cue": "High five the ceiling"},
    "checkpoints": [{"name": "Toss placement", "verdict": "good", "note": "In front of the shoulder."},
                    {"name": "Contact point", "verdict": "needs_work", "note": "Elbow bent at contact."}],
    "drill_keys": ["toss-towel", "not-a-real-drill"],
    "confidence_note": "Side view, whole body visible.",
}


def test_video_assessment_flow(client, auth, monkeypatch):
    from app import video_assess
    monkeypatch.setattr(video_assess, "_call_model",
                        lambda system, content: json.dumps(CANNED_FEEDBACK))

    # invalid skill and invalid frames rejected
    assert client.post("/player/video-assessments", headers=auth,
                       json={"skill_key": "game_iq", "frames": [FAKE_JPEG] * 3}).status_code == 422
    assert client.post("/player/video-assessments", headers=auth,
                       json={"skill_key": "serve", "frames": ["not-base64!!"] * 3}).status_code == 422

    body = {"skill_key": "serve", "frames": [FAKE_JPEG] * 5,
            "timestamps": [0.0, 0.5, 1.0, 1.5, 2.0], "duration_s": 2.5,
            "pose_frames": _serve_clip(hips_step=0.06)}
    r = client.post("/player/video-assessments", headers=auth, json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["skill_key"] == "serve"
    assert out["feedback"]["focus"]["cue"] == "High five the ceiling"
    # unknown drill filtered, real one resolved to a full entry
    assert out["feedback"]["drill_keys"] == ["toss-towel"]
    assert out["drills"][0]["key"] == "toss-towel"
    # pose metrics computed and stored
    assert out["metrics"]["ok"] is True and out["metrics"]["hitting_side"] == "right"

    hist = client.get("/player/video-assessments", headers=auth).json()["assessments"]
    assert len(hist) == 1 and hist[0]["id"] == out["id"]

    # the chat coach's context now knows about the review
    from app import db, player
    conn = db.connect(db.resolve_db_path())
    user = dict(conn.execute("SELECT * FROM users").fetchone())
    ctx = player._player_context(conn, user)
    conn.close()
    assert "Film Room" in ctx and "Bent elbow at contact" in ctx


def test_video_config(client, auth):
    cfg = client.get("/player/video-assessments/config", headers=auth).json()
    keys = [s["key"] for s in cfg["skills"]]
    assert keys == ["serve", "passing", "setting", "attacking", "blocking", "digging"]
    serve = cfg["skills"][0]
    assert serve["pose_metrics"] is True and "Side view" in serve["camera"]
    assert all(s["camera"] for s in cfg["skills"])


def test_video_requires_auth(client):
    r = client.post("/player/video-assessments",
                    json={"skill_key": "serve", "frames": [FAKE_JPEG] * 3})
    assert r.status_code == 401


def test_feedback_parser_tolerates_fences():
    from app.video_assess import _parse_feedback
    fenced = "```json\n" + json.dumps(CANNED_FEEDBACK) + "\n```"
    assert _parse_feedback(fenced)["summary"].startswith("Nice rhythm")
    with pytest.raises(ValueError):
        _parse_feedback("no json here")
