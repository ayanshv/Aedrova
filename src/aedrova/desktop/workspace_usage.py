"""Read the current workspace's shared AI allowance without blocking chat."""

from datetime import UTC, datetime

from PySide6.QtCore import QPoint, Qt, QThreadPool, QTimer, Slot
from PySide6.QtWidgets import QFrame, QHBoxLayout, QProgressBar, QVBoxLayout, QWidget

from aedrova.agents.managed import ManagedClient, application_origin
from aedrova.desktop.account import AccountJob
from aedrova.desktop.dialogs import label


class UsagePopover(QFrame):
    """A quiet summary of both windows. Opens from the usage line and closes on any click."""

    def __init__(self, parent, weekly, five_hour, notes):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("UsagePopoverShell")
        shell = QVBoxLayout(self)
        shell.setContentsMargins(8, 8, 8, 8)
        panel = QFrame()
        panel.setObjectName("UsagePopover")
        shell.addWidget(panel)
        column = QVBoxLayout(panel)
        column.setContentsMargins(18, 16, 18, 16)
        column.setSpacing(14)
        column.addWidget(label("AI usage", "title"))
        self.rows = []
        self.note = notes
        for title, left, reset in (
            ("Next 5 hours", five_hour[0], five_hour[1]),
            ("This week", weekly[0], weekly[1]),
        ):
            if left is None:
                continue
            block = QVBoxLayout()
            block.setSpacing(5)
            head = QHBoxLayout()
            head.addWidget(label(title))
            head.addStretch()
            value = label(f"{left}% left")
            value.setObjectName("UsageValue")
            head.addWidget(value)
            block.addLayout(head)
            bar = QProgressBar()
            bar.setObjectName("WorkspaceUsageBar")
            bar.setFixedHeight(6)
            bar.setRange(0, 100)
            bar.setValue(100 - left)
            bar.setTextVisible(False)
            bar.setAccessibleName(f"{title}: {left}% left")
            block.addWidget(bar)
            block.addWidget(label(reset or "Full capacity", "muted"))
            column.addLayout(block)
            self.rows.append((title, left, reset))
        if notes:
            column.addWidget(label(notes, "muted", wrap=True))
        column.addWidget(
            label(
                "Shared by your workspace. Chat, files and meetings never use it.",
                "muted",
                wrap=True,
            )
        )
        self.setFixedWidth(300)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        from aedrova.desktop.motion import fade_in_window

        fade_in_window(self, 140)


class WorkspaceUsage(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.scope = None
        self.job = None
        self.job_scope = None
        self.refresh_pending = False
        self.activation_tried = set()
        self.timer = QTimer(self)
        self.timer.setInterval(15_000)
        self.timer.timeout.connect(self.refresh)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 4)
        layout.setSpacing(6)
        row = QHBoxLayout()
        self.caption = label("Next 5 hours", "muted")
        row.addWidget(self.caption)
        row.addStretch()
        self.remaining = label("", "muted")
        row.addWidget(self.remaining)
        layout.addLayout(row)
        self.bar = QProgressBar()
        self.bar.setObjectName("WorkspaceUsageBar")
        self.bar.setFixedHeight(5)
        self.bar.setTextVisible(False)
        self.bar.setAccessibleName("AI allowance used in the next 5 hours")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("AI usage. Press to see weekly and five-hour details")
        self.data = None
        self.popover = None
        layout.addWidget(self.bar)
        self.hide()

    def sync_scope(self):
        connected = self.window.connected
        service = connected.account.service if connected and connected.active else None
        origin = application_origin() if service and service.user else ""
        scope = (
            (service, str(service.user.id), self.window.workspace_id, origin) if origin else None
        )
        if scope == self.scope:
            return
        self.scope = scope
        self.setVisible(scope is not None)
        self.refresh_pending = False
        self.set_state("Checking…")
        if scope is None:
            self.timer.stop()
            return
        self.timer.start()
        self.refresh()

    def refresh(self, workspace=None):
        scope = self.scope
        if scope is None or (workspace is not None and workspace != scope[2]):
            return
        if self.job is not None:
            self.refresh_pending = True
            return
        service, expected, workspace, origin = scope

        def operation():
            _, _, access, user = service.realtime_credentials()
            if user == expected:
                try:
                    return ManagedClient(origin, access).balance(workspace)
                except RuntimeError as error:
                    if "not active yet" in str(error):
                        # A workspace with no plan yet is inactive, not unavailable.
                        return {"status": "inactive"}
                    raise
            return None

        self.job = AccountJob(operation)
        self.job_scope = scope
        self.job.signals.finished.connect(self.loaded)
        QThreadPool.globalInstance().start(self.job)

    @Slot(object, bool)
    def loaded(self, data, ok):
        self.job = None
        current = self.job_scope is self.scope
        if current:
            self.show_balance(data if ok else None)
        self.job_scope = None
        if current and ok and isinstance(data, dict) and data.get("status") != "active":
            self.activate()
        if self.refresh_pending:
            self.refresh_pending = False
            self.refresh()

    def activate(self):
        """Included AI starts on its own. The service still checks role and eligibility.

        One automatic attempt per account and workspace; Settings keeps the manual button.
        """
        scope = self.scope
        if scope is None or self.job is not None or scope[1:] in self.activation_tried:
            return
        self.activation_tried.add(scope[1:])
        service, expected, workspace, origin = scope

        def operation():
            _, _, access, user = service.realtime_credentials()
            if user == expected:
                return ManagedClient(origin, access).activate_free(workspace)
            return None

        self.set_state("Setting up…", detail="Turning on included AI for this workspace.")
        self.job = AccountJob(operation)
        self.job_scope = scope
        self.job.signals.finished.connect(self.activated)
        QThreadPool.globalInstance().start(self.job)

    @Slot(object, bool)
    def activated(self, data, ok):
        self.job = None
        if self.job_scope is self.scope and ok and isinstance(data, dict):
            self.show_balance(data)
        elif self.job_scope is self.scope:
            self.set_state(
                "Inactive",
                detail="Included AI could not start automatically. "
                "A workspace owner can retry in Settings → Plan & AI access.",
            )
        self.job_scope = None
        if self.refresh_pending:
            self.refresh_pending = False
            self.refresh()

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.show_details()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.show_details()
            return
        super().keyPressEvent(event)

    def show_details(self):
        data = self.data
        if not isinstance(data, dict) or self.popover is not None and self.popover.isVisible():
            return
        weekly = self.window_left(data.get("weekly_budget"), data.get("weekly_spent"))
        five = self.window_left(data.get("five_hour_budget"), data.get("five_hour_spent"))
        notes = ""
        if five == 0:
            notes = "AI is paused until the 5-hour window frees up. Chat still works."
        elif weekly == 0:
            notes = "AI is paused until this week’s usage ages out. Chat still works."
        self.popover = UsagePopover(
            self.window,
            (weekly, self.reset_words(data.get("weekly_reset_at"), short=False)),
            (five, self.reset_words(data.get("five_hour_reset_at"), short=True)),
            notes,
        )
        self.popover.adjustSize()
        anchor = self.mapToGlobal(QPoint(self.width() + 4, self.height() - self.popover.height()))
        self.popover.move(anchor)
        self.popover.show()

    def set_state(self, text, *, used=None, detail=""):
        self.remaining.setText(text)
        self.bar.setVisible(used is not None)
        self.bar.setValue(used or 0)
        self.setToolTip(detail)

    @staticmethod
    def window_left(budget, spent):
        """Percent left in one window, or None when the server did not report it."""
        if type(budget) is not int or budget <= 0 or type(spent) is not int:
            return None
        return 100 * max(0, budget - max(0, spent)) // budget

    @staticmethod
    def reset_words(stamp, *, short):
        now = datetime.now(UTC).timestamp()
        if type(stamp) is not int or stamp <= now or stamp > 4_102_444_800:
            return ""
        if short:
            hours, minutes = divmod(int((stamp - now) // 60), 60)
            return f"resets in {hours} h {minutes:02d} min" if hours else f"resets in {minutes} min"
        moment = datetime.fromtimestamp(stamp).astimezone()
        return "resets " + moment.strftime("%a %b %-d, %-I:%M %p")

    def show_balance(self, data):
        if not isinstance(data, dict):
            self.set_state("Unavailable", detail="Could not refresh your workspace’s AI usage.")
            return
        if data.get("status") != "active":
            self.set_state("Inactive", detail="Included AI is inactive for this workspace.")
            return
        weekly = self.window_left(data.get("weekly_budget"), data.get("weekly_spent"))
        five = self.window_left(data.get("five_hour_budget"), data.get("five_hour_spent"))
        if weekly is not None:
            self.data = data
            # The main line is always the five-hour window; a full week still stops work.
            shown = five if five is not None else weekly
            text = "<1% left" if 0 < shown < 1 else f"{shown}% left"
            full = [name for name, value in (("5-hour", five), ("weekly", weekly)) if value == 0]
            if data.get("available") == 0 or full:
                text = "Limit reached"
            if weekly == 0:
                self.caption.setText("This week")
            else:
                self.caption.setText("Next 5 hours")
            used = 100 if weekly == 0 else 100 - shown
            self.set_state(text, used=used, detail="Click for details")
            return
        budget = data.get("monthly_budget", data.get("allowance"))
        settled = data.get("monthly_settled")
        spent = settled if type(settled) is int else data.get("monthly_spent", data.get("spent"))
        if type(budget) is not int or budget <= 0 or type(spent) is not int:
            self.set_state("Unavailable")
            return
        remaining = max(0, budget - max(0, spent))
        percent = 100 * remaining // budget
        text = "<1% left" if remaining and not percent else f"{percent}% left"
        used = 100 - percent
        detail = f"{text} in your shared monthly AI allowance."
        pending = data.get("monthly_pending")
        if type(settled) is not int:
            detail += " This estimate can change while requests finish."
        elif type(pending) is int and pending > 0:
            detail += " Requests in progress have reserved some of this allowance."
        if data.get("available") == 0:
            text = "Limit reached"
            detail = f"AI is at a usage limit. {detail}"
        reset = data.get("reset_at")
        if type(reset) is int and 0 < reset < 4_102_444_800:
            date = datetime.fromtimestamp(reset, UTC).strftime("%b %d")
            detail += f" Monthly allowance resets {date} (UTC)."
        if text.endswith("% left") and type(settled) is not int:
            text = "≈" + text
        self.set_state(text, used=used, detail=detail)
