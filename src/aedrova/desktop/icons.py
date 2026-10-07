"""One compact native outline icon family. No emoji or font-dependent UI symbols."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QAbstractButton

SYMBOLS = {
    "+": "plus",
    "＋": "plus",
    "⌄": "chevron",
    "•••": "more",
    "Aa": "format",
    "×": "close",
    "☷": "sidebar",
    "◐": "appearance",
    "@": "mention",
    "☺": "smile",
    "↗": "arrow",
    "↑": "send",
}


def icon(name, color):
    pixmap = QPixmap(40, 40)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(2, 2)
    p.setPen(
        QPen(
            QColor(color),
            1.5,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    p.setBrush(Qt.BrushStyle.NoBrush)
    if name == "plus":
        p.drawLine(10, 4, 10, 16)
        p.drawLine(4, 10, 16, 10)
    elif name == "chevron":
        p.drawLine(5, 8, 10, 13)
        p.drawLine(10, 13, 15, 8)
    elif name == "more":
        for x in (5, 10, 15):
            p.drawPoint(x, 10)
    elif name == "format":
        p.drawLine(4, 16, 9, 4)
        p.drawLine(9, 4, 14, 16)
        p.drawLine(6, 12, 12, 12)
        p.drawLine(15, 9, 18, 9)
        p.drawLine(16, 9, 16, 16)
    elif name == "close":
        p.drawLine(5, 5, 15, 15)
        p.drawLine(15, 5, 5, 15)
    elif name == "sidebar":
        p.drawRoundedRect(QRectF(3, 4, 14, 12), 2, 2)
        p.drawLine(8, 4, 8, 16)
    elif name == "appearance":
        p.drawEllipse(QRectF(3, 3, 14, 14))
        path = QPainterPath()
        path.moveTo(10, 3)
        path.arcTo(3, 3, 14, 14, 90, 180)
        path.closeSubpath()
        p.fillPath(path, QColor(color))
    elif name == "search":
        p.drawEllipse(QRectF(3, 3, 10, 10))
        p.drawLine(12, 12, 17, 17)
    elif name == "mention":
        p.drawEllipse(QRectF(7, 7, 6, 6))
        p.drawArc(QRectF(3, 3, 14, 14), 45 * 16, 290 * 16)
        p.drawLine(13, 7, 13, 12)
        p.drawArc(QRectF(13, 9, 4, 5), 180 * 16, 180 * 16)
    elif name == "smile":
        p.drawEllipse(QRectF(3, 3, 14, 14))
        p.drawPoint(7, 8)
        p.drawPoint(13, 8)
        p.drawArc(QRectF(6, 7, 8, 7), 205 * 16, 130 * 16)
    elif name in {"arrow", "send"}:
        path = QPainterPath()
        path.moveTo(5, 14)
        path.lineTo(15, 4)
        path.moveTo(6, 4)
        path.lineTo(15, 4)
        path.lineTo(15, 13)
        p.drawPath(path)
    elif name == "work":
        p.drawRoundedRect(QRectF(3, 6, 14, 11), 2, 2)
        p.drawRoundedRect(QRectF(7, 3, 6, 4), 1, 1)
        p.drawLine(3, 10, 17, 10)
    elif name == "context":
        p.drawRoundedRect(QRectF(4, 3, 12, 14), 2, 2)
        for y in (7, 10, 13):
            p.drawLine(7, y, 13, y)
    elif name == "saved":
        path = QPainterPath()
        path.moveTo(5, 3)
        path.lineTo(15, 3)
        path.lineTo(15, 17)
        path.lineTo(10, 13)
        path.lineTo(5, 17)
        path.closeSubpath()
        p.drawPath(path)
    elif name == "activity":
        p.drawRoundedRect(QRectF(3, 4, 14, 12), 2, 2)
        p.drawLine(3, 11, 7, 11)
        p.drawLine(7, 11, 10, 14)
        p.drawLine(10, 14, 13, 11)
        p.drawLine(13, 11, 17, 11)
    p.end()
    return QIcon(pixmap)


def assign(button, name):
    button.setProperty("iconName", name)
    button.setIconSize(QSize(18, 18))
    button.setIcon(icon(name, button.palette().windowText().color().name()))


def refresh(root, theme):
    for button in root.findChildren(QAbstractButton):
        name = button.property("iconName")
        if name:
            color = theme.primary_text if button.property("role") == "primary" else theme.secondary
            button.setIcon(icon(name, color))
