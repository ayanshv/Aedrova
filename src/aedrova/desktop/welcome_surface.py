"""Quiet, theme-aware ambient canvas for native account onboarding."""

from PySide6.QtGui import QColor, QPainter, QPalette, QRadialGradient
from PySide6.QtWidgets import QWidget


class WelcomeSurface(QWidget):
    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        base = self.palette().color(QPalette.ColorRole.Window)
        p.fillRect(self.rect(), base)
        dark = base.lightness() < 100
        for x, color in ((0.3, "#70B5F6"), (0.75, "#92B6FA")):
            glow = QRadialGradient(self.width() * x, self.height() * 0.08, self.width() * 0.55)
            c = QColor(color)
            c.setAlpha(16 if dark else 34)
            glow.setColorAt(0, c)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.fillRect(self.rect(), glow)
