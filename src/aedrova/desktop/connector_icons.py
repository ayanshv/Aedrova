"""Offline brand marks for the Bud connector gallery."""

from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

COLORS = {
    "github": "#181717",
    "supabase": "#3ECF8E",
    "figma": "#F24E1E",
    "notion": "#000000",
    "stripe": "#635BFF",
    "instagram": "#E4405F",
    "tiktok": "#000000",
    "search": "#FB542B",
    "vercel": "#000000",
}
ASSETS = Path(__file__).parent / "assets" / "connectors"


def connector_pixmap(provider, size=36):
    """Keep brand marks readable on both themes without network requests."""
    color = COLORS.get(provider)
    if color is None:
        return QPixmap()
    try:
        svg = (ASSETS / f"{provider}.svg").read_bytes()
    except OSError:
        return QPixmap()
    svg = svg.replace(b"<path ", f'<path fill="{color}" '.encode(), 1)
    renderer = QSvgRenderer(QByteArray(svg))
    if not renderer.isValid():
        return QPixmap()
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(QRectF(0, 0, size, size), 8, 8)
    renderer.render(painter, QRectF(7, 7, size - 14, size - 14))
    painter.end()
    return pixmap
