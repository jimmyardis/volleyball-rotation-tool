"""Deterministic serve-form metrics from MediaPipe pose landmarks.

The browser runs MediaPipe's pose landmarker on the player's clip locally and
sends only the landmark series (33 points per sampled frame, normalized image
coordinates, y grows downward). This module is the quantitative half of the
Film Room serve assessment: pure Python, no ML, fully unit-testable.

Thresholds are coach-accepted approximations for youth players (full arm
extension at contact, visible leg load), not biomechanics-lab precision — the
qualitative labels say "about", and the vision model gets them clearly marked
as measured beta metrics.
"""

from __future__ import annotations

import math

# MediaPipe Pose landmark indices (subset we use).
NOSE = 0
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

_MIN_VIS = 0.5          # landmark visibility below this = don't trust the point
_MIN_FRAMES = 8         # fewer usable frames than this = refuse to measure
_WINDUP_WINDOW_S = 1.2  # how far before contact we look for the leg load


def _pt(frame: dict, idx: int) -> list[float] | None:
    """[x, y, z, visibility] for one landmark, or None if not trustworthy."""
    lm = frame["lm"]
    if idx >= len(lm):
        return None
    p = lm[idx]
    if len(p) >= 4 and p[3] < _MIN_VIS:
        return None
    return p


def _angle_deg(a, b, c) -> float:
    """Angle at vertex b (degrees) in image plane — e.g. elbow angle from
    shoulder-elbow-wrist."""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cos))


def _mid(p1, p2) -> tuple[float, float]:
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def _torso_len(frame: dict) -> float | None:
    ls, rs = _pt(frame, L_SHOULDER), _pt(frame, R_SHOULDER)
    lh, rh = _pt(frame, L_HIP), _pt(frame, R_HIP)
    if not all((ls, rs, lh, rh)):
        return None
    s, h = _mid(ls, rs), _mid(lh, rh)
    return math.hypot(s[0] - h[0], s[1] - h[1])


def _label(value: float | None, bands: list[tuple[float, str]], fallback: str) -> str:
    """First band whose threshold the value meets (bands ordered best-first)."""
    if value is None:
        return fallback
    for threshold, text in bands:
        if value >= threshold:
            return text
    return fallback


def compute_serve_metrics(pose_frames: list[dict]) -> dict:
    """pose_frames: [{"t": seconds, "lm": [[x, y, z, visibility] * 33]}, ...]

    Returns {"ok": False, "reason": ...} when the clip can't be measured, else
    {"ok": True, ...metrics with numbers + plain-language labels...}.
    """
    arm_sets = {
        "left": (L_SHOULDER, L_ELBOW, L_WRIST),
        "right": (R_SHOULDER, R_ELBOW, R_WRIST),
    }
    usable = [
        f for f in pose_frames
        if _pt(f, NOSE) and _torso_len(f)
        and any(all(_pt(f, i) for i in ids) for ids in arm_sets.values())
    ]
    if len(usable) < _MIN_FRAMES:
        return {"ok": False,
                "reason": "not enough of your body was visible — film again with "
                          "your whole body (feet to hands at full reach) in frame"}

    # Hitting arm = the wrist that gets highest (smallest y) anywhere in the clip.
    best: dict | None = None
    for side, (s_i, e_i, w_i) in arm_sets.items():
        for f in usable:
            pts = [_pt(f, i) for i in (s_i, e_i, w_i)]
            if not all(pts):
                continue
            if best is None or pts[2][1] < best["wrist"][1]:
                best = {"side": side, "frame": f, "shoulder": pts[0],
                        "elbow": pts[1], "wrist": pts[2]}
    if best is None:
        return {"ok": False, "reason": "couldn't track your hitting arm — try "
                                       "filming from your hitting-arm side"}

    contact = best["frame"]
    torso = _torso_len(contact) or 1e-6
    elbow_deg = _angle_deg(best["shoulder"], best["elbow"], best["wrist"])
    # Contact height in torso-lengths above the nose (y grows downward).
    height_ratio = (_pt(contact, NOSE)[1] - best["wrist"][1]) / torso

    # Leg load: deepest knee bend in the windup window before contact.
    knee_min: float | None = None
    t_contact = contact["t"]
    windup = [f for f in usable if t_contact - _WINDUP_WINDOW_S <= f["t"] <= t_contact]
    for f in windup:
        for h_i, k_i, a_i in ((L_HIP, L_KNEE, L_ANKLE), (R_HIP, R_KNEE, R_ANKLE)):
            pts = [_pt(f, i) for i in (h_i, k_i, a_i)]
            if all(pts):
                ang = _angle_deg(*pts)
                knee_min = ang if knee_min is None else min(knee_min, ang)

    # Weight transfer: reported as detected / not detected only — no published
    # magnitudes exist, so we just check whether the hip midpoint moved
    # horizontally during the windup by a meaningful fraction of torso length.
    step_detected: bool | None = None
    hips = [(f, _pt(f, L_HIP), _pt(f, R_HIP)) for f in windup]
    hips = [(f, _mid(lh, rh)) for f, lh, rh in hips if lh and rh]
    if len(hips) >= 3:
        xs = [h[1][0] for h in hips]
        step_detected = (max(xs) - min(xs)) / torso >= 0.15

    return {
        "ok": True,
        "hitting_side": best["side"],
        "contact_t": round(t_contact, 2),
        # Bands follow Reeser et al. 2010 ("extended at the elbow" at contact)
        # via coach-accepted cutoffs: >=160 near-full, 140-160 partial, <140 bent.
        "elbow_extension_deg": round(elbow_deg, 1),
        "elbow_label": _label(elbow_deg, [
            (160, "full arm extension at contact — great"),
            (140, "arm slightly bent at contact — reach a touch higher"),
        ], "arm clearly bent at contact — contact should happen at full reach"),
        "contact_height_ratio": round(height_ratio, 2),
        "contact_height_label": _label(height_ratio, [
            (0.6, "contact point high above your head — great"),
            (0.3, "contact a bit low — let the toss peak and reach up longer"),
        ], "contact well below full reach — toss higher and hit at the top"),
        "knee_min_deg": round(knee_min, 1) if knee_min is not None else None,
        "knee_label": (
            "legs not visible enough to judge leg drive" if knee_min is None else
            _label(-knee_min, [
                (-125, "good knee bend in the windup — legs are helping"),
                (-150, "some knee bend — try loading the legs a little more"),
            ], "legs mostly straight — bend the knees and drive up through the serve")
        ),
        "step_detected": step_detected,
        "step_label": (
            "couldn't judge the step/weight transfer" if step_detected is None else
            "body moved through the serve — weight transfer detected" if step_detected else
            "little body movement before contact — step into the serve, back foot to front"
        ),
    }


def summarize_for_prompt(metrics: dict) -> str:
    """Plain-text block the vision model receives alongside the frames."""
    if not metrics.get("ok"):
        return f"Pose tracking failed on this clip: {metrics.get('reason', 'unknown')}."
    lines = [
        "Measured pose metrics (beta — computed from MediaPipe landmarks, treat as approximate):",
        f"- Hitting arm: {metrics['hitting_side']}",
        f"- Elbow angle at contact: {metrics['elbow_extension_deg']}° ({metrics['elbow_label']})",
        f"- Contact height: {metrics['contact_height_ratio']} torso-lengths above head level ({metrics['contact_height_label']})",
    ]
    if metrics.get("knee_min_deg") is not None:
        lines.append(f"- Deepest knee bend before contact: {metrics['knee_min_deg']}° ({metrics['knee_label']})")
    else:
        lines.append(f"- Leg drive: {metrics['knee_label']}")
    lines.append(f"- Step/weight transfer: {metrics['step_label']}")
    return "\n".join(lines)
