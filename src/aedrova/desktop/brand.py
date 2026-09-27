"""The supplied Aedrova artwork, preserved intact and framed for native surfaces."""

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QIcon, QImage, QPainter
from PySide6.QtWidgets import QApplication, QWidget

ASSETS = Path(__file__).parent / "assets"


@lru_cache(maxsize=1)
def brand_image():
    image = QImage(str(ASSETS / "aedrova.png"))
    if image.isNull():
        raise RuntimeError("Aedrova brand artwork is missing")
    # Frame the visible mark, excluding near-transparent export noise.
    # Keep the original asset intact and leave room around its soft halo.
    points = [
        (x, y)
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() > 8
    ]
    left, right = min(x for x, _ in points), max(x for x, _ in points)
    top, bottom = min(y for _, y in points), max(y for _, y in points)
    return image.copy(left - 28, top - 28, right - left + 57, bottom - top + 57)


def app_icon():
    return QIcon(str(ASSETS / "aedrova.icns"))


class BrandMark(QWidget):
    """A quiet mark that lifts on hover; it never implies an active agent."""

    def __init__(self, size=40):
        super().__init__()
        self.setFixedSize(size, size)
        self.setAccessibleName("Aedrova brand mark")
        self.setToolTip("Aedrova · Where teams and AI build together")
        self.reduced_motion = bool(QApplication.instance().property("reduceMotion"))
        self._lift = 0.0
        self.animation = QPropertyAnimation(self, b"lift", self)
        self.animation.setDuration(650)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)

    def get_lift(self):
        return self._lift

    def set_lift(self, value):
        self._lift = value
        self.update()

    lift = Property(float, get_lift, set_lift)

    def set_reduced_motion(self, reduced):
        self.reduced_motion = reduced
        if reduced:
            self.animation.stop()
            self.set_lift(0.0)

    def animate(self, target):
        if self.reduced_motion:
            return
        self.animation.stop()
        self.animation.setStartValue(self._lift)
        self.animation.setEndValue(target)
        self.animation.start()

    def enterEvent(self, event):  # noqa: N802
        self.animate(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):  # noqa: N802
        self.animate(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):  # noqa: N802
        image = brand_image()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        area = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        size = image.size().scaled(area.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF(0, 0, size.width(), size.height())
        target.moveCenter(area.center())
        target.translate(0, -1.5 * self._lift)
        painter.drawImage(target, image)
