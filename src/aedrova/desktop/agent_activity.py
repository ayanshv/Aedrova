"""Accessible live activity text; displays public updates, never private reasoning."""

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QLabel, QPushButton

from aedrova.desktop.materials import system_font
from aedrova.desktop.theme import DARK


class AgentActivity(QPushButton):
    def __init__(self):
        super().__init__()
        self.setAccessibleName("Agent activity · open details")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFont(system_font(14))
        self.active = False
        self.reduced_motion = False
        self.phase = 0.0
        self.theme = DARK
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.advance)

    def sizeHint(self):  # noqa: N802
        return QSize(300, 32)

    def configure(self, theme, reduced_motion, active):
        self.theme, self.reduced_motion, self.active = theme, reduced_motion, active
        self.sync_animation()
        self.update()

    def sync_animation(self):
        if self.active and not self.reduced_motion and self.isVisible():
            self.timer.start()
        else:
            self.timer.stop()
            self.phase = 0.0

    def advance(self):
        self.phase = (self.phase + 0.018) % 1.0
        self.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.sync_animation()

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())
        base = QColor(self.theme.muted)
        if self.active and not self.reduced_motion:
            center = self.phase * (self.width() + 240) - 120
            glow = QLinearGradient(center - 100, 0, center + 100, 0)
            glow.setColorAt(0, base)
            glow.setColorAt(0.5, QColor(self.theme.text))
            glow.setColorAt(1, base)
            painter.setPen(QPen(glow, 1))
        else:
            painter.setPen(base)
        text = self.fontMetrics().elidedText(
            self.text(), Qt.TextElideMode.ElideRight, max(0, self.width() - 12)
        )
        painter.drawText(
            self.rect().adjusted(6, 0, -6, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QColor(self.theme.accent))
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class AgentClock(QLabel):
    """Elapsed work time only; no fabricated token or reasoning progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        import time

        self.now = time.monotonic
        self.started = None
        self.active = False
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setProperty("role", "muted")
        self.setAccessibleName("Elapsed agent work time")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.setInterval(1000)
        self.hide()

    def reset(self):
        self.started = None
        self.active = False
        self.timer.stop()
        self.hide()

    def set_active(self, active):
        if active and self.started is None:
            self.started = self.now()
        self.active = active
        if active:
            self.timer.start()
            self.show()
        else:
            self.timer.stop()
            self.hide()
        self.refresh()

    def refresh(self):
        seconds = int(self.now() - self.started) if self.started is not None else 0
        self.setText(f"{seconds // 60}:{seconds % 60:02d}")
        self.setToolTip("Elapsed work time on this Mac")
