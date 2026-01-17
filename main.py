from ai.deepseek import ask_deepseek
import os
import queue
import re
import threading
import time
from core.memory import add_message, get_conversation
from core.parser import parse_response
from actions.dispatcher import dispatch_action

from jarvis_avatar_web.server.avatar_ws_client import AvatarWSClient
from jarvis_avatar_web.server import mouse_stream_auto
from jarvis_avatar_web.server import ws_server as avatar_ws_server
from native_bridge import http_bridge
from core.control_server import ControlServer
from core.state import state
from core.stt_azure import AzureSpeechListener

# ===============================
# Azure Speech (DEV LOCAL)
# ===============================
AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "")
AZURE_KEY = AZURE_SPEECH_KEY
AZURE_REGION = AZURE_SPEECH_REGION
AZURE_VOICE = "es-MX-DaliaNeural"

SYSTEM_PROMPT = """
Eres JARVIS, un asistente virtual que controla una computadora con Windows.

IMPORTANTE:
- NO puedes usar teclado ni mouse.
- NO puedes simular teclas.
- NO puedes escribir letras para controlar aplicaciones.
- TODA acción debe hacerse usando las acciones disponibles.

RESPONDE SIEMPRE en JSON válido, sin texto adicional.

Formato obligatorio:
{
  "speech": "Texto breve que dirás al usuario",
  "emotion": "neutral | happy | sad | relaxed | surprised | angry | sarcastic | thinking | confident | tired | smug | annoyed | scared",
  "action": {
    "type": "none | open_app | open_url | youtube_control | play_spotify",
    "data": {}
  }
}

=== ACCIONES DISPONIBLES ===

1) open_app
data: { "app_name": "nombre de la aplicación" }

2) open_url
data: { "url": "https://..." }

3) youtube_control
data:
{
  "command": "open_video | play | pause | toggle | volume_up | volume_down | set_volume | seek_forward | seek_backward | next | prev",
  "query": "texto SOLO para open_video",
  "value": "número entre 0 y 1 SOLO para set_volume"
}

4) play_spotify
Usar SOLO para música.

=== REGLAS ===
- Si el usuario menciona video, youtube, reproducción, pausa, volumen → youtube_control
- NUNCA simules teclado
- Si no hay acción clara → type = "none"
- No inventes acciones que no existan
- No agregues campos extra
- Sé conciso y natural en speech
"""

SUPPORTED_EMOTIONS = {
    "neutral", "happy", "sad", "relaxed", "angry", "surprised",
    "sarcastic", "thinking", "confident", "tired", "smug", "annoyed", "scared",
}

def normalize_emotion(e: str) -> str:
    if not isinstance(e, str):
        return "neutral"
    e = e.strip().lower()
    if e not in SUPPORTED_EMOTIONS:
        return "neutral"
    return e

def have_azure_config() -> bool:
    return bool((AZURE_KEY or "").strip()) and bool((AZURE_REGION or "").strip())

def prepare_tts_text(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return text
    text = re.sub(r"\bjarvis\b", "Yarvis", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwow\b", "woooow", text, flags=re.IGNORECASE)
    return text

def start_local_servers():
    stop_handles = {}

    try:
        stop_handles["avatar_ws"] = avatar_ws_server.start_server_in_thread(with_console=False)
        print("✔ Avatar WS server iniciado desde main.py")
    except Exception as exc:
        print(f"⚠️ No se pudo iniciar Avatar WS server: {exc}")

    try:
        stop_handles["http_bridge"] = http_bridge.HttpBridgeServer()
        stop_handles["http_bridge"].start()
        print("✔ HTTP bridge iniciado desde main.py")
    except Exception as exc:
        stop_handles.pop("http_bridge", None)
        print(f"⚠️ No se pudo iniciar HTTP bridge: {exc}")

    try:
        stop_handles["mouse_stream"] = mouse_stream_auto.start_mouse_stream_in_thread(verbose=False)
        print("✔ Mouse listener iniciado desde main.py")
    except Exception as exc:
        print(f"⚠️ No se pudo iniciar mouse listener: {exc}")

    return stop_handles


def normalize_text(text: str) -> str:
    return (text or "").strip()


def handle_user_text(user_text: str):
    user_text = normalize_text(user_text)
    if not user_text:
        return

    add_message("user", user_text)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(get_conversation())

    try:
        raw_response = ask_deepseek(messages)
    except Exception as e:
        print("⚠️ Error comunicándose con la IA:", e)
        return

    try:
        data = parse_response(raw_response)
    except ValueError as e:
        print("⚠️ Error parseando JSON:", e)
        return

    emo = normalize_emotion(data.get("emotion", "neutral"))
    speech = (data.get("speech", "") or "").strip()
    tts_text = prepare_tts_text(speech)

    add_message("assistant", speech)
    print(f"Jarvis ({emo}): {speech}")

    # 1) mood persistente
    avatar.send_emotion(emo)

    # 2) TTS (Azure) -> WS type:"tts"
    #    Import LAZY para que NO truene el programa si falta el SDK / estás en otro Python.
    if tts_text and have_azure_config():
        try:
            from core.azure_tts import synthesize_tts_with_visemes

            audio_b64, visemes = synthesize_tts_with_visemes(
                tts_text,
                key=AZURE_KEY,
                region=AZURE_REGION,
                voice=AZURE_VOICE
            )

            if not audio_b64:
                raise RuntimeError("Azure devolvió audio vacío (audio_b64='').")

            print(f"[AZURE] OK audio_b64_len={len(audio_b64)} visemes={len(visemes)}")

            # Requiere que AvatarWSClient tenga send_raw()
            if not hasattr(avatar, "send_raw"):
                raise RuntimeError("AvatarWSClient no tiene send_raw(). Agrega send_raw() en avatar_ws_client.py")

            avatar.send_raw({
                "type": "tts",
                "emotion": emo,
                "audio_b64": audio_b64,
                "visemes": visemes
            })
            print("[WS OUT] tts queued, bytes=", len(audio_b64))
            print("[WS STATUS]", avatar.status())

        except Exception as e:
            print("[AZURE] FAIL -> fallback say:", repr(e))
            avatar.send_say(speech, emo)
    else:
        # Sin texto o sin config Azure
        if not tts_text:
            print("[TTS] speech vacío -> no mando TTS.")
        elif not have_azure_config():
            print("[TTS] falta AZURE_KEY/AZURE_REGION -> fallback say.")
        avatar.send_say(speech, emo)

    # 3) acción windows
    try:
        result = dispatch_action(data["action"])
        print("✔", result)
    except Exception as e:
        print("⚠️ Error ejecutando acción:", e)

def stop_local_servers(stop_handles):
    bridge = stop_handles.get("http_bridge")
    if bridge:
        bridge.stop()

    stop_event = stop_handles.get("avatar_ws")
    if stop_event:
        stop_event.set()

    mouse_stop = stop_handles.get("mouse_stream")
    if mouse_stop:
        mouse_stop.set()

server_handles = start_local_servers()

avatar = AvatarWSClient("ws://127.0.0.1:8765")
avatar.start()
control_server = ControlServer(state)
control_server.start()
whisper_listener = AzureSpeechListener(
    state,
    key=AZURE_SPEECH_KEY,
    region=AZURE_SPEECH_REGION,
)

print("Jarvis iniciado. Escribe 'salir' para terminar.")

try:
    input_queue: "queue.Queue[str]" = queue.Queue()
    stop_event = threading.Event()

    def stdin_worker():
        while not stop_event.is_set():
            try:
                user_input = input("Tú: ").strip()
            except EOFError:
                break
            if user_input:
                input_queue.put(user_input)

    threading.Thread(target=stdin_worker, daemon=True).start()

    wake_word = "oye jarvis"
    armed_until = {"value": 0.0}

    def play_wake_beep():
        try:
            import winsound

            winsound.Beep(880, 1000)
        except Exception:
            return

    def on_transcript(text: str):
        cleaned = normalize_text(text).lower()
        if not cleaned:
            return
        now = time.time()
        if wake_word in cleaned:
            remainder = cleaned.replace(wake_word, "").strip(" ,.")
            armed_until["value"] = now + 6.0
            state.set_wake_active(True)
            play_wake_beep()
            threading.Timer(1.2, lambda: state.set_wake_active(False)).start()
            if remainder:
                input_queue.put(remainder)
                state.set_wake_active(False)
            return
        if now <= armed_until["value"]:
            input_queue.put(cleaned)
            armed_until["value"] = 0.0
            state.set_wake_active(False)

    whisper_listener.start(on_transcript)

    while True:
        try:
            user_input = input_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        if user_input.lower() == "salir":
            break
        handle_user_text(user_input)

finally:
    whisper_listener.stop()
    avatar.stop()
    control_server.stop()
    stop_local_servers(server_handles)
