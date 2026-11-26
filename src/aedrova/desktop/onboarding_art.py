"""Setup's moving parts: the drifting colour wash, a painted scene per step, and a small burst.

Everything here is drawn, never a screenshot, so it follows the theme, stays sharp on any
display, and goes still when Reduce Motion is on.
"""

import math
import random

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import (
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QGraphicsBlurEffect, QWidget

from aedrova.desktop import motion
from aedrova.desktop.icons import icon
from aedrova.desktop.zen_theme import visual_theme

WASH_LIGHT = ("#FFD3E8", "#DCD0FF", "#FFE3CF", "#D2E8FF")
# Dark mode uses the same two soft glows as the iPhone workspace list: blue from the top left,
# teal from the top right. Each is (colour, opacity, reach as a share of the width, x, y).
GLOW_DARK = (
    ("#4D80FA", 0.20, 0.9, 0.0, 0.0),
    ("#40C7C7", 0.14, 0.82, 1.0, 0.0),
)
PERMISSION_ORDER = ("microphone", "camera", "screen")
PERMISSION_GLYPHS = {"microphone": "microphone", "camera": "camera", "screen": "screen"}


class AuroraSurface(QWidget):
    """A pastel wash that drifts slowly, and leans a different way on every step."""

    def __init__(self):
        super().__init__()
        self.phase, self.bias, self.level = 0.0, 0.0, 1.0
        self.cache, self.cache_key = None, None
        self.opening = False  # the first screen: a fuller wash, centred, nothing above it
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.advance)
        self.lean = QVariantAnimation(self)
        self.lean.setDuration(1100)
        self.lean.setEasingCurve(motion.EASE)
        self.lean.valueChanged.connect(self.set_bias)

    def set_bias(self, value):
        self.bias = float(value)
        self.update()

    def set_stage(self, index):
        goal = index * 0.9
        if motion.reduced() or not self.isVisible():
            self.bias = goal
            self.update()
            return
        self.lean.stop()
        self.lean.setStartValue(self.bias)
        self.lean.setEndValue(goal)
        self.lean.start()

    def set_active(self, active):
        self.level = 1.0 if active else 0.0
        if active and self.isVisible() and not motion.reduced():
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def advance(self):
        self.phase += 0.012
        self.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if self.level > 0 and not motion.reduced():
            self.timer.start()

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):  # noqa: N802
        base = QColor(visual_theme(self).bg)
        painter = QPainter(self)
        if self.level <= 0.01:
            painter.fillRect(self.rect(), base)
            return
        # The wash is soft, so it is drawn small and stretched: about a thirtieth of the
        # pixels, which keeps every other animation on screen smooth.
        scale = 6
        size = QSize(max(8, self.width() // scale), max(8, self.height() // scale))
        key = (
            size.width(),
            size.height(),
            round(self.phase, 3),
            round(self.bias, 3),
            base.rgb(),
            self.opening,
        )
        if key != self.cache_key:
            self.cache_key, self.cache = key, self.render_wash(size, base)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(self.rect(), self.cache)

    def render_wash(self, size, base):
        image = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(base)
        painter = QPainter(image)
        dark = base.lightness() < 128
        width, height = size.width(), size.height()
        radius = max(width, height) * 0.62
        if dark:
            drift = 0.03 * math.sin(self.phase)
            for hex_color, opacity, reach, x, y in GLOW_DARK:
                center = QPointF(width * (x + drift * (1 - 2 * x)), height * y)
                gradient = QRadialGradient(center, width * reach)
                color = QColor(hex_color)
                color.setAlphaF(min(1.0, opacity * (1.5 if self.opening else 1.0)))
                gradient.setColorAt(0.0, color)
                color.setAlpha(0)
                gradient.setColorAt(1.0, color)
                painter.fillRect(image.rect(), gradient)
            painter.end()
            return image
        for index, hex_color in enumerate(WASH_LIGHT):
            angle = self.phase * (0.8 + index * 0.25) + index * 1.7 + self.bias
            center = QPointF(
                width * (0.36 + 0.24 * math.cos(angle)),
                height * (0.68 + 0.18 * math.sin(angle * 0.9 + index)),
            )
            gradient = QRadialGradient(center, radius)
            color = QColor(hex_color)
            color.setAlpha(round((38 if dark else 105) * (1.4 if self.opening else 1.0)))
            gradient.setColorAt(0.0, color)
            color.setAlpha(0)
            gradient.setColorAt(1.0, color)
            painter.fillRect(image.rect(), gradient)
        if not self.opening:
            fade = QLinearGradient(0, 0, 0, height * 0.55)
            fade.setColorAt(0.0, QColor(255, 255, 255, 235))
            fade.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillRect(image.rect(), fade)
        painter.end()
        return image


class StageArt(QWidget):
    """The right half of setup. A new scene blurs and rises into place; nothing bounces."""

    SCENES = (
        "welcome",
        "account",
        "privacy",
        "theme",
        "permissions",
        "project",
        "import",
        "goal",
    )

    def __init__(self, flow):
        super().__init__(flow)
        self.flow = flow
        self.scene = "welcome"
        self.previous = None
        self.direction = 1
        self.enter = 1.0
        self.tick = 0.0
        self.preview = None  # the appearance the theme scene shows
        self.granted = set()
        self.levels = {kind: 0.0 for kind in PERMISSION_ORDER}
        self.arrival = QVariantAnimation(self)
        self.arrival.setDuration(520)
        self.arrival.setEasingCurve(motion.EASE)
        self.arrival.valueChanged.connect(self.set_enter)
        self.arrival.finished.connect(self.settled)
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.advance)
        self.setAccessibleName("Setup illustration")

    # -- state ---------------------------------------------------------------------
    @property
    def theme(self):
        return self.flow.theme

    def dark(self):
        return self.theme.name == "dark"

    def show_scene(self, scene, forward=True):
        if scene == self.scene and self.enter >= 1.0:
            return
        self.previous = self.scene if self.enter >= 1.0 else self.previous
        self.scene = scene
        self.direction = 1 if forward else -1
        self.arrival.stop()
        if motion.reduced() or not self.isVisible():
            self.enter, self.previous = 1.0, None
            self.update()
            return
        # One scene leaves as the next arrives; the blur peaks in the middle and clears.
        self.setGraphicsEffect(QGraphicsBlurEffect(self))
        self.arrival.setStartValue(0.0)
        self.arrival.setEndValue(1.0)
        self.arrival.start()

    def set_enter(self, value):
        self.enter = float(value)
        effect = self.graphicsEffect()
        if isinstance(effect, QGraphicsBlurEffect):
            effect.setBlurRadius(9 * math.sin(math.pi * self.enter))
        self.update()

    def settled(self):
        self.enter, self.previous = 1.0, None
        self.setGraphicsEffect(None)
        self.update()

    def set_preview(self, mode):
        self.preview = mode
        self.update()

    def set_granted(self, kinds):
        self.granted = set(kinds)
        if motion.reduced():
            self.levels = {k: 1.0 if k in self.granted else 0.0 for k in self.levels}
        self.update()

    def advance(self):
        self.tick += 0.04
        for kind, level in self.levels.items():
            goal = 1.0 if kind in self.granted else 0.0
            self.levels[kind] = level + max(-0.12, min(0.12, goal - level))
        self.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if not motion.reduced():
            self.timer.start()

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    # -- drawing helpers -----------------------------------------------------------
    def ink(self, alpha=255):
        color = QColor(self.theme.text)
        color.setAlpha(alpha)
        return color

    def paper(self):
        return QColor(self.theme.bg if self.dark() else "#FFFFFF")

    def card(self, p, rect, radius=16, fill=None):
        p.setPen(Qt.PenStyle.NoPen)
        for spread in range(8, 0, -2):
            shadow = QColor(0, 0, 0, 6 if self.dark() else 8)
            p.setBrush(shadow)
            p.drawRoundedRect(
                rect.adjusted(-spread, -spread + 5, spread, spread + 5),
                radius + spread,
                radius + spread,
            )
        p.setBrush(fill or (QColor(self.theme.surface) if self.dark() else QColor("#FFFFFF")))
        p.setPen(QPen(QColor(self.theme.border), 1))
        p.drawRoundedRect(rect, radius, radius)

    def bar(self, p, x, y, w, h=7, alpha=34):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.ink(alpha))
        p.drawRoundedRect(QRectF(x, y, w, h), h / 2, h / 2)

    def dot(self, p, cx, cy, r, color):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color))
        p.drawEllipse(QPointF(cx, cy), r, r)

    def toggle(self, p, rect, level):
        p.setPen(Qt.PenStyle.NoPen)
        off, on = QColor(self.ink(40)), QColor("#3D74FF")
        mix = QColor(
            round(off.red() + (on.red() - off.red()) * level),
            round(off.green() + (on.green() - off.green()) * level),
            round(off.blue() + (on.blue() - off.blue()) * level),
            round(off.alpha() + (on.alpha() - off.alpha()) * level),
        )
        p.setBrush(mix)
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        knob = rect.height() - 6
        x = rect.left() + 3 + (rect.width() - knob - 6) * level
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(x, rect.top() + 3, knob, knob))

    # -- painting ------------------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), self.paper())
        edge = QLinearGradient(0, 0, 26, 0)
        edge.setColorAt(0.0, QColor(0, 0, 0, 22 if not self.dark() else 60))
        edge.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(QRectF(0, 0, 26, self.height()), edge)
        float_y = math.sin(self.tick * 1.1) * 4 if not motion.reduced() else 0.0
        scale = max(0.8, min(self.width() / 460, self.height() / 520, 1.7))
        for name, opacity, shift in self.layers():
            p.save()
            p.setOpacity(opacity)
            p.translate(self.width() / 2 + shift, self.height() / 2 + float_y)
            p.scale(scale, scale)
            getattr(self, "paint_" + name)(p)
            p.restore()
        p.end()

    def layers(self):
        """The scenes on screen right now: the one leaving and the one arriving."""
        if self.enter >= 1.0 or self.previous is None:
            return [(self.scene, 1.0, 0.0)]
        e, d = self.enter, self.direction
        leaving = max(0.0, 1.0 - e * 2.0)
        arriving = max(0.0, e * 2.0 - 1.0)
        return [
            (self.previous, leaving, -d * 36 * e),
            (self.scene, arriving, d * 36 * (1.0 - e)),
        ]

    def paint_welcome(self, p):
        window = QRectF(-190, -135, 380, 270)
        self.card(p, window, 16)
        for i, color in enumerate(("#FF6058", "#FFBD2E", "#28C840")):
            self.dot(p, window.left() + 18 + i * 14, window.top() + 16, 4, color)
        side = QRectF(window.left() + 12, window.top() + 34, 96, window.height() - 46)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.ink(10))
        p.drawRoundedRect(side, 10, 10)
        for i, color in enumerate(("#8275E6", "#48A9AF", "#E58BC8")):
            y = side.top() + 22 + i * 34
            self.dot(p, side.left() + 20, y, 9, color)
            self.bar(p, side.left() + 36, y - 3, 40 - i * 6, 6, 60)
        chat = window.adjusted(124, 40, -16, -16)
        p.setBrush(self.ink(16))
        p.drawRoundedRect(QRectF(chat.left(), chat.top(), 150, 30), 10, 10)
        self.bar(p, chat.left() + 12, chat.top() + 12, 100, 6, 70)
        p.setBrush(QColor("#3D74FF"))
        p.drawRoundedRect(QRectF(chat.right() - 130, chat.top() + 42, 130, 30), 10, 10)
        p.setBrush(QColor(255, 255, 255, 220))
        p.drawRoundedRect(QRectF(chat.right() - 118, chat.top() + 54, 84, 6), 3, 3)
        agent = QRectF(chat.left(), chat.bottom() - 66, chat.width(), 62)
        self.card(p, agent, 12)
        self.bar(p, agent.left() + 14, agent.top() + 16, 120, 7, 70)
        self.bar(p, agent.left() + 14, agent.top() + 32, 80, 6, 36)
        for i in range(4):
            pulse = 0.5 + 0.5 * math.sin(self.tick * 3.2 - i * 0.8)
            alpha = 90 + round(165 * pulse)
            self.dot(
                p, agent.right() - 58 + i * 12, agent.top() + 20, 3.4, QColor(61, 116, 255, alpha)
            )

    def paint_account(self, p):
        ring = QPainterPath()
        ring.addEllipse(QPointF(0, -34), 58, 58)
        gradient = QLinearGradient(-58, -92, 58, 24)
        for stop, color in ((0, "#FFB5DA"), (0.5, "#C9B6FF"), (1, "#B9DCFF")):
            gradient.setColorAt(stop, QColor(color))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gradient)
        p.drawPath(ring)
        p.setBrush(QColor(255, 255, 255, 235))
        p.drawEllipse(QPointF(0, -48), 17, 17)
        p.drawChord(QRectF(-32, -24, 64, 52), 0, 180 * 16)
        for i, width in enumerate((200, 200)):
            box = QRectF(-width / 2, 52 + i * 46, width, 34)
            self.card(p, box, 11)
            self.bar(p, box.left() + 14, box.center().y() - 3, 70 + i * 30, 7, 40)
        p.setBrush(QColor("#3D74FF"))
        p.drawRoundedRect(QRectF(-100, 148, 200, 34), 11, 11)

    def paint_privacy(self, p):
        panel = QRectF(-130, -96, 260, 192)
        self.card(p, panel, 18)
        body = QRectF(-26, -52, 52, 40)
        p.setPen(QPen(QColor("#3D74FF"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        shackle = QPainterPath()
        shackle.moveTo(-15, -52)
        shackle.arcTo(QRectF(-15, -74, 30, 40), 180, -180)
        p.drawPath(shackle)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#3D74FF"))
        p.drawRoundedRect(body, 9, 9)
        p.setBrush(QColor(255, 255, 255, 230))
        p.drawEllipse(QPointF(0, -32), 5, 5)
        for i in range(3):
            y = 14 + i * 24
            self.dot(p, -96, y + 4, 8, QColor(40, 200, 120, 40))
            p.setPen(QPen(QColor("#1F9D55"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPolyline([QPointF(-100, y + 4), QPointF(-97, y + 7), QPointF(-92, y + 1)])
            self.bar(p, -78, y, 150 - i * 22, 8, 40)

    def paint_theme(self, p):
        mode = self.preview or getattr(self.flow, "theme_mode", "system")
        dark = mode == "dark" or (mode == "system" and self.dark())
        window = QRectF(-190, -120, 380, 240)
        p.setPen(Qt.PenStyle.NoPen)
        for spread in range(8, 0, -1):
            p.setBrush(QColor(0, 0, 0, 4))
            p.drawRoundedRect(
                window.adjusted(-spread, -spread + 5, spread, spread + 5), 16 + spread, 16 + spread
            )
        p.setPen(QPen(QColor("#393939" if dark else "#E1E5EB"), 1))
        p.setBrush(QColor("#171717" if dark else "#F8F9FB"))
        p.drawRoundedRect(window, 16, 16)
        for i, color in enumerate(("#FF6058", "#FFBD2E", "#28C840")):
            self.dot(p, window.left() + 18 + i * 14, window.top() + 16, 4, color)
        paper = QColor("#242424" if dark else "#FFFFFF")
        ink = QColor(255, 255, 255, 46) if dark else QColor(0, 0, 0, 20)
        side = QRectF(window.left() + 14, window.top() + 36, 110, window.height() - 50)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(paper)
        p.drawRoundedRect(QRectF(side.left(), side.top(), side.width(), 30), 9, 9)
        self.dot(p, side.left() + 16, side.top() + 15, 6, "#3D74FF")
        p.setBrush(ink)
        p.drawRoundedRect(QRectF(side.left() + 30, side.top() + 12, 44, 6), 3, 3)
        for i in range(4):
            p.drawRoundedRect(QRectF(side.left(), side.top() + 44 + i * 26, side.width(), 18), 7, 7)
        main = QRectF(window.left() + 138, window.top() + 36, window.width() - 152, 190)
        for i in range(3):
            p.setBrush(paper)
            p.drawRoundedRect(QRectF(main.left(), main.top() + i * 62, main.width(), 52), 11, 11)
            p.setBrush(ink)
            p.drawRoundedRect(QRectF(main.left() + 14, main.top() + i * 62 + 16, 120, 7), 3.5, 3.5)
            p.drawRoundedRect(QRectF(main.left() + 14, main.top() + i * 62 + 31, 70, 6), 3, 3)

    def paint_permissions(self, p):
        panel = QRectF(-170, -120, 340, 240)
        self.card(p, panel, 18)
        labels = {"microphone": 150, "camera": 118, "screen": 170}
        for i, kind in enumerate(PERMISSION_ORDER):
            row = QRectF(panel.left() + 18, panel.top() + 20 + i * 70, panel.width() - 36, 56)
            tile = QRectF(row.left() + 4, row.top() + 8, 40, 40)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.ink(14))
            p.drawRoundedRect(tile, 11, 11)
            color = self.theme.text
            icon(PERMISSION_GLYPHS[kind], color).paint(p, tile.adjusted(8, 8, -8, -8).toRect())
            self.bar(p, row.left() + 58, row.center().y() - 4, labels[kind] * 0.8, 8, 40)
            self.toggle(
                p, QRectF(row.right() - 54, row.center().y() - 15, 50, 30), self.levels[kind]
            )
            if i < 2:
                p.setPen(QPen(self.ink(18), 1))
                p.drawLine(
                    QPointF(row.left(), row.bottom() + 7), QPointF(row.right(), row.bottom() + 7)
                )

    def paint_project(self, p):
        folder = QPainterPath()
        folder.addRoundedRect(QRectF(-90, -62, 180, 120), 16, 16)
        tab = QPainterPath()
        tab.addRoundedRect(QRectF(-90, -82, 74, 36), 12, 12)
        gradient = QLinearGradient(-90, -80, 90, 60)
        gradient.setColorAt(0.0, QColor("#7DB4FF"))
        gradient.setColorAt(1.0, QColor("#3D74FF"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gradient)
        p.drawPath(tab.united(folder))
        terminal = QRectF(-130, 20, 260, 96)
        self.card(p, terminal, 14, QColor("#17181C"))
        steps = int(self.tick * 8) % 40 if not motion.reduced() else 40
        for i, width in enumerate((120, 170, 90)):
            shown = min(width, max(0, steps * 8 - i * 70))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 80 if i else 140))
            p.drawRoundedRect(
                QRectF(terminal.left() + 18, terminal.top() + 20 + i * 22, shown, 7), 3.5, 3.5
            )

    def paint_import(self, p):
        """Channels on one side, Aedrova on the other, messages travelling across."""
        left = QRectF(-190, -70, 120, 140)
        right = QRectF(70, -70, 120, 140)
        self.card(p, left, 16)
        from aedrova.desktop.slack_logo import paint_logo

        paint_logo(p, QRectF(left.center().x() - 24, left.top() + 20, 48, 48))
        for i in range(3):
            self.bar(p, left.left() + 22, left.top() + 84 + i * 16, 76 - i * 14, 7, 40)
        self.card(p, right, 16)
        icon("work", "#3D74FF").paint(
            p, QRectF(right.center().x() - 18, right.top() + 24, 36, 36).toRect()
        )
        self.bar(p, right.left() + 22, right.top() + 80, 76, 7, 50)
        self.bar(p, right.left() + 34, right.top() + 98, 52, 6, 30)
        run = self.tick * 0.9 if not motion.reduced() else 0.6
        for i in range(5):
            t = (run + i / 5) % 1.0
            x = left.right() + 10 + (right.left() - left.right() - 20) * t
            y = math.sin(t * math.pi * 2 + i) * 8
            alpha = round(255 * math.sin(t * math.pi))
            self.dot(p, x, y, 4, QColor(61, 116, 255, alpha))

    def paint_goal(self, p):
        for turn, shift, color in ((-9, -46, "#C9B6FF"), (0, 0, "#FFB5DA"), (9, 46, "#B9DCFF")):
            p.save()
            p.translate(shift, 12 + abs(shift) * 0.12)
            p.rotate(turn)
            card = QRectF(-70, -96, 140, 192)
            self.card(p, card, 16)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(color))
            p.drawRoundedRect(
                QRectF(card.left() + 12, card.top() + 12, card.width() - 24, 70), 10, 10
            )
            self.bar(p, card.left() + 14, card.top() + 98, 90, 8, 44)
            self.bar(p, card.left() + 14, card.top() + 116, 60, 7, 30)
            p.restore()


class Confetti(QWidget):
    """A short burst when setup finishes. Gone in under two seconds, skipped for Reduce Motion."""

    COLORS = ("#3D74FF", "#FFB5DA", "#C9B6FF", "#FFD3B3", "#48A9AF", "#FFC93C")

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setGeometry(parent.rect())
        rng = random.Random(7)
        self.pieces = [
            [
                parent.width() * rng.uniform(0.15, 0.85),
                parent.height() * 0.82,
                rng.uniform(-3.2, 3.2),
                rng.uniform(-13, -7),
                rng.uniform(4, 8),
                rng.uniform(0, 6.3),
                rng.choice(self.COLORS),
            ]
            for _ in range(70)
        ]
        self.age = 0
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.step)
        self.timer.start()
        self.show()
        self.raise_()

    def step(self):
        self.age += 1
        for piece in self.pieces:
            piece[0] += piece[2]
            piece[1] += piece[3]
            piece[3] += 0.35
            piece[5] += 0.2
        if self.age > 110:
            self.timer.stop()
            self.deleteLater()
        self.update()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        fade = max(0.0, min(1.0, (110 - self.age) / 40))
        for x, y, _, _, size, spin, color in self.pieces:
            p.save()
            p.translate(x, y)
            p.rotate(math.degrees(spin))
            shade = QColor(color)
            shade.setAlphaF(fade)
            p.setBrush(shade)
            p.drawRect(QRectF(-size / 2, -size / 4, size, size / 2))
            p.restore()
