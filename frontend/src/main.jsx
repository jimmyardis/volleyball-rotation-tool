import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import PlayerApp from "./player/PlayerApp.jsx";
import "./styles.css";

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
