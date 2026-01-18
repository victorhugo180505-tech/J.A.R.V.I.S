# 🧠 J.A.R.V.I.S — Roadmap de Evolución

> Objetivo final: un **Super Jarvis** que pueda:
> - conversar por voz tipo llamada (PC + móvil),
> - controlar un avatar 3D con lenguaje corporal y cámara “cinematográfica”,
> - ayudar con estudios, proyectos, código, productividad, calendario y documentos,
> - recordar de forma ética lo importante (personas, metas, hábitos),
> - actuar como “conciencia auxiliar”: acompañar, no molestar.

Cada versión está pensada para ser **una iteración razonable de 1 día** (aunque algunas puedan requerir 2 según la complejidad real).

---

## ⚙️ Arquitectura de Alto Nivel

Componentes principales:

- **Wake Word & Launcher (Windows / local)**
  - `core/wake_word.py` con openwakeword + sounddevice.
  - `tools/wake_jarvis.py` lanza `main.py` y `npm run tauri dev` si no están activos.
  - Usa `GET /health` y `POST /mic/toggle` en el control server.

- **Core Backend (Python)**
  - `main.py` orquesta LLM → JSON → emoción/acción.
  - Control server HTTP en `127.0.0.1:8780`:
    - `/health`, `/state`, `/audio|mic|vision/toggle`, `/vision/snapshot`.
  - STT:
    - Azure (default) con `core/stt_azure.py`.
    - Whisper local opcional con `core/stt_whisper.py`.
  - TTS Azure con visemas (`core/azure_tts.py`).
  - Memoria corta (`core/memory.py`).

- **Avatar UI (Web/Tauri)**
  - WS server en `jarvis_avatar_web/server/ws_server.py` (puerto 8765).
  - Cliente WS desde backend (`AvatarWSClient`).
  - Front web VRM en `jarvis_avatar_web/web/`.
  - Tauri en `jarvis_avatar_tauri/` (modo dev).

- **Automations / Integraciones**
  - Acciones locales: `open_app`, `youtube_control`.
  - Bridge con Chrome Extension: `native_bridge/http_bridge.py` → `127.0.0.1:8766/command`.
  - n8n planeado para Calendar, Docs, Sheets, notificaciones.

- **Multidispositivo (futuro)**
  - Cliente web/PWA para Android (texto + voz).
  - LiveKit/WebRTC para “modo llamada”.

- **Capa humana / de comportamiento (futuro)**
  - análisis de patrones (hábitos, procrastinación, horarios)
  - check-ins semanales
  - guardian social suave (recordar fechas/personas importantes sin invadir)
  - modos de operación (assist, semi-auto, observer)

---

## 🌱 Versión 0.1 — “Hermes Vigil”
**Objetivo:** Dejar sólido el wake word + launcher (lo existente, pero documentado y pulido).

Tareas:
- Documentar `WakeWordListener` (`core/wake_word.py`) y parámetros clave (threshold/cooldown).
- Documentar `tools/wake_jarvis.py`:
  - healthcheck `/health`
  - arranque de backend
  - arranque de Tauri (dev)
- Asegurar que:
  - si backend/Tauri no están corriendo → se levantan;
  - si ya corren → se hace `POST /mic/toggle`.
- Añadir sección de dependencias (openwakeword, sounddevice, requests, psutil).

---

## 🧩 Versión 0.2 — “Atenea Signal”
**Objetivo:** Formalizar la **máquina de estados de conversación**.

Tareas:
- Crear `core/conversation_state.py` con estados:
  - `IDLE`, `LISTENING`, `THINKING`, `SPEAKING`.
- Integrar estos estados en:
  - STT (cuando empieza/termina de escuchar).
  - LLM (cuando se envía/recibe respuesta).
  - TTS (cuando empieza/termina de hablar).
- Exponer estado actual vía:
  - WebSocket (mensaje `{type:"state", state:"SPEAKING"}`).
  - Endpoint `/status` (opcional).

---

## 💬 Versión 0.3 — “Iris Flow”
**Objetivo:** Manejo robusto de frases largas + normalización “Jarvis / Yarvis”.

Tareas:
- Ajustar el pipeline de STT:
  - ventana de escucha por frase (min/max duración).
  - finalización por silencio con timeout claro.
- Crear función `normalize_wake_name()`:
  - `normalize_wake_name("yarvis") -> "jarvis"`.
  - Usar en Azure y Whisper antes de activar comandos.

---

## 🧍 Versión 0.4 — “Hefesto Pulse”
**Objetivo:** Movimiento corporal procedural básico (sin manos todavía).

Tareas:
- Crear `AvatarMovementController` en el front (web/Tauri):
  - referencias a huesos VRM (`hips`, `spine`, `chest`, `neck`, `head`).
  - sway suave y micro-movimientos de cabeza.
- Ajustar comportamiento según `ConversationState`:
  - `IDLE`: sway suave, postura neutra.
  - `LISTENING`: inclinación ligera hacia adelante.
  - `THINKING`: cabeza ladeada.
  - `SPEAKING`: postura más erguida.

---

## 🎥 Versión 0.5 — “Artemisa Gaze”
**Objetivo:** Sistema de cámara con planos y transiciones suaves.

Tareas:
- Crear `CameraController` en el front:
  - modos: `DEFAULT`, `SLIGHT_IN`, `CLOSE_UP`, `ZOOM_OUT`.
  - cada modo = posición + lookAt + FOV.
  - interpolación suave entre modos.
- Mapear estado → modo de cámara:
  - `IDLE` → `DEFAULT`
  - `LISTENING` → `SLIGHT_IN`
  - `SPEAKING` → `CLOSE_UP`
  - `THINKING` → `ZOOM_OUT`

---

## 🎭 Versión 0.6 — “Afrodita Bridge”
**Objetivo:** Unificar emociones desde el backend hasta el avatar.

Tareas:
- Definir set de emociones estándar:
  - `neutral`, `happy`, `curious`, `sad`, `annoyed` (+ intensidad 0–1).
- Backend:
  - decide emoción por respuesta LLM + contexto.
  - envía `emotion` por WebSocket.
- Front:
  - mapea emoción → blendshapes + postura.
  - combina con `AvatarMovementController`.

---

## 🧠 Versión 0.7 — “Prometeo Dock”
**Objetivo:** Arquitectura limpia para el “cerebro” (LLM) con proveedor pluggable.

Tareas:
- Crear interfaz `LLMProvider`:
  - métodos tipo `generate(messages, tools, ...)`.
- Implementar:
  - `DeepSeekProvider`
  - `OpenAIProvider` (backup).
- Config vía `.env.local` para elegir proveedor.
- Encapsular llamadas LLM en módulo único.

---

## 🧾 Versión 0.8 — “Mnemosine Seed”
**Objetivo:** Memoria básica + base de datos de personas importantes (PeopleDB).

Tareas:
- Crear `MemoryStore`:
  - resúmenes de conversaciones.
  - hechos sobre el usuario (hábitos, preferencias).
- Crear `PeopleDB`:
  - nombre, relación, gustos, notas (sin datos ultra sensibles).
  - API: `add_person`, `update_person`, `get_person`, `list_people`.
- Conectar LLM:
  - herramientas para consultar memoria.

---

## ✅ Versión 0.9 — “Nike Weave”
**Objetivo:** Sistema de tareas y metas personales controlado por Jarvis.

Tareas:
- Implementar estructura local (DB/JSON) para:
  - tareas
  - proyectos
  - metas.
- Endpoints/API internos:
  - `create_task`, `list_tasks`, `update_task`, `complete_task`.
- Jarvis:
  - crea tareas por voz.
  - lista/prioriza.
  - marca completadas.

---

## 📆 Versión 1.0 — “Chronos Link”
**Objetivo:** Integración básica con Google Calendar vía n8n (o API directa).

Tareas:
- Configurar flujo en n8n:
  - crear eventos en Google Calendar.
  - listar próximos eventos.
- Backend:
  - `schedule_event(...)`
  - `get_upcoming_events(...)`
  - comunicación vía HTTP con n8n.
- Jarvis:
  - agendar eventos por voz.
  - leer próximos eventos.

---

## 📚 Versión 1.1 — “Calíope Scribe”
**Objetivo:** Jarvis capaz de generar y editar documentos (Docs/Sheets básicos).

Tareas:
- Flujos en n8n o módulos backend para:
  - crear Google Docs / Sheets.
  - rellenar contenido (resúmenes, tablas simples).
- Jarvis:
  - crea documentos por voz.
  - actualiza hojas básicas.

---

## 📱 Versión 1.2 — “Jano Echo”
**Objetivo:** Jarvis usable desde el teléfono sin app nativa (PWA/cliente web).

Tareas:
- UI web ligera:
  - chat + botón de micrófono.
  - audio out (streaming o chunks).
- Responsive para Android.
- Backend expuesto con túnel (ngrok/Cloudflare).
- Soporte:
  - mensajes de voz (STT).
  - respuestas habladas (TTS).

---

## 🎧 Versión 1.3 — “Orfeo Room”
**Objetivo:** Modo llamada con LiveKit/WebRTC.

Tareas:
- Configurar LiveKit (self-hosted o cloud).
- Bot que:
  - recibe audio del usuario.
  - envía audio de Jarvis (TTS).
- Integración backend:
  - STT conectado a entrada LiveKit.
  - TTS conectado a salida de la room.
- UI web/Tauri:
  - unirse a la room.
  - barge-in (si hablas → Jarvis se pausa).

---

## 🧘 Versión 1.4 — “Hestia Check-in”
**Objetivo:** Jarvis como espejo mental suave (check-ins e insights).

Tareas:
- Servicio interno de análisis de patrones:
  - tareas pospuestas
  - horarios aproximados de uso
  - sesiones de trabajo.
- Insights semanales (sin juzgar).
- Check-in semanal con opción:
  - “No volver a hablar de esto”.
  - “Recordármelo suave”.

---

## 🧑‍🤝‍🧑 Versión 1.5 — “Hera Guardian”
**Objetivo:** Guardian social suave basado en PeopleDB.

Tareas:
- Usar `PeopleDB` para:
  - recordar fechas importantes (cumpleaños light).
  - recordar gustos/temas clave.
- Jarvis:
  - sugiere gestos bonitos con permiso.
  - evita temas delicados sin aprobación.
- Configuración:
  - nivel de “intimidad social” (slider).

---

## 🛡️ Versión 1.6 — “Aegis Mode”
**Objetivo:** Modos de operación + seguridad y control.

Tareas:
- Modos:
  - `assist` (todo se confirma).
  - `semi-auto` (ciertas cosas se ejecutan solas).
  - `observer` (solo observa y comenta).
- Whitelist de acciones peligrosas:
  - borrar archivos
  - mandar correos importantes
  - cambios grandes en calendario.
- Logging:
  - registrar qué ejecutó, cuándo y por qué.
- Panel simple (Tauri/web):
  - ver comandos ejecutados.
  - ajustar modo de operación.

---

## 🎬 Versión 1.7 — “Apolo Presence”
**Objetivo:** Presencia más “humana”: gestos, movimientos contextuales, refinamiento.

Tareas:
- Extender `AvatarMovementController`:
  - gestos leves de hombros/brazos.
  - posturas especiales (explicar, escuchar serio).
- Micro-reacciones:
  - error → cambio corporal + expresión.
  - éxito → gesto sutil de satisfacción.
- Cámara:
  - transiciones más suaves.
  - planos especiales para explicaciones largas.

---

## 📦 Versión 2.0 — “Olympus Prime”
**Objetivo:** Integrar todas las piezas anteriores en una experiencia coherente.

En este punto, J.A.R.V.I.S debería:

- Estar siempre disponible localmente (wake word + launcher).
- Escuchar, pensar y responder con voz y avatar 3D con lenguaje corporal.
- Funcionar en PC + móvil (PWA y/o LiveKit).
- Ayudarte con:
  - tareas, proyectos y metas
  - calendario
  - documentos y hojas de cálculo
  - decisiones e ideas importantes.
- Recordar (de forma ética) lo importante sobre ti y tus personas clave.
- Ofrecer check-ins e insights sin ser invasivo.
- Tener modos de seguridad que den confianza total.

---

Fin del contenido para **docs/ROADMAP.md**.
