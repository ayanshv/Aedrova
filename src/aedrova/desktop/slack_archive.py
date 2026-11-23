"""The 'From Slack' sidebar list: each imported channel opens as a read-only copy."""

import time

from PySide6.QtCore import Qt, QThreadPool, Slot
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from aedrova.desktop.dialogs import label
from aedrova.desktop.projects import Job


class SlackArchiveList(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.workspace = None
        self.loaded_at = 0.0
        self.busy = False
        self.setObjectName("SlackArchive")
        column = QVBoxLayout(self)
        column.setContentsMargins(10, 0, 0, 0)
        column.setSpacing(4)
        column.addSpacing(12)
        self.header = label("From Slack", "section")
        column.addWidget(self.header)
        self.list = QListWidget()
        self.list.setObjectName("Navigation")
        self.list.setAccessibleName("Channels imported from Slack")
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.itemClicked.connect(self.open_channel)
        self.list.itemActivated.connect(self.open_channel)
        column.addWidget(self.list)
        self.hide()

    def service(self):
        connected = getattr(self.window, "connected", None)
        account = getattr(connected, "account", None) if connected and connected.active else None
        service = getattr(account, "service", None)
        return service if service is not None and getattr(service, "user", None) else None

    def refresh(self, *, force=False):
        service, workspace = self.service(), getattr(self.window, "workspace_id", None)
        if service is None or not workspace or not hasattr(service, "slack_channels"):
            self.hide()
            return
        fresh = workspace == self.workspace and time.monotonic() - self.loaded_at < 60
        if self.busy or (fresh and not force):
            return
        self.busy, self.workspace = True, workspace
        job = Job(lambda: service.slack_channels(str(workspace)))
        job.signals.finished.connect(self.loaded)
        QThreadPool.globalInstance().start(job)

    @Slot(object)
    def loaded(self, result):
        self.busy = False
        if self.workspace != getattr(self.window, "workspace_id", None):
            return
        self.loaded_at = time.monotonic()
        rows = result.get("value") if isinstance(result, dict) else None
        self.list.clear()
        for row in rows or []:
            item = QListWidgetItem(f"#    {row['channel_name']}")
            item.setData(Qt.ItemDataRole.UserRole, row)
            item.setToolTip(f"{int(row['message_count']):,} messages from Slack · read-only")
            self.list.addItem(item)
        self.list.setMaximumHeight(min(200, max(38, self.list.count() * 41)))
        self.setVisible(self.list.count() > 0)

    def open_channel(self, item):
        service, workspace = self.service(), getattr(self.window, "workspace_id", None)
        if item is None or service is None or not workspace:
            return
        from aedrova.desktop.slack_history import open_slack_history

        open_slack_history(
            self.window,
            service,
            workspace,
            mode="channel",
            channel=item.data(Qt.ItemDataRole.UserRole),
        )
        self.list.clearSelection()
