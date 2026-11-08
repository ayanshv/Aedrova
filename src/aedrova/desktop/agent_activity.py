"""Accessible live activity text; displays public updates, never private reasoning."""

import re

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QLabel, QPushButton

from aedrova.desktop.icons import icon
from aedrova.desktop.materials import system_font
from aedrova.desktop.theme import DARK


def activity_icon(text):
    text = text.casefold()
    if re.search(r"\b(?:pytest|unittest|test|tests|checking results|verif\w*)\b", text):
        return "check"
    if text.startswith(("running", "$ ")) or "command" in text:
        return "terminal"
    if text.startswith(("edited", "files changed", "updated project files")):
        return "file_changes"
    if re.search(r"\b(?:search\w*|find\w*|look\w*)\b", text):
        return "search"
    if re.search(r"\b(?:reading|context|evidence|consulting)\b", text):
        return "context"
    if re.search(r"\b(?:access|permission|approval)\b", text):
        return "permission_auto"
    return "activity"


def work_note(event):
    """Explain observed work without exposing raw tool output."""
    text = event.casefold()
    if text.startswith("running:"):
        if re.search(r"\b(?:pytest|unittest|test|tests)\b", text):
            return "I’m running the tests to check how the changes behave."
        return "I’m running a command in the build copy."
    for prefixes, note in (
        (("files changed:", "edited "), "I’ve made changes in the separate build copy."),
        (("preparing response", "thinking"), "I’m getting started on your request."),
        (("checking workspace access",), "I’m checking which workspace sources I can use."),
        (
            ("finding relevant context", "searching permitted", "reading #"),
            "I’m looking through the conversations I can access for details that matter here.",
        ),
        (
            ("reading source-backed product memory",),
            "I’m checking product decisions and their supporting sources.",
        ),
        (
            (
                "looking for shared",
                "consulting shared work",
                "reading shared work",
                "reading shared build reviews",
            ),
            "I’m looking at what the team and other Buds have already worked on.",
        ),
        (("reading reviewed meeting notes",), "I’m checking meeting notes the team has shared."),
        (
            ("choosing relevant buds", "rechecking connected tools"),
            "I’m checking which connected tools can help with this request.",
        ),
        (("analyzing:",), "I’m reading the connected sources I selected for this request."),
        (("reading the connected project",), "I’m reading the files in the connected project."),
        (
            ("preparing an independent local git copy",),
            "I’m setting up a separate copy so I can work without editing the original project.",
        ),
        (
            ("plan ready · starting background build", "plan ready. starting the build"),
            "The plan is ready. I’m moving on to the build.",
        ),
        (
            ("checking your workspace’s included ai access",),
            "I’m checking which AI access is available for this run.",
        ),
        (("writing a response",), "I’m putting the answer together."),
        (("checking reply sources",), "I’m checking the references in the reply."),
    ):
        if text.startswith(prefixes):
            return note
    return ""


class WorkNotes(QLabel):
    """A short, ephemeral log for the current request."""

    def __init__(self):
        super().__init__()
        self.notes = []
        self.setObjectName("AgentWorkNotes")
        self.setAccessibleName("What the agent is doing")
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(True)
        self.setFont(system_font(13))
        self.hide()

    def record(self, event):
        note = work_note(event)
        if not note or note in self.notes:
            return False
        self.notes = (self.notes + [note])[-3:]
        self.setText("\n\n".join(self.notes))
        self.show()
        return True

    def clear(self):
        self.notes.clear()
        super().clear()
        self.hide()


class AgentActivity(QPushButton):
    def __init__(self):
        super().__init__()
        self.setAccessibleName("Agent activity · open details")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFont(system_font(14))
        self.active = False
        self.reduced_motion = False
        self.phase = 0.0
        self.theme = DARK
        self.glyph_key = None
        self.glyph = None
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.advance)

    def sizeHint(self):  # noqa: N802
        return QSize(300, 32)

    def configure(self, theme, reduced_motion, active):
        self.theme, self.reduced_motion, self.active = theme, reduced_motion, active
        self.sync_animation()
        self.update()

    def sync_animation(self):
        if self.active and not self.reduced_motion and self.isVisible():
            if not self.timer.isActive():
                self.timer.start()
        else:
            self.timer.stop()
            self.phase = 0.0

    def advance(self):
        self.phase = (self.phase + 0.018) % 1.0
        self.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.sync_animation()

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())
        base = QColor(self.theme.muted)
        glyph_key = (activity_icon(self.text()), self.theme.secondary)
        if glyph_key != self.glyph_key:
            self.glyph_key = glyph_key
            self.glyph = icon(*glyph_key)
        self.glyph.paint(painter, 0, (self.height() - 16) // 2, 16, 16)
        metrics = self.fontMetrics()
        text = metrics.elidedText(
            self.text(), Qt.TextElideMode.ElideRight, max(0, self.width() - 28)
        )
        if text and self.active and not self.reduced_motion:
            text_width = metrics.horizontalAdvance(text)
            radius = min(100, max(12, text_width / 3))
            center = self.phase * (text_width + 2 * radius) - radius
            glow = QLinearGradient(22 + center - radius, 0, 22 + center + radius, 0)
            glow.setColorAt(0, base)
            glow.setColorAt(0.5, QColor(self.theme.text))
            glow.setColorAt(1, base)
            painter.setPen(QPen(glow, 1))
        else:
            painter.setPen(base)
        painter.drawText(
            self.rect().adjusted(22, 0, -6, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QColor(self.theme.accent))
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class AgentClock(QLabel):
    """Elapsed work time only; no fabricated token or reasoning progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        import time

        self.now = time.monotonic
        self.started = None
        self.active = False
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setProperty("role", "muted")
        self.setAccessibleName("Elapsed agent work time")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.setInterval(1000)
        self.hide()

    def reset(self):
        self.started = None
        self.active = False
        self.timer.stop()
        self.hide()
        self.refresh()

    def set_active(self, active):
        if active and self.started is None:
            self.started = self.now()
        self.active = active
        if active:
            self.timer.start()
            self.show()
        else:
            self.timer.stop()
            self.hide()
        self.refresh()

    def refresh(self):
        seconds = int(self.now() - self.started) if self.started is not None else 0
        self.setText(f"{seconds // 60}:{seconds % 60:02d}")
        self.setToolTip("Elapsed work time on this Mac")
