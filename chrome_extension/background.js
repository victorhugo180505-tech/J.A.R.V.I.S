let port = null;
let pingTimer = null;

function log(...args) {
  console.log("[JARVIS_EXT]", ...args);
}

function startPing() {
  stopPing();
  pingTimer = setInterval(() => {
    if (port) {
      try {
        port.postMessage({ action: "ping", ts: Date.now() });
      } catch (e) {
        // si falla, onDisconnect debería dispararse pronto
      }
    }
  }, 2000);
  log("Ping periódico iniciado");
}

function stopPing() {
  if (pingTimer) clearInterval(pingTimer);
  pingTimer = null;
}

function connectNative() {
  log("Intentando connectNative(...)");

  try {
    port = chrome.runtime.connectNative("com.victor.jarvis");
    log("connectNative() devuelto, port creado");

    startPing();

    port.onMessage.addListener((msg) => {
      log("Mensaje desde host:", msg);

      // Ignorar mensajes de control/estado
      if (msg && msg.action === "native_ready") {
        log("Native host listo");
        return;
      }

      handleNativeMessage(msg);
    });

    port.onDisconnect.addListener(() => {
      const err = chrome.runtime.lastError ? chrome.runtime.lastError.message : "(sin lastError)";
      log("DESCONEXIÓN del host. lastError:", err);
      stopPing();
      port = null;
      setTimeout(connectNative, 1500);
    });

  } catch (e) {
    log("EXCEPCIÓN en connectNative:", e);
    stopPing();
    port = null;
    setTimeout(connectNative, 2000);
  }
}

async function findYouTubeTab() {
  const active = await chrome.tabs.query({ active: true, currentWindow: true });
  if (active && active.length) {
    const t = active[0];
    if (
      t.url &&
      (t.url.startsWith("https://www.youtube.com/") ||
       t.url.startsWith("https://music.youtube.com/") ||
       t.url.startsWith("https://m.youtube.com/"))
    ) {
      return t;
    }
  }

  const tabs = await chrome.tabs.query({
    url: ["https://www.youtube.com/*", "https://music.youtube.com/*", "https://m.youtube.com/*"]
  });
  if (tabs && tabs.length) return tabs[0];

  return null;
}

function sendToYouTube(tabId, payload) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, payload, (resp) => {
      const err = chrome.runtime.lastError
        ? chrome.runtime.lastError.message
        : null;
      resolve({ resp, err });
    });
  });
}

async function ensureContentScript(tabId) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["youtube_content.js"]
    });
    log("Content script inyectado en tab:", tabId);
    return true;
  } catch (e) {
    log("No se pudo inyectar content script:", e);
    return false;
  }
}



async function handleNativeMessage(msg) {
  if (!msg || msg.action !== "youtube_control") {
    log("Mensaje ignorado (no youtube_control):", msg);
    return;
  }

  if (msg.command === "open_video") {
    const q = encodeURIComponent(msg.query || "");
    const url = `https://www.youtube.com/results?search_query=${q}`;
    log("Abriendo búsqueda:", url);
    await chrome.tabs.create({ url });
    return;
  }

  const tab = await findYouTubeTab();
  if (!tab || !tab.id) {
    log("No encontré pestaña YouTube / activa");
    return;
  }

  log("Enviando a content script en tab:", tab.id, "cmd:", msg.command);

const payload = {
  type: "YT_CMD",
  command: msg.command,
  value: msg.value
};

let { resp, err } = await sendToYouTube(tab.id, payload);

if (err) {
  log("sendMessage falló, intentando inyectar content script. Error:", err);

  const injected = await ensureContentScript(tab.id);
  if (!injected) return;

  ({ resp, err } = await sendToYouTube(tab.id, payload));
}

if (err) {
  log("sendMessage lastError (tras reintento):", err);
} else {
  log("Respuesta content script:", resp);
}

}

log("Service worker iniciado");
connectNative();
