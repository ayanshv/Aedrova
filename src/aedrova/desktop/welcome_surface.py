"""Neutral, theme-aware canvas for native account onboarding."""

from PySide6.QtGui import QPainter, QPalette
from PySide6.QtWidgets import QWidget


class WelcomeSurface(QWidget):
    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().color(QPalette.ColorRole.Window))
