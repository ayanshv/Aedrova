"""A persistent, quiet listening/permission capsule with actual audio-level feedback."""

import math

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.dialogs import icon_button
from aedrova.desktop.popup_depth import paint_depth


class AudioPulse(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.level = self.target = 0.0
        self.pending = True
        self.phase = 0
        self.setFixedSize(30, 28)
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.setAccessibleName("Waiting for audio permission")

    def tick(self):
        self.phase = (self.phase + 12) % 360
        self.level += (self.target - self.level) * 0.3
        self.target *= 0.9
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(
            QPen(self.palette().text().color(), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        if self.pending:
            painter.drawArc(QRectF(7, 6, 16, 16), self.phase * 16, 240 * 16)
            return
        for index, weight in enumerate((0.35, 0.7, 1.0, 0.6, 0.35)):
            height = 3 + 19 * min(1, math.sqrt(max(0, self.level)) * 3) * weight
            x = 5 + index * 5
            painter.drawLine(int(x), int(14 - height / 2), int(x), int(14 + height / 2))


class ListeningCapsule(QWidget):
    stop_requested = Signal()
    review_requested = Signal()

    def __init__(self, owner):
        super().__init__(
            owner,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle("Aedrova meeting notes")
        self.setFixedSize(344, 104)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(34, 20, 32, 28)
        layout.setSpacing(10)
        layout.addWidget(BrandMark(24))
        self.pulse = AudioPulse(self)
        layout.addWidget(self.pulse)
        self.caption = QLabel("Allow audio access")
        self.caption.setStyleSheet("background:transparent;font-size:12px;font-weight:500;")
        layout.addWidget(self.caption, 1)
        self.review = icon_button("context", "Open meeting notes")
        self.review.setFixedSize(28, 28)
        self.review.clicked.connect(self.review_requested)
        layout.addWidget(self.review)
        self.stop = icon_button("stop", "Stop listening")
        self.stop.setFixedSize(28, 28)
        self.stop.clicked.connect(self.stop_requested)
        layout.addWidget(self.stop)

    def set_state(self, caption, *, listening=False):
        self.caption.setText(caption)
        self.pulse.pending = not listening
        self.pulse.setAccessibleName(
            "Audio input level" if listening else "Waiting for audio permission"
        )
        self.setAccessibleName("Aedrova meeting notes: " + caption)
        self.update()

    def show_on_side(self):
        owner = self.parentWidget()
        theme = getattr(owner, "theme", None)
        if theme:
            self.caption.setStyleSheet(
                f"background:transparent;color:{theme.text};font-size:12px;font-weight:500;"
            )
        screen = owner.screen().availableGeometry()
        self.move(screen.right() - self.width() - 12, screen.bottom() - self.height() - 28)
        self.show()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        paint_depth(painter, self.rect(), self)

    def showEvent(self, event):  # noqa: N802
        self.pulse.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):  # noqa: N802
        self.pulse.timer.stop()
        super().hideEvent(event)
