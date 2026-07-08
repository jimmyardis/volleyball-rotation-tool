"""Pure progression-plan builder for the player-side app. No I/O.

A plan is an ordered list of mastery-gated skill BLOCKS built from:
  - the player's position (drives which skills lead — spec §5 weighting)
  - their current assessed levels (weakest primary skills first)

Each block targets current_level + 1 for one skill and carries concrete
checkpoints ("do drill X in 3 sessions") plus a "you'll know you've got it
when…" success criterion, which doubles as the final checkpoint.
"""

from . import knowledge

MAX_BLOCKS = 5
LEVEL_NAMES = knowledge.LEVEL_NAMES

# Per-skill success criteria, scaled by the block's target level (2-5).
# {n}-style slots keep these honest across levels without 32 hand strings.
_SUCCESS = {
    "serve":     lambda t: f"Hit {5 + t} of 10 serves in play, including {t} to a zone you call before the toss.",
    "passing":   lambda t: f"Pass {4 + t} of 10 easy-to-medium serves to the setter spot (high, 2-3 ft off the net).",
    "setting":   lambda t: f"Deliver {4 + t} of 10 hittable high sets to zone 4 from a tossed pass, no doubles called.",
    "attacking": lambda t: f"Put {4 + t} of 10 down-balls or approaches into the court, calling your shot on {t} of them.",
    "blocking":  lambda t: f"Show {t + 2} clean block reps in a row: correct footwork, hands pressed over, balanced landing.",
    "digging":   lambda t: f"Make a playable touch on {4 + t} of 10 attacked balls, stopped and low before each contact.",
    "movement":  lambda t: f"Complete your footwork circuit {t + 1} times staying low throughout, stopped before every ball contact.",
    "game_iq":   lambda t: f"Walk all 6 rotations naming your zone, base, and job without hesitating, and make {t * 2} loud calls in one scrimmage.",
}


def _pick_drills(skill_key: str, position: str, target: int, max_drills: int = 2) -> list[dict]:
    """Choose drills for a block: match the skill, fit the position, prefer
    solo-doable (player-owned, coach-optional) and the closest entry level."""
    def fits_position(d):
        return d["positions"] == "all" or position in d["positions"].split(",")
    candidates = [d for d in knowledge.DRILLS if d["skill_key"] == skill_key and fits_position(d)]
    candidates.sort(key=lambda d: (d["level"] > target, -d["solo"], abs(d["level"] - target)))
    return candidates[:max_drills]


def _block_for(skill_key: str, position: str, current: int) -> dict:
    target = min(5, current + 1)
    name = next(s["name"] for s in knowledge.SKILLS if s["key"] == skill_key)
    drills = _pick_drills(skill_key, position, target)
    criteria = _SUCCESS[skill_key](target)

    checkpoints = []
    if drills:
        checkpoints.append(f"Do “{drills[0]['name']}” in 3 different sessions (log each one).")
    if len(drills) > 1:
        checkpoints.append(f"Do “{drills[1]['name']}” twice, beating your first session's result.")
    cue = knowledge.KNOWLEDGE[skill_key]["cues"][0]
    checkpoints.append(f"In one focused rep set, demonstrate the key cue: {cue.rstrip('.')}.")
    checkpoints.append(f"Pass the block test: {criteria}")

    return {
        "skill_key": skill_key,
        "title": f"{name} → {LEVEL_NAMES[target]}",
        "level_target": target,
        "success_criteria": criteria,
        "checkpoints": checkpoints,
        "drill_keys": [d["key"] for d in drills],
    }


def build_plan(position: str, levels: dict[str, int]) -> list[dict]:
    """Ordered blocks for a position given current skill levels (1-5).

    Primary skills (position emphasis) come first, weakest first; secondary
    skills fill remaining slots the same way. Skills already at Mastery are
    skipped. At most MAX_BLOCKS blocks — one thing at a time.
    """
    if position not in knowledge.POSITION_EMPHASIS:
        raise ValueError(f"unknown position {position!r}")
    emphasis = knowledge.POSITION_EMPHASIS[position]
    lvl = lambda k: levels.get(k, 1)

    ordered: list[str] = []
    for group in (emphasis["primary"], emphasis["secondary"]):
        ordered.extend(sorted((k for k in group if lvl(k) < 5), key=lvl))

    # Never return an empty plan. A player who self-rates everything at
    # Mastery (kids max the sliders) gets PROVE-IT blocks: their primary
    # skills held at level 5 under the hardest success criteria. Without
    # this, onboarding ends with no plan and no way forward.
    if not ordered:
        ordered = list(emphasis["primary"])

    return [_block_for(k, position, lvl(k)) for k in ordered[:MAX_BLOCKS]]
