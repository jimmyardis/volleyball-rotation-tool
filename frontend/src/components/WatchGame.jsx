// Watch one simulated set like a broadcast: the wood court rotates live,
// the scoreboard ticks, and the play-by-play box narrates every touch.
// Controls: play/pause, 1x/2x/4x, next point, skip to end, new game.

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api.js";
import { zoneCenter } from "../roles.js";
import Court from "./Court.jsx";
import Loader from "./Loader.jsx";
import { narrate, eventDelay } from "../narrate.js";

export default function WatchGame({ lineupId, opponent }) {
  const [game, setGame] = useState(null);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const logRef = useRef(null);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const g = await api.simulateGame(lineupId, {
        opponent_skill: opponent,
        seed: Math.floor(Math.random() * 1e9),
      });
      setGame(g);
      setIdx(0);
      setPlaying(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const events = game?.events ?? [];

  // the clock: consume one event per tick, faster at 2x/4x
  useEffect(() => {
    if (!playing || !game || idx >= events.length) return;
    const t = setTimeout(() => setIdx((i) => i + 1), eventDelay(events[idx]) / speed);
    return () => clearTimeout(t);
  }, [playing, game, idx, speed, events]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [idx]);

  const everyone = useMemo(() => {
    if (!game) return {};
    const all = {};
    for (const p of game.players) all[p.id] = p;
    for (const p of game.opp_players) all[p.id] = p;
    return all;
  }, [game]);
  const nameOf = (pid) => everyone[pid]?.name ?? "someone";

  // current game state = the latest scoreboard-bearing event we've consumed
  const state = useMemo(() => {
    let score = [0, 0], rot = 0, serving = "us";
    for (let i = 0; i < idx && i < events.length; i++) {
      const e = events[i];
      if (e.score) score = e.score;
      if (e.us_rot != null) rot = e.us_rot;
      if (e.k === "rally_start") serving = e.server;
    }
    return { score, rot, serving };
  }, [idx, events]);

  const placements = useMemo(() => {
    if (!game) return [];
    const positions = game.rotations[state.rot];
    const setterId = Object.values(positions)
      .map((pid) => everyone[pid])
      .find((p) => p?.primary_role === "S")?.id;
    return Object.entries(positions).map(([zone, pid]) => {
      const [x, y] = zoneCenter(Number(zone));
      const p = everyone[pid] ?? {};
      return {
        key: pid, playerId: pid, name: p.name, jersey: p.jersey_number,
        role: p.primary_role, x, y,
        isServer: Number(zone) === 1 && state.serving === "us",
        isSetter: pid === setterId,
      };
    });
  }, [game, state, everyone]);

  const lines = useMemo(
    () => events.slice(0, idx).map((e) => narrate(e, nameOf)).filter(Boolean),
    [idx, events] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const done = game && idx >= events.length;

  function nextPoint() {
    for (let i = idx; i < events.length; i++) {
      if (events[i].k === "point" || events[i].k === "set_end") { setIdx(i + 1); return; }
    }
    setIdx(events.length);
  }

  if (!game) {
    return (
      <div className="watch-empty">
        {busy ? (
          <Loader label="Setting up the court…" />
        ) : (
          <>
            <p className="hint">Play a full set touch by touch — serves, passes, kills, and every
            tagged mistake, narrated as it happens.</p>
            {error && <p className="error">{error}</p>}
            <button className="primary" disabled={lineupId == null} onClick={start}>
              ▶ Watch one set
            </button>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="watch-game">
      <div className="watch-main">
        <div className="watch-scorebar">
          <span className={`watch-score ${state.serving === "us" ? "serving" : ""}`}>
            US <strong>{state.score[0]}</strong>
          </span>
          <span className="watch-rot">R{state.rot + 1}</span>
          <span className={`watch-score ${state.serving === "them" ? "serving" : ""}`}>
            <strong>{state.score[1]}</strong> THEM
          </span>
        </div>
        <Court placements={placements} />
        <div className="watch-controls">
          {!done ? (
            <button className="ghost" onClick={() => setPlaying(!playing)}>
              {playing ? "⏸ Pause" : "▶ Play"}
            </button>
          ) : (
            <button className="primary" onClick={start}>▶ New game</button>
          )}
          {[1, 2, 4].map((s) => (
            <button key={s} className={`ghost speed ${speed === s ? "active-ghost" : ""}`}
                    onClick={() => setSpeed(s)}>{s}x</button>
          ))}
          <button className="ghost" disabled={done} onClick={nextPoint}>⏭ Point</button>
          <button className="ghost" disabled={done} onClick={() => setIdx(events.length)}>Skip to end</button>
        </div>
      </div>

      <div className="narration watch-log" ref={logRef}>
        <span className="narration-title">Play-by-play</span>
        <div className="watch-lines">
          {lines.map((l, i) => (
            <p key={i} className={`watch-line tone-${l.tone} ${l.divider ? "divider" : ""} ${l.point ? "point" : ""}`}>
              {l.text}
            </p>
          ))}
          {!done && lines.length === 0 && <p className="watch-line tone-neutral">Warming up…</p>}
        </div>
      </div>
    </div>
  );
}
