import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import PlayerApp from "./player/PlayerApp.jsx";
import "./styles.css";

// Inside the Capacitor iOS shell the webview reports display-mode "browser",
// so the standalone-PWA media query never fires. Tag the root instead and let
// the CSS treat .is-native like installed mode (safe areas, no URL bar).
if (window.Capacitor?.isNativePlatform?.()) {
  document.documentElement.classList.add("is-native");
  // The iOS app IS the Player Zone: launch straight into it, never the
  // coach chooser (still reachable via the in-app "Coach tools" link).
  if (!location.hash) location.hash = "#player";
}

// Two surfaces, one app: the coach tool (default) and the Player Zone
// (#player). Hash routing keeps it dead simple — no router dependency.
function Root() {
  const [hash, setHash] = useState(location.hash);
  useEffect(() => {
    const onChange = () => setHash(location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash.startsWith("#player") ? <PlayerApp /> : <App />;
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
