import time
from pathlib import Path
import subprocess
import sys
from typing import Optional

import psutil
import requests

from core.wake_word import WakeWordListener

REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PY_PATH = REPO_ROOT / "main.py"
TAURI_EXECUTABLE = Path("C:/path/to/jarvis.exe")
TAURI_PROCESS_NAME = "jarvis.exe"
BACKEND_HEALTH_URL = "http://127.0.0.1:8780/health"
MIC_TOGGLE_URL = "http://127.0.0.1:8780/mic/toggle"


def is_backend_running(timeout: float = 0.5) -> bool:
    try:
        response = requests.get(BACKEND_HEALTH_URL, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def launch_backend() -> Optional[subprocess.Popen]:
    if not MAIN_PY_PATH.exists():
        return None
    return subprocess.Popen(
        [sys.executable, str(MAIN_PY_PATH)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def is_tauri_running() -> bool:
    target = TAURI_PROCESS_NAME.lower()
    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info.get("name") or ""
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if name.lower() == target:
            return True
    return False


def launch_tauri() -> Optional[subprocess.Popen]:
    if not TAURI_EXECUTABLE.exists():
        return None
    return subprocess.Popen(
        [str(TAURI_EXECUTABLE)],
        cwd=str(TAURI_EXECUTABLE.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def toggle_mic(timeout: float = 0.5) -> None:
    try:
        requests.post(MIC_TOGGLE_URL, timeout=timeout)
    except requests.RequestException:
        return


def handle_wake_word() -> None:
    backend_running = is_backend_running()
    tauri_running = is_tauri_running()

    if not backend_running:
        launch_backend()

    if not tauri_running:
        launch_tauri()

    if backend_running and tauri_running:
        toggle_mic()


def main() -> None:
    listener = WakeWordListener(
        on_detected=handle_wake_word,
        wake_word="jarvis",
        threshold=0.55,
        cooldown_seconds=3.0,
    )
    listener.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()


if __name__ == "__main__":
    main()
