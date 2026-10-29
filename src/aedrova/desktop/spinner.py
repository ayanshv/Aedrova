"""Small native busy indicator; no timer runs while hidden or idle."""

from PySide6.QtCore import QEvent, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import QVBoxLayout, QWidget


class Spinner(QWidget):
    def __init__(self, parent=None, *, size=20):
        super().__init__(parent)
        self.setFixedSize(size, size)
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
        color = self.window().palette().color(QPalette.ColorRole.Text)
        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        track = QColor(color)
        track.setAlpha(35)
        painter.setPen(QPen(track, 2.5))
        painter.drawEllipse(rect)
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, -self.angle * 16, 260 * 16)


class CenteredSpinner(QWidget):
    """Cover only the content area, keeping one visible busy indicator at its center."""

    def __init__(self, target):
        super().__init__(target)
        self.setObjectName("ConnectorLoadingOverlay")
        self.setAccessibleName("Loading connectors")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAutoFillBackground(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        self.spinner = Spinner(self, size=34)
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        target.installEventFilter(self)
        self.setGeometry(target.rect())
        self.hide()

    def eventFilter(self, target, event):  # noqa: N802
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.setGeometry(target.rect())
        return super().eventFilter(target, event)

    def set_active(self, active):
        if active:
            self.setGeometry(self.parentWidget().rect())
            self.show()
            self.raise_()
        else:
            self.hide()
        self.spinner.set_active(active)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.window().palette().color(QPalette.ColorRole.Base))
