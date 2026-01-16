import asyncio
import json
import threading
import time

import pyautogui
from screeninfo import get_monitors
import websockets

WS_URL = "ws://127.0.0.1:8765"
FPS = 60
MONITOR_INDEX = 1   # 0 = principal, 1 = secundario (derecha)

def _get_monitor(index: int):
    monitors = get_monitors()
    if not monitors:
        raise RuntimeError("No se detectaron monitores.")
    if index < 0 or index >= len(monitors):
        raise RuntimeError(f"Monitor fuera de rango: {index}. Disponibles: {len(monitors)}")
    return monitors[index]

async def stream_mouse(stop_event: threading.Event, monitor_index: int = MONITOR_INDEX):
    monitor = _get_monitor(monitor_index)
    async with websockets.connect(WS_URL) as ws:
        print(f"🖥️ Mouse stream monitor {monitor_index}: {monitor.width}x{monitor.height} at ({monitor.x},{monitor.y})")

        while not stop_event.is_set():
            x, y = pyautogui.position()

            # ¿el mouse está dentro del monitor del avatar?
            if monitor.x <= x <= monitor.x + monitor.width and monitor.y <= y <= monitor.y + monitor.height:
                # normalizar a -1..1
                nx = ((x - monitor.x) / monitor.width) * 2 - 1
                ny = -(((y - monitor.y) / monitor.height) * 2 - 1)

                await ws.send(json.dumps({
                    "type": "mouse",
                    "x": max(-1, min(1, nx)),
                    "y": max(-1, min(1, ny))
                }))

            await asyncio.sleep(1 / FPS)

async def run_forever(stop_event: threading.Event, monitor_index: int = MONITOR_INDEX):
    while not stop_event.is_set():
        try:
            await stream_mouse(stop_event, monitor_index=monitor_index)
        except Exception as e:
            print("mouse_stream: WS caído, reintentando...", repr(e))
            await asyncio.sleep(1.0)

def start_mouse_stream_in_thread(monitor_index: int = MONITOR_INDEX):
    stop_event = threading.Event()

    def runner():
        asyncio.run(run_forever(stop_event, monitor_index=monitor_index))

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    return stop_event

if __name__ == "__main__":
    asyncio.run(run_forever(threading.Event(), monitor_index=MONITOR_INDEX))
