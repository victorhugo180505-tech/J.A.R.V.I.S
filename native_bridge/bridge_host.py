import json
import struct
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Si stdout no está conectado al pipe de Chrome, esto falla.
def try_send_native_message(obj) -> tuple[bool, str]:
    try:
        data = json.dumps(obj).encode("utf-8")
        sys.stdout.buffer.write(struct.pack("<I", len(data)))
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        return True, ""
    except BrokenPipeError:
        return False, "BrokenPipe: el host no está conectado a Chrome (connectNative no activo)"
    except Exception as e:
        return False, f"Error enviando a Chrome: {e}"

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/command":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")

        try:
            payload = json.loads(raw)
        except Exception:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":false,"error":"JSON invalido"}')
            return

        ok, err = try_send_native_message(payload)

        if ok:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            # IMPORTANTÍSIMO: responde en vez de cerrar la conexión
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            msg = json.dumps({"ok": False, "error": err}).encode("utf-8")
            self.wfile.write(msg)

    def log_message(self, format, *args):
        return

def main():
    server = HTTPServer(("127.0.0.1", 8766), Handler)
    server.serve_forever()

if __name__ == "__main__":
    main()
