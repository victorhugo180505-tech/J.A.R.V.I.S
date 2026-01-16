from actions.open_app import open_app
from actions.youtube_ext import youtube_control

def dispatch_action(action):
    action_type = action.get("type")
    data = action.get("data", {})

    if action_type == "none":
        return "Sin acción."

    if action_type == "open_app":
        app_name = data.get("app_name")
        if not app_name:
          raise ValueError("open_app requiere data.app_name")
        open_app(app_name)
        return f"App '{app_name}' abierta."
    elif action_type == "youtube_control":
        return youtube_control(action["data"])
    raise ValueError(f"Acción desconocida: {action_type}")
