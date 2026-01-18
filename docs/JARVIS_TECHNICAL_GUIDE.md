# J.A.R.V.I.S — Guía técnica, arquitectura actualizada y roadmap

> Objetivo: evolucionar J.A.R.V.I.S de asistente conversacional a **compañero digital persistente** con presencia audiovisual, interacción por voz, visión de pantallas, control del sistema y automatizaciones (n8n), respetando privacidad y control del usuario.

## 1) Contexto actual del repo (resumen técnico)

### 1.1 Flujo principal (backend)
- `main.py` orquesta el loop principal: recibe texto, consulta al LLM (DeepSeek), parsea JSON, actualiza emociones y dispara acciones, además de enviar eventos al avatar vía WebSocket.【F:main.py†L1-L209】
- El backend inicia servicios locales:
  - WS del avatar (`jarvis_avatar_web/server/ws_server.py`).【F:main.py†L73-L97】
  - HTTP bridge para la extensión de Chrome (`native_bridge/http_bridge.py`).【F:main.py†L79-L90】
  - Mouse stream para el avatar (`jarvis_avatar_web/server/mouse_stream_auto.py`).【F:main.py†L92-L97】
- Controla STT con `AzureSpeechListener` y gating por wake word detectado en transcripción.【F:main.py†L201-L299】

### 1.2 IA, memoria y parsing
- `ai/deepseek.py` es el cliente LLM actual (DeepSeek).【F:ai/deepseek.py†L1-L19】
- `core/memory.py` mantiene memoria corta (últimos 10 mensajes).【F:core/memory.py†L1-L16】
- `core/parser.py` valida el JSON devuelto por el LLM.【F:core/parser.py†L1-L9】

### 1.3 Voz y estado
- `core/azure_tts.py` sintetiza TTS con visemas (Azure) para sincronizar labios con el avatar.【F:core/azure_tts.py†L1-L93】
- `core/stt_azure.py` escucha el micrófono y emite transcripciones (Azure).【F:core/stt_azure.py†L1-L75】
- `core/stt_whisper.py` ofrece alternativa local (Whisper) con VAD simple y segmentación por silencio.【F:core/stt_whisper.py†L1-L209】
- `core/state.py` mantiene toggles de audio/mic/visión y estado de wake word.【F:core/state.py†L1-L41】

### 1.4 Captura de audio/visión
- `core/audio_capture.py` define loopback del sistema (soundcard).【F:core/audio_capture.py†L1-L67】
- `core/mic_input.py` es una base para VAD/STT local con sounddevice.【F:core/mic_input.py†L1-L72】
- `core/vision_capture.py` captura pantallas con `mss` y respeta `vision_enabled`.【F:core/vision_capture.py†L1-L39】

### 1.5 Control server local (HTTP)
- `core/control_server.py` expone:
  - `/health` (salud), `/state` (snapshot).
  - toggles POST: `/audio/toggle`, `/mic/toggle`, `/vision/toggle`.
  - `/vision/snapshot?monitor=N` para imagen PNG del monitor.【F:core/control_server.py†L1-L94】

### 1.6 Wake word + launcher
- `core/wake_word.py` integra openwakeword con modelo `hey_jarvis_v0.1`.【F:core/wake_word.py†L1-L140】
- `tools/wake_jarvis.py` lanza `main.py` y Tauri en dev, valida `/health` y hace `POST /mic/toggle` al detectar wake word.【F:tools/wake_jarvis.py†L1-L150】

### 1.7 Acciones + bridge con Chrome
- `actions/dispatcher.py` rutea acciones (`open_app`, `youtube_control`).【F:actions/dispatcher.py†L1-L20】
- `actions/open_app.py` abre apps con whitelist local.【F:actions/open_app.py†L1-L20】
- `actions/youtube_ext.py` usa el HTTP bridge en `127.0.0.1:8766/command` para controlar YouTube.【F:actions/youtube_ext.py†L1-L32】
- `native_bridge/http_bridge.py` y `native_bridge/native_host.py` conectan con la extensión de Chrome.【F:native_bridge/http_bridge.py†L1-L80】【F:native_bridge/native_host.py†L1-L130】

### 1.8 Avatar y UI
- `jarvis_avatar_web/server/ws_server.py` es el WS hub que recibe `emotion`, `say` y `tts`.【F:jarvis_avatar_web/server/ws_server.py†L1-L145】
- `jarvis_avatar_web/web/` contiene el front web (Three.js + VRM).【F:jarvis_avatar_web/web/main.js†L1-L200】
- `jarvis_avatar_tauri/` existe para empaquetar UI de escritorio (dev mode desde `tools/wake_jarvis.py`).【F:tools/wake_jarvis.py†L18-L92】

---

## 2) Arquitectura actualizada (as-is)

### 2.1 Wake word & launcher
- Listener local (`core/wake_word.py`) + launcher (`tools/wake_jarvis.py`).
- Detecta wake word, asegura backend y Tauri, y activa mic con `/mic/toggle`.

### 2.2 Core Backend (Python)
- `main.py` = orquestador actual (LLM → JSON → emoción/acción).
- Control server: `core/control_server.py` en `127.0.0.1:8780`.
- Estado global en `core/state.py` (audio/mic/visión/wake).
- STT activo: Azure por defecto (`core/stt_azure.py`), Whisper opcional (`core/stt_whisper.py`).
- TTS Azure con visemas (`core/azure_tts.py`).
- Memoria corta (`core/memory.py`).

### 2.3 Avatar/UI
- WS backend en `jarvis_avatar_web/server/ws_server.py` (puerto 8765).
- Front Web VRM en `jarvis_avatar_web/web/`.
- Cliente WS en backend `AvatarWSClient` (envía `emotion`, `say`, `tts`).【F:jarvis_avatar_web/server/avatar_ws_client.py†L1-L120】
- Tauri en `jarvis_avatar_tauri/` (dev, no siempre activo).

### 2.4 Integraciones y acciones
- Acciones locales: `open_app`, `youtube_control`.
- Bridge con Chrome Extension vía `native_bridge/http_bridge.py`.
- n8n: **futuro** (no implementado aún en el repo).

### 2.5 Privacidad y control
- Toggles de audio/mic/visión via ControlServer.
- Capturas bloqueadas si `vision_enabled = False`.

---

## 3) Brechas vs objetivos (qué falta consolidar)

1. **Máquina de estados de conversación** (IDLE/LISTENING/THINKING/SPEAKING).
2. **Pipeline de STT robusto** para frases largas y normalización de “Jarvis/Yarvis”.
3. **Movimiento corporal y cámara** en el avatar (hoy es mayormente estático).
4. **Memoria persistente** (hoy es solo memoria corta in-memory).
5. **Integraciones reales** (n8n, Calendar, Docs, etc.).
6. **Multidispositivo** (PWA/LiveKit).

---

## 4) Roadmap con nombres “cool” (mitología/SCI-FI)

> Cada versión es una iteración de ~1 día (algunas pueden requerir 2).

### 0.1 — “Hermes Vigil” (Wake word + launcher)
- Documentar y pulir `core/wake_word.py` (openwakeword) y `tools/wake_jarvis.py`.
- Verificar healthcheck `GET /health` antes de lanzar Tauri.
- Consolidar `POST /mic/toggle` como entrada principal del modo escucha.
- Añadir nota de instalación de dependencias (`sounddevice`, `openwakeword`).

### 0.2 — “Atenea Signal” (State machine)
- Crear `core/conversation_state.py` con estados `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`.
- Integrar estado con:
  - STT (inicio/fin de escucha).
  - LLM (envío/recepción de respuesta).
  - TTS (inicio/fin de habla).
- Publicar estado vía WS (`type: "state"`) y opcional `/status`.

### 0.3 — “Iris Flow” (STT robusto)
- Mejorar `core/stt_whisper.py` para frases largas (ventana + timeout).
- Normalizar wake word con `normalize_wake_name()` y usarlo tanto en Azure como Whisper.
- Añadir pruebas locales para detectar “Jarvis/Yarvis” sin falsos positivos.

### 0.4 — “Hefesto Pulse” (Movimiento corporal)
- Implementar `AvatarMovementController` en `jarvis_avatar_web/web/main.js`.
- Mapear huesos VRM (hips, spine, chest, neck, head) para sway suave.
- Ajustar postura según estado (IDLE/LISTENING/THINKING/SPEAKING).

### 0.5 — “Artemisa Gaze” (Cámara)
- Crear `CameraController` en el front (web/Tauri).
- Modos: `DEFAULT`, `SLIGHT_IN`, `CLOSE_UP`, `ZOOM_OUT`.
- Transiciones suaves por interpolación en cada frame.

### 0.6 — “Afrodita Bridge” (Emoción end-to-end)
- Estándar de emociones `{name, intensity}`.
- Backend decide emoción por respuesta LLM + contexto.
- Front mapea emoción → blendshapes + postura.

### 0.7 — “Prometeo Dock” (LLM pluggable)
- Interfaz `LLMProvider` con `generate(messages, tools)`.
- Implementar `DeepSeekProvider` + fallback `OpenAIProvider`.
- Configuración por `.env.local`.

### 0.8 — “Mnemosine Seed” (Memoria)
- `MemoryStore` persistente + `PeopleDB`.
- API: `add_person`, `update_person`, `get_person`, `list_people`.
- LLM usa herramientas para consultar memoria.

### 0.9 — “Nike Weave” (Tareas y metas)
- Persistencia local para tareas/proyectos/metas.
- Endpoints: `create_task`, `list_tasks`, `update_task`, `complete_task`.
- Flujos de voz para crear y cerrar tareas.

### 1.0 — “Chronos Link” (Calendar)
- Integración con Google Calendar vía n8n.
- Endpoints: `schedule_event`, `get_upcoming_events`.
- UX de voz para agendar y consultar.

### 1.1 — “Calíope Scribe” (Docs/Sheets)
- Flujos en n8n para Docs/Sheets.
- Generar resúmenes y tablas simples desde voz.

### 1.2 — “Jano Echo” (PWA móvil)
- UI web ligera (chat + mic + audio output).
- Responsive para Android.
- Backend expuesto con túnel (ngrok/Cloudflare).

### 1.3 — “Orfeo Room” (Modo llamada)
- LiveKit/WebRTC para audio bidireccional.
- Bot Jarvis en la room + cliente móvil/PC.
- Barge-in: si usuario habla, Jarvis se pausa.

### 1.4 — “Hestia Check-in” (Salud mental suave)
- Análisis semanal de hábitos/uso.
- Check-ins con opción de opt-out.

### 1.5 — “Hera Guardian” (PeopleDB social)
- Recordatorios suaves de fechas/personas clave.
- Control de intensidad social (slider).

### 1.6 — “Aegis Mode” (Seguridad)
- Modos: `assist`, `semi-auto`, `observer`.
- Whitelist de acciones peligrosas.
- Panel para auditoría de comandos.

### 1.7 — “Apolo Presence” (Presencia avanzada)
- Gestos de hombros/brazos.
- Micro-reacciones a errores/éxitos.
- Cámara con planos especiales para explicaciones largas.

### 2.0 — “Olympus Prime” (Super Jarvis)
- Integración completa de voz, avatar, memoria y multi-dispositivo.
- Experiencia coherente con seguridad, privacidad y continuidad.

---

## 5) Qué puedo implementar ahora mismo vs. qué requiere tu intervención

### Lo que puedo hacer por mi cuenta
- Refactor modular del backend (state machine + WS state events).
- Mejoras en STT local (Whisper) y normalización de wake word.
- Mejoras en el front del avatar (movimiento + cámara).

### Lo que requiere tu intervención
- Elección definitiva de STT/TTS (local vs cloud).
- Credenciales para servicios externos (n8n, Calendar, Docs).
- Políticas de privacidad y retención de datos.
