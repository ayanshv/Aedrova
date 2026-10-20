"""A loopback-only static preview with no source-directory or credential exposure."""

import functools
import http.server
import shutil
import tempfile
import threading
from pathlib import Path
from urllib.parse import unquote, urlsplit

from aedrova.delivery.files import inventory

STATIC = {
    ".html",
    ".css",
    ".js",
    ".mjs",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
}


class PreviewServer(http.server.ThreadingHTTPServer):
    """A local page cannot exhaust threads by opening idle preview connections."""

    daemon_threads = True
    request_queue_size = 8

    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(*args, **kwargs)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(2)
        return connection, address

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def list_directory(self, path):
        self.send_error(404)
        return None

    def permitted(self):
        if self.headers.get_all("Host", []) != [f"127.0.0.1:{self.server.server_port}"]:
            self.send_error(403)
            return False
        if self.headers.get("Origin") not in {None, f"http://127.0.0.1:{self.server.server_port}"}:
            self.send_error(403)
            return False
        if len(self.path) > 8192 or len(self.headers.get_all("Origin", [])) > 1:
            self.send_error(400)
            return False
        path = unquote(urlsplit(self.path).path)
        if any(part.startswith(".") for part in path.split("/") if part):
            self.send_error(404)
            return False
        return True

    def do_GET(self):  # noqa: N802
        if self.permitted():
            super().do_GET()

    def do_HEAD(self):  # noqa: N802
        if self.permitted():
            super().do_HEAD()

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; connect-src 'none'; form-action 'none'; "
            "frame-ancestors 'none'",
        )
        super().end_headers()


class StaticPreview:
    def __init__(self, project):
        data = inventory(project)
        if "index.html" not in data:
            raise ValueError(
                "Static preview needs index.html at the project root. Use your IDE for "
                "server/framework projects."
            )
        self.temp = Path(tempfile.mkdtemp(prefix="aedrova-preview-"))
        for name, version in data.items():
            relative = Path(name)
            if relative.suffix.lower() not in STATIC or any(
                p.startswith(".") for p in relative.parts
            ):
                continue
            target = self.temp / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(version.data)
        handler = functools.partial(StaticHandler, directory=str(self.temp))
        self.server = PreviewServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        shutil.rmtree(self.temp)
