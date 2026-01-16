import json
import uuid
import websocket
from vtube_api.config import VTS_WS, VTUBE_TOKEN, PLUGIN_NAME, PLUGIN_DEVELOPER

def vtube_speak(text: str):
    ws = websocket.WebSocket()
    ws.connect(VTS_WS)

    # Auth
    auth = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": str(uuid.uuid4()),
        "messageType": "AuthenticationRequest",
        "data": {
            "pluginName": PLUGIN_NAME,
            "pluginDeveloper": PLUGIN_DEVELOPER,
            "authenticationToken": VTUBE_TOKEN
        }
    }
    ws.send(json.dumps(auth))
    ws.recv()

    # Speak
    speak = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": str(uuid.uuid4()),
        "messageType": "SpeechRequest",
        "data": {
            "text": text
        }
    }
    ws.send(json.dumps(speak))
    ws.recv()

    ws.close()
