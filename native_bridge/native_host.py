import json
import socket
import struct
import sys
import threading
import time

LOCK_PORT = 8768          # impedir múltiples instancias
BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 8767        # (para futuro http_bridge)

PING_TIMEOUT_SEC = 6      # si no hay ping en 6s, cerramos

def send_native_message(obj: dict) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()

def acquire_single_instance_lock() -> socket.socket:
    lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lock.bind(("127.0.0.1", LOCK_PORT))
    lock.listen(1)
    return lock

def read_exact(n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sys.stdin.buffer.read(n - len(buf))
        if not chunk:
            return b""  # EOF
        buf += chunk
    return buf

def read_native_message() -> dict | None:
    """
    Lee un mensaje Native Messaging:
    4 bytes little-endian length + JSON bytes.
    Devuelve None si EOF (Chrome cerrado).
    """
    raw_len = read_exact(4)
    if not raw_len:
        return None
    msg_len = struct.unpack("<I", raw_len)[0]
    raw = read_exact(msg_len)
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return {}

def try_connect_bridge() -> socket.socket | None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect((BRIDGE_HOST, BRIDGE_PORT))
        s.settimeout(None)
        return s
    except Exception:
        return None

def watchdog(stop_event: threading.Event, last_ping_ref: list[float]) -> None:
    while not stop_event.is_set():
        time.sleep(1)
        if time.time() - last_ping_ref[0] > PING_TIMEOUT_SEC:
            stop_event.set()
            break

def chrome_reader(stop_event: threading.Event, last_ping_ref: list[float]) -> None:
    """
    Lee mensajes desde Chrome.
    Si llega EOF -> stop_event.
    Si llega ping -> actualiza last_ping_ref.
    """
    try:
        while not stop_event.is_set():
            msg = read_native_message()
            if msg is None:
                break  # EOF -> Chrome cerrado/desconectado
            if msg.get("action") == "ping":
                last_ping_ref[0] = time.time()
    finally:
        stop_event.set()

def main() -> None:
    # 1) Evitar duplicados
    try:
        lock_sock = acquire_single_instance_lock()
    except OSError:
        sys.exit(0)

    stop_event = threading.Event()
    last_ping_ref = [time.time()]

    # 2) Thread que lee stdin (y pings) correctamente
    t_reader = threading.Thread(target=chrome_reader, args=(stop_event, last_ping_ref), daemon=True)
    t_reader.start()

    # 3) Watchdog por ping (por si Chrome queda en background raro)
    t_watch = threading.Thread(target=watchdog, args=(stop_event, last_ping_ref), daemon=True)
    t_watch.start()

    # 4) Aviso a la extensión
    try:
        send_native_message({"action": "native_ready"})
    except Exception:
        sys.exit(0)

    bridge_sock = None

    try:
        while not stop_event.is_set():
            # (Opcional/futuro) Conectar al bridge y reenviar comandos a la extensión
            if bridge_sock is None:
                bridge_sock = try_connect_bridge()

            if bridge_sock is not None:
                try:
                    raw = bridge_sock.recv(65536)
                    if not raw:
                        bridge_sock.close()
                        bridge_sock = None
                    else:
                        payload = json.loads(raw.decode("utf-8", errors="replace"))
                        send_native_message(payload)
                except Exception:
                    try:
                        bridge_sock.close()
                    except Exception:
                        pass
                    bridge_sock = None

            time.sleep(0.05)
    finally:
        try:
            if bridge_sock is not None:
                bridge_sock.close()
        except Exception:
            pass
        try:
            lock_sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
