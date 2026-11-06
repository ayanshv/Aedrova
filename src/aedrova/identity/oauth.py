"""Native desktop OAuth: system browser, PKCE, and a short-lived loopback callback."""

import json
import os
import secrets
import socket
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Event, Thread
from urllib.parse import parse_qs, urlsplit

from aedrova.identity.callback_page import CSP, render_callback

PORT = 43827
REDIRECT_ALLOWLIST = f"http://127.0.0.1:{PORT}/auth/**"


class LoopbackServer(HTTPServer):


    allow_reuse_address = True

    def handle_error(self, request, client_address):

        pass

    def get_request(self):
        connection, address = super().get_request()
        self.active_connection = connection
        connection.settimeout(1)
        return connection, address


def apple_login_enabled():
    config = Path(__file__).parents[1] / "desktop/assets/public-config.json"
    if not getattr(sys, "frozen", False) and "AEDROVA_APPLE_LOGIN_ENABLED" in os.environ:
        return os.environ["AEDROVA_APPLE_LOGIN_ENABLED"] == "true"
    return config.is_file() and json.loads(config.read_text()).get("apple_login_enabled") is True


def google_sign_in(service, cancel=None, **options):
    return provider_sign_in(service, cancel, provider="google", **options)


def apple_sign_in(service, cancel=None, **options):
    return provider_sign_in(service, cancel, provider="apple", **options)


def provider_sign_in(
    service, cancel=None, *, provider, opener=webbrowser.open, timeout=180, port=PORT
):
    """Runs off the UI thread. Tokens never appear in the browser response or logs."""
    if provider not in {"google", "apple"}:
        raise ValueError("Unsupported sign-in provider")
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
                page = render_callback(True)
            elif "error" in query:
                result["error"] = True
                page = render_callback(False)
            else:
                self.send_error(400)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

    with LoopbackServer(("127.0.0.1", port), Callback) as server:
        server.timeout = 0.25
        redirect = f"http://127.0.0.1:{server.server_port}{path}"
        url = (
            service.google_authorization_url(redirect) if provider == "google"
            else service.apple_authorization_url(redirect)
        )
        if cancel.is_set():
            raise InterruptedError("Sign-in cancelled")
        if not opener(url):
            raise RuntimeError("Could not open system browser")
        deadline = time.monotonic() + timeout
        finished = Event()

        def interrupt_stalled_request():

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
        raise PermissionError(f"{provider.title()} sign-in was not completed")
    user = service.finish_google_sign_in(result["code"])
    if cancel.is_set():
        service.sign_out()
        raise InterruptedError("Sign-in cancelled")
    return user
