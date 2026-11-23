"""The browser panel: one isolated profile, visible agent activity, and a Stop button."""

from pathlib import Path

from PySide6.QtCore import (
    QEvent,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QStandardPaths,
    Qt,
    QTimer,
    QUrl,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

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


class GlobeMark(QWidget):
    """The web icon, drawn as vectors so it stays sharp at any display scale."""

    def __init__(self, size=56):
        super().__init__()
        self.setFixedSize(size, size)
        self.setAccessibleName("Web")

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        ink = QColor(self.palette().color(self.palette().ColorRole.Text))
        ink.setAlpha(200)
        painter.setPen(QPen(ink, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        side = min(self.width(), self.height()) - 8
        box = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)
        painter.drawEllipse(box)
        painter.drawEllipse(QRectF(box.center().x() - side * 0.2, box.top(), side * 0.4, side))
        middle = box.center().y()
        painter.drawLine(QPointF(box.left(), middle), QPointF(box.right(), middle))
        radius = side / 2
        for fraction in (0.27, 0.73):  # latitude lines, as wide as the circle is at that height
            y = box.top() + side * fraction
            half = (radius**2 - (y - middle) ** 2) ** 0.5
            painter.drawLine(
                QPointF(box.center().x() - half, y), QPointF(box.center().x() + half, y)
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
    view_changed = Signal(bool)

    TITLE = "Browse with Aedrova"
    TEXT = (
        "Open any website here. Ask Aedrova to read it, research it or do the clicking for "
        "you, and watch every step. You can take over or press Stop at any time."
    )

    def __init__(self, parent=None, *, persistent=True):
        super().__init__(parent)
        self.setObjectName("BrowserPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.approved = set()
        self.pending = None
        self.page = self.view = self.cursor = None
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

        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_welcome())
        column.addWidget(self.stack, 1)
        self.setMinimumWidth(380)
        self.set_navigation(False)

    # -- the empty state ------------------------------------------------------------
    def build_welcome(self):
        page = QWidget()
        page.setObjectName("BrowserWelcome")
        box = QVBoxLayout(page)
        box.setContentsMargins(32, 0, 32, 0)
        box.setSpacing(10)
        box.addStretch(3)
        self.welcome_icon = GlobeMark(56)
        box.addWidget(self.welcome_icon, alignment=Qt.AlignmentFlag.AlignHCenter)
        box.addSpacing(8)
        self.welcome_title = label(self.TITLE, "heading")
        self.welcome_title.setObjectName("BrowserWelcomeTitle")
        self.welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(self.welcome_title)
        self.welcome_text = label(self.TEXT, "muted", wrap=True)
        self.welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_text.setFixedWidth(340)
        self.welcome_text.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        box.addWidget(self.welcome_text, alignment=Qt.AlignmentFlag.AlignHCenter)
        box.addStretch(4)
        return page

    def fit_welcome(self):
        """Give the description exactly the height its wrapped text needs on this display."""
        metrics = self.welcome_text.fontMetrics()
        wanted = metrics.boundingRect(
            0, 0, self.welcome_text.width(), 10000, Qt.TextFlag.TextWordWrap, self.TEXT
        ).height()
        self.welcome_text.setFixedHeight(wanted + 6)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.fit_welcome()

    def changeEvent(self, event):  # noqa: N802
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            if hasattr(self, "welcome_text"):
                self.fit_welcome()
        super().changeEvent(event)

    # -- the page, made only when it is needed ---------------------------------------
    def ensure_view(self):
        """Create the web view on first use. Application-wide event filters are lifted while
        it exists, because the engine's internal objects crash them."""
        if self.view is not None:
            return self.view
        from PySide6.QtWebEngineWidgets import QWebEngineView

        from aedrova.desktop.appfilters import registry

        registry.hold("browser")
        self.page = BrowserPage(self.profile, self)
        self.page.notice.connect(self.say)
        self.view = QWebEngineView()
        self.view.setPage(self.page)
        self.stack.addWidget(self.view)
        self.stack.setCurrentWidget(self.view)
        self.cursor = AgentCursor(self.view)
        self.back.clicked.connect(self.view.back)
        self.forward.clicked.connect(self.view.forward)
        self.reload.clicked.connect(self.view.reload)
        self.view.urlChanged.connect(self.url_changed)
        self.set_navigation(True)
        self.view_changed.emit(True)
        return self.view

    def release_view(self):
        """Close the page and give the application its event filters back."""
        if self.view is None:
            return
        import shiboken6

        from aedrova.desktop.appfilters import registry

        view, page = self.view, self.page
        self.view = self.page = self.cursor = None
        self.stack.removeWidget(view)
        self.stack.setCurrentIndex(0)
        view.hide()
        view.setParent(None)
        view.deleteLater()
        if page is not None and shiboken6.isValid(page):
            page.deleteLater()
        self.address.clear()
        self.set_navigation(False)
        registry.release("browser")
        self.view_changed.emit(False)

    def set_navigation(self, on):
        for control in (self.back, self.forward, self.reload):
            control.setEnabled(on)

    def url_changed(self, url):
        self.address.setText(url.toString())

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
        self.ensure_view().load(QUrl(text))

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
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearHttpCache()
        self.approved.clear()

    def shutdown(self):
        """Chromium wants its page gone before its profile; call this before quitting."""
        import shiboken6

        from aedrova.desktop.appfilters import registry

        page = self.page
        self.page = None
        if self.view is not None:
            self.view.setPage(None)
        if page is not None and shiboken6.isValid(page):
            shiboken6.delete(page)
        registry.release("browser")

    def current_host(self):
        return host_of(self.view.url().toString()) if self.view is not None else ""
