import { useEffect, useRef, useState } from "react";
import { subscribeToLoading } from "../api/loadingIndicator";

export function TopLoadingBar() {
  const [visible, setVisible] = useState(false);
  const [progress, setProgress] = useState(0);
  const growTimer = useRef<number | null>(null);
  const hideTimer = useRef<number | null>(null);

  useEffect(() => {
    return subscribeToLoading((isLoading) => {
      if (growTimer.current) window.clearInterval(growTimer.current);
      if (hideTimer.current) window.clearTimeout(hideTimer.current);

      if (isLoading) {
        setVisible(true);
        setProgress(20);
        // Creeps toward (but never reaches) 90% while the request is in
        // flight, so it always reads as "still working" rather than stalled.
        growTimer.current = window.setInterval(() => {
          setProgress((p) => (p < 90 ? p + (90 - p) * 0.15 : p));
        }, 200);
      } else {
        setProgress(100);
        hideTimer.current = window.setTimeout(() => {
          setVisible(false);
          setProgress(0);
        }, 200);
      }
    });
  }, []);

  if (!visible) return null;
  return (
    <div className="top-loading-bar-track">
      <div className="top-loading-bar" style={{ width: `${progress}%` }} />
    </div>
  );
}
