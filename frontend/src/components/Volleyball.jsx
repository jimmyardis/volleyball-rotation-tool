// The volleyball mark — her chosen art (assets/volleyball.png, ink on
// transparent alpha, extracted from her upload 2026-07-23). Replaces the
// old drawn-SVG mark everywhere it was used.
import ball from "../assets/volleyball.png";

export default function Volleyball({ size = 26, className = "", style }) {
  return (
    <img
      className={`vb-mark pz-mark-img ${className}`}
      src={ball}
      width={size}
      height={size}
      style={style}
      alt=""
      aria-hidden="true"
    />
  );
}
