import asyncio, json, time
import pyautogui
import websockets

WS_URL = "ws://127.0.0.1:8765"

async def run_once():
    async with websockets.connect(WS_URL) as ws:
        while True:
            x, y = pyautogui.position()
            await ws.send(json.dumps({"type":"mouse","x":x,"y":y}))
            await asyncio.sleep(1/30)

async def main():
    while True:
        try:
            await run_once()
        except Exception as e:
            print("mouse_stream: WS caído, reintentando...", repr(e))
            await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(main())
import asyncio, json, pyautogui
from screeninfo import get_monitors
import websockets

WS_URL = "ws://127.0.0.1:8765"
FPS = 60
MONITOR_INDEX = 1   # 0 = principal, 1 = secundario (derecha)

monitors = get_monitors()
MON = monitors[MONITOR_INDEX]

async def main():
    async with websockets.connect(WS_URL) as ws:
        print(f"🖥️ Usando monitor {MONITOR_INDEX}: {MON.width}x{MON.height} at ({MON.x},{MON.y})")

        while True:
            x, y = pyautogui.position()

            # ¿el mouse está dentro del monitor del avatar?
            if MON.x <= x <= MON.x + MON.width and MON.y <= y <= MON.y + MON.height:
                # normalizar a -1..1
                nx = ((x - MON.x) / MON.width) * 2 - 1
                ny = -(((y - MON.y) / MON.height) * 2 - 1)

                await ws.send(json.dumps({
                    "type": "mouse",
                    "x": max(-1, min(1, nx)),
                    "y": max(-1, min(1, ny))
                }))

            await asyncio.sleep(1 / FPS)

asyncio.run(main())
