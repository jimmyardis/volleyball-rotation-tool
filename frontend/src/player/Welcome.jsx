// First-launch welcome: a full-screen, swipeable three-slide intro that ends
// in "Get started". This is the app's front door on iOS (the coach chooser is
// a web-only concern) — it shows once, then signed-out users land on sign-in.

import { useRef, useState } from "react";
import Volleyball from "../components/Volleyball.jsx";
import { tap } from "../haptics.js";

const SLIDES = [
  {
    key: "hello",
    art: (
      <div className="pz-hero-mark">
        <Volleyball size={132} />
      </div>
    ),
    title: "Player Zone",
    body: "Your own coach, your own plan, your own progress — built around how you play.",
  },
  {
    key: "plan",
    art: (
      <div className="pz-mock-card" aria-hidden="true">
        {[
          { label: "Toss height: 10 clean tosses", done: true },
          { label: "Wall serves — 15 in a row", done: true },
          { label: "Film one serve for Coach", done: false },
        ].map((r) => (
          <div key={r.label} className={`pz-mock-row ${r.done ? "done" : ""}`}>
            <span className="pz-mock-tick">{r.done ? "✓" : ""}</span>
            <span>{r.label}</span>
          </div>
        ))}
      </div>
    ),
    title: "A plan that grows with you",
    body: "Pick your position, rate your skills, and get goals that unlock as you master them.",
  },
  {
    key: "film",
    art: (
      <div className="pz-mock-film" aria-hidden="true">
        <div className="pz-mock-lens">
          <Volleyball size={56} />
        </div>
        <div className="pz-mock-frames">
          <span /><span /><span />
        </div>
      </div>
    ),
    title: "Film a rep, get coached",
    body: "Record one serve or pass and Coach breaks it down frame by frame. Your video never leaves your phone.",
  },
];

export default function Welcome({ onStart }) {
  const [index, setIndex] = useState(0);
  const trackRef = useRef(null);

  function onScroll() {
    const el = trackRef.current;
    if (!el) return;
    const i = Math.round(el.scrollLeft / el.clientWidth);
    if (i !== index) { setIndex(i); tap(); }
  }

  return (
    <div className="pz-welcome">
      <div className="pz-carousel" ref={trackRef} onScroll={onScroll}>
        {SLIDES.map((s) => (
          <section key={s.key} className="pz-slide">
            {s.art}
            <h2>{s.title}</h2>
            <p>{s.body}</p>
          </section>
        ))}
      </div>

      <div className="pz-dots" role="tablist" aria-label="Intro pages">
        {SLIDES.map((s, i) => (
          <span key={s.key} className={`pz-dot ${i === index ? "active" : ""}`} />
        ))}
      </div>

      <div className="pz-welcome-actions">
        <button className="pz-cta" onClick={() => onStart("register")}>Get started</button>
        <button className="link" onClick={() => onStart("login")}>I already have an account</button>
      </div>
    </div>
  );
}
