"""The browser as its own small process.

Qt WebEngine and the app's application-wide Python event filters cannot share one process:
the first time the page takes focus, a filter looks at one of the page's internal objects and
the whole app dies. So the browser panel, its rules and the agent bridge live here, in a
process with no such filters, and the main app talks to it over standard input and output.

Commands in (one JSON per line): show (with a screen rectangle), hide, mode, quit.
Events out: ready (port and token for the agent tools), closed, hidden.
"""

import json
import sys
import threading


def main():
    import PySide6.QtWebEngineWidgets  # noqa: F401  (must come before the application)
    from PySide6.QtCore import QCoreApplication, QObject, QRect, Qt, Signal
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Aedrova")
    app.setQuitOnLastWindowClosed(False)

    from aedrova.browser.bridge import BrowserBridge
    from aedrova.browser.controller import BrowserController
    from aedrova.browser.panel import BrowserPanel
    from aedrova.desktop.brand import app_icon
    from aedrova.desktop.theme import LIGHT, palette, stylesheet

    app.setPalette(palette(LIGHT))
    app.setStyleSheet(stylesheet(LIGHT))
    window = QWidget()
    window.setWindowTitle("Aedrova Browser")
    window.setWindowIcon(app_icon())
    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    panel = BrowserPanel()
    layout.addWidget(panel)
    state = {"mode": "ask"}
    controller = BrowserController(panel, mode=lambda: state["mode"])
    bridge = BrowserBridge(controller)
    bridge.start()

    def emit(**event):
        sys.stdout.write(json.dumps(event) + "\n")
        sys.stdout.flush()

    class Commands(QObject):
        arrived = Signal(dict)

    commands = Commands()

    def reveal(rect=None):
        if rect:
            window.setGeometry(QRect(rect["x"], rect["y"], rect["w"], rect["h"]))
        window.show()
        window.raise_()
        window.activateWindow()

    def handle(command):
        kind = command.get("cmd")
        if kind == "show":
            reveal(command.get("rect"))
        elif kind == "hide":
            window.hide()
        elif kind == "mode" and command.get("mode") in {"ask", "auto", "full"}:
            state["mode"] = command["mode"]
        elif kind == "quit":
            panel.shutdown()
            app.quit()

    commands.arrived.connect(handle)

    def listen():
        for line in sys.stdin:
            try:
                commands.arrived.emit(json.loads(line))
            except ValueError:
                continue
        commands.arrived.emit({"cmd": "quit"})  # the app went away

    threading.Thread(target=listen, daemon=True).start()
    panel.closed.connect(lambda: (window.hide(), emit(event="hidden")))
    controller.requested.connect(lambda _job: (reveal(), emit(event="shown")))
    app.aboutToQuit.connect(panel.shutdown)
    emit(event="ready", port=bridge.port, token=bridge.token)
    app.exec()


if __name__ == "__main__":
    main()
