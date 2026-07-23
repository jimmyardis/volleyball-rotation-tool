// Tiny haptics wrapper: real taps in the iOS app, silent no-op on the web
// (the plugin's web fallback would try navigator.vibrate, which iOS Safari
// doesn't have — skipping keeps the PWA behavior unchanged).
import { Haptics, ImpactStyle, NotificationType } from "@capacitor/haptics";

const native = typeof window !== "undefined" && window.Capacitor?.isNativePlatform?.();

export const tap = () => { if (native) Haptics.impact({ style: ImpactStyle.Light }).catch(() => {}); };
export const success = () => { if (native) Haptics.notification({ type: NotificationType.Success }).catch(() => {}); };
