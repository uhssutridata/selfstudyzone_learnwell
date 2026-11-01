(() => {
  let lastTick = Date.now();
  let wasVisible = document.visibilityState === "visible";
  let pending = 0;
  const csrf = document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith("csrftoken="))?.split("=").slice(1).join("=");
  const send = async (seconds) => {
    if (!csrf || seconds < 1) return;
    const data = new URLSearchParams({ seconds: String(Math.min(seconds, 300)) });
    try {
      await fetch("/activity/study-time/", { method: "POST", credentials: "same-origin", headers: { "X-CSRFToken": decodeURIComponent(csrf), "Content-Type": "application/x-www-form-urlencoded" }, body: data });
    } catch { /* A later interval can record the next active period. */ }
  };
  const flush = (useBeacon = false) => {
    const now = Date.now();
    if (wasVisible) pending += Math.floor((now - lastTick) / 1000);
    lastTick = now;
    const seconds = pending;
    pending = 0;
    if (seconds > 0 && useBeacon && navigator.sendBeacon) {
      const form = new URLSearchParams({ seconds: String(Math.min(seconds, 300)), csrfmiddlewaretoken: decodeURIComponent(csrf || "") });
      navigator.sendBeacon("/activity/study-time/", form);
    } else if (seconds > 0) {
      void send(seconds);
    }
    wasVisible = document.visibilityState === "visible";
  };
  window.setInterval(flush, 60000);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState !== "visible") flush(true); else { lastTick = Date.now(); wasVisible = true; } });
  window.addEventListener("pagehide", () => flush(true));
})();
