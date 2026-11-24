"""Draw the installer window background in Aedrova's light, quiet product style."""

import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, SCALE = 660, 400, 2
INK, MUTED, ACCENT = QColor("#1D1D1F"), QColor("#5B6475"), QColor("#2563FF")


def draw(target):
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)  # noqa: F841
    image = QImage(WIDTH * SCALE, HEIGHT * SCALE, QImage.Format.Format_ARGB32)
    image.setDevicePixelRatio(SCALE)
    painter = QPainter(image)
    painter.setRenderHints(
        QPainter.RenderHint.Antialiasing
        | QPainter.RenderHint.TextAntialiasing
        | QPainter.RenderHint.SmoothPixmapTransform
    )
    sky = QLinearGradient(0, 0, WIDTH, HEIGHT)
    sky.setColorAt(0, QColor("#EEF0FF"))
    sky.setColorAt(0.55, QColor("#F1EEF8"))
    sky.setColorAt(1, QColor("#FCF1EF"))
    painter.fillRect(QRectF(0, 0, WIDTH, HEIGHT), sky)
    glow = QRadialGradient(QPointF(WIDTH * 0.2, HEIGHT * 0.1), 320)
    glow.setColorAt(0, QColor(160, 175, 255, 70))
    glow.setColorAt(1, QColor(160, 175, 255, 0))
    painter.fillRect(QRectF(0, 0, WIDTH, HEIGHT), glow)

    svg = (ROOT / "src/aedrova/desktop/assets/aedrova-wordmark.svg").read_text()
    renderer = QSvgRenderer(QByteArray(svg.replace("currentColor", "#1D1D1F").encode()))
    mark_width = 128
    mark_height = mark_width * 80.48 / 380.5
    renderer.render(painter, QRectF((WIDTH - mark_width) / 2, 40, mark_width, mark_height))

    painter.setPen(INK)
    heading = QFont("Helvetica Neue", 20)
    heading.setWeight(QFont.Weight.DemiBold)
    painter.setFont(heading)
    painter.drawText(QRectF(0, 88, WIDTH, 32), Qt.AlignmentFlag.AlignCenter, "Install Aedrova")
    painter.setPen(MUTED)
    painter.setFont(QFont("Helvetica Neue", 13))
    painter.drawText(
        QRectF(0, 120, WIDTH, 22),
        Qt.AlignmentFlag.AlignCenter,
        "Drag Aedrova into Applications.",
    )

    # A soft arrow between the app and the Applications folder, centered on the icon row.
    y, left, right = 215, 262, 398
    painter.setPen(QPen(ACCENT, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(left, y), QPointF(right, y))
    head = QPainterPath()
    head.moveTo(right - 12, y - 11)
    head.lineTo(right, y)
    head.lineTo(right - 12, y + 11)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(head)

    painter.setPen(MUTED)
    painter.setFont(QFont("Helvetica Neue", 11))
    painter.drawText(
        QRectF(0, HEIGHT - 44, WIDTH, 20),
        Qt.AlignmentFlag.AlignCenter,
        "Then open Aedrova from Applications.",
    )
    painter.end()
    dots = int(144 / 0.0254)
    image.setDotsPerMeterX(dots)
    image.setDotsPerMeterY(dots)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(target), "PNG")


if __name__ == "__main__":
    draw(sys.argv[1])
