"""Content-shaped loading placeholders; no extra windows or focus changes."""

import time

from PySide6.QtCore import QEvent, QRectF, Qt, QTimer
from PySide6.QtGui import QLinearGradient, QPainter, QPalette
from PySide6.QtWidgets import QWidget


class Skeleton(QWidget):
    def __init__(self, target, kind="form"):
        super().__init__(target)
        self.kind = kind
        self.setObjectName("LoadingSkeleton")
        self.setAccessibleName("Loading content")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.update)
        target.installEventFilter(self)
        self.setGeometry(target.rect())
        self.hide()

    def eventFilter(self, target, event):  # noqa: N802
        if event.type() == QEvent.Type.Resize:
            self.setGeometry(target.rect())
        return super().eventFilter(target, event)

    def reduced_motion(self):
        parent = self.parentWidget()
        while parent is not None:
            if getattr(parent, "reduced_motion", False):
                return True
            parent = parent.parentWidget()
        return False

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if not self.reduced_motion():
            self.timer.start()

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Stylesheet-polished intermediate containers can inherit the platform's
        # default Base color. Resolve the window palette, which owns the theme.
        colors = self.window().palette()
        parent = self.parentWidget()
        while parent is not None:
            theme = getattr(parent, "theme", None)
            if theme is not None:
                from aedrova.desktop.theme import palette

                colors = palette(theme)
                break
            parent = parent.parentWidget()
        painter.fillRect(self.rect(), colors.color(QPalette.ColorRole.Base))
        painter.setPen(Qt.PenStyle.NoPen)
        base = colors.color(QPalette.ColorRole.AlternateBase)
        highlight = colors.color(QPalette.ColorRole.Midlight)
        highlight.setAlpha(75)
        brush = base
        if not self.reduced_motion():
            offset = (time.monotonic() % 2.4) / 2.4 * (self.width() + 240) - 240
            gradient = QLinearGradient(offset, 0, offset + 240, 0)
            gradient.setColorAt(0, base)
            gradient.setColorAt(0.5, highlight)
            gradient.setColorAt(1, base)
            brush = gradient
        painter.setBrush(brush)
        width = max(0, self.width() - 48)

        def bar(x, y, w, h=12, radius=6):
            painter.drawRoundedRect(QRectF(x, y, max(0, w), h), radius, radius)

        if self.kind == "gallery":
            bar(24, 28, width * 0.4, 24)
            bar(24, 70, width * 0.65)
            columns = max(1, min(3, int((width + 16) / 200)))
            cell = max(0, (width - (columns - 1) * 16) / columns)
            for index in range(9):
                x = 24 + (index % columns) * (cell + 16)
                y = 110 + (index // columns) * 154
                if y > self.height():
                    break
                bar(x, y, cell, 138, 12)
        elif self.kind == "feed":
            for index in range(max(1, self.height() // 92)):
                y = 24 + index * 92
                bar(24, y, 34, 34, 17)
                bar(72, y + 2, width * 0.22)
                bar(72, y + 25, max(0, width - 65) * (0.85 if index % 2 else 1))
                bar(72, y + 48, width * 0.48)
        else:
            form_width = min(480, width)
            x = max(24, (self.width() - form_width) / 2)
            bar(x, 32, form_width * 0.62, 26)
            bar(x, 78, form_width * 0.9)
            for index in range(4):
                y = 126 + index * 86
                if y > self.height():
                    break
                bar(x, y, form_width * 0.28)
                bar(x, y + 24, form_width, 40, 10)
        painter.end()


def set_loading(owner, target, active, kind="form"):
    skeleton = getattr(owner, "_loading_skeleton", None)
    if skeleton is None:
        if not active:
            return
        skeleton = Skeleton(target, kind)
        owner._loading_skeleton = skeleton
    skeleton.kind = kind
    if active:
        skeleton.setGeometry(target.rect())
        skeleton.show()
        skeleton.raise_()
    else:
        skeleton.hide()
    status = getattr(owner, "status", None)
    if status is not None:
        status.setVisible(not active)
