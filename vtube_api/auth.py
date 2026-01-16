import json
import uuid
import websocket

VTS_WS = "ws://127.0.0.1:8001"

PLUGIN_NAME = "Jarvis"
PLUGIN_DEVELOPER = "Victor"

def send(ws, msg: dict) -> dict:
    ws.send(json.dumps(msg))
    raw = ws.recv()
    return json.loads(raw)

def main():
    ws = websocket.WebSocket()
    ws.connect(VTS_WS)

    req_id = str(uuid.uuid4())
    msg = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": req_id,
        "messageType": "AuthenticationTokenRequest",
        "data": {
            "pluginName": PLUGIN_NAME,
            "pluginDeveloper": PLUGIN_DEVELOPER
        }
    }

    resp = send(ws, msg)
    print(json.dumps(resp, indent=2, ensure_ascii=False))

    ws.close()

if __name__ == "__main__":
    main()
