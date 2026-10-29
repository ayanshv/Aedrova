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
    if name == "spaces":
        for x in (4, 11):
            for y in (4, 11):
                p.drawRoundedRect(QRectF(x, y, 5, 5), 1, 1)
    elif name == "plus":
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
    elif name == "refresh":
        p.drawArc(QRectF(4, 4, 12, 12), 35 * 16, 300 * 16)
        p.drawLine(16, 3, 16, 8)
        p.drawLine(12, 8, 16, 8)
    elif name == "back":
        p.drawLine(16, 10, 4, 10)
        p.drawLine(9, 5, 4, 10)
        p.drawLine(9, 15, 4, 10)
    elif name == "logout":
        p.drawLine(9, 3, 3, 3)
        p.drawLine(3, 3, 3, 17)
        p.drawLine(3, 17, 9, 17)
        p.drawLine(8, 10, 18, 10)
        p.drawLine(14, 6, 18, 10)
        p.drawLine(14, 14, 18, 10)
    elif name == "folder":
        path = QPainterPath()
        path.moveTo(2, 6)
        path.lineTo(2, 16)
        path.quadTo(2, 17, 3, 17)
        path.lineTo(17, 17)
        path.quadTo(18, 17, 18, 16)
        path.lineTo(18, 6)
        path.lineTo(10, 6)
        path.lineTo(8, 3)
        path.lineTo(3, 3)
        path.quadTo(2, 3, 2, 4)
        path.closeSubpath()
        p.drawPath(path)
    elif name == "check":
        p.drawLine(4, 10, 8, 14)
        p.drawLine(8, 14, 16, 5)
    elif name == "link":
        p.drawRoundedRect(QRectF(2, 7, 9, 6), 3, 3)
        p.drawRoundedRect(QRectF(9, 7, 9, 6), 3, 3)
    elif name == "enter":
        p.drawLine(3, 10, 17, 10)
        p.drawLine(12, 5, 17, 10)
        p.drawLine(12, 15, 17, 10)
    elif name == "invite":
        p.drawEllipse(QRectF(4, 3, 6, 6))
        p.drawArc(QRectF(2, 10, 10, 12), 0, 180 * 16)
        p.drawLine(15, 8, 15, 14)
        p.drawLine(12, 11, 18, 11)
    elif name == "settings":
        for y, x in ((5, 7), (10, 13), (15, 8)):
            p.drawLine(3, y, x - 2, y)
            p.drawLine(x + 2, y, 17, y)
            p.drawEllipse(QRectF(x - 2, y - 2, 4, 4))
    elif name in {"archive", "restore"}:
        p.drawRoundedRect(QRectF(3, 4, 14, 4), 1, 1)
        path = QPainterPath()
        path.moveTo(4, 8)
        path.lineTo(4, 17)
        path.lineTo(16, 17)
        path.lineTo(16, 8)
        p.drawPath(path)
        if name == "archive":
            p.drawLine(8, 11, 12, 11)
        else:
            p.drawLine(10, 15, 10, 10)
            p.drawLine(7, 13, 10, 10)
            p.drawLine(13, 13, 10, 10)
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
    if not button.toolTip():
        button.setToolTip(
            button.accessibleName() or button.text() or name.replace("_", " ").title()
        )


def refresh(root, theme):
    for button in root.findChildren(QAbstractButton):
        name = button.property("iconName")
        if name:
            color = theme.primary_text if button.property("role") == "primary" else theme.secondary
            button.setIcon(icon(name, color))
