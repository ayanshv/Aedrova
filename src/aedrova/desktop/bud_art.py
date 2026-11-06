"""Reference-derived sculpted Bud sprites; shared by preview and living shelf."""

import math
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

LOOKS = ("builder", "designer", "marketing", "finance", "research", "product")
LABELS = ("Builder", "Designer", "Marketing", "Finance", "Research", "Product")

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


def smoothstep(low, high, value):
    t = max(0.0, min(1.0, (value - low) / (high - low)))
    return t * t * (3 - 2 * t)


@lru_cache(maxsize=1)
def atlas_image():
    return QImage(str(Path(__file__).parent / "assets/buds/reference-atlas.png"))


def tinted_body(tile, look, target, base):
    """Continuous tint at original resolution; no clipped shadow/highlight bands."""
    hue = base.hslHueF()
    base_light = base.lightnessF()
    target_hue = max(0.0, target.hslHueF())


    pivot = max(0.18, min(0.86, base_light + (target.lightnessF() - base_light) * 0.75))
    saturation_rate = -math.log1p(-target.hslSaturationF() * 0.92) / max(0.1, base.hslSaturationF())
    for y in range(tile.height()):
        for x in range(tile.width()):
            pixel = tile.pixelColor(x, y)
            if not pixel.alpha():
                continue
            h, saturation, light, alpha = pixel.getHslF()
            distance = (h - hue + 0.5) % 1.0 - 0.5
            strength = 1 - smoothstep(0.055, 0.12, abs(distance))
            strength *= smoothstep(0.035, 0.14, saturation) * smoothstep(0.12, 0.32, light)


            px, py = x * 512 / tile.width(), y * 512 / tile.height()
            if look == "builder":
                strength *= smoothstep(-2, 8, py - (270 - 0.14 * px))
            elif look == "designer" and px > 390 and py < 225:


                strength *= 1 - smoothstep(0.02, 0.045, abs(distance))
            elif look == "research":
                radius = math.hypot(px - 365, py - 174)
                strength *= smoothstep(76, 83, radius)
            if strength <= 0:
                continue
            shaded = (
                light / base_light * pivot
                if light <= base_light
                else pivot + (light - base_light) / (1 - base_light) * (1 - pivot)
            )
            tint = QColor.fromHslF(
                (target_hue + distance * 0.35) % 1.0,
                -math.expm1(-saturation_rate * saturation),
                shaded,
                alpha,
            )

            pixel.setRgbF(
                pixel.redF() + (tint.redF() - pixel.redF()) * strength,
                pixel.greenF() + (tint.greenF() - pixel.greenF()) * strength,
                pixel.blueF() + (tint.blueF() - pixel.blueF()) * strength,
                alpha,
            )
            tile.setPixelColor(x, y, pixel)
    return tile


@lru_cache(maxsize=32)
def sprite(look, color=""):
    if look == "research" and color.upper() in {"", "#4388F5", "#9CCCE6"}:
        color = "#70C8B7"
    atlas = atlas_image()
    if atlas.isNull():
        return QPixmap()
    index = LOOKS.index(look)
    width, height = atlas.width() // 3, atlas.height() // 2
    tile = atlas.copy((index % 3) * width, (index // 3) * height, width, height)
    if color and color.upper() not in {"#4388F5", BASE_COLORS[index].upper()}:
        target = QColor(color)
        if target.isValid():
            tile = tinted_body(tile, look, target, QColor(BASE_COLORS[index]))
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

    p.scale(breathing, breathing)
    p.translate(max(-1, min(1, look)) * rect.width() * 0.012, math.sin(phase) * 0.4)
    side = min(rect.width(), rect.height())
    p.drawPixmap(QRectF(-side / 2, -side / 2, side, side), pixmap, QRectF(pixmap.rect()))
    p.restore()
    return True



EYES = {
    "builder": ((257, 309, 35, 79), (349, 308, 34, 77)),
    "designer": ((222, 303, 36, 80), (322, 303, 36, 80)),
    "marketing": ((181, 289, 36, 80), (281, 289, 36, 80)),
    "finance": ((201, 246, 34, 73), (318, 244, 34, 74)),
    "research": ((175, 258, 35, 75), (267, 258, 35, 75)),
    "product": ((149, 269, 34, 70), (231, 269, 34, 71)),
}


@lru_cache(maxsize=32)
def blinking_sprite(look, color=""):
    """Close only the eyes using adjacent satin pixels and the original eye texture."""
    original = sprite(look, color)
    closed = original.copy()
    painter = QPainter(closed)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    sx, sy = closed.width() / 512, closed.height() / 512
    for x, y, width, height in EYES[look]:
        target = QRectF(x * sx, y * sy, width * sx, height * sy)

        painter.drawPixmap(target, original, QRectF((x - 9) * sx, y * sy, 4 * sx, height * sy))
        eye = QRectF(target.x(), target.center().y() - 2 * sy, target.width(), 4 * sy)
        painter.drawPixmap(eye, original, target)
    painter.end()
    return closed
