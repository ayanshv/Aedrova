"""Finite Aedrova context composition for the original welcome screen."""

import time

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from aedrova.desktop.brand import brand_image
from aedrova.desktop.bud_art import paint_bud
from aedrova.desktop.icons import icon
from aedrova.desktop.materials import system_font


def ease(value):
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


class OpeningScene(QWidget):
    """A short convergence sequence, then a quiet still composition."""

    def __init__(self, flow):
        super().__init__(flow)
        self.flow = flow
        self.started = time.monotonic()
        self.setMinimumSize(0, 210)
        self.setAccessibleName(
            "Conversations, projects and meetings converge around Aedrova and Buds"
        )
        self.timer = QTimer(self)
        self.timer.setInterval(24)
        self.timer.timeout.connect(self.tick)

    def showEvent(self, event):  # noqa: N802
        self.started = time.monotonic()
        if not self.flow.reduced:
            self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def tick(self):
        self.update()
        if time.monotonic() - self.started > 4:
            self.timer.stop()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        t = self.flow.theme
        p.fillRect(self.rect(), QColor(t.bg))
        scale = min(self.width() / 740, self.height() / 350)
        p.translate(self.width() / 2, self.height() / 2)
        p.scale(scale, scale)
        elapsed = time.monotonic() - self.started
        progress = 1 if self.flow.reduced else ease(elapsed / 2.6)
        # Real neutral material and soft offsets replace continuous blur effects.
        area = QRectF(-208, -126, 416, 252)
        for offset, alpha in ((18, 3), (10, 6), (4, 10)):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, alpha if t.name == "light" else alpha // 2))
            p.drawRoundedRect(area.translated(0, offset), 26, 26)
        gradient = QLinearGradient(area.topLeft(), area.bottomRight())
        gradient.setColorAt(0, QColor(t.elevated))
        gradient.setColorAt(1, QColor(t.surface))
        p.setBrush(gradient)
        p.setPen(QPen(QColor(t.border), 1))
        p.drawRoundedRect(area, 24, 24)
        p.setPen(QColor(t.muted))
        p.setFont(system_font(11, QFont.Weight.Medium))
        p.drawText(QRectF(-176, -106, 320, 24), "YOUR SPACE")
        for i, (name, glyph) in enumerate(
            (("Conversations", "mention"), ("Projects", "folder"), ("Meetings", "camera"))
        ):
            reveal = 1 if self.flow.reduced else ease((elapsed - 0.18 * i) / 1.8)
            x = (-280, 206, -260)[i] + (40 if i != 1 else -40) * reveal
            y = (-72, -28, 68)[i] + 22 * (1 - progress)
            tile = QRectF(x, y, 152, 50)
            p.setOpacity(reveal)
            p.setPen(QPen(QColor(t.border), 1))
            p.setBrush(QColor(t.elevated))
            p.drawRoundedRect(tile, 12, 12)
            pix = icon(glyph, t.accent).pixmap(19, 19)
            p.drawPixmap(int(x + 14), int(y + 15), pix)
            p.setFont(system_font(11, QFont.Weight.Medium))
            p.setPen(QColor(t.text))
            p.drawText(tile.adjusted(42, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, name)
        p.setOpacity(1 if self.flow.reduced else ease(elapsed / 0.9))
        side = 88 + 14 * progress
        p.drawImage(QRectF(-side / 2, -side / 2 - 20, side, side), brand_image())
        p.setFont(system_font(13, QFont.Weight.DemiBold))
        p.setPen(QColor(t.text))
        p.drawText(QRectF(-90, 44, 180, 26), Qt.AlignmentFlag.AlignCenter, "Aedrova")
        for i, role in enumerate(("builder", "research", "product")):
            p.setOpacity(1 if self.flow.reduced else ease((elapsed - 0.8 - i * 0.15) / 1.1))
            paint_bud(p, QRectF(-108 + i * 76, 84, 64, 64), {"appearance": role}, phase=0)
        p.end()
