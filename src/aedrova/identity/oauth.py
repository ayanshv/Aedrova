"""Native desktop OAuth: system browser, PKCE, and a short-lived loopback callback."""

import secrets
import socket
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread
from urllib.parse import parse_qs, urlsplit

PORT = 43827
REDIRECT_ALLOWLIST = f"http://127.0.0.1:{PORT}/auth/**"


class LoopbackServer(HTTPServer):
    allow_reuse_address = False

    def handle_error(self, request, client_address):
        # Ignore incomplete/broken loopback requests without logging callback data.
        pass

    def get_request(self):
        connection, address = super().get_request()
        self.active_connection = connection
        connection.settimeout(1)
        return connection, address


def google_sign_in(service, cancel=None, *, opener=webbrowser.open, timeout=180, port=PORT):
    """Runs off the UI thread. Tokens never appear in the browser response or logs."""
    cancel = cancel or Event()
    path = "/auth/" + secrets.token_urlsafe(32)
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):  # noqa: N802
            parsed = urlsplit(self.path)
            expected_host = f"127.0.0.1:{self.server.server_port}"
            if (
                self.headers.get("Host") != expected_host
                or parsed.scheme
                or parsed.netloc
                or parsed.path != path
                or result
            ):
                self.send_error(404)
                return
            if len(parsed.query) > 8192:
                self.send_error(400)
                return
            try:
                query = parse_qs(parsed.query, max_num_fields=10)
            except ValueError:
                self.send_error(400)
                return
            codes = query.get("code", [])
            if len(codes) == 1 and codes[0] and len(codes[0]) <= 4096 and "error" not in query:
                result["code"] = codes[0]
                text = "Return to Aedrova to finish signing in. You can close this tab."
            elif "error" in query:
                result["error"] = True
                text = "Sign-in was not completed. Return to Aedrova to try again."
            else:
                self.send_error(400)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(text.encode())))
            self.end_headers()
            self.wfile.write(text.encode())

    with LoopbackServer(("127.0.0.1", port), Callback) as server:
        server.timeout = 0.25
        redirect = f"http://127.0.0.1:{server.server_port}{path}"
        url = service.google_authorization_url(redirect)
        if cancel.is_set():
            raise InterruptedError("Sign-in cancelled")
        if not opener(url):
            raise RuntimeError("Could not open system browser")
        deadline = time.monotonic() + timeout
        finished = Event()

        def interrupt_stalled_request():
            # Cancellation and the overall deadline also interrupt partial HTTP headers.
            while not finished.wait(0.05):
                if cancel.is_set() or time.monotonic() >= deadline:
                    connection = getattr(server, "active_connection", None)
                    if connection is not None:
                        try:
                            connection.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass
                    return

        watcher = Thread(target=interrupt_stalled_request, daemon=True)
        watcher.start()
        try:
            while not result and not cancel.is_set() and time.monotonic() < deadline:
                server.handle_request()
        finally:
            finished.set()
            watcher.join(timeout=1)
    if cancel.is_set():
        raise InterruptedError("Sign-in cancelled")
    if not result:
        raise TimeoutError("Sign-in timed out")
    if "error" in result:
        raise PermissionError("Google sign-in was not completed")
    user = service.finish_google_sign_in(result["code"])
    if cancel.is_set():
        service.sign_out()
        raise InterruptedError("Sign-in cancelled")
    return user
