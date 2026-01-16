function getVideo() {
  return document.querySelector("video");
}

function clickIf(selector) {
  const el = document.querySelector(selector);
  if (el) { el.click(); return true; }
  return false;
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  try {
    if (!msg || msg.type !== "YT_CMD") return;

    const v = getVideo();
    const cmd = msg.command;

    if (cmd === "play") {
      if (v) v.play();
      return sendResponse({ ok: true });
    }

    if (cmd === "pause") {
      if (v) v.pause();
      return sendResponse({ ok: true });
    }

    if (cmd === "toggle") {
      if (v) (v.paused ? v.play() : v.pause());
      return sendResponse({ ok: true });
    }

    if (cmd === "volume_up") {
      if (v) v.volume = Math.min(1, v.volume + 0.05);
      return sendResponse({ ok: true });
    }

    if (cmd === "volume_down") {
      if (v) v.volume = Math.max(0, v.volume - 0.05);
      return sendResponse({ ok: true });
    }

    if (cmd === "set_volume") {
      const value = typeof msg.value === "number" ? msg.value : 0.5;
      if (v) v.volume = Math.max(0, Math.min(1, value));
      return sendResponse({ ok: true });
    }

    if (cmd === "seek_forward") {
      if (v) v.currentTime = Math.max(0, v.currentTime + 10);
      return sendResponse({ ok: true });
    }

    if (cmd === "seek_backward") {
      if (v) v.currentTime = Math.max(0, v.currentTime - 10);
      return sendResponse({ ok: true });
    }

    if (cmd === "next") {
      if (clickIf(".ytp-next-button")) return sendResponse({ ok: true });
      return sendResponse({ ok: false, error: "No next button" });
    }

    if (cmd === "prev") {
      // SIEMPRE volver al video anterior (historial)
      history.back();
      return sendResponse({ ok: true, mode: "history_back" });
    }

    return sendResponse({ ok: false, error: "Comando no soportado" });

  } catch (e) {
    return sendResponse({ ok: false, error: String(e) });
  }
});
