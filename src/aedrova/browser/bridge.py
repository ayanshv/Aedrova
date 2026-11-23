"""A loopback socket between the app's browser and the tool server an agent talks to.

Only a process that was handed this session's random token can use it, and every request
still passes the access-mode rules in the controller. The socket accepts one short JSON
line per request and answers with one JSON line.
"""

import hmac
import json
import secrets
import socketserver
import sys
import threading

from aedrova.browser.policy import ACTIONS

MAX_REQUEST = 64 * 1024
TIMEOUT = 90


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        bridge = self.server.bridge
        try:
            line = self.rfile.readline(MAX_REQUEST + 1)
            if not line or len(line) > MAX_REQUEST:
                raise ValueError("Request too large.")
            request = json.loads(line)
            token = str(request.get("token", ""))
            if not hmac.compare_digest(token, bridge.token):
                raise PermissionError("Not authorized.")
            action, args = request.get("action"), request.get("args") or {}
            if action not in ACTIONS or not isinstance(args, dict):
                raise ValueError("That browser action is not available.")
            result = bridge.controller.submit(action, args).result(timeout=TIMEOUT)
            reply = {"ok": True, "result": result}
        except Exception as error:  # the agent gets a plain sentence, never a traceback
            reply = {"ok": False, "error": str(error) or "The browser could not do that."}
        self.wfile.write((json.dumps(reply) + "\n").encode())


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class BrowserBridge:
    def __init__(self, controller):
        self.controller = controller
        self.token = secrets.token_urlsafe(24)
        self.server = None

    @property
    def port(self):
        return self.server.server_address[1] if self.server else None

    def start(self):
        if self.server is None:
            self.server = Server(("127.0.0.1", 0), Handler)
            self.server.bridge = self
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self.port

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    def launch_config(self):
        """What the agent runtime needs to start the tool server and reach this bridge."""
        self.start()
        if getattr(sys, "frozen", False):
            command, args = sys.executable, ["--browser-mcp"]
        else:
            command, args = sys.executable, ["-m", "aedrova.browser.mcp_server"]
        return {
            "command": command,
            "args": args,
            "env": {
                "AEDROVA_BROWSER_PORT": str(self.port),
                "AEDROVA_BROWSER_TOKEN": self.token,
            },
        }
