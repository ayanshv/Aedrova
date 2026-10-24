"""Small native busy indicator; no timer runs while hidden or idle."""

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget


class Spinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setAccessibleName("Loading connectors")
        self.active = False
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.advance)
        self.hide()

    def set_active(self, active):
        self.active = bool(active)
        self.setVisible(self.active)
        self.sync()

    def sync(self):
        if self.active and self.isVisible():
            self.timer.start()
        else:
            self.timer.stop()

    def advance(self):
        self.angle = (self.angle + 18) % 360
        self.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.sync()

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.palette().highlight().color(), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(QRectF(3, 3, 14, 14), -self.angle * 16, 260 * 16)
