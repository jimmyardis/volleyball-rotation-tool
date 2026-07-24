// Loading = her volleyball, spinning (both surfaces use the same one).
import BallSpinner from "./BallSpinner.jsx";

export default function Loader({ label = "Loading…" }) {
  return <BallSpinner label={label} />;
}
