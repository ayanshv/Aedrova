"""Connects the browser to the main window.

The browser runs in its own process (see `aedrova.browser.host`) and sits beside the main
window. This module starts it when first needed, keeps it told which access mode applies, and
hands agent runs the address and token of its tool bridge.
"""

import json
import sys

from PySide6.QtCore import QEventLoop, QObject, QProcess, QTimer, Signal

PANEL_WIDTH = 480


def host_command():
    if getattr(sys, "frozen", False):
        return sys.executable, ["--browser-host"]
    return sys.executable, ["-m", "aedrova.browser.host"]


class BrowserHost(QObject):
    ready = Signal()
    visibility = Signal(bool)

    def __init__(self, window, command=None):
        super().__init__(window)
        self.window = window
        self.command = command or host_command()
        self.process = None
        self.port = self.token = None
        self.visible = False
        self.pending = b""

    def running(self):
        return self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning

    def start(self):
        if self.running():
            return
        self.port = self.token = None
        self.process = QProcess(self)
        program, arguments = self.command
        self.process.readyReadStandardOutput.connect(self.read)
        self.process.finished.connect(self.stopped)
        self.process.start(program, arguments)

    def read(self):
        self.pending += bytes(self.process.readAllStandardOutput())
        while b"\n" in self.pending:
            line, self.pending = self.pending.split(b"\n", 1)
            try:
                event = json.loads(line)
            except ValueError:
                continue  # a stray log line from the toolkit
            self.handle(event)

    def handle(self, event):
        kind = event.get("event")
        if kind == "ready":
            self.port, self.token = event["port"], event["token"]
            self.send({"cmd": "mode", "mode": current_mode(self.window)})
            self.ready.emit()
        elif kind in {"shown", "hidden"}:
            self.visible = kind == "shown"
            self.visibility.emit(self.visible)

    def stopped(self, *_):
        self.port = self.token = None
        self.visible = False
        self.visibility.emit(False)

    def send(self, command):
        if self.running():
            self.process.write((json.dumps(command) + "\n").encode())

    def wait_ready(self, timeout=20000):
        """Start if needed and wait, without freezing the window, until the bridge is up."""
        self.start()
        if self.port is None:
            loop = QEventLoop()
            self.ready.connect(loop.quit)
            self.process.finished.connect(loop.quit)
            QTimer.singleShot(timeout, loop.quit)
            loop.exec()
        return self.port is not None

    def show(self):
        self.wait_ready()
        self.send({"cmd": "show", "rect": dock_rectangle(self.window)})
        self.visible = True
        self.visibility.emit(True)

    def hide(self):
        self.send({"cmd": "hide"})
        self.visible = False
        self.visibility.emit(False)

    def shutdown(self):
        if self.running():
            self.send({"cmd": "quit"})
            self.process.waitForFinished(3000)
            if self.running():
                self.process.kill()


def current_mode(window):
    from aedrova.desktop.agent_permissions import mode

    return mode(window)


def dock_rectangle(window):
    """Beside the conversation: flush with the main window's right edge, same height."""
    frame = window.frameGeometry()
    screen = (window.screen() or window.windowHandle().screen()).availableGeometry()
    x = frame.right() + 1
    if x + PANEL_WIDTH > screen.right():  # no room beside it: tuck against the screen edge
        x = max(screen.left(), screen.right() - PANEL_WIDTH)
    return {
        "x": x,
        "y": frame.top(),
        "w": PANEL_WIDTH,
        "h": max(480, frame.height()),
    }


def ensure_browser(window):
    host = getattr(window, "browser_host", None)
    if host is None:
        from PySide6.QtWidgets import QApplication

        host = window.browser_host = BrowserHost(window)
        host.visibility.connect(lambda shown: sync_button(window, shown))
        QApplication.instance().aboutToQuit.connect(host.shutdown)
    return host


def sync_button(window, shown):
    button = getattr(window, "browser_button", None)
    if button is not None:
        button.setChecked(bool(shown))


def set_browser_visible(window, visible):
    host = ensure_browser(window) if visible else getattr(window, "browser_host", None)
    if host is None:
        return
    host.show() if visible else host.hide()


def toggle_browser(window):
    host = getattr(window, "browser_host", None)
    set_browser_visible(window, not (host is not None and host.visible))


def push_mode(window):
    """Tell the browser which access mode is selected now."""
    host = getattr(window, "browser_host", None)
    if host is not None:
        host.send({"cmd": "mode", "mode": current_mode(window)})


def browser_launch_config(window):
    """How an agent run reaches this window's browser, or None when it is switched off."""
    if not window.settings.value("browser/enabled", True, type=bool):
        return None
    host = ensure_browser(window)
    if not host.wait_ready():
        return None
    push_mode(window)
    command, arguments = (
        (sys.executable, ["--browser-mcp"])
        if getattr(sys, "frozen", False)
        else (sys.executable, ["-m", "aedrova.browser.mcp_server"])
    )
    return {
        "command": command,
        "args": arguments,
        "env": {"AEDROVA_BROWSER_PORT": str(host.port), "AEDROVA_BROWSER_TOKEN": host.token},
    }
