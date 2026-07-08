"""Curated volleyball knowledge base for the player-side app.

This module is the MVP stand-in for the spec's RAG store: a small, structured,
hand-curated corpus. It grounds the AI coach (error -> cause -> correction
tables, cues, position guidance) and seeds the drill library. When the corpus
outgrows a module, it can move to embeddings without changing callers.
"""

# The 8-skill taxonomy (spec §5): six fundamentals + movement + game IQ.
SKILLS = [
    {"key": "serve",     "name": "Serving"},
    {"key": "passing",   "name": "Serve-Receive / Passing"},
    {"key": "setting",   "name": "Setting"},
    {"key": "attacking", "name": "Attacking / Spiking"},
    {"key": "blocking",  "name": "Blocking"},
    {"key": "digging",   "name": "Digging / Defense"},
    {"key": "movement",  "name": "Movement / Footwork"},
    {"key": "game_iq",   "name": "Game IQ"},
]

LEVEL_NAMES = {1: "Foundation", 2: "Developing", 3: "Proficient", 4: "Advanced", 5: "Mastery"}

# Position weighting (spec §5): which skills a plan emphasizes, in order.
# primary skills come first in the plan; shared fundamentals fill the rest.
POSITION_EMPHASIS = {
    "S":   {"primary": ["setting", "game_iq", "serve"],            "secondary": ["blocking", "digging", "movement"]},
    "OH":  {"primary": ["attacking", "passing", "serve"],          "secondary": ["digging", "blocking", "movement"]},
    "OPP": {"primary": ["attacking", "blocking", "serve"],         "secondary": ["digging", "setting", "movement"]},
    "MB":  {"primary": ["blocking", "attacking", "movement"],      "secondary": ["serve", "game_iq", "digging"]},
    "L":   {"primary": ["passing", "digging", "movement"],         "secondary": ["setting", "game_iq", "serve"]},
    "DS":  {"primary": ["passing", "digging", "serve"],            "secondary": ["movement", "game_iq", "setting"]},
}

# Per-skill coaching knowledge: key cues + error -> likely cause -> correction.
# This structure is exactly what the AI coach uses to diagnose (spec §5).
KNOWLEDGE = {
    "serve": {
        "cues": [
            "Consistent toss: same height, slightly in front of the hitting shoulder, every time.",
            "Contact the ball at full extension with a firm, open hand.",
            "Weight transfers from back foot to front foot through contact.",
            "Pick a target zone BEFORE the toss; serve routines beat serve hopes.",
        ],
        "errors": [
            {"error": "serve into the net",
             "cause": "toss too low or too far in front; contact point drops",
             "fix": "raise the toss so contact happens at full arm extension; freeze the follow-through toward the target"},
            {"error": "serve sails long",
             "cause": "contact under the ball with an open palm scooping upward",
             "fix": "contact the back-middle of the ball with a flat hand and snap the wrist; finish shorter"},
            {"error": "no consistency serve to serve",
             "cause": "toss varies each attempt",
             "fix": "drill the toss alone: 10 tosses that land on a towel placed at your front foot before hitting again"},
            {"error": "float serve doesn't float",
             "cause": "wrist snaps or fingers wrap the ball, adding spin",
             "fix": "stiff wrist, contact dead-center with the heel of the hand, abrupt stop on follow-through"},
        ],
    },
    "passing": {
        "cues": [
            "Beat the ball to the spot — move first, then pass; platform comes late.",
            "Face the server, angle the platform to the target.",
            "Ball contacts the forearms, not the hands; shrug the shoulders, don't swing.",
            "Call it early and loud: 'mine' before the ball crosses the net.",
        ],
        "errors": [
            {"error": "pass flies over your head / off the court",
             "cause": "swinging the arms instead of angling a still platform",
             "fix": "quiet arms: platform set before contact, legs provide the power; finish with hands below shoulders"},
            {"error": "shanked passes off the side",
             "cause": "late feet — reaching for the ball beside the body",
             "fix": "footwork first: shuffle so the ball is centered between your knees at contact"},
            {"error": "passes too low/tight to the net",
             "cause": "platform angle too flat toward the net",
             "fix": "drop the inside shoulder and aim the platform at the setter's target spot, 2-3 ft off the net"},
        ],
    },
    "setting": {
        "cues": [
            "Square shoulders and hips to the target (zone 4 unless setting elsewhere).",
            "Ball-shaped hands above the forehead; contact all ten fingers.",
            "Extend arms AND legs together — finish tall, wrists to the target.",
            "Tempo is a decision: know the set (high, quick, back) before the pass arrives.",
        ],
        "errors": [
            {"error": "double contact called",
             "cause": "hands uneven — one hand contacts before the other",
             "fix": "shape the ball early: hands up and formed before the ball arrives; catch-and-release drills with a heavier ball"},
            {"error": "sets drift tight to the net",
             "cause": "setting on the move, momentum carrying toward the net",
             "fix": "beat the pass to the spot and stop; square up before contact"},
            {"error": "quick sets mistimed with the middle",
             "cause": "tempo mismatch — setter and hitter disagree on when the ball leaves",
             "fix": "reps with just the MB: hitter jumps as the pass hits the setter's hands; talk every rep"},
        ],
    },
    "attacking": {
        "cues": [
            "Approach rhythm: slow-to-fast; last two steps are the biggest (left-RIGHT-LEFT for righties).",
            "Both arms swing back, then UP — high elbow, hand above the ear.",
            "Contact high and in front; snap the wrist over the ball.",
            "See the block before you swing: line, angle, tool, or tip is a choice.",
        ],
        "errors": [
            {"error": "hitting into the net",
             "cause": "ball drifted behind the head — late or under the set",
             "fix": "start the approach later than feels natural; contact point stays in front of the hitting shoulder"},
            {"error": "no power on the swing",
             "cause": "no arm backswing / jumping off the wrong footwork",
             "fix": "wall-swing progression: footwork only, then footwork + arm swing, then against a wall, then live"},
            {"error": "always hitting the same shot",
             "cause": "predictable — eyes never leave the ball",
             "fix": "peek at the block during the approach; call your shot out loud in practice reps"},
        ],
    },
    "blocking": {
        "cues": [
            "Start in a loaded stance, hands at shoulder height, eyes on the hitter (ball-setter-ball-hitter).",
            "Penetrate: press hands OVER the net into their space, don't swat down.",
            "Seal the line or the angle — a block that takes away one shot is a good block.",
            "Land balanced, turn, and be ready to transition to attack.",
        ],
        "errors": [
            {"error": "getting tooled off the hands",
             "cause": "reaching sideways with soft, separated hands",
             "fix": "firm hands and thumbs up, pike over the net; take your hands down on balls clearly outside your block"},
            {"error": "late to the pin on quick sets",
             "cause": "watching the ball instead of reading the setter",
             "fix": "eye-sequence drill: ball-setter-ball-hitter; leave with the setter's release, not the set's peak"},
            {"error": "netting on the block",
             "cause": "jumping forward into the net instead of straight up",
             "fix": "block from a chair drill / jump touches with a vertical marker; chest stays behind the hands"},
        ],
    },
    "digging": {
        "cues": [
            "Stopped and low BEFORE the attacker contacts — read, don't guess.",
            "Weight forward, platform ready but relaxed; dig with legs and angles.",
            "Take the ball high and behind the attacker's power line.",
            "Every dig has a target: middle of the court, high, off the net.",
        ],
        "errors": [
            {"error": "hard-driven balls blow through the platform",
             "cause": "standing tall — no time to get under the ball",
             "fix": "be stopped in a low base at attacker contact; absorb with a slight platform give"},
            {"error": "digs go straight back over the net",
             "cause": "platform flat / facing the attacker",
             "fix": "angle the platform up and toward the middle; cushion the ball, aim 10 ft high"},
            {"error": "frozen on tips and roll shots",
             "cause": "anticipating the hard swing only",
             "fix": "read the hitter's shoulder drop / open hand; first step forward is the default on a broken play"},
        ],
    },
    "movement": {
        "cues": [
            "Athletic base everywhere: knees bent, weight on the balls of the feet.",
            "Shuffle for short distances, crossover-run for long ones — never backpedal for a ball.",
            "Stop BEFORE you play the ball; play from a still base.",
            "Footwork patterns (approach, block shuffle, transition off the net) deserve their own reps.",
        ],
        "errors": [
            {"error": "always a step late to the ball",
             "cause": "watching outcomes instead of moving on cues; standing base too tall",
             "fix": "reaction footwork drills; move on the opponent's contact, not the ball's flight"},
            {"error": "off-balance at contact",
             "cause": "playing the ball while still moving",
             "fix": "'feet then ball': exaggerate the stop in drills — freeze one beat before every contact"},
        ],
    },
    "game_iq": {
        "cues": [
            "Know the rotation: where's the setter, who's front row, what's my base and my job right now?",
            "Talk constantly: 'in/out', 'tip', 'line's open', 'two blockers' — information wins rallies.",
            "Watch the opponent between points: their best hitter, their server's pattern, the open seam.",
            "Next-play mindset: the previous point is over the moment it ends.",
        ],
        "errors": [
            {"error": "caught out of position between plays",
             "cause": "not resetting to base after each contact",
             "fix": "call your base out loud in scrimmages until it's automatic"},
            {"error": "silent on the court",
             "cause": "unsure what to say or afraid of being wrong",
             "fix": "start with the two freebies: call 'mine' on every ball you take and 'out/in' on every serve"},
        ],
    },
}

# Position guidance the coach can cite (spec §5 emphasis table, in prose).
POSITION_GUIDE = {
    "S":   "Setters run the offense: hands and footwork tempo come first, then decision-making — who's hot, what's the matchup, when to dump. A back-row setter must also defend right back and still get to every second ball.",
    "OH":  "Outside hitters are the all-phase players: they take the most swings AND the most serve-receive. Passing consistency is what keeps an OH on the floor; attacking range (line, angle, high hands, off-speed) is what wins points.",
    "OPP": "Opposites anchor the right side: attacking against the opponent's best blocker and blocking the opponent's OH. Big block presence + back-row attack range set great opposites apart.",
    "MB":  "Middles live at the net: lateral block footwork and quick-tempo attacking in front of and behind the setter. Reading the setter early is the difference between closing a block and waving at it.",
    "L":   "Liberos own the back court: serve-receive and digging are the job, ball-control everything. By rule a libero never attacks above the net or blocks — the plan weights passing, digging, movement, and communication instead.",
    "DS":  "Defensive specialists bring serving and back-row defense off the bench: elite passing and digging plus a reliable (ideally aggressive) serve.",
}

# Drill library seed. positions: 'all' or CSV of codes. solo: doable alone.
DRILLS = [
    # serve
    {"key": "toss-towel", "name": "Toss on a Towel", "skill_key": "serve", "positions": "all", "level": 1, "equipment": "ball, towel", "solo": 1,
     "how_to": "Place a towel a foot in front of your lead foot. 10 serve tosses in a row must peak above reach height and land on the towel. Don't hit until 10/10 — the toss IS the serve."},
    {"key": "wall-serve-contact", "name": "Wall Contact Snaps", "skill_key": "serve", "positions": "all", "level": 1, "equipment": "ball, wall", "solo": 1,
     "how_to": "Stand 15 ft from a wall. Serve into the wall focusing only on flat-hand contact and wrist snap. 3 sets of 10; every rep should sound the same."},
    {"key": "zone-serving", "name": "Zone Serving Ladder", "skill_key": "serve", "positions": "all", "level": 2, "equipment": "ball, court", "solo": 1,
     "how_to": "Divide the far court into 6 zones. Serve to zone 1 until you hit it twice, then zone 5, then zone 6. Track total serves needed; beat your number next session."},
    {"key": "pressure-serves", "name": "10-Point Pressure Serving", "skill_key": "serve", "positions": "all", "level": 3, "equipment": "ball, court", "solo": 1,
     "how_to": "Start at 0. In-play serve = +1, ace-zone target hit = +2, error = back to 0. Reach 10 to finish. Simulates end-of-set nerves."},
    # passing
    {"key": "wall-pass", "name": "Wall Platform Passing", "skill_key": "passing", "positions": "all", "level": 1, "equipment": "ball, wall", "solo": 1,
     "how_to": "Pass continuously against a wall, ball above a line 10 ft up. Quiet arms, legs do the work. Sets of 25 without losing control."},
    {"key": "shuffle-pass", "name": "Shuffle-and-Freeze Passing", "skill_key": "passing", "positions": "OH,L,DS,MB", "level": 2, "equipment": "ball, partner", "solo": 0,
     "how_to": "Partner tosses two steps left/right alternately. Shuffle, STOP, then pass. The freeze before contact is the whole drill. 3 sets of 20."},
    {"key": "target-pass", "name": "Pass to Target Hoop", "skill_key": "passing", "positions": "all", "level": 3, "equipment": "ball, partner, hoop/chair", "solo": 0,
     "how_to": "Partner serves easy from across the net; you pass to a hoop (or chair) at the setter spot, 2-3 ft off the net. Score 10 makes; move the server deeper as you improve."},
    # setting
    {"key": "wall-sets", "name": "Wall Set Shaping", "skill_key": "setting", "positions": "S,OPP", "level": 1, "equipment": "ball, wall", "solo": 1,
     "how_to": "Set against a wall above a 10-ft line: 25 reps close for hand shape, then 25 from 10 ft for extension. All ten fingers, no spin on the ball."},
    {"key": "self-set-sit", "name": "Seated Self-Sets", "skill_key": "setting", "positions": "all", "level": 1, "equipment": "ball", "solo": 1,
     "how_to": "Sit cross-legged and set to yourself 50 times, ball peaking 3-5 ft up. Sitting removes the legs so your hands must be perfect."},
    {"key": "square-up-sets", "name": "Move-Square-Set Triangle", "skill_key": "setting", "positions": "S", "level": 3, "equipment": "ball, partner", "solo": 0,
     "how_to": "Partner tosses to three spots along the net; you move, square to zone 4, and deliver a hittable high ball each time. 3 rounds of 12; a coach watches shoulder alignment."},
    # attacking
    {"key": "approach-footwork", "name": "Approach Footwork Reps", "skill_key": "attacking", "positions": "OH,MB,OPP,S", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "No ball: 20 full approaches (left-right-left for righties), slow-to-fast, both arms swinging back then up. Film one from the side and check the last two steps are the biggest."},
    {"key": "wall-spikes", "name": "Wall Spike Snaps", "skill_key": "attacking", "positions": "all", "level": 2, "equipment": "ball, wall", "solo": 1,
     "how_to": "Toss to yourself and spike into the floor so the ball hits the wall and returns. High contact in front of the shoulder, wrist snap over the top. 3 sets of 15."},
    {"key": "call-your-shot", "name": "Call-Your-Shot Hitting", "skill_key": "attacking", "positions": "OH,MB,OPP", "level": 3, "equipment": "ball, setter, court", "solo": 0,
     "how_to": "Before each set, call 'line', 'angle', or 'tip' out loud, then hit exactly that. 12 swings; a called-and-made shot beats a harder uncalled one."},
    # blocking
    {"key": "block-footwork", "name": "Shuffle-Crossover Block Steps", "skill_key": "blocking", "positions": "MB,OH,OPP,S", "level": 1, "equipment": "net (or line on wall)", "solo": 1,
     "how_to": "Along the net: shuffle-shuffle-jump to the pin, then crossover-step-close the other way. Hands stay at shoulder height the whole trip. 6 trips each direction."},
    {"key": "penetration-jumps", "name": "Press-Over Penetration Jumps", "skill_key": "blocking", "positions": "MB,OH,OPP,S", "level": 2, "equipment": "net", "solo": 1,
     "how_to": "Stand at the net, jump and press both hands over into the opponent's space (no swatting down), land balanced. 3 sets of 10; add a partner tossing a ball to seal on."},
    {"key": "eye-sequence", "name": "Ball-Setter-Ball-Hitter Reads", "skill_key": "blocking", "positions": "MB,OH,OPP", "level": 3, "equipment": "live hitters", "solo": 0,
     "how_to": "Front a live attack line. Say the sequence out loud as you read: 'pass... setter... set... hitter'. Leave with the setter's release. 15 reads; score blocks that take away the called shot."},
    # digging
    {"key": "low-base-holds", "name": "Low Base Position Holds", "skill_key": "digging", "positions": "all", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "Hold a low defensive base 30 seconds x 5: feet wider than shoulders, weight forward, hands free. Between holds, 5 lateral shuffles each way staying low."},
    {"key": "wall-dig-react", "name": "Wall Rebound Digs", "skill_key": "digging", "positions": "L,DS,OH,S", "level": 2, "equipment": "ball, wall", "solo": 1,
     "how_to": "Throw the ball hard into the wall and dig the rebound high to yourself. Vary the angle so you must move first. 3 sets of 12 controlled digs."},
    {"key": "tip-and-rip", "name": "Tip-or-Rip Reads", "skill_key": "digging", "positions": "L,DS,OH,MB,OPP,S", "level": 3, "equipment": "partner on a box", "solo": 0,
     "how_to": "Partner alternates randomly: hard swing or tip. You must be stopped at their contact, then dig or sprint-forward accordingly. 20 balls; score any playable touch."},
    # movement
    {"key": "star-drill", "name": "Star Touch Footwork", "skill_key": "movement", "positions": "all", "level": 1, "equipment": "5 cones/objects", "solo": 1,
     "how_to": "Place 5 markers in a star around you. From center: shuffle to a marker, touch, return to center in base. 2 rounds of the full star, staying low the whole time."},
    {"key": "feet-then-ball", "name": "Feet-Then-Ball Freeze Reps", "skill_key": "movement", "positions": "all", "level": 2, "equipment": "ball, partner", "solo": 0,
     "how_to": "Partner tosses anywhere within 3 steps. Move, FREEZE for one beat, then play the ball (pass or set). The freeze is exaggerated on purpose. 3 sets of 15."},
    # game IQ
    {"key": "rotation-quiz", "name": "Rotation Walkthrough Quiz", "skill_key": "game_iq", "positions": "all", "level": 1, "equipment": "none (use the coach app court)", "solo": 1,
     "how_to": "Using the rotation viewer, step through all 6 rotations of your lineup. For each: say your zone, your base spot, your serve-receive job, and who you'd set/hit with. Repeat until instant."},
    {"key": "film-one-thing", "name": "Watch For One Thing", "skill_key": "game_iq", "positions": "all", "level": 2, "equipment": "any match video", "solo": 1,
     "how_to": "Watch 10 minutes of any volleyball match tracking exactly ONE thing (e.g., where the setter puts every second ball, or how the libero calls serves). Write 3 observations in your training log."},
    {"key": "talk-freebies", "name": "The Two Freebies", "skill_key": "game_iq", "positions": "all", "level": 1, "equipment": "scrimmage", "solo": 0,
     "how_to": "In your next scrimmage, commit to the two freebie calls: 'mine' on every ball you play and 'in/out' on every serve near a line. Log how it changed your team's chaos level."},
]


def drill_snippets(skill_keys: list[str], position: str | None, max_drills: int = 6) -> str:
    """Full drill-library entries for the AI coach, so it can explain drills
    accurately (name, level, equipment, and the complete how-to)."""
    def fits(d):
        return d["positions"] == "all" or (position and position in d["positions"].split(","))
    picked = [d for d in DRILLS if d["skill_key"] in skill_keys and fits(d)]
    picked.sort(key=lambda d: (d["level"], -d["solo"]))
    lines = []
    for d in picked[:max_drills]:
        solo = "solo" if d["solo"] else "needs a partner/coach"
        lines.append(f"- “{d['name']}” ({LEVEL_NAMES[d['level']]} level, {solo}; "
                     f"equipment: {d['equipment']}): {d['how_to']}")
    return "\n".join(lines)


def knowledge_snippets(skill_keys: list[str], position: str | None) -> str:
    """Assemble grounding text for the AI coach: cues + error tables for the
    requested skills, plus position guidance."""
    parts: list[str] = []
    if position and position in POSITION_GUIDE:
        parts.append(f"Position guide ({position}): {POSITION_GUIDE[position]}")
    for key in skill_keys:
        k = KNOWLEDGE.get(key)
        if not k:
            continue
        name = next((s["name"] for s in SKILLS if s["key"] == key), key)
        parts.append(f"\n{name} — key cues:")
        parts.extend(f"- {c}" for c in k["cues"])
        parts.append(f"{name} — error diagnosis table (error / likely cause / correction):")
        parts.extend(f"- {e['error']} | {e['cause']} | {e['fix']}" for e in k["errors"])
    return "\n".join(parts)
