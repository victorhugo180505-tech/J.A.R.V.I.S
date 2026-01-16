import subprocess

# Lista blanca de apps permitidas
ALLOWED_APPS = {
    "notepad": "notepad",
    "calc": "calc",
    "calculator": "calc",
    "explorer": "explorer",
    "cmd": "cmd"
}

def open_app(app_name):
    app_name = app_name.lower()

    if app_name not in ALLOWED_APPS:
        raise ValueError(f"App no permitida: {app_name}")

    subprocess.Popen(ALLOWED_APPS[app_name], shell=True)