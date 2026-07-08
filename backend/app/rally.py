"""Rally engine — Phase 3's touch-by-touch set simulator.

Pure functions, no I/O (same contract as engine.py). One simulated point is a
chain of real volleyball events — serve -> pass -> set -> attack -> block/dig
-> counterattack — where every touch names a player and rolls against their
actual ratings and tagged mistake tendencies. A set is rally-scored to
`target` (win by 2), with real rotation tracking on sideouts.

Vocabulary:
    rotations      the 6 on-court states (positions dicts), subs applied —
                   rotation r's six actually play rotation r.
    mistakes       {player_id: {mistake_key: severity}} from the coach.
    stakes         0..1, how big the moment is (late + close = high). A
                   player's low `pressure` rating makes their tagged
                   mistakes MORE likely as stakes rise (mistake_multiplier).
    phantom team   the opponent six generated from the difficulty slider;
                   negative player ids so they can never collide with ours.

Events are compact dicts ({"k": kind, ...}) meant for frontend playback; the
narration text lives in the UI, not here.
"""

from __future__ import annotations

from . import engine

# ---------------------------------------------------------------------------
# Mistake catalog — every entry is wired to a specific moment in the rally.
# `moment` is documentation + UI grouping; the engine hooks are explicit in
# the code below (grep the key). Severity scales how often it bites.
# ---------------------------------------------------------------------------

MISTAKE_CATALOG: dict[str, dict] = {
    "serve_net":  {"label": "Serves into the net",        "moment": "serving"},
    "serve_long": {"label": "Serves long / wide",         "moment": "serving"},
    "shank_pass": {"label": "Shanks tough serves",        "moment": "serve receive"},
    "net_hit":    {"label": "Hits into the net",          "moment": "attacking"},
    "hit_out":    {"label": "Hits out against a big block", "moment": "attacking"},
    "net_touch":  {"label": "Net touches when blocking",  "moment": "blocking"},
    "ball_watch": {"label": "Ball-watches on defense",    "moment": "defense"},
    "lost_rotation": {"label": "Gets lost in the rotation", "moment": "positioning"},
}

SEVERITIES = ("sometimes", "often")
_SEV_MULT = {"sometimes": 1.0, "often": 2.2}

SCORE_CAP = 40  # runtime bound; a real set practically never gets here

# Probability constants, grouped for tuning. All skills are 0-100.
SERVE_ERR_BASE = 0.045
SERVE_ERR_SKILL = 0.07      # + this much at skill 0, scaled down to 0 at 100
MISTAKE_SERVE = 0.055       # each tagged serve mistake adds this * sev * pressure
SHANK_BASE = 0.09
MISTAKE_SHANK = 0.8         # multiplies shank prob (tough serves only)
MISTAKE_ATTACK = 0.05
MISTAKE_OVERLAP = 0.018
NET_TOUCH_GIFT = 0.30       # chance a stuff turns into the blocker's net touch
BALL_WATCH_KILL = 0.05      # opponent kill prob bonus per ball-watching defender
MAX_TRANSITIONS = 6


def mistake_multiplier(stakes: float, pressure: float) -> float:
    """>= 1. How much a big moment inflates this player's mistake rates."""
    return 1.0 + stakes * (1.0 - pressure / 100.0) * 1.8


def _sev(mistakes: dict, pid: int, key: str) -> float:
    """0 if the player isn't tagged with this mistake, else its severity mult."""
    return _SEV_MULT.get((mistakes.get(pid) or {}).get(key, ""), 0.0)


def _a(player: dict, key: str) -> float:
    v = player.get(key)
    return float(v) if v is not None else 50.0


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

_PHANTOM_ROLES = ["S", "OH", "MB", "OPP", "OH", "MB"]


def phantom_team(skill: float, rng) -> dict[int, dict]:
    """Six generic opponents around `skill`. Negative ids, generic names."""
    team: dict[int, dict] = {}
    names = {"S": "their setter", "OH": "their outside", "MB": "their middle",
             "OPP": "their right side"}
    seen: dict[str, int] = {}
    for i, role in enumerate(_PHANTOM_ROLES):
        pid = -(i + 1)
        jitter = rng.uniform(-6, 6)
        attrs = {a: max(15.0, min(95.0, skill + jitter + rng.uniform(-4, 4)))
                 for a in engine.ATTRS}
        seen[role] = seen.get(role, 0) + 1
        suffix = f" #{seen[role]}" if _PHANTOM_ROLES.count(role) > 1 else ""
        team[pid] = {"id": pid, "name": names[role] + suffix,
                     "jersey_number": i + 7, "primary_role": role,
                     "is_libero": False, **attrs}
    return team


class _Side:
    """One team's live state during a set. Not exported."""

    def __init__(self, key, players, positions, mistakes, rotations=None):
        self.key = key                      # "us" | "them"
        self.players = players
        self.positions = dict(positions)
        self.mistakes = mistakes
        self.rotations = rotations          # our 6 effective states, or None
        self.rot = 0

    def rotate(self):
        self.rot = (self.rot + 1) % 6
        if self.rotations:
            self.positions = dict(self.rotations[self.rot])
        else:
            self.positions = engine.rotate_once(self.positions)

    def on_court(self):
        return [self.players[pid] for pid in self.positions.values()]

    def zone_players(self, zones):
        return [self.players[self.positions[z]] for z in zones]

    def setter(self):
        six = self.on_court()
        for p in six:
            if p.get("primary_role") == "S":
                return p
        return max(six, key=lambda p: _a(p, "setting"))

    def attackers(self):
        fronts = self.zone_players(engine.FRONT_ROW)
        pool = [p for p in fronts
                if p.get("primary_role") != "S" and not p.get("is_libero")]
        return pool or fronts

    def front_avg(self, key):
        f = self.zone_players(engine.FRONT_ROW)
        return sum(_a(p, key) for p in f) / len(f)

    def back_avg(self, key):
        b = self.zone_players(engine.BACK_ROW)
        return sum(_a(p, key) for p in b) / len(b)


def _weighted(rng, items, weight):
    weights = [max(weight(x), 0.01) for x in items]
    total = sum(weights)
    r = rng.uniform(0, total)
    acc = 0.0
    for x, w in zip(items, weights):
        acc += w
        if r <= acc:
            return x
    return items[-1]


# ---------------------------------------------------------------------------
# One rally
# ---------------------------------------------------------------------------

def _play_rally(serve_side: _Side, recv_side: _Side, stakes, rng, emit):
    """Play one point. Returns (winner_key, reason, credit) where credit is
    {player_id: {stat: +n}} increments for OUR players only."""
    credit: dict[int, dict] = {}

    def bump(side, pid, stat, n=1):
        if side.key == "us":
            credit.setdefault(pid, {}).setdefault(stat, 0)
            credit[pid][stat] += n

    server = serve_side.players[serve_side.positions[engine.SERVER_ZONE]]
    sid = server["id"]
    press = mistake_multiplier(stakes, _a(server, "pressure"))

    # -- lost_rotation: a tagged receiver lines up wrong -> overlap call
    for p in recv_side.on_court():
        sev = _sev(recv_side.mistakes, p["id"], "lost_rotation")
        if sev and rng.random() < MISTAKE_OVERLAP * sev * mistake_multiplier(
                stakes, _a(p, "pressure")):
            emit({"k": "overlap", "tm": recv_side.key, "p": p["id"]})
            bump(recv_side, p["id"], "mistake_points")
            return serve_side.key, "overlap", credit

    # -- serve
    emit({"k": "serve", "tm": serve_side.key, "p": sid})
    p_err = SERVE_ERR_BASE + SERVE_ERR_SKILL * (1 - _a(server, "serving") / 100)
    sev_net = _sev(serve_side.mistakes, sid, "serve_net")
    sev_long = _sev(serve_side.mistakes, sid, "serve_long")
    p_err += MISTAKE_SERVE * (sev_net + sev_long) * press
    if rng.random() < p_err:
        tagged = (sev_net + sev_long) > 0
        how = "net" if rng.random() < (sev_net + 0.5) / (sev_net + sev_long + 1.0) else "long"
        emit({"k": "serve_error", "tm": serve_side.key, "p": sid,
              "how": how, "mk": tagged})
        bump(serve_side, sid, "serve_errors")
        if tagged:
            bump(serve_side, sid, "mistake_points")
        return recv_side.key, "serve_error", credit

    toughness = _a(server, "serving") + rng.uniform(-12, 18)

    # -- serve receive
    backs = recv_side.zone_players(engine.BACK_ROW)
    passer = _weighted(
        rng, backs,
        lambda p: (1.7 if p.get("is_libero") else 1.0)
        * (1.25 if _sev(recv_side.mistakes, p["id"], "shank_pass") else 1.0))
    d = (_a(passer, "defense") - 0.75 * toughness) / 100.0
    p_shank = min(0.5, max(0.02, SHANK_BASE - 0.30 * d))
    sev_shank = _sev(recv_side.mistakes, passer["id"], "shank_pass")
    if sev_shank and toughness > 55:
        p_shank *= 1 + MISTAKE_SHANK * sev_shank * mistake_multiplier(
            stakes, _a(passer, "pressure"))
    if rng.random() < min(0.6, p_shank):
        emit({"k": "ace", "tm": serve_side.key, "p": sid,
              "victim": passer["id"], "mk": bool(sev_shank)})
        bump(serve_side, sid, "aces")
        bump(recv_side, passer["id"], "shanks")
        if sev_shank:
            bump(recv_side, passer["id"], "mistake_points")
        return serve_side.key, "ace", credit
    p3 = min(0.75, max(0.05, 0.35 + 0.5 * d))
    roll = rng.random()
    pass_q = 3 if roll < p3 else (2 if roll < p3 + (1 - p3) * 0.6 else 1)
    emit({"k": "pass", "tm": recv_side.key, "p": passer["id"], "q": pass_q})
    bump(recv_side, passer["id"], "passes")

    # -- attack / counterattack loop
    atk_side, def_side = recv_side, serve_side
    quality = pass_q / 3.0
    for transition in range(MAX_TRANSITIONS):
        setter = atk_side.setter()
        set_q = max(0.2, min(1.0, 0.42 + 0.36 * _a(setter, "setting") / 100
                             + 0.15 * quality - 0.08 * transition))
        attacker = _weighted(rng, atk_side.attackers(),
                             lambda p: (_a(p, "attacking") / 100) ** 1.5)
        aid = attacker["id"]
        emit({"k": "set", "tm": atk_side.key, "p": setter["id"], "target": aid})

        blk = def_side.front_avg("blocking")
        dig = def_side.back_avg("defense")
        apress = mistake_multiplier(stakes, _a(attacker, "pressure"))

        p_kill = max(0.08, min(0.85, 0.16 + 0.52 * _a(attacker, "attacking") / 100
                               + 0.20 * (set_q - 0.5)
                               - 0.30 * (0.5 * blk + 0.5 * dig) / 100))
        for p in def_side.on_court():
            if _sev(def_side.mistakes, p["id"], "ball_watch"):
                p_kill += BALL_WATCH_KILL * _sev(def_side.mistakes, p["id"], "ball_watch")
        sev_nh = _sev(atk_side.mistakes, aid, "net_hit")
        sev_ho = _sev(atk_side.mistakes, aid, "hit_out") if blk > 58 else 0.0
        p_err = 0.06 + 0.05 * (1 - set_q) + MISTAKE_ATTACK * (sev_nh + sev_ho) * apress
        p_stuff = max(0.01, min(0.2, 0.03 + 0.09 * blk / 100 - 0.03 * set_q))

        roll = rng.random()
        if roll < p_kill:
            emit({"k": "attack", "tm": atk_side.key, "p": aid, "out": "kill"})
            bump(atk_side, aid, "kills")
            return atk_side.key, "kill", credit
        roll -= p_kill
        if roll < p_err:
            tagged = (sev_nh + sev_ho) > 0
            how = "net" if rng.random() < (sev_nh + 0.5) / (sev_nh + sev_ho + 1.0) else "out"
            emit({"k": "attack", "tm": atk_side.key, "p": aid, "out": "error",
                  "how": how, "mk": tagged})
            bump(atk_side, aid, "attack_errors")
            if tagged:
                bump(atk_side, aid, "mistake_points")
            return def_side.key, "attack_error", credit
        roll -= p_err
        if roll < p_stuff:
            blocker = _weighted(rng, def_side.zone_players(engine.FRONT_ROW),
                                lambda p: (_a(p, "blocking") / 100) ** 2)
            sev_nt = _sev(def_side.mistakes, blocker["id"], "net_touch")
            if sev_nt and rng.random() < NET_TOUCH_GIFT * sev_nt * mistake_multiplier(
                    stakes, _a(blocker, "pressure")):
                emit({"k": "net_touch", "tm": def_side.key, "p": blocker["id"]})
                bump(def_side, blocker["id"], "mistake_points")
                return atk_side.key, "net_touch", credit
            emit({"k": "block", "tm": def_side.key, "p": blocker["id"]})
            bump(def_side, blocker["id"], "stuffs")
            return def_side.key, "stuff", credit
        # dug -> rally continues the other way
        digger = _weighted(rng, def_side.zone_players(engine.BACK_ROW),
                           lambda p: (_a(p, "defense") / 100) ** 1.5)
        emit({"k": "attack", "tm": atk_side.key, "p": aid, "out": "dug"})
        emit({"k": "dig", "tm": def_side.key, "p": digger["id"]})
        bump(def_side, digger["id"], "digs")
        atk_side, def_side = def_side, atk_side
        quality = 0.6  # transition ball

    # scramble: nobody could finish — weighted coin on overall strength
    a_str = atk_side.front_avg("attacking") + atk_side.back_avg("defense")
    d_str = def_side.front_avg("attacking") + def_side.back_avg("defense")
    winner = atk_side if rng.uniform(0, a_str + d_str) < a_str else def_side
    emit({"k": "scramble", "tm": winner.key})
    return winner.key, "scramble", credit


# ---------------------------------------------------------------------------
# One set
# ---------------------------------------------------------------------------

def _stakes(us: int, them: int, target: int) -> float:
    mx = max(us, them)
    late = max(0.0, (mx - 18) / (target - 18)) if target > 18 else 0.0
    close = 0.2 if mx >= 15 and abs(us - them) <= 2 else 0.0
    return min(1.0, late + close)


def simulate_set(start, players, mistakes, opponent_skill, rng, target=25,
                 rotations=None, collect_events=True):
    """Simulate one rally-scored set. We serve first (rotation 0's server).

    start:      {zone: player_id} for OUR starting six.
    players:    {player_id: player dict} (extras like the libero are fine).
    mistakes:   {player_id: {mistake_key: severity}}.
    rotations:  optional 6 effective positions dicts (subs applied); falls
                back to pure clockwise rotation of `start`.
    """
    opp_players = phantom_team(opponent_skill, rng)
    us = _Side("us", players, (rotations[0] if rotations else start),
               mistakes, rotations)
    them = _Side("them", opp_players,
                 {z: -((i % 6) + 1) for i, z in enumerate(engine.ZONES)}, {})

    events: list[dict] = []
    emit = events.append if collect_events else (lambda e: None)

    rotation_stats = [{"serve_points": 0, "serve_won": 0,
                       "recv_points": 0, "recv_won": 0} for _ in range(6)]
    player_stats: dict[int, dict] = {pid: {} for pid in players}

    score = {"us": 0, "them": 0}
    serving = "us"
    while True:
        emit({"k": "rally_start", "server": serving, "us_rot": us.rot,
              "score": [score["us"], score["them"]]})
        stakes = _stakes(score["us"], score["them"], target)
        serve_side, recv_side = (us, them) if serving == "us" else (them, us)
        winner, reason, credit = _play_rally(serve_side, recv_side, stakes, rng, emit)

        for pid, stats in credit.items():
            for stat, n in stats.items():
                player_stats[pid][stat] = player_stats[pid].get(stat, 0) + n

        score[winner] += 1
        bucket = rotation_stats[us.rot]
        if serving == "us":
            bucket["serve_points"] += 1
            bucket["serve_won"] += winner == "us"
        else:
            bucket["recv_points"] += 1
            bucket["recv_won"] += winner == "us"

        emit({"k": "point", "winner": winner, "reason": reason,
              "score": [score["us"], score["them"]], "us_rot": us.rot})

        u, t = score["us"], score["them"]
        if ((u >= target or t >= target) and abs(u - t) >= 2) or max(u, t) >= SCORE_CAP:
            break

        if winner != serving:                     # sideout -> winner rotates
            (us if winner == "us" else them).rotate()
            if winner == "us":
                emit({"k": "rotate", "tm": "us", "us_rot": us.rot})
            serving = winner

    emit({"k": "set_end", "score": [score["us"], score["them"]],
          "won": score["us"] > score["them"]})
    return {
        "score": score,
        "won": score["us"] > score["them"],
        "events": events,
        "rotation_stats": rotation_stats,
        "player_stats": player_stats,
        "opp_players": opp_players,
    }


# ---------------------------------------------------------------------------
# Batches + insights
# ---------------------------------------------------------------------------

def simulate_batch(start, players, mistakes, opponent_skill, sets=200, seed=None,
                   rotations=None):
    """Run many sets and aggregate per-rotation and per-player numbers."""
    import random as _random
    rng = _random.Random(seed)
    rots = rotations or engine.all_rotations(start)

    agg_rot = [{"serve_points": 0, "serve_won": 0, "recv_points": 0, "recv_won": 0}
               for _ in range(6)]
    agg_players: dict[int, dict] = {pid: {} for pid in players}
    won = 0
    for _ in range(sets):
        r = simulate_set(start, players, mistakes, opponent_skill, rng,
                         rotations=rots, collect_events=False)
        won += r["won"]
        for i, b in enumerate(r["rotation_stats"]):
            for k, v in b.items():
                agg_rot[i][k] += v
        for pid, stats in r["player_stats"].items():
            for k, v in stats.items():
                agg_players[pid][k] = agg_players[pid].get(k, 0) + v

    rotations_out = []
    for i, b in enumerate(agg_rot):
        points = b["serve_points"] + b["recv_points"]
        rotations_out.append({
            "rot": i,
            **b,
            "sideout_pct": (b["recv_won"] / b["recv_points"]) if b["recv_points"] else 0.0,
            "serve_win_pct": (b["serve_won"] / b["serve_points"]) if b["serve_points"] else 0.0,
            "point_win_pct": ((b["serve_won"] + b["recv_won"]) / points) if points else 0.0,
            "server_id": rots[i][engine.SERVER_ZONE],
            "attacker_count": len([
                p for z, p in rots[i].items() if z in engine.FRONT_ROW
                and players[p].get("primary_role") != "S"
                and not players[p].get("is_libero")
            ]),
        })
    return {
        "sets": sets,
        "win_rate": won / sets if sets else 0.0,
        "rotations": rotations_out,
        "player_stats": agg_players,
    }


def _name(players, pid):
    p = players.get(pid) or {}
    return p.get("name") or f"#{p.get('jersey_number', '?')}"


def generate_insights(batch, players) -> list[dict]:
    """Plain-English best/worst callouts, computed — never invented."""
    out: list[dict] = []
    sets = max(1, batch["sets"])
    rots = batch["rotations"]

    best = max(rots, key=lambda r: r["point_win_pct"])
    worst = min(rots, key=lambda r: r["point_win_pct"])

    def why(r, good):
        serve, recv = r["serve_win_pct"], r["sideout_pct"]
        server = _name(players, r["server_id"])
        if good:
            edge = ("serve runs behind " + server) if serve >= recv else "strong siding out"
            extra = f" with {r['attacker_count']} front-row attackers" if r["attacker_count"] >= 3 else ""
            return f"{edge}{extra}"
        weak = ("struggles on serve receive — it sided out only "
                f"{round(r['sideout_pct'] * 100)}% of the time") if recv <= serve else (
               f"gives points back when {server} serves")
        return weak

    out.append({"kind": "best", "text":
                f"Rotation {best['rot'] + 1} was your best — it won "
                f"{round(best['point_win_pct'] * 100)}% of its points, mostly on {why(best, True)}."})
    out.append({"kind": "worst", "text":
                f"Rotation {worst['rot'] + 1} was your weakest — it won only "
                f"{round(worst['point_win_pct'] * 100)}% of its points; it {why(worst, False)}."})

    stats = batch["player_stats"]

    def per_set(pid, key):
        return stats.get(pid, {}).get(key, 0) / sets

    killers = sorted(stats, key=lambda pid: stats[pid].get("kills", 0), reverse=True)
    if killers and stats[killers[0]].get("kills", 0):
        pid = killers[0]
        out.append({"kind": "player", "text":
                    f"{_name(players, pid)} was your go-to attacker — about "
                    f"{per_set(pid, 'kills'):.1f} kills per set."})

    acers = sorted(stats, key=lambda pid: stats[pid].get("aces", 0), reverse=True)
    if acers and per_set(acers[0], "aces") >= 0.5:
        pid = acers[0]
        out.append({"kind": "serve", "text":
                    f"{_name(players, pid)}'s serve was a weapon: "
                    f"{per_set(pid, 'aces'):.1f} aces per set."})

    costly = sorted(stats, key=lambda pid: stats[pid].get("mistake_points", 0), reverse=True)
    if costly and per_set(costly[0], "mistake_points") >= 0.6:
        pid = costly[0]
        out.append({"kind": "mistake", "text":
                    f"{_name(players, pid)}'s tagged mistakes cost about "
                    f"{per_set(pid, 'mistake_points'):.1f} points per set — "
                    "worth a practice focus."})

    if best["attacker_count"] > worst["attacker_count"]:
        out.append({"kind": "lineup", "text":
                    "You score best with more front-row attackers — the top "
                    "rotation had "
                    f"{best['attacker_count']} up front, the weakest only "
                    f"{worst['attacker_count']}."})
    return out
