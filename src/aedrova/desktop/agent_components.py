"""Live, interactive pieces of an agent response.

Everything here shows work the app actually observed. Steps come from real phases and
commands, never from invented progress, and approvals and questions are real gates.
"""

import json
import math
import re

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontDatabase, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

ACCENT = "#3D74FF"
SUCCESS = "#2E9E6B"
FAILURE = "#D6455D"


def reduced_motion():
    app = QApplication.instance()
    return bool(app and app.property("reduceMotion") is True)


def ease(t):
    return t * t * (3 - 2 * t)


class FourDots(QWidget):
    """Four dots that trade places in turn: the quiet 'working' signature."""

    PATTERNS = ((1, 0, 3, 2), (0, 2, 1, 3), (3, 1, 2, 0), (1, 0, 3, 2), (2, 3, 0, 1))
    STEP_MS = 640
    TICK_MS = 33

    def __init__(self, parent=None, *, spacing=9, radius=2.6):
        super().__init__(parent)
        self.spacing, self.radius = spacing, radius
        self.setFixedSize(round(spacing * 3 + radius * 2 + 4), 18)
        self.setAccessibleName("Agent is working")
        self.slots = [0, 1, 2, 3]  # slot of each dot at rest
        self.target = list(self.slots)
        self.elapsed = 0
        self.cycle = 0
        self.timer = QTimer(self)
        self.timer.setInterval(self.TICK_MS)
        self.timer.timeout.connect(self.advance)

    def progress(self):
        return min(1.0, self.elapsed / (self.STEP_MS * 0.7))

    def advance(self):
        self.elapsed += self.TICK_MS
        if self.elapsed >= self.STEP_MS:
            self.slots = list(self.target)
            pattern = self.PATTERNS[self.cycle % len(self.PATTERNS)]
            self.target = [pattern[slot] for slot in self.slots]
            self.cycle += 1
            self.elapsed = 0
        self.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if not reduced_motion():
            self.timer.start()

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = self.palette().color(QPalette.ColorRole.Text)
        accent = QColor(ACCENT)
        t = ease(self.progress())
        mid = self.height() / 2
        for dot, (start, end) in enumerate(zip(self.slots, self.target, strict=True)):
            x = self.radius + 2 + (start + (end - start) * t) * self.spacing
            moving = start != end
            y = mid + (math.sin(math.pi * t) * (5 if dot % 2 else -5) if moving else 0)
            color = QColor(accent if dot == 0 else text)
            color.setAlpha(255 if dot == 0 else (150 if moving else 95))
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), self.radius, self.radius)


class StepIcon(QWidget):
    """Pending ring, spinning arc, check or cross."""

    def __init__(self, state="pending", parent=None):
        super().__init__(parent)
        self.state, self.angle = state, 0
        self.setFixedSize(18, 18)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = self.palette().color(QPalette.ColorRole.Text)
        rect = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        if self.state == "running":
            track = QColor(text)
            track.setAlpha(40)
            painter.setPen(QPen(track, 2))
            painter.drawEllipse(rect)
            pen = QPen(QColor(ACCENT), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(rect, -self.angle * 16, 100 * 16)
        elif self.state == "done":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(SUCCESS))
            painter.drawEllipse(rect)
            pen = QPen(QColor("white"), 1.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            x, y, w = rect.x(), rect.y(), rect.width()
            painter.drawPolyline(
                [
                    QPointF(x + w * 0.27, y + w * 0.53),
                    QPointF(x + w * 0.44, y + w * 0.70),
                    QPointF(x + w * 0.75, y + w * 0.32),
                ]
            )
        elif self.state == "failed":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(FAILURE))
            painter.drawEllipse(rect)
            pen = QPen(QColor("white"), 1.8)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            x, y, w = rect.x(), rect.y(), rect.width()
            a, b = x + w * 0.34, x + w * 0.66
            c, d = y + w * 0.34, y + w * 0.66
            painter.drawLine(QPointF(a, c), QPointF(b, d))
            painter.drawLine(QPointF(b, c), QPointF(a, d))
        else:
            ring = QColor(text)
            ring.setAlpha(90)
            painter.setPen(QPen(ring, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect)


TESTS = re.compile(r"\b(?:pytest|unittest|tests?|vitest|jest|ruff|lint|mypy)\b", re.IGNORECASE)

CONTEXT_PHASES = (
    "finding relevant context",
    "searching permitted",
    "reading #",
    "reading source-backed",
    "looking for shared",
    "consulting shared",
    "reading shared",
    "reading reviewed meeting",
    "choosing relevant buds",
    "rechecking connected",
    "analyzing:",
    "reading the connected",
    "reading the teammate",
)
CHAT_STEPS = (
    ("access", "Checking workspace access"),
    ("context", "Gathering context"),
    ("respond", "Putting the reply together"),
)
BUILD_STEPS = (
    ("copy", "Preparing a safe copy of your project"),
    ("plan", "Reading the project and planning"),
    ("build", "Making changes"),
    ("checks", "Running checks"),
)


class StepChecklist(QWidget):
    """A task list that fills in as the agent works."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps = []  # {"key", "label", "state", "commands": [{"text", "state"}]}
        self.flow = None
        self.rows = []
        self.parts = {}
        self.phase = 0
        self.read_count = None  # how many messages were actually read, for the reply step
        self.setAccessibleName("Agent task list")
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 2, 0, 2)
        self.column.setSpacing(5)
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.spin)
        self.hide()

    # -- model -------------------------------------------------------------
    def find(self, key):
        return next((s for s in self.steps if s["key"] == key), None)

    def seed(self, flow):
        if self.flow:
            return
        self.flow = flow
        for key, label in CHAT_STEPS if flow == "chat" else BUILD_STEPS:
            self.steps.append({"key": key, "label": label, "state": "pending", "commands": []})

    def current(self):
        return next((s for s in self.steps if s["state"] == "running"), None)

    @staticmethod
    def rank(key):
        for order in (CHAT_STEPS, BUILD_STEPS):
            for position, (name, _) in enumerate(order):
                if name == key:
                    return position
        return 50  # extra steps (checking sources, ad hoc work) belong after the standard ones

    @staticmethod
    def default_label(key):
        for order in (CHAT_STEPS, BUILD_STEPS):
            for name, label in order:
                if name == key:
                    return label
        return {"sources": "Checking sources", "work": "Working"}.get(key, key.capitalize())

    def start(self, key, label=None):
        step = self.find(key)
        if step is None:
            text = label or self.default_label(key)
            step = {
                "key": key,
                "label": text[:1].upper() + text[1:],
                "state": "pending",
                "commands": [],
            }
            # Keep the standard order even when a step is reported late: access is checked
            # while context is already being gathered, and must not jump below it.
            at = next(
                (
                    i
                    for i, other in enumerate(self.steps)
                    if self.rank(other["key"]) > self.rank(key)
                ),
                len(self.steps),
            )
            self.steps.insert(at, step)
        if step["state"] == "running":
            return
        if any(
            other["state"] in {"running", "done"} and self.rank(other["key"]) > self.rank(key)
            for other in self.steps
        ):
            # A later step is already under way, so this one finished before the report
            # arrived (or is being repeated). Never reopen it or disturb the current step.
            if step["state"] == "pending":
                step["state"] = "done"
            return
        position = self.steps.index(step)
        for other in list(self.steps[:position]):
            if other["state"] == "pending" and not other["commands"] and self.flow == "chat":
                self.steps.remove(other)  # skipped: it never applied to this request
            elif other["state"] in {"running", "pending"}:
                self.close_commands(other)
                other["state"] = "done"
        for other in self.steps:
            if other is not step and other["state"] == "running":
                self.close_commands(other)
                other["state"] = "done"
        if step["state"] != "failed":
            step["state"] = "running"

    @staticmethod
    def close_commands(step):
        for command in step["commands"]:
            if command["state"] == "running":
                command["state"] = "done"

    def observe(self, text):
        """Update from one public progress line. Returns True when the list changed."""
        before = json.dumps(self.steps, sort_keys=True)
        lowered = text.casefold().strip()
        if not self.flow:
            building = lowered.startswith(
                ("preparing an independent", "plan ready", "files changed", "working")
            )
            self.seed("build" if building else "chat")
        if lowered.startswith("running:"):
            command = text.split(":", 1)[1].strip()
            step = self.current()
            if step is None:
                step = self.find("plan" if self.flow == "build" else "context")
                self.start(step["key"] if step else "work", "Working")
                step = self.current()
            if self.flow == "build" and TESTS.search(command) and step["key"] == "build":
                self.start("checks")
                step = self.current()
            step["commands"] = (step["commands"] + [{"text": command, "state": "running"}])[-4:]
        elif lowered.startswith("$ "):
            lines = text.splitlines()
            command = lines[0][2:]
            ok = lines[-1].strip() == "Exit code: 0"
            for step in self.steps:
                for entry in step["commands"]:
                    if entry["text"] == command and entry["state"] == "running":
                        entry["state"] = "done" if ok else "failed"
        elif lowered.startswith(("files changed:", "edited ")) and self.flow == "build":
            self.start("build")
        elif lowered.startswith("plan ready"):
            self.start("build") if self.flow == "build" else None
        elif lowered.startswith(("build ready", "needs attention")):
            self.finish(ok=lowered.startswith("build ready"))
        elif lowered.startswith(("preparing an independent",)):
            self.start("copy")
        elif lowered.startswith(
            ("checking workspace access", "checking your workspace’s included ai")
        ):
            self.start("access")
        elif lowered.startswith("gathered "):
            step = self.find("context")
            if step is not None:  # the real amount read, e.g. "Read 142 messages"
                step["label"] = text.removesuffix(" for context").replace("Gathered", "Read", 1)
            found = re.search(r"(\d[\d,]*)\s+messages?", text)
            self.read_count = int(found.group(1).replace(",", "")) if found else None
        elif lowered.startswith(CONTEXT_PHASES):
            self.start("context", "Gathering context")
        elif lowered.startswith("writing a response"):
            # The status line above already says "Writing a response", so this row says what
            # the reply is built from instead of repeating it.
            respond = self.find("respond")
            on_web = " web" in lowered
            if respond is not None and (self.read_count or on_web):
                noun = "message" if self.read_count == 1 else "messages"
                parts = [f"{self.read_count:,} {noun} of context"] if self.read_count else []
                if on_web:
                    parts.append("the live web")
                respond["label"] = "Replying from " + " and ".join(parts)
            self.start("respond")
        elif lowered.startswith("checking reply sources"):
            self.start("sources", "Checking sources")
        elif lowered.startswith("preparing response") and self.flow == "build":
            self.start("plan")
        changed = json.dumps(self.steps, sort_keys=True) != before
        if changed:
            self.rebuild()
        return changed

    def finish(self, *, ok=True):
        for step in list(self.steps):
            self.close_commands(step)
            if step["state"] == "running":
                step["state"] = "done" if ok else "failed"
            elif step["state"] == "pending":
                self.steps.remove(step)
        self.rebuild()

    def states(self):
        return [(s["key"], s["state"]) for s in self.steps]

    # -- view --------------------------------------------------------------
    def rebuild(self):
        """Bring the rows in line with the steps without recreating widgets.

        Tearing every row down and building it again on each progress line made the list
        flash and jump while the agent worked. Rows are now kept, updated in place, and
        only added or removed when a step appears or goes.
        """
        desired = []
        for step in self.steps:
            desired.append((("step", step["key"]), step))
            for index, command in enumerate(step["commands"]):
                desired.append((("command", step["key"], index), command))
        wanted = {key for key, _ in desired}
        self.setUpdatesEnabled(False)
        try:
            for key in [k for k in self.parts if k not in wanted]:
                self.remove_part(self.parts.pop(key))
            self.rows = []
            for position, (key, item) in enumerate(desired):
                part = self.parts.get(key)
                if part is None:
                    part = self.parts[key] = self.make_part(key)
                    self.column.insertLayout(position, part["layout"])
                elif self.column.indexOf(part["layout"]) != position:
                    self.column.removeItem(part["layout"])
                    self.column.insertLayout(position, part["layout"])
                self.update_part(key, part, item)
                self.rows.append(part["icon"])
        finally:
            self.setUpdatesEnabled(True)
        self.setVisible(bool(self.steps))
        self.sync_timer()
        self.updateGeometry()
        self.changed.emit()

    def make_part(self, key):
        if key[0] == "step":
            row = QHBoxLayout()
            row.setSpacing(9)
            icon = StepIcon("pending")
            row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
            label = QLabel()
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            row.addWidget(label, 1)
        else:
            row = QHBoxLayout()
            row.setContentsMargins(27, 0, 0, 0)
            row.setSpacing(7)
            icon = StepIcon("pending")
            icon.setFixedSize(14, 14)
            row.addWidget(icon)
            label = QLabel()
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
            label.setProperty("role", "muted")
            row.addWidget(label, 1)
        return {"layout": row, "icon": icon, "label": label}

    def update_part(self, key, part, item):
        icon, label = part["icon"], part["label"]
        if icon.state != item["state"]:
            icon.state = item["state"]
            icon.update()
        if key[0] == "step":
            text, state = item["label"], item["state"]
            if label.text() != text:
                label.setText(text)
            role = "muted" if state == "pending" else ""
            if label.property("role") != role or part.get("state") != state:
                label.setProperty("role", role)
                label.setStyleSheet("font-weight: 600;" if state == "running" else "")
                label.style().unpolish(label)
                label.style().polish(label)
            label.setAccessibleName(text + " · " + state)
            part["state"] = state
        else:
            text = item["text"][:96]
            if label.text() != text:
                label.setText(text)
                label.setToolTip(item["text"][:600])

    def remove_part(self, part):
        layout = part["layout"]
        self.column.removeItem(layout)
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()
        layout.deleteLater()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def sync_timer(self):
        running = any(icon.state == "running" for icon in self.rows)
        if running and self.isVisible() and not reduced_motion():
            self.timer.start()
        else:
            self.timer.stop()

    def spin(self):
        self.phase = (self.phase + 14) % 360
        for icon in self.rows:
            if icon.state == "running":
                icon.angle = self.phase
                icon.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.sync_timer()

    def hideEvent(self, event):  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)


class Card(QFrame):
    """Base for in-stream cards so they flow through the stream's sizing like any row."""

    def showEvent(self, event):  # noqa: N802
        first = not getattr(self, "shown_once", False)
        self.shown_once = True
        super().showEvent(event)
        if first:
            from aedrova.desktop.motion import fade_in

            fade_in(self)

    def __init__(self, summary):
        super().__init__()
        self.summary = summary
        self.toggle = None
        self.pending = False
        self.setObjectName("AgentCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(74, 4, 20, 8)
        self.panel = QFrame()
        self.panel.setObjectName("AgentCardPanel")
        outer.addWidget(self.panel)
        self.body = QVBoxLayout(self.panel)
        self.body.setContentsMargins(14, 12, 14, 12)
        self.body.setSpacing(9)

    @staticmethod
    def action(text, *, primary=False):
        from aedrova.desktop.dialogs import button

        widget = button(text, role="primary" if primary else "outline")
        widget.setMinimumHeight(32)
        return widget


def describe(tool, data):
    """Plain-language title and detail for an action awaiting approval."""
    if tool == "Bash":
        return "Run a command in your build copy", str(data.get("command", ""))[:600]
    paths = data.get("paths") or [data.get("file_path", "")]
    names = [str(p) for p in paths if p]
    return (
        "Change files in your build copy" if tool in {"Edit", "Write"} else f"Use {tool}",
        "\n".join(names[:8]) if names else json.dumps(data, indent=2)[:600],
    )


class ApprovalCard(Card):
    """Allow once / Deny. The agent waits until one is chosen."""

    decided = Signal(bool)

    def __init__(self, tool, data):
        title, detail = describe(tool, data)
        super().__init__(title)
        self.resolved = False
        self.setAccessibleName("Approval needed: " + title)
        header = QLabel("Needs your approval")
        header.setProperty("role", "muted")
        self.body.addWidget(header)
        heading = QLabel(title)
        heading.setStyleSheet("font-weight: 600;")
        heading.setWordWrap(True)
        self.body.addWidget(heading)
        if detail:
            code = QLabel(detail)
            code.setTextFormat(Qt.TextFormat.PlainText)
            code.setWordWrap(True)
            code.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
            code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            code.setObjectName("AgentCardCode")
            self.body.addWidget(code)
        reason = data.get("reason")
        if isinstance(reason, str) and reason.strip():
            why = QLabel(reason.strip()[:240])
            why.setWordWrap(True)
            why.setProperty("role", "muted")
            self.body.addWidget(why)
        self.buttons = QHBoxLayout()
        self.buttons.setSpacing(8)
        self.allow = self.action("Allow once", primary=True)
        self.deny = self.action("Deny")
        self.allow.setAccessibleName("Allow once")
        self.deny.setAccessibleName("Deny")
        self.allow.clicked.connect(lambda: self.resolve(True))
        self.deny.clicked.connect(lambda: self.resolve(False))
        self.buttons.addWidget(self.allow)
        self.buttons.addWidget(self.deny)
        self.buttons.addStretch()
        self.body.addLayout(self.buttons)
        self.outcome = QLabel("")
        self.outcome.setProperty("role", "muted")
        self.outcome.hide()
        self.body.addWidget(self.outcome)

    def resolve(self, approved):
        if self.resolved:
            return
        self.resolved = True
        self.allow.hide()
        self.deny.hide()
        self.outcome.setText(
            "Allowed once." if approved else "Denied. The agent will continue without it."
        )
        self.outcome.show()
        self.decided.emit(approved)


class PromptCard(Card):
    """Questions from the agent as buttons and text boxes."""

    submitted = Signal(object)

    def __init__(self, question):
        super().__init__(question["title"])
        self.question = question
        self.resolved = False
        self.inputs = []
        self.setAccessibleName("Question from the agent: " + question["title"])
        header = QLabel("Aedrova has a question")
        header.setProperty("role", "muted")
        self.body.addWidget(header)
        title = QLabel(question["title"])
        title.setWordWrap(True)
        title.setStyleSheet("font-weight: 600;")
        self.body.addWidget(title)
        for field in question["fields"]:
            caption = field["label"] + ("" if field["required"] else " (optional)")
            label = QLabel(caption)
            label.setWordWrap(True)
            label.setProperty("role", "muted")
            self.body.addWidget(label)
            kind = field["type"]
            if kind == "text":
                control = QLineEdit()
                control.setMaxLength(4000)
                control.setPlaceholderText("Type your answer")
                control.setMinimumHeight(32)
                control.returnPressed.connect(self.send)
                self.body.addWidget(control)
                chips = None
            else:
                control = None
                chips = []
                wrap = QHBoxLayout()
                wrap.setSpacing(8)
                for option in field["options"]:
                    chip = self.action(option)
                    chip.setCheckable(True)
                    chip.setProperty("chip", True)
                    chip.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
                    chip.setAccessibleName(option)
                    if kind == "single":
                        chip.clicked.connect(lambda _c, c=chip, group=chips: self.choose(c, group))
                    chips.append(chip)
                    wrap.addWidget(chip)
                wrap.addStretch()
                self.body.addLayout(wrap)
            self.inputs.append((field, control, chips))
        actions = QHBoxLayout()
        self.send_button = self.action("Send answer", primary=True)
        self.send_button.clicked.connect(self.send)
        actions.addWidget(self.send_button)
        actions.addStretch()
        self.body.addLayout(actions)
        self.note = QLabel("")
        self.note.setProperty("role", "muted")
        self.note.setWordWrap(True)
        self.note.hide()
        self.body.addWidget(self.note)

    @staticmethod
    def choose(chip, group):
        for other in group:
            other.setChecked(other is chip and chip.isChecked())

    def answers(self):
        result = []
        for field, control, chips in self.inputs:
            if field["type"] == "text":
                value = control.text().strip()
            elif field["type"] == "single":
                value = next((c.text() for c in chips if c.isChecked()), None)
            else:
                value = [c.text() for c in chips if c.isChecked()]
            if not value and field["required"]:
                return None
            result.append({"label": field["label"], "answer": value})
        return result

    def send(self):
        if self.resolved:
            return
        answers = self.answers()
        if answers is None:
            self.note.setText("Choose or type an answer for each required question.")
            self.note.show()
            return
        self.resolved = True
        for _, control, chips in self.inputs:
            for widget in [control] if control else chips:
                widget.setEnabled(False)
        self.send_button.hide()
        self.note.setText("Answer sent. Continuing…")
        self.note.show()
        self.submitted.emit(answers)

    def focus_first(self):
        for _, control, chips in self.inputs:
            target = control or (chips[0] if chips else None)
            if target:
                target.setFocus()
                return


class StepSummary(QWidget):
    """What the agent did, kept with its answer. Collapsed until asked for."""

    changed = Signal()

    def __init__(self, steps, parent=None):
        super().__init__(parent)
        done = [s for s in steps if s["state"] in {"done", "failed"}]
        failed = any(s["state"] == "failed" for s in done)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        count = len(done)
        self.toggle = QToolButton()
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.toggle.setCheckable(True)
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.setStyleSheet("border: none; background: transparent; padding: 2px 0;")
        plural = "s" if count != 1 else ""
        self.title = f"{count} step{plural} {'with an issue' if failed else 'completed'}"
        self.toggle.setAccessibleName("Agent steps · " + self.title)
        self.list = StepChecklist()
        self.list.steps = [dict(s, commands=[dict(c) for c in s["commands"]]) for s in done]
        self.list.flow = "summary"
        self.list.rebuild()
        self.list.setVisible(False)
        self.toggle.toggled.connect(self.expand)
        column.addWidget(self.toggle)
        column.addWidget(self.list)
        self.expand(False)

    def expand(self, expanded):
        from aedrova.desktop.icons import icon

        color = self.palette().color(QPalette.ColorRole.Text).name()
        self.toggle.setIcon(icon("chevron" if expanded else "chevron_right", color))
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.setText(self.title)
        self.list.setVisible(expanded)
        self.changed.emit()


class DeliveryCard(QFrame):
    """Ship a finished build from the conversation: review, apply, open a pull request.

    It drives the same guarded review flow as the Review dialog. Each step shows its exact
    scope here and needs its own click, and applying and publishing stay separate.
    """

    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog
        self.mode = "loading"
        self.setObjectName("AgentCardPanel")
        self.setAccessibleName("Deliver this build")
        column = QVBoxLayout(self)
        column.setContentsMargins(14, 12, 14, 12)
        column.setSpacing(9)
        self.headline = QLabel("Reading the changes…")
        self.headline.setStyleSheet("font-weight: 600;")
        self.headline.setWordWrap(True)
        column.addWidget(self.headline)
        self.detail = QLabel("")
        self.detail.setWordWrap(True)
        self.detail.setTextFormat(Qt.TextFormat.PlainText)
        self.detail.setProperty("role", "muted")
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.detail.hide()
        column.addWidget(self.detail)
        self.buttons = QHBoxLayout()
        self.buttons.setSpacing(8)
        self.review_button = Card.action("Review changes")
        self.apply_button = Card.action("Apply to project", primary=True)
        self.pr_button = Card.action("Open pull request")
        self.confirm_button = Card.action("", primary=True)
        self.cancel_button = Card.action("Cancel")
        self.link_button = Card.action("Open on GitHub", primary=True)
        for control in (
            self.review_button,
            self.apply_button,
            self.pr_button,
            self.confirm_button,
            self.cancel_button,
            self.link_button,
        ):
            self.buttons.addWidget(control)
        self.buttons.addStretch()
        column.addLayout(self.buttons)
        self.review_button.clicked.connect(self.open_review)
        self.apply_button.clicked.connect(self.ask_apply)
        self.pr_button.clicked.connect(self.ask_pull_request)
        self.confirm_button.clicked.connect(self.confirm)
        self.cancel_button.clicked.connect(self.reset)
        self.link_button.clicked.connect(self.open_link)
        self.url = ""
        self.applied = False
        self.show_buttons()
        dialog.state.connect(self.on_state)
        if dialog.review is not None:
            self.on_state("loaded", dialog.review)

    # -- helpers -------------------------------------------------------------
    def show_buttons(self, *names):
        controls = {
            "review": self.review_button,
            "apply": self.apply_button,
            "pr": self.pr_button,
            "confirm": self.confirm_button,
            "cancel": self.cancel_button,
            "link": self.link_button,
        }
        for name, control in controls.items():
            control.setVisible(name in names)

    def say(self, headline, detail=""):
        self.headline.setText(headline)
        self.detail.setText(detail)
        self.detail.setVisible(bool(detail))

    def idle_buttons(self):
        names = ["review"]
        if not self.applied:
            names.append("apply")
        if not self.url:
            names.append("pr")
        self.show_buttons(*names)

    def reset(self):
        self.mode = "ready"
        review = self.dialog.review
        if review is not None:
            self.on_state("loaded", review, keep=True)

    # -- dialog events -------------------------------------------------------
    def on_state(self, kind, payload, *, keep=False):
        if kind == "loaded":
            review = payload
            count = len(review.changes)
            if not count:
                self.say("This build made no changes to your project.")
                self.show_buttons()
                return
            added = sum(c.line_counts()[0] or 0 for c in review.changes)
            removed = sum(c.line_counts()[1] or 0 for c in review.changes)
            self.mode = "ready"
            self.say(
                f"{count} file{'s' if count != 1 else ''} changed  +{added} −{removed}",
                "Ready for your review. Nothing has touched your project yet.",
            )
            self.idle_buttons()
        elif kind == "applied":
            self.applied = True
            self.mode = "ready"
            self.say("Applied to your project.", "A recovery copy was kept. Nothing was pushed.")
            self.idle_buttons()
        elif kind == "needs_repository":
            self.mode = "ready"
            self.say("Connect a GitHub repository first.", "Then open the pull request again.")
            self.confirm_button.setText("Connect a repository…")
            self.mode = "connect"
            self.show_buttons("confirm", "cancel")
        elif kind == "prepared":
            self.mode = "publish"
            self.say("Create this draft pull request?", self.dialog.scope.text())
            self.confirm_button.setText("Create draft pull request")
            self.show_buttons("confirm", "cancel")
        elif kind == "published":
            self.mode = "done"
            self.url = payload.get("url", "")
            self.say(payload.get("message", "Published."), self.url)
            self.show_buttons("review", "link")
        elif kind == "error":
            self.mode = "ready"
            self.say("That did not complete.", str(payload))
            self.idle_buttons()

    # -- actions -------------------------------------------------------------
    def open_review(self):
        self.dialog.studio.open_review()

    def ask_apply(self):
        review = self.dialog.review
        if not review or not review.changes:
            return
        self.mode = "apply"
        self.say(
            f"Apply {len(review.changes)} file change{'s' if len(review.changes) != 1 else ''} "
            "to your project?",
            f"{review.source}\nExisting edits to these files block applying. A recovery copy "
            "is kept. This does not stage, commit or push anything.",
        )
        self.confirm_button.setText("Apply changes")
        self.show_buttons("confirm", "cancel")

    def ask_pull_request(self):
        self.mode = "preparing"
        self.say("Checking the repository…", "")
        self.show_buttons()
        self.dialog.prepare()

    def confirm(self):
        mode = self.mode
        if mode == "apply":
            self.say("Applying…")
            self.show_buttons()
            self.dialog.apply(confirmed=True)
        elif mode == "publish":
            self.say("Creating the draft pull request…")
            self.show_buttons()
            self.dialog.publish(confirmed=True)
        elif mode == "connect":
            self.dialog.open_project_connection()

    def open_link(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        if self.url.startswith("https://"):
            QDesktopServices.openUrl(QUrl(self.url))


class ChoiceCard(QFrame):
    """Suggested next steps as buttons, with a text box for anything else."""

    chosen = Signal(str, bool)  # text, free-form

    def __init__(self, options):
        super().__init__()
        self.setObjectName("AgentChoices")
        self.setAccessibleName("Choose how to continue")
        self.done = False
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 6, 0, 2)
        column.setSpacing(7)
        self.buttons = []
        for option in options:
            button = Card.action(option)
            button.setProperty("choice", True)
            button.setToolTip(option)
            button.setAccessibleName(option)
            button.setMinimumHeight(38)
            button.setStyleSheet("text-align: left; padding: 8px 14px;")
            button.clicked.connect(lambda _c=False, text=option: self.pick(text, False))
            column.addWidget(button)
            self.buttons.append(button)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Or tell Aedrova what you’d like instead…")
        self.input.setMaxLength(2000)
        self.input.setMinimumHeight(36)
        self.input.setAccessibleName("Your own answer")
        self.input.returnPressed.connect(self.send)
        self.send_button = Card.action("Send", primary=True)
        self.send_button.setMinimumHeight(36)
        self.send_button.clicked.connect(self.send)
        row.addWidget(self.input, 1)
        row.addWidget(self.send_button)
        column.addLayout(row)

    def send(self):
        text = self.input.text().strip()
        if text:
            self.pick(text, True)

    def pick(self, text, free):
        if self.done:
            return
        self.done = True
        for control in (*self.buttons, self.input, self.send_button):
            control.setEnabled(False)
        self.input.clear()
        self.chosen.emit(text, free)
