"""The browser panel: one isolated profile, visible agent activity, and a Stop button."""

from pathlib import Path

from PySide6.QtCore import QPointF, QPropertyAnimation, QStandardPaths, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QVBoxLayout, QWidget

from aedrova.browser.policy import Refusal, check_url, host_of
from aedrova.desktop import motion
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.icons import assign


def storage_path():
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    return str(Path(base) / "browser")


def is_local_host(host):
    from aedrova.browser.policy import is_public_address

    if not host:
        return False
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        return True
    return (
        host.replace(".", "").replace(":", "").isalnum()
        and (host[0].isdigit() or ":" in host or host.startswith("["))
        and not is_public_address(host.strip("[]"))
    )


class Guard(QWebEngineUrlRequestInterceptor):
    """While an agent is driving, pages may not reach into the local network."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.strict = False

    def interceptRequest(self, info):  # noqa: N802
        if self.strict and is_local_host(info.requestUrl().host().lower()):
            info.block(True)


class BrowserPage(QWebEnginePage):
    notice = Signal(str)

    def __init__(self, profile, panel):
        super().__init__(profile, panel)
        self.panel = panel
        self.allow_html = False  # tests load their own pages with setHtml
        settings = self.settings()
        for attribute, value in (
            (QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False),
            (QWebEngineSettings.WebAttribute.PluginsEnabled, False),
            (QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, False),
            (QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False),
            (QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False),
            (QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False),
        ):
            settings.setAttribute(attribute, value)
        # No camera, microphone, location, notification or clipboard prompts, ever.
        self.permissionRequested.connect(lambda permission: permission.deny())

    def createWindow(self, kind):  # noqa: N802
        return self  # a pop-up opens in this same panel, never in a window of its own

    def acceptNavigationRequest(self, url, kind, is_main_frame):  # noqa: N802
        if not is_main_frame:
            return True
        if self.allow_html and url.scheme() == "data":
            return True
        if url.scheme() not in {"http", "https", "about", "blob"}:
            self.notice.emit("That kind of link can't be opened here.")
            return False
        if self.panel.guard.strict and url.scheme() in {"http", "https"}:
            try:
                check_url(url.toString())
            except Refusal as refusal:
                self.notice.emit(str(refusal))
                return False
        return True


class AgentCursor(QWidget):
    """A soft ring that glides to where the agent is about to click or type."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedSize(34, 34)
        self.hide()
        self.slide = QPropertyAnimation(self, b"pos", self)
        self.slide.setDuration(320)
        self.slide.setEasingCurve(motion.EASE)
        self.idle = QTimer(self)
        self.idle.setSingleShot(True)
        self.idle.timeout.connect(self.hide)

    def move_to(self, x, y):
        target = QPointF(x - 17, y - 17).toPoint()
        if motion.reduced() or not self.isVisible():
            self.move(target)
        else:
            self.slide.stop()
            self.slide.setStartValue(self.pos())
            self.slide.setEndValue(target)
            self.slide.start()
        self.show()
        self.raise_()
        self.idle.start(2500)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#3D74FF"), 2))
        painter.setBrush(QColor(61, 116, 255, 50))
        painter.drawEllipse(4, 4, 26, 26)


class Bar(QFrame):
    def __init__(self, name):
        super().__init__()
        self.setObjectName(name)
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(12, 8, 12, 8)
        self.row.setSpacing(8)
        self.text = label("", wrap=True)
        self.row.addWidget(self.text, 1)
        self.hide()


class BrowserPanel(QWidget):
    closed = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None, *, persistent=True):
        super().__init__(parent)
        self.setObjectName("BrowserPanel")
        self.approved = set()
        self.pending = None
        self.profile = (
            QWebEngineProfile("AedrovaBrowser", self) if persistent else QWebEngineProfile(self)
        )
        if persistent:
            self.profile.setPersistentStoragePath(storage_path())
            self.profile.setCachePath(storage_path() + "/cache")
            self.profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
            )
        self.profile.downloadRequested.connect(self.refuse_download)
        self.guard = Guard(self)
        self.profile.setUrlRequestInterceptor(self.guard)
        self.page = BrowserPage(self.profile, self)
        self.page.notice.connect(self.say)

        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        tools = QFrame()
        tools.setObjectName("BrowserToolbar")
        row = QHBoxLayout(tools)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(6)
        self.back = button("", "Back", "icon")
        assign(self.back, "back")
        self.forward = button("", "Forward", "icon")
        assign(self.forward, "chevron_right")
        self.reload = button("", "Reload", "icon")
        assign(self.reload, "refresh")
        for control in (self.back, self.forward, self.reload):
            control.setFixedSize(28, 28)
            row.addWidget(control)
        self.address = QLineEdit()
        self.address.setPlaceholderText("Search or enter a web address")
        self.address.setAccessibleName("Web address")
        self.address.returnPressed.connect(lambda: self.go(self.address.text()))
        row.addWidget(self.address, 1)
        self.close_button = button("", "Close browser", "icon")
        assign(self.close_button, "close")
        self.close_button.setFixedSize(28, 28)
        self.close_button.clicked.connect(self.closed.emit)
        row.addWidget(self.close_button)
        column.addWidget(tools)

        self.banner = Bar("BrowserBanner")
        self.stop = button("Stop", role="outline")
        self.stop.clicked.connect(self.stop_requested.emit)
        self.banner.row.addWidget(self.stop)
        self.allow_again = button("Let Aedrova continue", role="outline")
        self.allow_again.hide()
        self.banner.row.addWidget(self.allow_again)
        column.addWidget(self.banner)
        self.approval = Bar("BrowserApproval")
        self.allow = button("Allow", role="primary")
        self.deny = button("Not now", role="outline")
        self.approval.row.addWidget(self.deny)
        self.approval.row.addWidget(self.allow)
        self.allow.clicked.connect(lambda: self.answer(True))
        self.deny.clicked.connect(lambda: self.answer(False))
        column.addWidget(self.approval)
        self.notice = Bar("BrowserNotice")
        column.addWidget(self.notice)

        self.view = QWebEngineView()
        self.view.setPage(self.page)
        column.addWidget(self.view, 1)
        self.cursor = AgentCursor(self.view)
        self.back.clicked.connect(self.view.back)
        self.forward.clicked.connect(self.view.forward)
        self.reload.clicked.connect(self.view.reload)
        self.view.urlChanged.connect(lambda url: self.address.setText(url.toString()))
        self.setMinimumWidth(360)

    # -- people ---------------------------------------------------------------------
    def go(self, text):
        """A person may open any web address; only the agent is held to the public-web rule."""
        text = text.strip()
        if not text:
            return
        if "." not in text and "://" not in text and "localhost" not in text:
            text = "https://duckduckgo.com/?q=" + QUrl.toPercentEncoding(text).data().decode()
        elif "://" not in text:
            text = "https://" + text
        self.view.load(QUrl(text))

    def refuse_download(self, download):
        download.cancel()
        self.say("Downloads are blocked in this panel.")

    def say(self, text):
        self.notice.text.setText(text)
        self.notice.show()
        QTimer.singleShot(5000, self.notice.hide)

    # -- the agent ------------------------------------------------------------------
    def set_agent_active(self, active, text="Aedrova is browsing"):
        self.guard.strict = bool(active)  # the public-web rule applies while an agent drives
        self.banner.text.setText(text)
        self.stop.setVisible(active)
        self.allow_again.hide()
        self.banner.setVisible(active)
        if active:
            motion.fade_in(self.banner, motion.BASE)

    def set_stopped(self, stopped):
        self.banner.text.setText("Stopped. Aedrova can't use the browser until you allow it.")
        self.stop.hide()
        self.allow_again.setVisible(stopped)
        self.banner.setVisible(stopped)

    def ask(self, question, callback):
        """Ask the person; the agent's action waits for the answer."""
        if self.pending is not None:
            callback(False)
            return
        self.pending = callback
        self.approval.text.setText(question)
        self.approval.show()
        motion.fade_in(self.approval, motion.BASE)
        self.allow.setFocus()

    def answer(self, allowed):
        callback, self.pending = self.pending, None
        self.approval.hide()
        if callback:
            callback(allowed)

    def clear_data(self):
        """Forget cookies and sign-ins for the panel's own profile."""
        store = self.profile.cookieStore()
        store.deleteAllCookies()
        self.profile.clearHttpCache()
        self.approved.clear()

    def shutdown(self):
        """Chromium wants its page gone before its profile; call this before quitting."""
        import shiboken6

        page, self.page = self.page, None
        if page is not None and shiboken6.isValid(page):
            self.view.setPage(None)
            shiboken6.delete(page)

    def current_host(self):
        return host_of(self.view.url().toString())
