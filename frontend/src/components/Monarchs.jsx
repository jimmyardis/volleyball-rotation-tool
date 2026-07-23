// The monarch — her chosen art (assets/monarch.png, side-view orange/black
// butterfly, ink extracted onto transparent alpha from her upload
// 2026-07-23). Replaced the drawn-SVG monarch everywhere.
import monarch from "../assets/monarch.png";

export function Monarch({ size = 24, className = "", style }) {
  return (
    <img
      className={`pz-mark-img ${className}`}
      src={monarch}
      width={size}
      height={size}
      style={style}
      alt=""
      aria-hidden="true"
    />
  );
}

// ONE monarch perched on its own strip at the top of the page (Intense,
// both surfaces). In normal flow: scrolls with the page, never covers
// buttons.
export function MonarchPerch() {
  return (
    <div className="monarch-perch" aria-hidden="true">
      <Monarch size={46} />
    </div>
  );
}
