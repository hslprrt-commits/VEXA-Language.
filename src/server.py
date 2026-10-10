
import io
import json
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from vexa import VEXAInterpreter, VEXAError

BASE_DIR = Path(__file__).resolve().parent
MAX_REQUEST_SIZE = 16_000
MAX_OUTPUT_SIZE = 20_000


class LimitedOutput(io.StringIO):
    def write(self, text):
        if self.tell() + len(text) > MAX_OUTPUT_SIZE:
            raise ValueError("Output limit exceeded.")
        return super().write(text)


class VEXAServer(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return

        page = BASE_DIR / "index.html"

        if not page.is_file():
            self.send_error(404, "Create src/index.html first")
            return

        body = page.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/run":
            self.send_json(404, {"error": "Endpoint not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid request length"})
            return

        if length < 1 or length > MAX_REQUEST_SIZE:
            self.send_json(413, {"error": "Request too large or empty"})
            return

        try:
            data = json.loads(self.rfile.read(length))
            code = data.get("code", "")
            inputs = data.get("inputs", [])

            if not isinstance(code, str) or len(code) > 10_000:
                self.send_json(400, {"error": "Invalid or oversized code"})
                return

            if (
                not isinstance(inputs, list)
                or len(inputs) > 50
                or any(not isinstance(x, str) or len(x) > 1000 for x in inputs)
            ):
                self.send_json(400, {"error": "Invalid input values"})
                return

            output = LimitedOutput()
            pending_inputs = iter(inputs)

            def read_input(prompt=""):
                output.write(str(prompt) + "\n")
                return next(pending_inputs, "")

            with redirect_stdout(output), patch(
                "builtins.input", side_effect=read_input
            ):
                VEXAInterpreter().run(code)

            self.send_json(200, {
                "output": output.getvalue(),
                "success": True,
            })

        except VEXAError as exc:
            self.send_json(400, {
                "error": str(exc),
                "success": False,
            })
        except (ValueError, TypeError, ZeroDivisionError) as exc:
            self.send_json(400, {
                "error": str(exc) or "Invalid VEXA program",
                "success": False,
            })
        except Exception:
            self.send_json(500, {
                "error": "Internal server error",
                "success": False,
            })

    def log_message(self, format, *args):
        print("[VEXA]", format % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), VEXAServer)
    print("VEXA server starting on port 8000...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nVEXA server stopped.")
    finally:
        server.server_close()
