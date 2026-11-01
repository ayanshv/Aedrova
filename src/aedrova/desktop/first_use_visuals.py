"""Finite native motion and actual brand/Bud artwork for first use."""

import time

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QWidget

from aedrova.desktop.brand import brand_image
from aedrova.desktop.bud_art import paint_bud
from aedrova.desktop.icons import icon
from aedrova.desktop.materials import system_font

ROLE_COPY = {
    "builder": "Plan and review software changes.",
    "designer": "Explore design with your shared references.",
    "product": "Turn goals into clear requirements.",
    "research": "Find evidence and follow the sources.",
    "marketing": "Shape campaigns with your approved context.",
    "finance": "Explain the financial information you share.",
}
PURPOSE_ROLES = {
    "software": "builder",
    "design": "designer",
    "research": "research",
    "marketing": "marketing",
    "operations": "product",
    "personal": "research",
}


def ease(value):
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


class OpeningScene(QWidget):
    """A short convergence sequence, then a quiet still composition."""

    def __init__(self, flow):
        super().__init__(flow)
        self.flow = flow
        self.started = time.monotonic()
        self.setMinimumSize(0, 210)
        self.setAccessibleName(
            "Conversations, projects and meetings converge around Aedrova and Buds"
        )
        self.timer = QTimer(self)
        self.timer.setInterval(24)
        self.timer.timeout.connect(self.tick)

    def showEvent(self, event):  # noqa: N802
        self.started = time.monotonic()
        if not self.flow.reduced:
            self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def tick(self):
        self.update()
        if time.monotonic() - self.started > 4:
            self.timer.stop()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        t = self.flow.theme
        scale = min(self.width() / 740, self.height() / 350)
        p.translate(self.width() / 2, self.height() / 2)
        p.scale(scale, scale)
        elapsed = time.monotonic() - self.started
        progress = 1 if self.flow.reduced else ease(elapsed / 2.6)
        # Real neutral material and soft offsets replace continuous blur effects.
        area = QRectF(-208, -126, 416, 252)
        for offset, alpha in ((18, 3), (10, 6), (4, 10)):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, alpha if t.name == "light" else alpha // 2))
            p.drawRoundedRect(area.translated(0, offset), 26, 26)
        gradient = QLinearGradient(area.topLeft(), area.bottomRight())
        gradient.setColorAt(0, QColor(t.elevated))
        gradient.setColorAt(1, QColor(t.surface))
        p.setBrush(gradient)
        p.setPen(QPen(QColor(t.border), 1))
        p.drawRoundedRect(area, 24, 24)
        p.setPen(QColor(t.muted))
        p.setFont(system_font(11, QFont.Weight.Medium))
        p.drawText(QRectF(-176, -106, 320, 24), "YOUR SPACE")
        for i, (name, glyph) in enumerate(
            (("Conversations", "mention"), ("Projects", "folder"), ("Meetings", "camera"))
        ):
            reveal = 1 if self.flow.reduced else ease((elapsed - 0.18 * i) / 1.8)
            x = (-280, 206, -260)[i] + (40 if i != 1 else -40) * reveal
            y = (-72, -28, 68)[i] + 22 * (1 - progress)
            tile = QRectF(x, y, 152, 50)
            p.setOpacity(reveal)
            p.setPen(QPen(QColor(t.border), 1))
            p.setBrush(QColor(t.elevated))
            p.drawRoundedRect(tile, 12, 12)
            pix = icon(glyph, t.accent).pixmap(19, 19)
            p.drawPixmap(int(x + 14), int(y + 15), pix)
            p.setFont(system_font(11, QFont.Weight.Medium))
            p.setPen(QColor(t.text))
            p.drawText(tile.adjusted(42, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, name)
        p.setOpacity(1 if self.flow.reduced else ease(elapsed / 0.9))
        side = 88 + 14 * progress
        p.drawImage(QRectF(-side / 2, -side / 2 - 20, side, side), brand_image())
        p.setFont(system_font(13, QFont.Weight.DemiBold))
        p.setPen(QColor(t.text))
        p.drawText(QRectF(-90, 44, 180, 26), Qt.AlignmentFlag.AlignCenter, "Aedrova")
        for i, role in enumerate(("builder", "research", "product")):
            p.setOpacity(1 if self.flow.reduced else ease((elapsed - 0.8 - i * 0.15) / 1.1))
            paint_bud(p, QRectF(-108 + i * 76, 84, 64, 64), {"appearance": role}, phase=0)
        p.end()


class BudChoice(QAbstractButton):
    def __init__(self, role, flow):
        super().__init__(flow)
        self.role, self.flow = role, flow
        self.active = False
        self._selection = 0.0
        self.selection_animation = QPropertyAnimation(self, b"selection", self)
        self.selection_animation.setDuration(230)
        self.selection_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self.animate_selection)
        self.setCheckable(True)
        self.setText(role.title())
        self.setAccessibleName(role.title() + " Bud. " + ROLE_COPY[role])
        self.setToolTip(ROLE_COPY[role])
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(134, 185)
        self.setMaximumHeight(224)

    def get_selection(self):
        return self._selection

    def set_selection(self, value):
        self._selection = value
        self.update()

    selection = Property(float, get_selection, set_selection)

    def animate_selection(self, checked):
        self.selection_animation.stop()
        if self.flow.reduced:
            self.set_selection(float(checked))
        else:
            self.selection_animation.setStartValue(self._selection)
            self.selection_animation.setEndValue(float(checked))
            self.selection_animation.start()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.flow.theme
        width, height = self.width(), self.height()
        chosen = self.isChecked() or self.active
        rect = QRectF(5, 5, width - 10, height - 10)
        if chosen or self.underMouse() or self.hasFocus():
            p.setBrush(QColor(t.accent_bg if chosen else t.surface))
            p.setPen(QPen(QColor(t.accent if self.hasFocus() or chosen else t.border), 1))
            p.drawRoundedRect(rect, 16, 16)
        size = min(106 + 4 * self._selection, width - 24)
        paint_bud(p, QRectF((width - size) / 2, 12, size, size), {"appearance": self.role})
        p.setFont(system_font(14, QFont.Weight.DemiBold))
        p.setPen(QColor(t.text))
        p.drawText(QRectF(8, 122, width - 16, 22), Qt.AlignmentFlag.AlignCenter, self.text())
        p.setFont(system_font(10))
        p.setPen(QColor(t.muted))
        p.drawText(
            QRectF(14, 148, width - 28, height - 154),
            Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap,
            "Active" if self.active else ROLE_COPY[self.role],
        )
        if self.role == PURPOSE_ROLES[self.flow.purpose.currentData()] and not self.active:
            p.setFont(system_font(9, QFont.Weight.Medium))
            p.setPen(QColor(t.accent))
            p.drawText(QRectF(12, 8, width - 44, 18), "Recommended")
        if chosen:
            p.drawPixmap(width - 26, 13, icon("check", t.accent).pixmap(14, 14))
        p.end()
