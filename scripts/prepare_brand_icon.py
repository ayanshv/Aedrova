"""Frame the original transparent logo for the macOS Dock; requires iconutil."""

import subprocess
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter

from aedrova.desktop.brand import ASSETS, brand_image

ROOT = Path(__file__).resolve().parents[1]
iconset = ROOT / "work" / "Aedrova.iconset"
iconset.mkdir(parents=True, exist_ok=True)
image = QImage(1024, 1024, QImage.Format.Format_ARGB32_Premultiplied)
image.fill(Qt.GlobalColor.transparent)
painter = QPainter(image)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QColor("#1C1C1E"))
painter.drawRoundedRect(QRectF(40, 40, 944, 944), 212, 212)
logo = brand_image()
size = logo.size().scaled(780, 780, Qt.AspectRatioMode.KeepAspectRatio)
rect = QRectF(0, 0, size.width(), size.height())
rect.moveCenter(QRectF(0, 0, 1024, 1024).center())
painter.drawImage(rect, logo)
painter.end()
for logical in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        pixels = logical * scale
        suffix = "@2x" if scale == 2 else ""
        target = iconset / f"icon_{logical}x{logical}{suffix}.png"
        if not image.scaled(
            pixels,
            pixels,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ).save(str(target)):
            raise RuntimeError(f"Could not save {target}")
subprocess.run(
    ["iconutil", "-c", "icns", str(iconset), "-o", str(ASSETS / "aedrova.icns")], check=True
)
