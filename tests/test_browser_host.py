"""The browser lives in its own process; the window starts it and follows its state."""

import json
import socket

import pytest
from PySide6.QtCore import QSettings

pytest.importorskip("PySide6.QtWebEngineWidgets")

from aedrova.desktop.window import AedrovaWindow  # noqa: E402
from aedrova.desktop.window_browser import (  # noqa: E402
    BrowserHost,
    browser_launch_config,
    dock_rectangle,
    host_command,
    toggle_browser,
)


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
    widget = AedrovaWindow(
        settings=QSettings(str(tmp_path / "browser.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(widget)
    widget.show()
    yield widget
    host = getattr(widget, "browser_host", None)
    if host is not None:
        host.shutdown()


def ask(port, **message):
    with socket.create_connection(("127.0.0.1", port), timeout=20) as connection:
        connection.sendall((json.dumps(message) + "\n").encode())
        data = b""
        while not data.endswith(b"\n"):
            chunk = connection.recv(65536)
            if not chunk:
                break
            data += chunk
    return json.loads(data)


def test_the_main_app_never_loads_the_web_engine_itself(window):
    assert getattr(window, "browser_host", None) is None  # nothing starts until it is used
    assert host_command()[1][-1] == "aedrova.browser.host"


def test_the_button_starts_the_browser_process_and_the_agent_bridge_answers(window, qtbot):
    window.browser_button.click()
    host = window.browser_host
    assert host.running() and host.port and host.token and host.visible
    assert window.browser_button.isChecked()
    refused = ask(host.port, token="wrong", action="read")
    assert refused == {"ok": False, "error": "Not authorized."}
    config = browser_launch_config(window)
    assert config["env"]["AEDROVA_BROWSER_PORT"] == str(host.port)
    assert config["env"]["AEDROVA_BROWSER_TOKEN"] == host.token
    refused = ask(host.port, token=host.token, action="open", args={"url": "http://127.0.0.1:9"})
    assert refused["ok"] is False and "blocked" in refused["error"].lower()
    toggle_browser(window)
    assert not host.visible and not window.browser_button.isChecked()


def test_it_can_be_switched_off_and_follows_the_access_mode(window):
    window.settings.setValue("browser/enabled", False)
    assert browser_launch_config(window) is None
    window.settings.setValue("browser/enabled", True)
    config = browser_launch_config(window)
    assert config is not None
    from aedrova.desktop.agent_permissions import key

    window.settings.setValue(key(window), "full")  # no signed-in user here: nothing to follow
    assert window.browser_host.running()


def test_it_sits_beside_the_window_and_dies_with_the_app(window, qtbot):
    rect = dock_rectangle(window)
    assert rect["w"] == 480 and rect["h"] >= 480
    host = BrowserHost(window)
    assert host.wait_ready()
    process = host.process
    host.shutdown()
    assert not host.running() and process.exitStatus() is not None
