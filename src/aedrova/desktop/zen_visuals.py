"""Native onboarding visuals: real theme captures and clearly illustrative setup diagrams."""

import math
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QAbstractButton, QWidget

from aedrova.desktop.brand import ASSETS
from aedrova.desktop.materials import system_font
from aedrova.desktop.zen_theme import tone, visual_theme

BLUE = "#1478E8"


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
        self.photos = {
            m: QPixmap(str(ASSETS / "onboarding" / f"{m}.png")) for m in ("light", "dark")
        }

    def paintEvent(self, event):  # noqa: N802
        theme = visual_theme(self)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
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
        clip = QPainterPath()
        clip.addRoundedRect(image_rect, 10, 10)
        p.save()
        p.setClipPath(clip)
        for mode in ("light", "dark") if self.mode == "system" else (self.mode,):
            photo = self.photos[mode]
            p.save()
            if self.mode == "system":
                half = QRectF(image_rect)
                half.setWidth(image_rect.width() / 2)
                if mode == "dark":
                    half.moveLeft(image_rect.center().x())
                p.setClipRect(half, Qt.ClipOperation.IntersectClip)
            if photo.isNull():
                p.fillRect(image_rect, QColor("#F5F5F7" if mode == "light" else "#1C1C1E"))
            else:
                p.drawPixmap(image_rect.toRect(), photo)
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
        self.setMinimumHeight(172)
        self.setAccessibleName(kind + " setup illustration")
        flow.timer.timeout.connect(self.update)

    def paintEvent(self, event):  # noqa: N802
        theme = visual_theme(self)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(QPen(QColor(tone(theme, "#D8E9FB")), 1))
        p.setBrush(QColor(tone(theme, "#F2F8FF")))
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 20, 20)
        t = 0 if self.flow.reduced else self.flow.now() - self.flow.entered

        def tile(rect, text, blue=False):
            p.setPen(QPen(QColor(tone(theme, "#B5D5FA" if blue else "#DEE7F0")), 1))
            p.setBrush(QColor(tone(theme, "#E0EFFF" if blue else "#FFFFFF")))
            p.drawRoundedRect(rect, 14, 14)
            caption(p, rect, text, 14, color=BLUE if blue else "#283A52")

        if self.kind == "workflow":
            names = ("Context", "Plan", "Build copy", "Tests")
            gap = 12
            tw = (w - 48 - gap * 3) / 4
            on = self.enabled() if self.enabled else False
            for i, name in enumerate(names):
                rect = QRectF(24 + i * (tw + gap), 34, tw, 60)
                tile(rect, name, on)
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
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(tone(theme, ("#DCEFFF", "#E8E4FB", "#DFEFFF")[i])))
                p.drawEllipse(QRectF(x - 29, y, 58, 58))
                caption(p, QRectF(x - 29, y, 58, 58), initial, 15, color=BLUE)
            caption(p, QRectF(12, 113, w - 24, 36), "A familiar name. A familiar face.", 16)
        elif self.kind == "folder":
            x = w / 2 - 50
            path = QPainterPath()
            path.moveTo(x, 35)
            path.lineTo(x + 38, 35)
            path.lineTo(x + 48, 48)
            path.lineTo(x + 100, 48)
            path.lineTo(x + 100, 112)
            path.lineTo(x, 112)
            path.closeSubpath()
            p.setPen(QPen(QColor(tone(theme, "#8DBCF0")), 1))
            p.setBrush(QColor(tone(theme, "#CBE5FF")))
            p.drawPath(path)
            caption(p, QRectF(16, 121, w - 32, 32), self.detail or "Your project lives here", 16)
        elif self.kind == "repository":
            tile(QRectF(w * 0.12, 35, w * 0.3, 65), "Build copy", True)
            tile(QRectF(w * 0.58, 35, w * 0.3, 65), "GitHub", True)
            p.setPen(QPen(QColor(tone(theme, "#70ABE9")), 2))
            p.drawLine(w * 0.43, 68, w * 0.57, 68)
            caption(p, QRectF(16, 115, w - 32, 35), "Review → approve → publish", 16)
        elif self.kind == "meeting":
            for i, name in enumerate(("Microphone", "Camera", "Screen")):
                rect = QRectF(16 + i * (w - 32) / 3, 25, (w - 48) / 3, 70)
                tile(rect, name, True)
                p.setPen(QPen(QColor(tone(theme, "#85B8EB")), 2))
                for j in range(7):
                    d = 5 + abs(math.sin(t * 2 + i + j)) * 10
                    x = rect.center().x() + (j - 3) * 6
                    p.drawLine(x, 110 - d / 2, x, 110 + d / 2)
            caption(p, QRectF(16, 129, w - 32, 30), "Check locally. Join when ready.", 14)
        elif self.kind == "review":
            for i, name in enumerate(("Your space", "Your project", "Your control")):
                tile(QRectF(18 + i * (w - 36) / 3, 30, (w - 54) / 3, 70), name, True)
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
