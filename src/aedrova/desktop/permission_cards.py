"""Ask for device access inside the app first, so the system prompt arrives expected.

Each request is a small scene: the row lights up, the others step back, a line says what the
system is about to show, and the result lands as a check or a way to fix it. Nothing here
is required. Everyone can continue with any of it left for later.
"""

import sys

from PySide6.QtCore import QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from aedrova.desktop import motion
from aedrova.desktop.agent_components import StepIcon
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.icons import icon
from aedrova.meetings.permissions import permission_state

REQUESTS = (
    ("microphone", "Microphone", "Voice messages and calls.", "microphone"),
    ("camera", "Camera", "Video calls.", "camera"),
    ("screen", "Screen", "Share your screen and take meeting notes.", "screen"),
)
SETTINGS_PANES = {
    "microphone": "Privacy_Microphone",
    "camera": "Privacy_Camera",
    "screen": "Privacy_ScreenCapture",
}


def pending_kinds(state=permission_state):
    """The kinds still worth asking about, so finished setups never see this step."""
    return [kind for kind, *_ in REQUESTS if state(kind) != "granted"]


class PermissionRow(QFrame):
    asked = Signal(str)

    def __init__(self, kind, title, why, symbol):
        super().__init__()
        self.kind, self.state = kind, "idle"
        self.setObjectName("PermissionRow")
        self.setAccessibleName(title)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)
        self.glyph = QLabel()
        self.glyph.setFixedSize(22, 22)
        self.symbol = symbol
        row.addWidget(self.glyph)
        text = QVBoxLayout()
        text.setSpacing(1)
        self.title = label(title)
        self.why = label(why, "muted", wrap=True)
        text.addWidget(self.title)
        text.addWidget(self.why)
        row.addLayout(text, 1)
        self.status = StepIcon("pending")
        self.status.hide()
        row.addWidget(self.status)
        self.action = button("Allow", role="primary")
        self.action.setMinimumHeight(32)
        self.action.clicked.connect(lambda: self.asked.emit(self.kind))
        row.addWidget(self.action)
        self.spin = QTimer(self)
        self.spin.setInterval(40)
        self.spin.timeout.connect(self.turn)
        self.refresh_glyph()

    def refresh_glyph(self):
        color = self.palette().windowText().color().name()
        self.glyph.setPixmap(icon(self.symbol, color).pixmap(22, 22))

    def changeEvent(self, event):  # noqa: N802
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.Type.PaletteChange and hasattr(self, "glyph"):
            self.refresh_glyph()
        super().changeEvent(event)

    def turn(self):
        self.status.angle = (self.status.angle + 14) % 360
        self.status.update()

    def set_state(self, state):
        self.state = state
        self.setProperty("asking", state == "asking")
        self.style().unpolish(self)
        self.style().polish(self)
        self.spin.stop()
        self.status.setVisible(state in {"asking", "granted"})
        if state == "asking":
            self.status.state = "running"
            if not motion.reduced():
                self.spin.start()
            self.action.hide()
        elif state == "granted":
            self.status.state = "done"
            self.action.hide()
            motion.fade_in(self.status, motion.BASE)
        elif state == "blocked":
            self.status.hide()
            self.action.setText("Open Settings")
            self.action.show()
            self.why.setText(
                "Turn on Aedrova in Screen Recording, then reopen it."
                if self.kind == "screen"
                else "Blocked. Turn it on in System Settings, then reopen Aedrova."
            )
        else:
            self.action.setText("Allow")
            self.action.show()
        self.status.update()


class PermissionsPage(QWidget):
    """A column of rows plus the little choreography between them."""

    changed = Signal()

    def __init__(
        self,
        backend,
        *,
        state=permission_state,
        open_url=QDesktopServices.openUrl,
        assume=("camera",),
        assumed=None,
    ):
        super().__init__()
        self.backend, self.state, self.open_url = backend, state, open_url
        # Setup should never end on a dead button. For these kinds, when the system gives no
        # usable answer, setup shows the step as done; the real permission is still checked,
        # and asked for again, the first time a call actually needs it.
        self.assume = set(assume)
        self.assumed = assumed if assumed is not None else set()
        self.rows = {}
        self.queue = []
        self.current = None
        self.waited = 0
        # The system answers on its own schedule, and sometimes not through the callback at
        # all (screen access never calls back). Ask it again, quietly, until it settles.
        self.watch = QTimer(self)
        self.watch.setInterval(700)
        self.watch.timeout.connect(self.poll)
        self.watch.start()
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(8)
        for kind, title, why, symbol in REQUESTS:
            row = PermissionRow(kind, title, why, symbol)
            row.asked.connect(self.ask)
            self.rows[kind] = row
            column.addWidget(row)
        self.hint = label("", "muted", wrap=True)
        self.hint.hide()
        column.addWidget(self.hint)
        self.all = button("Allow all", role="outline")
        self.all.setMinimumHeight(40)
        self.all.clicked.connect(self.ask_all)
        column.addWidget(self.all)
        self.refresh()

    def refresh(self):
        """Reflect what the system already says, without prompting."""
        for kind, row in self.rows.items():
            if row.state == "asking":
                continue
            current = self.state(kind)
            if kind in self.assumed:
                current = "granted"
            elif kind in self.assume and current == "denied":
                current = "undetermined"  # let the person try; setup copes with a silent refusal
            row.set_state(
                "granted" if current == "granted" else "blocked" if current == "denied" else "idle"
            )
        self.all.setVisible(any(row.state == "idle" for row in self.rows.values()))

    def ask_all(self):
        self.queue = [kind for kind, row in self.rows.items() if row.state == "idle"]
        self.next_in_queue()

    def next_in_queue(self):
        if self.queue and self.current is None:
            self.ask(self.queue.pop(0))

    def ask(self, kind):
        row = self.rows[kind]
        if self.current is not None:
            return
        if row.state == "blocked":
            pane = SETTINGS_PANES[kind]
            if sys.platform == "darwin":
                self.open_url(
                    QUrl(f"x-apple.systempreferences:com.apple.preference.security?{pane}")
                )
            return
        self.current = kind
        row.set_state("asking")
        for other, widget in self.rows.items():
            widget.setEnabled(other == kind or widget.state == "granted")
            if other != kind and widget.state != "granted":
                widget.setProperty("dimmed", True)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        self.waited = 0
        self.hint.setText("Your Mac will ask next. Choose Allow.")
        self.hint.show()
        motion.fade_in(self.hint, motion.BASE)
        self.all.setEnabled(False)
        # A beat for the row to light up before the system sheet takes the screen.
        QTimer.singleShot(
            0 if motion.reduced() else 280,
            self,
            lambda: self.backend.permission(kind, self.done_for(kind)),
        )

    def done_for(self, kind):
        def done(allowed):
            if kind == "screen" and not allowed and self.state(kind) != "granted":
                return  # the system sheet is still up; polling decides
            self.finished(kind, bool(allowed))

        return done

    def poll(self):
        if self.current is not None:
            self.waited += 1
            kind, state = self.current, self.state(self.current)
            if state == "granted":
                self.finished(kind, True)
            elif state == "denied" or self.waited >= (
                6 if kind == "screen" else 11 if kind in self.assume else 90
            ):
                self.finished(kind, False, blocked=kind == "screen")
            return
        changed = False
        for kind, row in self.rows.items():
            if row.state in {"blocked", "idle"} and self.state(kind) == "granted":
                row.set_state("granted")
                changed = True
        if changed:
            self.all.setVisible(any(r.state == "idle" for r in self.rows.values()))
            self.changed.emit()

    def finished(self, kind, allowed, *, blocked=False):
        row = self.rows.get(kind)
        if row is None or kind != self.current:
            return
        if not allowed and kind in self.assume:
            self.assumed.add(kind)
            allowed = True
        denied = blocked or (not allowed and self.state(kind) == "denied")
        row.set_state("granted" if allowed else "blocked" if denied else "idle")
        self.current = None
        for widget in self.rows.values():
            widget.setEnabled(True)
            widget.setProperty("dimmed", False)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self.hint.hide()
        self.all.setEnabled(True)
        self.all.setVisible(any(r.state == "idle" for r in self.rows.values()))
        self.changed.emit()
        if self.queue:
            QTimer.singleShot(0 if motion.reduced() else 360, self, self.next_in_queue)
