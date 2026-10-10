"""Native living teammate shelf: bounded local physics, no model calls while idle."""

import math
import time
from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from aedrova.desktop.dialogs import button, label


def _planet_clip(r):
    path = QPainterPath()
    path.addEllipse(QRectF(-r, -r, 2 * r, 2 * r))
    return path


def paint_orb(p, rect, config, *, phase=0.0, blink=False, look=0.0, rotation=0.0):
    from aedrova.desktop.bud_art import paint_bud

    if paint_bud(p, rect, config, phase=phase, blink=blink, look=look, rotation=rotation):
        return
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(rect.center())
    p.rotate(rotation)
    scale = 1 + math.sin(phase * 1.7) * 0.018
    p.scale(scale, scale)
    # Planets stay legible at sidebar scale: one sphere, two eyes, one smile.
    r = min(rect.width(), rect.height()) * 0.37
    base = QColor(config.get("color", "#4388F5"))
    if not base.isValid():
        base = QColor("#4388F5")
    shape = config.get("shape", "round")
    ringed = shape in {"cloud", "ringed"}
    ink = QColor("#FFFFFF") if base.lightnessF() < 0.53 else QColor("#202124")
    if ringed:
        p.save()
        p.rotate(-18)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(base.lighter(140), max(1.4, r * 0.11)))
        p.drawEllipse(QRectF(-r * 1.47, -r * 0.34, r * 2.94, r * 0.68))
        p.restore()
    from PySide6.QtGui import QRadialGradient

    gradient = QRadialGradient(-r * 0.4, -r * 0.5, r * 2.2)
    gradient.setColorAt(0, base.lighter(115))
    gradient.setColorAt(1, base.darker(115))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(gradient)
    p.drawEllipse(QRectF(-r, -r, r * 2, r * 2))
    if shape in {"squircle", "moon"}:
        p.save()
        p.setClipPath(_planet_clip(r))
        crater = QColor(base.darker(120))
        crater.setAlpha(55)
        p.setBrush(crater)
        for x, y, size in [(-0.6, -0.5, 0.24), (0.56, 0.44, 0.30), (0.68, -0.48, 0.17)]:
            p.drawEllipse(QRectF(x * r, y * r, size * r, size * r))
        p.restore()
    if ringed:
        p.save()
        p.rotate(-18)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(
            QPen(
                base.lighter(140),
                max(1.4, r * 0.11),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        p.drawArc(QRectF(-r * 1.47, -r * 0.34, r * 2.94, r * 0.68), 180 * 16, 180 * 16)
        p.restore()
    gaze = max(-1.0, min(1.0, look)) * r * 0.06
    p.setBrush(ink)
    for x in (-r * 0.25, r * 0.25):
        if blink:
            p.setPen(QPen(ink, max(1.2, r * 0.08), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(x - r * 0.04 + gaze, -r * 0.08, x + r * 0.04 + gaze, -r * 0.08)
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.drawEllipse(QRectF(x - r * 0.055 + gaze, -r * 0.15, r * 0.11, r * 0.13))
    smile = QPainterPath()
    smile.moveTo(-r * 0.10, r * 0.15)
    smile.cubicTo(-r * 0.08, r * 0.34, r * 0.08, r * 0.34, r * 0.10, r * 0.15)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(ink, max(1.1, r * 0.05), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawPath(smile)
    p.restore()


class OrbButton(QAbstractButton):
    def __init__(self, row, parent):
        super().__init__(parent)
        self.row = row
        self.phase = self.rotation = self.look = 0.0
        self.setFixedSize(56, 56)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_row(row)

    def update_row(self, row):
        self.row = row
        name = row["config"]["name"]
        self.setAccessibleName("Mention AI teammate " + name)
        self.setToolTip(name + (" · Paused" if row["paused"] else " · Click to mention"))
        self.update()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        period = 4.2 + (sum(map(ord, self.row["id"])) % 10) / 10
        blink = self.phase > 0 and self.phase % period < 0.14
        paint_orb(
            p,
            QRectF(self.rect()).adjusted(2, 2, -2, -2),
            self.row["config"],
            phase=self.phase,
            blink=blink,
            look=self.look,
            rotation=self.rotation,
        )
        if self.row["paused"]:
            p.setPen(QPen(QColor("#7A8CA6"), 2))
            p.drawLine(24, 40, 24, 46)
            p.drawLine(30, 40, 30, 46)
        if self.row.get("provider"):
            status = self.row.get("status", "Needs authorization")
            colors = {
                "Connected": "#4388F5",
                "Syncing": "#8275E6",
                "Connecting": "#8275E6",
                "Error": "#D981A3",
                "Permission issue": "#D981A3",
            }
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(colors.get(status, "#7A8CA6")))
            p.drawEllipse(QRectF(42, 43, 5, 5))
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor("#4388F5"), 2))
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)


@dataclass
class Marble:
    widget: OrbButton
    x: float
    y: float
    vx: float = 0
    vy: float = 0
    angle: float = 0


class Habitat(QWidget):
    mentioned = Signal(object)

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.workspace = None
        self.marbles = {}
        self.last = time.monotonic()
        self.setMinimumHeight(82)
        self.setMouseTracking(True)
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.empty = QLabel("Another pair of hands.\nCreate your first AI teammate.", self)
        self.empty.setProperty("role", "muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def sync(self, rows, workspace):
        if workspace != self.workspace:
            for marble in self.marbles.values():
                marble.widget.deleteLater()
            self.marbles.clear()
            self.workspace = workspace
        live = {r["id"]: r for r in rows}
        for key in list(self.marbles):
            if key not in live:
                self.marbles.pop(key).widget.deleteLater()
        for key, row in live.items():
            if key in self.marbles:
                self.marbles[key].widget.update_row(row)
                continue
            widget = OrbButton(row, self)
            widget.clicked.connect(lambda checked=False, k=key: self.wake(k))
            n = len(self.marbles)
            self.marbles[key] = Marble(
                widget, 8 + (n % 3) * 57, -58 - n * 18, (-1 if n % 2 else 1) * 35
            )
            widget.show()
        self.setFixedHeight(max(82, min(250, 64 * math.ceil(max(1, len(live)) / 3) + 12)))
        self.empty.setVisible(not live)
        if self.window.reduced_motion:
            self.settle_grid()
        if self.isVisible() and not self.window.reduced_motion and live:
            self.last = time.monotonic()
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def wake(self, key):
        marble = self.marbles.get(key)
        if marble is None:
            return
        if not self.window.reduced_motion:
            marble.vy = -130
            marble.vx = 32 if marble.x < self.width() / 2 else -32
        self.mentioned.emit(marble.widget.row)

    def settle_grid(self):
        cols = max(1, self.width() // 58)
        for n, m in enumerate(self.marbles.values()):
            m.x, m.y = (n % cols) * 58, self.height() - 58 - (n // cols) * 58
            m.vx = m.vy = m.angle = 0
            m.widget.phase = m.widget.rotation = 0
            m.widget.move(int(m.x), int(m.y))
            m.widget.update()

    def step(self, dt):
        dt = min(0.033, max(0, dt))
        width, floor = max(0, self.width() - 56), self.height() - 56
        values = list(self.marbles.values())
        for m in values:
            m.vy = min(500, m.vy + 660 * dt)
            m.x += m.vx * dt
            m.y += m.vy * dt
            if m.x < 0 or m.x > width:
                m.x = min(width, max(0, m.x))
                m.vx *= -0.48
            if m.y > floor:
                m.y = floor
                m.vy = -m.vy * 0.34 if m.vy > 35 else 0
                m.vx *= 0.86
            m.angle = (m.angle + m.vx * dt * 1.8) * 0.995
        for _ in range(4):
            for i, a in enumerate(values):
                for b in values[i + 1 :]:
                    dx, dy = b.x - a.x, b.y - a.y
                    distance = math.hypot(dx, dy)
                    if 0.001 < distance < 50:
                        nx, ny = dx / distance, dy / distance
                        shift = (50 - distance) / 2
                        a.x -= nx * shift
                        a.y -= ny * shift
                        b.x += nx * shift
                        b.y += ny * shift
                        velocity = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
                        if velocity < 0:
                            impulse = -0.62 * velocity
                            a.vx -= impulse * nx
                            a.vy -= impulse * ny
                            b.vx += impulse * nx
                            b.vy += impulse * ny
            for m in values:
                m.x = min(width, max(0, m.x))
                m.y = min(floor, m.y)

    def tick(self):
        now = time.monotonic()
        if self.window.reduced_motion:
            self.timer.stop()
            self.settle_grid()
            return
        self.step(now - self.last)
        self.last = now
        look = self.mapFromGlobal(QCursor.pos()).x() / max(1, self.width()) * 2 - 1
        for m in self.marbles.values():
            m.widget.phase = now
            m.widget.look = max(-1, min(1, look))
            m.widget.rotation = m.angle
            m.widget.move(round(m.x), round(m.y))
            m.widget.update()

    def resizeEvent(self, event):  # noqa: N802
        self.empty.setGeometry(self.rect())
        if self.window.reduced_motion:
            self.settle_grid()
        super().resizeEvent(event)

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):  # noqa: N802
        self.last = time.monotonic()
        if self.marbles and not self.window.reduced_motion:
            self.timer.start()
        super().showEvent(event)


class TeamSection(QFrame):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setObjectName("TeamSection")
        column = QVBoxLayout(self)
        column.setContentsMargins(8, 10, 8, 8)
        column.setSpacing(4)
        header = QHBoxLayout()
        self.title = label("AI teammates", "section")
        header.addWidget(self.title)
        header.addStretch()
        add = button("+", "Create or manage AI teammates", "icon")
        add.setFixedSize(24, 24)
        from aedrova.desktop.ai_teammates import open_teammates

        add.clicked.connect(lambda: open_teammates(window))
        self.add_button = add
        header.addWidget(add)
        column.addLayout(header)
        self.habitat = Habitat(window)
        self.habitat.mentioned.connect(self.mention)
        column.addWidget(self.habitat)

    def mention(self, row):
        if row["paused"]:
            self.window.notify(row["config"]["name"] + " is paused. Resume them in AI teammates.")
            return
        composer = self.window.composer
        name = row["config"]["name"]
        composer.mention_tokens[name] = "<@ai:" + row["id"] + "|" + name + ">"
        cursor = composer.editor.textCursor()
        cursor.insertText("@" + name + " ")
        composer.editor.setTextCursor(cursor)
        composer.editor.setFocus()

    def sync(self, rows, workspace):
        self.title.setText("AI teammates" + (f" · {len(rows)}" if rows else ""))
        self.habitat.sync(rows, workspace)
