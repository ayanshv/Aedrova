"""The browser as a large side panel inside the workspace.

The panel is created hidden. Its web page is only made when something opens it, and
application-wide event filters are lifted while a page exists (see `appfilters`).
"""

from PySide6.QtCore import Qt

CHAT_SHARE, BROWSER_SHARE = 5, 4  # the browser takes a little under half of the width


def ensure_browser(window):
    """Create the panel, its controller and its agent bridge the first time they are needed."""
    if getattr(window, "browser_panel", None) is not None:
        return window.browser_panel
    from PySide6.QtWidgets import QApplication

    from aedrova.browser.bridge import BrowserBridge
    from aedrova.browser.controller import BrowserController
    from aedrova.browser.panel import BrowserPanel
    from aedrova.desktop.agent_permissions import mode

    panel = BrowserPanel(window.chat_page)
    panel.hide()
    panel.closed.connect(lambda: set_browser_visible(window, False))
    window.chat_row.addWidget(panel)
    window.chat_row.setStretchFactor(window.chat_column, CHAT_SHARE)
    window.chat_row.setStretchFactor(panel, 0)
    window.browser_panel = panel
    window.browser_controller = BrowserController(panel, mode=lambda: mode(window))
    window.browser_controller.requested.connect(
        lambda _job: set_browser_visible(window, True), Qt.ConnectionType.QueuedConnection
    )
    window.browser_bridge = BrowserBridge(window.browser_controller)
    QApplication.instance().aboutToQuit.connect(panel.shutdown)
    QApplication.instance().aboutToQuit.connect(window.browser_bridge.stop)
    return panel


def set_browser_visible(window, visible):
    panel = ensure_browser(window) if visible else getattr(window, "browser_panel", None)
    if panel is None:
        return
    if visible:
        window.select_tab(0)  # the panel sits beside the conversation
        window.chat_row.setStretchFactor(panel, BROWSER_SHARE)
        panel.show()
        panel.address.setFocus()
    else:
        panel.hide()
        window.chat_row.setStretchFactor(panel, 0)
        if panel.pending is not None:
            panel.answer(False)
        panel.release_view()  # closing the panel closes its page and returns the app's filters
    button = getattr(window, "browser_button", None)
    if button is not None:
        button.setChecked(bool(visible))


def toggle_browser(window):
    panel = getattr(window, "browser_panel", None)
    set_browser_visible(window, not (panel is not None and panel.isVisible()))


def browser_launch_config(window):
    """How an agent run reaches this window's browser, or None when it is switched off."""
    if not window.settings.value("browser/enabled", True, type=bool):
        return None
    ensure_browser(window)
    return window.browser_bridge.launch_config()
