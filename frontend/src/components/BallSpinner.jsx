// Loading = her volleyball, spinning. Used anywhere the app is waiting.
import Volleyball from "./Volleyball.jsx";

export default function BallSpinner({ label = "Loading…", size = 44 }) {
  return (
    <div className="ball-spinner" role="status" aria-label={label}>
      <span className="ball-spinner-ball"><Volleyball size={size} /></span>
      <span className="hint">{label}</span>
    </div>
  );
}
