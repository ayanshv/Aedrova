"""The supplied Aedrova artwork, preserved intact and framed for native surfaces."""

import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Property, QByteArray, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPalette
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget

ASSETS = Path(__file__).parent / "assets"


WORDMARK = ASSETS / "aedrova-wordmark.svg"
WORDMARK_ASPECT = 380.5 / 74.48


@lru_cache(maxsize=16)
def wordmark_artwork(ink):
    svg = WORDMARK.read_text(encoding="utf-8").replace("currentColor", ink)
    return QSvgRenderer(QByteArray(svg.encode("utf-8")))


def paint_brand_wordmark(painter, bounds, color):
    wordmark_artwork(color.name()).render(painter, bounds)


def paint_brand_lockup(painter, center, mark_size, text_height, color):
    text_width = text_height * WORDMARK_ASPECT
    gap = mark_size * 0.2
    left = center.x() - (mark_size + gap + text_width) / 2
    paint_brand_mark(
        painter, QRectF(left, center.y() - mark_size / 2, mark_size, mark_size)
    )
    paint_brand_wordmark(
        painter,
        QRectF(left + mark_size + gap, center.y() - text_height / 2, text_width, text_height),
        color,
    )


class BrandWordmark(QWidget):
    def __init__(self, height):
        super().__init__()
        self.setFixedSize(round(height * WORDMARK_ASPECT), height)
        self.setAccessibleName("Aedrova")

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        color = self.palette().color(QPalette.ColorRole.WindowText)
        paint_brand_wordmark(painter, QRectF(self.rect()), color)


class BrandLockup(QWidget):
    def __init__(self, mark_size=32, text_height=18):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(round(mark_size * 0.2))
        mark = BrandMark(mark_size)
        mark.setAccessibleName("")
        layout.addWidget(mark, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(BrandWordmark(text_height), alignment=Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(layout.sizeHint())


@lru_cache(maxsize=1)
def brand_image():
    image = QImage(str(ASSETS / "aedrova.png"))
    if image.isNull():
        raise RuntimeError("Aedrova brand artwork is missing")


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


    resources = Path(sys.executable).parent.parent / "Resources"
    if (
        sys.platform == "darwin"
        and resources.parent.name == "Contents"
        and (resources / "Assets.car").is_file()
    ):
        return QIcon()
    return QIcon(str(ASSETS / ("aedrova.ico" if sys.platform == "win32" else "aedrova.icns")))


def paint_brand_mark(painter, rect, *, lift=0.0):
    image = brand_image()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    area = rect.adjusted(3, 3, -3, -3)
    size = image.size().scaled(area.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
    target = QRectF(0, 0, size.width(), size.height())
    target.moveCenter(area.center())
    target.translate(0, -1.5 * lift)
    painter.drawImage(target, image)
    painter.restore()


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
        painter = QPainter(self)
        paint_brand_mark(painter, QRectF(self.rect()), lift=self._lift)
