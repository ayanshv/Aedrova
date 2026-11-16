"""Read the current workspace's shared AI allowance without blocking chat."""

from datetime import UTC, datetime

from PySide6.QtCore import QThreadPool, QTimer, Slot
from PySide6.QtWidgets import QHBoxLayout, QProgressBar, QVBoxLayout, QWidget

from aedrova.agents.managed import ManagedClient, application_origin
from aedrova.desktop.account import AccountJob
from aedrova.desktop.dialogs import label


class WorkspaceUsage(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.scope = None
        self.job = None
        self.job_scope = None
        self.refresh_pending = False
        self.timer = QTimer(self)
        self.timer.setInterval(15_000)
        self.timer.timeout.connect(self.refresh)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 4)
        layout.setSpacing(6)
        row = QHBoxLayout()
        row.addWidget(label("Shared AI usage", "muted"))
        row.addStretch()
        self.remaining = label("", "muted")
        row.addWidget(self.remaining)
        layout.addLayout(row)
        self.bar = QProgressBar()
        self.bar.setObjectName("WorkspaceUsageBar")
        self.bar.setFixedHeight(5)
        self.bar.setTextVisible(False)
        self.bar.setAccessibleName("Shared monthly AI allowance used")
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
                return ManagedClient(origin, access).balance(workspace)
            return None

        self.job = AccountJob(operation)
        self.job_scope = scope
        self.job.signals.finished.connect(self.loaded)
        QThreadPool.globalInstance().start(self.job)

    @Slot(object, bool)
    def loaded(self, data, ok):
        self.job = None
        if self.job_scope is self.scope:
            self.show_balance(data if ok else None)
        self.job_scope = None
        if self.refresh_pending:
            self.refresh_pending = False
            self.refresh()

    def set_state(self, text, *, used=None, detail=""):
        self.remaining.setText(text)
        self.bar.setVisible(used is not None)
        self.bar.setValue(used or 0)
        self.setToolTip(detail)

    def show_balance(self, data):
        if not isinstance(data, dict):
            self.set_state("Unavailable", detail="Could not refresh your workspace’s AI usage.")
            return
        if data.get("status") != "active":
            self.set_state("Inactive", detail="Included AI is inactive for this workspace.")
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
        if data.get("available") == 0 or (
            type(data.get("monthly_request_limit")) is int
            and type(data.get("monthly_requests")) is int
            and data["monthly_requests"] >= data["monthly_request_limit"] > 0
        ):
            text = "Limit reached"
            detail = f"AI is at a usage limit. {detail}"
        reset = data.get("reset_at")
        if type(reset) is int and 0 < reset < 4_102_444_800:
            date = datetime.fromtimestamp(reset, UTC).strftime("%b %d")
            detail += f" Monthly allowance resets {date} (UTC)."
        if text.endswith("% left") and type(settled) is not int:
            text = "≈" + text
        self.set_state(text, used=used, detail=detail)
