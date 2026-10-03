"""Small monochrome meeting symbols drawn at native display resolution."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPainterPath, QPen, QPixmap


def meeting_icon(kind, color, *, off=False):
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(2, 2)
    painter.setPen(QPen(color, 1.6, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    if kind == 'microphone':
        painter.drawRoundedRect(QRectF(9, 3, 6, 12), 3, 3)
        painter.drawArc(QRectF(6, 6, 12, 12), 180 * 16, 180 * 16)
        painter.drawLine(12, 18, 12, 21)
        painter.drawLine(8, 21, 16, 21)
    elif kind == 'camera':
        painter.drawRoundedRect(QRectF(3, 6, 12, 12), 2, 2)
        path = QPainterPath()
        path.moveTo(15, 10)
        path.lineTo(21, 6)
        path.lineTo(21, 18)
        path.lineTo(15, 14)
        painter.drawPath(path)
    elif kind == 'screen':
        painter.drawRoundedRect(QRectF(3, 4, 18, 13), 2, 2)
        painter.drawLine(12, 17, 12, 21)
        painter.drawLine(8, 21, 16, 21)
        painter.drawLine(12, 13, 12, 7)
        painter.drawLine(9, 10, 12, 7)
        painter.drawLine(15, 10, 12, 7)
    elif kind == 'participants':
        painter.drawEllipse(QRectF(8, 3, 7, 7))
        painter.drawArc(QRectF(5, 12, 13, 12), 0, 180 * 16)
        painter.drawArc(QRectF(16, 5, 5, 5), -90 * 16, 180 * 16)
        painter.drawArc(QRectF(16, 12, 6, 10), 0, 90 * 16)
    elif kind == 'settings':
        for x in (5, 12, 19):
            painter.drawEllipse(QRectF(x - 1, 11, 2, 2))
    else:
        painter.drawLine(4, 12, 20, 12)
        painter.drawLine(16, 8, 20, 12)
        painter.drawLine(16, 16, 20, 12)
    if off and kind in {'microphone', 'camera'}:
        painter.drawLine(3, 3, 21, 21)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)
