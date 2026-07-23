// Where the API lives, for every runtime the frontend ships in:
//   - Vite dev server: "/api" (proxied to localhost:8000, see vite.config.js)
//   - Web prod: "" — same-origin, FastAPI serves the SPA and the API together
//   - Capacitor iOS: the WebView origin is capacitor://localhost, so relative
//     URLs would go nowhere. Call the Railway deployment directly (CORS on the
//     backend already allows it — verified 2026-07-21).
const RAILWAY = "https://volleyball-api-production.up.railway.app";

const isNative = typeof window !== "undefined" && window.Capacitor?.isNativePlatform?.();

export const API_BASE = isNative ? RAILWAY : import.meta.env.PROD ? "" : "/api";
