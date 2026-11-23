"""The Slack mark, drawn from the bundled vector so it stays sharp at any size."""

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

LOGO = Path(__file__).parent / "assets" / "slack-logo.svg"


@lru_cache(maxsize=1)
def renderer():
    return QSvgRenderer(str(LOGO))


def paint_logo(painter, rect):
    renderer().render(painter, QRectF(rect))


@lru_cache(maxsize=8)
def slack_pixmap(size, ratio=2):
    image = QImage(size * ratio, size * ratio, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    paint_logo(painter, QRectF(0, 0, size * ratio, size * ratio))
    painter.end()
    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(ratio)
    return pixmap


def slack_icon(size=20):
    return QIcon(slack_pixmap(size))
