# J.A.R.V.I.S — Guía técnica, roadmap y plan incremental

> Objetivo: evolucionar JARVIS de asistente conversacional a **compañero digital persistente** con presencia audiovisual, interacción por voz, visión de pantallas, control de audio del sistema y automatizaciones con n8n.

## 1) Contexto actual del repo (resumen técnico)

### 1.1 Flujo principal
- `main.py` ejecuta el loop interactivo, llama a DeepSeek, parsea JSON, actualiza emociones y dispara acciones. Integra TTS de Azure con visemas y envía mensajes por WebSocket al avatar.【F:main.py†L1-L140】
- `core/memory.py` mantiene memoria corta (últimos 10 mensajes).【F:core/memory.py†L1-L16】
- `core/parser.py` valida JSON de la IA.【F:core/parser.py†L1-L9】

### 1.2 IA y prompts
- `ai/deepseek.py` es el cliente único actual del LLM principal.【F:ai/deepseek.py†L1-L19】
- `config.py` contiene claves y parámetros del modelo.【F:config.py†L1-L5】

### 1.3 Acciones y automatización local
- `actions/dispatcher.py` enruta acciones (open_app, youtube_control).【F:actions/dispatcher.py†L1-L19】
- `actions/open_app.py` abre apps con lista blanca local.【F:actions/open_app.py†L1-L20】
- `actions/youtube_ext.py` usa HTTP bridge local en `127.0.0.1:8766/command` para controlar YouTube vía extensión de Chrome.【F:actions/youtube_ext.py†L1-L32】

### 1.4 Avatar + WS
- `jarvis_avatar_web/server/ws_server.py` es el hub WS para emoción/estado/mensajes del avatar y puede iniciarse en background desde `main.py` para evitar pasos manuales.【F:jarvis_avatar_web/server/ws_server.py†L1-L145】

### 1.5 Bridge con Chrome
- `native_bridge/http_bridge.py` expone `/command` para enviar JSON a la extensión (Native Messaging) y puede iniciarse desde `main.py` en el mismo arranque del asistente.【F:native_bridge/http_bridge.py†L1-L80】
- `native_bridge/native_host.py` transmite payloads entre el bridge y el Chrome Extension.【F:native_bridge/native_host.py†L1-L130】

---

## 2) Arquitectura objetivo (módulos concretos)

### 2.1 Orquestador central (Dialogue Orchestrator)
**Responsabilidades**
- Recibir inputs: texto, voz, eventos del sistema.
- Enviar respuestas inmediatas (fast brain) y delegar razonamiento profundo (deep brain).
- Gobernar estado emocional global y sincronizar avatar/voz/texto.

**Integración con el repo actual**
- Se conecta al mismo flujo de `main.py` (o reemplaza el loop actual con una versión asíncrona).
- Usa `AvatarWSClient` para reacciones inmediatas (emotion, say).【F:main.py†L1-L133】

### 2.2 Sistema de “dos cerebros” (Fast + Deep)
- **Fast brain**: respuestas reactivas inmediatas, fillers, gestos.
- **Deep brain**: razonamiento, planeación, tareas multi-paso.

**Comunicación**
- Un bus interno (event queue) donde:
  - Fast brain publica un “ack/placeholder” inmediato.
  - Deep brain publica la respuesta final y/o acciones.

**Coherencia de personalidad**
- Ambos cerebros comparten un “persona descriptor” fijo para tono y estilo.

### 2.3 Memoria avanzada
- **Corto plazo**: conversación actual (mantener y extender `core/memory.py`).【F:core/memory.py†L1-L16】
- **Episódica**: eventos importantes (acciones, tareas finalizadas).
- **Emocional**: “cómo se sintió” cada evento.
- **Semántica**: hechos sobre el usuario (preferencias, contextos).
- **Operativa**: tareas pendientes y estados.

**Reglas**
- Guardar eventos de alto impacto (acciones reales, cambios de emoción relevantes).
- Olvidar microconversas triviales.
- Consultar memoria profunda solo cuando el deep brain detecte necesidad.

### 2.4 Sistema nervioso externo (n8n)
- JARVIS delega tareas a n8n vía webhooks.
- n8n ejecuta integraciones y devuelve resultados a JARVIS.

---

## 3) Requisitos nuevos del usuario (audio + visión + wake word + privacy)

### 3.1 Acceso al audio del sistema
**Objetivo**: JARVIS “escucha” audio del sistema (música, videollamadas, etc.).

**Propuesta técnica (PC local)**
- **Windows**: capturar audio del sistema con WASAPI loopback.
- Crear un módulo `audio_capture.py` que exponga:
  - `start_audio_stream()`
  - `pause_audio_stream()`
  - `resume_audio_stream()`
- Enviar frames a:
  - Transcriptor (STT local o API)
  - Detector de eventos (por ejemplo, identificar música o conversaciones)

### 3.2 Visión de pantallas (multi-monitor)
**Objetivo**: JARVIS ve ambas pantallas (captura de imagen periódica o bajo demanda).

**Propuesta técnica**
- Captura por monitor (por ejemplo `mss` o APIs del SO).
- Mantener buffers de imagen con timestamps.
- Endpoint local `/vision/snapshot?monitor=1|2` para JARVIS.
- Botón de “pausa visión” para desactivar capturas.

### 3.3 Voz del usuario (input hablado)
**Objetivo**: hablar con JARVIS usando micrófono.

**Propuesta**
- Pipeline: mic → VAD → STT → text → orquestador.
- VAD reduce latencia y evita transcripciones innecesarias.
- Opción de “mute mic” como interrupción de privacidad.

### 3.4 Wake word (frase activadora)
**Objetivo**: JARVIS se activa al escuchar una frase.

**Propuesta**
- Frase activadora definida: **“Oye JARVIS”** (pronunciado “yarbis”).
- Motor wake word local (ej. Porcupine u otro lightweight local).
- Solo despierta el pipeline de STT cuando detecta frase.

### 3.5 Botones “pausar visión” y “pausar audio”
**Objetivo**: control total del usuario sobre privacidad.

**Implementación**
- Estado global `vision_enabled` y `audio_enabled`.
- UI (web o Tauri) con botones de toggle (Tauri ya llama al control server local).
- Orquestador verifica estos estados antes de capturar o procesar audio/vision.

### 3.6 TTS local y gratuito
**Objetivo**: usar TTS gratuito sin depender de servicios pagos.

**Propuesta**
- Motor TTS local (ej. Piper u otro motor offline).

---

## 4) Experiencia humana y presencia realista

### 4.1 Latencia percibida
- Objetivo: respuesta inicial <300–500ms.
- Estrategia:
  - Respuesta inmediata (fast brain) con filler.
  - Deep brain procesa en background.

### 4.2 Emociones como sistema
- Estado emocional persistente con decay.
- Emoción afecta:
  - Texto (tono)
  - Voz (ritmo, énfasis)
  - Avatar (expresiones)

### 4.3 Sincronización avatar-voz
- Emoción se envía al WS antes del audio.
- TTS genera visemas, avatar sincroniza labios.

---

## 5) Integración con n8n (acciones reales, no solo demo)

### 5.1 Ejemplos concretos
- “Activa modo focus”: cerrar apps distractoras, activar playlist, abrir IDE.
- “Resumen diario”: recoger tareas y enviar recordatorios.
- “Rutinas de salud”: water reminders + pausas.
- “Reacción emocional”: si detecta frustración → baja tono, sugiere descanso.
- “Memoria persistente”: n8n guarda eventos importantes en DB externa.

### 5.2 Flujo sugerido
- JARVIS → n8n (webhook) → acción → callback a JARVIS.

---

## 6) Roadmap de evolución

### Fase 1 — Fundaciones
1. Refactorizar loop principal para soportar entradas simultáneas (texto + voz + eventos).
2. Introducir estados globales: `audio_enabled`, `vision_enabled`.
3. Crear módulo de audio capture (sistema y micrófono).
4. Crear módulo de vision capture (pantallas).

### Fase 2 — Fast/Deep brain
1. Implementar “fast brain” inmediato con prompt mínimo.
2. Implementar “deep brain” con razonamiento largo.
3. Bus interno de eventos para coordinar respuestas.

### Fase 3 — Memoria avanzada
1. Guardado episódico + emocional.
2. Consultas semánticas en segundo plano.
3. Persistencia externa (DB local o n8n).

### Fase 4 — Presencia realista
1. Micro-expresiones y gestos automáticos.
2. Streaming de respuestas (partial speech).
3. Señales visuales de “pensando”.

---

## 7) Plan incremental con tareas concretas (accionable)

### Iteración 1: Audio y controles de privacidad
- [ ] Crear `core/audio_capture.py` con WASAPI loopback.
- [ ] Crear `core/mic_input.py` con VAD + STT.
- [ ] Añadir estados `audio_enabled` y `mic_enabled`.
- [ ] Exponer toggles en UI (web/tauri).

### Iteración 2: Visión multi-monitor
- [ ] Crear `core/vision_capture.py` con snapshots por monitor.
- [ ] Botón UI “Pause Vision”.
- [ ] Endpoint local para snapshots.

### Iteración 3: Wake word
- [ ] Integrar motor wake word.
- [ ] Activar pipeline STT solo tras wake word.

### Iteración 4: Dual-brain
- [ ] Crear `brain_fast.py` + `brain_deep.py`.
- [ ] Event bus para outputs.
- [ ] Fast brain responde en <300ms.

### Iteración 5: Memoria avanzada
- [ ] Agregar DB local o sqlite.
- [ ] Persistir memoria episódica + semántica.
- [ ] Resumen diario con n8n.

---

## 8) Qué puedo implementar ahora mismo vs. qué requiere tu intervención

### Lo que puedo hacer por mi cuenta (sin tocar hardware ni credenciales)
- Implementar el armazón de módulos:
  - `core/audio_capture.py` (loopback de sistema con pausa/reanudar).
  - `core/mic_input.py` (VAD + STT, con mute explícito).
  - `core/vision_capture.py` (captura por monitor con toggle).
- Crear endpoints locales (ej. `/vision/snapshot`, `/audio/toggle`, `/mic/toggle`) para controlar estados.
- Añadir el estado global y flujos de “pausa audio” y “pausa visión”.
- Integrar un bus interno para eventos (fast/deep brain) sin cambiar tu UX principal.

### Lo que sí requiere tu intervención (por permisos o decisiones personales)
- **Elegir tecnología de STT y wake word** (por privacidad/latencia):
  - Local (recomendado para privacidad): Vosk/Whisper local + Porcupine.
  - Cloud (más simple): APIs externas (necesitan claves).
- **Permisos de audio y pantalla del SO** (Windows):
  - Habilitar WASAPI loopback y permitir captura en segundo plano.
  - Elegir si quieres capturar siempre o solo bajo demanda.
- **Decidir política de privacidad**:
  - ¿Guardar transcripciones? ¿Borrar automáticamente? ¿Ventana de retención?
- **Definir frase de activación** (wake word).
- **Confirmar apps sensibles** que jamás deben ser automatizadas.

---

## 9) Plan fase a fase (para probar evolución)

### Fase 1 (ya puedo empezar): Infraestructura de audio/visión + toggles
Objetivo: JARVIS ve/escucha **pero con switches de privacidad**.
- Implementar módulos de captura con “pause/resume”.
- Estados globales: `audio_enabled`, `vision_enabled`, `mic_enabled`.
- Endpoints locales para toggles.

**Tu intervención**: seleccionar STT y wake word.

### Fase 2: Wake word + STT en tiempo real
Objetivo: activar pipeline de voz solo tras la frase de activación.
- Integrar motor wake word.
- Activar VAD + STT solo cuando hay wake word.

**Tu intervención**: definir frase de activación y política de privacidad.

### Fase 3: Dual-brain + memoria
Objetivo: respuestas inmediatas + razonamiento profundo con continuidad.
- Implementar fast/deep brain con bus interno.
- Persistir memoria episódica y semántica.

**Tu intervención**: decidir qué datos guardar y por cuánto tiempo.

---

## 10) Riesgos y mitigaciones

- **Latencia perceptible** → usar fillers + reacciones instantáneas.
- **Privacidad** → toggles claros, por defecto “OFF”.
- **Complejidad** → construir módulos aislados e integrarlos gradualmente.

---

## 11) Qué no hacer todavía
- No habilitar grabación continua sin necesidad (privacidad).
- No automatizar acciones destructivas sin confirmación.

---

## 12) Conclusión

Con estas fases, JARVIS evoluciona de un bot conversacional a un asistente con presencia real, con visión y audio del entorno, controlable y seguro. El plan mantiene coherencia con el repo actual, expandiéndolo de forma incremental sin romper su flujo base.
