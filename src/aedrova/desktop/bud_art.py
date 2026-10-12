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


def original_color(config):
    """The visible original body color, including Research's distinct mint tint."""
    look = appearance(config)
    return "#70C8B7" if look == "research" else BASE_COLORS[LOOKS.index(look)]


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
    if look == "research" and color.upper() in {"", "#4388F5", "#9CCCE6"}:
        color = "#70C8B7"
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
    pixmap = (blinking_sprite if blink else sprite)(
        appearance(config), str(config.get("color", "#4388F5"))
    )
    if pixmap.isNull():
        return False
    p.save()
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.translate(rect.center())
    p.rotate(rotation)
    breathing = 1 + math.sin(phase * 1.7) * 0.015
    # A single organic squint preserves the exact rendered eye geometry.
    p.scale(breathing, breathing)
    p.translate(max(-1, min(1, look)) * rect.width() * 0.012, math.sin(phase) * 0.4)
    side = min(rect.width(), rect.height())
    p.drawPixmap(QRectF(-side / 2, -side / 2, side, side), pixmap, QRectF(pixmap.rect()))
    p.restore()
    return True


# Eye rectangles in the original 512px atlas cells. Accessories stay untouched.
EYES = {
    "builder": ((257, 309, 35, 79), (349, 308, 34, 77)),
    "designer": ((222, 303, 36, 80), (322, 303, 36, 80)),
    "marketing": ((181, 289, 36, 80), (281, 289, 36, 80)),
    "finance": ((201, 246, 34, 73), (318, 244, 34, 74)),
    "research": ((175, 258, 35, 75), (267, 258, 35, 75)),
    "product": ((149, 269, 34, 70), (231, 269, 34, 71)),
}


@lru_cache(maxsize=48)
def blinking_sprite(look, color=""):
    """Close only the eyes using adjacent satin pixels and the original eye texture."""
    original = sprite(look, color)
    closed = original.copy()
    painter = QPainter(closed)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    sx, sy = closed.width() / 512, closed.height() / 512
    for x, y, width, height in EYES[look]:
        target = QRectF(x * sx, y * sy, width * sx, height * sy)
        # A nearby clean face strip preserves the artwork's illumination and tint.
        painter.drawPixmap(target, original, QRectF((x - 9) * sx, y * sy, 4 * sx, height * sy))
        eye = QRectF(target.x(), target.center().y() - 2 * sy, target.width(), 4 * sy)
        painter.drawPixmap(eye, original, target)
    painter.end()
    return closed
