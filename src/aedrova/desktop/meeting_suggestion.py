"""A calm pill that offers meeting notes. It never records, and it dismisses itself."""

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import AppMenu
from aedrova.desktop.motion import reduced

WIDTH, HEIGHT = 560, 92
LIFETIME_MS = 30000


class ChevronButton(QPushButton):
    """The dropdown half of the split button, with a crisp drawn chevron."""

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(
            QPen(
                QColor("#FFFFFF"),
                2.2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        x, y = self.width() / 2 + 1, self.height() / 2 - 2
        painter.drawPolyline([QPointF(x - 6, y), QPointF(x, y + 6), QPointF(x + 6, y)])


class MeetingSuggestion(QWidget):
    review_requested = Signal()  # Start notes
    stop_requested = Signal()  # Not now
    disable_requested = Signal()  # Turn off suggestions
    expired = Signal()

    def __init__(self, owner):
        super().__init__(
            owner,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        self.setWindowTitle("Aedrova meeting notes")
        self.setFixedSize(WIDTH, HEIGHT)
        self.remaining = 1.0
        self.theme = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(34, 14, 28, 14)
        outer.setSpacing(16)
        outer.addWidget(BrandMark(40), alignment=Qt.AlignmentFlag.AlignVCenter)
        copy = QVBoxLayout()
        copy.setSpacing(1)
        self.title = QLabel("Take meeting notes?")
        self.detail = QLabel("Transcription stays on this Mac")
        copy.addStretch()
        copy.addWidget(self.title)
        copy.addWidget(self.detail)
        copy.addStretch()
        outer.addLayout(copy, 1)

        self.start = QPushButton("Start notes")
        self.start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start.setAccessibleName("Start meeting notes")
        self.start.setToolTip("Start meeting notes")
        self.start.clicked.connect(self.review_requested)
        self.more = ChevronButton("")
        self.more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more.setAccessibleName("More meeting note options")
        self.more.setToolTip("More options")
        self.more.clicked.connect(self.open_menu)
        split = QHBoxLayout()
        split.setSpacing(1)
        split.addWidget(self.start)
        split.addWidget(self.more)
        outer.addLayout(split)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)
        self.apply_theme(None)

    # The detector drives the pill with the same calls it used for the old capsule.
    @property
    def review(self):
        return self.start

    @property
    def stop(self):
        return self.more

    def set_state(self, caption, *, listening=False):
        self.title.setText(caption)
        self.setAccessibleName("Aedrova meeting notes: " + caption)

    def apply_theme(self, theme):
        self.theme = theme
        dark = bool(theme) and theme.name != "light"
        text = theme.text if theme else "#20242C"
        muted = theme.muted if theme else "#5B6573"
        accent = theme.accent if theme else "#246BFD"
        hover = theme.accent_hover if theme else "#1E5CE0"
        self.title.setStyleSheet(
            f"background:transparent;color:{text};font-size:17px;font-weight:600;"
        )
        self.detail.setStyleSheet(f"background:transparent;color:{muted};font-size:14px;")
        base = (
            f"QPushButton{{background:{accent};color:#FFFFFF;border:0;"
            "font-size:16px;font-weight:600;}"
            f"QPushButton:hover{{background:{hover};}}"
        )
        self.start.setStyleSheet(
            base + "QPushButton{border-top-left-radius:21px;border-bottom-left-radius:21px;"
            "border-top-right-radius:4px;border-bottom-right-radius:4px;padding:0 24px;}"
        )
        self.more.setStyleSheet(
            base + "QPushButton{border-top-right-radius:21px;border-bottom-right-radius:21px;"
            "border-top-left-radius:4px;border-bottom-left-radius:4px;padding:0 14px;"
            "}"
        )
        self.start.setFixedHeight(42)
        self.more.setFixedSize(46, 42)
        self.pill = QColor("#1F2126" if dark else "#FFFFFF")
        self.edge = QColor(255, 255, 255, 36) if dark else QColor(0, 0, 0, 30)
        self.track = QColor(accent)
        self.update()

    def open_menu(self):
        menu = AppMenu(self)
        menu.addAction("Not now", self.stop_requested.emit)
        menu.addAction("Turn off suggestions", self.disable_requested.emit)
        menu.popup(self.more.mapToGlobal(self.more.rect().bottomRight()))

    def show_on_side(self):
        owner = self.parentWidget()
        self.apply_theme(getattr(owner, "theme", None))
        area = owner.screen().availableGeometry()
        self.move(area.center().x() - self.width() // 2, area.top() + 10)
        self.remaining = 1.0
        self.show()

    def tick(self):
        self.remaining -= self.timer.interval() / LIFETIME_MS
        if self.remaining <= 0:
            self.timer.stop()
            self.hide()
            self.expired.emit()
            return
        self.update()

    def showEvent(self, event):  # noqa: N802
        if not reduced():
            self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        body = QRectF(self.rect()).adjusted(18, 10, -18, -18)
        radius = body.height() / 2
        painter.setPen(Qt.PenStyle.NoPen)
        for spread in range(12, 0, -1):  # soft depth without a live blur
            alpha = round(6 * (1 - spread / 13) ** 1.6)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(
                body.translated(0, 6).adjusted(-spread, -spread, spread, spread),
                radius + spread,
                radius + spread,
            )
        path = QPainterPath()
        path.addRoundedRect(body, radius, radius)
        painter.setBrush(self.pill)
        painter.setPen(QPen(self.edge, 1))
        painter.drawPath(path)
        if not reduced():  # a thin countdown along the bottom edge, like the reference
            painter.setClipPath(path)
            painter.setPen(Qt.PenStyle.NoPen)
            color = QColor(self.track)
            color.setAlpha(150)
            painter.setBrush(color)
            painter.drawRect(
                QRectF(body.left(), body.bottom() - 3, body.width() * max(0.0, self.remaining), 3)
            )
