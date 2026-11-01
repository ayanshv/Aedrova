"""Finite, reduced-motion-aware polish without changing setup navigation semantics."""

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QStackedWidget


class OnboardingStack(QStackedWidget):
    """Keep page changes synchronous while crossfading the outgoing surface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.motion = None
        self.overlay = None

    def reduced(self):
        parent = self.parentWidget()
        while parent is not None:
            if getattr(parent, "reduced_motion", False) or getattr(parent, "reduced", False):
                return True
            parent = parent.parentWidget()
        return False

    def setCurrentIndex(self, index):  # noqa: N802
        if index == self.currentIndex():
            return
        if self.motion:
            self.motion.stop()
            self.motion.deleteLater()
            self.motion = None
        if self.overlay:
            self.overlay.deleteLater()
            self.overlay = None
        image = self.grab() if self.isVisible() and not self.reduced() else None
        super().setCurrentIndex(index)
        if image is None or image.isNull():
            return
        self.overlay = QLabel(self)
        self.overlay.setPixmap(image)
        self.overlay.setGeometry(self.rect())
        from PySide6.QtCore import Qt

        self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        effect = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(effect)
        self.overlay.show()
        self.overlay.raise_()
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setDuration(210)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.motion = QParallelAnimationGroup(self)
        self.motion.addAnimation(animation)
        overlay = self.overlay
        self.motion.finished.connect(overlay.deleteLater)
        self.motion.finished.connect(lambda: setattr(self, "overlay", None))
        self.motion.start()
