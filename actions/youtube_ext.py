import requests

BRIDGE_URL = "http://127.0.0.1:8766/command"

def youtube_control(data: dict) -> str:
    """
    Envía comandos de control de YouTube al bridge local,
    que a su vez se comunica con la extensión de Chrome.
    """

    command = data.get("command")
    if not command:
        raise ValueError("youtube_control requiere data.command")

    payload = {
        "action": "youtube_control",
        "command": command,
        "query": data.get("query", ""),
        "value": data.get("value", None)
    }

    try:
        response = requests.post(
            BRIDGE_URL,
            json=payload,
            timeout=3
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error comunicándose con el bridge: {e}")

    return f"YouTube: comando '{command}' enviado correctamente"
