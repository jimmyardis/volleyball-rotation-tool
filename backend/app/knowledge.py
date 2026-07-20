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
            "Float serve: LIFT the toss low with a straight arm — just above your reach, in front of your hitting shoulder, the same lift every time.",
            "Rhythm is place–step–hit: contact the ball right after your front foot lands.",
            "Contact at full extension: flat palm, fingers together, heel of the hand through the dead center of the ball — then stop your arm (float).",
            "Topspin serve: toss higher and a bit more in front, reach tall, and wrap your hand over the top of the ball.",
            "Start your body at a 45-degree angle with the arm drawn back like a bow — power comes from your body turning through the serve, not just the arm.",
            "Weight transfers from back foot to front foot through contact.",
            "Serve the seams — the gaps between two passers — not just open floor. Pick the target BEFORE the toss.",
            "Mix short serves (zone 3) with deep corners to make the other team move.",
            "Same routine every serve: bounce, breathe, pick your zone, lift. Serve routines beat serve hopes.",
        ],
        "errors": [
            {"error": "serve into the net",
             "cause": "rushed rhythm or toss drifting low/behind — contact point drops",
             "fix": "keep the lift low but IN FRONT of the hitting shoulder and fix the rhythm: place, step, hit — contact just after the front foot lands, reaching tall"},
            {"error": "serve sails long",
             "cause": "contact under the ball with an open palm scooping upward",
             "fix": "contact the back-middle of the ball with a flat hand at full reach; for floats, stop the arm shorter after contact"},
            {"error": "no consistency serve to serve",
             "cause": "toss varies each attempt",
             "fix": "drill the toss alone: 10 straight-arm lifts that land on a towel placed at your front foot before hitting again"},
            {"error": "float serve doesn't float",
             "cause": "wrist snaps or fingers wrap the ball, adding spin",
             "fix": "stiff wrist, fingers together, contact dead-center with the heel of the hand, abrupt stop on follow-through"},
            {"error": "toss drifts behind your head; serves spray high or long",
             "cause": "throwing the toss instead of lifting it",
             "fix": "straight-arm LIFT released about shoulder height, finishing in front of the hitting shoulder — re-earn 10/10 on the towel before hitting again"},
            {"error": "serves land in but are easy to pass",
             "cause": "aiming safe middle-court with no plan",
             "fix": "target the seams between passers and mix short (zone 3) with deep corners — make somebody move and decide whose ball it is"},
            {"error": "topspin serve sails long and flat",
             "cause": "contacting under/behind the ball with no wrap",
             "fix": "toss slightly higher and more in front, reach tall, contact the top-back of the ball and wrap your hand over it"},
            {"error": "all-arm serve with no power",
             "cause": "no weight transfer or torso rotation",
             "fix": "start at 45 degrees, step toward your target, and let hips and torso rotate through contact — torque, not arm"},
            {"error": "great serves in warmup, misses in matches",
             "cause": "no fixed pre-serve routine, so nerves change the motion",
             "fix": "build a 3-step routine (bounce, breathe, pick your zone) and run it on every serve, including in pressure drills"},
        ],
    },
    "passing": {
        "cues": [
            "Beat the ball to the spot — be stopped and balanced before contact whenever possible.",
            "Get your platform out early and make only small late adjustments: wrists and hands together, elbows locked — two arms, one flat board.",
            "Get behind the ball so it plays off your midline — centered between your knees, not beside you.",
            "Read the server: watch their toss and arm swing so you know the serve's line before it crosses the net.",
            "Ball contacts the forearms, not the hands; shrug the shoulders, don't swing — legs get you low, arms stay quiet.",
            "Face the server, angle the platform to the target — pass to a spot about 5 feet off the net, never ON the net.",
            "Short serve: step-shuffle, then drop a knee to get your platform under the ball.",
            "High, deep floater? Take it overhead with your hands — legal on first contact and more accurate than backpedaling.",
            "Call it early and loud ('mine' before the ball crosses the net), and agree on seams with your neighbor before the serve.",
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
             "fix": "drop the inside shoulder and aim the platform at the setter's spot, 4-5 ft off the net — a perfect pass is never on the net"},
            {"error": "fine on serves at you, shanks anything to the side",
             "cause": "reading the ball late — eyes only on flight, not the server",
             "fix": "watch the server's toss and arm swing; call the line ('short!'/'deep!') before the ball crosses the net"},
            {"error": "deep floaters push you back and the pass flies over the net",
             "cause": "taking deep balls on the forearms while backpedaling",
             "fix": "drop-step and turn to run the ball down, or take high deep floaters overhead with your hands"},
            {"error": "short serves drop in front of you untouched",
             "cause": "tall posture and no short-ball footwork",
             "fix": "step-shuffle then knee-drop: run forward, drop the lead knee, platform under the ball before it dies"},
            {"error": "two passers collide — or both watch the ball drop",
             "cause": "seam ownership never decided",
             "fix": "agree seams before the serve (shortest distance takes it; deeper player takes the deep seam ball) and call it out loud"},
            {"error": "ball spins off one arm",
             "cause": "wrists apart, platform uneven",
             "fix": "press wrists and heels of the hands together, thumbs even, elbows locked — one flat surface from wrists to elbows"},
            {"error": "hard serves rocket off your arms out of control",
             "cause": "swinging to 'help' a ball that already has pace",
             "fix": "on hard serves just set the angle and absorb — soften the shoulders and let the serve's speed do the work"},
        ],
    },
    "setting": {
        "cues": [
            "Square to the left antenna every single time — front sets and back sets should look identical until release.",
            "Show the window early: hands up and ball-shaped above your forehead BEFORE the ball arrives, thumbs near your hairline.",
            "Take every ball on your forehead — in and out on your midline, all ten finger pads on the ball.",
            "Feet beat the ball: plant left, lead right — weight moving through the ball, right foot finishing toward the target.",
            "Extend arms AND legs together — finish tall, wrists to the target.",
            "Soft to fast: quiet hands catch the ball's shape, then arms and legs extend quickly together.",
            "Set the ball 2-4 feet off the net — a hitter can fix 'off'; nobody can fix 'tight'.",
            "Tempo is a decision: know the set (quick, go, high four, back) before the pass arrives — and in trouble, the default is automatic: high ball to the left pin.",
        ],
        "errors": [
            {"error": "double contact called",
             "cause": "hands uneven — one hand contacts before the other",
             "fix": "shape the ball early: hands up and formed before the ball arrives; catch-and-release drills with a heavier ball"},
            {"error": "sets drift tight to the net",
             "cause": "setting on the move, momentum carrying toward the net",
             "fix": "beat the pass to the spot and stop; square up before contact — and aim 2-4 ft off the net on purpose"},
            {"error": "quick sets mistimed with the middle",
             "cause": "tempo mismatch — setter and hitter disagree on when the ball leaves",
             "fix": "reps with just the MB: hitter jumps as the pass hits the setter's hands; talk every rep"},
            {"error": "ball squirts sideways / wobbles out of the hands",
             "cause": "one hand dominating — contact not centered on the midline",
             "fix": "wall-shaping reps: ball enters and leaves directly above the forehead; check both thumbs near the hairline before every rep"},
            {"error": "taking the ball low, at chest height",
             "cause": "hands shown late — still rising as the ball arrives",
             "fix": "show the window: hands shaped above the forehead before the ball gets there; freeze the catch position on toss reps first"},
            {"error": "every back set is read by the blockers",
             "cause": "posture changes — hips thrust, back arches, or eyes glance backward before contact",
             "fix": "identical neutral posture for front and back sets; extend up-and-through at the last instant only"},
            {"error": "sets die short of the antenna",
             "cause": "arms-only setting, weight stuck on the heels",
             "fix": "finish the left-right pattern with weight transferring through the ball; legs extend with the arms, right foot pointing at the target"},
            {"error": "chaos when the pass is off the net",
             "cause": "no out-of-system default — trying fancy sets on bad balls",
             "fix": "automatic rule decided before the pass: bad pass = high, loopy set to zone 4, aimed a few feet off the net"},
            {"error": "late to the target spot from defense",
             "cause": "releasing only after watching the pass go up",
             "fix": "release the moment the ball crosses to your side; rep the base-to-target footwork without a ball until automatic"},
        ],
    },
    "attacking": {
        "cues": [
            "Approach rhythm slow-to-fast: the second-to-last step is your longest and fastest; the LAST step is short and quick — it turns run into jump (left-RIGHT-left for righties; lefties mirror).",
            "Four-step for full speed: right-left-right-left for righties — step 1 is small and points you at the set.",
            "Both arms rip back together on the step-close, then drive UP together — the arms are part of the jump.",
            "Bow-and-arrow in the air: elbow high, hand back by your ear, chest open — then whip a fast, loose arm.",
            "Contact high and in FRONT of the hitting shoulder; hit over the top of the ball — a fast, relaxed arm beats a muscled one, and the wrist takes care of itself.",
            "Start behind the 10-foot line and wait — go on the setter's release, then accelerate.",
            "See the block before you swing: line, angle, tool, or tip is a choice.",
            "Jump up, not forward: take off and land in nearly the same spot, off the net.",
            "After every attack or block: off the net first, past the 10-foot line, turned so you can see the setter.",
        ],
        "errors": [
            {"error": "hitting into the net",
             "cause": "ball drifted behind the head — late or under the set, or launching too close to the net",
             "fix": "start the approach later than feels natural and stay off the net; jump up, not forward — contact point stays in front of the hitting shoulder"},
            {"error": "no power on the swing",
             "cause": "no arm backswing / jumping off the wrong footwork",
             "fix": "wall-swing progression: footwork only, then footwork + arm swing, then against a wall, then live"},
            {"error": "always hitting the same shot",
             "cause": "predictable — eyes never leave the ball",
             "fix": "peek at the block during the approach; call your shot out loud in practice reps"},
            {"error": "goofy-footed approach (righty closing right-left)",
             "cause": "footwork learned backward; arms and legs out of sync",
             "fix": "slow-motion approaches syncing arms to steps — hands drift forward on the left step, sweep back on the right; groove it before adding a ball"},
            {"error": "broad-jumping into the net",
             "cause": "final step too long — horizontal momentum never converts to height",
             "fix": "make the last step short and quick, plant and jump straight up; drill inside a taped takeoff box — land where you took off"},
            {"error": "always jammed / ball behind your head",
             "cause": "starting too close to the net, or leaving before reading the set",
             "fix": "start behind the 10-ft line (put a cone at your start spot); go on the setter's release, not the pass"},
            {"error": "hitting long over and over",
             "cause": "contacting under/behind the ball with an open palm",
             "fix": "reach full extension and contact the top-back of the ball in front of the shoulder; keep the hitting hand up after contact"},
            {"error": "slow, weak arm despite a strong approach",
             "cause": "muscling the swing — tight shoulder, clenched hand",
             "fix": "loose hand, relaxed shoulder; swing for pure speed against a wall with zero accuracy pressure, then bring that speed to the court"},
            {"error": "blocked straight down every time",
             "cause": "hitting the same power angle into a set block",
             "fix": "on tight sets swing high off the blocker's hands (tool) or use the roll/tip — a smart shot beats a hard shot into two blockers"},
            {"error": "never ready for a second swing in transition",
             "cause": "standing at the net admiring the first play",
             "fix": "land, drop-step and crossover off the net past the 10-ft line, turn to face the setter, then approach again — every rally"},
        ],
    },
    "blocking": {
        "cues": [
            "Start an arm's length (1.5-2 ft) off the net, loaded stance, hands at shoulder height, eyes on the hitter (ball-setter-ball-hitter).",
            "Eyes early: find the setter before the set leaves their hands — early eyes buy you time.",
            "Short trip = shuffle; long trip = 3-step crossover: small quick lead step, big crossover, hop-close squared to the hitter.",
            "Penetrate: press hands OVER the net into their space — reaching OVER beats reaching HIGH. Don't swat down.",
            "Be a wall, not a swatter: firm, still hands tilted about 45° down into their court.",
            "Timing scales with the set: quicks you leave with the setter's release; high outside sets you jump AFTER the hitter — higher and farther off, later jump.",
            "Seal the line or the angle — a block that takes away one shot is a good block; pins set the block, the middle closes the seam.",
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
             "fix": "start 1.5-2 ft off the net; jump touches with a vertical marker — chest stays behind the hands"},
            {"error": "slow to the pin even with fast feet",
             "cause": "big lunging first step",
             "fix": "make step one small and QUICK (speed, not ground coverage), then a big crossover and hop-close — the 3-step crossover, not repeated shuffles"},
            {"error": "hitter scores through the seam between blockers",
             "cause": "middle late, or the pin blocker drifting",
             "fix": "the pin sets the block and holds; the middle crossover-closes until the hands overlap — no gap a ball fits through"},
            {"error": "slapping or swinging at the ball",
             "cause": "trying to 'make a play' instead of taking space",
             "fix": "be a wall: press firm 45°-tilted hands over the net and hold the shape still"},
            {"error": "mistimed block on high outside sets",
             "cause": "using quick-set timing on everything",
             "fix": "the higher and farther off the net the set, the later you jump — let the hitter load first, then go"},
            {"error": "big vertical, ball still rolls down your side of the hands",
             "cause": "jumping straight up with no reach-over",
             "fix": "start 1.5-2 ft off the net and press the hands over on the way up — penetration beats height"},
        ],
    },
    "digging": {
        "cues": [
            "Stopped and low BEFORE the attacker contacts — read, don't guess.",
            "Read in order: pass → setter → set → hitter's approach and shoulders.",
            "Straight approach = line shot; angled approach = cross-court — shift your feet to that line early.",
            "If you can see the attacker's open hand, the arm is slowing: expect off-speed and get moving forward.",
            "Arms are shock absorbers, not a brick wall — relax and give slightly on hard-driven balls.",
            "Every dig has a target: high to the middle of the court, off the net.",
            "Two arms whenever possible; one hand or a pancake only when the ball is outside two-arm reach.",
            "Know your three spots: starting spot, read spot (frozen at attacker contact), adjust steps after contact.",
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
            {"error": "diving for balls a step away",
             "cause": "going to the floor too early",
             "fix": "feet first: emergency skills only when the ball is outside two-arm reach"},
            {"error": "sprinting past the ball sideways",
             "cause": "moving at contact instead of before it",
             "fix": "be at your read spot and STOPPED when the attacker swings; small adjust steps after"},
            {"error": "hard balls ricochet wildly off the platform",
             "cause": "rigid arms fighting power",
             "fix": "relax the shoulders and forearms; let the platform give slightly toward your torso at contact"},
            {"error": "pancake attempts flop — ball hits the floor",
             "cause": "palm not flat or hand arrives late",
             "fix": "progression: from kneeling, slide the hand palm-flat along the floor under a low ball, then from a lunge — hand pressed flat before the ball lands"},
        ],
    },
    "movement": {
        "cues": [
            "Athletic base everywhere: knees bent, weight on the balls of the feet.",
            "Small hop-to-a-stop (split step) timed to the opponent's contact — land loaded and ready.",
            "Shuffle for short distances, crossover-run for long ones — never backpedal for a ball.",
            "Deep ball behind you? Drop-step, turn, and RUN — playing it facing away from the net is fine.",
            "First step small and fast; second step covers the ground.",
            "Stop BEFORE you play the ball; play from a still base.",
            "Land balanced from every jump — a stuck landing is the start of your next move.",
            "Footwork patterns (approach, block crossover, transition off the net) deserve their own reps.",
        ],
        "errors": [
            {"error": "always a step late to the ball",
             "cause": "watching outcomes instead of moving on cues; standing base too tall",
             "fix": "reaction footwork drills; move on the opponent's contact, not the ball's flight"},
            {"error": "off-balance at contact",
             "cause": "playing the ball while still moving",
             "fix": "'feet then ball': exaggerate the stop in drills — freeze one beat before every contact"},
            {"error": "backpedaling under deep balls and falling",
             "cause": "trying to stay facing the net",
             "fix": "drop-step, turn, run the ball down, and play it up even facing away"},
            {"error": "a beat late despite seeing the play",
             "cause": "flat-footed between contacts — no split step",
             "fix": "small hop landing in base timed to the opponent's contact"},
            {"error": "slow off the net after a block",
             "cause": "landing, then deciding",
             "fix": "rehearse block-land-turn-transition as one continuous pattern until automatic"},
        ],
    },
    "game_iq": {
        "cues": [
            "Know the rotation: where's the setter, who's front row, what's my base and my job right now?",
            "Talk constantly: 'in/out', 'tip', 'line's open', 'two blockers' — information wins rallies.",
            "Seam rule: shortest distance takes it — know your seams before the serve, not during.",
            "In the seam, one voice says 'mine'; the partner answers 'out — got you' and covers behind.",
            "Every rotation, find their setter: front row or back row? Front row = dump threat and only two hitters.",
            "Servers repeat: after each serve, note where it went and shift a step before the next whistle.",
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
            {"error": "seam serves drop untouched",
             "cause": "no agreed seam rule",
             "fix": "adopt 'shortest distance takes it' and rep seam serves until the call is automatic"},
            {"error": "two players collide (or both pull off)",
             "cause": "late or unanswered calls",
             "fix": "caller says 'mine' before the ball crosses the net; the seam partner answers 'out' and covers behind"},
            {"error": "surprised by a setter dump",
             "cause": "not tracking the setter's row",
             "fix": "each rotation say 'setter front' or 'setter back' out loud — front-row setter means dump threat"},
            {"error": "chaos on free balls",
             "cause": "no standard call or spots",
             "fix": "one word — 'FREE!' — everyone to free-ball positions; rehearse it like a play"},
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
     "how_to": "Partner serves easy from across the net; you pass to a hoop (or chair) at the setter spot, 4-5 ft off the net. Score 10 makes; move the server deeper as you improve."},
    # setting
    {"key": "wall-sets", "name": "Wall Set Shaping", "skill_key": "setting", "positions": "S,OPP", "level": 1, "equipment": "ball, wall", "solo": 1,
     "how_to": "Set against a wall above a 10-ft line: 25 reps close for hand shape, then 25 from 10 ft for extension. All ten fingers, no spin on the ball."},
    {"key": "self-set-sit", "name": "Seated Self-Sets", "skill_key": "setting", "positions": "all", "level": 1, "equipment": "ball", "solo": 1,
     "how_to": "Sit cross-legged and set to yourself 50 times, ball peaking 3-5 ft up. Sitting removes the legs so your hands must be perfect."},
    {"key": "square-up-sets", "name": "Move-Square-Set Triangle", "skill_key": "setting", "positions": "S", "level": 3, "equipment": "ball, partner", "solo": 0,
     "how_to": "Partner tosses to three spots along the net; you move, square to zone 4, and deliver a hittable high ball each time. 3 rounds of 12; a coach watches shoulder alignment."},
    # attacking
    {"key": "approach-footwork", "name": "Approach Footwork Reps", "skill_key": "attacking", "positions": "OH,MB,OPP,S", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "No ball: 20 full approaches (left-right-left for righties), slow-to-fast, both arms swinging back then up. Film one from the side and check the second-to-last step is long and low and the LAST step is short and quick — that's what turns your run into jump."},
    {"key": "wall-spikes", "name": "Wall Spike Snaps", "skill_key": "attacking", "positions": "all", "level": 2, "equipment": "ball, wall", "solo": 1,
     "how_to": "Toss to yourself and spike into the floor so the ball hits the wall and returns. High contact in front of the shoulder with a fast, loose arm hitting over the top of the ball — don't force a wrist snap, it happens on its own. 3 sets of 15."},
    {"key": "call-your-shot", "name": "Call-Your-Shot Hitting", "skill_key": "attacking", "positions": "OH,MB,OPP", "level": 3, "equipment": "ball, setter, court", "solo": 0,
     "how_to": "Before each set, call 'line', 'angle', or 'tip' out loud, then hit exactly that. 12 swings; a called-and-made shot beats a harder uncalled one."},
    # blocking
    {"key": "block-footwork", "name": "Shuffle-Crossover Block Steps", "skill_key": "blocking", "positions": "MB,OH,OPP,S", "level": 1, "equipment": "net (or line on wall)", "solo": 1,
     "how_to": "Along the net: shuffle-jump for a short trip one way, then the 3-step crossover the other way (small quick lead step, big crossover, hop-close squared to the hitter) — crossover is the default for long trips to the pin. Hands stay at shoulder height the whole time. 6 trips each direction."},
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
    {"key": "film-one-thing", "name": "Watch a Match, Track One Thing", "skill_key": "game_iq", "positions": "all", "level": 2, "equipment": "any volleyball video on a phone/TV", "solo": 1,
     "how_to": "Pull up 10 minutes of ANY volleyball match (YouTube is fine). Pick ONE thing to follow the whole time — e.g. where the setter puts every second ball, or how the libero calls each serve in/out — and ignore everything else. Jot 3 things you noticed in your training log. That's it: one match, one thing, three notes."},
    {"key": "talk-freebies", "name": "The Two Freebies", "skill_key": "game_iq", "positions": "all", "level": 1, "equipment": "scrimmage", "solo": 0,
     "how_to": "In your next scrimmage, commit to the two freebie calls: 'mine' on every ball you play and 'in/out' on every serve near a line. Log how it changed your team's chaos level."},
    # --- no net, no partner: solo drills you can do at home with just a ball (or nothing) ---
    {"key": "toss-pass-self", "name": "Toss & Pass to Yourself", "skill_key": "passing", "positions": "all", "level": 1, "equipment": "ball", "solo": 1,
     "how_to": "Toss the ball 6-8 ft straight up, slide behind it, and pass it back up to yourself with a quiet platform (arms still, legs lift). Keep the streak alive — aim for 20 in a row without moving your feet more than a step. No wall, no partner."},
    {"key": "straight-set-ladder", "name": "Straight-Up Set Ladder", "skill_key": "setting", "positions": "all", "level": 1, "equipment": "ball", "solo": 1,
     "how_to": "Set the ball straight up above your forehead, 3-4 ft high, 30 times without letting it drift off your spot. Then do 5 with your eyes closed and feel where it lands — good hands catch it soft and centered. Ball only."},
    {"key": "shadow-approach-arms", "name": "Approach + Arm Swing Shadow", "skill_key": "attacking", "positions": "OH,MB,OPP,S", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "No ball, no net. 15 full approaches with a real arm swing on top — arms drive back as you plant, then whip up and snap over an imaginary ball. Freeze at the top each rep and check your hitting elbow is high and in front. Slow, then game speed."},
    {"key": "shadow-block-press", "name": "Shadow Block Presses", "skill_key": "blocking", "positions": "MB,OH,OPP,S", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "Face a wall or open space — no net needed. Jump straight up and press both hands high and FORWARD, like reaching over the net into the other side, then land balanced. Hands stay wide, thumbs up. 3 sets of 10; think 'press over,' never 'swat down.'"},
    {"key": "sprawl-recover", "name": "Sprawl & Recover", "skill_key": "digging", "positions": "all", "level": 2, "equipment": "ball", "solo": 1,
     "how_to": "From a low base, toss the ball out to one side just past your reach, sprawl to pop it up with one hand, then scramble back to your feet in base. 6 each side. You set your own chase — no partner needed."},
    {"key": "line-hops-base", "name": "Line Hops to Base", "skill_key": "movement", "positions": "all", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "Use any floor line or a strip of tape. Quick two-foot hops side-to-side over the line for 20 seconds, then on your own 'go' freeze into a low defensive base and hold 2 seconds. 5 rounds. Builds fast feet that can stop under control."},
    # --- research batch (2026-07): serve ---
    {"key": "place-step-hit", "name": "Place-Step-Hit Shadow Serves", "skill_key": "serve", "positions": "all", "level": 1, "equipment": "ball", "solo": 1,
     "how_to": "Groove the serve rhythm without a court: stand at 45 degrees, arm back like a bow. 15 slow 'place, step, hit' reps CATCHING your own lift instead of hitting — check the lift stays low and in front of your hitting shoulder. Then 15 full-speed reps into open space or a wall. Success: front foot lands, THEN contact — never the reverse."},
    {"key": "serve-routine", "name": "Serve Routine Builder", "skill_key": "serve", "positions": "all", "level": 1, "equipment": "ball", "solo": 1,
     "how_to": "Design your personal 3-step pre-serve routine (e.g. two bounces, one breath, pick a zone out loud). Serve 20 balls using the identical routine every time; a rushed or skipped routine doesn't count. This drill scores the routine, not the serve — 20/20 identical routines wins regardless of where the balls land."},
    {"key": "short-deep-mix", "name": "Short-Deep Mix", "skill_key": "serve", "positions": "all", "level": 2, "equipment": "ball, court, 2 towels", "solo": 1,
     "how_to": "Put one towel just past the far 10-ft line (short, zone 3) and one in a deep corner. Alternate strictly short, deep, short, deep for 20 serves, 1 point per towel-side hit. Beat 12. Making the other team move between short and deep is a complete serving strategy by itself."},
    {"key": "seam-hunting", "name": "Seam Hunting", "skill_key": "serve", "positions": "all", "level": 3, "equipment": "ball, court, 2 chairs", "solo": 1,
     "how_to": "Place two chairs where opposing passers would stand. Serve 15 balls at the GAPS: between the chairs, and between each chair and the sideline. Score 2 for a seam, 1 for in-play elsewhere, minus 1 for an error. Seams beat zones — two humans have to decide whose ball it is."},
    {"key": "topspin-wrap", "name": "Topspin Wrap Progression", "skill_key": "serve", "positions": "S,OH,OPP,DS", "level": 3, "equipment": "ball, wall or court", "solo": 1,
     "how_to": "Step 1: self-toss high, reach tall, wrap your hand over the top of the ball and spike it into the floor with visible forward spin — 10 reps. Step 2: from 20 ft, topspin serve into a wall above a 7.5-ft line — 10 reps. Step 3: 10 full-court topspin serves. Success: 6/10 in with a clear topspin dive at the end of flight."},
    {"key": "jump-float-ladder", "name": "Jump-Float Footwork Ladder", "skill_key": "serve", "positions": "all", "level": 4, "equipment": "ball, court", "solo": 1,
     "how_to": "Learn step-step-toss-step-step (right, left, toss, right, left for righties). 10 shadow reps with no ball, arms up in bow-and-arrow through the hop. Then 10 toss-and-catch reps — the low lift must land where your jump takes you. Finish with 10 full jump-floats. 7/10 in play with no spin; drop back a stage whenever the toss breaks down."},
    {"key": "first-serve-reset", "name": "First-Serve Reset Game", "skill_key": "serve", "positions": "all", "level": 3, "equipment": "ball, court", "solo": 1,
     "how_to": "Every serve simulates entering the game cold: serve once, leave the end line for a 30-second reset (jog, shadow reps, anything), come back, run your full routine, and serve once to a called zone. 10 total 'first serves', score makes-to-zone, target 6/10. This trains the serve you actually get in matches: one attempt, no rhythm."},
    # --- research batch: passing ---
    {"key": "off-center-midline", "name": "Off-Center Midline Reps", "skill_key": "passing", "positions": "all", "level": 2, "equipment": "ball", "solo": 1,
     "how_to": "Progression from Toss & Pass to Yourself: toss the ball 8 ft up but deliberately 2-3 steps left or right. Step-shuffle behind it so contact happens on your midline between your knees; freeze one beat after the pass with hands below shoulders. 3 sets of 10, alternating sides. 8/10 straight back up without reaching sideways."},
    {"key": "overhead-floater-take", "name": "Overhead Floater Take", "skill_key": "passing", "positions": "all", "level": 2, "equipment": "ball", "solo": 1,
     "how_to": "Toss the ball high and deep so it would carry over your head; drop-step, get under it, and take it with setting hands overhead, pushing it forward-up to a target. 3 sets of 10. Then 10 random tosses where you decide in the air and call it: 'hands!' for high/deep, 'platform!' for low/fast. 7/10 correct, controlled decisions."},
    {"key": "knee-drop-short", "name": "Knee-Drop Short-Ball Runs", "skill_key": "passing", "positions": "OH,L,DS,MB", "level": 2, "equipment": "ball", "solo": 1,
     "how_to": "Toss a dying short ball 10 ft in front of you (or have a partner toss). Sprint with a step-shuffle, drop the lead knee, and pass from UNDER the ball to a target. 3 sets of 8. 6/8 playable passes that go up, not forward — the knee drop is what stops you from swinging at it."},
    {"key": "read-server-calls", "name": "Read-the-Server Calls", "skill_key": "passing", "positions": "OH,L,DS", "level": 3, "equipment": "ball, partner serving, court", "solo": 0,
     "how_to": "Partner serves at random depths. First 10 reps: your ONLY job is to call 'short!' or 'deep!' the instant the ball leaves their hand — no passing, scored on correct early calls. Then 15 reps calling AND passing to a target 5 ft off the net. 12/15 correct calls; the read (server's toss and arm) is what buys your feet time."},
    {"key": "butterfly", "name": "Butterfly Serve-Receive", "skill_key": "passing", "positions": "all", "level": 3, "equipment": "ball, net, 3+ players", "solo": 0,
     "how_to": "One server, one passer, one target at the setter slot 5 ft off the net. Serve → pass to target → rotate server-to-passer-to-target. 10-serve rounds, grading every pass 0-3. Team average 2.0+ wins. USA Volleyball's canonical serve-receive engine."},
    {"key": "seam-partner-rule", "name": "Seam Partner Rule", "skill_key": "passing", "positions": "OH,L,DS", "level": 3, "equipment": "ball, server, 2 passers", "solo": 0,
     "how_to": "Two passers share one seam; before EVERY serve they point and confirm out loud who owns it (shortest distance takes it; deeper player takes the deep seam ball). Server aims only at the seam for 15 serves. Any hesitation, double-call, or dropped seam ball scores for the server. Passers win 10 of 15 — the drill trains the pre-serve decision, not the pass."},
    {"key": "tug-of-war-pass", "name": "Tug-of-War Passing", "skill_key": "passing", "positions": "all", "level": 4, "equipment": "ball, net, 4+ players", "solo": 0,
     "how_to": "Passers vs servers, score starts at 5. Good pass (2-3 quality) +1, bad pass -1, missed serve +1 for passers. Passers win at 10, servers at 0, then swap. The sliding score keeps every rep consequential."},
    {"key": "servers-vs-passers", "name": "Servers vs Passers 0-3", "skill_key": "passing", "positions": "all", "level": 5, "equipment": "ball, net, team", "solo": 0,
     "how_to": "Half the team serves, half receives with a target; every pass is graded 0-3, passers bank the grade, servers bank 3-minus-grade. First side to 25. Sustain a 2.0+ team average under real serving pressure — the standard match-transfer drill."},
    # --- research batch: setting ---
    {"key": "catch-check-window", "name": "Catch-and-Check Window", "skill_key": "setting", "positions": "all", "level": 1, "equipment": "ball", "solo": 1,
     "how_to": "Toss just above your head, catch in setting shape above your forehead, and FREEZE. Check: triangle window between thumbs and forefingers, thumbs near hairline, elbows out, right foot slightly forward. Push it straight up out of the freeze. 3 sets of 10; when 10/10 freezes pass the check, shrink the freeze until it's a normal set."},
    {"key": "setter-release-footwork", "name": "Setter Release Footwork", "skill_key": "setting", "positions": "S", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "Start in right-back defensive base. On your own 'go', sprint your release path to the target spot at the net, plant the left foot, lead with the right, and finish a shadow set with weight moving toward an imaginary zone-4 target. 3 sets of 10. Every rep ends balanced with the right foot pointing at the target."},
    {"key": "wall-sets-300", "name": "300 Club Wall Sets", "skill_key": "setting", "positions": "S,OPP", "level": 2, "equipment": "ball, wall", "solo": 1,
     "how_to": "Pick one spot on the wall above 10 ft. Set to it in groups of 50 until you reach 300, hands high and contact on the forehead every rep. Only clean, no-spin reps count toward each 50. Rest 1 minute between groups. The volume progression after Wall Set Shaping."},
    {"key": "toss-move-square", "name": "Toss-Move-Square Ladder", "skill_key": "setting", "positions": "S,OPP", "level": 2, "equipment": "ball, any tall target", "solo": 1,
     "how_to": "Toss the ball 2-3 steps away in a random direction, beat it there with quick feet, square your hips to your target, and deliver a set at it. 3 sets of 12; score a point only when you were stopped and squared BEFORE contact. Increase the toss distance as you improve."},
    {"key": "mirror-front-back", "name": "Mirror Front/Back Sets", "skill_key": "setting", "positions": "S", "level": 3, "equipment": "ball, partner", "solo": 0,
     "how_to": "Partner tosses to your forehead; alternate front sets to a target ahead and back sets behind, keeping your posture identical until release — no hip thrust, no arch, no looking back. Partner yells 'read it!' any time they could tell the back set was coming. 3 rounds of 10; success is a round with zero calls."},
    {"key": "call-the-set", "name": "Call-the-Set Decision Reps", "skill_key": "setting", "positions": "S", "level": 4, "equipment": "ball, partner, court", "solo": 0,
     "how_to": "Partner tosses simulated passes of random quality — perfect, medium, off the net. Before the ball reaches you, call the right set out loud ('one!', 'go!', 'high four!') and deliver it: good pass earns a quick or go, bad pass is the automatic high outside. 20 balls; score reps where the call matched the pass quality AND the set was hittable."},
    {"key": "oos-high-ball", "name": "Out-of-System High-Ball Rally", "skill_key": "setting", "positions": "all", "level": 3, "equipment": "ball, partner", "solo": 0,
     "how_to": "Stand 25-30 ft apart. Rally high, loopy sets to each other using proper left-right footwork under every ball — this is the emergency set every position needs. Go 2 minutes without the ball dropping; restart the clock on a drop or lazy feet."},
    # --- research batch: attacking ---
    {"key": "arm-leg-sync", "name": "Arm-Leg Sync Walkthrough", "skill_key": "attacking", "positions": "OH,OPP,MB,S", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "Walk your approach in slow motion, exaggerating the wiring: for righties, hands drift forward on the left step, sweep back on the right, then both arms rip back on the step-close and drive up on the jump (lefties mirror). 15 walking reps, 10 at half speed, 5 at full speed. The fix and the vaccine for goofy-footing."},
    {"key": "long-short-tape", "name": "Long-Short Tape Steps", "skill_key": "attacking", "positions": "OH,OPP,MB,S", "level": 2, "equipment": "tape or chalk", "solo": 1,
     "how_to": "Mark two spots: a long-low second-to-last step and a short-quick final step. Approach hitting the marks and jump straight up off the short step. 3 sets of 8; film one set from the side — success is your head rising vertically at takeoff instead of drifting forward."},
    {"key": "takeoff-box", "name": "Takeoff Box Jumps", "skill_key": "attacking", "positions": "OH,OPP,MB", "level": 2, "equipment": "tape", "solo": 1,
     "how_to": "Tape a 2x2-ft box on the floor as your takeoff spot. Full approach, jump from inside the box, land back inside it (or within one shoe-length forward). 3 sets of 6. Landing far forward means the last step is too long — shorten it and repeat. Cures broad-jumping into the net."},
    {"key": "four-step-locator", "name": "Four-Step Locator Approaches", "skill_key": "attacking", "positions": "OH,OPP,MB,S", "level": 2, "equipment": "none", "solo": 1,
     "how_to": "Add the first 'locator' step: right-left-right-left for righties (lefties mirror), starting behind an imaginary 10-ft line. Step 1 is small and points you at the set; rhythm is 'slow... slow... FAST-FAST'. 20 reps: 10 straight, 5 angled left, 5 angled right — real sets move you."},
    {"key": "fast-arm-wall", "name": "Fast-Arm Wall Ladder", "skill_key": "attacking", "positions": "all", "level": 2, "equipment": "ball, wall", "solo": 1,
     "how_to": "Stand 10-15 ft from a wall and throw-spike self-tossed balls at it caring ONLY about arm speed — loose hand, relaxed shoulder, full whip, zero accuracy pressure. 3 sets of 15, varying contact height each set. Success: the last rep sounds as loud as the first with the shoulder still loose."},
    {"key": "block-land-transition", "name": "Block-Land-Transition-Swing", "skill_key": "attacking", "positions": "OH,OPP,MB", "level": 3, "equipment": "none", "solo": 1,
     "how_to": "Start at the net as if you just landed from a block. Drop-step, crossover off the net past the 10-ft line, turn to face the imaginary setter, then run your full approach and shadow swing. 3 sets of 8, alternating left-side and middle starts. Off the net, turned, and moving forward within about 2 seconds."},
    {"key": "shot-menu", "name": "Shot Menu to Targets", "skill_key": "attacking", "positions": "OH,OPP,MB", "level": 4, "equipment": "ball, setter, court, 3 towels", "solo": 0,
     "how_to": "Towels on the far court: deep line corner, deep cross-court angle, short middle (tip/roll zone). Run a 4-shot menu in order — line, angle, roll, tip — then 8 more where the tosser calls the shot mid-approach. 12 total; a controlled roll or tip counts the same as a kill."},
    {"key": "see-the-hands", "name": "See-the-Hands Vision Reps", "skill_key": "attacking", "positions": "OH,OPP,MB", "level": 4, "equipment": "ball, setter, partner across the net", "solo": 0,
     "how_to": "A partner across the net raises both hands to the line side, the angle side, or holds them down while you approach. Call what you saw ('line!'/'angle!'/'no block!') at takeoff and hit the open shot. 15 swings; a correct call with a controlled shot beats a hard swing into the 'block'."},
    # --- research batch: blocking ---
    {"key": "crossover-pin-threes", "name": "Crossover-to-Pin Threes", "skill_key": "blocking", "positions": "MB,OH,OPP,S", "level": 2, "equipment": "none", "solo": 1,
     "how_to": "Practice the 3-step crossover along any floor line: small quick lead step, big crossover step, hop-close with shoulders square. 6 trips each direction slow, then 6 at game speed, jumping and pressing at the end of each trip. Finish squared to an imaginary hitter, balanced, no drift."},
    {"key": "wall-seal-shape", "name": "Wall Seal Shape", "skill_key": "blocking", "positions": "MB,OH,OPP,S", "level": 1, "equipment": "wall", "solo": 1,
     "how_to": "Mark a line on a wall above your standing reach. Jump and press both palms flat on the wall above the line — hands tilted slightly down, wrists firm, thumbs up — and hold the 'wall' shape a beat before landing. 3 sets of 8. No slapping motion; both hands land flat and still every rep."},
    {"key": "setter-release-reads", "name": "Setter-Release Reads (Film)", "skill_key": "blocking", "positions": "MB,OH,OPP", "level": 2, "equipment": "any match video on a phone/TV", "solo": 1,
     "how_to": "Watch a match and call the set direction out loud ('outside!' / 'quick!' / 'back!') the instant the ball leaves the setter's hands. 20 calls, then 20 more pausing to check yourself. 15/20 correct at release — not at set peak — wins. The solo version of Ball-Setter-Ball-Hitter Reads."},
    {"key": "pat-the-hands", "name": "Pat-the-Hands Seal", "skill_key": "blocking", "positions": "MB,OH,OPP,S", "level": 2, "equipment": "net, partner", "solo": 0,
     "how_to": "Partner stands on the other side of the net; jump together and touch palms flat over the top, both reaching into each other's space. 3 sets of 10 jumps. Contact happens on the opponent's side of the net plane without touching the net."},
    {"key": "seam-close-pairs", "name": "Seam-Close Pairs", "skill_key": "blocking", "positions": "MB,OH,OPP", "level": 3, "equipment": "net, tosser, partner", "solo": 0,
     "how_to": "Outside blocker sets the block at the pin; middle runs the crossover and closes until the hands overlap — no seam. Tosser alternates high sets to either pin; 12 closes each side. Score only reps where the two blocks form one wall: no gap, no drift."},
    # --- research batch: digging ---
    {"key": "pancake-progression", "name": "Pancake Progression", "skill_key": "digging", "positions": "all", "level": 2, "equipment": "ball, smooth floor", "solo": 1,
     "how_to": "Stage 1: from kneeling, slide one hand palm-flat along the floor and let a self-tossed low ball bounce up off the back of your hand — 10 clean pops each hand. Stage 2: from a low lunge, extend and pancake a ball tossed just out of reach. The hand is flat on the floor BEFORE the ball arrives."},
    {"key": "overhead-hard-digs", "name": "Overhead Hard-Ball Digs", "skill_key": "digging", "positions": "L,DS,OH,S", "level": 2, "equipment": "ball, wall", "solo": 1,
     "how_to": "Throw the ball hard and high off the wall so the rebound comes at your face or chest; take it overhead with firm hands pressed together, deflecting up. 3 sets of 10. 7/10 rebounds go up and stay on your side with no backing away. Complements Wall Rebound Digs, which trains the low balls."},
    {"key": "call-shot-film", "name": "Call-the-Shot Film Reads", "skill_key": "digging", "positions": "all", "level": 2, "equipment": "any match video", "solo": 1,
     "how_to": "Watch attacks and call 'line', 'cross', or 'tip' at the hitter's contact, using approach angle and arm speed (visible open hand = off-speed). 20 attacks; track your hit rate in your training log. 60%+ correct and improving week over week. The solo version of Tip-or-Rip Reads."},
    {"key": "sprint-through-tips", "name": "Sprint-Through Tips", "skill_key": "digging", "positions": "all", "level": 2, "equipment": "ball", "solo": 1,
     "how_to": "From a deep low base, toss the ball short and low in front of you, sprint forward, and run THROUGH the ball, playing it high with your platform without stopping. 10 reps, then 5 finishing with a sprawl on purpose. 8/10 playable balls popped high toward an imaginary target."},
    {"key": "box-reads", "name": "Box Reads: Base-to-Spot", "skill_key": "digging", "positions": "all", "level": 3, "equipment": "coach on a box, court", "solo": 0,
     "how_to": "Defenders start at starting positions; as the coach on a box at the pin receives the toss, move to your read spot and be FROZEN at contact; the coach hits, tips, or rolls anywhere. 20 balls. Score stopped-at-contact on every rep plus playable touches. Trains starting spot → read spot → adjust."},
    # --- research batch: movement ---
    {"key": "turn-and-run", "name": "Turn-and-Run Chase", "skill_key": "movement", "positions": "all", "level": 2, "equipment": "ball", "solo": 1,
     "how_to": "Toss the ball high over your head and behind you, drop-step, turn, and sprint it down, playing it up before the second bounce — facing away from the 'net' is fine. 8 reps alternating turn directions. 6/8 playable, zero backpedals."},
    {"key": "split-step-wall", "name": "Split-Step Wall Timing", "skill_key": "movement", "positions": "all", "level": 2, "equipment": "ball, wall", "solo": 1,
     "how_to": "Throw the ball at the wall; time a small hop so you land in a low base exactly as the ball hits the wall, then move and dig the rebound. 3 sets of 10. Landing and wall-contact happen together — you move from a loaded stop, not flat feet."},
    {"key": "block-transition-loop", "name": "Block-Land-Transition Loop", "skill_key": "movement", "positions": "MB,OH,OPP", "level": 2, "equipment": "none", "solo": 1,
     "how_to": "Block jump with a press at the 'net' (wall or line), stick the landing, open and take a 3-step transition off the net, then run full approach footwork back in. 8 continuous loops. Every landing balanced, no stutter between landing and the first transition step."},
    {"key": "stick-the-landing", "name": "Stick-the-Landing Jumps", "skill_key": "movement", "positions": "all", "level": 1, "equipment": "none", "solo": 1,
     "how_to": "Max-effort vertical jumps landing soft and silent in an athletic base, holding the frozen landing 2 seconds. 3 sets of 6. No stumble-steps on any landing — the position you land in is the position you could move from. (Also your knees' best friend.)"},
    # --- research batch: game IQ ---
    {"key": "server-chart", "name": "Server Chart", "skill_key": "game_iq", "positions": "all", "level": 2, "equipment": "notebook + any match/video", "solo": 1,
     "how_to": "Chart one team's serves for a full set: for each server, mark the zone (1-6) and short/deep. Afterward write one sentence per server ('#12 goes deep to zone 1 twice, then short'). Success: at least one repeatable pattern found — that's the pre-shift you'd make as a passer."},
    {"key": "call-set-freeze", "name": "Call-the-Set Freeze", "skill_key": "game_iq", "positions": "all", "level": 3, "equipment": "any match video", "solo": 1,
     "how_to": "Pause the video the moment the pass is contacted; predict where the set is going from pass quality and setter position, then play and check. 15 reps per session, log your accuracy. 60%+ is the read that gets blockers and defenders moving early. Progression from Watch a Match, Track One Thing."},
    {"key": "seam-wars", "name": "Seam Wars", "skill_key": "game_iq", "positions": "all", "level": 2, "equipment": "server + 3 passers, court", "solo": 0,
     "how_to": "Server aims only at the seams between passers. A pass counts ONLY if the 'mine'/'out' exchange happened before the ball crossed the net, following the shortest-distance rule. 15 serves; passing team scores 10 to win."},
    {"key": "free-ball-race", "name": "Free-Ball Race", "skill_key": "game_iq", "positions": "all", "level": 2, "equipment": "team, coach with ball", "solo": 0,
     "how_to": "Mid-rally-simulation, the coach shouts 'FREE!' and lobs a free ball; the whole team must call it and hit free-ball positions before it arrives, then run the transition attack. 10 reps; count the clean ones and beat last practice's number."},
    {"key": "setter-row-callouts", "name": "Setter-Row Callouts", "skill_key": "game_iq", "positions": "all", "level": 1, "equipment": "none (use the rotation viewer)", "solo": 1,
     "how_to": "Step through all 6 rotations and for each, say out loud whether the OPPONENT'S setter is front or back row and what that changes: dump threat, two vs three front-row attackers, who your blockers watch. Repeat until instant. Extends the Rotation Walkthrough Quiz to the other side of the net."},
]


# Practice-design principles (motor-learning research + youth-safety
# guidance) that shape HOW the AI coach advises, not what technique it
# teaches. Injected into the coach + Film Room system prompts.
PRACTICE_PRINCIPLES = [
    "Game-like beats blocked: random, varied, game-speed reps win for long-term learning. Blocked repetition of one identical rep is only for brand-new movements or a short technique rebuild — then go back to game-like.",
    "One cue at a time: give exactly ONE focus per rep or session. Three corrections at once teach zero. Pick the highest-leverage fault and stay silent on the rest for now.",
    "Prefer external cues (the ball, the target, the net — 'hit the top of the ball toward the far corner') over body-part cues ('snap your wrist'). External focus measurably speeds up learning.",
    "Don't give feedback on every rep — praise or correct after a block of reps, and taper as the player improves. Constant commentary feels helpful but slows learning.",
    "Only correct real faults: if a rep was close enough, let it go or just confirm. Save corrections for clearly out-of-band errors.",
    "Offer choices: letting the player pick the drill variant, which skill to film, or when to get feedback improves learning and motivation.",
    "Solo sessions should be deliberate practice: 20-40 minutes, ONE skill focus, a countable target ('7/10 serves past the 20-ft line'), and a logged result — not marathon unfocused reps.",
    "Vary within the skill once the movement is stable: different targets, distances, and ball flights build the adaptability that transfers to games.",
    "Jump-load safety: increase weekly jump volume gradually, avoid sudden spikes, always land two-footed with bent knees, and put lighter non-jumping days after heavy jump days. Persistent pain below the kneecap = stop and tell a parent/coach.",
    "Shoulder care: don't do maximal serving/spiking every single day — mix in sub-max placement serving. Shoulder pain during overhead motion is a stop signal, never something to serve through.",
    "Growth spurts temporarily scramble coordination and lower tendon tolerance: expect some technique regression, respond by reducing load and complexity — not by piling on cues. Keep training fun; fun sustains the volume that builds skill.",
]


def practice_principles_text() -> str:
    return "How to coach (practice-design principles — follow these when giving advice):\n" + \
        "\n".join(f"- {p}" for p in PRACTICE_PRINCIPLES)


# Film Room video-review rubrics: what a coach actually looks for frame-by-
# frame in a single-phone-camera clip, per skill. Each checkpoint = name,
# what GOOD looks like, and the most common youth fault. `camera` is the
# angle the player is told to film from.
VIDEO_RUBRICS = {
    "serve": {
        "camera": "Side view from your hitting-arm side, far enough back that your whole body and the toss peak stay in frame.",
        "checkpoints": [
            {"name": "Starting stance", "good": "Opposite foot forward, weight on the back foot, ball held in front at waist-chest height, eyes on a target.", "fault": "Feet square or wrong foot forward; no visible target routine."},
            {"name": "Toss placement", "good": "A low straight-arm LIFT peaking 12-18 inches above full reach, in front of the hitting shoulder.", "fault": "Toss too high (server waits, timing collapses) or drifting behind the head / across the body."},
            {"name": "Draw / loading", "good": "Hitting elbow draws back high (bow-and-arrow), hips and shoulders turn slightly, back leg loads.", "fault": "Elbow drops below the shoulder or the arm swings from the waist."},
            {"name": "Contact point", "good": "Contact at full arm extension, in front of the hitting shoulder, firm flat hand behind the middle of the ball.", "fault": "Bent elbow at contact, or ball contacted above/behind the head."},
            {"name": "Weight transfer", "good": "Weight flows back-foot to front-foot through contact; body moves toward the target.", "fault": "All arm — feet stay planted flat, no step or drift into the court."},
            {"name": "Follow-through", "good": "Hand continues toward the target (float: abbreviated stop, stiff wrist; topspin: hand wraps over).", "fault": "Arm DECELERATES before contact — a poke instead of a swing; or the arm wraps across the body, sending it wide."},
        ],
    },
    "passing": {
        "camera": "Face the camera from where the ball comes from (or 45°), whole body in frame including feet.",
        "checkpoints": [
            {"name": "Ready position", "good": "Feet wider than shoulders, knees bent, weight forward on the balls of the feet, hands apart and relaxed in front.", "fault": "Standing tall with hands already clasped together."},
            {"name": "Feet to the ball", "good": "Moves and STOPS behind the ball before it arrives — ball played between the knees.", "fault": "Reaching sideways for the ball while still moving."},
            {"name": "Platform", "good": "Heels of the hands together, thumbs side by side and EVEN, elbows locked — one flat surface built early, adjusted late.", "fault": "Uneven thumbs / bent elbows, or the 'praying' double-move: arms up, down, then up again through the ball."},
            {"name": "Contact", "good": "Ball contacts the forearms above the wrists; shoulders shrug slightly; legs provide the lift.", "fault": "Ball hits the hands/thumbs, or a big arm swing sends it over the head."},
            {"name": "Platform angle", "good": "Platform angled toward the target; inside shoulder drops on angled passes.", "fault": "Platform faces where the ball came from, not where it should go."},
            {"name": "Finish", "good": "Still and balanced after contact, hands finish below shoulders, eyes tracking the pass.", "fault": "Falling backward or spinning away before the ball leaves."},
        ],
    },
    "setting": {
        "camera": "Front-on or 45° from the front, close enough to see hand shape above the forehead.",
        "checkpoints": [
            {"name": "Feet to the ball", "good": "Beats the ball to the spot and stops; right foot slightly forward; ball taken above the forehead.", "fault": "Setting on the move or letting the ball drop to chest height."},
            {"name": "Hand shape", "good": "Hands make a ball-shaped window above the forehead BEFORE the ball arrives; thumbs and index fingers form a triangle.", "fault": "Hands flat, late, or catching too low/in front of the face."},
            {"name": "Contact", "good": "All ten fingers touch simultaneously; ball in and out quickly with no spin.", "fault": "Uneven hands (double contact) or slapping with palms."},
            {"name": "Body line", "good": "Shoulders and hips square to the target; ball, forehead, and target in one line.", "fault": "Twisting mid-set or drifting sideways with the momentum of the pass."},
            {"name": "Extension", "good": "Arms AND legs extend together — finish tall, wrists flick toward the target, hands finish 'in the window'.", "fault": "All arms, no legs; or elbows flare wide killing accuracy."},
            {"name": "Result flight", "good": "Set travels with little to no spin, peaks where the hitter can attack it 2-3 ft off the net.", "fault": "Heavy spin (uneven contact) or set drifting tight/into the net."},
        ],
    },
    "attacking": {
        "camera": "Side view from your hitting-arm side, far enough to see the full approach and the jump.",
        "checkpoints": [
            {"name": "Start position", "good": "Starts behind the 3-m line (outside the court for an OH), relaxed, watching the setter.", "fault": "Starting under the net with no room to approach."},
            {"name": "Approach tempo", "good": "Slow-to-fast: small directional step, then a LONG, low, fast second-to-last step and a SHORT, quick last step (left-RIGHT-left for righties).", "fault": "Even-tempo jog with no acceleration, or a huge final stride that broad-jumps forward."},
            {"name": "Plant", "good": "Last two steps land quickly heel-to-toe, feet near shoulder width, knees deeply bent, hips loaded — momentum converts UP.", "fault": "Feet far apart or one leaping stride; jumping off one foot; drifting into the net."},
            {"name": "Arm backswing", "good": "BOTH arms swing back on the plant, then drive up hard together — the lift comes with the arms.", "fault": "Arms stay low or only the hitting arm moves."},
            {"name": "Hitting position in air", "good": "Bow-and-arrow: hitting elbow high and back, hand above the ear, off-arm pointing at the ball.", "fault": "Elbow drops ('pushing' the ball) or hand behind the head."},
            {"name": "Contact", "good": "Contact at full extension, at the peak of the jump, in FRONT of the hitting shoulder; a fast, loose hand finishes over the top of the ball.", "fault": "Ball behind the head (late/under the set), bent-arm contact, or contact on the way down."},
            {"name": "Landing", "good": "Two-foot balanced landing, knees bending to absorb, ready to transition.", "fault": "One-foot landing or drifting into the net/center line."},
        ],
    },
    "blocking": {
        "camera": "Front-on from across the net if possible, otherwise side view at the net; hands and feet both in frame.",
        "checkpoints": [
            {"name": "Ready stance", "good": "Feet shoulder-width, knees flexed, hands up at shoulder-to-eye height, palms forward, eyes on the hitter.", "fault": "Hands down at the waist — they'll be late over the net."},
            {"name": "Footwork to the spot", "good": "Shuffle for short trips, crossover-step-close for long ones; hips stay square to the net the whole way.", "fault": "Turning and running with hips open, arriving unsquared."},
            {"name": "Jump timing", "good": "Loads and jumps just after the hitter (set-dependent) — hands over as the hitter swings.", "fault": "Jumping with (or before) the hitter on a high set, landing as they contact."},
            {"name": "Penetration", "good": "Hands press OVER the net into the opponent's space, arms angled down-and-over ('pike'), shoulders shrugged.", "fault": "Swatting down or reaching straight up behind the net tape."},
            {"name": "Hands", "good": "Fingers spread wide and firm, thumbs up, hands about a ball-width apart, sealed toward the ball.", "fault": "Soft separated hands — the ball tools off them out of bounds."},
            {"name": "Body control + landing", "good": "Jumps straight up (no drift into the net), lands balanced, turns to find the ball.", "fault": "Broad-jumping into the net or landing facing away from play."},
        ],
    },
    "digging": {
        "camera": "Front-on from the direction of the attack (or 45°), whole body in frame.",
        "checkpoints": [
            {"name": "Base position", "good": "Low, stopped, and balanced BEFORE the attacker contacts: feet wide, weight forward, hands free in front.", "fault": "Still moving (or standing tall) when the hitter swings."},
            {"name": "Read posture", "good": "Eyes go to the hitter's approach and shoulder, not just the ball; body leans toward the likely angle.", "fault": "Ball-watching — frozen by tips and cut shots."},
            {"name": "Contact", "good": "Ball taken low and in front on a still platform angled UP; absorbs pace (soft give) instead of swinging.", "fault": "Swinging at a hard-driven ball, sending it straight back over."},
            {"name": "Platform direction", "good": "Dig targets high to the middle of the court — 10 ft up, off the net.", "fault": "Flat platform facing the attacker returns the ball to them."},
            {"name": "Emergency skills", "good": "Sprawl/extension used to keep low balls off the floor, then quick recovery to the feet.", "fault": "Bending at the waist and stabbing down at the ball."},
        ],
    },
}


def video_rubric_text(skill_key: str) -> str:
    """Rubric as prompt text for the Film Room vision review."""
    r = VIDEO_RUBRICS.get(skill_key)
    if not r:
        return ""
    name = next((s["name"] for s in SKILLS if s["key"] == skill_key), skill_key)
    lines = [f"Video review rubric — {name} (checkpoint / what good looks like / common youth fault):"]
    lines += [f"- {c['name']} | GOOD: {c['good']} | COMMON FAULT: {c['fault']}"
              for c in r["checkpoints"]]
    return "\n".join(lines)


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
