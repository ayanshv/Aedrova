"""Connects the browser panel to the main window: where it docks, and who may drive it."""

from PySide6.QtCore import Qt


def ensure_browser(window):
    """Create the panel, its controller and its bridge the first time they are needed."""
    if getattr(window, "browser_panel", None) is not None:
        return window.browser_panel
    from aedrova.browser.bridge import BrowserBridge
    from aedrova.browser.controller import BrowserController
    from aedrova.browser.panel import BrowserPanel
    from aedrova.desktop.agent_permissions import mode

    panel = BrowserPanel(window.chat_page)
    panel.setMaximumWidth(640)
    panel.hide()
    panel.closed.connect(lambda: set_browser_visible(window, False))
    window.chat_row.addWidget(panel, 1)
    window.browser_panel = panel
    from PySide6.QtWidgets import QApplication

    QApplication.instance().aboutToQuit.connect(panel.shutdown)
    window.browser_controller = BrowserController(panel, mode=lambda: mode(window))
    window.browser_controller.requested.connect(
        lambda _job: set_browser_visible(window, True), Qt.ConnectionType.QueuedConnection
    )
    window.browser_bridge = BrowserBridge(window.browser_controller)
    return panel


def set_browser_visible(window, visible):
    panel = ensure_browser(window) if visible else getattr(window, "browser_panel", None)
    if panel is None:
        return
    panel.setVisible(visible)
    button = getattr(window, "browser_button", None)
    if button is not None:
        button.setChecked(visible)
    if visible and not panel.view.url().isValid():
        panel.address.setFocus()


def toggle_browser(window):
    panel = getattr(window, "browser_panel", None)
    set_browser_visible(window, not (panel is not None and panel.isVisible()))


def browser_launch_config(window):
    """How an agent run reaches this window's browser, or None when it is switched off."""
    if not window.settings.value("browser/enabled", True, type=bool):
        return None
    ensure_browser(window)
    return window.browser_bridge.launch_config()
