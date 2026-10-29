"""Native onboarding visuals: minimal theme windows and illustrative setup diagrams."""

import math
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QWidget

from aedrova.desktop.materials import system_font
from aedrova.desktop.zen_theme import tone, visual_theme

BLUE = "#1478E8"


def glass_panel(painter, rect, theme, *, raised=False, radius=20):
    """Soft cool glass for illustrations only; product controls keep their own style."""
    dark = theme.name == "dark"
    painter.save()
    if raised:
        painter.setPen(Qt.PenStyle.NoPen)
        for spread in range(9, 0, -1):
            shadow = QColor("#000000" if dark else "#648CE3")
            shadow.setAlpha(3 if dark else 2)
            painter.setBrush(shadow)
            painter.drawRoundedRect(
                rect.adjusted(-spread, -spread + 5, spread, spread + 5),
                radius + spread,
                radius + spread,
            )
    fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
    colors = (
        ("#414141", "#303030", "#383838")
        if dark and raised
        else ("#303030", "#242424", "#2B2B2B")
        if dark
        else ("#FBFDFF", "#E8F0FF", "#DCEAFF")
        if raised
        else ("#F6FBFF", "#EDF4FF", "#EAF4FF")
    )
    for stop, color in zip((0, 0.5, 1), colors, strict=True):
        fill.setColorAt(stop, QColor(color))
    painter.setBrush(fill)
    painter.setPen(QPen(QColor("#5F5F5F" if dark else "#B6D6FF"), 0.8))
    painter.drawRoundedRect(rect, radius, radius)
    rim = QLinearGradient(rect.topLeft(), rect.bottomRight())
    rim.setColorAt(0, QColor(255, 255, 255, 85 if dark else 245))
    rim.setColorAt(0.45, QColor(255, 255, 255, 8 if dark else 50))
    rim.setColorAt(1, QColor(190, 190, 190, 65) if dark else QColor(145, 183, 255, 150))
    painter.setPen(QPen(rim, 1.2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius - 1, radius - 1)
    if raised:
        gleam = QPainterPath()
        gleam.moveTo(rect.left() + 5, rect.top() + 22)
        gleam.quadTo(rect.left() + 6, rect.top() + 5, rect.left() + 24, rect.top() + 5)
        painter.setPen(QPen(QColor(255, 255, 255, 90 if dark else 230), 1.6))
        painter.drawPath(gleam)
    painter.restore()


def setup_glyph(painter, rect, name, theme):
    """Resolution-independent outline symbols, without baked-in text or backgrounds."""
    painter.save()
    painter.translate(rect.left(), rect.top())
    painter.scale(rect.width() / 40, rect.height() / 40)
    painter.setPen(
        QPen(
            QColor(theme.accent_text),
            1.65,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    if name == "microphone":
        painter.drawRoundedRect(QRectF(15, 5, 10, 21), 5, 5)
        path.moveTo(10, 20)
        path.cubicTo(10, 35, 30, 35, 30, 20)
        path.moveTo(20, 32)
        path.lineTo(20, 37)
    elif name == "camera":
        path.moveTo(7, 11)
        path.lineTo(13, 11)
        path.lineTo(16, 7)
        path.lineTo(24, 7)
        path.lineTo(27, 11)
        path.lineTo(33, 11)
        path.quadTo(36, 11, 36, 15)
        path.lineTo(36, 31)
        path.quadTo(36, 34, 33, 34)
        path.lineTo(7, 34)
        path.quadTo(4, 34, 4, 31)
        path.lineTo(4, 15)
        path.quadTo(4, 11, 7, 11)
        painter.drawEllipse(QRectF(14, 16, 12, 12))
    elif name == "screen":
        painter.drawRoundedRect(QRectF(4, 8, 32, 23), 3, 3)
        painter.drawLine(12, 36, 28, 36)
    elif name == "check":
        path.moveTo(9, 21)
        path.lineTo(17, 29)
        path.lineTo(32, 12)
    elif name == "code":
        path.moveTo(13, 10)
        path.lineTo(5, 20)
        path.lineTo(13, 30)
        path.moveTo(27, 10)
        path.lineTo(35, 20)
        path.lineTo(27, 30)
        path.moveTo(23, 8)
        path.lineTo(17, 32)
    elif name == "branch":
        painter.drawEllipse(QRectF(7, 4, 7, 7))
        painter.drawEllipse(QRectF(26, 4, 7, 7))
        painter.drawEllipse(QRectF(7, 29, 7, 7))
        path.moveTo(10.5, 11)
        path.lineTo(10.5, 29)
        path.moveTo(29.5, 11)
        path.cubicTo(29.5, 22, 10.5, 16, 10.5, 27)
    elif name == "shield":
        path.moveTo(20, 4)
        path.lineTo(33, 9)
        path.lineTo(32, 24)
        path.quadTo(30, 31, 20, 37)
        path.quadTo(10, 31, 8, 24)
        path.lineTo(7, 9)
        path.closeSubpath()
    else:
        painter.drawRoundedRect(QRectF(9, 5, 23, 31), 4, 4)
        for y in (14, 21, 28):
            painter.drawLine(15, y, 26, y)
    painter.drawPath(path)
    painter.restore()


@lru_cache(maxsize=1)
def project_folder_image():
    image = QImage(str(Path(__file__).parent / "assets/onboarding/project-folder.png"))
    if image.isNull():
        raise RuntimeError("Project folder artwork is missing")
    return image


def caption(painter, rect, text, size=14, weight=None, color="#283A52"):
    from PySide6.QtGui import QFont

    painter.setFont(system_font(size, weight or QFont.Weight.Medium))
    painter.setPen(QColor(tone(visual_theme(painter.device()), color)))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, text)


class ThemePhoto(QAbstractButton):
    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(100, 150)
        self.setAccessibleName(
            "Choose "
            + {
                "system": "System appearance",
                "light": "Light appearance",
                "dark": "Dark appearance",
            }[mode]
        )

    def paintEvent(self, event):  # noqa: N802
        theme = visual_theme(self)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        frame = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        p.setPen(
            QPen(
                QColor(tone(theme, BLUE if self.isChecked() else "#DFE7F0")),
                2 if self.isChecked() else 1,
            )
        )
        p.setBrush(QColor(tone(theme, "#EDF5FF" if self.isChecked() else "white")))
        p.drawRoundedRect(frame, 18, 18)
        image_rect = frame.adjusted(8, 8, -8, -44)
        desktop = QRectF(
            image_rect.left() + image_rect.width() * 0.12,
            image_rect.top() + image_rect.height() * 0.17,
            image_rect.width() * 1.16,
            image_rect.height() * 1.08,
        )
        clip = QPainterPath()
        clip.addRoundedRect(image_rect, 10, 10)
        p.save()
        p.setClipPath(clip)
        for mode in ("light", "dark") if self.mode == "system" else (self.mode,):
            p.save()
            if self.mode == "system":
                half = QRectF(image_rect)
                half.setWidth(image_rect.width() / 2)
                if mode == "dark":
                    half.moveLeft(image_rect.center().x())
                p.setClipRect(half, Qt.ClipOperation.IntersectClip)
            light = mode == "light"
            p.setPen(QPen(QColor("#D5DAE2" if light else "#393939"), 1))
            p.setBrush(QColor("#EFF1F5" if light else "#171717"))
            p.drawRoundedRect(desktop, 12, 12)
            dot = 3.2
            p.setPen(Qt.PenStyle.NoPen)
            for index, color in enumerate(("#FF6058", "#FFBD2E", "#28C840")):
                p.setBrush(QColor(color))
                p.drawEllipse(
                    QRectF(
                        desktop.left() + 10 + index * 5.5,
                        desktop.top() + 9,
                        dot,
                        dot,
                    )
                )
            for x, y, size, fill in (
                (0.39, 0.22, 0.48, "#FAFBFD" if light else "#2B2B2B"),
                (0.15, 0.40, 0.56, "#FFFFFF" if light else "#424242"),
            ):
                window = QRectF(
                    desktop.left() + desktop.width() * x,
                    desktop.top() + desktop.height() * y,
                    desktop.height() * size,
                    desktop.height() * size,
                )
                p.setPen(QPen(QColor("#D2D7DF" if light else "#595959"), 1))
                p.setBrush(QColor(fill))
                p.drawRoundedRect(window, 7, 7)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor("#B9C0CB" if light else "#969EAA"))
                for index in range(3):
                    p.drawEllipse(
                        QRectF(
                            window.left() + 6 + index * 4,
                            window.top() + 6,
                            2,
                            2,
                        )
                    )
            p.restore()
        p.restore()
        caption(
            p,
            QRectF(frame.left() + 6, frame.bottom() - 36, frame.width() - 12, 28),
            {"system": "System", "light": "Light", "dark": "Dark"}[self.mode],
        )
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(tone(theme, BLUE)), 2))
            p.drawRoundedRect(frame.adjusted(2, 2, -2, -2), 16, 16)
        p.end()


class SetupVisual(QWidget):
    def __init__(self, flow, kind, *, detail="", enabled=None):
        super().__init__()
        self.flow, self.kind, self.detail, self.enabled = flow, kind, detail, enabled
        self.setMinimumHeight(226 if kind == "meeting" else 172)
        self.setAccessibleName(kind + " setup illustration")
        flow.timer.timeout.connect(self.update)

    def paintEvent(self, event):  # noqa: N802
        theme = visual_theme(self)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        glass_panel(p, QRectF(1, 1, w - 2, h - 2), theme)
        t = 0 if self.flow.reduced else self.flow.now() - self.flow.entered

        def tile(rect, text, blue=False, glyph=None):
            glass_panel(p, rect, theme, raised=True, radius=16)
            if glyph:
                setup_glyph(
                    p, QRectF(rect.center().x() - 13, rect.top() + 10, 26, 26), glyph, theme
                )
                caption(p, rect.adjusted(3, 38, -3, -4), text, 13)
            else:
                caption(p, rect, text, 14, color=BLUE if blue else "#283A52")

        if self.kind == "workflow":
            names = ("Context", "Plan", "Build copy", "Tests")
            gap = 12
            tw = (w - 48 - gap * 3) / 4
            on = self.enabled() if self.enabled else False
            for i, name in enumerate(names):
                rect = QRectF(24 + i * (tw + gap), 22, tw, 80)
                tile(rect, name, on, ("context", "plan", "code", "check")[i])
                if i < 3:
                    p.setPen(QPen(QColor(tone(theme, "#7EB7F1")), 2))
                    p.drawLine(rect.right() + 2, 64, rect.right() + gap - 2, 64)
            caption(p, QRectF(16, 110, w - 32, 38), "Apply changes & publish → your approval", 14)
            if on and not self.flow.reduced:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(tone(theme, BLUE)))
                p.drawEllipse(QRectF(24 + (w - 48) * ((t * 0.22) % 1) - 3, 25, 6, 6))
        elif self.kind == "profile":
            for i, (initial, y) in enumerate((("You", 32), ("Team", 45), ("Agent", 32))):
                x = w / 2 + (i - 1) * min(140, w / 3.3)
                glass_panel(p, QRectF(x - 29, y, 58, 58), theme, raised=True, radius=29)
                caption(p, QRectF(x - 29, y, 58, 58), initial, 15, color=BLUE)
            caption(p, QRectF(12, 113, w - 24, 36), "A familiar name. A familiar face.", 16)
        elif self.kind == "folder":
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.drawImage(QRectF(w / 2 - 90, 10, 180, 120), project_folder_image())
            # Native overlay stays crisp and follows the active appearance.
            cx, cy = w / 2 + 49, 103
            p.setPen(QPen(QColor(theme.border), 1))
            p.setBrush(QColor(theme.surface))
            p.drawEllipse(QRectF(cx - 11, cy - 11, 22, 22))
            p.setPen(
                QPen(QColor(theme.accent_text), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            p.drawLine(QRectF(cx - 4, cy, 8, 0).topLeft(), QRectF(cx - 4, cy, 8, 0).topRight())
            p.drawLine(QRectF(cx, cy - 4, 0, 8).topLeft(), QRectF(cx, cy - 4, 0, 8).bottomLeft())
            caption(p, QRectF(16, 121, w - 32, 32), self.detail or "Your project lives here", 16)
        elif self.kind == "repository":
            tile(QRectF(w * 0.12, 22, w * 0.3, 80), "Build copy", True, "code")
            tile(QRectF(w * 0.58, 22, w * 0.3, 80), "GitHub", True, "branch")
            p.setPen(QPen(QColor(tone(theme, "#70ABE9")), 2))
            p.drawLine(w * 0.43, 68, w * 0.57, 68)
            caption(p, QRectF(16, 115, w - 32, 35), "Review → approve → publish", 16)
        elif self.kind == "meeting":
            for i, name in enumerate(("Microphone", "Camera", "Screen")):
                gap, margin = 12, 24
                tw = (w - margin * 2 - gap * 2) / 3
                rect = QRectF(margin + i * (tw + gap), 25, tw, h - 96)
                glass_panel(p, rect, theme, raised=True, radius=24)
                setup_glyph(
                    p, QRectF(rect.center().x() - 18, rect.top() + 15, 36, 36), name.lower(), theme
                )
                caption(p, QRectF(rect.left() + 2, rect.top() + 57, rect.width() - 4, 28), name, 14)
                wave = QLinearGradient(0, rect.bottom() - 28, 0, rect.bottom() - 12)
                wave.setColorAt(0, QColor(theme.accent))
                wave.setColorAt(1, QColor(theme.accent_text))
                p.setPen(QPen(wave, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                for j in range(7):
                    d = 4 + abs(math.sin(t * 2 + i + j)) * 9
                    x, y = rect.center().x() + (j - 3) * 5, rect.bottom() - 21
                    p.drawLine(
                        QRectF(x, y - d / 2, 0, d).topLeft(),
                        QRectF(x, y - d / 2, 0, d).bottomLeft(),
                    )
            caption(p, QRectF(16, h - 49, w - 32, 32), "Check locally. Join when ready.", 15)
        elif self.kind == "review":
            for i, name in enumerate(("Your space", "Your project", "Your control")):
                tile(
                    QRectF(18 + i * (w - 36) / 3, 22, (w - 54) / 3, 80),
                    name,
                    True,
                    ("context", "code", "shield")[i],
                )
            caption(p, QRectF(16, 122, w - 32, 32), "Ready for your next shared idea.", 16)
        p.end()


class ProjectPicker(QAbstractButton):
    def __init__(self, flow, path):
        super().__init__()
        self.path = path
        self.setMinimumHeight(190)
        self.setAccessibleName("Choose a local project folder")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        from PySide6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.visual = SetupVisual(flow, "folder")
        self.visual.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.visual)
        path.textChanged.connect(self.refresh)
        self.refresh()

    def paintEvent(self, event):  # noqa: N802
        theme = visual_theme(self)
        surface = QColor(theme.text)
        surface.setAlpha(12)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(surface)
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 24, 24)
        painter.end()
        if self.hasFocus():
            theme = visual_theme(self)
            p = QPainter(self)
            p.setPen(QPen(QColor(tone(theme, BLUE)), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(2, 2, -2, -2), 20, 20)
            p.end()

    def refresh(self):
        self.visual.detail = (
            Path(self.path.text()).name if self.path.text().strip() else "Choose your project →"
        )
        self.visual.update()
