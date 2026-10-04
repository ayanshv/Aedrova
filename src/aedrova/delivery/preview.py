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


class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def list_directory(self, path):
        self.send_error(404)
        return None

    def permitted(self):
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self.send_error(403)
            return False
        if self.headers.get("Origin") not in {None, f"http://127.0.0.1:{self.server.server_port}"}:
            self.send_error(403)
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
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        shutil.rmtree(self.temp)
