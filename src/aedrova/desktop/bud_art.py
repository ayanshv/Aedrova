"""Reference-derived sculpted Bud sprites; shared by preview and living shelf."""

import math
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

LOOKS = ("builder", "designer", "marketing", "finance", "research", "product")
LABELS = ("Builder", "Designer", "Marketing", "Finance", "Research", "Product")
# Atlas cell coordinates, not generated UI or remote assets.
BASE_COLORS = ("#9BC8ED", "#BAA1EA", "#F4CD68", "#BAD28B", "#9CCCE6", "#F3B59E")


def appearance(config):
    chosen = config.get("appearance", "auto")
    if chosen in LOOKS:
        return chosen
    purpose = (str(config.get("role", "")) + " " + str(config.get("name", ""))).lower()
    for key, words in {
        "designer": ("design", "creative", "artist"),
        "marketing": ("market", "sales", "growth"),
        "finance": ("financ", "revenue", "account", "billing"),
        "research": ("research", "analyst", "insight"),
        "product": ("product", "strategy", "roadmap"),
    }.items():
        if any(word in purpose for word in words):
            return key
    return {"squircle": "designer", "cloud": "marketing"}.get(config.get("shape"), "builder")


@lru_cache(maxsize=48)
def sprite(look, color=""):
    atlas = QImage(str(Path(__file__).parent / "assets/buds/reference-atlas.png"))
    if atlas.isNull():
        return QPixmap()
    index = LOOKS.index(look)
    width, height = atlas.width() // 3, atlas.height() // 2
    tile = atlas.copy((index % 3) * width, (index // 3) * height, width, height)
    # Tint only the body hues, retaining eyes, accessories and sculpted luminance.
    # Process a bounded 160px preview once per cached color, never per animation frame.
    if color and color.upper() not in {"#4388F5", BASE_COLORS[index].upper()}:
        tile = tile.scaled(
            160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        target = QColor(color)
        base = QColor(BASE_COLORS[index])
        if target.isValid():
            for y in range(tile.height()):
                for x in range(tile.width()):
                    pixel = tile.pixelColor(x, y)
                    h, s, lightness, a = pixel.getHslF()
                    distance = abs(h - base.hslHueF())
                    if (
                        a > 0
                        and lightness > 0.30
                        and s > 0.12
                        and min(distance, 1 - distance) < 0.10
                    ):
                        # Hue adjustment preserves highlights and satin depth.
                        pixel.setHslF(
                            max(0, target.hslHueF()),
                            min(1, s * target.hslSaturationF() / max(0.1, base.hslSaturationF())),
                            min(
                                0.97,
                                max(
                                    0.12,
                                    lightness + (target.lightnessF() - base.lightnessF()) * 0.65,
                                ),
                            ),
                            a,
                        )
                        tile.setPixelColor(x, y, pixel)
    return QPixmap.fromImage(tile)


def paint_bud(p, rect, config, *, phase=0, blink=False, look=0, rotation=0):
    pixmap = sprite(appearance(config), str(config.get("color", "#4388F5")))
    if pixmap.isNull():
        return False
    p.save()
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.translate(rect.center())
    p.rotate(rotation)
    breathing = 1 + math.sin(phase * 1.7) * 0.015
    # A single organic squint preserves the exact rendered eye geometry.
    p.scale(breathing, breathing * (0.97 if blink else 1))
    p.translate(max(-1, min(1, look)) * rect.width() * 0.012, math.sin(phase) * 0.4)
    side = min(rect.width(), rect.height())
    p.drawPixmap(QRectF(-side / 2, -side / 2, side, side), pixmap, QRectF(pixmap.rect()))
    p.restore()
    return True
